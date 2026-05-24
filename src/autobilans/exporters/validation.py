from __future__ import annotations

import csv
import json
from pathlib import Path

from autobilans.validation.compare import ValidationItem, validation_item_to_dict


def export_validation_report(
    *,
    results: list[ValidationItem],
    output_dir: Path,
) -> dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)

    json_path = output_dir / "validation_report.json"
    csv_path = output_dir / "validation_report.csv"

    with json_path.open("w", encoding="utf-8") as handle:
        json.dump([validation_item_to_dict(item) for item in results], handle, ensure_ascii=False, indent=2)

    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["code", "expected", "actual", "delta", "matched"])
        writer.writeheader()
        for item in results:
            writer.writerow(validation_item_to_dict(item))

    return {
        "json": json_path,
        "csv": csv_path,
    }
