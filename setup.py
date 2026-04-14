from setuptools import setup, find_packages

setup(
    name="scichunk",
    version="0.1.0",
    description="Scientific Document Preprocessing Pipeline for LLMs",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="Priyam Thakar",
    url="https://github.com/YOUR_USERNAME/scichunk",
    packages=find_packages(),
    python_requires=">=3.9",
    install_requires=[
        "pymupdf>=1.23.0",
        "python-docx>=1.0.0",
        "pyyaml>=6.0",
        "requests>=2.31.0",
        "tiktoken>=0.5.0",
        "click>=8.1.0",
        "rich>=13.0.0",
        "nbformat>=5.9.0",
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
        "Topic :: Scientific/Engineering :: Bio-Informatics",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.9",
    ],
)
