# Architecture Overview

The project separates concerns into six replaceable layers:

| Layer | Input | Output | Main contract |
|---|---|---|---|
| L1 | PDF (legacy skeleton keeps other raw artifact types) | `RawDocument` -> Markdown / `MarkdownDocument` | PDF structure is preserved without LLM interpretation |
| L2 | Markdown `RawDocument` | Validated `KnowledgeState` | four logical agents, deterministic verification, limited user interaction loop |
| L3 | `KnowledgeState` | `SysMLModel` | requirements, blocks, ports, connections, activities, state machines, sequences, constraints, parameters |
| L4 | `SysMLModel` | `WorldModelIR` | independent IR with entities, state variables, parameters, dynamics, events, interfaces and simulation settings |
| L5 | `WorldModelIR` | `SimulationResult` | executable model contract and runtime state |
| L6 | `SimulationResult` | `OptimizationResult` | model-neutral optimization problem and solver contract |

The dependency direction is downwards only. A lower layer does not import a higher layer. L5 never imports a SysML tool, and L6 never imports a concrete world model implementation.

## Extension rules

1. Add a new source adapter behind the relevant Protocol rather than changing callers.
2. Extend data classes through new fields with explicit defaults or new subclasses.
3. Keep physical formulas in L5 dynamics modules, not in the L2 extractor or L4 compiler.
4. Keep solver formulations in L6 adapters, not in the pipeline.
5. Add a contract test before replacing a placeholder implementation.