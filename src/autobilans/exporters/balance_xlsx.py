from __future__ import annotations

from pathlib import Path

import xlsxwriter

from autobilans.validation.compare import ValidationItem


def export_balance_xlsx(
    *,
    calculated_balance: dict[str, float],
    validation_results: list[ValidationItem],
    output_dir: Path,
) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    target = output_dir / "bilans.xlsx"
    workbook = xlsxwriter.Workbook(str(target))
    sheet = workbook.add_worksheet("Bilans")
    summary = workbook.add_worksheet("Podsumowanie")

    header_fmt = workbook.add_format({"bold": True, "bg_color": "#D9E1F2"})
    num_fmt = workbook.add_format({"num_format": "#,##0.00"})
    ok_fmt = workbook.add_format({"font_color": "#107C41"})
    bad_fmt = workbook.add_format({"font_color": "#C00000"})

    headers = ["Kod", "Sekcja", "Kwota", "Kwota XML", "Delta", "Zgodne"]
    for col, label in enumerate(headers):
        sheet.write(0, col, label, header_fmt)

    validation_map = {item.code: item for item in validation_results}
    rows = [
        (code, amount)
        for code, amount in calculated_balance.items()
        if "__" not in code
    ]
    rows.sort(key=lambda item: item[0])

    for row_idx, (code, amount) in enumerate(rows, start=1):
        validation_item = validation_map.get(code)
        section = "aktywa" if code.startswith("Aktywa_") else "pasywa" if code.startswith("Pasywa_") else ""
        expected = validation_item.expected if validation_item else 0.0
        delta = validation_item.delta if validation_item else amount
        matched = validation_item.matched if validation_item else False

        sheet.write(row_idx, 0, code)
        sheet.write(row_idx, 1, section)
        sheet.write_number(row_idx, 2, float(amount), num_fmt)
        sheet.write_number(row_idx, 3, float(expected), num_fmt)
        sheet.write_number(row_idx, 4, float(delta), num_fmt)
        sheet.write(row_idx, 5, "TAK" if matched else "NIE", ok_fmt if matched else bad_fmt)

    sheet.set_column(0, 0, 40)
    sheet.set_column(1, 1, 12)
    sheet.set_column(2, 4, 16)
    sheet.set_column(5, 5, 10)

    total = len(validation_results)
    matched = sum(1 for item in validation_results if item.matched)
    mismatched = total - matched

    summary.write(0, 0, "Metryka", header_fmt)
    summary.write(0, 1, "Wartość", header_fmt)
    summary.write(1, 0, "Pozycje ogółem")
    summary.write_number(1, 1, total)
    summary.write(2, 0, "Pozycje zgodne")
    summary.write_number(2, 1, matched)
    summary.write(3, 0, "Pozycje niezgodne")
    summary.write_number(3, 1, mismatched)
    summary.set_column(0, 0, 24)
    summary.set_column(1, 1, 14)

    workbook.close()
    return target

