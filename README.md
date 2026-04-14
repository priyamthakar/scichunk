<p align="center">
  <img src="docs/logo.svg" alt="SciChunk" width="120"/>
</p>

<h1 align="center">SciChunk</h1>
<p align="center"><strong>Scientific Document Preprocessing Pipeline for LLMs</strong></p>

<p align="center">
  <a href="#features">Features</a> •
  <a href="#installation">Installation</a> •
  <a href="#quickstart">Quickstart</a> •
  <a href="#how-it-works">How It Works</a> •
  <a href="#configuration">Configuration</a> •
  <a href="#contributing">Contributing</a>
</p>

---

> Upload any scientific document → get clean, structured, semantically chunked output ready for Claude, Gemini, or any LLM.

**SciChunk** is purpose-built for scientific and pharmaceutical literature. Unlike generic document chunkers, it understands IMRaD structure (Introduction, Methods, Results, Discussion), preserves figure–caption links, respects citation boundaries, and extracts formulation parameters — so your LLM gets *research-aware* context, not blind token splits.

## Why SciChunk?

| Generic Chunkers | SciChunk |
|---|---|
| Split by token count | Split by **scientific sections** (IMRaD) |
| Break mid-citation | **Reference-aware** boundaries |
| Ignore figures/tables | **Figure & table extraction** with captions |
| No domain knowledge | **Chemical entity & formulation** detection |
| One-size-fits-all | **Research mode** for pharma/bio/chem papers |

## Features

- **Multi-format ingestion** — PDF, DOCX, TXT, Markdown, Jupyter notebooks (`.ipynb`)
- **IMRaD section detection** — automatically identifies Introduction, Methods, Results, Discussion, Abstract, References
- **Semantic chunking** — section-based, figure-aware, citation-respecting chunks
- **Figure & table extraction** — extracts images, links captions, generates descriptions via LLM vision
- **Formulation-aware parsing** — detects drug names, excipients, concentrations, ratios
- **Reference preservation** — never splits mid-citation; groups references separately
- **LLM-ready output** — JSON or Markdown with full metadata (token count, section, chunk ID)
- **OpenRouter integration** — uses any model via OpenRouter API (vision + text)
- **CLI + Python API** — use from terminal or import as a library

## Installation

```bash
# Clone
git clone https://github.com/priyamthakar/scichunk.git
cd scichunk

# Install
pip install -e .

# Set your OpenRouter API key
export OPENROUTER_API_KEY="your-key-here"
```

### Requirements

- Python 3.9+
- Tesseract OCR (optional, for scanned PDFs): `sudo apt install tesseract-ocr`

## Quickstart

### CLI

```bash
# Process a single PDF
scichunk process paper.pdf --output chunks/

# Process entire folder
scichunk process ./papers/ --output chunks/ --format json

# Research mode (pharma-aware extraction)
scichunk process paper.pdf --research-mode pharma --output chunks/

# Specify target LLM for token-aware chunking
scichunk process paper.pdf --model claude --max-tokens 4000
```

### Python API

```python
from scichunk import SciChunker

chunker = SciChunker(
    research_mode="pharma",
    max_chunk_tokens=4000,
    target_model="claude"
)

# Process a file
chunks = chunker.process("paper.pdf")

for chunk in chunks:
    print(f"[{chunk.section}] Chunk {chunk.id} ({chunk.token_count} tokens)")
    print(chunk.text[:200])
    print("---")
```

## How It Works

```
┌─────────────┐     ┌──────────────┐     ┌─────────────────┐     ┌──────────────┐
│   LOADERS   │────▶│  PROCESSORS  │────▶│    CHUNKERS     │────▶│   OUTPUTS    │
│             │     │              │     │                 │     │              │
│ • PDF       │     │ • Section    │     │ • Section-based │     │ • JSON       │
│ • DOCX      │     │   Detector   │     │ • Token-aware   │     │ • Markdown   │
│ • TXT/MD    │     │ • Figure     │     │ • Reference-    │     │ • TXT        │
│ • IPYNB     │     │   Extractor  │     │   preserving    │     │              │
│             │     │ • Reference  │     │ • Figure-aware  │     │              │
│             │     │   Parser     │     │                 │     │              │
│             │     │ • Entity     │     │                 │     │              │
│             │     │   Detector   │     │                 │     │              │
└─────────────┘     └──────────────┘     └─────────────────┘     └──────────────┘
```

## Output Format

Each chunk includes rich metadata:

```json
{
  "id": "chunk_001",
  "source_file": "paper.pdf",
  "section": "Methods",
  "subsection": "Nanoparticle Preparation",
  "text": "PCL nanoparticles were prepared by nanoprecipitation...",
  "token_count": 1247,
  "page_numbers": [4, 5],
  "figures": ["fig_3"],
  "tables": ["table_2"],
  "references_cited": ["[12]", "[15]", "[23]"],
  "entities": {
    "drugs": ["quercetin"],
    "polymers": ["PCL", "chitosan"],
    "techniques": ["nanoprecipitation", "DLS"]
  },
  "chunk_type": "text",
  "target_model": "claude"
}
```

## Configuration

Create a `scichunk.yaml` in your project root or pass `--config`:

```yaml
# scichunk.yaml
openrouter:
  api_key: ${OPENROUTER_API_KEY}
  model: "anthropic/claude-sonnet-4-20250514"
  vision_model: "anthropic/claude-sonnet-4-20250514"

chunking:
  max_tokens: 4000
  overlap_tokens: 200
  respect_sections: true
  respect_references: true
  respect_figures: true

research_mode: pharma  # Options: pharma, bio, chem, general

extraction:
  detect_entities: true
  extract_figures: true
  extract_tables: true
  ocr_scanned: true

output:
  format: json  # json, markdown, txt
  include_metadata: true
```

## Research Modes

| Mode | What it detects |
|---|---|
| `pharma` | Drug names, excipients, formulation parameters, dosage forms, pharmacokinetic terms |
| `bio` | Gene names, protein targets, organism names, assay types |
| `chem` | Chemical compounds, IUPAC names, reaction types, solvents |
| `general` | Basic scientific entity detection |

## Project Structure

```
scichunk/
├── scichunk/
│   ├── __init__.py
│   ├── core.py              # SciChunker main class
│   ├── cli.py               # CLI interface
│   ├── config.py            # Configuration management
│   ├── loaders/
│   │   ├── __init__.py
│   │   ├── base.py          # Base loader interface
│   │   ├── pdf_loader.py
│   │   ├── docx_loader.py
│   │   ├── text_loader.py
│   │   └── ipynb_loader.py
│   ├── processors/
│   │   ├── __init__.py
│   │   ├── section_detector.py
│   │   ├── figure_extractor.py
│   │   ├── reference_parser.py
│   │   └── entity_detector.py
│   ├── outputs/
│   │   ├── __init__.py
│   │   ├── json_output.py
│   │   └── markdown_output.py
│   └── utils/
│       ├── __init__.py
│       ├── tokenizer.py
│       └── openrouter.py
├── tests/
├── examples/
├── docs/
├── scichunk.yaml
├── setup.py
├── pyproject.toml
├── LICENSE
└── README.md
```

## Roadmap

- [ ] Vector DB export (ChromaDB, Pinecone, Qdrant)
- [ ] RAG pipeline integration
- [ ] Streamlit web UI
- [ ] BibTeX / RIS reference parsing
- [ ] Chemical structure image recognition (OCSR)
- [ ] Batch processing with progress tracking
- [ ] PubMed / arXiv direct ingestion

## Contributing

Contributions welcome! See [CONTRIBUTING.md](docs/CONTRIBUTING.md).

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
