# Renewable Energy Demo

This directory contains example/demo material only. It is not formal thesis data and does not define a physical Wind/PV/Battery/Grid/Load model.

## L1 PDF -> Markdown demo

```text
examples/renewable_energy/pdf/demo.pdf
        ↓
examples/renewable_energy/pdf/demo.md
```

Regenerate the demo PDF with:

```powershell
python examples/renewable_energy/pdf/generate_demo_pdf.py
```

Regenerate Markdown with:

```powershell
python pipelines/l1_pdf_to_markdown.py examples/renewable_energy/pdf/demo.pdf --output examples/renewable_energy/pdf/demo.md
```
## L2 raw Markdown -> KnowledgeState demo

`examples/renewable_energy/l2/demo_system.md` is an example/demo input for the offline L2 agent chain. Run:

```powershell
python -m l2_modeling.demo
```

The demo uses MockLLMClient only and does not call DeepSeek.
## L3 KnowledgeState -> SysML -> PlantUML demo

```powershell
python -m l3_sysml.demo
```

Outputs:

```text
examples/renewable_energy/l3/demo_sysml.json
examples/renewable_energy/l3/demo_sysml.puml
```

The demo is deterministic and uses no API.
## L4 SysML -> World Model IR demo

```powershell
python -m l4_compiler.demo
```

Outputs:

```text
examples/renewable_energy/l4/world_model.json
```

The compiler is deterministic and uses no LLM.
## L2 ScenarioData demo

```powershell
python -m l2_modeling.scenario_demo
```

This produces `examples/renewable_energy/scenario_data/scenario_data.csv` while preserving the existing KnowledgeState -> L3 -> L4 path.
## L5 24h simulation demo

```powershell
python -m l5_world_model.demo
```

Inputs:

```text
examples/renewable_energy/l4/world_model.json
examples/renewable_energy/l5/scenario_24h.json
```

Output:

```text
examples/renewable_energy/l5/simulation_result.json
```
## L6 CVXPY optimization + what-if demo

```powershell
python -m l6_optimization.demo
python -m l6_optimization.what_if_demo
```

Inputs:

```text
examples/renewable_energy/l4/world_model.json
examples/renewable_energy/l5/scenario_24h.json
```

Outputs:

```text
examples/renewable_energy/l6/optimization_result.json
examples/renewable_energy/l6/what_if_result.json
```

L6 solves the 24h dispatch with CVXPY, then executes the optimal `Action`
sequence through the L5 runtime to prove the closed loop.
