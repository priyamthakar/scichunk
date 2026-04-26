import json
from pathlib import Path

from click.testing import CliRunner

from scichunk.cli import _to_markdown, _to_txt, main
from scichunk.core import Chunk


def test_renderers_can_omit_metadata() -> None:
    chunk = Chunk(
        id="chunk_001",
        source_file="paper.md",
        section="Introduction",
        text="Important scientific content.",
        token_count=12,
        word_count=3,
        char_count=29,
        start_word=0,
        end_word=3,
        references_cited=["[12]"],
        entities={"drugs": ["quercetin"]},
    )

    markdown = _to_markdown([chunk], include_metadata=False)
    text = _to_txt([chunk], include_metadata=False)

    assert "Approx. tokens" not in markdown
    assert "References cited" not in markdown
    assert "| 12 approx. tokens" not in text


def test_cli_no_metadata_writes_minimal_json(tmp_path: Path) -> None:
    input_file = tmp_path / "paper.md"
    output_dir = tmp_path / "out"
    input_file.write_text("Abstract\nShort abstract.", encoding="utf-8")

    result = CliRunner().invoke(
        main,
        [
            "process",
            str(input_file),
            "--output",
            str(output_dir),
            "--format",
            "json",
            "--no-metadata",
        ],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads((output_dir / "paper_chunks.json").read_text(encoding="utf-8"))
    assert payload == [
        {
            "id": "chunk_001",
            "source_file": "paper.md",
            "section": "Abstract",
            "text": "Short abstract.",
        }
    ]
