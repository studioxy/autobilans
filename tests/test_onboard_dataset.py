from pathlib import Path

from autobilans.cli import cmd_onboard_dataset


def test_cmd_onboard_dataset_creates_folder_and_copies_files(tmp_path: Path) -> None:
    data_root = tmp_path / "data"
    output_root = tmp_path / "outputs"
    config_path = tmp_path / "local.yaml"
    config_path.write_text(
        (
            "paths:/n"
            f"  data_root: {data_root}/n"
            f"  output_root: {output_root}/n"
            "pipeline:/n"
            "  default_company: demo/n"
            "  default_year: 2025/n"
        ),
        encoding="utf-8",
    )
    source_xlsx = tmp_path / "input.xlsx"
    source_xlsx.write_text("xlsx", encoding="utf-8")

    code = cmd_onboard_dataset(
        config_path=str(config_path),
        company="newco",
        year=2026,
        xlsx=str(source_xlsx),
        xml=None,
        pdf=None,
    )

    assert code == 0
    assert (data_root / "newco" / "2026" / "input.xlsx").exists()
