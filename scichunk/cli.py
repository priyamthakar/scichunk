from __future__ import annotations

import json
from pathlib import Path

import click
from rich.console import Console

from .config import load_config
from .core import SciChunker

console = Console()


@click.group()
def main() -> None:
    """SciChunk command-line interface."""


@main.command()
@click.argument("input_path", type=click.Path(exists=True, path_type=Path))
@click.option("--output", "output_dir", type=click.Path(path_type=Path), default=Path("chunks"), show_default=True)
@click.option("--format", "output_format", type=click.Choice(["json", "markdown", "txt"]), default=None)
@click.option("--research-mode", type=click.Choice(["pharma", "bio", "chem", "general"]), default=None)
@click.option("--max-tokens", type=int, default=None, help="Approximate maximum tokens per chunk.")
@click.option("--overlap-tokens", type=int, default=None, help="Approximate overlapping tokens between adjacent chunks.")
@click.option("--model", "target_model", default=None, help="Target LLM name for metadata.")
@click.option("--config", "config_path", type=click.Path(exists=True, path_type=Path), default=None, help="Optional scichunk YAML config file.")
def process(
    input_path: Path,
    output_dir: Path,
    output_format: str | None,
    research_mode: str | None,
    max_tokens: int | None,
    overlap_tokens: int | None,
    target_model: str | None,
    config_path: Path | None,
) -> None:
    """Process one scientific document or every supported file in a folder."""

    config = load_config(config_path)
    research_mode = research_mode or config.research_mode
    output_format = output_format or config.output_format
    max_tokens = max_tokens or config.max_tokens
    overlap_tokens = overlap_tokens if overlap_tokens is not None else config.overlap_tokens
    target_model = target_model or config.target_model

    output_dir.mkdir(parents=True, exist_ok=True)
    chunker = SciChunker(
        research_mode=research_mode,  # type: ignore[arg-type]
        max_chunk_tokens=max_tokens,
        overlap_tokens=overlap_tokens,
        target_model=target_model,
    )

    files = _collect_files(input_path)
    if not files:
        raise click.ClickException("No supported files found. Supported: .pdf, .docx, .txt, .md, .markdown")

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
        elif output_format == "markdown":
            destination.write_text(_to_markdown(chunks), encoding="utf-8")
        else:
            destination.write_text(_to_txt(chunks), encoding="utf-8")
        console.print(f"[green]✓[/green] {file_path.name}: {len(chunks)} chunks → {destination}")

    console.print(f"[bold green]Done.[/bold green] Processed {len(files)} file(s), generated {total_chunks} chunk(s).")


def _collect_files(path: Path) -> list[Path]:
    supported = {".pdf", ".docx", ".txt", ".md", ".markdown"}
    if path.is_file():
        return [path] if path.suffix.lower() in supported else []
    return sorted(file for file in path.rglob("*") if file.is_file() and file.suffix.lower() in supported)


def _to_markdown(chunks) -> str:
    parts: list[str] = []
    for chunk in chunks:
        parts.append(f"## {chunk.id} — {chunk.section}\n")
        parts.append(f"- Source: `{chunk.source_file}`")
        parts.append(f"- Approx. tokens: {chunk.token_count}")
        parts.append(f"- Words: {chunk.word_count}")
        if chunk.references_cited:
            parts.append(f"- References cited: {', '.join(chunk.references_cited)}")
        if chunk.entities:
            parts.append(f"- Entities: `{json.dumps(chunk.entities, ensure_ascii=False)}`")
        parts.append("\n" + chunk.text + "\n")
    return "\n".join(parts)


def _to_txt(chunks) -> str:
    parts: list[str] = []
    for chunk in chunks:
        parts.append(f"[{chunk.id}] {chunk.section} | {chunk.token_count} approx. tokens")
        parts.append(chunk.text)
        parts.append("-" * 80)
    return "\n".join(parts)


if __name__ == "__main__":
    main()
