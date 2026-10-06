"""Objects returned by the complete L1 -> L6 pipeline."""

from __future__ import annotations

from dataclasses import dataclass

from l1_data import RawDataBundle
from l2_modeling import KnowledgeState
from l3_sysml import SysMLModel
from l4_compiler import WorldModelIR
from l5_world_model import ExecutableWorldModel, SimulationResult
from l6_optimization import OptimizationProblem, OptimizationResult


@dataclass(frozen=True, slots=True)
class PipelineResult:
    raw_data: RawDataBundle
    knowledge_state: KnowledgeState
    sysml_model: SysMLModel
    world_model_ir: WorldModelIR
    executable_world_model: ExecutableWorldModel
    simulation_result: SimulationResult
    optimization_problem: OptimizationProblem
    optimization_result: OptimizationResult