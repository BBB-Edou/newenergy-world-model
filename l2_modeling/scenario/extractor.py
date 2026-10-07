"""LLM interpretation of candidate tables into a DataManifest."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from l2_modeling.agents.base import call_json_model
from l2_modeling.extraction.schema import RawDocument
from l2_modeling.llm import LLMClient
from l2_modeling.scenario.markdown_tables import MarkdownTable, scenario_candidates
from l2_modeling.scenario.schema import DataManifest, ScenarioExtraction, ScenarioSource


PROMPT_PATH = Path(__file__).resolve().parents[1] / "prompts" / "scenario_data_agent.txt"


@dataclass(slots=True)
class ScenarioDataExtractor:
    llm_client: LLMClient
    last_candidates: list[MarkdownTable] = field(default_factory=list)

    def extract(self, document: RawDocument) -> ScenarioExtraction:
        candidates = scenario_candidates(document.content)
        self.last_candidates = candidates
        if not candidates:
            return ScenarioExtraction(document_id=document.document_id, manifests=[])

        prompt = PROMPT_PATH.read_text(encoding="utf-8")
        system_prompt, user_template = prompt.split("---USER---", maxsplit=1)
        candidate_payload = [
            {"table_id": table.table_id, "page": table.page, "headers": table.headers, "rows": table.rows}
            for table in candidates
        ]
        user_prompt = user_template.replace("{{CANDIDATE_TABLES_JSON}}", json.dumps(candidate_payload, ensure_ascii=False, indent=2))
        extraction = call_json_model(
            client=self.llm_client,
            agent_name=self.__class__.__name__,
            system_prompt=system_prompt.strip(),
            user_prompt=user_prompt.strip(),
            model_type=ScenarioExtraction,
        )
        by_id = {table.table_id: table for table in candidates}
        corrected: list[DataManifest] = []
        for manifest in extraction.manifests:
            table = by_id.get(manifest.table_id)
            if table is None:
                continue
            source = ScenarioSource(document=document.filename or document.document_id, table_id=table.table_id, page=table.page)
            corrected.append(manifest.model_copy(update={"source": source}))
        return extraction.model_copy(update={"document_id": document.document_id, "manifests": corrected})