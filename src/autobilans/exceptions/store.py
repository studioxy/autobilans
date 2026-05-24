from __future__ import annotations

import json
from pathlib import Path

import yaml


def _load_yaml(path: Path) -> dict[str, object]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def _write_yaml(path: Path, payload: dict[str, object]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        yaml.safe_dump(payload, handle, allow_unicode=True, sort_keys=False)


def apply_force_target_code_decision(
    *,
    path: str | Path,
    company: str,
    year: int,
    account_no: str,
    target_code: str,
) -> Path:
    rules_path = Path(path)
    payload = _load_yaml(rules_path)
    root = payload.setdefault("manual_rules", {})
    company_scope = root.setdefault(company, {})
    if not isinstance(company_scope, dict):
        company_scope = {}
        root[company] = company_scope
    year_scope = company_scope.setdefault(str(year), {})
    if not isinstance(year_scope, dict):
        year_scope = {}
        company_scope[str(year)] = year_scope
    year_scope[str(account_no)] = str(target_code)
    _write_yaml(rules_path, payload)
    return rules_path


def apply_exclude_secondary_code_decision(
    *,
    path: str | Path,
    company: str,
    year: int,
    account_no: str,
    secondary_code: str,
) -> Path:
    policies_path = Path(path)
    payload = _load_yaml(policies_path)
    root = payload.setdefault("decision_policies", {})
    company_scope = root.setdefault(company, {})
    if not isinstance(company_scope, dict):
        company_scope = {}
        root[company] = company_scope

    year_scope = company_scope.setdefault(str(year), {})
    if not isinstance(year_scope, dict):
        year_scope = {}
        company_scope[str(year)] = year_scope

    exclude_scope = year_scope.setdefault("exclude_secondary_codes", {})
    if not isinstance(exclude_scope, dict):
        exclude_scope = {}
        year_scope["exclude_secondary_codes"] = exclude_scope

    account_scope = exclude_scope.setdefault(str(account_no), [])
    if not isinstance(account_scope, list):
        account_scope = []
        exclude_scope[str(account_no)] = account_scope

    if str(secondary_code) not in account_scope:
        account_scope.append(str(secondary_code))

    _write_yaml(policies_path, payload)
    return policies_path


def append_decision_log(*, output_dir: str | Path, entry: dict[str, object]) -> Path:
    target_dir = Path(output_dir)
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / "decision_log.json"
    payload: list[dict[str, object]]
    if target.exists():
        payload = json.loads(target.read_text(encoding="utf-8"))
    else:
        payload = []
    payload.append(entry)
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return target


def load_decision_file(path: str | Path) -> list[dict[str, object]]:
    target = Path(path)
    return json.loads(target.read_text(encoding="utf-8"))
