"""Deterministic ordering normalizer for SysML input."""

from __future__ import annotations

from l3_sysml import SysMLModel


class SysMLNormalizer:
    def normalize(self, model: SysMLModel) -> SysMLModel:
        requirements = sorted(model.requirements, key=lambda item: item.id)
        blocks = sorted(model.bdd.blocks, key=lambda item: item.id)
        blocks = [
            block.model_copy(update={"attributes": sorted(block.attributes, key=lambda item: item.id)})
            for block in blocks
        ]
        connectors = sorted(model.ibd.connectors, key=lambda item: item.id)
        actions = sorted(model.activity.actions, key=lambda item: item.id)
        machines = sorted(model.state.machines, key=lambda item: item.id)
        machines = [
            machine.model_copy(update={
                "states": sorted(machine.states, key=lambda item: item.id),
                "transitions": sorted(machine.transitions, key=lambda item: item.id),
            })
            for machine in machines
        ]
        equations = sorted(model.parametric.equations, key=lambda item: item.id)
        parameters = sorted(model.parametric.parameters, key=lambda item: item.id)
        return model.model_copy(
            update={
                "requirements": requirements,
                "bdd": model.bdd.model_copy(update={"blocks": blocks}),
                "ibd": model.ibd.model_copy(update={"block_ids": sorted(model.ibd.block_ids), "connectors": connectors}),
                "activity": model.activity.model_copy(update={"actions": actions}),
                "state": model.state.model_copy(update={"machines": machines}),
                "parametric": model.parametric.model_copy(update={"parameters": parameters, "equations": equations}),
            }
        )