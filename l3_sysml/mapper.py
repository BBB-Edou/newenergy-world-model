"""Deterministic KnowledgeState -> SysMLModel mapping.

This mapper is useful for tests, offline visualization, and as a structural
reference for the LLM prompt. It does not invent facts.
"""

from __future__ import annotations

from collections import defaultdict

from l2_modeling.knowledge_state import KnowledgeState
from l3_sysml.schema import (
    BDD,
    IBD,
    ActivityAction,
    ActivityModel,
    Block,
    BlockAttribute,
    Equation,
    IBDConnector,
    ParameterBinding,
    ParametricModel,
    Requirement,
    StateMachine,
    StateModel,
    StateVertex,
    SysMLModel,
)


class KnowledgeStateToSysMLMapper:
    def map(self, state: KnowledgeState) -> SysMLModel:
        attributes_by_entity: dict[str, list] = defaultdict(list)
        for attribute in state.attributes:
            attributes_by_entity[attribute.entity_id].append(attribute)

        blocks: list[Block] = []
        block_by_entity_id: dict[str, Block] = {}
        for entity in state.entities:
            block = Block(
                id=f"block-{entity.id}",
                name=entity.name,
                block_type=entity.entity_type,
                description=entity.description,
                attributes=[
                    BlockAttribute(
                        id=attribute.id,
                        name=attribute.name,
                        value=attribute.value,
                        unit=attribute.unit,
                        source_attribute_id=attribute.id,
                    )
                    for attribute in attributes_by_entity.get(entity.id, [])
                ],
                source_entity_id=entity.id,
            )
            blocks.append(block)
            block_by_entity_id[entity.id] = block

        connectors = [
            IBDConnector(
                id=f"connector-{relation.id}",
                source_block_id=f"block-{relation.source_entity_id}",
                target_block_id=f"block-{relation.target_entity_id}",
                relation_type=relation.relation_type,
                description=relation.description,
                source_relation_id=relation.id,
            )
            for relation in state.relations
            if relation.source_entity_id in block_by_entity_id and relation.target_entity_id in block_by_entity_id
        ]

        actions = [
            ActivityAction(
                id=f"action-{process.id}",
                name=process.name,
                description=process.description,
                inputs=list(process.inputs),
                outputs=list(process.outputs),
                source_process_id=process.id,
            )
            for process in state.processes
        ]

        states_by_entity: dict[str, list] = defaultdict(list)
        for state_variable in state.states:
            states_by_entity[state_variable.entity_id].append(state_variable)
        machines: list[StateMachine] = []
        for entity in state.entities:
            variables = states_by_entity.get(entity.id, [])
            if not variables:
                continue
            machines.append(
                StateMachine(
                    id=f"state-machine-{entity.id}",
                    name=f"{entity.name} State Machine",
                    block_id=f"block-{entity.id}",
                    states=[
                        StateVertex(
                            id=state_variable.id,
                            name=state_variable.name,
                            description=state_variable.description,
                            value=state_variable.value,
                            unit=state_variable.unit,
                            source_state_id=state_variable.id,
                        )
                        for state_variable in variables
                    ],
                    source_entity_ids=[entity.id],
                )
            )

        requirements = [
            Requirement(
                id=f"requirement-{constraint.id}",
                name=constraint.name,
                text=constraint.expression or constraint.description or constraint.name,
                requirement_type="constraint",
                source_ids=[constraint.id],
            )
            for constraint in state.constraints
        ]
        requirements.extend(
            Requirement(
                id=f"requirement-{objective.id}",
                name=objective.name,
                text=objective.expression or objective.description or objective.name,
                requirement_type="objective",
                source_ids=[objective.id],
            )
            for objective in state.objectives
        )

        parameters = [
            ParameterBinding(
                id=attribute.id,
                name=attribute.name,
                value=attribute.value,
                unit=attribute.unit,
                source_attribute_id=attribute.id,
            )
            for attribute in state.attributes
        ]
        parameters.extend(
            ParameterBinding(
                id=state_variable.id,
                name=state_variable.name,
                value=state_variable.value,
                unit=state_variable.unit,
                source_state_id=state_variable.id,
            )
            for state_variable in state.states
        )
        equations = [
            Equation(
                id=f"equation-{constraint.id}",
                name=constraint.name,
                expression=constraint.expression,
                variable_ids=list(constraint.variables),
                source_constraint_ids=[constraint.id],
            )
            for constraint in state.constraints
            if constraint.expression
        ]
        equations.extend(
            Equation(
                id=f"equation-{objective.id}",
                name=objective.name,
                expression=objective.expression,
                source_objective_ids=[objective.id],
            )
            for objective in state.objectives
            if objective.expression
        )

        root_block_id = next(
            (block.id for block in blocks if "system" in block.block_type.lower()),
            None,
        )
        return SysMLModel(
            requirements=requirements,
            bdd=BDD(root_block_id=root_block_id, blocks=blocks),
            ibd=IBD(block_ids=[block.id for block in blocks], connectors=connectors),
            activity=ActivityModel(actions=actions),
            state=StateModel(machines=machines),
            parametric=ParametricModel(parameters=parameters, equations=equations),
        )