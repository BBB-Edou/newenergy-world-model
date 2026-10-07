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

Two paths are supported.

Placeholder path (Phase 0), kept for backward compatibility:

```text
build_optimization_problem(SimulationResult) -> OptimizationProblem
PlaceholderSolver.solve(OptimizationProblem) -> OptimizationResult
```

Real path (L6 MVP):

```text
CVXPYOptimizer.solve(
    world_model_ir=WorldModelIR,
    scenario_binding=ScenarioInputBinding,
    scenario_data=ScenarioData,
    initial_state=WorldState | None,
    simulation_config=SimulationConfig,
    optimization_config=OptimizationConfig,
) -> OptimizationResult
```

L6 emits a real L5 `Action` sequence and does not modify L5 internals: the
optimizer executes the actions through `WorldModelRuntime` and returns the
resulting `SimulationResult` plus a numerical consistency report. `run_l5_to_l6`
selects the real path only when `world_model_ir` and `binding` are supplied.
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
## L4 World Model IR Contract

`compile_sysml_to_world_model(sysml_model) -> WorldModel` consumes only the validated six-part L3 `SysMLModel` and performs deterministic mapping without LLM calls.

`WorldModel` contains exactly:

```text
metadata
entities
attributes
states
behaviors
events
equations
constraints
objectives
interfaces
```

Every mapped object carries `trace` links back to SysML source ids and, where available, KnowledgeState ids. `validate_world_model()` checks structural and reference integrity before the IR is exposed to L5.
## L2 ScenarioData Side Channel

`ScenarioDataExtractor` interprets candidate Markdown tables into `DataManifest` objects using the shared LLM client. `build_scenario_data()` then copies cell values from the original Markdown table deterministically. No LLM-generated numeric values enter `ScenarioData`.

`VerificationAgent.verify_scenario_data()` reuses the existing `VerificationResult` and `UserInteractionAgent` supports field-targeted ScenarioData corrections. `ScenarioData` remains independent from L3/L4 and is combined with `WorldModelIR` only at the L5 input boundary.
## Scenario Input Binding Contract

`ScenarioAlignment.align(world_model, scenario) -> ScenarioInputBinding` is deterministic and performs no LLM call.

Alignment checks:

- required input presence from `WorldModelMetadata.required_inputs` or `Interface.variable_ids`
- exact variable names, or explicit `ScenarioData.metadata["variable_aliases"]`
- deterministic unit compatibility and conversion metadata
- time-step equality without resampling
- structured READY / NEED_INPUT / INVALID summary

The binding does not mutate either input and is the interface handed to L5.
## L5 Runtime Contract

L5 consumes the real `WorldModelIR`, `ScenarioInputBinding`, and `ScenarioData` produced by upstream layers.

```text
WorldModelRuntime(
    world_model=...,
    binding=...,
    scenario=...,
    config=...,
    initial_state=...,
    action_policy=...,
).run() -> SimulationResult
```

The runtime performs deterministic state transitions and returns structured `SimulationResult` containing states, actions, inputs, events, constraint violations, per-step metrics, summary metrics, and final state. It does not optimize actions or modify L1-L4.
## ScenarioInputContract

`WorldModelIR` carries a formal `ScenarioInputContract` generated deterministically by L4. Each `ScenarioInputSpec` declares name, owning entity, semantic role, unit, data type, required/temporal flags, aliases, and source IDs. `time_requirements` declares step size, horizon, time unit, and timestamp field.

Scenario Alignment uses the contract as the source of truth for required-input checks, units, numeric data types, and horizon sufficiency. L5 consumes only the validated Binding and does not infer input semantics.