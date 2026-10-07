"""Trace link helpers for SysML -> World Model IR compilation."""

from __future__ import annotations

from l4_compiler.world_model_ir import TraceSource


def sysml_trace(source_id: str, source_view: str, *, parent_id: str | None = None) -> TraceSource:
    return TraceSource(source_type="sysml", source_id=source_id, source_view=source_view, source_parent_id=parent_id)


def knowledge_state_trace(source_id: str, source_view: str, *, parent_id: str | None = None) -> TraceSource:
    return TraceSource(source_type="knowledge_state", source_id=source_id, source_view=source_view, source_parent_id=parent_id)


def compiler_trace(source_id: str, *, parent_id: str | None = None) -> TraceSource:
    return TraceSource(source_type="compiler", source_id=source_id, source_view="L4", source_parent_id=parent_id)