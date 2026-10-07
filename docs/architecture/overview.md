# Architecture Overview

The project separates concerns into six replaceable layers:

| Layer | Input | Output | Main contract |
|---|---|---|---|
| L1 | PDF (legacy skeleton keeps other raw artifact types) | `RawDocument` -> Markdown / `MarkdownDocument` | PDF structure is preserved without LLM interpretation |
| L2 | Markdown `RawDocument` | Validated `KnowledgeState` | four logical agents, deterministic verification, limited user interaction loop |
| L3 | Validated `KnowledgeState` | `SysMLModel` -> PlantUML | exactly six sections: Requirements, BDD, IBD, Activity, State, Parametric |
| L4 | Validated `SysMLModel` | Validated `WorldModelIR` | deterministic six-view mapping, traceability, IR validation and ExecutableModel interface |
| L5 | `WorldModelIR` | `SimulationResult` | executable model contract and runtime state |
| L6 | `WorldModelIR` + `ScenarioInputBinding` (+ optional `SimulationResult`) | `OptimizationResult` (+ `SimulationResult`, `WhatIfResult`) | CVXPY dispatch optimization emitting L5 `Action`s; model-neutral problem+solver contract retained |

The dependency direction is downwards only. A lower layer does not import a higher layer. L5 never imports a SysML tool, and L6 never imports a concrete world model implementation.

## Extension rules

1. Add a new source adapter behind the relevant Protocol rather than changing callers.
2. Extend data classes through new fields with explicit defaults or new subclasses.
3. Keep physical formulas in L5 dynamics modules, not in the L2 extractor or L4 compiler.
4. Keep solver formulations in L6 adapters, not in the pipeline.
5. Add a contract test before replacing a placeholder implementation.