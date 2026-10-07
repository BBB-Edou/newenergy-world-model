"""CVXPY optimization MVP backed by the real L5 runtime."""

from __future__ import annotations

import cvxpy as cp

from l2_modeling.scenario import ScenarioData, ScenarioInputBinding
from l4_compiler.world_model_ir import WorldModel
from l5_world_model import Action, OpenLoopActionSequence, SimulationConfig, WorldModelRuntime
from l5_world_model.dynamics.battery import resolve_battery_parameters
from l5_world_model.simulation.engine import _resolve_grid_limit
from l5_world_model.simulation.input_provider import ScenarioInputProvider
from l6_optimization.constraints.builder import build_constraints
from l6_optimization.evaluator import compare_optimization_and_simulation
from l6_optimization.models import (
    ConstraintSummary,
    OptimizationConfig,
    OptimizationResult,
    SolverInfo,
    SolverStatus,
)
from l6_optimization.objective import build_total_cost_objective
from l6_optimization.problem import build_dispatch_problem
from l6_optimization.variables import OptimizationVariables, build_variables


class OptimizationModelError(ValueError):
    pass


class CVXPYOptimizer:
    def solve(
        self,
        *,
        world_model_ir: WorldModel,
        scenario_binding: ScenarioInputBinding,
        scenario_data: ScenarioData | None = None,
        initial_state=None,
        simulation_config: SimulationConfig | None = None,
        optimization_config: OptimizationConfig | None = None,
    ) -> OptimizationResult:
        optimization_config = optimization_config or OptimizationConfig()
        scenario = scenario_data or scenario_binding.scenario_data
        if scenario is None:
            raise OptimizationModelError("ScenarioData is required")
        contract = world_model_ir.scenario_input_contract
        if contract is None:
            raise OptimizationModelError("WorldModelIR has no ScenarioInputContract")
        time = contract.time_requirements
        simulation_config = simulation_config or SimulationConfig(steps=time.horizon, step_size=time.step_size, time_unit=time.time_unit)
        horizon = simulation_config.steps
        if horizon <= 0:
            raise OptimizationModelError("optimization horizon must be positive")
        provider = ScenarioInputProvider(scenario_binding, scenario)
        input_series = [provider.get_inputs(step) for step in range(horizon)]
        wind = [item["wind_power"] for item in input_series]
        pv = [item["pv_power"] for item in input_series]
        load = [item["load_power"] for item in input_series]
        prices = [item.get("electricity_price") for item in input_series]
        if any(price is None for price in prices):
            raise OptimizationModelError("electricity_price is required by the MVP cost objective")

        battery = resolve_battery_parameters(world_model_ir, simulation_config)
        initial_soc = self._initial_soc(world_model_ir, battery.state_id, initial_state)
        variables = build_variables(horizon)
        delta_hours = _delta_hours(simulation_config)
        grid_limit = _resolve_grid_limit(world_model_ir)
        constraints = build_constraints(
            variables=variables,
            wind_power=wind,
            pv_power=pv,
            load_power=load,
            battery=battery,
            grid_import_limit=grid_limit,
            delta_hours=delta_hours,
            initial_soc=initial_soc,
        )
        objective = build_total_cost_objective(variables, [float(price) for price in prices], delta_hours)
        problem = cp.Problem(cp.Minimize(objective), constraints)
        solver = getattr(cp, optimization_config.solver_name, None)
        if solver is None:
            raise OptimizationModelError(f"CVXPY solver {optimization_config.solver_name!r} is unavailable")
        problem.solve(solver=solver, verbose=False)
        status = self._status(problem.status)
        solver_info = SolverInfo(solver_name=optimization_config.solver_name, status=status, message=problem.status, metadata={"cvxpy_status": problem.status})
        problem_spec = build_dispatch_problem(horizon, simulation_config)
        if status not in {SolverStatus.OPTIMAL, SolverStatus.FEASIBLE}:
            return OptimizationResult(
                result_id="optimization-result",
                problem_id=problem_spec.problem_id,
                status=status,
                solver_name=optimization_config.solver_name,
                feasible=False,
                solver_info=solver_info,
                constraint_summary=ConstraintSummary(total=len(constraints), satisfied=0, violated=len(constraints), details=[problem.status]),
                message=f"CVXPY status: {problem.status}",
            )

        actions = self._actions(variables, horizon)
        runtime = WorldModelRuntime(
            world_model=world_model_ir,
            binding=scenario_binding,
            scenario=scenario,
            config=simulation_config,
            initial_state=initial_state,
            action_policy=OpenLoopActionSequence(actions),
        )
        simulation_result = runtime.run()
        consistency = compare_optimization_and_simulation(
            variables=variables,
            simulation_result=simulation_result,
            predicted_cost=float(problem.value),
            tolerance=optimization_config.tolerance,
        )
        return OptimizationResult(
            result_id="optimization-result",
            problem_id=problem_spec.problem_id,
            status=status,
            solver_name=optimization_config.solver_name,
            feasible=True,
            objective_value=float(problem.value),
            variable_values={"soc": self._values(variables.soc)},
            decision_variables=self._decision_values(variables),
            action_sequence=actions,
            constraint_summary=ConstraintSummary(total=len(constraints), satisfied=len(constraints), violated=0),
            solver_info=solver_info,
            simulation_result=simulation_result,
            consistency_report=consistency,
            message="CVXPY optimum executed by the L5 runtime",
            metadata={"scenario_id": scenario.scenario_id, "horizon": horizon, "delta_hours": delta_hours},
        )

    @staticmethod
    def _status(status: str) -> SolverStatus:
        if status in {"optimal", "optimal_inaccurate"}:
            return SolverStatus.OPTIMAL
        if status == "infeasible":
            return SolverStatus.INFEASIBLE
        return SolverStatus.ERROR

    @staticmethod
    def _initial_soc(world_model: WorldModel, state_id: str, initial_state) -> float:
        if initial_state is not None and state_id in initial_state.values:
            return float(initial_state.values[state_id])
        state = next((item for item in world_model.states if item.id == state_id), None)
        if state is None or state.value is None:
            raise OptimizationModelError(f"missing initial value for {state_id}")
        return float(state.value)

    @staticmethod
    def _values(variable) -> list[float]:
        return [0.0 if abs(float(value)) < 1e-9 else float(value) for value in variable.value]

    @staticmethod
    def _actions(variables: OptimizationVariables, horizon: int) -> list[Action]:
        actions: list[Action] = []
        for step in range(horizon):
            actions.append(
                Action(
                    action_id=f"optimal-{step}",
                    name="cvxpy_optimal_dispatch",
                    values={
                        "battery_charge": max(0.0, float(variables.charge.value[step])),
                        "battery_discharge": max(0.0, float(variables.discharge.value[step])),
                        "grid_import": max(0.0, float(variables.grid_import.value[step])),
                    },
                    metadata={"source": "CVXPYOptimizer"},
                )
            )
        return actions

    @staticmethod
    def _decision_values(variables: OptimizationVariables) -> dict[str, list[float]]:
        return {
            "battery_charge": CVXPYOptimizer._values(variables.charge),
            "battery_discharge": CVXPYOptimizer._values(variables.discharge),
            "grid_import": CVXPYOptimizer._values(variables.grid_import),
            "curtailment": CVXPYOptimizer._values(variables.curtailment),
            "battery_soc": CVXPYOptimizer._values(variables.soc),
        }


def _delta_hours(config: SimulationConfig) -> float:
    unit = config.time_unit.lower()
    if unit in {"h", "hr", "hour", "hours", "小时"}:
        return config.step_size
    if unit in {"m", "min", "minute", "minutes", "分钟"}:
        return config.step_size / 60.0
    if unit in {"s", "sec", "second", "seconds", "秒"}:
        return config.step_size / 3600.0
    raise OptimizationModelError(f"unsupported simulation time unit: {config.time_unit}")