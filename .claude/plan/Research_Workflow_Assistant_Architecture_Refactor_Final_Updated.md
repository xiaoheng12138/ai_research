---
id: plan-20260118-arch-refactor-v2
scenario: system.refactor
risk: medium
created_at: 2026-01-18
models:
  - claude
  - codex
  - gemini
inputs:
  - architecture-refactor.md
outputs:
  - .claude/commands/research/*.md (21 files migrated)
  - .claude/agents/research/*.md (8 agents)
  - .claude/.research/* (config + prompts + schemas + ui)
  - src/research_workflow_assistant/bridge/* (model bridge + trace)
  - src/research_workflow_assistant/workflow/* (evidence gate + manifest)
  - src/research_workflow_assistant/ui/* (webui adapter + server)
  - artifacts/* (output directories)
---

# 📋 实施计划：Research Workflow Assistant 架构重构（最终校验版）

### 任务类型
- [x] 后端 (→ Codex)：架构设计、路由逻辑、多模型协作协议
- [x] 前端 (→ Gemini)：UX 设计、命令交互、结果呈现
- [√] 全栈 (→ 并行)：同时包含

> **目标**：以 Claude Code 为运行载体，参考 CCG 的“多模型交互与编排”架构，重构为面向科研的 Skills 系统；并新增 **复用 CCG WebUI** 的能力，将 Codex / Gemini 的“可展示推理”与结果过程化呈现。
 **参考的项目**：D:\ccg-workflow-main，复用其WebUI时可参考。

## 0. 本版修订说明（相对 architecture-refactor.md）

1. **删除“CLI 作为用户入口”的暗示**：
   - 唯一用户入口是 Claude Code 的 `/research` 与各域 `/lit:* /idea:* /data:* /sim:* /write:*` 斜杠命令。
   - 所有脚本/命令行仅作为 *Skills 的内部后端桥接*（deterministic），不承担自然语言意图识别。
2. **新增：复用 CCG WebUI**（可选开启）
   - 用于可视化 Codex/Gemini 输出与工作流事件流（trace），并展示 Evidence Gate 的验证标注。
3. **强化三模型定位（科研导向）**：
   - **Claude（主载体）**：工作流编排与路由、风险门控、产物落盘、最终裁决。
   - **Codex（推理主力）**：科研推理、长期任务规划、实验/仿真/数据链路的可执行拆解与审计。
   - **Gemini（世界知识 + 创意表达）**：头脑风暴、方案联想、写作组织与表达；其事实性陈述默认需要 Evidence Gate 或交叉验证。
4. **修正：SESSION_ID 不应写死**：改为运行时动态获取与持久化管理。

## 1. 设计原则与边界（防过度设计）

### 1.1 设计原则
- **AI-first 意图识别**：意图识别与路由只发生在 Claude（intent-router agent + taxonomy/mapping），不引入 CLI parser 或规则引擎来“抢答意图”。
- **Deterministic Guardrails**：对高风险动作采用 confirm/preview；对 Gemini 的“事实性主张”统一走 Evidence Gate。
- **单一事实来源（SSoT）**：研究配置与角色提示词统一以 `.claude/.research/` 为准；Claude Code 规定路径的 agent 文件放在 `.claude/agents/`（内容与 `.claude/.research/prompts/claude/` 同步）；运行态只放在 `.research/`；产物只放在 `artifacts/`。
- **可视化是“观测层”，不是“控制层”**：WebUI 只展示与回放，不直接成为新的交互入口（避免再造一套产品面）。

### 1.2 明确不做
- 不做独立 CLI 应用来承接用户自然语言（避免与 `/research` 入口竞争、也避免意图误判）。
- 不做复杂插件系统/市场（先把“研究闭环”做通：文献→想法→数据/仿真→写作）。
- 不做 WebUI 上的在线编辑/执行（执行仍在 Claude Code 的命令与门控中完成）。

## 2. 技术方案（Strangler + 观测层增强）

采用 **Strangler 迁移策略**（先建新骨架 + 双路径兼容 + 分阶段切换）：
1. 先落地目录骨架 + 配置事实来源（`.claude/.research`）
2. 建立统一 **Model Bridge**（Codex/Gemini 调用 + 会话管理 + trace 事件流）
3. 重写协议与命令文件，清除所有 `.ccg` 引用（包括角色提示词路径、绝对路径）
4. 接入 **CCG WebUI 复用层**：让 trace + 子模型输出可视化（可选开启）
5. 最后清理重复与旧目录，补齐测试与示例

---

## 3. 实施步骤

### Phase 0：目录骨架与基线整理（P0）

#### Step 0.1：创建目标目录结构
> 在原骨架基础上 **新增 UI 与 trace 目录**。

```
.claude/
├── commands/research/          # 21 个命令文件迁移目标
├── agents/research/            # 8 个 agent 文件
└── .research/
    ├── _protocol.md            # Protocol v2（需重写）
    ├── capabilities.yaml       # 能力映射
    ├── scenarios.yaml          # 场景定义
    ├── intent-taxonomy.yaml    # 意图分类
    ├── intent-mapping.yaml     # 意图-模块映射
    ├── prompts/
    │   ├── registry.yaml       # 提示词注册表（Claude/Codex/Gemini 角色映射）
    │   ├── claude/
    │   │   ├── orchestrator.md
    │   │   ├── intent-router.md
    │   │   ├── planner.md
    │   │   ├── verifier.md
    │   │   ├── librarian.md
    │   │   ├── data-analyst.md
    │   │   ├── simulation-engineer.md
    │   │   └── writer.md
    │   ├── codex/
    │   │   ├── planner.md
    │   │   ├── reasoner.md
    │   │   ├── engineer.md
    │   │   └── reviewer.md
    │   └── gemini/
    │       ├── ideator.md
    │       ├── writer.md
    │       ├── explainer.md
    │       └── designer.md
    ├── schemas/
    │   ├── plan.schema.json
    │   ├── evidence.schema.json
    │   ├── manifest.schema.json
    │   └── trace.schema.json          # 新增：trace 事件（最小字段）
    ├── templates/
    │   ├── plan.md
    │   └── report.md
    └── ui/
        ├── ccg-webui/                 # 新增：复用的 WebUI 前端（vendor）
        └── ui.config.yaml             # 新增：UI 开关/端口/trace level

.research/                      # Runtime 目录（从配置目录转变）
├── tasks/
├── plans/
├── logs/
│   └── traces/                 # 新增：trace jsonl 文件
├── cache/
└── kb/

artifacts/                      # 产物目录
├── reports/
├── figures/
├── processed-data/
├── models/
├── papers/
├── writing/
└── manifest/
```

#### Step 0.2：迁移命令文件
从 `commands/research/*.md` → `.claude/commands/research/*.md`

需迁移的 21 个文件：
1. `_protocol.md` → 重写为 Protocol v2
2. `research.md`
3. `research-help.md`
4. `lit-search.md`
5. `lit-ingest.md`
6. `lit-summarize.md`
7. `lit-compare.md`
8. `lit-cite.md`
9. `idea-brainstorm.md`
10. `idea-evaluate.md`
11. `data-process.md`
12. `data-train.md`
13. `data-calibrate.md`
14. `data-compare.md`
15. `sim-modify.md`
16. `sim-batch.md`
17. `sim-debug.md`
18. `sim-odb.md`
19. `write-paper.md`
20. `write-patent.md`
21. `write-patent-search.md`

#### Step 0.3：迁移配置文件
从 `.research/*.yaml` → `.claude/.research/*.yaml`

需迁移的 4 个文件：
- `capabilities.yaml`
- `scenarios.yaml`
- `intent-taxonomy.yaml`
- `intent-mapping.yaml`

处理 `src/research_workflow_assistant/registry/data/*.yaml` 重复：
- 短期保留作为 fallback
- 中期统一到 `.claude/.research/`

#### Step 0.4：更新 .gitignore
> 新增忽略 trace 日志与 UI 运行态输出（如有）。

```gitignore
# Runtime (不入库)
.research/cache/
.research/logs/
.research/tasks/*.state.json

# Trace (不入库)
.research/logs/traces/

# Artifacts (大文件不入库)
artifacts/**/*.pdf
artifacts/**/*.odb
artifacts/models/
artifacts/processed-data/

# 保留示例
!artifacts/reports/.gitkeep
!artifacts/figures/.gitkeep
```

---

### Phase 1：核心协议 + 模型桥接 + 可视化（P0）

#### Step 1.1：Protocol v2 重写（科研导向 + 可视化友好）
文件：`.claude/.research/_protocol.md`

必须包含：
- Plan Card / Result Card / Evidence Record / Artifact Manifest 格式
- 风险门控规则：none/low/medium/high → auto/confirm/confirm+preview
- 协作模式：S（单模型）/ X（交叉验证）/ T（三角协作）
- **“可展示推理”约束**：要求 Codex/Gemini 输出 *可供 UI 展示的推理结构*（而不是无边界冗长思维流）
- 外部模型不落盘原则（仅保留必要结果、trace 可做脱敏/截断）
- 证据门控：主张分类（fact/inference/speculation）+ 状态（verified/unverified/rejected）
- **WebUI 钩子**：每次子模型调用都写入 trace（run_id/task_id、backend、role、输入摘要、输出摘要、artifact refs）

#### Step 1.2：Claude/Codex/Gemini 提示词体系（科研三角协作对齐）
新建 16 个角色提示词，并明确其“展示层输出”结构：

**Claude 角色（主控编排，负责路由/门控/仲裁/落盘）**
- `orchestrator.md`：总控编排、选择协作模式（S/X/T）、风险门控、调度 Codex/Gemini、产物落盘与 UI 输出摘要（输出：Plan Card/Result Card 关键块 + 调度决策摘要）
- `intent-router.md`：意图识别与命令推荐（taxonomy/mapping + 置信度）；低置信度进入澄清（输出：intent + confidence + next_question）
- `planner.md`：将用户目标转为可执行计划（驱动 Codex planner/reasoner）；拆分里程碑/依赖/验证点（输出：Plan Card 草案 + 风险解释）
- `verifier.md`：Evidence Gate：抽取/归类/验证主张，标注 ✅/⚠️/❌；必要时调度 Codex reviewer 审计（输出：Evidence Record + To-Verify 清单）
- `librarian.md`：文献筛选、去重、聚类、引用管理（驱动 Codex reasoner + Gemini explainer）（输出：阅读清单 + 引用建议 + 待核对点）
- `data-analyst.md`：数据流程、指标、可视化建议（驱动 Codex engineer + Gemini explainer）（输出：分析路径 + 可复现步骤 + 风险点）
- `simulation-engineer.md`：仿真脚本/作业/后处理策略（驱动 Codex engineer + Codex reviewer）（输出：可执行步骤 + 资源/成本风险门控建议）
- `writer.md`：论文/专利写作结构一致性（驱动 Gemini writer + Codex reviewer）（输出：章节结构 + 术语表 + 事实性主张待核对点）

> **阶段对齐建议（Claude 如何“指挥” Codex/Gemini）**：
> 1) 路由阶段：`intent-router` → 选择目标命令/场景与模式（S/X/T）
> 2) 计划阶段：`orchestrator/planner` → 产出 Plan Card + 选择 Codex/Gemini 角色组合
> 3) 执行阶段：`orchestrator` → 通过 Model Bridge 调用 Codex/Gemini（只传结构化上下文；不落盘原始 prompt/response）
> 4) 验证阶段：`verifier` → Evidence Gate（必要时调度 `codex/reviewer` 复核 Gemini 的事实性主张）
> 5) 交付阶段：`orchestrator/writer` → 仲裁整合 + 产物落盘 + Manifest/trace

**Codex 角色（推理主力，偏结构化，可长期规划）**
- `planner.md`：长期规划/里程碑/依赖拆解（输出：JSON Plan + 关键假设）
- `reasoner.md`：科研推理/论证链/反例检查/风险矩阵（输出：JSON + 论证链）
- `engineer.md`：脚本/实验/仿真可复现步骤；涉及改文件→diff-only（输出：diff + 变更说明）
- `reviewer.md`：审计 Gemini 主张/检查漏洞/提出验证方案（输出：Issue 列表 + 验证优先级）

**Gemini 角色（世界知识 + 创意表达，默认需验证）**
- `ideator.md`：创意发散（输出：Ideas + Claims + Evidence Needed）
- `writer.md`：写作润色（输出：Draft + Uncertainties；禁止编造 DOI/作者/年份）
- `explainer.md`：科普/叙事组织（输出：Narrative + To-Verify Checklist）
- `designer.md`：图表/呈现设计（输出：Figure Specs + Data Needed）

> **关键校验**：所有 Gemini 输出必须显式区分 fact/inference/speculation，并生成“待核对点”，以便 Evidence Gate 标注；Claude `verifier` 负责把用于最终交付的 fact 主张推进到 verified 或改写为 inference/speculation。

#### Step 1.3：结构化 Schema（新增 trace）
保留 3 个核心 Schema，并新增 1 个最小 trace schema：
- `plan.schema.json`
- `evidence.schema.json`
- `manifest.schema.json`
- `trace.schema.json`（最小字段：ts/run_id/task_id/backend/role/phase/content/artifacts）

> 说明：trace schema 只校验“形状”，不约束 content 的语义，以免造成开发负担。

#### Step 1.4：Model Bridge（统一调用 + 会话管理 + trace）
新建 Python 模块：`src/research_workflow_assistant/bridge/`

核心能力：
1. **统一调用接口**：Codex/Gemini 的请求渲染、role prompt 装载、输出解析
2. **会话管理**：自动获取/复用 session_id（不写死）
3. **trace 事件流**：对“请求→流式输出→完成/错误”写入 `.research/logs/traces/<run_id>.jsonl`
4. **WebUI 对接**：当 UI 开启时，将 trace 事件推送给 UI（SSE/WebSocket）

伪代码：
```python
# bridge/model_bridge.py
class ModelBridge:
    def run(self, backend: str, role: str, task: str,
            context: dict,
            output_format: str = "json",
            run_id: str | None = None,
            trace: bool = True,
            trace_level: str = "brief") -> "ModelOutput":
        """统一模型调用接口（不做意图识别）"""
        ...

# bridge/session_store.py
# 存储位置：.research/tasks/sessions.json
# 结构：{ "codex": {"session_id": "...", "updated_at": "..."}, "gemini": {...} }
```

#### Step 1.5：桥接入口（供 Skills 调用，非用户入口）
> 这一步是对“CLI 扩展”的收敛：**只保留最小、确定性的桥接入口**，用于命令文件内调用，不接收自然语言。

方式：`python -m research_workflow_assistant.bridge.run --request <json> --out <json>`

请求文件（示例）：
```json
{
  "backend": "codex",
  "role": "reasoner",
  "task": "为某研究问题建立论证链并列出关键假设",
  "context": {"project": "...", "files": ["..."]},
  "output_format": "json",
  "trace": true,
  "trace_level": "brief"
}
```

> 说明：桥接入口只处理结构化请求，因此不存在“误判意图”的问题。

#### Step 1.6：复用 CCG WebUI（可视化层）
目标：把 Codex/Gemini 的“可展示推理”与执行过程可视化（观测层），并在同一时间线中呈现 Evidence Gate / Artifacts 等关键事件。

**先做一次“可复用性勘查”（避免过度实现）**
- 明确 CCG WebUI 属于哪一层（随 runner/wrapper 内置，还是独立前端/服务）
- 明确事件协议/接口（SSE/WS/文件轮询）与最小数据字段
- 输出一份 `docs/ui-compat.md`：RWA trace → CCG UI 事件的字段映射与差异点

**复用路线（按优先级选择，尽量走 A）**
- A. **直接启用 CCG WebUI**（若其随 codeagent-wrapper/runner 提供）
  - Model Bridge 只需：①开启 UI；②输出/转写兼容事件；③把 run_id/task_id 与 UI 会话关联
  - 优点：几乎不写 UI 代码；风险：对外部组件耦合更强，需要锁定版本/接口
- B. **vendor 前端 + 自建最小 Server**（当 A 不可行，或需要把 Evidence Gate/Manifest 也显示在 UI）
  - vendor 位置：`.claude/.research/ui/ccg-webui/`
  - server：`src/research_workflow_assistant/ui/server.py`（SSE/WebSocket 推送）
  - adapter：`src/research_workflow_assistant/ui/adapter_ccg.py`（trace → UI event 适配）

**UI 开关与启动方式（最小）**
- 默认关闭：`.claude/.research/ui/ui.config.yaml -> enabled: false`
- 开启后：
  - `/research` 与各域命令在执行时输出 WebUI 地址，并生成/写入 run_id
  - 可选提供显式命令：`/research:ui start|status`（只做启动与状态，不做“控制执行”）

**UI 最小页面信息**（避免过度设计）
- 左侧：Run 列表（run_id、命令、时间、风险等级）
- 中间：事件时间线（Plan / Calls / Evidence / Artifacts）
- 右侧：双面板
  - Codex 输出（JSON/patch + Claude 的人类可读摘要）
  - Gemini 输出（markdown + Evidence Gate 标注：✅/⚠️/❌）

**重要：license 与归属**
- vendor 引入必须保留原项目 LICENSE 与 NOTICE（若存在），并在 `docs/attribution.md` 记录来源与改动。

#### Step 1.7：子智能体（Agents）
新建 8 个 agent 文件：`.claude/agents/research/`

> 说明：Claude 是主控模型，这些 agents 视为 Claude 的“角色提示词实现”。为满足 SSoT，建议在 `.claude/.research/prompts/claude/` 保留同名模板，并用脚本同步到 `.claude/agents/research/`（Claude Code 原生加载路径）。

| Agent | 职责 |
|-------|------|
| `orchestrator.md` | 总控编排、门控、产物落盘、UI 输出摘要 |
| `intent-router.md` | 基于 taxonomy/mapping 识别意图并给出置信度 |
| `planner.md` | 生成可执行计划（偏工程化，驱动 Codex planner/reasoner） |
| `verifier.md` | Evidence Gate：验证主张、标注风险、生成待验证清单 |
| `librarian.md` | 文献筛选、去重、聚类、引用管理 |
| `data-analyst.md` | 数据流程、指标、可视化建议 |
| `simulation-engineer.md` | 仿真脚本/作业/后处理策略 |
| `writer.md` | 论文/专利写作结构一致性（驱动 Gemini writer + Codex reviewer） |

#### Step 1.8：去 CCG 化全局清扫（含协议与命令）
需清理内容：命令文件/协议文件中的 `.ccg`/绝对路径/旧 wrapper 调用。

替换规则（示例）：
```
# 旧（示意）
C:/Users/xxx/.claude/bin/codeagent-wrapper.exe --backend codex ...
ROLE_FILE: C:/Users/xxx/.claude/.ccg/prompts/codex/analyzer.md

# 新（示意）
ROLE_FILE: .claude/.research/prompts/codex/reasoner.md
python -m research_workflow_assistant.bridge.run --request .research/tmp/request.json --out .research/tmp/out.json
```

并补充守卫：
- `scripts/lint_no_ccg_refs.py`：默认扫描全仓库；对 vendor 的 `ccg-webui/` 可做白名单（避免误报）

---

### Phase 2：科研核心闭环（P0/P1）

#### Step 2.1：/research 入口改造（AI 路由，非 CLI）
- 读取 `.claude/.research/*.yaml`
- 获取上下文：项目文件/最近 artifacts/plan/task ledger
- 输出：路由结果（intent + 置信度）+ 推荐命令 + 下一步
- 当 UI 开启：生成 run_id 并写入 trace（便于 WebUI 回放）

#### Step 2.2：文献域命令升级
- `/lit:search`：检索 + 筛选 + 导出（csv/bibtex）
- `/lit:ingest`：PDF/DOI/arXiv → KB 条目
- `/lit:summarize`：Codex（结构化推理）+ Gemini（叙事表达）+ Evidence Gate + 合并
- `/lit:compare`：对比矩阵 + 推荐阅读顺序
- `/lit:cite`：引用网络图 + 分析报告

#### Step 2.3：想法域命令升级
- `/idea:brainstorm`（三角协作 T）：Gemini 发散 → Codex 评审 → Claude 汇总 TOP-N
- `/idea:evaluate`（交叉验证 X）：Codex 可行性/风险矩阵 + Gemini 叙事/受众适配 + 仲裁

#### Step 2.4：写作域命令升级
- `/write:paper`（交叉验证 X）：Codex 构建论证链与结构 → Gemini 写作组织 → Codex reviewer 查错
- `/write:patent-search`：检索策略 + 专利列表
- `/write:patent`（交叉验证 X）：权利要求结构 + 措辞规范化 + 风险检查

#### Step 2.5：Evidence Gate v1（面向 Gemini 幻觉治理）
实现：`src/research_workflow_assistant/workflow/evidence_gate.py`
- extract_claims：从 Gemini 输出中抽取 Claims（含类别与置信）
- verify_claims：基于可用能力（web search / semantic scholar / KB）验证
- annotate_report：在最终报告与 WebUI 中标注 ✅/⚠️/❌

#### Step 2.6：Artifact Manifest v1（可追溯）
实现：`src/research_workflow_assistant/workflow/manifest.py`
- 写入 `artifacts/manifest/<task-id>.json`
- 包含：inputs/outputs/models_used/run_id/trace_ref

---

### Phase 3：数据/仿真深度集成（P1）

#### Step 3.1：数据域命令升级
- `/data:process`：处理脚本 + 数据质量检查 + 可视化
- `/data:train`（high-risk）：训练脚本 + 评估脚本 + 门控
- `/data:calibrate`（high-risk）：敏感性分析 + 参数标定

#### Step 3.2：仿真域命令升级
- `/sim:modify`（medium-risk）：Unified Diff + 自动备份
- `/sim:batch`（high-risk）：作业数量/资源预算/并发限制
- `/sim:debug`（medium-risk）：日志解析 → 诊断 → 建议
- `/sim:odb`（low-risk）：ODB 提取脚本 + 可视化

#### Step 3.3：会话路径迁移
更新 `src/research_workflow_assistant/integration/session.py`：
- 从 `~/.research_workflow/sessions` → `.research/tasks/`
- 添加迁移兼容逻辑

---

### Phase 4：工作流组合与长期任务管理（P2）

#### Step 4.1：/compose 命令
- 定义 `compose.schema.json`（steps、depends_on、cache_key、retry、risk）
- 实现 `workflow/dag_executor.py`

#### Step 4.2：Task Ledger
- `.research/tasks/task-ledger.jsonl`
- `/research:status` 命令

#### Step 4.3：Resume 增强
- 从 `state.json` 恢复
- high-risk 步骤恢复前强制再次确认

---

### Phase 5：测试与文档（P1/P2）

#### Step 5.1：守卫脚本
- `scripts/lint_no_ccg_refs.py`：扫描 `.ccg`/绝对路径（vendor 可白名单）
- `scripts/validate_config.py`：校验 YAML 结构与一致性
- `scripts/sync_agent_prompts.py`（可选）：从 `.claude/.research/prompts/claude/` 同步生成 `.claude/agents/research/`，避免角色提示词漂移
- `scripts/validate_trace.py`（可选）：抽样校验 trace.schema.json

#### Step 5.2：单元测试
- `tests/test_schema_validate.py`
- `tests/test_model_bridge_mock.py`
- `tests/test_evidence_gate.py`
- `tests/test_trace_writer.py`

#### Step 5.3：文档
- `docs/quickstart.md`
- `docs/ui.md`（如何启用 WebUI、如何定位 run_id）
- `docs/attribution.md`（CCG WebUI 复用归属与许可）
- `examples/` 示例工程

---

## 4. 关键文件（更新）

| 文件/目录 | 操作 | 说明 |
|------|------|------|
| `.claude/commands/research/*.md` | 新建/迁移 | 21 个命令文件 |
| `.claude/agents/research/*.md` | 新建 | 8 个 agent 文件（Claude 角色提示词加载入口，可与 prompts/claude 同步） |
| `.claude/.research/_protocol.md` | 重写 | Protocol v2（含 trace/UI 钩子） |
| `.claude/.research/prompts/**/*.md` | 新建 | 16 个角色提示词（Claude 8 + Codex 4 + Gemini 4） |
| `.claude/.research/schemas/*.json` | 新建 | 4 个 schema（新增 trace） |
| `.claude/.research/ui/*` | 新建 | vendor WebUI + UI 配置 |
| `src/research_workflow_assistant/bridge/` | 新建 | Model Bridge（调用/会话/trace） |
| `src/research_workflow_assistant/ui/` | 新建 | UI server + trace adapter |
| `src/research_workflow_assistant/workflow/` | 新建 | Evidence Gate + Manifest |
| `commands/research/*.md` | 删除 | 迁移后删除旧目录 |
| `.research/*.yaml` | 迁移 | 移动到 `.claude/.research/` |

---

## 5. 风险与缓解（更新）

| 风险 | 缓解措施 |
|------|----------|
| 路径迁移导致命令找不到配置 | config loader 多路径回退 + deprecation 警告 |
| 旧 `.research/` 从配置变为 runtime 冲突 | 一次性迁移脚本 + 启动时检测冲突 |
| 仍残留 `.ccg` 引用或绝对路径 | lint_no_ccg_refs + CI/golden set |
| 引入 WebUI 导致“新入口”膨胀 | UI 明确为观测层；交互仍以 Claude Code 命令为准 |
| WebUI/trace 泄露敏感内容 | trace_level=brief 默认；支持脱敏/截断；不写入原始 prompt 全量 |
| trace 文件膨胀 | jsonl 轮转与清理策略（按天/按大小）；仅保存最近 N 次 |
| SESSION_ID 失效导致调用失败 | session_store 自动刷新；失败时自动新建会话并记录 |
| 大量未实现模块导致路由后不可执行 | 短期以命令层工作流交付，中期补齐模块 |

---

## 6. SESSION_ID 管理原则（替代“写死 SESSION_ID”）

- **不硬编码**：不在仓库/文档写死具体 session_id。
- **运行时获取**：首次调用时不带 resume；由工具返回 session_id 后写入 `.research/tasks/sessions.json`。
- **失效自愈**：若 resume 失败，自动丢弃旧 id、创建新会话并更新。
- **可观测**：session 更新事件写入 trace，便于在 WebUI/日志中定位。
