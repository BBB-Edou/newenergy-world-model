"""Parametric Model -> World Model Equation/Constraint mapping."""

from __future__ import annotations

from l3_sysml import ParametricModel
from l4_compiler.compiler.references import ReferenceResolver
from l4_compiler.compiler.traceability import knowledge_state_trace, sysml_trace
from l4_compiler.world_model_ir import Constraint, Equation


def _is_constraint_expression(expression: str) -> bool:
    return any(operator in expression for operator in ("<=", ">=", "==", "<", ">", "!="))


def map_parametric(
    parametric: ParametricModel,
    resolver: ReferenceResolver,
    existing_constraint_sources: set[str],
) -> tuple[list[Equation], list[Constraint]]:
    equations: list[Equation] = []
    constraints: list[Constraint] = []
    for source_equation in sorted(parametric.equations, key=lambda item: item.id):
        source_ids = source_equation.source_constraint_ids + source_equation.source_objective_ids
        primary_source_id = source_ids[0] if source_ids else source_equation.id
        variables = resolver.resolved_list(source_equation.variable_ids)
        units = {variable_id: resolver.unit_of(variable_id) for variable_id in variables}
        trace = [sysml_trace(source_equation.id, "Parametric")]
        for source_id in source_ids:
            if source_id in source_equation.source_constraint_ids:
                trace.append(knowledge_state_trace(source_id, "Constraint"))
            else:
                trace.append(knowledge_state_trace(source_id, "Objective"))
        equations.append(
            Equation(
                id=f"equation-{primary_source_id}",
                name=source_equation.name,
                expression=source_equation.expression,
                variables=variables,
                units=units,
                trace=trace,
            )
        )
        if (
            _is_constraint_expression(source_equation.expression)
            and not (set(source_equation.source_constraint_ids) & existing_constraint_sources)
        ):
            scope = sorted({owner for variable in source_equation.variable_ids if (owner := resolver.owner_of(variable))})
            constraints.append(
                Constraint(
                    id=f"constraint-{primary_source_id}",
                    name=source_equation.name,
                    expression=source_equation.expression,
                    scope=scope,
                    variables=variables,
                    trace=trace,
                )
            )
    return equations, constraints