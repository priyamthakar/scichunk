from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass(slots=True)
class SciChunkConfig:
    """Runtime configuration for SciChunk."""

    research_mode: str = "general"
    max_tokens: int = 1200
    overlap_tokens: int = 120
    output_format: str = "json"
    target_model: str = "generic"
    include_metadata: bool = True


VALID_RESEARCH_MODES = {"pharma", "bio", "chem", "general"}
VALID_OUTPUT_FORMATS = {"json", "markdown", "txt"}


def load_config(path: str | Path | None = None) -> SciChunkConfig:
    """Load configuration from YAML.

    If no path is supplied, SciChunk looks for ``scichunk.yaml`` in the current
    working directory. Missing config files are allowed and return defaults.
    """

    if path is None:
        candidate = Path("scichunk.yaml")
        if not candidate.exists():
            return SciChunkConfig()
        path = candidate

    config_path = Path(path)
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    raw = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    if not isinstance(raw, dict):
        raise ValueError("Config file must contain a YAML mapping/object.")

    chunking = _section(raw, "chunking")
    output = _section(raw, "output")

    config = SciChunkConfig(
        research_mode=str(raw.get("research_mode", "general")),
        max_tokens=int(chunking.get("max_tokens", 1200)),
        overlap_tokens=int(chunking.get("overlap_tokens", 120)),
        output_format=str(output.get("format", "json")),
        target_model=str(raw.get("target_model", raw.get("model", "generic"))),
        include_metadata=bool(output.get("include_metadata", True)),
    )
    _validate_config(config)
    return config


def _section(raw: dict[str, Any], key: str) -> dict[str, Any]:
    value = raw.get(key, {})
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise ValueError(f"Config section '{key}' must be a mapping/object.")
    return value


def _validate_config(config: SciChunkConfig) -> None:
    if config.research_mode not in VALID_RESEARCH_MODES:
        raise ValueError(f"research_mode must be one of {sorted(VALID_RESEARCH_MODES)}")
    if config.output_format not in VALID_OUTPUT_FORMATS:
        raise ValueError(f"output.format must be one of {sorted(VALID_OUTPUT_FORMATS)}")
    if config.max_tokens < 200:
        raise ValueError("chunking.max_tokens must be at least 200")
    if config.overlap_tokens < 0:
        raise ValueError("chunking.overlap_tokens cannot be negative")
    if config.overlap_tokens >= config.max_tokens:
        raise ValueError("chunking.overlap_tokens must be smaller than chunking.max_tokens")
