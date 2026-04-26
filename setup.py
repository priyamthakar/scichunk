from pathlib import Path

from setuptools import find_packages, setup

ROOT = Path(__file__).parent

setup(
    name="scichunk",
    version="0.2.0",
    description="Scientific document preprocessing and chunking pipeline for LLM workflows",
    long_description=(ROOT / "README.md").read_text(encoding="utf-8"),
    long_description_content_type="text/markdown",
    author="Priyam Thakar",
    url="https://github.com/priyamthakar/scichunk",
    packages=find_packages(),
    python_requires=">=3.9",
    install_requires=[
        "pymupdf>=1.23.0",
        "python-docx>=1.0.0",
        "pyyaml>=6.0",
        "click>=8.1.0",
        "rich>=13.0.0",
    ],
    extras_require={
        "ocr": ["pytesseract>=0.3.10", "Pillow>=10.0.0"],
        "dev": ["pytest>=7.0", "ruff>=0.1.0"],
    },
    entry_points={
        "console_scripts": [
            "scichunk=scichunk.cli:main",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Information Analysis",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
)
