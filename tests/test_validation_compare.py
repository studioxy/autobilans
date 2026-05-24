from autobilans.calculation.balance import calculate_balance
from autobilans.mapping.rules import build_history_rules
from autobilans.mapping.service import map_rows
from autobilans.parsers.bilans_xml import parse_bilans_xml
from autobilans.parsers.zois import parse_zois
from autobilans.validation.compare import compare_balance_to_xml, summarize_validation


def test_compare_balance_to_xml_matches_known_positions_with_aliases() -> None:
    rows = parse_zois(r"D:\autobilans\8spzoo\2025\zois2025.xlsx")
    decisions = map_rows(rows, build_history_rules(rows))
    totals = calculate_balance(rows, decisions)
    positions = parse_bilans_xml(r"D:\autobilans\8spzoo\2025\2026_01_24_SF_8_2025.xml")

    results = compare_balance_to_xml(
        totals,
        positions,
        mapping_aliases={
            "Aktywa_A_II_1_A": "BAAII1a",
            "Aktywa_A_II_1_B": "BAAII1b",
            "Aktywa_B_III_1_C_1": "BABIII1c1_SPKR",
            "Pasywa_A_I": "BPAI",
            "Pasywa_A_II": "BPAII_INN",
            "Pasywa_A_VI": "BPAVI",
        },
    )

    ground = next(item for item in results if item.code == "Aktywa_A_II_1_A")
    building = next(item for item in results if item.code == "Aktywa_A_II_1_B")
    cash = next(item for item in results if item.code == "Aktywa_B_III_1_C_1")
    equity = next(item for item in results if item.code == "Pasywa_A_I")
    reserve = next(item for item in results if item.code == "Pasywa_A_II")
    result = next(item for item in results if item.code == "Pasywa_A_VI")

    assert ground.matched is True
    assert building.matched is True
    assert cash.matched is True
    assert equity.matched is True
    assert reserve.matched is True
    assert result.matched is True


def test_summarize_validation_counts_matches_and_mismatches() -> None:
    rows = parse_zois(r"D:\autobilans\8spzoo\2025\zois2025.xlsx")
    decisions = map_rows(rows, build_history_rules(rows))
    totals = calculate_balance(rows, decisions)
    positions = parse_bilans_xml(r"D:\autobilans\8spzoo\2025\2026_01_24_SF_8_2025.xml")

    results = compare_balance_to_xml(
        totals,
        positions,
        mapping_aliases={"Aktywa_A_II_1_A": "BAAII1a"},
    )
    summary = summarize_validation(results)

    assert summary["total_positions"] == len(results)
    assert summary["matched_positions"] >= 1
    assert summary["mismatched_positions"] >= 1


def test_compare_balance_to_xml_supports_composite_aliases() -> None:
    positions = parse_bilans_xml(r"D:\autobilans\metro\2025\2026-01-30-SF-metro-2025 jw.xml")
    results = compare_balance_to_xml(
        {
            "BABIII1c1_SPKR__POS": 697396.78,
            "BABIII1c2_ISP": 18500.0,
        },
        positions,
        mapping_aliases={
            "Aktywa_B_III_1_C_1": ["BABIII1c1_SPKR__POS", "BABIII1c2_ISP"],
        },
    )
    cash = next(item for item in results if item.code == "Aktywa_B_III_1_C_1")
    assert cash.matched is True
