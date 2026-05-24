from __future__ import annotations

import json
from pathlib import Path

from .aliases import load_xml_aliases
from .calculation import calculate_balance_with_contributions
from .decision_policies import apply_secondary_code_exclusions, load_decision_policies
from .dataset_index import DatasetEntry, build_dataset_index
from .exporters import export_balance_xlsx, export_code_contributions, export_mapping_report, export_validation_report
from .manual_rules import load_manual_rules
from .mapping import build_history_rules, map_rows
from .parsers import parse_bilans_xml, parse_zois
from .validation.compare import compare_balance_to_xml, summarize_validation


def run_local_pipeline(
    *,
    entry: DatasetEntry,
    output_root: Path,
    allow_llm_fallback: bool,
) -> Path:
    run_dir = output_root / "runs" / entry.company / str(entry.year)
    run_dir.mkdir(parents=True, exist_ok=True)
    aliases = load_xml_aliases(
        Path(__file__).resolve().parents[2] / "config" / "xml_aliases.yaml",
        company=entry.company,
        year=entry.year,
    )
    manual_rules = load_manual_rules(
        Path(__file__).resolve().parents[2] / "config" / "manual_rules.yaml",
        company=entry.company,
        year=entry.year,
    )
    decision_policies = load_decision_policies(
        Path(__file__).resolve().parents[2] / "config" / "decision_policies.yaml",
        company=entry.company,
        year=entry.year,
    )

    zois_rows = parse_zois(entry.xlsx_path, company=entry.company, year=entry.year) if entry.xlsx_path else []
    apply_secondary_code_exclusions(zois_rows, decision_policies)
    bilans_positions = parse_bilans_xml(entry.xml_path) if entry.xml_path else []
    labeled_rows = sum(1 for row in zois_rows if row.balance_code)
    all_entries = build_dataset_index(Path(__file__).resolve().parents[2])

    company_history_rows = []
    global_history_rows = []
    for history_entry in all_entries:
        if not history_entry.xlsx_path:
            continue
        history_rows = parse_zois(history_entry.xlsx_path, company=history_entry.company, year=history_entry.year)
        global_history_rows.extend(history_rows)
        if history_entry.company == entry.company:
            company_history_rows.extend(history_rows)

    history_rules = build_history_rules(company_history_rows)
    global_history_rules = build_history_rules(global_history_rows)
    mapping_decisions = map_rows(
        zois_rows,
        history_rules,
        global_history_rules=global_history_rules,
        manual_rules=manual_rules,
    )
    resolved_mappings = sum(1 for decision in mapping_decisions if decision.balance_code)
    calculated_balance, code_contributions = calculate_balance_with_contributions(zois_rows, mapping_decisions)
    calculated_balance_path = run_dir / "calculated_balance.json"
    with calculated_balance_path.open("w", encoding="utf-8") as handle:
        json.dump(calculated_balance, handle, ensure_ascii=False, indent=2)
    exported_contributions = export_code_contributions(contributions=code_contributions, output_dir=run_dir)
    validation_results = compare_balance_to_xml(calculated_balance, bilans_positions, mapping_aliases=aliases)
    validation_summary = summarize_validation(validation_results)
    bilans_xlsx_path = export_balance_xlsx(
        calculated_balance=calculated_balance,
        validation_results=validation_results,
        output_dir=run_dir,
    )
    exported_mapping = export_mapping_report(rows=zois_rows, decisions=mapping_decisions, output_dir=run_dir)
    exported_reports = export_validation_report(results=validation_results, output_dir=run_dir)

    summary = {
        "company": entry.company,
        "year": entry.year,
        "xlsx_path": entry.xlsx_path,
        "xml_path": entry.xml_path,
        "pdf_path": entry.pdf_path,
        "zois_rows": len(zois_rows),
        "zois_labeled_rows": labeled_rows,
        "bilans_leaf_positions": len(bilans_positions),
        "resolved_mappings": resolved_mappings,
        "unresolved_mappings": len(mapping_decisions) - resolved_mappings,
        "calculated_positions": len(calculated_balance),
        "calculated_balance_json": str(calculated_balance_path),
        "calculated_balance_xlsx": str(bilans_xlsx_path),
        "code_contributions_json": str(exported_contributions["json"]),
        "code_contributions_csv": str(exported_contributions["csv"]),
        "validation": validation_summary,
        "mapping_report_json": str(exported_mapping["json"]),
        "mapping_report_csv": str(exported_mapping["csv"]),
        "validation_report_json": str(exported_reports["json"]),
        "validation_report_csv": str(exported_reports["csv"]),
        "allow_llm_fallback": allow_llm_fallback,
        "status": "validated",
        "next_step": "Implement export and improve mapping coverage.",
    }

    target = run_dir / "run_summary.json"
    with target.open("w", encoding="utf-8") as handle:
        json.dump(summary, handle, ensure_ascii=False, indent=2)

    return target
