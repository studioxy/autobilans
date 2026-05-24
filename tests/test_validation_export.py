from pathlib import Path

from autobilans.exporters.validation import export_validation_report
from autobilans.validation.compare import ValidationItem


def test_export_validation_report_writes_json_and_csv(tmp_path: Path) -> None:
    results = [
        ValidationItem(code="A", expected=10.0, actual=10.0, delta=0.0, matched=True),
        ValidationItem(code="B", expected=20.0, actual=15.0, delta=-5.0, matched=False),
    ]

    paths = export_validation_report(results=results, output_dir=tmp_path)

    assert paths["json"].exists()
    assert paths["csv"].exists()
    assert "validation_report.json" in str(paths["json"])
    assert "validation_report.csv" in str(paths["csv"])
