---
id: plan-20260122-ai-research-workflow-refactor
scenario: system.refactor
risk: medium
created_at: 2026-01-22
models:
  - claude
  - codex
  - gemini
source: AI_Research_Refactor_Plan_v3.md
---

# 📋 实施计划：AI Research Workflow 架构重构

## 任务类型
- [x] 后端 (→ Codex)
- [x] 前端 (→ Gemini)
- [√] 全栈 (→ 并行)

> **说明**：本任务涉及架构重构、契约定义、多模型协作配置，需要 Codex（结构化设计）与 Gemini（写作流程设计）协作。

---

## 技术方案

### 核心目标（MVP）
1. **命令入口极简**：仅 6 个核心命令（research/analyze/ideate/code/paper/patent）
2. **三类提示词齐全**：claude / codex / gemini 三类 prompt 均存在；总量控制在 **12 个**
3. **智能体最小化**：仅保留 `clock`（生成 run_id / 时间戳），其余 agent 暂不实现
4. **强制"输出契约"**：每个命令必须落盘标准化 artifacts + manifest
5. **强制"KB 契约"**：KB 条目 metadata 最小集合固定

### 明确不做（P0 排除）
- ❌ intent-taxonomy / intent-mapping / scenarios / capabilities 路由配置系统
- ❌ 复杂 Evidence Gate 工作流（用 `mcp__gork` 强制核验替代）
- ❌ 8 个子智能体（librarian/bootstrap 等全部暂停）
- ❌ WebUI 作为交互入口（可选观测层后置到 P1/P2）

---

## 实施步骤

### Phase 0：落地骨架 + 契约文档（必做）

| 步骤 | 操作 | 预期产物 |
|------|------|----------|
| 0.1 | 创建目录骨架 | `.claude/commands/ai_research/`、`.claude/agents/ai_research/`、`.claude/.ai_research/`、`.research/kb/`、`artifacts/` |
| 0.2 | 写入 `contracts/artifacts.md` | 输出契约文档（第 5 章精简版） |
| 0.3 | 写入 `contracts/kb.md` | KB 契约文档（第 6 章精简版） |
| 0.4 | 写入 `contracts/model_bridge.md` | 模型桥接规范（调用规范/输入输出形状/并行模式） |
| 0.5 | 写入 `contracts/manifest.schema.json` | Manifest JSON Schema（仅校验最小字段形状） |
| 0.6 | 写入 `config.toml` | 基础配置文件 |
| 0.7 | 更新 `.gitignore` | 忽略 runtime/cache、可选忽略大 pdf |

### Phase 1：12 Prompts（先写"短而硬"）

**Claude Prompts（4 个）**

| 文件 | 职责 |
|------|------|
| `.claude/.ai_research/prompts/claude/orchestrator.md` | 统一编排、仲裁、落盘、风险门控、MCP 调度 |
| `.claude/.ai_research/prompts/claude/research.md` | research 命令交互与检索编排 |
| `.claude/.ai_research/prompts/claude/codeflow.md` | code 命令编排（context7→codex→review→合并） |
| `.claude/.ai_research/prompts/claude/writeflow.md` | paper/patent 编排（结构→初稿→gork 事实审查→整合） |

**Codex Prompts（4 个）**

| 文件 | 职责 |
|------|------|
| `.claude/.ai_research/prompts/codex/analyze.md` | 结构化分析 / 论证链 / 反例与局限 |
| `.claude/.ai_research/prompts/codex/ideate.md` | 想法生成（偏可执行实验设计） |
| `.claude/.ai_research/prompts/codex/code.md` | 代码原型（仅原型/patch，不直接落库写入） |
| `.claude/.ai_research/prompts/codex/review.md` | 代码审查（静态审查/测试建议/风险） |

**Gemini Prompts（4 个）**

| 文件 | 职责 |
|------|------|
| `.claude/.ai_research/prompts/gemini/analyze.md` | 资料分析（世界知识/联想视角） |
| `.claude/.ai_research/prompts/gemini/ideate.md` | 想法生成（偏发散/创意） |
| `.claude/.ai_research/prompts/gemini/draft.md` | 写作初稿（paper/patent） |
| `.claude/.ai_research/prompts/gemini/review.md` | 代码审查补充（可读性/潜在 bug/边界条件） |

**Prompt 写作规则**
- 每个 prompt **不超过 120 行**（推荐 60~100 行）
- 固定三部分结构：`Role`（一句话职责）+ `Rules`（≤12 条）+ `Output Format`（固定模板）
- 所有 prompt 必须强制输出 `To Verify` 段

### Phase 2：6 Commands（只写骨架）

| 文件 | 用途 | MCP 工具 |
|------|------|----------|
| `.claude/commands/ai_research/research.md` | 调研与文献检索 | gork + semantic_scholar |
| `.claude/commands/ai_research/analyze.md` | 资料分析 | gork (事实核验) |
| `.claude/commands/ai_research/ideate.md` | 想法生成 | - |
| `.claude/commands/ai_research/code.md` | 代码编写 | context7 |
| `.claude/commands/ai_research/paper.md` | 论文撰写 | gork (事实核验) |
| `.claude/commands/ai_research/patent.md` | 专利撰写 | gork (事实核验) |

**Command 写作规则**
- 每个 command **不超过 180 行**
- 固定结构：`Purpose` → `Inputs` → `Steps`（≤8）→ `Tools` → `Outputs`

### Phase 3：Agent + 目录布局

| 步骤 | 操作 | 预期产物 |
|------|------|----------|
| 3.1 | 创建 clock agent | `.claude/agents/ai_research/clock.md` |
| 3.2 | 创建 KB 目录结构 | `.research/kb/{items,raw,files}/` |
| 3.3 | 创建 artifacts 目录结构 | `artifacts/{research,analyze,ideate,code,paper,patent,manifest}/` |
| 3.4 | 创建 KB 示例条目 | `.research/kb/items/example.md` |

---

## 关键文件

| 文件/目录 | 操作 | 说明 |
|-----------|------|------|
| `.claude/commands/ai_research/*.md` | 新建 | 6 个命令入口 |
| `.claude/agents/ai_research/clock.md` | 新建 | 唯一 agent（run_id 生成） |
| `.claude/.ai_research/config.toml` | 新建 | SSoT 配置 |
| `.claude/.ai_research/prompts/claude/*.md` | 新建 | 4 个 Claude prompts |
| `.claude/.ai_research/prompts/codex/*.md` | 新建 | 4 个 Codex prompts |
| `.claude/.ai_research/prompts/gemini/*.md` | 新建 | 4 个 Gemini prompts |
| `.claude/.ai_research/contracts/*.md` | 新建 | 契约文档（artifacts/kb/model_bridge） |
| `.claude/.ai_research/contracts/manifest.schema.json` | 新建 | Manifest JSON Schema |
| `.research/kb/{items,raw,files}/` | 新建 | KB 目录布局 |
| `artifacts/{command}/` | 新建 | 产物目录（6 个命令 + manifest） |
| `.gitignore` | 修改 | 添加 runtime/cache 忽略规则 |

---

## 输出契约摘要

### Run ID 格式
```
run_id = <YYYYMMDD-HHMMSS>-<short>
```
- `YYYYMMDD-HHMMSS` 由 `clock` agent 提供
- `<short>` 4~8 位短随机串

### 产物目录规则
每次命令执行必须生成：
1. **Primary Artifact**：`artifacts/<command>/<run_id>.md`
2. **Manifest**：`artifacts/manifest/<run_id>.json`
3. （code 命令额外）**Patch**：`artifacts/code/<run_id>.patch`

### Primary Artifact 通用结构
```markdown
# Title
## Run Metadata
## Inputs
## Output
## Assumptions
## To Verify
## Next Actions
```

### Manifest 最小字段
```json
{
  "run_id": "...",
  "created_at": "...",
  "command": "...",
  "models_used": [...],
  "mcp_used": [...],
  "inputs": {...},
  "artifacts": [...],
  "verification": {...},
  "next_actions": [...]
}
```

---

## 模型协作规则

| 规则 | 说明 |
|------|------|
| Claude 主权 | Claude 永远是最终输出的唯一作者/裁决者（整合 + 落盘） |
| Gemini 事实核验 | Gemini 输出的 Facts 必须调用 `mcp__gork` 校验后再写入 |
| 代码豁免 | 代码相关内容不做 gork 事实核验 |
| 并行模式 | `analyze`/`ideate` 使用 Codex+Gemini 并行 |
| 顺序模式 | `code`/`paper`/`patent` 使用 MCP→Codex→review 顺序 |

---

## 风险与缓解

| 风险 | 缓解措施 |
|------|----------|
| Prompt/Command 过长导致模型不遵守 | 强制行数限制（Prompt≤120行，Command≤180行）+ 固定输出模板 |
| KB 元数据不稳定导致后续 init 返工 | metadata 字段"必须齐全"，即使为空 |
| Gemini 幻觉进入最终稿 | Facts 段强制 gork 核验；核验失败则改写为假设/待验证 |
| 输出落盘不一致导致无法复盘 | artifacts 路径与结构强制契约；manifest 记录所有产物 |

---

## 验收标准（Definition of Done）

- [ ] 目录结构与计划一致
- [ ] 12 prompts 全部存在，且满足"短而硬"规则
- [ ] 6 commands 全部存在，且都严格落盘 artifacts + manifest
- [ ] KB 条目可用：至少 1 个示例条目（metadata 完整）
- [ ] `code` 命令必定生成 `.patch` 且包含 review 合并结果
- [ ] Gemini facts 在 analyze/paper/patent 场景下必触发 gork

---

## SESSION_ID（供 /ccg:execute 使用）

- CODEX_SESSION: `<待执行时生成>`
- GEMINI_SESSION: `<待执行时生成>`

---

## 参考文档

- 源计划：`.claude/plan/AI_Research_Refactor_Plan_v3.md`
- 详细输出契约：见源计划第 5 章
- 详细 KB 契约：见源计划第 6 章
