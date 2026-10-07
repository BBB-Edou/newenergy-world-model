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
## Run L3 offline demo

```powershell
python -m l3_sysml.demo
```

## Optional live L3 SysML Agent test

```powershell
$env:DEEPSEEK_API_KEY = "..."
python -m l3_sysml.live_test --live
```

The live test reuses the existing L2 DeepSeek client configuration.
## Run L4 compiler demo

```powershell
python -m l4_compiler.demo
```

This compiles `examples/renewable_energy/l3/demo_sysml.json` into `examples/renewable_energy/l4/world_model.json`.
## Run L2 ScenarioData demo

```powershell
python -m l2_modeling.scenario_demo
```

Outputs:

```text
examples/renewable_energy/scenario_data/scenario_data.json
examples/renewable_energy/scenario_data/scenario_data.csv
```
## Run Scenario Input Alignment demo

```powershell
python -m scenario_binding.demo
```

This aligns `WorldModelIR` with `ScenarioData` and writes `scenario_input_binding.json`.
## Run L5 24h simulation demo

```powershell
python -m l5_world_model.demo
```

This writes `examples/renewable_energy/l5/simulation_result.json`.
## Run L6 optimization demo (CVXPY -> L5 closed loop)

```powershell
python -m l6_optimization.demo
```

This optimizes the 24h dispatch with CVXPY, executes the optimal `Action`
sequence through the L5 `WorldModelRuntime`, and writes
`examples/renewable_energy/l6/optimization_result.json`. Add `cvxpy` via
`python -m pip install -r requirements.txt` if it is not yet installed.

## Run L6 what-if demo

```powershell
python -m l6_optimization.what_if_demo
```

This re-optimizes and re-simulates battery-size, price and renewable variants
and writes `examples/renewable_energy/l6/what_if_result.json`.
