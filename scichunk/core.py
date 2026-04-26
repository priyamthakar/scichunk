from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
import re
from typing import Literal

ResearchMode = Literal["pharma", "bio", "chem", "general"]
HEADING_PREFIX = r"(?:\d+(?:\.\d+)*|[IVXLCM]+)\.?"


def _build_section_pattern(*headings: str) -> re.Pattern[str]:
    heading_pattern = "|".join(re.escape(heading) for heading in headings)
    return re.compile(
        rf"^\s*(?:{HEADING_PREFIX}\s+)?(?:{heading_pattern})\s*$",
        re.I | re.M,
    )


@dataclass(slots=True)
class Chunk:
    """A single LLM-ready scientific text chunk."""

    id: str
    source_file: str
    section: str
    text: str
    token_count: int
    word_count: int
    char_count: int
    start_word: int
    end_word: int
    chunk_type: str = "text"
    page_numbers: list[int] = field(default_factory=list)
    references_cited: list[str] = field(default_factory=list)
    entities: dict[str, list[str]] = field(default_factory=dict)
    target_model: str = "generic"

    def to_dict(self, include_metadata: bool = True) -> dict:
        payload = asdict(self)
        if include_metadata:
            return payload
        return {
            "id": payload["id"],
            "source_file": payload["source_file"],
            "section": payload["section"],
            "text": payload["text"],
        }


class SciChunker:
    """Chunk scientific documents using section-aware and citation-aware rules.

    Current supported inputs: PDF, DOCX, TXT, Markdown.
    """

    SECTION_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
        ("Abstract", _build_section_pattern("abstract", "summary")),
        ("Introduction", _build_section_pattern("introduction")),
        ("Methods", _build_section_pattern("materials and methods", "methods", "methodology", "experimental")),
        ("Results", _build_section_pattern("results")),
        ("Discussion", _build_section_pattern("discussion")),
        ("Conclusion", _build_section_pattern("conclusion", "conclusions")),
        ("References", _build_section_pattern("references", "bibliography")),
    )

    ENTITY_PATTERNS: dict[str, tuple[str, ...]] = {
        "drugs": (r"\bquercetin\b", r"\bdoxorubicin\b", r"\bpaclitaxel\b", r"\bcisplatin\b", r"\bcurcumin\b"),
        "polymers": (r"\bPCL\b", r"\bPLGA\b", r"\bchitosan\b", r"\bPEG\b", r"\bEudragit\b", r"\bHPC\b"),
        "techniques": (r"\bDLS\b", r"\bHPLC\b", r"\bTEM\b", r"\bSEM\b", r"\bDSC\b", r"\bnanoprecipitation\b"),
    }

    SUPPORTED_SUFFIXES = {".pdf", ".docx", ".txt", ".md", ".markdown"}

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

        text = self._normalize_text(self._load_text(path))
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
        if suffix == ".docx":
            return self._load_docx(path)
        raise ValueError(
            f"Unsupported file type: {suffix}. Supported: {', '.join(sorted(self.SUPPORTED_SUFFIXES))}"
        )

    def _load_pdf(self, path: Path) -> str:
        try:
            import fitz  # PyMuPDF
        except ImportError as exc:
            raise ImportError("PDF support requires PyMuPDF. Install with: pip install pymupdf") from exc

        document = fitz.open(path)
        pages = [page.get_text("text") for page in document]
        return "\n\n".join(pages)

    def _load_docx(self, path: Path) -> str:
        try:
            from docx import Document
        except ImportError as exc:
            raise ImportError("DOCX support requires python-docx. Install with: pip install python-docx") from exc

        document = Document(path)
        parts: list[str] = []
        for paragraph in document.paragraphs:
            text = paragraph.text.strip()
            if text:
                parts.append(text)
        for table in document.tables:
            for row in table.rows:
                cells = [cell.text.strip() for cell in row.cells if cell.text.strip()]
                if cells:
                    parts.append(" | ".join(cells))
        return "\n\n".join(parts)

    @staticmethod
    def _normalize_text(text: str) -> str:
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()

    def _split_into_sections(self, text: str) -> list[tuple[str, str]]:
        hits: list[tuple[int, int, str]] = []
        for section_name, pattern in self.SECTION_PATTERNS:
            for match in pattern.finditer(text):
                hits.append((match.start(), match.end(), section_name))

        hits.sort(key=lambda item: item[0])
        if not hits:
            return [("Document", text.strip())]

        sections: list[tuple[str, str]] = []
        deduped_hits: list[tuple[int, int, str]] = []
        seen_starts: set[int] = set()
        for hit in hits:
            if hit[0] in seen_starts:
                continue
            seen_starts.add(hit[0])
            deduped_hits.append(hit)

        first_start = deduped_hits[0][0]
        if text[:first_start].strip():
            sections.append(("Document", text[:first_start].strip()))

        for index, (_start, end, section_name) in enumerate(deduped_hits):
            next_start = deduped_hits[index + 1][0] if index + 1 < len(deduped_hits) else len(text)
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
                        word_count=len(chunk_words),
                        char_count=len(chunk_text),
                        start_word=start,
                        end_word=end,
                        references_cited=self._extract_reference_mentions(chunk_text),
                        entities=self._extract_entities(chunk_text),
                        target_model=self.target_model,
                    )
                )
                chunk_index += 1

            if end == len(words):
                break
            start = max(end - self.overlap_tokens, start + 1)
        return chunks

    @staticmethod
    def _estimate_tokens(text: str) -> int:
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
