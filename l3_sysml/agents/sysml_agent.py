"""LLM-backed SysML Agent using the shared L2 DeepSeek client abstraction."""

from __future__ import annotations

from pathlib import Path

from l2_modeling.agents.base import call_json_model
from l2_modeling.knowledge_state import KnowledgeState
from l2_modeling.llm import LLMClient
from l3_sysml.schema import SysMLModel

PROMPT_PATH = Path(__file__).resolve().parents[1] / "prompts" / "sysml_agent.txt"


class SysMLAgent:
    def __init__(self, llm_client: LLMClient) -> None:
        self.llm_client = llm_client

    def run(self, knowledge_state: KnowledgeState) -> SysMLModel:
        system_prompt, user_template = PROMPT_PATH.read_text(encoding="utf-8").split("---USER---", maxsplit=1)
        user_prompt = user_template.replace(
            "{{KNOWLEDGE_STATE_JSON}}",
            knowledge_state.model_dump_json(indent=2),
        )
        return call_json_model(
            client=self.llm_client,
            agent_name=self.__class__.__name__,
            system_prompt=system_prompt.strip(),
            user_prompt=user_prompt.strip(),
            model_type=SysMLModel,
            max_tokens=8192,
        )