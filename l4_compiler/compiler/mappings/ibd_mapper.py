"""IBD Connector -> World Model Interface mapping."""

from __future__ import annotations

from l3_sysml import IBD
from l4_compiler.compiler.traceability import knowledge_state_trace, sysml_trace
from l4_compiler.world_model_ir import Interface


def map_ibd(ibd: IBD, entity_id_by_block: dict[str, str]) -> list[Interface]:
    interfaces: list[Interface] = []
    for connector in sorted(ibd.connectors, key=lambda item: item.id):
        source = entity_id_by_block[connector.source_block_id]
        target = entity_id_by_block[connector.target_block_id]
        source_relation_id = connector.source_relation_id or connector.id
        trace = [sysml_trace(connector.id, "IBD")]
        if connector.source_relation_id:
            trace.append(knowledge_state_trace(connector.source_relation_id, "Relation"))
        interfaces.append(
            Interface(
                id=f"interface-{source_relation_id}",
                name=connector.relation_type,
                source=source,
                target=target,
                interface_type=connector.relation_type,
                trace=trace,
            )
        )
    return interfaces