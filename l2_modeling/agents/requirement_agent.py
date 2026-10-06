"""RequirementAgent: Raw Markdown -> RequirementExtraction."""

from __future__ import annotations

from l2_modeling.agents.base import call_json_model, load_prompt
from l2_modeling.extraction.schema import RawDocument, RequirementExtraction
from l2_modeling.llm import LLMClient


class RequirementAgent:
    def __init__(self, llm_client: LLMClient) -> None:
        self.llm_client = llm_client

    def run(self, document: RawDocument) -> RequirementExtraction:
        system_prompt, user_template = load_prompt("requirement_agent.txt").split("---USER---", maxsplit=1)
        user_prompt = user_template.replace("{{DOCUMENT_CONTENT}}", document.content)
        return call_json_model(
            client=self.llm_client,
            agent_name=self.__class__.__name__,
            system_prompt=system_prompt.strip(),
            user_prompt=user_prompt.strip(),
            model_type=RequirementExtraction,
        )