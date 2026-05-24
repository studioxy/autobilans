from autobilans.decision_policies import apply_secondary_code_exclusions, load_decision_policies
from autobilans.models import ZoisRow


def test_load_decision_policies_merges_all_and_year(tmp_path) -> None:
    target = tmp_path / "decision_policies.yaml"
    target.write_text(
        """
decision_policies:
  metro:
    all:
      exclude_secondary_codes:
        "201-1":
          - BPBIII3d_D12
    "2025":
      exclude_secondary_codes:
        "202-1":
          - BPBIII3g
""".strip(),
        encoding="utf-8",
    )

    policies = load_decision_policies(target, company="metro", year=2025)

    assert policies["exclude_secondary_codes"]["201-1"] == ["BPBIII3d_D12"]
    assert policies["exclude_secondary_codes"]["202-1"] == ["BPBIII3g"]


def test_apply_secondary_code_exclusions_removes_only_configured_codes() -> None:
    rows = [
        ZoisRow(
            account_no="201-1",
            name="A",
            name_2="",
            closing_debit=0.0,
            closing_credit=1.0,
            persaldo=-1.0,
            balance_code="BABII3a_D12",
            additional_balance_codes=("BPBIII3d_D12", "BPBIII3g"),
        ),
        ZoisRow(
            account_no="202-1",
            name="B",
            name_2="",
            closing_debit=0.0,
            closing_credit=1.0,
            persaldo=-1.0,
            balance_code="BABII3a_D12",
            additional_balance_codes=("BPBIII3d_D12",),
        ),
    ]
    policies = {
        "exclude_secondary_codes": {
            "201-1": ["BPBIII3d_D12"],
        }
    }

    changed = apply_secondary_code_exclusions(rows, policies)

    assert changed == 1
    assert rows[0].additional_balance_codes == ("BPBIII3g",)
    assert rows[1].additional_balance_codes == ("BPBIII3d_D12",)
