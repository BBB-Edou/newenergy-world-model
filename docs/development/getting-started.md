# Getting Started

## Requirements

- Python 3.11 or newer
- PyMuPDF for L1 PDF parsing
- pytest for tests

Create and activate a project environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

## Run L1

```powershell
python pipelines/l1_pdf_to_markdown.py examples/renewable_energy/pdf/demo.pdf
```

The default output is generated under `data/processed/markdown/`.

Use the package entry point if preferred:

```powershell
python -m l1_data.service examples/renewable_energy/pdf/demo.pdf
```

## Run tests

```powershell
pytest
```

## Current boundary

L1 reads PDF and writes Markdown. L2 must read the Markdown through `FileMarkdownLoader` and is responsible for all downstream LLM extraction and Knowledge State creation.
## Run L2 offline demo

```powershell
python -m l2_modeling.demo
```

This uses `MockLLMClient` and performs no network call.

## Optional live DeepSeek test

```powershell
$env:DEEPSEEK_API_KEY = "..."
python -m l2_modeling.live_test examples/renewable_energy/l2/demo_system.md --live
```

Do not place API keys in source files or test fixtures.