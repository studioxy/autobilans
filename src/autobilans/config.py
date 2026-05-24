from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import BaseModel, Field


class PathsConfig(BaseModel):
    data_root: Path
    output_root: Path


class PipelineConfig(BaseModel):
    default_company: str = "8spzoo"
    default_year: int = 2025
    write_dataset_index: bool = True
    allow_llm_fallback: bool = False


class LlmConfig(BaseModel):
    provider: str = "none"
    model: str = ""
    endpoint: str = ""
    timeout_seconds: int = Field(default=30, ge=1)


class AppConfig(BaseModel):
    paths: PathsConfig
    pipeline: PipelineConfig = PipelineConfig()
    llm: LlmConfig = LlmConfig()


def load_config(path: str | Path) -> AppConfig:
    config_path = Path(path)
    with config_path.open("r", encoding="utf-8") as handle:
        payload = yaml.safe_load(handle) or {}
    return AppConfig.model_validate(payload)
