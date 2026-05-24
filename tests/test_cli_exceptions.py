from autobilans.cli import build_parser


def test_cli_supports_exception_commands() -> None:
    parser = build_parser()

    args = parser.parse_args(
        ["build-exception-queue", "--config", "config/local.example.yaml", "--company", "metro", "--year", "2025"]
    )
    assert args.command == "build-exception-queue"

    args = parser.parse_args(
        [
            "apply-decisions",
            "--config",
            "config/local.example.yaml",
            "--company",
            "metro",
            "--year",
            "2025",
            "--decision-file",
            "outputs/runs/metro/2025/decision.json",
            "--dry-run",
        ]
    )
    assert args.command == "apply-decisions"
    assert args.dry_run is True

    args = parser.parse_args(
        [
            "review-exceptions",
            "--config",
            "config/local.example.yaml",
            "--company",
            "metro",
            "--year",
            "2025",
            "--limit",
            "3",
        ]
    )
    assert args.command == "review-exceptions"

    args = parser.parse_args(
        [
            "suggest-decisions",
            "--config",
            "config/local.example.yaml",
            "--company",
            "metro",
            "--year",
            "2025",
            "--limit",
            "5",
        ]
    )
    assert args.command == "suggest-decisions"

    args = parser.parse_args(
        [
            "menu",
            "--config",
            "config/local.example.yaml",
        ]
    )
    assert args.command == "menu"

    args = parser.parse_args(
        [
            "run-isolated",
            "--config",
            "config/local.example.yaml",
            "--company",
            "nordoen",
            "--year",
            "2026",
        ]
    )
    assert args.command == "run-isolated"

    args = parser.parse_args(
        [
            "onboard-dataset",
            "--config",
            "config/local.example.yaml",
            "--company",
            "newco",
            "--year",
            "2026",
        ]
    )
    assert args.command == "onboard-dataset"
