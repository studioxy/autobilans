from autobilans.parsers.zois import parse_zois


def test_parse_zois_reads_real_rows() -> None:
    rows = parse_zois(
        r"D:\autobilans\8spzoo\2025\zois2025.xlsx",
        company="8spzoo",
        year=2025,
    )

    assert len(rows) == 73

    row = next(item for item in rows if item.account_no == "011-0-01")
    assert row.closing_debit == 816093.13
    assert row.closing_credit == 0.0
    assert row.persaldo == 816093.13
    assert row.balance_code == "BAAII1a_W"
    assert row.company == "8spzoo"
    assert row.year == 2025


def test_parse_zois_keeps_unlabeled_rows_as_none() -> None:
    rows = parse_zois(r"D:\autobilans\metro\2025\zois2025.xlsx")

    row = next(item for item in rows if item.account_no == "011")
    assert row.balance_code is None


def test_parse_zois_reads_additional_balance_codes() -> None:
    rows = parse_zois(r"D:\autobilans\metro\2025\zois2025.xlsx")

    row = next(item for item in rows if item.account_no == "220-01-01")
    assert row.balance_code == "BABII3b"
    assert row.additional_balance_codes == ("BPBIII3g",)


def test_parse_zois_supports_short_format_without_mapping_columns() -> None:
    rows = parse_zois(r"D:\autobilans\nordoen\2026\zois 2026.xlsx")

    row = next(item for item in rows if item.account_no == "011")
    assert row.name == "Środki trwałe"
    assert row.name_2 == ""
    assert row.closing_debit == 7893230.69
    assert row.closing_credit == 0.0
    assert row.persaldo == 7893230.69
    assert row.balance_code is None
