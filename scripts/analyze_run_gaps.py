from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from autobilans.gap_analysis import analyze_gaps

def load_mapping_rows(path: Path) -> list[dict[str, str]]:
    return list(csv.DictReader(path.open(encoding="utf-8")))


def load_validation_rows(path: Path) -> list[dict[str, str]]:
    return list(csv.DictReader(path.open(encoding="utf-8")))


def load_calculated_balance(path: Path) -> dict[str, float]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--company", required=True)
    parser.add_argument("--year", required=True, type=int)
    parser.add_argument("--root", default=r"D:\autobilans\outputs\runs")
    args = parser.parse_args()

    run_dir = Path(args.root) / args.company / str(args.year)
    mapping_rows = load_mapping_rows(run_dir / "mapping_report.csv")
    validation_rows = load_validation_rows(run_dir / "validation_report.csv")
    calculated_balance = load_calculated_balance(run_dir / "calculated_balance.json")
    report = analyze_gaps(
        mapping_rows=mapping_rows,
        validation_rows=validation_rows,
        calculated_balance=calculated_balance,
    )

    target = run_dir / "gap_analysis.json"
    target.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Gap analysis written to: {target}")
    print(f"Mismatches analyzed: {len(report)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
