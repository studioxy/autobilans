from autobilans.parsers.bilans_xml import parse_bilans_xml


def test_parse_bilans_xml_reads_leaf_positions() -> None:
    positions = parse_bilans_xml(r"8spzoo/2025/2026_01_24_SF_8_2025.xml")

    assert positions

    ground = next(item for item in positions if item.code == "Aktywa_A_II_1_A")
    assert ground.section == "aktywa"
    assert ground.amount_current == 816093.13
    assert ground.amount_previous == 816093.13

    cash = next(item for item in positions if item.code == "Aktywa_B_III_1_C_1")
    assert cash.amount_current == 389462.15
    assert cash.amount_previous == 97597.49


def test_parse_bilans_xml_reads_pasywa_positions() -> None:
    positions = parse_bilans_xml(r"metro/2025/2026-01-30-SF-metro-2025 jw.xml")

    liability = next(item for item in positions if item.code == "Pasywa_B_III_3_A")
    assert liability.section == "pasywa"
    assert liability.amount_current == 50849.58
    assert liability.amount_previous == 23904.50
