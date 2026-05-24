from __future__ import annotations

from pathlib import Path

import yaml


def _normalize_rule_map(payload: dict[object, object]) -> dict[str, str]:
    return {str(key): str(value) for key, value in payload.items()}


def load_manual_rules(
    path: str | Path,
    *,
    company: str | None = None,
    year: int | None = None,
) -> dict[str, str]:
    rules_path = Path(path)
    if not rules_path.exists():
        return {}

    with rules_path.open("r", encoding="utf-8") as handle:
        payload = yaml.safe_load(handle) or {}

    root = payload.get("manual_rules", {})
    if not isinstance(root, dict):
        return {}

    if company is None:
        return {}

    company_rules = root.get(company, {})
    if not isinstance(company_rules, dict):
        return {}

    # Backward-compatible flat scope:
    # manual_rules:
    #   metro:
    #     201-1: CODE
    if all(not isinstance(value, dict) for value in company_rules.values()):
        return _normalize_rule_map(company_rules)

    merged: dict[str, str] = {}

    all_rules = company_rules.get("all", {})
    if isinstance(all_rules, dict):
        merged.update(_normalize_rule_map(all_rules))

    if year is not None:
        year_rules = company_rules.get(str(year), {})
        if isinstance(year_rules, dict):
            merged.update(_normalize_rule_map(year_rules))

    return merged
