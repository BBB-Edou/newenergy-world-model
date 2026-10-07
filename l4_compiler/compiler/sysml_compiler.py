"""Compatibility alias for the canonical L4 ModelCompiler."""

from __future__ import annotations

from .compiler import ModelCompiler


class SysMLToWorldModelCompiler(ModelCompiler):
    """Backward-compatible compiler class name."""