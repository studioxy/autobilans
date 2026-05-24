from pathlib import Path


def test_run_all_script_exists() -> None:
    assert Path(r"D:\autobilans\scripts\run_all_pipelines.py").exists()
