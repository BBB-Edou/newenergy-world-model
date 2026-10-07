"""Deprecated compatibility module.

Canonical BDD mapping now lives in compiler.mappings.bdd_mapper.
"""

from __future__ import annotations

from l4_compiler.compiler.mappings.bdd_mapper import infer_value_type as map_parameter_type
from l4_compiler.compiler.mappings.bdd_mapper import map_bdd

__all__ = ["map_bdd", "map_parameter_type"]