from __future__ import annotations

import unittest
from pathlib import Path

from l1_data import load_demo_scenario
from pipelines.run_pipeline import run_pipeline


ROOT = Path(__file__).resolve().parents[2]
SCENARIO = ROOT / "examples" / "renewable_energy" / "scenario" / "demo_scenario.json"


class FullPipelineTests(unittest.TestCase):
    def test_l1_to_l6_demo_pipeline(self) -> None:
        raw_data = load_demo_scenario(SCENARIO)

        result = run_pipeline(raw_data=raw_data, steps=2, step_size=1.0)

        self.assertEqual(len(result.knowledge_state.entities), 5)
        self.assertEqual(len(result.sysml_model.blocks), 5)
        self.assertEqual(len(result.world_model_ir.entities), 5)
        self.assertEqual(result.simulation_result.final_state.time, 2.0)
        self.assertEqual(result.optimization_result.status.value, "placeholder")
        self.assertEqual(result.optimization_problem.source_simulation_id, result.simulation_result.simulation_id)


if __name__ == "__main__":
    unittest.main()