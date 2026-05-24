from autobilans.gap_analysis import analyze_gaps


def test_analyze_gaps_suggests_exact_alias_bucket() -> None:
    mapping_rows = [
        {
            "account_no": "202-1",
            "name": "Dostawca A",
            "persaldo": "-100.0",
            "balance_code": "BABII3a_D12",
            "source": "label:S_12_1",
        }
    ]
    validation_rows = [
        {
            "code": "Pasywa_B_III_3_D_1",
            "expected": "100.0",
            "actual": "0.0",
            "delta": "-100.0",
            "matched": "False",
        }
    ]
    calculated_balance = {
        "BABII3a_D12": -100.0,
        "BABII3a_D12__NEG": 100.0,
    }

    result = analyze_gaps(
        mapping_rows=mapping_rows,
        validation_rows=validation_rows,
        calculated_balance=calculated_balance,
    )

    assert result[0]["suggested_aliases"] == ["BABII3a_D12__NEG"]


def test_analyze_gaps_ignores_already_matched_rows() -> None:
    result = analyze_gaps(
        mapping_rows=[],
        validation_rows=[
            {
                "code": "Aktywa_B_IV",
                "expected": "10.0",
                "actual": "10.0",
                "delta": "0.0",
                "matched": "True",
            }
        ],
        calculated_balance={"BABIV": 10.0},
    )

    assert result == []
