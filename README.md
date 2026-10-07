# 新能源系统 World Model

面向本科毕业设计的 L1-L6 分层工程。当前已经打通：

```text
PDF
 ↓
L1 PDF -> Markdown
 ↓
L2 Requirement / Modeling / Verification + ScenarioData
 ↓
Validated KnowledgeState + ScenarioData
 ↓
L3 SysMLAgent
 ↓
SysMLModel
 ↓
L4 Deterministic Model Compiler
 ↓
Validated WorldModelIR + ScenarioInputContract
 ↓
ScenarioInputBinding
 ↓
L5 Deterministic World Model Runtime
 ↓
SimulationResult
 ↓
L6 CVXPY Dispatch Optimization
 ↓
OptimizationResult + What-if Analysis
```

## Current Status

```text
L1: PDF -> Markdown implemented
L2: Raw Markdown -> Validated KnowledgeState + Validated ScenarioData implemented
L3: Validated KnowledgeState -> SysMLModel -> PlantUML implemented
L4: SysMLModel -> Validated WorldModelIR -> ExecutableModel interface implemented
L5: Deterministic World Model Runtime implemented
L6: CVXPY dispatch optimization + what-if implemented
```

L4 不调用 LLM，不解析 PDF/Markdown，只消费 Validated `SysMLModel`。

## L2 ScenarioData 并行分支

除 KnowledgeState 外，L2 还可以从同一份 Markdown 中提取运行场景表格：

```text
Raw Markdown
├── KnowledgeState
└── DataManifest -> ScenarioData -> ScenarioData.csv
```

LLM 只负责识别候选表格与列语义。所有原始数值由 Python 从 Markdown Table 原样提取。ScenarioData 通过现有 Verification / User Interaction 机制处理缺失值、缺失单位和非数值错误。

离线 Demo：

```powershell
python -m l2_modeling.scenario_demo
```

输出：

```text
examples/renewable_energy/scenario_data/scenario_data.json
examples/renewable_energy/scenario_data/scenario_data.csv
```

## L5 World Model Runtime

L5 直接使用真实 `WorldModelIR + ScenarioInputBinding + ScenarioData` 运行确定性离散时间仿真。

```text
ScenarioInputBinding
        ↓
WorldModelRuntime
        ↓
WorldState(t+1) = Transition(State(t), Inputs(t), Action(t))
        ↓
ConstraintEvaluator -> EventProcessor -> MetricsCollector
        ↓
SimulationResult
```

支持：

- 24h、1h timestep
- Wind / PV / Load 外部输入
- Battery SOC 演化
- 充放电功率约束
- Grid 功率平衡
- 结构化约束违规
- SimulationStart / End / Violation / SOC Boundary / Grid Limit 事件
- JSON 序列化与重新加载

运行：

```powershell
python -m l5_world_model.demo
```

输出：

```text
examples/renewable_energy/l5/simulation_result.json
```

## L6 Optimization and What-if

L6 decides *what to do*; L5 decides *what happens next*. The optimizer never
touches L5 internals: it emits a real `Action` sequence that is executed through
the existing `WorldModelRuntime`.

```text
WorldModelIR + ScenarioInputBinding
        ↓
CVXPYOptimizer            (decision)
        ↓
Optimal ActionSequence
        ↓
L5 WorldModelRuntime      (dynamics)
        ↓
SimulationResult
        ↓
OptimizationResult + consistency report
```

Decision variables (per hour, matching the L5 Battery SOC semantics in `%`):

```text
battery_charge[t]      battery_discharge[t]
grid_import[t]         curtailment[t]
battery_soc[t]         (t = 0 .. horizon)
```

Objective (MVP, explicit and not claimed to be SysML-derived):

```text
minimize sum(electricity_price[t] * grid_import[t] * delta_hours)
```

Constraints reuse the real `WorldModelIR` parameters resolved by L5
(`resolve_battery_parameters`): SOC bounds, charge/discharge limits, Grid import
limit, hourly power balance, and the L5 SOC transition equation.

After solving, the optimizer converts the CVXPY optimum into L5 `Action`s,
executes them with `WorldModelRuntime`, and compares the predicted trajectory to
the simulated one (SOC, grid import, charge, discharge, curtailment, total cost)
within a declared tolerance.

Run the closed-loop demo:

```powershell
python -m l6_optimization.demo
```

Output:

```text
examples/renewable_energy/l6/optimization_result.json
```

Run the what-if demo (battery size, price and renewable variations):

```powershell
python -m l6_optimization.what_if_demo
```

Output:

```text
examples/renewable_energy/l6/what_if_result.json
```

`pipelines/l5_to_l6.py` keeps the Phase 0 placeholder by default and switches to
the real CVXPY closed loop when a `WorldModelIR` and `ScenarioInputBinding` are
supplied.

## Scenario Input Alignment

L4 `WorldModelIR` 与 L2 `ScenarioData` 通过确定性 Binding 对齐：

```text
Validated WorldModelIR
+ Validated ScenarioData
        ↓
ScenarioAlignment
        ↓
ScenarioInputBinding
```

对齐内容包括变量映射、单位转换、时间步长和必需输入完整性。不会自动猜测变量或单位，不会插值、重采样或修改原始数据。

离线 Demo：

```powershell
python -m scenario_binding.demo
```

输出：

```text
examples/renewable_energy/scenario_data/scenario_input_binding.json
```

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

### ScenarioInputContract

`WorldModelIR` 现在正式包含：

```text
ScenarioInputContract
├── inputs[]
│   ├── name
│   ├── entity
│   ├── semantic_role
│   ├── unit
│   ├── data_type
│   ├── required
│   ├── temporal
│   └── aliases/source_ids
└── time_requirements
```

L4 Compiler 根据 Behavior 输入/输出实体、BDD Attribute、SimulationSettings 确定性地生成契约，不调用 LLM，不硬编码 Wind/PV/Load。

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
- MPC、RL、DRO、随机优化、预测模型
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