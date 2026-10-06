# Renewable Energy Placeholder Example

`examples/renewable_energy/scenario/demo_scenario.json` contains only five labelled component records:

- Wind
- PV
- Battery
- Grid
- Load

No physical equation, capacity, efficiency, price, profile, SOC value or objective is defined. Component folders contain matching `component.placeholder.json` files so later L1/L2 work can replace them without changing the pipeline interface.

The example exists to prove one thing: a raw structured artifact can traverse L1 -> L6 without skipping a layer.
## L1 PDF demo

The actual L1 demo is under `examples/renewable_energy/pdf/`. Its `demo.pdf` contains two pages with headings, paragraphs and a simple table. `demo.md` is the generated reference Markdown.
## L2 KnowledgeState demo

`examples/renewable_energy/l2/demo_system.md` is a raw Markdown example. The offline command `python -m l2_modeling.demo` runs RequirementAgent -> ModelingAgent -> VerificationAgent with a MockLLMClient and produces a VALID KnowledgeState.
## L3 SysML demo

`python -m l3_sysml.demo` maps the renewable-energy KnowledgeState into BDD, IBD, Activity, State, Requirement, and Parametric sections, then writes JSON and PlantUML under `examples/renewable_energy/l3/`.