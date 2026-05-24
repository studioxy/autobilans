import csv
from pathlib import Path

from autobilans.calculation.balance import calculate_balance_with_contributions
from autobilans.exporters.code_contributions import export_code_contributions
from autobilans.mapping.service import MappingDecision
from autobilans.models import ZoisRow


def test_calculate_balance_with_contributions_tracks_primary_and_secondary_codes() -> None:
    rows = [
        ZoisRow(
            account_no="202-1",
            name="Dostawca A",
            name_2="",
            closing_debit=0.0,
            closing_credit=10.0,
            persaldo=-10.0,
            balance_code="BABII3a_D12",
            additional_balance_codes=("BPBIII3d_D12",),
        )
    ]
    decisions = [
        MappingDecision(
            account_no="202-1",
            balance_code="BABII3a_D12",
            source="label:S_12_1",
            confidence=1.0,
        )
    ]

    totals, contributions = calculate_balance_with_contributions(rows, decisions)

    assert totals["BABII3a_D12__NEG"] == 10.0
    assert totals["BPBIII3d_D12__NEG"] == 10.0
    assert contributions["BPBIII3d_D12__NEG"][0]["account_no"] == "202-1"


def test_export_code_contributions_writes_json_and_csv(tmp_path: Path) -> None:
    contributions = {
        "BPBIII3d_D12__NEG": [
            {
                "account_no": "202-1",
                "name": "Dostawca A",
                "source_code": "BPBIII3d_D12",
                "raw_amount": -10.0,
                "bucket_amount": 10.0,
            }
        ]
    }

    paths = export_code_contributions(contributions=contributions, output_dir=tmp_path)

    assert paths["json"].exists()
    assert paths["csv"].exists()
    assert "code_contributions.json" in str(paths["json"])
    assert "code_contributions.csv" in str(paths["csv"])


def test_export_code_contributions_skips_zero_rows(tmp_path: Path) -> None:
    contributions = {
        "BPBIII3d_D12": [
            {
                "account_no": "202-0",
                "name": "Zero",
                "source_code": "BPBIII3d_D12",
                "raw_amount": 0.0,
                "bucket_amount": 0.0,
            },
            {
                "account_no": "202-1",
                "name": "Nonzero",
                "source_code": "BPBIII3d_D12",
                "raw_amount": -10.0,
                "bucket_amount": 10.0,
            },
        ]
    }

    paths = export_code_contributions(contributions=contributions, output_dir=tmp_path)

    with paths["csv"].open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))

    assert len(rows) == 1
    assert rows[0]["account_no"] == "202-1"
