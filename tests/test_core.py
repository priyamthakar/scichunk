from pathlib import Path

from scichunk import SciChunker


def test_process_markdown_sections(tmp_path: Path) -> None:
    paper = tmp_path / "paper.md"
    paper.write_text(
        "Abstract\nThis is a short abstract.\n\n"
        "Introduction\nQuercetin was studied with PCL nanoparticles [12].\n\n"
        "Methods\nNanoprecipitation and DLS were used.",
        encoding="utf-8",
    )

    chunks = SciChunker(research_mode="pharma", max_chunk_tokens=200).process(paper)

    assert chunks
    assert {chunk.section for chunk in chunks} >= {"Abstract", "Introduction", "Methods"}
    intro_chunk = next(chunk for chunk in chunks if chunk.section == "Introduction")
    assert "[12]" in intro_chunk.references_cited
    assert "quercetin" in [entity.lower() for entity in intro_chunk.entities["drugs"]]


def test_unsupported_file_type(tmp_path: Path) -> None:
    file_path = tmp_path / "paper.csv"
    file_path.write_text("x,y", encoding="utf-8")

    try:
        SciChunker().process(file_path)
    except ValueError as exc:
        assert "Unsupported file type" in str(exc)
    else:
        raise AssertionError("Expected ValueError for unsupported file type")
