from __future__ import annotations

import json
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from itertools import combinations
from pathlib import Path

from autobilans.calculation import calculate_balance_with_contributions
from autobilans.dataset_index import DatasetEntry
from autobilans.exporters import (
    export_balance_pdf,
    export_balance_xlsx,
    export_code_contributions,
    export_mapping_report,
)
from autobilans.mapping.rules import account_prefixes
from autobilans.mapping.service import MappingDecision
from autobilans.models import ZoisRow
from autobilans.parsers import parse_bilans_xml, parse_zois


@dataclass(slots=True)
class LearnedPrefixRule:
    prefix: str
    balance_code: str
    evidence_years: list[int]
    confidence: float


@dataclass(slots=True)
class LearnedCompanyRules:
    company: str
    target_year: int
    history_years: list[int]
    prefix_rules: dict[str, LearnedPrefixRule]


def _leaf_prefix_totals(rows: list[ZoisRow], *, max_depth: int | None = None) -> dict[str, float]:
    accounts = {row.account_no for row in rows}
    non_leaf_accounts = set()
    for account_no in accounts:
        parts = account_no.split("-")
        for i in range(1, len(parts)):
            non_leaf_accounts.add("-".join(parts[:i]))

    totals: dict[str, float] = defaultdict(float)
    for row in rows:
        if row.account_no in non_leaf_accounts:
            continue
        prefixes = account_prefixes(row.account_no)
        if max_depth is not None:
            prefixes = prefixes[:max_depth]
        for prefix in prefixes:
            totals[prefix] += row.persaldo
    return dict(totals)


def _transformed_amount(code: str, raw_total: float) -> float:
    if code.startswith("Pasywa_"):
        return -raw_total
    return raw_total


def _matches_position_amount(code: str, raw_total: float, expected: float, tolerance: float) -> bool:
    if abs(expected) <= tolerance:
        return False
    transformed = _transformed_amount(code, raw_total)
    return transformed > 0 and abs(transformed - expected) <= tolerance


def _best_prefix(candidates: list[str]) -> str | None:
    if not candidates:
        return None
    return sorted(candidates, key=lambda item: (len(item.split("-")), len(item), item))[0]


def _overlaps(left: str, right: str) -> bool:
    return left == right or left.startswith(f"{right}-") or right.startswith(f"{left}-")


def _non_overlapping(prefixes: tuple[str, ...]) -> bool:
    for left, right in combinations(prefixes, 2):
        if _overlaps(left, right):
            return False
    return True


def _candidate_prefixes(
    *,
    code: str,
    expected: float,
    totals: dict[str, float],
    tolerance: float,
) -> list[tuple[str, float]]:
    max_abs = max(abs(expected) * 1.5, abs(expected) + 50_000.0)
    candidates: list[tuple[str, float]] = []
    for prefix, raw_total in totals.items():
        transformed = round(_transformed_amount(code, raw_total), 2)
        if abs(transformed) <= tolerance:
            continue
        if abs(transformed) <= max_abs:
            candidates.append((prefix, transformed))
    return sorted(candidates, key=lambda item: abs(item[1]), reverse=True)[:50]


def _find_prefix_combo(
    *,
    code: str,
    expected: float,
    totals: dict[str, float],
    tolerance: float,
) -> tuple[str, ...]:
    if abs(expected) <= tolerance:
        return ()

    exact_single = [
        prefix
        for prefix, total in totals.items()
        if _matches_position_amount(code, total, expected, tolerance)
    ]
    best_single = _best_prefix(exact_single)
    if best_single:
        return (best_single,)

    candidates = _candidate_prefixes(code=code, expected=expected, totals=totals, tolerance=tolerance)
    expected_cents = round(expected * 100)
    candidate_cents = [(prefix, round(value * 100)) for prefix, value in candidates]

    for size in (2, 3):
        for combo in combinations(candidate_cents, size):
            prefixes = tuple(prefix for prefix, _ in combo)
            if not _non_overlapping(prefixes):
                continue
            if sum(value for _, value in combo) == expected_cents:
                return tuple(sorted(prefixes, key=lambda item: (len(item.split("-")), item)))

    return ()


def _history_entries(entries: list[DatasetEntry], company: str, target_year: int) -> list[DatasetEntry]:
    return sorted(
        (
            entry
            for entry in entries
            if entry.company == company
            and entry.year < target_year
            and entry.xlsx_path
            and entry.xml_path
        ),
        key=lambda entry: entry.year,
    )


def learn_prefix_rules_from_history(
    *,
    entries: list[DatasetEntry],
    company: str,
    target_year: int,
    tolerance: float = 0.01,
) -> LearnedCompanyRules:
    history_entries = _history_entries(entries, company, target_year)
    evidence: dict[str, Counter[str]] = defaultdict(Counter)
    evidence_years: dict[tuple[str, str], list[int]] = defaultdict(list)
    history_years: list[int] = []

    for entry in history_entries:
        rows = parse_zois(entry.xlsx_path, company=entry.company, year=entry.year)
        positions = parse_bilans_xml(entry.xml_path)
        totals = _leaf_prefix_totals(rows, max_depth=2)
        history_years.append(entry.year)

        for position in positions:
            learned_prefixes = _find_prefix_combo(
                code=position.code,
                expected=position.amount_current,
                totals=totals,
                tolerance=tolerance,
            )
            for prefix in learned_prefixes:
                evidence[prefix][position.code] += 1
                evidence_years[(prefix, position.code)].append(entry.year)

    prefix_rules: dict[str, LearnedPrefixRule] = {}
    for prefix, counter in evidence.items():
        if not counter:
            continue
        balance_code, count = counter.most_common(1)[0]
        if len(counter) > 1:
            # Ambiguous historical evidence is intentionally skipped.
            continue
        prefix_rules[prefix] = LearnedPrefixRule(
            prefix=prefix,
            balance_code=balance_code,
            evidence_years=evidence_years[(prefix, balance_code)],
            confidence=round(count / max(len(history_entries), 1), 2),
        )

    return LearnedCompanyRules(
        company=company,
        target_year=target_year,
        history_years=history_years,
        prefix_rules=prefix_rules,
    )


def _map_row_from_prefix_rules(row: ZoisRow, rules: LearnedCompanyRules) -> MappingDecision:
    for prefix in reversed(account_prefixes(row.account_no)):
        rule = rules.prefix_rules.get(prefix)
        if rule:
            return MappingDecision(
                account_no=row.account_no,
                balance_code=rule.balance_code,
                source=f"isolated-history:{prefix}",
                confidence=rule.confidence,
            )
    return MappingDecision(
        account_no=row.account_no,
        balance_code=None,
        source="unresolved",
        confidence=0.0,
    )


def _leaf_rows(rows: list[ZoisRow]) -> list[ZoisRow]:
    accounts = {row.account_no for row in rows}
    non_leaf_accounts = set()
    for account_no in accounts:
        parts = account_no.split("-")
        for i in range(1, len(parts)):
            non_leaf_accounts.add("-".join(parts[:i]))

    return [
        row
        for row in rows
        if row.account_no not in non_leaf_accounts
    ]


def _find_target_entry(entries: list[DatasetEntry], company: str, year: int) -> DatasetEntry:
    for entry in entries:
        if entry.company == company and entry.year == year:
            return entry
    raise ValueError(f"Nie znaleziono zestawu dla spółki={company!r}, roku={year!r}")


def _previous_year_balance(entries: list[DatasetEntry], company: str, year: int) -> dict[str, float]:
    previous_year = year - 1
    for entry in entries:
        if entry.company == company and entry.year == previous_year and entry.xml_path:
            return {
                position.code: position.amount_current
                for position in parse_bilans_xml(entry.xml_path)
            }
    return {}


def run_isolated_company_pipeline(
    *,
    entries: list[DatasetEntry],
    company: str,
    year: int,
    output_root: Path,
) -> Path:
    target_entry = _find_target_entry(entries, company, year)
    if not target_entry.xlsx_path:
        raise ValueError(f"Zestaw {company}/{year} nie ma pliku ZOiS.")

    learned = learn_prefix_rules_from_history(
        entries=entries,
        company=company,
        target_year=year,
    )
    rows = parse_zois(target_entry.xlsx_path, company=company, year=year)
    decisions = [_map_row_from_prefix_rules(row, learned) for row in rows]
    leaf_account_numbers = {row.account_no for row in _leaf_rows(rows)}
    leaf_decisions = [
        decision
        for decision in decisions
        if decision.account_no in leaf_account_numbers
    ]
    calculated_balance, code_contributions = calculate_balance_with_contributions(rows, decisions)

    run_dir = output_root / "runs" / company / str(year) / "isolated"
    run_dir.mkdir(parents=True, exist_ok=True)

    calculated_balance_path = run_dir / "calculated_balance.json"
    calculated_balance_path.write_text(
        json.dumps(calculated_balance, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    rules_path = run_dir / "learned_prefix_rules.json"
    rules_path.write_text(
        json.dumps(
            {
                "company": learned.company,
                "target_year": learned.target_year,
                "history_years": learned.history_years,
                "prefix_rules": {
                    prefix: asdict(rule)
                    for prefix, rule in sorted(learned.prefix_rules.items())
                },
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    exported_mapping = export_mapping_report(rows=rows, decisions=decisions, output_dir=run_dir)
    exported_contributions = export_code_contributions(contributions=code_contributions, output_dir=run_dir)
    bilans_xlsx_path = export_balance_xlsx(
        calculated_balance=calculated_balance,
        validation_results=[],
        output_dir=run_dir,
    )
    previous_balance = _previous_year_balance(entries, company, year)
    bilans_pdf_path = export_balance_pdf(
        company=f"{company} sp. z o.o.",
        year=year,
        current_balance=calculated_balance,
        previous_balance=previous_balance,
        output_dir=run_dir,
    )

    resolved = sum(1 for decision in decisions if decision.balance_code)
    resolved_leaf = sum(1 for decision in leaf_decisions if decision.balance_code)
    summary = {
        "company": company,
        "year": year,
        "mode": "isolated-company-history",
        "history_years": learned.history_years,
        "learned_prefix_rules": len(learned.prefix_rules),
        "zois_rows": len(rows),
        "zois_leaf_rows": len(leaf_decisions),
        "resolved_mappings": resolved,
        "unresolved_mappings": len(decisions) - resolved,
        "resolved_leaf_mappings": resolved_leaf,
        "unresolved_leaf_mappings": len(leaf_decisions) - resolved_leaf,
        "calculated_positions": len(calculated_balance),
        "calculated_balance_json": str(calculated_balance_path),
        "calculated_balance_xlsx": str(bilans_xlsx_path),
        "calculated_balance_pdf": str(bilans_pdf_path),
        "learned_prefix_rules_json": str(rules_path),
        "mapping_report_json": str(exported_mapping["json"]),
        "mapping_report_csv": str(exported_mapping["csv"]),
        "code_contributions_json": str(exported_contributions["json"]),
        "code_contributions_csv": str(exported_contributions["csv"]),
        "status": "generated_without_external_company_context",
    }
    summary_path = run_dir / "run_summary.json"
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    return summary_path
