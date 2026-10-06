"""Optional live SysML Agent test using the existing shared DeepSeekClient."""

from __future__ import annotations

import argparse
from pathlib import Path

from l2_modeling import DeepSeekClient, KnowledgeState
from l3_sysml import PlantUMLGenerator, SysMLAgent

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = PROJECT_ROOT / "examples" / "renewable_energy" / "l3" / "demo_knowledge_state.json"
DEFAULT_OUTPUT = PROJECT_ROOT / "examples" / "renewable_energy" / "l3" / "live_sysml.json"
DEFAULT_PLANTUML = PROJECT_ROOT / "examples" / "renewable_energy" / "l3" / "live_sysml.puml"


def main() -> int:
    parser = argparse.ArgumentParser(description="Optional live L3 SysML Agent test.")
    parser.add_argument("--knowledge-state", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--plantuml", type=Path, default=DEFAULT_PLANTUML)
    parser.add_argument("--live", action="store_true", help="Actually call the existing DeepSeek client")
    args = parser.parse_args()

    if not args.live:
        print("Live L3 test skipped. Re-run with --live and the existing DEEPSEEK_API_KEY configuration.")
        return 0

    state = KnowledgeState.model_validate_json(args.knowledge_state.read_text(encoding="utf-8"))
    model = SysMLAgent(DeepSeekClient()).run(state)
    args.output.write_text(model.model_dump_json(indent=2) + "\n", encoding="utf-8")
    args.plantuml.write_text(PlantUMLGenerator().generate(model), encoding="utf-8")
    print(f"SysMLModel: {args.output}")
    print(f"PlantUML: {args.plantuml}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())