from autobilans.exceptions.decisions import suggest_decisions, validate_decisions


def test_suggest_decisions_prefers_original_code_for_unresolved_account() -> None:
    queue = [
        {
            "id": "x-1",
            "kind": "unresolved_account",
            "account_no": "201-1",
            "original_balance_code": "Aktywa_A_IV",
        }
    ]

    suggested = suggest_decisions(queue)

    assert len(suggested) == 1
    assert suggested[0]["action"] == "force_target_code"
    assert suggested[0]["target_code"] == "Aktywa_A_IV"


def test_suggest_decisions_builds_exclude_secondary_from_top_contributor() -> None:
    queue = [
        {
            "id": "x-2",
            "kind": "validation_mismatch",
            "target_code": "Pasywa_B_III_3_D_1",
            "top_contributors": [
                {
                    "account_no": "202-1",
                    "source_code": "BPBIII3d_D12",
                }
            ],
        }
    ]

    suggested = suggest_decisions(queue)

    assert len(suggested) == 1
    assert suggested[0]["action"] == "exclude_secondary_code"
    assert suggested[0]["account_no"] == "202-1"
    assert suggested[0]["secondary_code"] == "BPBIII3d_D12"


def test_validate_decisions_rejects_invalid_target_code_and_skips_duplicates() -> None:
    decisions = [
        {"action": "force_target_code", "account_no": "201-1", "target_code": "X"},
        {"action": "exclude_secondary_code", "account_no": "201-1", "secondary_code": "BP"},
        {"action": "exclude_secondary_code", "account_no": "201-1", "secondary_code": "BP"},
    ]

    result = validate_decisions(decisions, known_target_codes={"Aktywa_A_IV"})

    assert len(result.errors) == 1
    assert "Unknown target_code" in result.errors[0]
    assert len(result.valid) == 1
    assert result.duplicate_count == 1
