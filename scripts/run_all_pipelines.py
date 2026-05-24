from __future__ import annotations

import json
from pathlib import Path

from autobilans.config import load_config
from autobilans.dataset_index import build_dataset_index
from autobilans.pipeline import run_local_pipeline


def main() -> int:
    config = load_config(r"config/local.example.yaml")
    entries = build_dataset_index(config.paths.data_root)

    summaries: list[dict[str, object]] = []
    for entry in entries:
        summary_path = run_local_pipeline(
            entry=entry,
            output_root=Path(config.paths.output_root),
            allow_llm_fallback=config.pipeline.allow_llm_fallback,
        )
        summaries.append(json.loads(Path(summary_path).read_text(encoding="utf-8")))

    batch_dir = Path(config.paths.output_root) / "batch"
    batch_dir.mkdir(parents=True, exist_ok=True)
    target = batch_dir / "all_runs_summary.json"
    target.write_text(json.dumps(summaries, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Batch summary written to: {target}")
    print(f"Datasets processed: {len(summaries)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
