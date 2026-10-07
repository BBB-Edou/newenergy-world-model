"""L6 acceptance for the real L5 -> L6 pipeline stage."""

from __future__ import annotations

from pathlib import Path

from l2_modeling.scenario import ScenarioData
from l4_compiler.world_model_ir import WorldModel
from l5_world_model import SimulationConfig
from l6_optimization import CVXPYOptimizer, OptimizationResult, SolverStatus
from pipelines.l5_to_l6 import run_l5_to_l6
from scenario_binding import ScenarioAlignment


ROOT = Path(__file__).resolve().parents[2]
WORLD_MODEL_PATH = ROOT / "examples" / "renewable_energy" / "l4" / "world_model.json"
SCENARIO_PATH = ROOT / "examples" / "renewable_energy" / "l5" / "scenario_24h.json"


def _inputs():
    world_model = WorldModel.model_validate_json(WORLD_MODEL_PATH.read_text(encoding="utf-8"))
    scenario = ScenarioData.model_validate_json(SCENARIO_PATH.read_text(encoding="utf-8"))
    binding = ScenarioAlignment().align(world_model, scenario)
    config = SimulationConfig(steps=24, step_size=1.0, time_unit="h")
    return world_model, scenario, binding, config


def test_real_pipeline_stage_runs_cvxpy_closed_loop() -> None:
    world_model, scenario, binding, config = _inputs()
    reference = CVXPYOptimizer().solve(world_model_ir=world_model, scenario_binding=binding, simulation_config=config)
    assert reference.simulation_result is not None

    problem, result = run_l5_to_l6(
        reference.simulation_result,
        world_model_ir=world_model,
        binding=binding,
        scenario_data=scenario,
        simulation_config=config,
    )

    assert problem.problem_id == "l6-24h-dispatch"
    assert problem.source_simulation_id is None
    assert [variable.variable_id for variable in problem.variables][0] == "battery_charge"
    assert isinstance(result, OptimizationResult)
    assert result.status == SolverStatus.OPTIMAL
    assert result.simulation_result is not None
    assert result.simulation_result.status == "COMPLETED"
    assert result.consistency_report is not None and result.consistency_report.valid


def test_pipeline_stage_without_world_model_stays_placeholder() -> None:
    world_model, _, binding, config = _inputs()
    reference = CVXPYOptimizer().solve(world_model_ir=world_model, scenario_binding=binding, simulation_config=config)
    assert reference.simulation_result is not None

    problem, result = run_l5_to_l6(reference.simulation_result)

    assert result.status == SolverStatus.PLACEHOLDER
    assert problem.source_simulation_id == reference.simulation_result.simulation_id
