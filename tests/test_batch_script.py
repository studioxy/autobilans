from pathlib import Path


def test_run_all_script_exists() -> None:
    assert Path(r"scripts/run_all_pipelines.py").exists()
