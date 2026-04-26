from __future__ import annotations

import json
from pathlib import Path

import click
from rich.console import Console

from .core import SciChunker

console = Console()


@click.group()
def main() -> None:
    """SciChunk command-line interface."""


@main.command()
@click.argument("input_path", type=click.Path(exists=True, path_type=Path))
@click.option("--output", "output_dir", type=click.Path(path_type=Path), default=Path("chunks"), show_default=True)
@click.option("--format", "output_format", type=click.Choice(["json", "markdown"]), default="json", show_default=True)
@click.option("--research-mode", type=click.Choice(["pharma", "bio", "chem", "general"]), default="general", show_default=True)
@click.option("--max-tokens", default=1200, show_default=True, help="Approximate maximum tokens per chunk.")
@click.option("--overlap-tokens", default=120, show_default=True, help="Approximate overlapping tokens between adjacent chunks.")
@click.option("--model", "target_model", default="generic", show_default=True, help="Target LLM name for metadata.")
def process(
    input_path: Path,
    output_dir: Path,
    output_format: str,
    research_mode: str,
    max_tokens: int,
    overlap_tokens: int,
    target_model: str,
) -> None:
    """Process one scientific document or every supported file in a folder."""

    output_dir.mkdir(parents=True, exist_ok=True)
    chunker = SciChunker(
        research_mode=research_mode,  # type: ignore[arg-type]
        max_chunk_tokens=max_tokens,
        overlap_tokens=overlap_tokens,
        target_model=target_model,
    )

    files = _collect_files(input_path)
    if not files:
        raise click.ClickException("No supported files found. Supported: .pdf, .txt, .md, .markdown")

    total_chunks = 0
    for file_path in files:
        chunks = chunker.process(file_path)
        total_chunks += len(chunks)
        destination = output_dir / f"{file_path.stem}_chunks.{output_format}"
        if output_format == "json":
            destination.write_text(
                json.dumps([chunk.to_dict() for chunk in chunks], indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
        else:
            destination.write_text(_to_markdown(chunks), encoding="utf-8")
        console.print(f"[green]✓[/green] {file_path.name}: {len(chunks)} chunks → {destination}")

    console.print(f"[bold green]Done.[/bold green] Processed {len(files)} file(s), generated {total_chunks} chunk(s).")


def _collect_files(path: Path) -> list[Path]:
    supported = {".pdf", ".txt", ".md", ".markdown"}
    if path.is_file():
        return [path] if path.suffix.lower() in supported else []
    return sorted(file for file in path.rglob("*") if file.is_file() and file.suffix.lower() in supported)


def _to_markdown(chunks) -> str:
    parts: list[str] = []
    for chunk in chunks:
        parts.append(f"## {chunk.id} — {chunk.section}\n")
        parts.append(f"- Source: `{chunk.source_file}`")
        parts.append(f"- Approx. tokens: {chunk.token_count}")
        if chunk.references_cited:
            parts.append(f"- References cited: {', '.join(chunk.references_cited)}")
        parts.append("\n" + chunk.text + "\n")
    return "\n".join(parts)


if __name__ == "__main__":
    main()
