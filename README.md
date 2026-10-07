# 新能源系统 World Model

面向本科毕业设计的 L1-L6 分层工程。当前已经打通：

```text
PDF
 ↓
L1 PDF -> Markdown
 ↓
L2 Requirement / Modeling / Verification
 ↓
Validated KnowledgeState
 ↓
L3 SysMLAgent
 ↓
SysMLModel
 ↓
L4 Deterministic Model Compiler
 ↓
Validated WorldModelIR
 ↓
ExecutableModel Interface
```

## Current Status

```text
L1: PDF -> Markdown implemented
L2: Raw Markdown -> Validated KnowledgeState implemented
L3: Validated KnowledgeState -> SysMLModel -> PlantUML implemented
L4: SysMLModel -> Validated WorldModelIR -> ExecutableModel interface implemented
L5: Skeleton
L6: Skeleton
```

L4 不调用 LLM，不解析 PDF/Markdown，只消费 Validated `SysMLModel`。

## L4 WorldModel IR

顶层结构由 Pydantic Schema 固定为：

```text
WorldModel
├── metadata
├── entities
├── attributes
├── states
├── behaviors
├── events
├── equations
├── constraints
├── objectives
└── interfaces
```

正式定义位于：

```text
l4_compiler/world_model_ir/schema.py
```

所有 IR 对象具有稳定 ID 和 `trace`，可以追溯：

```text
WorldModelIR object
        ↓
SysML source id / source view
        ↓
KnowledgeState source id
```

## L4 Compiler Pipeline

```text
Validated SysMLModel
        ↓
SysML Loader
        ↓
SysML Validator
        ↓
SysML Normalizer
        ↓
BDD / IBD / Activity / State / Parametric / Requirement Mappers
        ↓
WorldModelIR
        ↓
IR Validator
        ↓
JSON Exporter
```

主要接口：

```python
compile_sysml_to_world_model(sysml_model) -> WorldModel
validate_world_model(world_model) -> IRValidationReport
export_world_model_json(world_model) -> str
```

支持的映射：

```text
BDD Block            -> Entity
BlockAttribute       -> Attribute
IBD Connector        -> Interface
ActivityAction       -> Behavior
StateVertex          -> State
StateTransition      -> Event
Parametric Equation  -> Equation
Constraint/Equation  -> Constraint
Requirement          -> Constraint / Objective
```

## 运行 L4 Demo

```powershell
python -m l4_compiler.demo
```

输出：

```text
examples/renewable_energy/l4/world_model.json
```

当前 Demo 编译结果：

```text
IR valid: True
Entities: 5
Attributes: 9
States: 1
Behaviors: 5
Events: 0
Equations: 2
Constraints: 1
Objectives: 1
Interfaces: 4
```

`Events: 0` 是因为当前 L3 Demo 的 Battery State Machine 没有显式 `StateTransition`。Compiler 不会凭空生成事件；当 SysML 提供 transition 时，会确定性地生成 `Event`。

## L5 Executable Interface

L4 只定义接口：

```text
l4_compiler/runtime/executable_model.py
```

```python
initialize(initial_state)
step(action, inputs)
apply_event(event)
get_state()
check_constraints()
calculate_metrics()
```

不在 L4 实现仿真动力学。

## 安装与测试

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
pytest
```

## 当前未实现

- 完整物理动态和仿真引擎
- 复杂数学公式自动推导
- 优化、MPC、RL
- Web、FastAPI、前端
- RAG、Embedding、Vector DB
- XMI、MagicDraw/Cameo、完整 SysML 解析器

## 层间正式接口

```text
L2 -> L3:
Validated KnowledgeState

L3 -> L4:
SysMLModel
  requirements / bdd / ibd / activity / state / parametric

L4 -> L5:
WorldModelIR
  metadata / entities / attributes / states / behaviors / events /
  equations / constraints / objectives / interfaces
```

L4 只依赖 L3 的正式 Pydantic Schema，不依赖 L2 Prompt、Agent 或 DeepSeek。