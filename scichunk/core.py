from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
import re
from typing import Iterable, Literal

ResearchMode = Literal["pharma", "bio", "chem", "general"]


@dataclass(slots=True)
class Chunk:
    """A single LLM-ready scientific text chunk."""

    id: str
    source_file: str
    section: str
    text: str
    token_count: int
    chunk_type: str = "text"
    page_numbers: list[int] = field(default_factory=list)
    references_cited: list[str] = field(default_factory=list)
    entities: dict[str, list[str]] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)


class SciChunker:
    """Chunk scientific documents using section-aware and citation-aware rules.

    This first implementation intentionally focuses on reliable text, Markdown,
    and lightweight PDF extraction. It avoids pretending to perform deep figure
    understanding unless that feature is explicitly added later.
    """

    SECTION_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
        ("Abstract", re.compile(r"^\s*(abstract|summary)\s*$", re.I | re.M)),
        ("Introduction", re.compile(r"^\s*(\d+\.?\s*)?introduction\s*$", re.I | re.M)),
        ("Methods", re.compile(r"^\s*(\d+\.?\s*)?(materials\s+and\s+methods|methods|methodology|experimental)\s*$", re.I | re.M)),
        ("Results", re.compile(r"^\s*(\d+\.?\s*)?results\s*$", re.I | re.M)),
        ("Discussion", re.compile(r"^\s*(\d+\.?\s*)?discussion\s*$", re.I | re.M)),
        ("Conclusion", re.compile(r"^\s*(\d+\.?\s*)?(conclusion|conclusions)\s*$", re.I | re.M)),
        ("References", re.compile(r"^\s*(references|bibliography)\s*$", re.I | re.M)),
    )

    ENTITY_PATTERNS: dict[str, tuple[str, ...]] = {
        "drugs": (r"\bquercetin\b", r"\bdoxorubicin\b", r"\bpaclitaxel\b", r"\bcisplatin\b"),
        "polymers": (r"\bPCL\b", r"\bPLGA\b", r"\bchitosan\b", r"\bPEG\b", r"\bEudragit\b"),
        "techniques": (r"\bDLS\b", r"\bHPLC\b", r"\bTEM\b", r"\bSEM\b", r"\bnanoprecipitation\b"),
    }

    def __init__(
        self,
        research_mode: ResearchMode = "general",
        max_chunk_tokens: int = 1200,
        overlap_tokens: int = 120,
        target_model: str = "generic",
    ) -> None:
        if max_chunk_tokens < 200:
            raise ValueError("max_chunk_tokens should be at least 200 for useful scientific chunks.")
        if overlap_tokens < 0:
            raise ValueError("overlap_tokens cannot be negative.")
        if overlap_tokens >= max_chunk_tokens:
            raise ValueError("overlap_tokens must be smaller than max_chunk_tokens.")

        self.research_mode = research_mode
        self.max_chunk_tokens = max_chunk_tokens
        self.overlap_tokens = overlap_tokens
        self.target_model = target_model

    def process(self, file_path: str | Path) -> list[Chunk]:
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Input file not found: {path}")

        text = self._load_text(path)
        sections = self._split_into_sections(text)

        chunks: list[Chunk] = []
        for section_name, section_text in sections:
            chunks.extend(self._chunk_section(path.name, section_name, section_text, len(chunks)))
        return chunks

    def _load_text(self, path: Path) -> str:
        suffix = path.suffix.lower()
        if suffix in {".txt", ".md", ".markdown"}:
            return path.read_text(encoding="utf-8", errors="replace")
        if suffix == ".pdf":
            return self._load_pdf(path)
        raise ValueError(f"Unsupported file type: {suffix}. Supported: .txt, .md, .markdown, .pdf")

    def _load_pdf(self, path: Path) -> str:
        try:
            import fitz  # PyMuPDF
        except ImportError as exc:
            raise ImportError("PDF support requires PyMuPDF. Install with: pip install pymupdf") from exc

        document = fitz.open(path)
        pages = [page.get_text("text") for page in document]
        return "\n\n".join(pages)

    def _split_into_sections(self, text: str) -> list[tuple[str, str]]:
        hits: list[tuple[int, int, str]] = []
        for section_name, pattern in self.SECTION_PATTERNS:
            for match in pattern.finditer(text):
                hits.append((match.start(), match.end(), section_name))

        hits.sort(key=lambda item: item[0])
        if not hits:
            return [("Document", text.strip())]

        sections: list[tuple[str, str]] = []
        for index, (start, end, section_name) in enumerate(hits):
            next_start = hits[index + 1][0] if index + 1 < len(hits) else len(text)
            body = text[end:next_start].strip()
            if body:
                sections.append((section_name, body))
        return sections or [("Document", text.strip())]

    def _chunk_section(self, source_file: str, section: str, text: str, offset: int) -> list[Chunk]:
        words = text.split()
        if not words:
            return []

        chunks: list[Chunk] = []
        start = 0
        chunk_index = offset + 1
        while start < len(words):
            end = min(start + self.max_chunk_tokens, len(words))
            chunk_words = words[start:end]
            chunk_text = " ".join(chunk_words).strip()
            if chunk_text:
                chunks.append(
                    Chunk(
                        id=f"chunk_{chunk_index:03d}",
                        source_file=source_file,
                        section=section,
                        text=chunk_text,
                        token_count=self._estimate_tokens(chunk_text),
                        references_cited=self._extract_reference_mentions(chunk_text),
                        entities=self._extract_entities(chunk_text),
                    )
                )
                chunk_index += 1

            if end == len(words):
                break
            start = max(end - self.overlap_tokens, start + 1)
        return chunks

    @staticmethod
    def _estimate_tokens(text: str) -> int:
        # Conservative approximation when model-specific tokenizers are unavailable.
        return max(1, round(len(text.split()) * 1.3))

    @staticmethod
    def _extract_reference_mentions(text: str) -> list[str]:
        refs = re.findall(r"\[(?:\d{1,3})(?:\s*[-,]\s*\d{1,3})*\]", text)
        return sorted(set(refs))

    def _extract_entities(self, text: str) -> dict[str, list[str]]:
        if self.research_mode == "general":
            return {}
        entities: dict[str, list[str]] = {}
        for label, patterns in self.ENTITY_PATTERNS.items():
            matches: set[str] = set()
            for pattern in patterns:
                matches.update(match.group(0) for match in re.finditer(pattern, text, re.I))
            if matches:
                entities[label] = sorted(matches, key=str.lower)
        return entities
