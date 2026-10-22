# Contributing

## Development setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m pytest -q
```

## Guidelines

- Keep the layer boundaries: L1 PDF -> Markdown, L2 KnowledgeState/ScenarioData,
  L3 SysML, L4 WorldModelIR, L5 runtime, L6 optimization.
- Do not add LLM calls to L4/L5/L6 deterministic paths.
- Do not modify L5 world dynamics from L6; L6 influences L5 only through `Action`.
- Never commit API keys, tokens, `.env` files, or generated secrets.
- Add or update tests for every behavioural change.
- Keep demo artifacts under `examples/renewable_energy/` and mark them as demo data.

## Commit style

```text
feat: add ...
fix: correct ...
test: cover ...
docs: update ...
```
