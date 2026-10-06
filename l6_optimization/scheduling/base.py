"""Build an optimization problem from a simulation result without coupling solvers."""

from __future__ import annotations

from l5_world_model import SimulationResult
from l6_optimization.models import OptimizationProblem


def build_optimization_problem(simulation_result: SimulationResult) -> OptimizationProblem:
    """Create an empty Phase 0 problem; later layers add explicit variables."""

    return OptimizationProblem(
        problem_id=f"{simulation_result.simulation_id}-optimization",
        name=f"Placeholder optimization for {simulation_result.model_id}",
        source_simulation_id=simulation_result.simulation_id,
        parameters={"final_time": simulation_result.final_state.time},
        metadata={
            "status": "placeholder",
            "builder": "build_optimization_problem",
            "notice": "No decision variables, objectives or constraints are inferred automatically.",
        },
    )