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