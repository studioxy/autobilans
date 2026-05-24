from __future__ import annotations

import csv
import json
from pathlib import Path

from autobilans.mapping.service import MappingDecision, mapping_to_dict
from autobilans.models import ZoisRow


def export_mapping_report(
    *,
    rows: list[ZoisRow],
    decisions: list[MappingDecision],
    output_dir: Path,
) -> dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)

    json_path = output_dir / "mapping_report.json"
    csv_path = output_dir / "mapping_report.csv"

    payload: list[dict[str, object]] = []
    row_by_account = {row.account_no: row for row in rows}
    for decision in decisions:
        row = row_by_account[decision.account_no]
        item = {
            "account_no": row.account_no,
            "name": row.name,
            "persaldo": row.persaldo,
            "original_balance_code": row.balance_code,
            "original_additional_balance_codes": "|".join(row.additional_balance_codes),
            **mapping_to_dict(decision),
        }
        payload.append(item)

    with json_path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)

    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "account_no",
                "name",
                "persaldo",
                "original_balance_code",
                "original_additional_balance_codes",
                "balance_code",
                "source",
                "confidence",
            ],
        )
        writer.writeheader()
        for item in payload:
            writer.writerow(item)

    return {
        "json": json_path,
        "csv": csv_path,
    }
