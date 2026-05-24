import csv
from pathlib import Path

from autobilans.exporters.mapping import export_mapping_report
from autobilans.mapping.service import MappingDecision
from autobilans.models import ZoisRow


def test_export_mapping_report_writes_json_and_csv(tmp_path: Path) -> None:
    rows = [
        ZoisRow(
            account_no="100",
            name="Kasa",
            name_2="",
            closing_debit=10.0,
            closing_credit=0.0,
            persaldo=10.0,
            balance_code="BABIII1c1_SPKR",
            additional_balance_codes=("BPBIII3g",),
        )
    ]
    decisions = [
        MappingDecision(
            account_no="100",
            balance_code="BABIII1c1_SPKR",
            source="label:S_12_1",
            confidence=1.0,
        )
    ]

    paths = export_mapping_report(rows=rows, decisions=decisions, output_dir=tmp_path)

    assert paths["json"].exists()
    assert paths["csv"].exists()
    assert "mapping_report.json" in str(paths["json"])
    assert "mapping_report.csv" in str(paths["csv"])

    with paths["csv"].open("r", encoding="utf-8", newline="") as handle:
        row = next(csv.DictReader(handle))

    assert row["original_additional_balance_codes"] == "BPBIII3g"
