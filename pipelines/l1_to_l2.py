"""L1 -> L2 pipeline stage."""

from __future__ import annotations

from l1_data import RawDataBundle
from l2_modeling import KnowledgeExtractor, KnowledgeState, RuleBasedKnowledgeExtractor


def run_l1_to_l2(raw_data: RawDataBundle, *, extractor: KnowledgeExtractor | None = None) -> KnowledgeState:
    return (extractor or RuleBasedKnowledgeExtractor()).extract(raw_data)