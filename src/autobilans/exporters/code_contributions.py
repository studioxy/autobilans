from __future__ import annotations

import csv
import json
from pathlib import Path


def export_code_contributions(
    *,
    contributions: dict[str, list[dict[str, object]]],
    output_dir: Path,
) -> dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)

    json_path = output_dir / "code_contributions.json"
    csv_path = output_dir / "code_contributions.csv"

    with json_path.open("w", encoding="utf-8") as handle:
        json.dump(contributions, handle, ensure_ascii=False, indent=2)

    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "code",
                "account_no",
                "name",
                "source_code",
                "raw_amount",
                "bucket_amount",
            ],
        )
        writer.writeheader()
        for code, items in contributions.items():
            filtered_items = [
                item for item in items if abs(float(item.get("bucket_amount", 0.0))) > 0.009
            ]
            for item in sorted(
                filtered_items,
                key=lambda entry: abs(float(entry.get("bucket_amount", 0.0))),
                reverse=True,
            ):
                writer.writerow({"code": code, **item})

    return {
        "json": json_path,
        "csv": csv_path,
    }
