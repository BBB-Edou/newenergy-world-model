"""Minimal structural SysML -> World Model IR compiler."""

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
    """Compile structure now; physical dynamics are intentionally deferred."""

    def compile(
        self,
        sysml_model: SysMLModel,
        *,
        simulation: SimulationStepSpec | None = None,
    ) -> WorldModelIR:
        ir_parameters = tuple(to_ir_parameter(parameter) for parameter in sysml_model.parameters)
        parameter_id_map = {
            parameter.parameter_id: target.parameter_id
            for parameter, target in zip(sysml_model.parameters, ir_parameters, strict=True)
        }
        parameters_by_id = {parameter.parameter_id: parameter for parameter in sysml_model.parameters}
        parameter_owner: dict[str, str] = {}
        for block in sysml_model.blocks:
            entity_id = f"entity-{block.block_id}"
            for parameter_id in block.parameter_ids:
                parameter_owner[parameter_id] = entity_id

        attributes = tuple(
            to_ir_attribute(parameter, entity_id=parameter_owner[parameter.parameter_id])
            for parameter in sysml_model.parameters
            if parameter.parameter_id in parameter_owner
        )
        attribute_id_map = {
            attribute.source_ids[0]: attribute.attribute_id
            for attribute in attributes
            if attribute.source_ids
        }
        entities = tuple(
            to_ir_entity(
                block,
                parameter_id_map=parameter_id_map,
                attribute_id_map=attribute_id_map,
            )
            for block in sysml_model.blocks
        )

        ports_by_id = {port.port_id: port for port in sysml_model.ports}
        interfaces: list[InterfaceSpec] = []
        for connection in sysml_model.connections:
            source_port = ports_by_id.get(connection.source_port_id)
            target_port = ports_by_id.get(connection.target_port_id)
            if source_port is None or target_port is None:
                continue
            if not source_port.source_entity_ids or not target_port.source_entity_ids:
                continue
            interfaces.append(
                InterfaceSpec(
                    interface_id=f"interface-{connection.connection_id}",
                    name=connection.name,
                    source_entity_id=source_port.source_entity_ids[0],
                    target_entity_id=target_port.source_entity_ids[0],
                    source_ids=(connection.connection_id,),
                    metadata={"status": "placeholder", "connection_type": connection.connection_type},
                )
            )

        constraints = tuple(
            IRConstraintSpec(
                constraint_id=f"ir-{constraint.constraint_id}",
                name=constraint.name,
                expression=constraint.expression,
                source_ids=(constraint.constraint_id,),
                metadata={"status": "placeholder"},
            )
            for constraint in sysml_model.constraints
        )
        equations = tuple(
            EquationSpec(
                equation_id=f"equation-{constraint.constraint_id}",
                name=constraint.name,
                expression=constraint.expression,
                parameter_ids=tuple(
                    parameter_id_map[parameter_id]
                    for parameter_id in constraint.parameter_ids
                    if parameter_id in parameter_id_map
                ),
                source_ids=(constraint.constraint_id,),
                metadata={"status": "placeholder"},
            )
            for constraint in sysml_model.constraints
        )
        behaviors = tuple(
            BehaviorSpec(
                behavior_id=f"behavior-{activity.activity_id}",
                name=activity.name,
                source_ids=(activity.activity_id,),
                metadata={"status": "placeholder", "action_names": activity.action_names},
            )
            for activity in sysml_model.activities
        )
        objective_sense = {
            "minimize": ObjectiveSense.MINIMIZE,
            "maximize": ObjectiveSense.MAXIMIZE,
            "undecided": ObjectiveSense.UNDECIDED,
        }
        objectives = tuple(
            ObjectiveSpec(
                objective_id=f"objective-{requirement.requirement_id}",
                name=requirement.text,
                sense=objective_sense.get(str(requirement.metadata.get("direction", "undecided")), ObjectiveSense.UNDECIDED),
                source_ids=(requirement.requirement_id,),
                metadata={"status": "placeholder", "source_requirement_type": requirement.requirement_type},
            )
            for requirement in sysml_model.requirements
            if requirement.requirement_type == "draft-objective"
        )
        simulation_spec = simulation or SimulationStepSpec()
        world_id = f"world-{sysml_model.model_id}"

        return WorldModelIR(
            ir_id=f"{sysml_model.model_id}-ir",
            world=WorldSpec(
                world_id=world_id,
                name=sysml_model.name,
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
                "source_sysml_model_id": sysml_model.model_id,
                "compiler": self.__class__.__name__,
                "deferred": ("state_variables", "dynamics", "events", "resources"),
            },
        )