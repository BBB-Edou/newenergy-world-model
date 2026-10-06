# Layer Contracts

## L1 -> L2

Implemented input is Markdown:

```text
FileMarkdownLoader.load(markdown_path) -> MarkdownDocument
RawDocument.from_markdown_document(markdown_document) -> RawDocument
```

L1 does not call an LLM. L2 does not parse PDF.

## L2 -> L3

The formal boundary is the Pydantic `KnowledgeState`:

```text
schema_version
entities
attributes
states
relations
processes
constraints
objectives
```

`KnowledgeState` does not contain Source, Confidence, Prompt, Agent, or LLM-provider fields. L3 may read only these seven categories.

## L2 Internal Contracts

```text
RequirementAgent.run(RawDocument) -> RequirementExtraction
ModelingAgent.run(RequirementExtraction) -> KnowledgeState
VerificationAgent.verify(KnowledgeState) -> VerificationResult
UserInteractionAgent.generate_questions(KnowledgeState, VerificationResult) -> QuestionSet
UserInteractionAgent.apply_answers(KnowledgeState, list[UserAnswer]) -> StateUpdateResult
L2Orchestrator.run(RawDocument, max_interaction_rounds=5) -> L2PipelineResult
```

`VerificationResult.status` is one of `VALID`, `NEED_INPUT`, `INVALID`.

`L2PipelineResult.status` is one of `VALID`, `NEED_USER_INPUT`, `FAILED`.

## LLM Boundary

`DeepSeekClient` implements the OpenAI-compatible chat-completions API. Agents receive an `LLMClient`-compatible object and request:

```json
{"type": "json_object"}
```

Invalid JSON or Pydantic validation is retried once and then raises `AgentOutputError`.

## L3 -> L4

`SysMLModel` is a neutral subset, not a complete SysML implementation. `WorldModelIR` is independent and must not expose SysML classes to L5.

## L4 -> L5

`ExecutableWorldModel` exposes `initialize()`, `step()`, `run()`, `get_state()`, `apply_action()` and `calculate_metrics()`.

## L5 -> L6

`SimulationResult` is sufficient to create an `OptimizationProblem`. A solver adapter returns `OptimizationResult`.
## L3 SysML Contract

`SysMLAgent.run(validated_knowledge_state) -> SysMLModel` uses the shared `LLMClient` from L2.

`SysMLModel` contains exactly:

```text
requirements
bdd
ibd
activity
state
parametric
```

No additional top-level SysML branches are introduced. `PlantUMLGenerator.generate(sysml_model) -> str` renders all six sections for human inspection.