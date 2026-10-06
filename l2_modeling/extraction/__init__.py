"""L2 extraction schemas and compatibility adapters."""

from .base import KnowledgeExtractor
from .rule_based import RuleBasedKnowledgeExtractor
from .schema import ExtractionItem, RawDocument, RequirementExtraction

__all__ = ["ExtractionItem", "KnowledgeExtractor", "RawDocument", "RequirementExtraction", "RuleBasedKnowledgeExtractor"]