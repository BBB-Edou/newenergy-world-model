"""Deterministic legacy L1 -> L2 adapter for the Phase 0 JSON scenario."""

from __future__ import annotations

from typing import Mapping

from l1_data import Configuration, RawDataBundle
from l2_modeling.knowledge_state import Attribute, Entity, KnowledgeState, Relation


class RuleBasedKnowledgeExtractor:
    def extract(self, raw_data: RawDataBundle) -> KnowledgeState:
        entities: list[Entity] = []
        attributes: list[Attribute] = []
        relations: list[Relation] = []
        for artifact in raw_data.artifacts:
            if not isinstance(artifact, Configuration):
                continue
            for index, item in enumerate(artifact.values.get("components", []), start=1):
                if not isinstance(item, Mapping):
                    continue
                entity_id = str(item.get("id") or f"component-{index}")
                entities.append(Entity(id=entity_id, name=str(item.get("name") or entity_id), entity_type=str(item.get("kind") or "unclassified")))
                raw_attributes = item.get("attributes", {})
                if isinstance(raw_attributes, Mapping):
                    for attr_index, (name, value) in enumerate(raw_attributes.items(), start=1):
                        attributes.append(Attribute(id=f"{entity_id}-attribute-{attr_index}", entity_id=entity_id, name=str(name), value=value))
            for index, item in enumerate(artifact.values.get("relations", []), start=1):
                if not isinstance(item, Mapping):
                    continue
                source_id = item.get("source")
                target_id = item.get("target")
                if not source_id or not target_id:
                    continue
                relations.append(Relation(id=str(item.get("id") or f"relation-{index}"), relation_type=str(item.get("type") or "related_to"), source_entity_id=str(source_id), target_entity_id=str(target_id)))
        return KnowledgeState(entities=entities, attributes=attributes, relations=relations)