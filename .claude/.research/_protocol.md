# Research Workflow Assistant Protocol v2

本文件定义 Research Workflow Assistant（RWA）的共享协议，供所有 `/research` 相关 commands 与 agents 复用。

- **权威协议**：`.claude/.research/_protocol.md`（本文件）
- **旧版协议**：`.claude/commands/research/_protocol.md`（deprecated）

本协议的设计目标：
1. 统一 **Plan Card / Result Card / Evidence Record / Artifact Manifest** 的结构与字段
2. 统一 **风险门控**：`none/low/medium/high → auto/confirm/confirm+preview`
3. 升级 **协作模式**：S（单模型）/ X（交叉验证）/ T（三角协作）
4. 强制 **可展示推理**：Codex/Gemini 输出必须包含可供 UI 展示的推理结构（非隐藏思维链）
5. 落实 **外部模型不落盘**：仅保留必要结果；trace 可脱敏/截断；禁止保存原始 prompt/response 全量

---

## 0) 目录与术语

### 目录约定（SSoT + runtime + artifacts）
- **配置（SSoT）**：`.claude/.research/`（协议、prompts、schemas、capabilities、taxonomy 等）
- **运行态（runtime，不入库）**：`.research/`（tasks、plans、logs、cache、sessions 等）
- **产物（artifacts）**：`artifacts/`（reports、papers、figures、processed-data、manifest 等）

### 关键术语
- **Claude（主控）**：路由、风险门控、证据门控、产物落盘、最终仲裁与交付
- **子模型（外部模型）**：Codex / Gemini（只做结构化推理与草案产出；不负责落盘与最终裁决）
- **Model Bridge（桥接层）**：统一封装子模型调用、会话管理与 trace 写入

---

## 1) 输入规范

### 标准输入变量
- `$ARGUMENTS`：用户原始输入文本（命令参数/自然语言）
- `$CONTEXT`：上下文信息（最近结果、文件路径、运行态 IDs、用户约束等）

> 建议：在传递给子模型时，将 `$CONTEXT` 归一为结构化对象（files/snippets/constraints/ids），并在 trace 中只保存摘要。

### 能力依赖声明（每个 Skill/Command 必须声明）
```markdown
## 依赖能力
- `lit.search` - 论文检索
- `docs.query` - 文档查询（context7）
- `shell.run` - 本地命令执行
```

能力映射的权威来源：
- `.claude/.research/capabilities.yaml`

---

## 2) 标准输出构件（Cards / Records）

### 2.0 Schema 对齐（权威校验）
- JSON 结构以 `.claude/.research/schemas/` 下对应 schema 为准（plan/evidence/manifest/trace）
- 本协议中的 JSON 示例必须可被 schema 校验通过；字段允许扩展，但不得删除 schema 要求的最小字段

### 2.1 Plan Card（执行计划预览，用于门控）
**用途**：给用户/Claude 提供可确认的执行计划；风险 ≥ medium 必须输出。

**最小字段要求**：
- `task_id` / `plan_id` / `mode`（S/X/T）
- `overall_risk`（none/low/medium/high）与 `gate_action`（auto/confirm/confirm+preview）
- 分步骤 `steps[]`（每步含 risk 与产物预期）
- `expected_artifacts[]`（路径必须是相对路径）

**Markdown 模板（展示层）**：
```markdown
## 📋 Plan Card

**task_id**: task-20260119-xxxx
**mode**: X
**overall_risk**: medium
**gate_action**: confirm

| step | action | risk | expected_outputs |
|------|--------|------|------------------|
| 1 | 收集上下文（文件/片段/约束） | low | `.research/tasks/<task_id>/context.json` |
| 2 | 并行调用 Codex(reasoner) + Gemini(writer) | low | `.research/tasks/<task_id>/model_out/*.json` |
| 3 | Evidence Gate：抽取并验证 Claims | medium | `.research/tasks/<task_id>/evidence.json` |
| 4 | Claude 仲裁并生成最终报告 | low | `artifacts/reports/<task_id>.md` |
| 5 | 写入 Artifact Manifest + trace refs | low | `artifacts/manifest/<task_id>.json` |

**预计影响**:
- 写入 runtime: `.research/`（plans/tasks/logs）
- 写入产物: `artifacts/`（report/manifest）
```

**机器可读块（推荐，供 UI/解析）**：
```json
{
  "type": "plan_card",
  "task_id": "task-20260119-xxxx",
  "plan_id": "plan-20260119-xxxx",
  "mode": "X",
  "overall_risk": "medium",
  "gate_action": "confirm",
  "steps": [
    {
      "step": 1,
      "action": "Collect context",
      "risk": "low",
      "expected_outputs": [".research/tasks/<task_id>/context.json"]
    }
  ],
  "expected_artifacts": [
    {"path": "artifacts/reports/<task_id>.md", "type": "report"}
  ]
}
```

---

### 2.2 Result Card（执行结果，用于交付与追溯）
**用途**：对用户交付的最终结果；必须引用 Evidence 与 Manifest（若产生）。

**最小字段要求**：
- `task_id` / `run_id` / `mode`
- `result_summary[]`（要点）
- `evidence_summary`（verified/unverified/rejected 统计）
- `artifact_manifest`（相对路径）

**Markdown 模板（展示层）**：
```markdown
## ✅ Result Card

**task_id**: task-20260119-xxxx
**run_id**: run-20260119-xxxx
**mode**: X

### 结果摘要
- ...

### 证据摘要（Evidence Gate）
- ✅ verified: 8
- ⚠️ unverified: 2
- ❌ rejected: 1

### 产物与追溯
- Artifact Manifest: `artifacts/manifest/<task_id>.json`
- 关键产物:
  - `artifacts/reports/<task_id>.md`
  - `artifacts/papers/...`
```

**机器可读块（推荐，供 UI/解析）**：
```json
{
  "type": "result_card",
  "task_id": "task-20260119-xxxx",
  "run_id": "run-20260119-xxxx",
  "mode": "X",
  "result_summary": ["要点1", "要点2"],
  "evidence_summary": {"verified": 8, "unverified": 2, "rejected": 1},
  "artifact_manifest": "artifacts/manifest/<task_id>.json",
  "key_artifacts": [
    {"type": "report", "path": "artifacts/reports/<task_id>.md"}
  ]
}
```

---

### 2.3 Evidence Record（证据门控记录，用于幻觉治理）
**用途**：对"主张（Claims）"进行分类与状态管理；尤其用于 Gemini 的事实性陈述治理。

**Claim 分类（type）**：
- `fact`：可被外部证据直接验证的陈述（默认需要验证）
- `inference`：基于证据/逻辑推导出的结论（需说明依据与不确定性）
- `speculation`：假设、猜测、开放问题（必须明确标注为推测）

**Claim 状态（status）**：
- `verified`：已被可追溯证据支持（可在最终交付中当作事实使用）
- `unverified`：未验证/证据不足（不得当作事实表述；需标注 ⚠️）
- `rejected`：被证伪/与证据冲突（不得在交付中使用；需标注 ❌ 并移除或改写）

**Evidence Record（JSON，推荐落盘位置）**：`.research/tasks/<task_id>/evidence.json`
```json
{
  "type": "evidence_record",
  "task_id": "task-20260119-xxxx",
  "run_id": "run-20260119-xxxx",
  "generated_at": "2026-01-19T00:00:00Z",
  "claims": [
    {
      "claim_id": "c1",
      "text": "Claim text...",
      "type": "fact",
      "status": "unverified",
      "confidence": 0.6,
      "evidence": [
        {
          "source_type": "url",
          "ref": "https://example.com/...",
          "quote": "Optional short quote (<= 280 chars)",
          "retrieved_at": "2026-01-19T00:00:00Z"
        }
      ],
      "notes": "Why classified like this; what to verify next."
    }
  ],
  "summary": {"verified": 0, "unverified": 1, "rejected": 0}
}
```

---

### 2.4 Artifact Manifest（产物清单，用于可追溯与审计）
**用途**：把一次任务的 inputs/outputs/models/evidence/trace 关联起来，支持回放与审计。

**推荐落盘位置**：`artifacts/manifest/<task_id>.json`

**最小字段要求**：
- `task_id` / `run_id`
- `inputs[]`（相对路径或 URL；敏感信息仅摘要）
- `outputs[]`（相对路径；含 type 与简述）
- `models_used[]`（backend/role/session_id）
- `evidence_refs[]`（Evidence Record 路径）
- `trace_refs[]`（trace jsonl 路径）

```json
{
  "type": "artifact_manifest",
  "manifest_version": "1.0",
  "task_id": "task-20260119-xxxx",
  "run_id": "run-20260119-xxxx",
  "created_at": "2026-01-19T00:00:00Z",
  "inputs": [
    {"kind": "file", "ref": "src/...", "note": "used as context snippet"},
    {"kind": "url", "ref": "https://...", "note": "evidence source"}
  ],
  "outputs": [
    {"type": "report", "path": "artifacts/reports/<task_id>.md"},
    {"type": "manifest", "path": "artifacts/manifest/<task_id>.json"}
  ],
  "models_used": [
    {"backend": "codex", "role": "reasoner", "session_id": "<runtime>"},
    {"backend": "gemini", "role": "writer", "session_id": "<runtime>"}
  ],
  "evidence_refs": [".research/tasks/<task_id>/evidence.json"],
  "trace_refs": [".research/logs/traces/<run_id>.jsonl"]
}
```

---

## 3) 风险门控规则（Risk Gate）

### 3.1 风险等级 → 门控动作
| risk | gate_action | 说明 |
|------|-------------|------|
| `none` | `auto` | 自动执行；只读/无副作用 |
| `low` | `auto` | 自动执行；允许写入 `artifacts/` 或 `.research/` 但不改代码/不破坏性 |
| `medium` | `confirm` | 必须先展示 Plan Card，等待用户确认 |
| `high` | `confirm+preview` | Plan Card + 变更预览/影响评估 + 显式警告 + 用户确认 |

### 3.2 风险判定（指导规则）
- `none`：纯读取（检索、查询、统计、解析但不写盘）
- `low`：生成新文件（reports/figures/manifest）、追加日志/trace、KB 索引（可回滚）
- `medium`：修改代码/配置、批量处理、调用外部 API/网络获取、会影响实验/仿真可重复性
- `high`：提交 HPC 作业/大规模训练、批量删除/覆盖、不可逆操作、可能产生高成本或数据损失

> 默认策略：**不确定就升档**（none→low→medium→high），并在 Plan Card 中解释原因。

---

## 4) 多模型协作模式（S / X / T）

### 4.1 模式 S：单模型（Single）
定义：仅使用 **Claude**，或仅调用 **一个**子模型（Codex 或 Gemini）。

适用：
- 需求简单或高度确定：Claude-only
- 代码/仿真/数据工程：Codex-only（Claude 负责门控与落盘）
- 创意表达/叙事组织：Gemini-only（Claude 负责 Evidence Gate 与落盘）

基本流程：
```
用户输入 → Claude(路由+门控) → [可选: Model Bridge 调用单一子模型] → Claude(证据/仲裁) → 交付 + Manifest/trace
```

### 4.2 模式 X：交叉验证（Cross-Validation）
定义：Codex + Gemini **并行**；Claude 做仲裁整合。

适用：
- 文献总结/对比、专利/论文写作、想法评估（既要逻辑也要表达）

流程：
```
用户输入 → Claude(路由+门控)
  → (并行) Codex(reasoner/reviewer) + Gemini(writer/ideator)
  → Evidence Gate（抽取/验证 Claims，重点治理 Gemini 的 fact）
  → Claude(仲裁整合) → 交付 + Manifest/trace
```

仲裁原则（默认）：
- 逻辑结构/可行性/审计：优先 Codex；但仍需证据支持
- 表达/可读性/叙事：优先 Gemini；事实性表述必须经 Evidence Gate

### 4.3 模式 T：三角协作（Triangle）
定义：Claude + Codex + Gemini 全量协作（可多轮）；Claude 负责最终裁决。

适用：
- 复杂研究设计、重要写作交付、需要"发散→收敛→审计"的任务

典型流程（示例）：
1) Gemini(ideator) 发散：提出备选方案 + Claims + Evidence Needed
2) Codex(reasoner) 收敛：论证链、风险矩阵、验证计划
3) Codex(reviewer) 审计：找漏洞、补证据、列出拒绝/不确定项
4) Claude 统一：Evidence Gate + 最终交付 + Manifest/trace

---

## 5) "可展示推理"约束（Displayable Reasoning）

### 5.1 原则
- Codex/Gemini 的输出必须包含 **可供 UI 展示** 的推理结构（结构化、可折叠、可引用）
- **禁止**输出"隐藏思维链/私有推理"原文；改为 **可展示的理由摘要**（rationale）与可验证步骤（verification）

### 5.2 子模型输出的最小结构（推荐 JSON）
子模型（经 Model Bridge 返回）的输出应包含：
```json
{
  "output_summary": ["..."],
  "reasoning_display": {
    "problem": "一句话问题定义",
    "approach": [
      {"step": 1, "title": "做什么", "rationale": "为什么", "checks": ["如何验证"]}
    ],
    "assumptions": ["..."],
    "uncertainties": ["..."],
    "risk_notes": ["..."]
  },
  "claims": [
    {"claim_id": "c1", "text": "...", "type": "fact", "status": "unverified"}
  ],
  "payload": {
    "patch": "diff... (若为代码变更任务)",
    "draft": "markdown... (若为写作任务)",
    "tables": []
  }
}
```

> UI 展示要求：`output_summary` 与 `reasoning_display` 必须能在不依赖原始 prompt 的情况下理解；`claims` 供 Evidence Gate 消化。

---

## 6) 外部模型不落盘原则（Retention / Privacy）

### 6.1 必须遵守
- **不保存**外部模型的原始 prompt/response 全量（含流式 token、系统提示词、完整上下文代码）
- **只保留必要结果**：用于交付、复现、审计所必需的最小结构化产出
- trace 允许写盘，但必须支持 **脱敏/截断**（默认 brief）

### 6.2 允许落盘的"必要结果"示例
- Plan Card / Result Card（markdown + 最小 JSON）
- Evidence Record（claims + 证据指针）
- Artifact Manifest（inputs/outputs/models/trace refs）
- 交付产物（报告、图表、导出的引用、必要的 patch 文本）

### 6.3 脱敏/截断规则（建议）
- 对 `input_summary/output_summary`：限制长度（例如 1–2KB），去掉密钥/令牌/个人信息
- 对代码上下文：trace 中只记录文件路径 + 行范围摘要（不记录整段源码）
- 对 URL/引用：保留可追溯引用；若含敏感 query，去 query 或打码

---

## 7) 证据门控（Evidence Gate）

### 7.1 门控硬规则
- `fact` 且用于最终交付的主张：必须为 `verified`，否则必须改写为 `inference/speculation` 或显式标注为 `unverified`
- `rejected`：不得进入最终交付；需在 Result Card 的证据摘要中计数并说明处理（移除/改写）
- 子模型输出的 `claims[].status` 必须默认 `unverified`；仅 Evidence Gate 可以将其更新为 `verified` 或 `rejected`

### 7.2 UI 标注（推荐）
- ✅ `verified`
- ⚠️ `unverified`
- ❌ `rejected`

---

## 8) WebUI Trace 钩子（每次子模型调用必写）

### 8.1 写入要求
- **每次**子模型调用（Codex/Gemini）至少写入 2 条事件：
  - `model_call.started`
  - `model_call.completed` 或 `model_call.failed`
- trace 文件路径（推荐）：`.research/logs/traces/<run_id>.jsonl`

### 8.2 Trace 事件最小字段（必须包含）
- `ts`（ISO 8601 时间戳）
- `run_id` / `task_id`
- `backend`（codex/gemini）
- `role`
- `phase`（例如：`model_call.started`/`model_call.completed`/`model_call.failed`）
- `session_id`（会话标识，用于调试会话连续性）
- `content`（对象：包含 input_summary/output_summary/ok/duration_ms 等，需脱敏/截断）
- `artifacts`（相对路径数组）

### 8.3 TraceEvent（JSONL）示例
```json
{"ts":"2026-01-19T00:00:00Z","run_id":"run-20260119-xxxx","task_id":"task-20260119-xxxx","backend":"codex","role":"reasoner","phase":"model_call.started","session_id":"<runtime>","content":{"input_summary":"..."},"artifacts":[]}
{"ts":"2026-01-19T00:00:10Z","run_id":"run-20260119-xxxx","task_id":"task-20260119-xxxx","backend":"codex","role":"reasoner","phase":"model_call.completed","session_id":"<runtime>","content":{"output_summary":"...","ok":true,"duration_ms":10000},"artifacts":[".research/tasks/<task_id>/model_out/codex.reasoner.json"]}
```

> 若开启 WebUI（SSE/WS），Bridge 可在写文件的同时推送同构事件；协议字段以本节为准。

---

## 9) Model Bridge 调用规范（相对路径；不使用绝对路径）

### 9.1 统一入口（供 Skills 内部调用，非用户入口）
**必须使用**：
```bash
python -m research_workflow_assistant.bridge.run --request <request.json> --out <out.json>
```

约束：
- `--request/--out` 必须是 **相对路径**
- `role_file` 必须在 `.claude/.research/prompts/` 下（相对路径），不得引用任何 legacy prompts 目录或任何绝对路径（workspace 外路径）
- 从项目根目录执行（确保 `src` 在 `PYTHONPATH` 中）

### 9.2 Request JSON（最小建议字段）
```json
{
  "task_id": "task-20260119-xxxx",
  "run_id": "run-20260119-xxxx",
  "backend": "codex",
  "role": "reasoner",
  "role_file": ".claude/.research/prompts/codex/reasoner.md",
  "task": "结构化输出：论证链 + 风险矩阵 + 待验证清单",
  "context": {
    "arguments": "$ARGUMENTS",
    "context": "$CONTEXT",
    "files": ["src/..."],
    "constraints": ["diff-only", "no secrets"]
  },
  "output_format": "json",
  "trace": true,
  "trace_level": "brief",
  "session": {"mode": "auto"}
}
```

**Request/Out 文件保留规则**：
- request.json 默认仅包含引用（files/snippets/ids），避免内嵌整段源码或敏感文本；若必须内嵌，必须脱敏/截断
- request/out 文件默认放在 `.research/tmp/` 或 task 工作目录，并按策略清理（非必要不长期保留）

### 9.3 Out JSON（桥接输出的最小建议字段）
```json
{
  "ok": true,
  "task_id": "task-20260119-xxxx",
  "run_id": "run-20260119-xxxx",
  "backend": "codex",
  "role": "reasoner",
  "session_id": "<runtime>",
  "output": {
    "output_summary": ["..."],
    "reasoning_display": {"problem": "...", "approach": []},
    "claims": [],
    "payload": {}
  },
  "artifact_refs": [".research/tasks/<task_id>/model_out/codex.reasoner.json"]
}
```

> 注意：Out JSON 视为"必要结果"，但必须是**最小结构化输出**；不得包含原始 prompt/response 全量。

---

## 10) SESSION_ID 动态管理规则（不硬编码；运行时获取与持久化）

### 10.1 存储位置与结构（推荐）
存储文件：`.research/tasks/sessions.json`
```json
{
  "codex": {"session_id": "…", "updated_at": "2026-01-19T00:00:00Z"},
  "gemini": {"session_id": "…", "updated_at": "2026-01-19T00:00:00Z"}
}
```

### 10.2 规则
1. **首次调用**：不提供 session_id（`session.mode=auto`）；由 Bridge 创建新会话并返回 `session_id`
2. **后续调用**：Bridge 默认复用 `.research/tasks/sessions.json` 中对应 backend 的 session_id
3. **禁止硬编码**：仓库内协议/命令/示例不得出现固定 session_id 字符串；只能使用占位符或自动模式
4. **失效回退**：若 resume 失败/会话过期，Bridge 必须：
   - 丢弃旧 session_id
   - 创建新会话并更新 sessions.json
   - 写入 trace 事件（例如 `session.refreshed`）
5. **可观测**：每次 session_id 变更都要写入 trace，便于 WebUI 回放与审计

---

## 附录：角色提示词路径（统一约定）

Role prompts 必须位于（相对路径）：
- Codex：`.claude/.research/prompts/codex/<role>.md`
- Gemini：`.claude/.research/prompts/gemini/<role>.md`
- Claude:`.claude/.research/prompts/claude/<role>.md`
推荐角色（可按需要扩展）：
- Codex：`planner` / `reasoner` / `engineer` / `reviewer`
- Gemini：`ideator` / `writer` / `explainer` / `designer`
- claude:`orchestrator`/`intent-router`/`planner`/`verifier`/`librarian`/`data-analyst`/`simulation-engineer`/`writer`