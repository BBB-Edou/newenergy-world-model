from __future__ import annotations

import unittest

from l4_compiler.world_model_ir import State, WorldModel, WorldModelMetadata
from l5_world_model import Action, PlaceholderWorldModel, SimulationConfig


class PlaceholderWorldModelTests(unittest.TestCase):
    def test_run_and_action_contract(self) -> None:
        ir = WorldModel(
            metadata=WorldModelMetadata(ir_id="ir-1", name="Test World"),
            states=[State(id="state-x", owner="entity-1", name="X", value=0)],
        )
        model = PlaceholderWorldModel(ir, config=SimulationConfig(steps=1, step_size=1.0))
        model.initialize()
        model.apply_action(Action(action_id="action-1", name="Set X", target_id="state-x", values={"state-x": 7}))

        state = model.step()
        result = model.run()

        self.assertEqual(state.time, 1.0)
        self.assertEqual(state.values["state-x"], 7)
        self.assertEqual(result.metadata["status"], "placeholder")


if __name__ == "__main__":
    unittest.main()