---
id: plan-20260121-ai-research-refactor-v3
scenario: system.refactor
risk: medium
created_at: 2026-01-21
models:
  - claude
  - codex
  - gemini
inputs:
  - Research_Workflow_Assistant_Architecture_Refactor_Final_Updated.md
outputs:
  - .claude/commands/ai_research/{research,analyze,ideate,code,paper,patent}.md
  - .claude/agents/ai_research/clock.md
  - .claude/.ai_research/config.toml
  - .claude/.ai_research/prompts/{claude,codex,gemini}/*.md (12 prompts total)
  - .claude/.ai_research/contracts/{artifacts.md,kb.md,model_bridge.md,manifest.schema.json}
  - artifacts/{research,analyze,ideate,code,paper,patent,manifest}/ (standardized output paths)
  - .research/kb/{items,raw,files}/ (KB directory layout)
---

# 📋 Plan: AI Research Workflow Refactor (CCG-style, Minimal + Complete)

## 任务类型
- [x] 架构重构（从“编码工作流”→“科研工作流”）
- [x] 协议收敛（输出契约 / KB 契约）
- [x] 多模型协作（Claude 编排 + Codex 原型 + Gemini 写作/创意）
- [ ] WebUI/Trace（P1/P2，可选，不阻塞 MVP）

## 1) 目标与边界

### 1.1 目标（MVP）
1. **命令入口极简**：仅 6 个核心命令（research/analyze/ideate/code/paper/patent）。
2. **三类提示词齐全**：claude / codex / gemini 三类 prompt 均存在；总量控制在 **12 个**。
3. **智能体最小化**：仅保留 `clock`（生成 run_id / 时间戳），其余 agent 暂不实现。
4. **强制“输出契约”**：每个命令必须落盘标准化 artifacts + manifest（可复盘、可复用、可迁移）。
5. **强制“KB 契约”**：KB 条目 metadata 最小集合固定；用户用 MinerU 手动抽取后入库。

### 1.2 明确不做（P0 不做，避免冗余）
- 不做 intent-taxonomy / intent-mapping / scenarios / capabilities 一整套“路由配置系统”
- 不做复杂 Evidence Gate 工作流（用 `mcp__gork` 强制核验替代）
- 不做 8 个子智能体（librarian/bootstrap 等全部暂停）
- 不做 WebUI 作为交互入口（可选观测层后置）

## 2) 目标架构（目录骨架）

> 关键原则：**SSoT（单一事实来源）** + **runtime 隔离** + **artifacts 可追溯**。

```
.claude/
  commands/
    ai_research/
      research.md
      analyze.md
      ideate.md
      code.md
      paper.md
      patent.md
  agents/
    ai_research/
      clock.md

.claude/.ai_research/                 # SSoT（配置 + prompts + 契约）
  config.toml
  prompts/
    claude/
    codex/
    gemini/
  contracts/
    artifacts.md
    kb.md
    model_bridge.md
    manifest.schema.json

.research/                             # runtime（不强制入库）
  kb/
    items/                             # KB 条目（metadata + 人类可读）
    raw/                               # MinerU 抽取原文（markdown/json）
    files/                             # PDF 等大文件（可选）
  cache/
  runs/

artifacts/                             # 产物（建议可入库；大文件可忽略）
  research/
  analyze/
  ideate/
  code/
  paper/
  patent/
  manifest/
```

### 2.1 Model Bridge（Claude → Codex/Gemini，P0 必须显式存在）

> 目的：让“三模型协作”从概念变成**可执行、可复盘**的固定部件。  
> 实现方式保持 CCG 风格：**命令中按固定 Handoff 模板调用子模型**；并用一份契约文档固化调用规范。

**位置（SSoT）**
- `.claude/.ai_research/contracts/model_bridge.md`（只写“调用规范/输入输出形状/并行模式”，不写长背景）
- 所有命令通过该契约约定的 **Bridge Call Card** 调用 Codex/Gemini（“口头假装调用”禁止）

**职责**
1. **Role 解析**：`(backend, role)` → `ROLE_FILE=.claude/.ai_research/prompts/<backend>/<role>.md`
2. **Handoff 请求结构**（固定字段）：`run_id / command / task / context(kb_refs, files) / constraints / output_contract`
3. **并行调用模式**（MVP 固定两种）  
   - `parallel`：Codex 与 Gemini 并行（用于 `analyze`、`ideate`）  
   - `sequential`：先 context7/gork 等 MCP → 再 Codex → 再 review（用于 `code`、`paper`、`patent`）
4. **模型特点（非强制）**：Codex 往往更偏严谨推理/结构化拆解；Gemini 往往更偏世界知识/联想补充。  
   - Bridge **不施加**“深/快/时长”等硬约束  
   - 只要求严格遵守 `output_contract`（结构化输出 + Assumptions + To Verify）
5. **可追踪**：manifest 必须记录所有 Bridge calls（至少 backend+role+mode）

> 注意：P0 只写**契约与命令调用模板**；是否抽成 Python bridge 模块/trace/WebUI，后置到 P1。


## 3) 角色提示词（12 个，三类齐全）

### 3.1 Prompt 清单（总量=12）
> 命名要求：小写、短、可复用；避免“场景化长命名”。  
> 写作要求：**精简、高效、完整**（见第 6 节“字数/结构约束”）。

**Claude（4）**
- `orchestrator`：统一编排、仲裁、落盘、风险门控、MCP 调度
- `research`：research 命令交互与检索编排（gork→semantic_scholar→用户选择→KB 入库指引）
- `codeflow`：code 命令编排（context7→codex→review→合并）
- `writeflow`：paper/patent 编排（结构→初稿→gork 事实审查→整合）

**Codex（4）**
- `analyze`：结构化分析 / 论证链 / 反例与局限
- `ideate`：想法生成（偏可执行实验设计）
- `code`：代码原型（仅原型/patch，不直接落库写入）
- `review`：代码审查（静态审查/测试建议/风险）

**Gemini（4）**
- `ideate`：想法生成（偏发散/创意）
- `draft`：写作初稿（paper/patent）
- `review`：代码审查补充（可读性/潜在 bug/边界条件）
- `analyze`：资料分析（世界知识/联想视角；结构化输出；可提出补充资料与待核对点）

### 3.2 角色协作总规则（高层）
- **Claude 永远是最终输出的唯一作者/裁决者**（整合 + 落盘）。
- **Gemini 的事实性内容默认不可信**：只要 Gemini 输出包含 Facts 段落，Claude 必须调用 `mcp__gork` 校验后再写入最终交付。
- **代码相关不做 gork 事实核验**（包括 Gemini 的代码审查建议）。
- **同名优先（非强制）**：当 Codex 与 Gemini 在同一类任务中承担**相似职责**（常见于 analyze/ideate/review 的并行输出）时，尽量使用相同 role 名称，便于 Bridge 解析与复用；当职责天然不同（如 paper/patent：Codex 结构/论证链，Gemini 初稿写作）时，允许使用不同 role 名称。

## 4) 命令集（6 个，固定入口）

- `/ai_research:research`  调研与文献检索（MCP：gork + semantic_scholar；MinerU 手动入库）
- `/ai_research:analyze`   资料分析（Claude 先做初步分析 → Codex+Gemini 并行分析 → Claude 整合；优先基于 KB）
- `/ai_research:ideate`    想法生成（Codex+Gemini 并行 → Claude 汇总）
- `/ai_research:code`      代码编写（context7→codex 原型→Claude 落地→codex+gemini review）
- `/ai_research:paper`     论文撰写（codex 结构→gemini 初稿→Claude+gork 事实审查）
- `/ai_research:patent`    专利撰写（流程同 paper）

> 注意：本计划仅定义“输出契约与高层流程”，**不在 P0 编写命令/智能体的具体实现细节**。

---

# 5) Output Contracts（每个命令的标准产物格式）

## 5.1 通用约定

### 5.1.1 Run ID（强制）
- `run_id = <YYYYMMDD-HHMMSS>-<short>`  
  - `YYYYMMDD-HHMMSS` 由 `clock` agent 提供  
  - `<short>` 4~8 位短随机串或计数器（避免并发冲突）

### 5.1.2 产物目录（强制）
每次命令执行必须至少生成：
1) **Primary Artifact**（Markdown）：`artifacts/<command>/<run_id>.md`  
2) **Manifest**（JSON）：`artifacts/manifest/<run_id>.json`

> `code` 命令额外强制生成 patch：`artifacts/code/<run_id>.patch`

### 5.1.3 Primary Artifact 通用结构（强制）
所有 `<run_id>.md` 至少包含以下固定标题（顺序固定）：

1. `# Title`
2. `## Run Metadata`（run_id / created_at / command / kb_refs / mcp_used / models_used）
3. `## Inputs`（用户输入摘要 + 引用的 KB 条目）
4. `## Output`（核心结果）
5. `## Assumptions`（假设/前提）
6. `## To Verify`（待核对点；若无则写 `None`）
7. `## Next Actions`（下一步建议，<= 5 条）

> 说明：固定结构可显著提升复用性，避免模型自由发挥导致落盘不可控。

---

## 5.2 Manifest（最小字段）

文件：`artifacts/manifest/<run_id>.json`

```jsonc
{
  "run_id": "20260121-153012-ab12",
  "created_at": "2026-01-21T15:30:12",
  "command": "ai_research:analyze",

  "models_used": [
    {"backend": "claude", "role": "orchestrator"},
    {"backend": "codex", "role": "analyze"},
    {"backend": "gemini", "role": "analyze"}
  ],

  "mcp_used": [
    {"tool": "mcp__gork", "purpose": "fact_check", "invoked": false}
  ],

  "inputs": {
    "user_request": "string (trimmed)",
    "kb_refs": ["kb:paper:xxxx", "kb:report:yyyy"],
    "files": ["relative/path.ext"]
  },

  "artifacts": [
    {"path": "artifacts/analyze/20260121-153012-ab12.md", "type": "primary_md"},
    {"path": "artifacts/manifest/20260121-153012-ab12.json", "type": "manifest"}
  ],

  "verification": {
    "facts_checked": 0,
    "tool": "mcp__gork",
    "status": "n/a",
    "notes": ""
  },

  "next_actions": ["..."]
}
```

> 规则：manifest 字段保持稳定；新增字段只能向后兼容（可选字段）。

---

## 5.3 各命令的标准产物（MVP）

### 5.3.1 `research` 命令
**Primary Artifact**：`artifacts/research/<run_id>.md`  
**Optional Artifact**：`artifacts/research/<run_id>.bib`（用户选择的文献导出）  
**Manifest**：`artifacts/manifest/<run_id>.json`

Primary Artifact 的 `## Output` 必含子段：
- `### Domain Scan (Optional)`：是否使用 gork、得到的关键词簇
- `### Search Queries`：semantic_scholar 查询语句（可复用）
- `### Candidate Papers`：候选列表（最多 20 条，含 paper_id/年份/标题）
- `### User Selection`：用户最终选择的 paper_id 列表
- `### MinerU Ingestion Instructions`：MinerU 抽取与 KB 入库步骤（简短步骤）

> research 不产出“论文总结”，其核心价值是：**可复用检索策略 + 可追踪选择过程 + 可落库路径**。

---

### 5.3.2 `analyze` 命令
**Primary Artifact**：`artifacts/analyze/<run_id>.md`  
**Manifest**：`artifacts/manifest/<run_id>.json`

> 协作顺序（固定）：**Claude 初步分析 → [Codex(analyze) ∥ Gemini(analyze)] 并行分析 → Claude 综合整合**。
>
> 说明：Codex 的“更深/更严谨”和 Gemini 的“更快/联想更强”通常来自模型特点，**不是硬性要求**；命令只要求两者都按同一 `output_contract` 给出结构化分析。

Primary Artifact 的 `## Output` 必含子段（顺序固定）：
- `### Claude Preliminary Analysis`：Claude 对资料/KB 的初步分析与“关键问题清单”（3~7 条）
- `### Analysis (Codex)`：Codex 的结构化分析（强调论证链、推理步骤、反例、局限；**不要求长度/速度**）
- `### Analysis (Gemini)`：Gemini 的结构化分析（强调世界知识/联想补充、可能遗漏点与替代解释；**不要求长度/速度**）
- `### Claude Synthesis`：整合输出，至少包含：
  - `#### Key Findings`：3~7 条要点（最终版本）
  - `#### Claims (fact/inference/speculation)`：表格（最多 12 条）
  - `#### Evidence Links (KB)`：引用 KB 条目（kb_id 列表）
  - `#### Limitations`：局限与反例（至少 2 条）

事实核验规则（强制）：
- 只要 `Analysis (Gemini)` 或 `Claude Synthesis` 中包含新的事实性断言（Facts），manifest 必须记录 `mcp__gork` 是否被调用及核验结论（verified/uncertain/refuted）。

---

### 5.3.3 `ideate` 命令
**Primary Artifact**：`artifacts/ideate/<run_id>.md`  
**Manifest**：`artifacts/manifest/<run_id>.json`

Primary Artifact 的 `## Output` 必含子段：
- `### Problem Restatement`：问题重述（<= 5 行）
- `### Idea Pool (Codex)`：Codex ideas（最多 10 条）
- `### Idea Pool (Gemini)`：Gemini ideas（最多 10 条）
- `### Claude Synthesis (Top-N)`：去重聚类后的 Top 5（每条：价值/可行性/验证实验/风险）
- `### Minimal Experiment Plan`：1~3 个最小实验（可快速验证）

---

### 5.3.4 `code` 命令
**Primary Artifact**：`artifacts/code/<run_id>.md`  
**Required Artifact**：`artifacts/code/<run_id>.patch`（Unified Diff）  
**Manifest**：`artifacts/manifest/<run_id>.json`

Primary Artifact 的 `## Output` 必含子段：
- `### Context7 Best Practices (Summary)`：context7 返回的最佳实践摘要（<= 10 条）
- `### Prototype Strategy (Codex)`：原型方案（模块/接口/测试点）
- `### Implementation Notes (Claude)`：实际落地说明（运行方式/变更文件/风险）
- `### Reviews`：Codex(review) + Gemini(review) 的要点合并（每方最多 8 条）
- `### Final Decisions`：Claude 采纳/拒绝的审查建议（带理由）

Patch 文件要求：
- 只能包含必要改动
- 以统一 diff 格式输出
- 每个文件改动块需有简短注释（在 Primary Artifact 里解释，不在 patch 里长篇）

---

### 5.3.5 `paper` 命令
**Primary Artifact**：`artifacts/paper/<run_id>.md`  
**Manifest**：`artifacts/manifest/<run_id>.json`

Primary Artifact 的 `## Output` 必含子段：
- `### Argument Chain / Outline (Codex)`：结构与论证链（章节级）
- `### Draft (Gemini)`：初稿（可不完整，但要结构齐）
- `### Fact Check (Gork)`：Claude 调 gork 后的核验结果（仅列出被核验的点）
- `### Revision (Claude)`：整合后的稿件片段/改写策略

---

### 5.3.6 `patent` 命令
**Primary Artifact**：`artifacts/patent/<run_id>.md`  
**Manifest**：`artifacts/manifest/<run_id>.json`

结构与 `paper` 同构，但 `## Output` 必含子段：
- `### Claim Set Skeleton (Codex)`：权利要求骨架（独立权利要求 + 从属建议）
- `### Draft (Gemini)`：说明书/实施例初稿
- `### Fact Check (Gork)`：事实核验与现有技术风险提示（简短）
- `### Revision (Claude)`：最终整合（强调技术效果与可实施性）

---

# 6) KB Contract（KB 条目 metadata 最小集合）

## 6.1 KB 目录约定（MVP）
- `.research/kb/items/`：每条知识的“索引卡”（metadata + 人类可读摘要）
- `.research/kb/raw/`：MinerU 原始抽取文本（建议按 kb_id 建目录）
- `.research/kb/files/`：PDF 等（可选；大文件可不入库）

## 6.2 KB 条目文件格式（强制）

路径：`.research/kb/items/<kb_id>.md`

### 6.2.1 YAML Front Matter（最小字段）
```yaml
---
kb_id: "kb:paper:20260121-0001"        # 唯一且稳定（建议带类型前缀）
type: "paper"                          # paper|report|patent|dataset|web|note
title: "..."
authors: ["..."]                       # 允许为空数组，但字段必须存在
year: 2024                              # 不确定可写 null
source:
  provider: "semantic_scholar"          # semantic_scholar|doi|arxiv|url|manual
  id: "..."                              # paperId / DOI / arXivId / url_hash
url: "..."                              # 可为空字符串
tags: ["..."]                           # 可为空数组
added_at: "2026-01-21"                  # YYYY-MM-DD
files:
  pdf: ".research/kb/files/....pdf"     # 可为空字符串
  mineru: ".research/kb/raw/<kb_id>/mineru.md"  # 可为空字符串
---
```

### 6.2.2 Body（推荐最小结构）
```md
## Abstract
(可选)

## Key Contributions
- ...

## Methods / Key Details
- ...

## Results (if any)
- ...

## Notes
- ...

## Quotes (Optional)
> ...
```

> 规则：**metadata 字段必须齐全**（即使为空），以便未来 init/index 不返工。

## 6.3 KB 入库工作流（与 research 命令对齐）
1. `/ai_research:research` 产出候选文献与 paper_id 列表
2. 用户选择文献
3. 用户用 MinerU 抽取 → 输出到 `.research/kb/raw/<kb_id>/mineru.md`
4. 创建 `.research/kb/items/<kb_id>.md`（填 metadata + 写少量 notes）
5. 后续 `/ai_research:analyze|paper|patent` 默认只引用 KB（kb_id），避免直接引用“聊天记录里的事实”

---

# 7) Prompt & Command 编写规范（必须强调：精简、高效、完整）

> 目的：避免提示词/命令文件字数冗余导致模型“读不完/不遵守”。

## 7.1 Prompt 写作硬规则
- 每个 prompt **不超过 120 行**（推荐 60~100 行）
- 只包含三部分：
  1) `Role`（一句话职责）
  2) `Rules`（不超过 12 条）
  3) `Output Format`（固定模板，不超过 1 屏）
- 禁止：长背景介绍、长例子、多套输出格式、重复说明
- 所有 prompt 必须强制输出 `To Verify` 段（没有就写 None）

## 7.2 Command 写作硬规则
- 每个 command 文件 **不超过 180 行**
- 固定结构（顺序固定）：
  1) Purpose
  2) Inputs (ask-up-front questions)
  3) Steps (numbered, <= 8 steps)
  4) Tools (MCP usage points)
  5) Outputs (exact file paths)
- 禁止：多分支长流程（分支应下沉到 prompt/Claude 裁决）

---

# 8) 实施步骤（Strangler：先契约→再命令→再增强）

## Phase 0 (P0): 落地骨架 + 契约文档（必做）
1. 创建目录骨架（.claude/commands、.claude/agents、.claude/.ai_research、.research/kb、artifacts）
2. 写入 `contracts/artifacts.md`（复制本计划第 5 章精简版）
3. 写入 `contracts/kb.md`（复制本计划第 6 章精简版）
4. 写入 `contracts/manifest.schema.json`（仅校验最小字段形状）
5. 更新 `.gitignore`（runtime/cache、可选忽略大 pdf）

## Phase 1 (P0): 12 prompts（先写“短而硬”）
1. 建立 prompts 三目录：claude/codex/gemini
2. 按第 3 节清单创建 12 个 prompt 文件
3. 逐个 prompt 自检：行数、结构、输出模板是否固定

## Phase 2 (P0): 6 commands（只写骨架，不写长逻辑）
1. 创建 6 个命令 markdown（research/analyze/ideate/code/paper/patent）
2. 每个命令只做：
   - 输入问题（最少）
   - 固定步骤（≤ 8）
   - MCP 调用点（何时 gork / semantic_scholar / context7）
   - 输出文件路径（严格按契约）
3. 保持命令文本短：宁可把细节交给 prompts，也不要把命令写成长文

## Phase 3 (P1): MCP 工具点位接入（按命令逐个打通）
- research：gork(可选) → semantic_scholar → 用户选择 → KB 入库指引
- analyze/paper/patent：Gemini facts → gork 强制核验
- code：context7 → codex(code) → codex(review)+gemini(review)

## Phase 4 (P1): 质量门槛与示例
1. 增加 `examples/`：至少 1 个 KB 条目示例 + 1 次 analyze artifact 示例
2. 增加 `README`：只写最短 Quickstart（命令列表 + KB 入库流程 + artifacts 路径）

---

# 9) 验收标准（Definition of Done）

- [ ] 目录结构与本计划一致
- [ ] 12 prompts 全部存在，且满足“短而硬”规则（行数/结构/输出模板）
- [ ] 6 commands 全部存在，且都严格落盘 artifacts + manifest
- [ ] KB 条目可用：至少 1 个示例条目（metadata 完整）
- [ ] `code` 命令必定生成 `.patch` 且包含 review 合并结果
- [ ] Gemini facts 在 analyze/paper/patent 场景下必触发 gork（以日志/manifest 记录为准）

---

# 10) 风险与缓解

| 风险 | 缓解 |
|---|---|
| Prompt/Command 过长导致模型不遵守 | 强制行数限制 + 固定输出模板 |
| KB 元数据不稳定导致后续 init 返工 | metadata 字段“必须齐全”，即使为空 |
| Gemini 幻觉进入最终稿 | Facts 段强制 gork；核验失败则改写为假设/待验证 |
| 输出落盘不一致导致无法复盘 | artifacts 路径与结构强制契约；manifest 记录所有产物 |

