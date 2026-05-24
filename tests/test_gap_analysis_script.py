from pathlib import Path


def test_gap_analysis_script_exists() -> None:
    assert Path(r"scripts/analyze_run_gaps.py").exists()
