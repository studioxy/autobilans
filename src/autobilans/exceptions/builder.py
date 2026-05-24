from __future__ import annotations

import csv
import json
from pathlib import Path


def _load_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _load_json(path: Path) -> object:
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8"))


def build_exception_queue(
    *,
    company: str,
    year: int,
    validation_rows: list[dict[str, str]],
    gap_analysis: list[dict[str, object]],
    mapping_rows: list[dict[str, str]],
    code_contributions: dict[str, list[dict[str, object]]],
) -> list[dict[str, object]]:
    queue: list[dict[str, object]] = []
    gap_by_code = {
        str(item.get("code")): item
        for item in gap_analysis
        if isinstance(item, dict) and item.get("code")
    }

    for row in validation_rows:
        if row.get("matched") != "False":
            continue
        code = str(row["code"])
        gap_item = gap_by_code.get(code, {})
        candidate_source_codes = [
            str(item)
            for item in gap_item.get("suggested_aliases", [])
            if isinstance(item, str)
        ]
        top_contributors = []
        for source_code in candidate_source_codes:
            top_contributors.extend(code_contributions.get(source_code, [])[:5])

        queue.append(
            {
                "id": f"{company}-{year}-{code}",
                "company": company,
                "year": year,
                "kind": "validation_mismatch",
                "status": "open",
                "target_code": code,
                "expected": float(row["expected"]),
                "actual": float(row["actual"]),
                "delta": float(row["delta"]),
                "candidate_source_codes": candidate_source_codes,
                "top_contributors": top_contributors[:10],
            }
        )

    for row in mapping_rows:
        if row.get("source") != "unresolved":
            continue
        amount = float(row.get("persaldo", 0.0))
        if abs(amount) < 0.009:
            continue
        queue.append(
            {
                "id": f"{company}-{year}-unresolved-{row['account_no']}",
                "company": company,
                "year": year,
                "kind": "unresolved_account",
                "status": "open",
                "account_no": row["account_no"],
                "account_name": row.get("name", ""),
                "amount": amount,
                "original_balance_code": row.get("original_balance_code", ""),
                "original_additional_balance_codes": row.get("original_additional_balance_codes", ""),
                "candidate_source_codes": [],
                "top_contributors": [],
            }
        )

    return queue


def build_exception_queue_from_run_dir(run_dir: Path) -> list[dict[str, object]]:
    summary_path = run_dir / "run_summary.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    return build_exception_queue(
        company=str(summary["company"]),
        year=int(summary["year"]),
        validation_rows=_load_csv(run_dir / "validation_report.csv"),
        gap_analysis=_load_json(run_dir / "gap_analysis.json"),
        mapping_rows=_load_csv(run_dir / "mapping_report.csv"),
        code_contributions=_load_json(run_dir / "code_contributions.json"),
    )
