from __future__ import annotations

from pathlib import Path

import yaml

from autobilans.models import ZoisRow


def _normalize_exclude_payload(payload: dict[object, object]) -> dict[str, list[str]]:
    normalized: dict[str, list[str]] = {}
    for account_no, codes in payload.items():
        if isinstance(codes, list):
            normalized[str(account_no)] = [str(code) for code in codes]
        elif codes is not None:
            normalized[str(account_no)] = [str(codes)]
    return normalized


def load_decision_policies(
    path: str | Path,
    *,
    company: str | None = None,
    year: int | None = None,
) -> dict[str, dict[str, list[str]]]:
    policy_path = Path(path)
    if not policy_path.exists():
        return {"exclude_secondary_codes": {}}

    with policy_path.open("r", encoding="utf-8") as handle:
        payload = yaml.safe_load(handle) or {}

    root = payload.get("decision_policies", {})
    if not isinstance(root, dict) or company is None:
        return {"exclude_secondary_codes": {}}

    company_scope = root.get(company, {})
    if not isinstance(company_scope, dict):
        return {"exclude_secondary_codes": {}}

    merged: dict[str, list[str]] = {}

    all_scope = company_scope.get("all", {})
    if isinstance(all_scope, dict):
        all_excludes = all_scope.get("exclude_secondary_codes", {})
        if isinstance(all_excludes, dict):
            merged.update(_normalize_exclude_payload(all_excludes))

    if year is not None:
        year_scope = company_scope.get(str(year), {})
        if isinstance(year_scope, dict):
            year_excludes = year_scope.get("exclude_secondary_codes", {})
            if isinstance(year_excludes, dict):
                merged.update(_normalize_exclude_payload(year_excludes))

    return {"exclude_secondary_codes": merged}


def apply_secondary_code_exclusions(
    rows: list[ZoisRow],
    policies: dict[str, dict[str, list[str]]],
) -> int:
    excluded = policies.get("exclude_secondary_codes", {})
    changed = 0
    for row in rows:
        codes_to_remove = excluded.get(row.account_no, [])
        if not codes_to_remove:
            continue
        filtered = tuple(code for code in row.additional_balance_codes if code not in set(codes_to_remove))
        if filtered != row.additional_balance_codes:
            row.additional_balance_codes = filtered
            changed += 1
    return changed
