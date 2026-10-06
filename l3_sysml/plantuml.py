"""PlantUML rendering for the six L3 SysML sections."""

from __future__ import annotations

import re
from dataclasses import dataclass

from l3_sysml.schema import ActivityModel, BDD, IBD, ParametricModel, StateModel, SysMLModel


def _alias(prefix: str, value: str) -> str:
    safe = re.sub(r"[^0-9A-Za-z_]", "_", value)
    if safe and safe[0].isdigit():
        safe = f"n_{safe}"
    return f"{prefix}_{safe or 'unknown'}"


def _text(value: object) -> str:
    return str(value).replace("\"", "\\\"").replace("\n", "\\n")


def _value(value: object, unit: str | None) -> str:
    if value is None:
        return "unspecified"
    rendered = _text(value)
    return f"{rendered} {_text(unit)}" if unit else rendered


@dataclass(slots=True)
class PlantUMLGenerator:
    """Generate inspectable PlantUML source without a second LLM."""

    def generate(self, model: SysMLModel) -> str:
        return "\n\n".join(
            (
                self.requirements(model),
                self.bdd(model.bdd),
                self.ibd(model.ibd),
                self.activity(model.activity),
                self.state(model.state),
                self.parametric(model.parametric),
            )
        ).rstrip() + "\n"

    def requirements(self, model: SysMLModel) -> str:
        lines = ["@startuml requirements", "title L3 Requirements"]
        if not model.requirements:
            lines.append("note \"No requirements in SysMLModel\" as empty_requirements")
        for requirement in model.requirements:
            alias = _alias("req", requirement.id)
            lines.append(f'rectangle "{_text(requirement.name)}" as {alias}')
            lines.append(f'note right of {alias} : {_text(requirement.text)}\\ntype={requirement.requirement_type}')
        lines.append("@enduml")
        return "\n".join(lines)

    def bdd(self, bdd: BDD) -> str:
        lines = ["@startuml bdd", "title L3 BDD"]
        aliases: dict[str, str] = {}
        for block in bdd.blocks:
            alias = _alias("block", block.id)
            aliases[block.id] = alias
            lines.append(f'class "{_text(block.name)}" as {alias} {{')
            lines.append(f'  block_type = {_text(block.block_type)}')
            for attribute in block.attributes:
                lines.append(f'  {_text(attribute.name)} : {_value(attribute.value, attribute.unit)}')
            lines.append("}")
        if bdd.root_block_id and bdd.root_block_id in aliases:
            root_alias = aliases[bdd.root_block_id]
            for block in bdd.blocks:
                if block.id != bdd.root_block_id:
                    lines.append(f'{root_alias} *-- {aliases[block.id]}')
        if not bdd.blocks:
            lines.append("note \"No blocks in SysMLModel\" as empty_bdd")
        lines.append("@enduml")
        return "\n".join(lines)

    def ibd(self, ibd: IBD) -> str:
        lines = ["@startuml ibd", "title L3 IBD"]
        aliases: dict[str, str] = {}
        for block_id in ibd.block_ids:
            alias = _alias("block", block_id)
            aliases[block_id] = alias
            lines.append(f'rectangle "{_text(block_id)}" as {alias}')
        for connector in ibd.connectors:
            source = aliases.get(connector.source_block_id, _alias("block", connector.source_block_id))
            target = aliases.get(connector.target_block_id, _alias("block", connector.target_block_id))
            lines.append(f'{source} --> {target} : {_text(connector.relation_type)}')
        if not ibd.connectors:
            lines.append("note \"No connectors in SysMLModel\" as empty_ibd")
        lines.append("@enduml")
        return "\n".join(lines)

    def activity(self, activity: ActivityModel) -> str:
        lines = ["@startuml activity", "title L3 Activity"]
        lines.append("start")
        if activity.actions:
            for action in activity.actions:
                detail = f"{action.name}"
                if action.inputs or action.outputs:
                    detail += f"\\ninputs: {', '.join(action.inputs) or 'none'}\\noutputs: {', '.join(action.outputs) or 'none'}"
                lines.append(f":{_text(detail)};")
        else:
            lines.append(":No activities in SysMLModel;")
        lines.append("stop")
        lines.append("@enduml")
        return "\n".join(lines)

    def state(self, state_model: StateModel) -> str:
        lines = ["@startuml state", "title L3 State"]
        if not state_model.machines:
            lines.append("note \"No state machines in SysMLModel\" as empty_state")
        for machine in state_model.machines:
            machine_alias = _alias("machine", machine.id)
            lines.append(f'state "{_text(machine.name)}" as {machine_alias} {{')
            for state_vertex in machine.states:
                lines.append(f'  state "{_text(state_vertex.name)}" as {_alias("state", state_vertex.id)}')
            lines.append("}")
            if machine.states:
                lines.append(f'[*] --> {_alias("state", machine.states[0].id)}')
            for transition in machine.transitions:
                source = _alias("state", transition.source_state_id)
                target = _alias("state", transition.target_state_id)
                lines.append(f'{source} --> {target} : {_text(transition.trigger or transition.name)}')
        lines.append("@enduml")
        return "\n".join(lines)

    def parametric(self, parametric: ParametricModel) -> str:
        lines = ["@startuml parametric", "title L3 Parametric"]
        for parameter in parametric.parameters:
            alias = _alias("param", parameter.id)
            lines.append(f'rectangle "{_text(parameter.name)}\\n{_value(parameter.value, parameter.unit)}" as {alias}')
        for equation in parametric.equations:
            alias = _alias("equation", equation.id)
            lines.append(f'rectangle "{_text(equation.name)}" as {alias}')
            lines.append(f'note right of {alias} : {_text(equation.expression)}')
            for variable_id in equation.variable_ids:
                lines.append(f'{_alias("param", variable_id)} --> {alias} : variable')
        if not parametric.parameters and not parametric.equations:
            lines.append("note \"No parametric information in SysMLModel\" as empty_parametric")
        lines.append("@enduml")
        return "\n".join(lines)