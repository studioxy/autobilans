from autobilans.aliases import load_xml_aliases


def test_load_xml_aliases_reads_config_file() -> None:
    aliases = load_xml_aliases(r"config/xml_aliases.yaml", company="8spzoo", year=2025)

    assert aliases["Aktywa_A_II_1_A"] == "BAAII1a"
    assert aliases["Aktywa_B_III_1_C_1"] == ["BABIII1c1_SPKR__POS", "BABIII1c2_ISP"]


def test_load_xml_aliases_merges_company_scope() -> None:
    aliases = load_xml_aliases(r"config/xml_aliases.yaml", company="oksanbud", year=2025)

    assert aliases["Pasywa_A_I"] == "BPAI"
    assert aliases["Aktywa_B_IV"] == ["BABIV", "RPHI_RKKI_POZ"]
