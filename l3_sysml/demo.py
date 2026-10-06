"""Offline deterministic KnowledgeState -> SysML -> PlantUML demo."""

from __future__ import annotations

from pathlib import Path

from l2_modeling import KnowledgeState
from l3_sysml import KnowledgeStateToSysMLMapper, PlantUMLGenerator

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = PROJECT_ROOT / "examples" / "renewable_energy" / "l3" / "demo_knowledge_state.json"
DEFAULT_JSON_OUTPUT = PROJECT_ROOT / "examples" / "renewable_energy" / "l3" / "demo_sysml.json"
DEFAULT_PLANTUML_OUTPUT = PROJECT_ROOT / "examples" / "renewable_energy" / "l3" / "demo_sysml.puml"


def run_demo() -> int:
    state = KnowledgeState.model_validate_json(DEFAULT_INPUT.read_text(encoding="utf-8"))
    model = KnowledgeStateToSysMLMapper().map(state)
    plantuml = PlantUMLGenerator().generate(model)
    DEFAULT_JSON_OUTPUT.write_text(model.model_dump_json(indent=2) + "\n", encoding="utf-8")
    DEFAULT_PLANTUML_OUTPUT.write_text(plantuml, encoding="utf-8")
    print(f"KnowledgeState entities: {len(state.entities)}")
    print(f"BDD blocks: {len(model.bdd.blocks)}")
    print(f"IBD connectors: {len(model.ibd.connectors)}")
    print(f"Activity actions: {len(model.activity.actions)}")
    print(f"State machines: {len(model.state.machines)}")
    print(f"Requirements: {len(model.requirements)}")
    print(f"Parametric equations: {len(model.parametric.equations)}")
    print(f"SysML JSON: {DEFAULT_JSON_OUTPUT}")
    print(f"PlantUML: {DEFAULT_PLANTUML_OUTPUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(run_demo())