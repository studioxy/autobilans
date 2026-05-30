from autobilans.mapping.rules import build_history_rules
from autobilans.mapping.service import map_row
from autobilans.models import ZoisRow
from autobilans.parsers.zois import parse_zois


def test_build_history_rules_learns_account_and_prefix_rules() -> None:
    rows = parse_zois(r"metro/2025/zois2025.xlsx")
    rules = build_history_rules(rows)

    assert rules["account"]["011-3-01/2021"] == "BAAII1d_W"
    assert rules["account"]["071-3-01/2021"] == "BAAII1d_U"
    assert rules["prefix"]["011-3"] == "BAAII1d_W"
    assert rules["prefix"]["071-3"] == "BAAII1d_U"


def test_map_row_prefers_direct_label_over_history() -> None:
    rows = parse_zois(r"8spzoo/2025/zois2025.xlsx")
    rules = build_history_rules(rows)
    row = next(item for item in rows if item.account_no == "011-0-01")

    decision = map_row(row, rules)

    assert decision.balance_code == "BAAII1a_W"
    assert decision.source == "label:S_12_1"
    assert decision.confidence == 1.0


def test_map_row_uses_prefix_history_for_unlabeled_similar_account() -> None:
    rows = parse_zois(r"metro/2025/zois2025.xlsx")
    rules = build_history_rules(rows)
    unlabeled = ZoisRow(
        account_no="011-3-99/TEST",
        name="Testowy środek transportu",
        name_2="",
        closing_debit=123.0,
        closing_credit=0.0,
        persaldo=123.0,
        balance_code=None,
    )

    decision = map_row(unlabeled, rules)

    assert decision.balance_code == "BAAII1d_W"
    assert decision.source == "history-company:prefix:011-3"
    assert decision.confidence == 0.78


def test_map_row_can_use_global_history_when_company_history_is_missing() -> None:
    global_rows = parse_zois(r"metro/2025/zois2025.xlsx")
    company_rules = build_history_rules([])
    global_rules = build_history_rules(global_rows)
    unlabeled = ZoisRow(
        account_no="011-3-01/NEW",
        name="Nowy środek transportu",
        name_2="",
        closing_debit=100.0,
        closing_credit=0.0,
        persaldo=100.0,
        balance_code=None,
    )

    decision = map_row(unlabeled, company_rules, global_history_rules=global_rules)

    assert decision.balance_code == "BAAII1d_W"
    assert decision.source == "history-global:prefix:011-3"
    assert decision.confidence == 0.68


def test_map_row_returns_unresolved_when_no_rule_matches() -> None:
    rules = build_history_rules([])
    unknown = ZoisRow(
        account_no="999-XYZ",
        name="Nieznane konto",
        name_2="",
        closing_debit=0.0,
        closing_credit=10.0,
        persaldo=-10.0,
        balance_code=None,
    )

    decision = map_row(unknown, rules)

    assert decision.balance_code is None
    assert decision.source == "unresolved"
    assert decision.confidence == 0.0
