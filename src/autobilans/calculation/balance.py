from __future__ import annotations

from collections import defaultdict
from typing import Any

from autobilans.mapping.service import MappingDecision
from autobilans.models import ZoisRow


def _row_amount(row: ZoisRow) -> float:
    return float(row.persaldo)


def _normalize_balance_code(code: str) -> str:
    if code.endswith("_W") or code.endswith("_U"):
        return code[:-2]
    return code


def _normalize_amount(code: str, amount: float) -> float:
    # Equity and liability positions in ZOiS often arrive with opposite sign to XML balance output.
    if code.startswith("BP"):
        return abs(amount)
    return amount


def _decision_codes(row: ZoisRow, decision: MappingDecision) -> tuple[str, ...]:
    codes: list[str] = []
    if decision.balance_code:
        codes.append(decision.balance_code)
    codes.extend(row.additional_balance_codes)
    return tuple(dict.fromkeys(codes))


def calculate_balance_with_contributions(
    rows: list[ZoisRow],
    decisions: list[MappingDecision],
) -> tuple[dict[str, float], dict[str, list[dict[str, Any]]]]:
    row_by_account = {row.account_no: row for row in rows}

    non_leaf_accounts = set()
    for account_no in row_by_account:
        parts = account_no.split("-")
        for i in range(1, len(parts)):
            non_leaf_accounts.add("-".join(parts[:i]))

    totals: dict[str, float] = defaultdict(float)
    contributions: dict[str, list[dict[str, Any]]] = defaultdict(list)

    for decision in decisions:
        row = row_by_account[decision.account_no]
        decision_codes = _decision_codes(row, decision)
        if not decision_codes:
            continue
        if row.account_no in non_leaf_accounts:
            continue
        raw_amount = _row_amount(row)
        for code in decision_codes:
            normalized_code = _normalize_balance_code(code)
            normalized_amount = _normalize_amount(normalized_code, raw_amount)
            totals[normalized_code] += normalized_amount
            contributions[normalized_code].append(
                {
                    "account_no": row.account_no,
                    "name": row.name,
                    "source_code": code,
                    "raw_amount": raw_amount,
                    "bucket_amount": normalized_amount,
                }
            )
            if raw_amount > 0:
                totals[f"{normalized_code}__POS"] += raw_amount
                contributions[f"{normalized_code}__POS"].append(
                    {
                        "account_no": row.account_no,
                        "name": row.name,
                        "source_code": code,
                        "raw_amount": raw_amount,
                        "bucket_amount": raw_amount,
                    }
                )
            elif raw_amount < 0:
                totals[f"{normalized_code}__NEG"] += abs(raw_amount)
                contributions[f"{normalized_code}__NEG"].append(
                    {
                        "account_no": row.account_no,
                        "name": row.name,
                        "source_code": code,
                        "raw_amount": raw_amount,
                        "bucket_amount": abs(raw_amount),
                    }
                )

    return dict(totals), {key: value for key, value in contributions.items()}


def calculate_balance(rows: list[ZoisRow], decisions: list[MappingDecision]) -> dict[str, float]:
    totals, _ = calculate_balance_with_contributions(rows, decisions)
    return totals
