# 新能源系统 World Model

面向本科毕业设计的 L1-L6 分层工程。当前已实现两条独立、可测试的基础链路：

```text
PDF
 ↓
L1 PDF -> Markdown
 ↓
MarkdownDocument / .md
```

```text
Raw Markdown
 ↓
L2 RequirementAgent
 ↓
L2 ModelingAgent
 ↓
KnowledgeState
 ↓
VerificationAgent
 ↓
Validated KnowledgeState
```

L1 不调用 LLM；L2 不解析 PDF，只接收 Markdown。

## Current Status

```text
Phase 0:
Project Skeleton

L1: PDF -> Markdown implemented
L2: Raw Markdown -> Validated KnowledgeState implemented
L3: Skeleton
L4: Skeleton
L5: Skeleton
L6: Skeleton
```

当前 L2 未进行真实 DeepSeek API 测试。默认测试全部使用 Mock LLM Client。

## L1-L6 架构

| 层 | 职责 | 当前状态 |
|---|---|---|
| L1 原始建模资料层 | PDF 文本、结构、表格、页码和图片占位转换为 Markdown | PDF -> Markdown implemented |
| L2 智能建模层 | Requirement、Modeling、Verification、User Interaction、DeepSeek Client | Raw Markdown -> Validated KnowledgeState implemented |
| L3 标准系统模型层 | Requirement、Block、Port、Connection、Activity、StateMachine、Sequence、Constraint、Parameter | Skeleton |
| L4 模型编译层 | SysML 到独立 World Model IR 的编译接口 | Skeleton |
| L5 世界模型运行层 | Executable World Model、状态、步进、事件、指标 | Skeleton |
| L6 应用与优化层 | OptimizationProblem、变量、目标、约束、Solver、What-if 接口 | Skeleton |

## L2 正式 Schema

KnowledgeState 只包含七类模型对象，不包含 Source 或 Confidence：

- `Entity`
- `Attribute`
- `StateVariable`
- `Relation`
- `Process`
- `Constraint`
- `Objective`

结构：

```python
class KnowledgeState:
    schema_version: str = "1.0"
    entities: list[Entity]
    attributes: list[Attribute]
    states: list[StateVariable]
    relations: list[Relation]
    processes: list[Process]
    constraints: list[Constraint]
    objectives: list[Objective]
```

正式 Pydantic 定义：

```text
l2_modeling/knowledge_state/schema.py
```

生成后的 JSON Schema：

```text
schemas/knowledge_state/knowledge_state.schema.json
schemas/knowledge_state/requirement_extraction.schema.json
schemas/knowledge_state/verification_result.schema.json
```

## L2 四个逻辑 Agent

```python
RequirementAgent.run(document: RawDocument) -> RequirementExtraction
ModelingAgent.run(extraction: RequirementExtraction) -> KnowledgeState
VerificationAgent.verify(state: KnowledgeState) -> VerificationResult
UserInteractionAgent.generate_questions(state, verification) -> QuestionSet
UserInteractionAgent.apply_answers(state, answers) -> StateUpdateResult
```

`L2Orchestrator` 按照以下有限循环运行：

```text
RequirementAgent
  -> ModelingAgent
  -> VerificationAgent
  -> VALID: return
  -> NEED_INPUT: generate questions -> apply answers -> verify again
  -> INVALID: FAILED
```

默认最多 5 轮，不允许无限循环。

## DeepSeekClient

`l2_modeling/llm/deepseek.py` 使用 OpenAI Python SDK 调用 DeepSeek OpenAI-compatible API：

```python
DeepSeekClient(
    api_key=None,
    model=None,
    base_url="https://api.deepseek.com",
)
```

API Key 优先级：

1. 构造函数显式 `api_key`
2. 环境变量 `DEEPSEEK_API_KEY`

模型可通过参数或环境变量 `DEEPSEEK_MODEL` 配置。密钥不会写入 KnowledgeState、验证结果、日志或测试结果，也不会在 `repr` 中完整显示。

## 运行 L1

```powershell
python pipelines/l1_pdf_to_markdown.py examples/renewable_energy/pdf/demo.pdf
```

输出：

```text
data/processed/markdown/demo.md
```

## 运行 L2 离线 Demo

该命令只使用脚本化 Mock LLM，不访问网络：

```powershell
python -m l2_modeling.demo
```

Demo Markdown：

```text
examples/renewable_energy/l2/demo_system.md
```

Demo 输出一个 VALID KnowledgeState，包含 Wind、PV、Battery、Grid、Load，以及对应属性、状态、关系、过程、约束和目标。

## Live DeepSeek Test

默认不运行：

```powershell
python -m l2_modeling.live_test examples/renewable_energy/l2/demo_system.md
```

只有显式提供 `--live` 和 API Key 才会真实调用：

```powershell
$env:DEEPSEEK_API_KEY = "..."
python -m l2_modeling.live_test examples/renewable_energy/l2/demo_system.md --live
```

或者：

```powershell
python -m l2_modeling.live_test examples/renewable_energy/l2/demo_system.md --live --api-key "..."
```

本次交付没有执行真实 API 测试。

## 安装与测试

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
pytest
```

普通测试不调用真实 DeepSeek。

## 当前未实现

- SysML 生成与完整 SysML 标准
- World Model IR 动态编译
- 仿真、物理方程、SOC 动力学
- 优化、MPC、RL
- Web、FastAPI、前端
- RAG、Embedding、Vector DB
- LangGraph、CrewAI、AutoGen
- OCR 与图片视觉理解
- 真实 DeepSeek API 测试

## L2 -> L3 正式接口

```python
KnowledgeState
```

L3 只能读取 KnowledgeState 中正式的七类对象：

```text
entities
attributes
states
relations
processes
constraints
objectives
```

L3 不得依赖 DeepSeek、Prompt、Agent 或 L2 内部实现。当前 L2 输出：

```text
Validated KnowledgeState
```