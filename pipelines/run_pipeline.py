"""Run the complete Phase 0 L1 -> L6 smoke pipeline."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from l1_data import RawDataBundle, load_demo_scenario
from l4_compiler.world_model_ir import SimulationStepSpec
from l5_world_model import SimulationConfig
from pipelines.l1_to_l2 import run_l1_to_l2
from pipelines.l2_to_l3 import run_l2_to_l3
from pipelines.l3_to_l4 import run_l3_to_l4
from pipelines.l4_to_l5 import run_l4_to_l5
from pipelines.l5_to_l6 import run_l5_to_l6
from pipelines.models import PipelineResult

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SCENARIO = PROJECT_ROOT / "examples" / "renewable_energy" / "scenario" / "demo_scenario.json"


def run_pipeline(
    raw_data: RawDataBundle | None = None,
    *,
    scenario_path: str | Path | None = None,
    steps: int = 3,
    step_size: float = 1.0,
) -> PipelineResult:
    if raw_data is None:
        raw_data = load_demo_scenario(scenario_path or DEFAULT_SCENARIO)

    knowledge_state = run_l1_to_l2(raw_data)
    sysml_model = run_l2_to_l3(knowledge_state)
    world_model_ir = run_l3_to_l4(
        sysml_model,
        simulation=SimulationStepSpec(step_size=step_size, horizon=steps),
    )
    executable_world_model = run_l4_to_l5(
        world_model_ir,
        config=SimulationConfig(steps=steps, step_size=step_size),
    )
    simulation_result = executable_world_model.run()
    optimization_problem, optimization_result = run_l5_to_l6(simulation_result)

    return PipelineResult(
        raw_data=raw_data,
        knowledge_state=knowledge_state,
        sysml_model=sysml_model,
        world_model_ir=world_model_ir,
        executable_world_model=executable_world_model,
        simulation_result=simulation_result,
        optimization_problem=optimization_problem,
        optimization_result=optimization_result,
    )


def _summary(result: PipelineResult) -> dict[str, object]:
    return {
        "status": "placeholder",
        "raw_artifacts": len(result.raw_data.artifacts),
        "knowledge_entities": len(result.knowledge_state.entities),
        "sysml_blocks": len(result.sysml_model.blocks),
        "world_model_entities": len(result.world_model_ir.entities),
        "simulation_steps": len(result.simulation_result.trace) - 1,
        "simulation_final_time": result.simulation_result.final_state.time,
        "optimization_status": result.optimization_result.status.value,
        "optimization_variables": len(result.optimization_problem.variables),
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scenario", type=Path, default=DEFAULT_SCENARIO)
    parser.add_argument("--steps", type=int, default=3)
    parser.add_argument("--step-size", type=float, default=1.0)
    args = parser.parse_args(argv)

    result = run_pipeline(scenario_path=args.scenario, steps=args.steps, step_size=args.step_size)
    print("L1 -> L2 -> L3 -> L4 -> L5 -> L6 pipeline completed.")
    print(json.dumps(_summary(result), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())