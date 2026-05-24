import argparse

from autobilans.cli import main


if __name__ == "__main__":
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--config", default="config/local.example.yaml")
    parser.add_argument("--company")
    parser.add_argument("--year", type=int)
    args, _ = parser.parse_known_args()

    cli_args = [
        "run",
        "--config",
        args.config,
    ]
    if args.company:
        cli_args.extend(["--company", args.company])
    if args.year:
        cli_args.extend(["--year", str(args.year)])

    raise SystemExit(main(cli_args))
