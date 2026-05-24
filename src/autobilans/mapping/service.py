from __future__ import annotations

from dataclasses import asdict, dataclass

from autobilans.models import ZoisRow

from .rules import account_prefixes


@dataclass(slots=True)
class MappingDecision:
    account_no: str
    balance_code: str | None
    source: str
    confidence: float


def _decision_from_rules(
    row: ZoisRow,
    history_rules: dict[str, dict[str, str]],
    *,
    scope: str,
    account_confidence: float,
    prefix_confidence: float,
) -> MappingDecision | None:
    account_rules = history_rules.get("account", {})
    if row.account_no in account_rules:
        return MappingDecision(
            account_no=row.account_no,
            balance_code=account_rules[row.account_no],
            source=f"{scope}:account",
            confidence=account_confidence,
        )

    prefix_rules = history_rules.get("prefix", {})
    for prefix in reversed(account_prefixes(row.account_no)):
        if prefix in prefix_rules:
            return MappingDecision(
                account_no=row.account_no,
                balance_code=prefix_rules[prefix],
                source=f"{scope}:prefix:{prefix}",
                confidence=prefix_confidence,
            )

    return None


def map_row(
    row: ZoisRow,
    history_rules: dict[str, dict[str, str]],
    *,
    global_history_rules: dict[str, dict[str, str]] | None = None,
    manual_rules: dict[str, str] | None = None,
) -> MappingDecision:
    if manual_rules and row.account_no in manual_rules:
        return MappingDecision(
            account_no=row.account_no,
            balance_code=manual_rules[row.account_no],
            source="manual-rule",
            confidence=1.0,
        )

    if row.balance_code:
        return MappingDecision(
            account_no=row.account_no,
            balance_code=row.balance_code,
            source="label:S_12_1",
            confidence=1.0,
        )

    company_decision = _decision_from_rules(
        row,
        history_rules,
        scope="history-company",
        account_confidence=0.95,
        prefix_confidence=0.78,
    )
    if company_decision is not None:
        return company_decision

    if global_history_rules:
        global_decision = _decision_from_rules(
            row,
            global_history_rules,
            scope="history-global",
            account_confidence=0.88,
            prefix_confidence=0.68,
        )
        if global_decision is not None:
            return global_decision

    return MappingDecision(
        account_no=row.account_no,
        balance_code=None,
        source="unresolved",
        confidence=0.0,
    )


def map_rows(
    rows: list[ZoisRow],
    history_rules: dict[str, dict[str, str]],
    *,
    global_history_rules: dict[str, dict[str, str]] | None = None,
    manual_rules: dict[str, str] | None = None,
) -> list[MappingDecision]:
    return [
        map_row(
            row,
            history_rules,
            global_history_rules=global_history_rules,
            manual_rules=manual_rules,
        )
        for row in rows
    ]


def mapping_to_dict(decision: MappingDecision) -> dict[str, object]:
    return asdict(decision)
