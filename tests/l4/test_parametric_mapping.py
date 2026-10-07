from __future__ import annotations

from l3_sysml import Equation, ParametricModel
from l4_compiler.compiler.mappings import map_parametric
from l4_compiler.compiler.references import ReferenceResolver


def test_parametric_equation_maps_to_equation_and_constraint() -> None:
    resolver = ReferenceResolver()
    resolver.register("soc", "state-soc", owner="entity-battery", unit="%")
    resolver.register("soc_min", "attribute-soc-min", owner="entity-battery", unit="%")
    resolver.register("soc_max", "attribute-soc-max", owner="entity-battery", unit="%")
    parametric = ParametricModel(
        equations=[Equation(id="soc-bounds-equation", name="soc_bounds", expression="soc_min <= soc <= soc_max", variable_ids=["soc_min", "soc", "soc_max"], source_constraint_ids=["soc_bounds"])]
    )

    equations, constraints = map_parametric(parametric, resolver, set())

    assert len(equations) == 1
    assert equations[0].variables == ["attribute-soc-max", "attribute-soc-min", "state-soc"]
    assert len(constraints) == 1
    assert constraints[0].id == "constraint-soc_bounds"
    assert constraints[0].scope == ["entity-battery"]