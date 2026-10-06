"""Minimal structural compatibility compiler for the L3 six-part SysML schema."""

from __future__ import annotations

from l3_sysml import SysMLModel
from l4_compiler.transformation import to_ir_attribute, to_ir_entity, to_ir_parameter
from l4_compiler.world_model_ir import (
    BehaviorSpec,
    ConstraintSpec as IRConstraintSpec,
    EquationSpec,
    InterfaceSpec,
    ObjectiveSense,
    ObjectiveSpec,
    SimulationStepSpec,
    WorldModelIR,
    WorldSpec,
)


class SysMLToWorldModelCompiler:
    """Adapt L3 structure into the existing L4 IR without adding L4 behavior."""

    def compile(
        self,
        sysml_model: SysMLModel,
        *,
        simulation: SimulationStepSpec | None = None,
    ) -> WorldModelIR:
        parameters = sysml_model.parametric.parameters
        ir_parameters = tuple(to_ir_parameter(parameter) for parameter in parameters)
        parameter_id_map = {
            (parameter.source_attribute_id or parameter.source_state_id or parameter.id): target.parameter_id
            for parameter, target in zip(parameters, ir_parameters, strict=True)
        }

        blocks = sysml_model.bdd.blocks
        block_by_id = {block.id: block for block in blocks}
        parameter_owner: dict[str, str] = {}
        for block in blocks:
            entity_id = f"entity-{block.source_entity_id or block.id}"
            for attribute in block.attributes:
                parameter_owner[attribute.source_attribute_id or attribute.id] = entity_id

        attribute_parameters = [
            parameter
            for parameter in parameters
            if parameter.source_attribute_id and parameter.source_attribute_id in parameter_owner
        ]
        attributes = tuple(
            to_ir_attribute(parameter, entity_id=parameter_owner[parameter.source_attribute_id or parameter.id])
            for parameter in attribute_parameters
        )
        attribute_id_map = {
            (parameter.source_attribute_id or parameter.id): attribute.attribute_id
            for parameter, attribute in zip(attribute_parameters, attributes, strict=True)
        }
        entities = tuple(
            to_ir_entity(block, parameter_id_map=parameter_id_map, attribute_id_map=attribute_id_map)
            for block in blocks
        )

        interfaces: list[InterfaceSpec] = []
        for connector in sysml_model.ibd.connectors:
            source_block = block_by_id.get(connector.source_block_id)
            target_block = block_by_id.get(connector.target_block_id)
            if source_block is None or target_block is None:
                continue
            interfaces.append(
                InterfaceSpec(
                    interface_id=f"interface-{connector.id}",
                    name=connector.relation_type,
                    source_entity_id=f"entity-{source_block.source_entity_id or source_block.id}",
                    target_entity_id=f"entity-{target_block.source_entity_id or target_block.id}",
                    source_ids=(connector.source_relation_id or connector.id,),
                    metadata={"status": "placeholder", "connection_type": connector.relation_type},
                )
            )

        constraints = tuple(
            IRConstraintSpec(
                constraint_id=f"ir-{requirement.id}",
                name=requirement.name,
                expression=requirement.text,
                source_ids=tuple(requirement.source_ids),
                metadata={"status": "placeholder", "requirement_type": requirement.requirement_type},
            )
            for requirement in sysml_model.requirements
            if requirement.requirement_type == "constraint"
        )
        equations = tuple(
            EquationSpec(
                equation_id=f"equation-{equation.id}",
                name=equation.name,
                expression=equation.expression,
                parameter_ids=tuple(
                    parameter_id_map[variable_id]
                    for variable_id in equation.variable_ids
                    if variable_id in parameter_id_map
                ),
                source_ids=tuple(equation.source_constraint_ids + equation.source_objective_ids),
                metadata={"status": "placeholder"},
            )
            for equation in sysml_model.parametric.equations
        )
        behaviors = tuple(
            BehaviorSpec(
                behavior_id=f"behavior-{action.id}",
                name=action.name,
                source_ids=(action.source_process_id or action.id,),
                metadata={"status": "placeholder", "action_inputs": action.inputs, "action_outputs": action.outputs},
            )
            for action in sysml_model.activity.actions
        )
        objectives = tuple(
            ObjectiveSpec(
                objective_id=f"objective-{requirement.id}",
                name=requirement.name,
                sense=self._objective_sense(requirement.text),
                expression=requirement.text,
                source_ids=tuple(requirement.source_ids),
                metadata={"status": "placeholder"},
            )
            for requirement in sysml_model.requirements
            if requirement.requirement_type == "objective"
        )
        simulation_spec = simulation or SimulationStepSpec()
        root_block = block_by_id.get(sysml_model.bdd.root_block_id or "") if sysml_model.bdd.root_block_id else None
        world_entity_id = root_block.source_entity_id if root_block and root_block.source_entity_id else "knowledge-state"

        return WorldModelIR(
            ir_id=f"world-{world_entity_id}-ir",
            world=WorldSpec(
                world_id=f"world-{world_entity_id}",
                name=sysml_model.bdd.name,
                entity_ids=tuple(entity.entity_id for entity in entities),
                metadata={"status": "placeholder"},
            ),
            entities=entities,
            attributes=attributes,
            state_variables=(),
            parameters=ir_parameters,
            behaviors=behaviors,
            dynamics=(),
            events=(),
            resources=(),
            interfaces=tuple(interfaces),
            constraints=constraints,
            equations=equations,
            objectives=objectives,
            simulation=simulation_spec,
            metadata={
                "status": "placeholder",
                "compiler": self.__class__.__name__,
                "deferred": ("state_variables", "dynamics", "events", "resources"),
            },
        )

    @staticmethod
    def _objective_sense(expression: str) -> ObjectiveSense:
        lowered = expression.lower()
        if "minimize" in lowered or "minimise" in lowered:
            return ObjectiveSense.MINIMIZE
        if "maximize" in lowered or "maximise" in lowered:
            return ObjectiveSense.MAXIMIZE
        return ObjectiveSense.UNDECIDED