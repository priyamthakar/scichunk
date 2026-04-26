<h1 align="center">SciChunk</h1>
<p align="center"><strong>Scientific Document Preprocessing Pipeline for LLMs</strong></p>

<p align="center">
  <a href="#features">Features</a> •
  <a href="#installation">Installation</a> •
  <a href="#quickstart">Quickstart</a> •
  <a href="#configuration">Configuration</a> •
  <a href="#roadmap">Roadmap</a>
</p>

---

> Convert scientific documents into clean, structured, LLM-ready chunks.

**SciChunk** is an early-stage Python tool for preparing scientific and pharmaceutical documents for LLM workflows, RAG pipelines, and literature-review assistants. It focuses on section-aware chunking rather than blind token splitting, so outputs are easier to inspect, cite, and reuse.

## Why SciChunk?

| Generic Chunkers | SciChunk |
|---|---|
| Split only by size | Splits by scientific sections where possible |
| Lose document context | Adds source file, section, token, word, and character metadata |
| Hard to audit | Exports readable JSON, Markdown, or TXT |
| No domain hints | Optional pharma/bio/chem research modes |

## Features

### Implemented now

- **Multi-format ingestion** — PDF, DOCX, TXT, Markdown (`.md`, `.markdown`)
- **Scientific section detection** — Abstract, Introduction, Methods, Results, Discussion, Conclusion, References
- **Chunk metadata** — chunk ID, source file, section, estimated tokens, word count, character count, word span, target model
- **Citation mention extraction** — detects citation patterns such as `[12]`, `[12, 15]`, and `[12-15]`
- **Basic research-mode entity extraction** — simple pharma/bio/chem keyword detection for drugs, polymers, and techniques
- **CLI + Python API** — use from terminal or import as a Python library
- **Config file support** — use `scichunk.yaml` or pass `--config`
- **Output formats** — JSON, Markdown, and TXT

### Planned, not fully implemented yet

- Figure extraction and caption linking
- Table extraction into structured formats
- OCR for scanned PDFs
- OpenRouter/vision-model integration
- Jupyter notebook ingestion
- OCSR / chemical structure recognition
- Vector DB export and RAG integrations

## Installation

```bash
# Clone
git clone https://github.com/priyamthakar/scichunk.git
cd scichunk

# Install
pip install -e .
```

### Requirements

- Python 3.9+
- PyMuPDF for PDF loading
- python-docx for DOCX loading
- PyYAML for config loading

All core requirements are installed by `pip install -e .`.

## Quickstart

### CLI

```bash
# Process a single PDF
scichunk process paper.pdf --output chunks/

# Process a DOCX file
scichunk process manuscript.docx --output chunks/ --format markdown

# Process an entire folder
scichunk process ./papers/ --output chunks/ --format json

# Pharma-aware extraction
scichunk process paper.pdf --research-mode pharma --output chunks/

# Target-model metadata and larger chunks
scichunk process paper.pdf --model claude --max-tokens 4000 --overlap-tokens 200

# Use a YAML config file
scichunk process paper.pdf --config scichunk.yaml
```

### Python API

```python
from scichunk import SciChunker

chunker = SciChunker(
    research_mode="pharma",
    max_chunk_tokens=1200,
    overlap_tokens=120,
    target_model="claude"
)

chunks = chunker.process("paper.pdf")

for chunk in chunks:
    print(f"[{chunk.section}] {chunk.id} ({chunk.token_count} approx. tokens)")
    print(chunk.text[:200])
    print(chunk.entities)
```

## How It Works

```text
Document input
   ↓
Text extraction from PDF, DOCX, TXT, or Markdown
   ↓
Section detection: Abstract, Introduction, Methods, Results, Discussion, etc.
   ↓
Chunking with overlap
   ↓
Metadata enrichment: citations, entity hints, word/token counts
   ↓
Export to JSON, Markdown, or TXT
```

## Output Format

Each chunk includes metadata like this:

```json
{
  "id": "chunk_001",
  "source_file": "paper.pdf",
  "section": "Methods",
  "text": "PCL nanoparticles were prepared by nanoprecipitation...",
  "token_count": 1247,
  "word_count": 959,
  "char_count": 6420,
  "start_word": 0,
  "end_word": 959,
  "chunk_type": "text",
  "page_numbers": [],
  "references_cited": ["[12]", "[15]", "[23]"],
  "entities": {
    "drugs": ["quercetin"],
    "polymers": ["PCL", "chitosan"],
    "techniques": ["nanoprecipitation", "DLS"]
  },
  "target_model": "claude"
}
```

## Configuration

Create a `scichunk.yaml` in your project root or pass `--config`:

```yaml
research_mode: pharma
model: claude

chunking:
  max_tokens: 1200
  overlap_tokens: 120

output:
  format: json  # json, markdown, txt
  include_metadata: true
```

CLI arguments override config values.

## Research Modes

| Mode | Current behavior |
|---|---|
| `pharma` | Basic keyword hints for selected drugs, polymers, and techniques |
| `bio` | Uses the same early entity-detection framework; more biology terms planned |
| `chem` | Uses the same early entity-detection framework; more chemistry terms planned |
| `general` | No domain-entity extraction; only section/chunk metadata |

## Project Structure

```text
scichunk/
├── scichunk/
│   ├── __init__.py
│   ├── core.py      # SciChunker and Chunk dataclass
│   ├── cli.py       # Command-line interface
│   └── config.py    # YAML config loader
├── tests/
│   └── test_core.py
├── scichunk.yaml
├── setup.py
├── pyproject.toml
├── LICENSE
└── README.md
```

## Roadmap

- [ ] Better entity extraction with scientific NLP models
- [ ] Table extraction
- [ ] Figure extraction and caption linking
- [ ] OCR for scanned PDFs
- [ ] Streamlit web UI
- [ ] Vector DB export: ChromaDB, Qdrant, Pinecone
- [ ] RAG pipeline integration
- [ ] PubMed / arXiv ingestion
- [ ] Jupyter notebook ingestion
- [ ] Chemical structure image recognition (OCSR)

## Contributing

```bash
# Dev install
pip install -e ".[dev]"

# Run tests
pytest tests/

# Lint
ruff check scichunk/
```

## License

MIT License — see [LICENSE](LICENSE).

---

<p align="center">
  Built with ❤️ for the scientific community<br>
  <strong>SciChunk</strong> — because your LLM deserves research-grade context.
</p>
