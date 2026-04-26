from pathlib import Path

from scichunk.config import load_config


def test_load_config_from_yaml(tmp_path: Path) -> None:
    config_path = tmp_path / "scichunk.yaml"
    config_path.write_text(
        "research_mode: pharma\n"
        "model: claude\n"
        "chunking:\n"
        "  max_tokens: 1500\n"
        "  overlap_tokens: 150\n"
        "output:\n"
        "  format: markdown\n"
        "  include_metadata: true\n",
        encoding="utf-8",
    )

    config = load_config(config_path)

    assert config.research_mode == "pharma"
    assert config.target_model == "claude"
    assert config.max_tokens == 1500
    assert config.overlap_tokens == 150
    assert config.output_format == "markdown"
    assert config.include_metadata is True


def test_missing_default_config_returns_defaults(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)

    config = load_config()

    assert config.research_mode == "general"
    assert config.max_tokens == 1200
    assert config.output_format == "json"
