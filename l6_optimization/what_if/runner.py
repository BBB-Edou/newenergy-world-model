"""What-if scenario analysis over the L6 -> L5 closed loop."""

from __future__ import annotations

from dataclasses import dataclass

from l2_modeling.scenario import ScenarioData
from l4_compiler.world_model_ir import WorldModel
from l5_world_model import SimulationConfig
from l6_optimization.models import OptimizationConfig, WhatIfResult, WhatIfScenarioResult
from l6_optimization.optimizer import CVXPYOptimizer
from scenario_binding import ScenarioAlignment


@dataclass(slots=True)
class WhatIfRunner:
    optimizer: CVXPYOptimizer

    def run(
        self,
        *,
        world_model: WorldModel,
        scenario: ScenarioData,
        simulation_config: SimulationConfig,
        variants: dict[str, ScenarioData],
        world_model_variants: dict[str, WorldModel] | None = None,
        optimization_config: OptimizationConfig | None = None,
    ) -> WhatIfResult:
        scenarios: list[WhatIfScenarioResult] = []
        world_model_variants = world_model_variants or {}
        for name in sorted(variants):
            variant = variants[name]
            variant_model = world_model_variants.get(name, world_model)
            binding = ScenarioAlignment().align(variant_model, variant)
            optimization = self.optimizer.solve(
                world_model_ir=variant_model,
                scenario_binding=binding,
                scenario_data=variant,
                simulation_config=simulation_config,
                optimization_config=optimization_config,
            )
            simulation = optimization.simulation_result
            metrics = {item.name: item.value for item in simulation.metrics} if simulation else {}
            scenarios.append(
                WhatIfScenarioResult(
                    scenario_name=name,
                    optimization_result=optimization,
                    total_cost=metrics.get("total_cost"),
                    renewable_utilization=metrics.get("renewable_utilization"),
                    curtailment=metrics.get("curtailment"),
                    peak_grid_import=metrics.get("peak_grid_import"),
                    final_soc=metrics.get("final_soc"),
                )
            )
        return WhatIfResult(
            scenarios=scenarios,
            comparison={
                "total_cost": [item.total_cost for item in scenarios],
                "renewable_utilization": [item.renewable_utilization for item in scenarios],
                "curtailment": [item.curtailment for item in scenarios],
                "peak_grid_import": [item.peak_grid_import for item in scenarios],
                "final_soc": [item.final_soc for item in scenarios],
            },
        )

    @staticmethod
    def price_variant(scenario: ScenarioData, *, scenario_id: str, multiplier: float) -> ScenarioData:
        data = scenario.model_dump()
        data["scenario_id"] = scenario_id
        data["variables"]["electricity_price"] = [value * multiplier for value in scenario.variables["electricity_price"]]
        return ScenarioData.model_validate(data)

    @staticmethod
    def renewable_variant(scenario: ScenarioData, *, scenario_id: str, wind_factor: float, pv_factor: float) -> ScenarioData:
        data = scenario.model_dump()
        data["scenario_id"] = scenario_id
        data["variables"]["wind_power"] = [value * wind_factor for value in scenario.variables["wind_power"]]
        data["variables"]["pv_power"] = [value * pv_factor for value in scenario.variables["pv_power"]]
        return ScenarioData.model_validate(data)

    @staticmethod
    def capacity_variant(world_model: WorldModel, *, capacity_kwh: float) -> WorldModel:
        attributes = []
        found = False
        for attribute in world_model.attributes:
            if attribute.name == "capacity" and attribute.owner.endswith("battery"):
                attributes.append(attribute.model_copy(update={"value": capacity_kwh}))
                found = True
            else:
                attributes.append(attribute)
        if not found:
            raise ValueError("WorldModelIR has no Battery capacity attribute")
        return world_model.model_copy(update={"attributes": attributes})

    @staticmethod
    def battery_power_variant(world_model: WorldModel, *, max_power_kw: float) -> WorldModel:
        """Return a copy of the WorldModelIR with Battery charge/discharge limits capped.

        Setting ``max_power_kw`` to ``0`` disables the battery while keeping the IR
        schema valid, which models the "no battery" what-if scenario.
        """

        attributes = []
        found = False
        for attribute in world_model.attributes:
            if attribute.owner.endswith("battery") and attribute.name in {"max_charge_power", "max_discharge_power"}:
                attributes.append(attribute.model_copy(update={"value": max_power_kw}))
                found = True
            else:
                attributes.append(attribute)
        if not found:
            raise ValueError("WorldModelIR has no Battery charge/discharge power attribute")
        return world_model.model_copy(update={"attributes": attributes})
