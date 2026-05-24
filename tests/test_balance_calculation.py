from autobilans.calculation.balance import calculate_balance
from autobilans.mapping.rules import build_history_rules
from autobilans.mapping.service import map_rows
from autobilans.parsers.zois import parse_zois


def test_calculate_balance_sums_direct_and_history_mappings() -> None:
    rows = parse_zois(r"D:\autobilans\8spzoo\2025\zois2025.xlsx")
    rules = build_history_rules(rows)
    decisions = map_rows(rows, rules)

    totals = calculate_balance(rows, decisions)

    assert round(totals["BAAII1a"], 2) == 816093.13
    assert round(totals["BAAII1b"], 2) == 1889179.52
    assert round(totals["BABIII1c1_SPKR"], 2) == 389462.15
    assert round(totals["BPAI"], 2) == 5000.0
    assert round(totals["BPAII_INN"], 2) == 2557980.38


def test_calculate_balance_includes_additional_balance_codes() -> None:
    rows = parse_zois(r"D:\autobilans\metro\2025\zois2025.xlsx")
    rules = build_history_rules(rows)
    decisions = map_rows(rows, rules)

    totals = calculate_balance(rows, decisions)

    assert round(totals["BPBIII3g__NEG"], 2) == 4943.05
    assert round(totals["BPBIII3g__POS"], 2) == 5224.12
