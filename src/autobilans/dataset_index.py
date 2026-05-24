from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass(slots=True)
class DatasetEntry:
    company: str
    year: int
    xlsx_path: str | None
    xml_path: str | None
    pdf_path: str | None


def build_dataset_index(data_root: Path) -> list[DatasetEntry]:
    entries: list[DatasetEntry] = []
    candidate_company_dirs = []
    for path in sorted(p for p in data_root.iterdir() if p.is_dir()):
        if path.name in {"data", "docs", "config", "scripts", "src", "tests", "outputs", ".venv", ".pytest_cache"}:
            continue
        if any(child.is_dir() and child.name.isdigit() for child in path.iterdir()):
            candidate_company_dirs.append(path)

    for company_dir in candidate_company_dirs:
        for year_dir in sorted(
            p for p in company_dir.iterdir() if p.is_dir() and p.name.isdigit()
        ):
            xlsx_path = next((str(p) for p in sorted(year_dir.glob("zois*.xlsx"))), None)
            xml_path = next((str(p) for p in sorted(year_dir.glob("*.xml"))), None)
            pdf_path = next((str(p) for p in sorted(year_dir.glob("*.pdf"))), None)
            entries.append(
                DatasetEntry(
                    company=company_dir.name,
                    year=int(year_dir.name),
                    xlsx_path=xlsx_path,
                    xml_path=xml_path,
                    pdf_path=pdf_path,
                )
            )
    return entries


def write_dataset_index(entries: list[DatasetEntry], output_root: Path) -> Path:
    index_dir = output_root / "index"
    index_dir.mkdir(parents=True, exist_ok=True)
    target = index_dir / "datasets.json"
    with target.open("w", encoding="utf-8") as handle:
        json.dump([asdict(entry) for entry in entries], handle, ensure_ascii=False, indent=2)
    return target
