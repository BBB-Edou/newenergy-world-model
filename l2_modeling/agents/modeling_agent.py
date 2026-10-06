"""ModelingAgent: RequirementExtraction -> KnowledgeState."""

from __future__ import annotations

from l2_modeling.agents.base import call_json_model, load_prompt
from l2_modeling.extraction.schema import RequirementExtraction
from l2_modeling.knowledge_state import KnowledgeState
from l2_modeling.llm import LLMClient


class ModelingAgent:
    def __init__(self, llm_client: LLMClient) -> None:
        self.llm_client = llm_client

    def run(self, extraction: RequirementExtraction) -> KnowledgeState:
        system_prompt, user_template = load_prompt("modeling_agent.txt").split("---USER---", maxsplit=1)
        user_prompt = user_template.replace(
            "{{EXTRACTION_JSON}}",
            extraction.model_dump_json(indent=2),
        )
        return call_json_model(
            client=self.llm_client,
            agent_name=self.__class__.__name__,
            system_prompt=system_prompt.strip(),
            user_prompt=user_prompt.strip(),
            model_type=KnowledgeState,
        )