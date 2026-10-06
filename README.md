# 新能源系统 World Model

面向本科毕业设计的 L1-L6 分层工程。当前已实现：

```text
PDF
 ↓
L1 PDF -> Markdown
 ↓
Raw Markdown
 ↓
L2 Requirement / Modeling / Verification
 ↓
Validated KnowledgeState
 ↓
L3 SysML Agent
 ↓
SysMLModel
 ↓
PlantUML
```

L1 不调用 LLM；L2 负责从 Markdown 形成 Validated KnowledgeState；L3 只接收 Validated KnowledgeState，不重新读取 PDF 或 Markdown。

## Current Status

```text
Phase 0:
Project Skeleton

L1: PDF -> Markdown implemented
L2: Raw Markdown -> Validated KnowledgeState implemented
L3: Validated KnowledgeState -> SysMLModel -> PlantUML implemented
L4: Skeleton
L5: Skeleton
L6: Skeleton
```

L2 和 L3 默认测试使用 Mock LLM Client，不访问网络。真实 API 测试需要显式设置 `DEEPSEEK_API_KEY` 和 `--live`。

## L1-L6 架构

| 层 | 职责 | 当前状态 |
|---|---|---|
| L1 原始建模资料层 | PDF -> Markdown，保留标题、表格和页码结构 | PDF -> Markdown implemented |
| L2 智能建模层 | Requirement、Modeling、Verification、User Interaction | Validated KnowledgeState implemented |
| L3 标准系统模型层 | Requirements、BDD、IBD、Activity、State、Parametric；SysML Agent 和 PlantUML | Implemented |
| L4 模型编译层 | SysMLModel 到独立 World Model IR 的兼容接口 | Skeleton |
| L5 世界模型运行层 | Executable World Model、状态、步进、事件、指标 | Skeleton |
| L6 应用与优化层 | OptimizationProblem、变量、目标、约束、Solver | Skeleton |

## L2 正式 Schema

Pydantic `KnowledgeState` 只包含：

```text
entities
attributes
states
relations
processes
constraints
objectives
```

不包含 Source 或 Confidence。定义位于：

```text
l2_modeling/knowledge_state/schema.py
```

## L3 SysML Schema

`SysMLModel` 顶层严格只有六类：

```python
class SysMLModel:
    requirements: list[Requirement]
    bdd: BDD
    ibd: IBD
    activity: ActivityModel
    state: StateModel
    parametric: ParametricModel
```

内部元素包括：

- BDD：`Block`、`BlockAttribute`
- IBD：`IBDConnector`
- Activity：`ActivityAction`
- State：`StateMachine`、`StateVertex`、`StateTransition`
- Parametric：`ParameterBinding`、`Equation`

没有把 Interfaces、Connectors、Parameters、Ports 等扩展为新的顶层模型。

Pydantic 定义：

```text
l3_sysml/schema.py
```

JSON Schema：

```text
schemas/sysml/sysml_model.schema.json
```

## L3 映射关系

```text
Entity       -> BDD Block
Attribute    -> Block Attribute
Relation     -> IBD Connector
Process      -> Activity Action
State        -> State Machine / State Vertex
Constraint   -> Requirement / Parametric Equation
Objective    -> Requirement / Parametric Equation
```

确定性映射器位于：

```text
l3_sysml/mapper.py
```

LLM Agent 位于：

```text
l3_sysml/agents/sysml_agent.py
```

## 共享 DeepSeek Client

L3 不创建新的 API Client 或 API Key 配置，直接复用：

```text
l2_modeling/llm/deepseek.py
l2_modeling/llm/client.py
```

`SysMLAgent` 接收现有 `LLMClient` 实例，并使用现有 `DEEPSEEK_API_KEY` 配置。

## 运行 L3 离线 Demo

该命令使用确定性 mapper 和 PlantUML Generator，不访问网络：

```powershell
python -m l3_sysml.demo
```

输出：

```text
examples/renewable_energy/l3/demo_sysml.json
examples/renewable_energy/l3/demo_sysml.puml
```

## 运行 L3 Live Agent

使用现有 API Key 配置：

```powershell
$env:DEEPSEEK_API_KEY = "..."
python -m l3_sysml.live_test --live
```

默认命令不会调用真实 API：

```powershell
python -m l3_sysml.live_test
```

## 安装与测试

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
pytest
```

## 当前未实现

- SysML -> World Model IR 的完整语义编译
- 仿真、物理方程、SOC 动力学
- 优化、MPC、RL
- Web、FastAPI、前端
- RAG、Embedding、Vector DB
- LangGraph、CrewAI、AutoGen
- XMI、MagicDraw/Cameo、完整 SysML 解析器

## L2 -> L3 -> L4 接口

```text
L2
Validated KnowledgeState
        ↓
L3 SysMLModel
  requirements
  bdd
  ibd
  activity
  state
  parametric
        ↓
PlantUML / 人工检查
        ↓
L4
```

L4 只读取六类 `SysMLModel` 结构，不依赖 L2 的 Prompt 或 Agent。