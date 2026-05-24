from pathlib import Path

from autobilans.exporters import export_balance_pdf


def test_export_balance_pdf_writes_printable_balance(tmp_path: Path) -> None:
    target = export_balance_pdf(
        company="NORDOEN SP. Z O.O.",
        year=2026,
        current_balance={
            "Aktywa_A_I_3": 100.0,
            "Pasywa_A_I": -100.0,
        },
        previous_balance={
            "Aktywa_A_I_3": 80.0,
            "Pasywa_A_I": 80.0,
        },
        output_dir=tmp_path,
    )

    assert target.exists()
    assert target.read_bytes().startswith(b"%PDF")
