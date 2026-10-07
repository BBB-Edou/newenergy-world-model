"""Deterministic validation for the L3 SysMLModel input."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from l3_sysml import SysMLModel


class SysMLValidationIssue(BaseModel):
    model_config = ConfigDict(extra="forbid")
    code: str
    message: str
    target_type: str | None = None
    target_id: str | None = None


class SysMLValidationReport(BaseModel):
    model_config = ConfigDict(extra="forbid")
    valid: bool
    issues: list[SysMLValidationIssue] = Field(default_factory=list)


class SysMLValidationError(ValueError):
    def __init__(self, report: SysMLValidationReport) -> None:
        self.report = report
        details = "; ".join(issue.message for issue in report.issues)
        super().__init__(f"Invalid SysMLModel: {details}")


class SysMLValidator:
    def validate(self, model: SysMLModel) -> SysMLValidationReport:
        issues: list[SysMLValidationIssue] = []
        blocks = {block.id: block for block in model.bdd.blocks}
        block_ids = set(blocks)
        attribute_ids = {attribute.id for block in model.bdd.blocks for attribute in block.attributes}
        parameter_ids = {parameter.id for parameter in model.parametric.parameters}
        state_ids = {state.id for machine in model.state.machines for state in machine.states}
        known_refs = set(blocks) | attribute_ids | parameter_ids | state_ids
        known_refs |= {block.source_entity_id for block in model.bdd.blocks if block.source_entity_id}
        known_refs |= {attribute.source_attribute_id for block in model.bdd.blocks for attribute in block.attributes if attribute.source_attribute_id}
        known_refs |= {state.source_state_id for machine in model.state.machines for state in machine.states if state.source_state_id}
        known_refs |= {parameter.source_attribute_id for parameter in model.parametric.parameters if parameter.source_attribute_id}
        known_refs |= {parameter.source_state_id for parameter in model.parametric.parameters if parameter.source_state_id}

        self._duplicates("block", [block.id for block in model.bdd.blocks], issues)
        self._duplicates("attribute", [attribute.id for block in model.bdd.blocks for attribute in block.attributes], issues)
        self._duplicates("connector", [connector.id for connector in model.ibd.connectors], issues)
        self._duplicates("action", [action.id for action in model.activity.actions], issues)
        self._duplicates("state", [state.id for machine in model.state.machines for state in machine.states], issues)
        self._duplicates("equation", [equation.id for equation in model.parametric.equations], issues)

        if model.bdd.root_block_id and model.bdd.root_block_id not in block_ids:
            self._issue(issues, "bdd.root_missing", f"root block {model.bdd.root_block_id!r} does not exist", "BDD", model.bdd.root_block_id)
        for block_id in model.ibd.block_ids:
            if block_id not in block_ids:
                self._issue(issues, "ibd.block_missing", f"IBD references unknown block {block_id!r}", "IBD", block_id)
        for connector in model.ibd.connectors:
            if connector.source_block_id not in block_ids:
                self._issue(issues, "ibd.source_missing", f"connector source {connector.source_block_id!r} does not exist", "IBD", connector.id)
            if connector.target_block_id not in block_ids:
                self._issue(issues, "ibd.target_missing", f"connector target {connector.target_block_id!r} does not exist", "IBD", connector.id)
        for machine in model.state.machines:
            machine_state_ids = {state.id for state in machine.states}
            if machine.block_id and machine.block_id not in block_ids:
                self._issue(issues, "state.block_missing", f"state machine references unknown block {machine.block_id!r}", "State", machine.id)
            for transition in machine.transitions:
                if transition.source_state_id not in machine_state_ids:
                    self._issue(issues, "state.source_missing", f"transition source {transition.source_state_id!r} does not exist", "State", transition.id)
                if transition.target_state_id not in machine_state_ids:
                    self._issue(issues, "state.target_missing", f"transition target {transition.target_state_id!r} does not exist", "State", transition.id)
        for action in model.activity.actions:
            for ref in action.inputs + action.outputs:
                if ref not in known_refs:
                    self._issue(issues, "activity.ref_missing", f"activity action references unknown id {ref!r}", "Activity", action.id)
        for equation in model.parametric.equations:
            for variable_id in equation.variable_ids:
                if variable_id not in known_refs:
                    self._issue(issues, "parametric.variable_missing", f"equation references unknown variable {variable_id!r}", "Parametric", equation.id)

        return SysMLValidationReport(valid=not issues, issues=issues)

    @staticmethod
    def _duplicates(target_type: str, ids: list[str], issues: list[SysMLValidationIssue]) -> None:
        seen: set[str] = set()
        for item_id in ids:
            if item_id in seen:
                SysMLValidator._issue(issues, f"{target_type}.duplicate_id", f"duplicate {target_type} id {item_id!r}", target_type, item_id)
            seen.add(item_id)

    @staticmethod
    def _issue(issues: list[SysMLValidationIssue], code: str, message: str, target_type: str | None, target_id: str | None) -> None:
        issues.append(SysMLValidationIssue(code=code, message=message, target_type=target_type, target_id=target_id))


def validate_sysml(model: SysMLModel) -> SysMLValidationReport:
    return SysMLValidator().validate(model)