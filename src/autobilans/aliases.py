from __future__ import annotations

from pathlib import Path

import yaml


def _normalize_alias_map(payload: dict[object, object]) -> dict[str, str | list[str]]:
    normalized: dict[str, str | list[str]] = {}
    for key, value in payload.items():
        if isinstance(value, list):
            normalized[str(key)] = [str(item) for item in value]
        else:
            normalized[str(key)] = str(value)
    return normalized


def load_xml_aliases(
    path: str | Path,
    *,
    company: str | None = None,
    year: int | None = None,
) -> dict[str, str | list[str]]:
    alias_path = Path(path)
    if not alias_path.exists():
        return {}

    with alias_path.open("r", encoding="utf-8") as handle:
        payload = yaml.safe_load(handle) or {}

    root = payload.get("xml_aliases", {})
    if not isinstance(root, dict):
        return {}

    merged: dict[str, str | list[str]] = {}

    global_aliases = root.get("global", {})
    if isinstance(global_aliases, dict):
        merged.update(_normalize_alias_map(global_aliases))

    scoped = root.get("scoped", {})
    if company and isinstance(scoped, dict):
        company_scope = scoped.get(company, {})
        if isinstance(company_scope, dict):
            company_global = company_scope.get("all", {})
            if isinstance(company_global, dict):
                merged.update(_normalize_alias_map(company_global))

            if year is not None:
                year_scope = company_scope.get(str(year), {})
                if isinstance(year_scope, dict):
                    merged.update(_normalize_alias_map(year_scope))

    if not merged and all(not isinstance(v, dict) for v in root.values()):
        merged.update(_normalize_alias_map(root))

    return merged
