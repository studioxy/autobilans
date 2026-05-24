from pathlib import Path

from autobilans.dataset_index import build_dataset_index
from autobilans.isolated_pipeline import learn_prefix_rules_from_history, run_isolated_company_pipeline


def test_learn_prefix_rules_from_nordoen_history_uses_only_company_history() -> None:
    entries = build_dataset_index(Path(r"D:\autobilans"))

    learned = learn_prefix_rules_from_history(
        entries=entries,
        company="nordoen",
        target_year=2026,
    )

    assert learned.prefix_rules["011-0"].balance_code == "Aktywa_A_II_1_A"
    assert learned.prefix_rules["304"].balance_code == "Aktywa_A_II_2"
    assert learned.prefix_rules["803"].balance_code == "Pasywa_A_I"
    assert learned.history_years == [2024, 2025]


def test_run_isolated_company_pipeline_generates_nordoen_2026_outputs(tmp_path: Path) -> None:
    entries = build_dataset_index(Path(r"D:\autobilans"))

    summary_path = run_isolated_company_pipeline(
        entries=entries,
        company="nordoen",
        year=2026,
        output_root=tmp_path,
    )

    run_dir = summary_path.parent
    assert summary_path.exists()
    assert (run_dir / "bilans.xlsx").exists()
    assert (run_dir / "bilans.pdf").exists()
    assert (run_dir / "learned_prefix_rules.json").exists()
    assert (run_dir / "mapping_report.csv").exists()
