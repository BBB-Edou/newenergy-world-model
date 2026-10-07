from __future__ import annotations

from l3_sysml import IBD, IBDConnector
from l4_compiler.compiler.mappings import map_ibd


def test_ibd_connector_maps_to_interface() -> None:
    interfaces = map_ibd(
        IBD(block_ids=["block-wind", "block-load"], connectors=[IBDConnector(id="connector-wind-load", source_block_id="block-wind", target_block_id="block-load", relation_type="supplies", source_relation_id="wind_to_load")]),
        {"block-wind": "entity-wind", "block-load": "entity-load"},
    )

    assert len(interfaces) == 1
    assert interfaces[0].id == "interface-wind_to_load"
    assert interfaces[0].source == "entity-wind"
    assert interfaces[0].target == "entity-load"
    assert interfaces[0].interface_type == "supplies"