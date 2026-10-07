from __future__ import annotations

from l3_sysml import BDD, Block, BlockAttribute
from l4_compiler.compiler.mappings import map_bdd


def test_bdd_blocks_and_attributes_map_to_entities_and_attributes() -> None:
    bdd = BDD(
        blocks=[
            Block(
                id="block-battery",
                name="Battery",
                block_type="storage",
                source_entity_id="battery",
                attributes=[BlockAttribute(id="attr-capacity", name="capacity", value=200, unit="kWh", source_attribute_id="battery_capacity")],
            )
        ]
    )

    entities, attributes, entity_by_block, attributes_by_source = map_bdd(bdd)

    assert [entity.id for entity in entities] == ["entity-battery"]
    assert attributes[0].id == "attribute-battery_capacity"
    assert attributes[0].owner == "entity-battery"
    assert entity_by_block["block-battery"] == "entity-battery"
    assert attributes_by_source["battery_capacity"] == "attribute-battery_capacity"