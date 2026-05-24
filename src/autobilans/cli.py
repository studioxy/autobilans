from __future__ import annotations

import argparse
import csv
import json
import shutil
from datetime import datetime
from pathlib import Path

from .config import load_config
from .dataset_index import DatasetEntry, build_dataset_index, write_dataset_index
from .exceptions import (
    suggest_decisions,
    apply_exclude_secondary_code_decision,
    append_decision_log,
    apply_force_target_code_decision,
    build_exception_queue_from_run_dir,
    load_decision_file,
    validate_decisions,
)
from .isolated_pipeline import run_isolated_company_pipeline
from .pipeline import run_local_pipeline


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="autobilans")
    subparsers = parser.add_subparsers(dest="command", required=True)

    build_index = subparsers.add_parser("build-index", help="Zbuduj indeks zestawów z lokalnych katalogów")
    build_index.add_argument("--config", default="config/local.example.yaml")

    run = subparsers.add_parser("run", help="Uruchom lokalny pipeline dla wybranego zestawu")
    run.add_argument("--config", default="config/local.example.yaml")
    run.add_argument("--company")
    run.add_argument("--year", type=int)

    run_isolated = subparsers.add_parser(
        "run-isolated",
        help="Uruchom pipeline uczony wyłącznie na historii tej samej spółki",
    )
    run_isolated.add_argument("--config", default="config/local.example.yaml")
    run_isolated.add_argument("--company", required=True)
    run_isolated.add_argument("--year", type=int, required=True)

    build_exception_queue = subparsers.add_parser(
        "build-exception-queue",
        help="Zbuduj kolejkę wyjątków z istniejącego runu",
    )
    build_exception_queue.add_argument("--config", default="config/local.example.yaml")
    build_exception_queue.add_argument("--company")
    build_exception_queue.add_argument("--year", type=int)

    apply_decisions = subparsers.add_parser(
        "apply-decisions",
        help="Zastosuj zatwierdzone decyzje wyjątków do reguł",
    )
    apply_decisions.add_argument("--config", default="config/local.example.yaml")
    apply_decisions.add_argument("--company")
    apply_decisions.add_argument("--year", type=int)
    apply_decisions.add_argument("--decision-file", required=True)
    apply_decisions.add_argument("--dry-run", action="store_true")

    review_exceptions = subparsers.add_parser(
        "review-exceptions",
        help="Pokaż kolejkę wyjątków i opcjonalnie zapisz szablon decyzji",
    )
    review_exceptions.add_argument("--config", default="config/local.example.yaml")
    review_exceptions.add_argument("--company")
    review_exceptions.add_argument("--year", type=int)
    review_exceptions.add_argument("--kind")
    review_exceptions.add_argument("--limit", type=int, default=20)
    review_exceptions.add_argument("--decision-template")

    suggest = subparsers.add_parser(
        "suggest-decisions",
        help="Zaproponuj decyzje na podstawie kolejki wyjątków",
    )
    suggest.add_argument("--config", default="config/local.example.yaml")
    suggest.add_argument("--company")
    suggest.add_argument("--year", type=int)
    suggest.add_argument("--kind")
    suggest.add_argument("--limit", type=int, default=20)
    suggest.add_argument("--output")

    onboard = subparsers.add_parser(
        "onboard-dataset",
        help="Utwórz katalog zestawu dla spółki i roku oraz opcjonalnie skopiuj pliki wejściowe",
    )
    onboard.add_argument("--config", default="config/local.example.yaml")
    onboard.add_argument("--company", required=True)
    onboard.add_argument("--year", type=int, required=True)
    onboard.add_argument("--xlsx")
    onboard.add_argument("--xml")
    onboard.add_argument("--pdf")

    menu = subparsers.add_parser(
        "menu",
        help="Interaktywne menu konsolowe prowadzące krok po kroku",
    )
    menu.add_argument("--config", default="config/local.example.yaml")

    return parser


def cmd_build_index(config_path: str) -> int:
    config = load_config(config_path)
    entries = build_dataset_index(config.paths.data_root)
    target = write_dataset_index(entries, config.paths.output_root)
    print(f"Indeks zestawów zapisany do: {target}")
    print(f"Liczba pozycji: {len(entries)}")
    return 0


def cmd_run(config_path: str, company: str | None, year: int | None) -> int:
    config = load_config(config_path)
    entries = build_dataset_index(config.paths.data_root)

    selected_company = company or config.pipeline.default_company
    selected_year = year or config.pipeline.default_year

    match = next(
        (
            entry
            for entry in entries
            if entry.company == selected_company and entry.year == selected_year
        ),
        None,
    )
    if match is None:
        raise SystemExit(f"Nie znaleziono zestawu dla spółki={selected_company!r}, roku={selected_year!r}")

    if config.pipeline.write_dataset_index:
        write_dataset_index(entries, config.paths.output_root)

    target = run_local_pipeline(
        entry=match,
        output_root=Path(config.paths.output_root),
        allow_llm_fallback=config.pipeline.allow_llm_fallback,
    )
    print(f"Lokalny pipeline zakończył pracę: {target}")
    return 0


def cmd_run_isolated(config_path: str, company: str, year: int) -> int:
    config = load_config(config_path)
    entries = build_dataset_index(config.paths.data_root)
    target = run_isolated_company_pipeline(
        entries=entries,
        company=company,
        year=year,
        output_root=Path(config.paths.output_root),
    )
    print(f"Izolowany pipeline spółki zakończył pracę: {target}")
    return 0


def _resolve_dataset_selection(config_path: str, company: str | None, year: int | None) -> tuple[Path, str, int]:
    config = load_config(config_path)
    selected_company = company or config.pipeline.default_company
    selected_year = year or config.pipeline.default_year
    return Path(config.paths.output_root), selected_company, selected_year


def _prompt_with_default(label: str, default: str) -> str:
    value = input(f"{label} [{default}]: ").strip()
    return value or default


def _prompt_int_with_default(label: str, default: int) -> int:
    raw = input(f"{label} [{default}]: ").strip()
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError:
        print(f"Niepoprawna liczba, używam domyślnej wartości: {default}")
        return default


def cmd_menu(config_path: str) -> int:
    config = load_config(config_path)
    company = config.pipeline.default_company
    year = config.pipeline.default_year

    while True:
        output_root = Path(config.paths.output_root)
        run_dir = output_root / "runs" / company / str(year)
        default_decision_file = str(run_dir / "suggested_decisions.json")

        print("\n" + "=" * 64)
        print("AutoBilans - menu operatora")
        print("=" * 64)
        print(f"Bieżący zestaw: spółka={company} | rok={year}")
        _print_menu_context(run_dir)
        print("")
        print("Co chcesz zrobić:")
        print("1) Przelicz bilans dla bieżącego zestawu")
        print("2) Przejrzyj wyjątki")
        print("3) Wygeneruj propozycje decyzji")
        print("4) Zastosuj decyzje na sucho (bez zapisu)")
        print("5) Zastosuj decyzje na stałe")
        print("6) Zbuduj kolejkę wyjątków")
        print("7) Zmień spółkę lub rok")
        print("8) Pokaż pełny status runu i pliki wynikowe")
        print("9) Dodaj nową spółkę lub rok")
        print("0) Zakończ")

        choice = input("Wybierz opcję: ").strip()
        try:
            if choice == "1":
                cmd_run(config_path, company, year)
                print("\nPrzeliczenie zakończone. Aktualny status:")
                cmd_show_run_status(config_path, company, year)
            elif choice == "2":
                limit = _prompt_int_with_default("Liczba pozycji", 20)
                cmd_review_exceptions(config_path, company, year, None, limit, None)
            elif choice == "3":
                output = _prompt_with_default("Plik wyjściowy", default_decision_file)
                limit = _prompt_int_with_default("Liczba pozycji", 20)
                cmd_suggest_decisions(config_path, company, year, None, limit, output)
            elif choice == "4":
                decision_file = _prompt_with_default("Plik z decyzjami", default_decision_file)
                cmd_apply_decisions(config_path, company, year, decision_file, dry_run=True)
            elif choice == "5":
                decision_file = _prompt_with_default("Plik z decyzjami", default_decision_file)
                cmd_apply_decisions(config_path, company, year, decision_file, dry_run=False)
            elif choice == "6":
                cmd_build_exception_queue(config_path, company, year)
            elif choice == "7":
                company = _prompt_with_default("Spółka", company)
                year = _prompt_int_with_default("Rok", year)
            elif choice == "8":
                cmd_show_run_status(config_path, company, year)
            elif choice == "9":
                new_company = _prompt_with_default("Spółka", company)
                new_year = _prompt_int_with_default("Rok", year)
                xlsx_path = input("Ścieżka do ZOiS .xlsx (opcjonalnie): ").strip()
                xml_path = input("Ścieżka do Bilansu .xml (opcjonalnie): ").strip()
                pdf_path = input("Ścieżka do Bilansu .pdf (opcjonalnie): ").strip()
                cmd_onboard_dataset(
                    config_path=config_path,
                    company=new_company,
                    year=new_year,
                    xlsx=xlsx_path or None,
                    xml=xml_path or None,
                    pdf=pdf_path or None,
                )
                company = new_company
                year = new_year
            elif choice == "0":
                print("Kończę pracę w menu.")
                return 0
            else:
                print("Nie znam takiej opcji.")
        except SystemExit as exc:
            print(f"Operacja nie powiodła się: {exc}")
        except Exception as exc:  # pragma: no cover - interactive guardrail
            print(f"Operacja nie powiodła się: {exc}")


def _find_dataset_entry(config_path: str, company: str | None, year: int | None) -> tuple[DatasetEntry, bool]:
    config = load_config(config_path)
    entries = build_dataset_index(config.paths.data_root)
    selected_company = company or config.pipeline.default_company
    selected_year = year or config.pipeline.default_year
    match = next(
        (
            entry
            for entry in entries
            if entry.company == selected_company and entry.year == selected_year
        ),
        None,
    )
    if match is None:
        raise SystemExit(f"Nie znaleziono zestawu dla spółki={selected_company!r}, roku={selected_year!r}")
    return match, config.pipeline.allow_llm_fallback


def _ensure_exception_queue(run_dir: Path) -> tuple[Path, list[dict[str, object]]]:
    queue_path = run_dir / "exception_queue.json"
    if queue_path.exists():
        return queue_path, json.loads(queue_path.read_text(encoding="utf-8"))
    queue = build_exception_queue_from_run_dir(run_dir)
    queue_path.write_text(json.dumps(queue, ensure_ascii=False, indent=2), encoding="utf-8")
    return queue_path, queue


def _known_target_codes(run_dir: Path) -> set[str]:
    target = run_dir / "validation_report.csv"
    if not target.exists():
        return set()
    with target.open("r", encoding="utf-8", newline="") as handle:
        return {
            str(row.get("code", "")).strip()
            for row in csv.DictReader(handle)
            if str(row.get("code", "")).strip()
        }


def _copy_optional_file(source: str | None, target_dir: Path) -> str | None:
    if not source:
        return None
    source_path = Path(source)
    if not source_path.exists():
        raise SystemExit(f"Plik źródłowy nie istnieje: {source_path}")
    target = target_dir / source_path.name
    shutil.copy2(source_path, target)
    return str(target)


def cmd_onboard_dataset(
    *,
    config_path: str,
    company: str,
    year: int,
    xlsx: str | None,
    xml: str | None,
    pdf: str | None,
) -> int:
    config = load_config(config_path)
    target_dir = Path(config.paths.data_root) / company / str(year)
    target_dir.mkdir(parents=True, exist_ok=True)

    copied = {
        "xlsx": _copy_optional_file(xlsx, target_dir),
        "xml": _copy_optional_file(xml, target_dir),
        "pdf": _copy_optional_file(pdf, target_dir),
    }
    print(f"Katalog zestawu jest gotowy: {target_dir}")
    print(f"Skopiowane pliki: {copied}")
    return 0


def cmd_show_run_status(config_path: str, company: str | None, year: int | None) -> int:
    output_root, selected_company, selected_year = _resolve_dataset_selection(config_path, company, year)
    run_dir = output_root / "runs" / selected_company / str(selected_year)
    summary_path = run_dir / "run_summary.json"
    queue_path = run_dir / "exception_queue.json"

    if not summary_path.exists():
        print(f"Nie znaleziono podsumowania runu: {summary_path}")
        print("Podpowiedź: najpierw wybierz opcję 1 i przelicz bilans.")
        return 1

    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    validation = summary.get("validation", {})
    matched = int(validation.get("matched_positions", 0))
    total = int(validation.get("total_positions", 0))
    mismatched = int(validation.get("mismatched_positions", 0))
    resolved = int(summary.get("resolved_mappings", 0))
    unresolved = int(summary.get("unresolved_mappings", 0))
    run_time = datetime.fromtimestamp(summary_path.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S")
    print(f"Podsumowanie runu: {summary_path}")
    print(f"Ostatnie przeliczenie: {run_time}")
    print(
        "Walidacja: "
        f"zgodne={matched} / wszystkie={total} / niezgodne={mismatched}"
    )
    print(f"Mapowanie: rozstrzygnięte={resolved} / nierozstrzygnięte={unresolved}")
    print(f"Wynik JSON: {summary.get('calculated_balance_json', '')}")
    print(f"Wynik XLSX: {summary.get('calculated_balance_xlsx', '')}")
    print(f"Raport walidacji CSV: {summary.get('validation_report_csv', '')}")

    queue: list[dict[str, object]] = []
    if queue_path.exists():
        queue = json.loads(queue_path.read_text(encoding='utf-8'))
        stats = _queue_stats(queue)
        print(
            "Kolejka wyjątków: "
            f"łącznie={stats['total']}, rozbieżności={stats['validation_mismatch']}, "
            f"nierozstrzygnięte konta={stats['unresolved_account']}"
        )
    else:
        print("Kolejka wyjątków: jeszcze nie została zbudowana.")
        print("Podpowiedź: użyj opcji 6, aby ją zbudować.")

    _print_next_steps(
        has_queue=bool(queue_path.exists()),
        queue_items=len(queue),
        mismatched=mismatched,
        unresolved=unresolved,
    )

    return 0


def _print_menu_context(run_dir: Path) -> None:
    summary_path = run_dir / "run_summary.json"
    queue_path = run_dir / "exception_queue.json"
    if not summary_path.exists():
        print("Szybki status: ten zestaw nie był jeszcze liczony.")
        print("Podpowiedź: zacznij od opcji 1.")
        return

    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    validation = summary.get("validation", {})
    matched = int(validation.get("matched_positions", 0))
    total = int(validation.get("total_positions", 0))
    mismatched = int(validation.get("mismatched_positions", 0))
    unresolved = int(summary.get("unresolved_mappings", 0))
    status_line = f"Szybki status: zgodne {matched}/{total}, niezgodne={mismatched}, nierozstrzygnięte={unresolved}"
    if queue_path.exists():
        queue = json.loads(queue_path.read_text(encoding="utf-8"))
        status_line += f", wyjątki={len(queue)}"
    else:
        status_line += ", wyjątki=niezbudowane"
    print(status_line)

    if mismatched == 0 and queue_path.exists() and len(queue) == 0:
        print("Stan: bilans wygląda na gotowy.")
    elif mismatched > 0:
        print("Stan: są rozbieżności, warto przejrzeć wyjątki.")
    else:
        print("Stan: można sprawdzić status pełny w opcji 8.")


def _print_next_steps(*, has_queue: bool, queue_items: int, mismatched: int, unresolved: int) -> None:
    print("Co dalej:")
    if not has_queue:
        print("- Wybierz 6, aby zbudować kolejkę wyjątków.")
        return

    if queue_items == 0 and mismatched == 0:
        print("- Nie ma wyjątków. Otwórz plik XLSX z bilansem i sprawdź wynik końcowy.")
        if unresolved > 0:
            print("- Są nierozstrzygnięte konta, ale obecnie nie blokują poprawnego bilansu.")
        print("- Jeśli dane wejściowe się zmieniły, uruchom ponownie opcję 1.")
        return

    if queue_items == 0 and mismatched > 0:
        print("- Nadal są rozbieżności, ale kolejka jest pusta. Zbuduj ją ponownie opcją 6.")
        return

    print("- Wybierz 2, aby przejrzeć wyjątki.")
    print("- Wybierz 3, aby przygotować propozycje decyzji.")
    print("- Wybierz 4, aby sprawdzić decyzje na sucho.")
    print("- Wybierz 5, aby zastosować decyzje i wykonać automatyczne przeliczenie.")


def _queue_stats(queue: list[dict[str, object]]) -> dict[str, int]:
    open_items = sum(1 for item in queue if str(item.get("status", "open")) == "open")
    by_kind: dict[str, int] = {}
    for item in queue:
        kind = str(item.get("kind", "unknown"))
        by_kind[kind] = by_kind.get(kind, 0) + 1
    return {
        "total": len(queue),
        "open": open_items,
        "validation_mismatch": by_kind.get("validation_mismatch", 0),
        "unresolved_account": by_kind.get("unresolved_account", 0),
    }


def cmd_build_exception_queue(config_path: str, company: str | None, year: int | None) -> int:
    output_root, selected_company, selected_year = _resolve_dataset_selection(config_path, company, year)
    run_dir = output_root / "runs" / selected_company / str(selected_year)
    queue = build_exception_queue_from_run_dir(run_dir)
    target = run_dir / "exception_queue.json"
    target.write_text(__import__("json").dumps(queue, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Kolejka wyjątków zapisana do: {target}")
    print(f"Liczba pozycji: {len(queue)}")
    return 0


def _render_exception(item: dict[str, object]) -> str:
    kind = str(item.get("kind", "unknown"))
    if kind == "unresolved_account":
        return (
            f"[{item.get('id')}] nierozstrzygnięte konto {item.get('account_no')} "
            f"kwota={item.get('amount')}"
        )
    return (
        f"[{item.get('id')}] rozbieżność {item.get('target_code')} "
        f"oczekiwano={item.get('expected')} wyliczono={item.get('actual')} roznica={item.get('delta')}"
    )


def _build_decision_template(queue: list[dict[str, object]]) -> list[dict[str, object]]:
    template: list[dict[str, object]] = []
    for item in queue:
        if item.get("kind") == "unresolved_account":
            template.append(
                {
                    "exception_id": item.get("id"),
                    "action": "force_target_code",
                    "account_no": item.get("account_no"),
                    "target_code": "",
                    "reason": "",
                }
            )
            continue
        template.append(
            {
                "exception_id": item.get("id"),
                "action": "",
                "account_no": "",
                "target_code": "",
                "secondary_code": "",
                "reason": "",
            }
        )
    return template


def cmd_review_exceptions(
    config_path: str,
    company: str | None,
    year: int | None,
    kind: str | None,
    limit: int,
    decision_template: str | None,
) -> int:
    output_root, selected_company, selected_year = _resolve_dataset_selection(config_path, company, year)
    run_dir = output_root / "runs" / selected_company / str(selected_year)
    queue_path, queue = _ensure_exception_queue(run_dir)

    filtered = [
        item
        for item in queue
        if kind is None or str(item.get("kind")) == kind
    ][: max(limit, 0)]

    print(f"Kolejka wyjątków: {queue_path}")
    print(f"Pozycje po filtrze: {len(filtered)} / łącznie: {len(queue)}")
    for item in filtered:
        print(_render_exception(item))

    if decision_template:
        target = Path(decision_template)
        target.parent.mkdir(parents=True, exist_ok=True)
        template = _build_decision_template(filtered)
        target.write_text(json.dumps(template, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"Szablon decyzji zapisany do: {target}")

    return 0


def cmd_suggest_decisions(
    config_path: str,
    company: str | None,
    year: int | None,
    kind: str | None,
    limit: int,
    output: str | None,
) -> int:
    output_root, selected_company, selected_year = _resolve_dataset_selection(config_path, company, year)
    run_dir = output_root / "runs" / selected_company / str(selected_year)
    _, queue = _ensure_exception_queue(run_dir)
    filtered = [
        item
        for item in queue
        if (kind is None or str(item.get("kind")) == kind)
    ][: max(limit, 0)]
    suggested = suggest_decisions(filtered)
    target = Path(output) if output else run_dir / "suggested_decisions.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(suggested, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Propozycje decyzji zapisane do: {target}")
    print(f"Liczba propozycji: {len(suggested)}")
    return 0


def cmd_apply_decisions(
    config_path: str,
    company: str | None,
    year: int | None,
    decision_file: str,
    dry_run: bool = False,
) -> int:
    output_root, selected_company, selected_year = _resolve_dataset_selection(config_path, company, year)
    run_dir = output_root / "runs" / selected_company / str(selected_year)
    _, before_queue = _ensure_exception_queue(run_dir)
    decisions = load_decision_file(decision_file)
    validation = validate_decisions(decisions, known_target_codes=_known_target_codes(run_dir))
    if validation.errors:
        for message in validation.errors:
            print(f"Błąd walidacji: {message}")
        print("Nie zastosowano żadnych zmian.")
        return 1

    rules_path = Path(__file__).resolve().parents[2] / "config" / "manual_rules.yaml"
    policies_path = Path(__file__).resolve().parents[2] / "config" / "decision_policies.yaml"

    applied = 0
    for decision in validation.valid:
        action = str(decision.get("action", "")).strip()
        if action == "force_target_code":
            if not dry_run:
                apply_force_target_code_decision(
                    path=rules_path,
                    company=selected_company,
                    year=selected_year,
                    account_no=str(decision["account_no"]),
                    target_code=str(decision["target_code"]),
                )
                append_decision_log(output_dir=run_dir, entry=decision)
            applied += 1
        elif action == "exclude_secondary_code":
            if not dry_run:
                apply_exclude_secondary_code_decision(
                    path=policies_path,
                    company=selected_company,
                    year=selected_year,
                    account_no=str(decision["account_no"]),
                    secondary_code=str(decision["secondary_code"]),
                )
                append_decision_log(output_dir=run_dir, entry=decision)
            applied += 1

    if validation.duplicate_count:
        print(f"Pominięte duplikaty: {validation.duplicate_count}")

    before_stats = _queue_stats(before_queue)
    after_stats = before_stats
    if not dry_run and applied > 0:
        entry, allow_llm_fallback = _find_dataset_entry(config_path, selected_company, selected_year)
        run_local_pipeline(
            entry=entry,
            output_root=Path(output_root),
            allow_llm_fallback=allow_llm_fallback,
        )
        after_queue = build_exception_queue_from_run_dir(run_dir)
        queue_path = run_dir / "exception_queue.json"
        queue_path.write_text(json.dumps(after_queue, ensure_ascii=False, indent=2), encoding="utf-8")
        after_stats = _queue_stats(after_queue)

    print(f"Liczba zastosowanych decyzji: {applied}")
    if dry_run:
        print("Tryb dry-run: nie zmieniono żadnych plików.")
    print(f"Zaktualizowane reguły ręczne: {rules_path}")
    print(f"Zaktualizowane polityki decyzji: {policies_path}")
    print(
        "Kolejka przed/po: "
        f"łącznie {before_stats['total']}->{after_stats['total']}, "
        f"rozbieżności {before_stats['validation_mismatch']}->{after_stats['validation_mismatch']}, "
        f"nierozstrzygnięte {before_stats['unresolved_account']}->{after_stats['unresolved_account']}"
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "build-index":
        return cmd_build_index(args.config)
    if args.command == "run":
        return cmd_run(args.config, args.company, args.year)
    if args.command == "run-isolated":
        return cmd_run_isolated(args.config, args.company, args.year)
    if args.command == "build-exception-queue":
        return cmd_build_exception_queue(args.config, args.company, args.year)
    if args.command == "apply-decisions":
        return cmd_apply_decisions(args.config, args.company, args.year, args.decision_file, args.dry_run)
    if args.command == "review-exceptions":
        return cmd_review_exceptions(
            args.config,
            args.company,
            args.year,
            args.kind,
            args.limit,
            args.decision_template,
        )
    if args.command == "suggest-decisions":
        return cmd_suggest_decisions(
            args.config,
            args.company,
            args.year,
            args.kind,
            args.limit,
            args.output,
        )
    if args.command == "onboard-dataset":
        return cmd_onboard_dataset(
            config_path=args.config,
            company=args.company,
            year=args.year,
            xlsx=args.xlsx,
            xml=args.xml,
            pdf=args.pdf,
        )
    if args.command == "menu":
        return cmd_menu(args.config)

    raise SystemExit(f"Nieobsługiwana komenda: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
