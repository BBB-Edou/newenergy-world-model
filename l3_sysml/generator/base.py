"""Replaceable L2 -> L3 generator contract and compatibility implementation."""

from __future__ import annotations

from typing import Any, Protocol

from l2_modeling.knowledge_state import KnowledgeState
from l3_sysml.models import Activity, Block, Connection, ConstraintSpec, Parameter, Parametric, Port, Requirement, StateMachine, SysMLModel


class SysMLGenerator(Protocol):
    def generate(self, knowledge_state: KnowledgeState) -> SysMLModel:
        ...


class KnowledgeStateToSysMLGenerator:
    def generate(self, knowledge_state: KnowledgeState) -> SysMLModel:
        attributes_by_entity: dict[str, list[Any]] = {}
        for attribute in knowledge_state.attributes:
            attributes_by_entity.setdefault(attribute.entity_id, []).append(attribute)
        states_by_entity: dict[str, list[str]] = {}
        for state_variable in knowledge_state.states:
            states_by_entity.setdefault(state_variable.entity_id, []).append(state_variable.name)

        parameters: list[Parameter] = []
        blocks: list[Block] = []
        for entity in knowledge_state.entities:
            parameter_ids: list[str] = []
            for attribute in attributes_by_entity.get(entity.id, []):
                parameter = Parameter(
                    parameter_id=f"param-{attribute.id}",
                    name=attribute.name,
                    value_type=self._value_type(attribute.value),
                    unit=attribute.unit,
                    default_value=attribute.value,
                    source_attribute_ids=(attribute.id,),
                    metadata={"status": "placeholder"},
                )
                parameters.append(parameter)
                parameter_ids.append(parameter.parameter_id)
            blocks.append(
                Block(
                    block_id=f"block-{entity.id}",
                    name=entity.name,
                    block_type=entity.entity_type,
                    parameter_ids=tuple(parameter_ids),
                    source_entity_ids=(entity.id,),
                    metadata={"status": "placeholder"},
                )
            )

        entity_ids = {entity.id for entity in knowledge_state.entities}
        ports: list[Port] = []
        connections: list[Connection] = []
        block_ports: dict[str, list[str]] = {entity_id: [] for entity_id in entity_ids}
        for relation in knowledge_state.relations:
            if relation.source_entity_id not in entity_ids or relation.target_entity_id not in entity_ids:
                continue
            source_port_id = f"port-{relation.id}-source"
            target_port_id = f"port-{relation.id}-target"
            ports.extend(
                (
                    Port(port_id=source_port_id, name=f"{relation.source_entity_id}-{relation.relation_type}", port_type=relation.relation_type, source_entity_ids=(relation.source_entity_id,)),
                    Port(port_id=target_port_id, name=f"{relation.target_entity_id}-{relation.relation_type}", port_type=relation.relation_type, source_entity_ids=(relation.target_entity_id,)),
                )
            )
            block_ports[relation.source_entity_id].append(source_port_id)
            block_ports[relation.target_entity_id].append(target_port_id)
            connections.append(Connection(connection_id=f"connection-{relation.id}", name=relation.relation_type, source_port_id=source_port_id, target_port_id=target_port_id, connection_type=relation.relation_type, source_relation_ids=(relation.id,)))

        blocks = [
            Block(block_id=block.block_id, name=block.name, block_type=block.block_type, port_ids=tuple(block_ports.get(block.source_entity_ids[0], ())), parameter_ids=block.parameter_ids, source_entity_ids=block.source_entity_ids, metadata=block.metadata)
            for block in blocks
        ]
        state_machines = tuple(
            StateMachine(state_machine_id=f"state-machine-{entity_id}", name=f"{entity_id} state machine", state_names=tuple(names), initial_state=names[0] if names else None, source_entity_ids=(entity_id,), metadata={"status": "placeholder"})
            for entity_id, names in states_by_entity.items()
        )
        activities = tuple(
            Activity(activity_id=f"activity-{process.id}", name=process.name, action_names=tuple(process.inputs + process.outputs), source_process_ids=(process.id,), metadata={"status": "placeholder"})
            for process in knowledge_state.processes
        )
        constraints = tuple(
            ConstraintSpec(constraint_id=f"constraint-{constraint.id}", name=constraint.name, expression=constraint.expression, source_constraint_ids=(constraint.id,), metadata={"status": "placeholder", "variables": constraint.variables})
            for constraint in knowledge_state.constraints
        )
        parametrics = tuple(
            Parametric(parametric_id=f"parametric-{constraint.id}", name=f"{constraint.name} parametric binding", constraint_ids=(constraint.id,), parameter_ids=tuple(parameter.parameter_id for parameter in parameters), metadata={"status": "placeholder"})
            for constraint in knowledge_state.constraints
        )
        requirements = tuple(
            Requirement(requirement_id=f"requirement-{objective.id}", text=objective.expression or objective.name, requirement_type="draft-objective", source_ids=(objective.id,), metadata={"status": "placeholder", "direction": objective.direction})
            for objective in knowledge_state.objectives
        )
        return SysMLModel(
            model_id=f"knowledge-state-{knowledge_state.schema_version}-sysml",
            name="Knowledge State SysML compatibility model",
            requirements=requirements,
            blocks=tuple(blocks),
            ports=tuple(ports),
            connections=tuple(connections),
            activities=activities,
            state_machines=state_machines,
            constraints=constraints,
            parameters=tuple(parameters),
            parametrics=parametrics,
            metadata={"status": "placeholder", "schema_version": knowledge_state.schema_version},
        )

    @staticmethod
    def _value_type(value: Any) -> str:
        return "unspecified" if value is None else type(value).__name__