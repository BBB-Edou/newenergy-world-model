from __future__ import annotations

import unittest

from l4_compiler.world_model_ir import SimulationStepSpec, StateVariableSpec, WorldModelIR
from l5_world_model import Action, PlaceholderWorldModel, SimulationConfig


class PlaceholderWorldModelTests(unittest.TestCase):
    def test_run_and_action_contract(self) -> None:
        ir = WorldModelIR(
            ir_id="ir-1",
            state_variables=(
                StateVariableSpec(state_variable_id="x", entity_id="entity-1", name="X", initial_value=0),
            ),
            simulation=SimulationStepSpec(step_size=1.0, horizon=1),
        )
        model = PlaceholderWorldModel(ir, config=SimulationConfig(steps=1, step_size=1.0))
        model.initialize()
        model.apply_action(Action(action_id="action-1", name="Set X", target_id="x", values={"x": 7}))

        state = model.step()
        result = model.run()

        self.assertEqual(state.time, 1.0)
        self.assertEqual(state.values["x"], 7)
        self.assertEqual(result.metadata["status"], "placeholder")


if __name__ == "__main__":
    unittest.main()