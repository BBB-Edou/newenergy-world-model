"""L5 -> L6 pipeline stage.

Two modes are supported:

* default (placeholder): build a metadata-only problem from a ``SimulationResult``
  and solve it with :class:`PlaceholderSolver`, preserving Phase 0 behaviour;
* real L6: when a ``WorldModelIR`` and a ``ScenarioInputBinding`` are supplied, run
  the CVXPY dispatch optimizer and execute the resulting action sequence on L5.
"""

from __future__ import annotations

from l2_modeling.scenario import ScenarioData, ScenarioInputBinding
from l4_compiler.world_model_ir import WorldModel
from l5_world_model import SimulationConfig, SimulationResult
from l6_optimization import (
    CVXPYOptimizer,
    OptimizationConfig,
    OptimizationProblem,
    OptimizationResult,
    PlaceholderSolver,
    Solver,
    build_dispatch_problem,
    build_optimization_problem,
)


def run_l5_to_l6(
    simulation_result: SimulationResult,
    *,
    solver: Solver | None = None,
    world_model_ir: WorldModel | None = None,
    binding: ScenarioInputBinding | None = None,
    scenario_data: ScenarioData | None = None,
    simulation_config: SimulationConfig | None = None,
    optimization_config: OptimizationConfig | None = None,
) -> tuple[OptimizationProblem, OptimizationResult]:
    if world_model_ir is not None and binding is not None:
        return _run_real_optimization(
            world_model_ir=world_model_ir,
            binding=binding,
            scenario_data=scenario_data,
            simulation_config=simulation_config,
            optimization_config=optimization_config,
        )
    problem = build_optimization_problem(simulation_result)
    result = (solver or PlaceholderSolver()).solve(problem)
    return problem, result


def _run_real_optimization(
    *,
    world_model_ir: WorldModel,
    binding: ScenarioInputBinding,
    scenario_data: ScenarioData | None,
    simulation_config: SimulationConfig | None,
    optimization_config: OptimizationConfig | None,
) -> tuple[OptimizationProblem, OptimizationResult]:
    contract = world_model_ir.scenario_input_contract
    if contract is None:
        raise ValueError("WorldModelIR has no ScenarioInputContract; cannot build an L6 optimization problem")
    if simulation_config is None:
        time = contract.time_requirements
        simulation_config = SimulationConfig(steps=time.horizon, step_size=time.step_size, time_unit=time.time_unit)
    optimization = CVXPYOptimizer().solve(
        world_model_ir=world_model_ir,
        scenario_binding=binding,
        scenario_data=scenario_data,
        simulation_config=simulation_config,
        optimization_config=optimization_config,
    )
    problem = build_dispatch_problem(simulation_config.steps, simulation_config)
    return problem, optimization
