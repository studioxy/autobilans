import json
from pathlib import Path

import yaml

from autobilans.exceptions.builder import build_exception_queue
from autobilans.exceptions.store import (
    apply_exclude_secondary_code_decision,
    apply_force_target_code_decision,
    append_decision_log,
)


def test_build_exception_queue_collects_mismatches_and_unresolved_accounts() -> None:
    validation_rows = [
        {
            "code": "Pasywa_B_III_3_D_1",
            "expected": "15493.2",
            "actual": "0.0",
            "delta": "-15493.2",
            "matched": "False",
        }
    ]
    gap_analysis = [
        {
            "code": "Pasywa_B_III_3_D_1",
            "expected": 15493.2,
            "actual": 0.0,
            "delta": -15493.2,
            "suggested_aliases": ["BPBIII3d_D12__NEG"],
            "candidate_combos": [],
        }
    ]
    mapping_rows = [
        {
            "account_no": "999-1",
            "name": "Nieopisane konto",
            "persaldo": "120.0",
            "original_balance_code": "",
            "original_additional_balance_codes": "",
            "balance_code": "",
            "source": "unresolved",
            "confidence": "0.0",
        }
    ]
    code_contributions = {
        "BPBIII3d_D12__NEG": [
            {
                "account_no": "202-1",
                "name": "Dostawca A",
                "source_code": "BPBIII3d_D12",
                "raw_amount": -100.0,
                "bucket_amount": 100.0,
            }
        ]
    }

    queue = build_exception_queue(
        company="metro",
        year=2025,
        validation_rows=validation_rows,
        gap_analysis=gap_analysis,
        mapping_rows=mapping_rows,
        code_contributions=code_contributions,
    )

    assert len(queue) == 2
    assert queue[0]["kind"] == "validation_mismatch"
    assert queue[0]["candidate_source_codes"] == ["BPBIII3d_D12__NEG"]
    assert queue[0]["top_contributors"][0]["account_no"] == "202-1"
    assert queue[1]["kind"] == "unresolved_account"
    assert queue[1]["account_no"] == "999-1"


def test_apply_force_target_code_decision_updates_manual_rules_by_year(tmp_path: Path) -> None:
    target = tmp_path / "manual_rules.yaml"
    target.write_text("manual_rules: {}/n", encoding="utf-8")

    apply_force_target_code_decision(
        path=target,
        company="metro",
        year=2025,
        account_no="201-2-1-XYZ",
        target_code="Aktywa_A_III_3",
    )

    payload = yaml.safe_load(target.read_text(encoding="utf-8"))
    assert payload["manual_rules"]["metro"]["2025"]["201-2-1-XYZ"] == "Aktywa_A_III_3"


def test_append_decision_log_writes_audit_entry(tmp_path: Path) -> None:
    log_path = append_decision_log(
        output_dir=tmp_path,
        entry={
            "company": "metro",
            "year": 2025,
            "account_no": "201-2-1-XYZ",
            "action": "force_target_code",
        },
    )

    payload = json.loads(log_path.read_text(encoding="utf-8"))
    assert payload[0]["action"] == "force_target_code"


def test_apply_exclude_secondary_code_decision_updates_policy_file(tmp_path: Path) -> None:
    target = tmp_path / "decision_policies.yaml"
    target.write_text("decision_policies: {}/n", encoding="utf-8")

    apply_exclude_secondary_code_decision(
        path=target,
        company="metro",
        year=2025,
        account_no="201-2-1-XYZ",
        secondary_code="BPBIII3d_D12",
    )

    payload = yaml.safe_load(target.read_text(encoding="utf-8"))
    codes = payload["decision_policies"]["metro"]["2025"]["exclude_secondary_codes"]["201-2-1-XYZ"]
    assert codes == ["BPBIII3d_D12"]
