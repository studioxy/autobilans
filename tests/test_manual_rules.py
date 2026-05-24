from autobilans.manual_rules import load_manual_rules
from autobilans.mapping.service import map_row
from autobilans.models import ZoisRow


def test_load_manual_rules_reads_company_scope() -> None:
    rules = load_manual_rules(r"D:\autobilans\config\manual_rules.yaml", company="metro")
    assert isinstance(rules, dict)


def test_load_manual_rules_merges_all_and_year_scope(tmp_path) -> None:
    target = tmp_path / "manual_rules.yaml"
    target.write_text(
        """
manual_rules:
  metro:
    all:
      201-1: BASE
    "2025":
      201-2: YEAR
""".strip(),
        encoding="utf-8",
    )

    rules = load_manual_rules(target, company="metro", year=2025)

    assert rules == {"201-1": "BASE", "201-2": "YEAR"}


def test_load_manual_rules_supports_legacy_company_scope(tmp_path) -> None:
    target = tmp_path / "manual_rules.yaml"
    target.write_text(
        """
manual_rules:
  metro:
    201-1: BASE
""".strip(),
        encoding="utf-8",
    )

    rules = load_manual_rules(target, company="metro", year=2025)

    assert rules == {"201-1": "BASE"}


def test_map_row_prefers_manual_rule_over_history() -> None:
    row = ZoisRow(
        account_no="999-1",
        name="Ręczne konto",
        name_2="",
        closing_debit=0.0,
        closing_credit=1.0,
        persaldo=-1.0,
        balance_code=None,
    )

    decision = map_row(
        row,
        {"account": {"999-1": "OLD"}, "prefix": {}},
        manual_rules={"999-1": "NEW"},
    )

    assert decision.balance_code == "NEW"
    assert decision.source == "manual-rule"
