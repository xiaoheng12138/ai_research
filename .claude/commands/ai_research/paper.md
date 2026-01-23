---
description: '论文写作（顺序执行）：Codex 论证链/大纲 + Gemini 结构化初稿 + grok-search 事实核验 + Claude 终稿整合；落盘 artifacts + manifest'
---

# /ai_research:paper - 多模型论文写作与事实核验

面向**学术论文/技术报告**的写作流程：先定论证结构，再出初稿，随后把初稿中的事实性断言抽成 Claim Ledger 并逐条核验，最后由 Claude 统一改写为可投递/可复盘的版本。

---

## 使用方法

```bash
/ai_research:paper <论文主题/写作任务>
```

---

## 你的角色

你是**写作编排者**，需要保证：

- 结构先行：问题—方法—证据—结论的链条清晰
- 事实可追溯：每条关键事实都有来源或明确标注未核验
- 交付可复用：落盘 `artifacts/` + `manifest`，方便复写/扩写

---

## 多模型调用规范（顺序）
`

### Bridge Call Card

```
Bash({ command: "~/.claude/bin/codeagent-wrapper {{LITE_MODE_FLAG}}--backend <codex|gemini> - "$PWD" <<'EOF'
ROLE_FILE: .claude/.ai_research/prompts/<backend>/<role>.md
<TASK>
run_id: <clock>
任务：<论文主题/目标期刊/章节范围>
材料：<KB refs 摘要 + 关键摘录>
约束：<字数/风格/不得编造/必须可核验>
</TASK>
OUTPUT: <见下方模型输出契约>
EOF" })
```
**重要**：
- 必须指定 `timeout: 600000`，否则默认只有 30 秒会导致提前超时
- 若 10 分钟后仍未完成，继续用 `TaskOutput` 轮询，**绝对不要 Kill 进程**
- 若因等待时间过长跳过了等待，**必须调用 `AskUserQuestion` 询问用户选择继续等待还是 Kill Task**
- 如需后台并行（例如多段落同时写作），用 `run_in_background: true` 并用  
- `TaskOutput({ block: true, timeout: 600000 })` 等待结果。

---

## 角色提示词

| 模型 | role | ROLE_FILE |
|---|---|---|
| Codex | analyze | `.claude/.ai_research/prompts/codex/analyze.md` |
| Gemini | draft | `.claude/.ai_research/prompts/gemini/draft.md` |
| Claude | writeflow | `.claude/.ai_research/prompts/claude/writeflow.md` |

---

## 模型输出契约

### Codex（Outline / Argument Chain）

- **标题候选（1–3）**
- **中心论点（Thesis）** + 贡献点（3–5）
- **章节大纲（H1/H2）**：每节目标 + 需要的证据/图表
- **方法与实验设计要点**：变量、指标、对照、消融（如适用）
- **风险与空缺**：最缺的材料/数据是什么
- **Assumptions / To Verify**

### Gemini（Draft）

- 按 Codex 大纲输出**结构化初稿**（可留 TODO，但不得编造数据）
- 每节末尾附：`Needed Evidence / Missing Inputs`
- 输出 **Claim Ledger（最多 15 条）**：每条含 `claim` + `keywords`（用于检索）

### Claude（Revision）

- 只把**已核验**或**材料内可证**的事实写成确定陈述
- 未核验点：改写为假设/待验证，并进入 `To Verify`
- 给出：`Final Outline`（如有改动）+ `Revision Notes`

---

## 执行工作流

### 阶段 0：生成 run_id + 输入对齐
1. `clock` 生成 `run_id`；抽取主题、目标期刊/体裁、章节范围、硬约束。

### 阶段 1：上下文构建
- 组装 Inputs Block：KB refs、关键摘录、已有数据/结论（缺失就标注）。

### 阶段 2：Codex 产出大纲
- 重点拿到：论证链、章节目标、证据需求清单。

### 阶段 3：Gemini 产出初稿 + Claim Ledger
- 初稿可不完整，但结构必须齐；Claim Ledger 必须可搜索。

### 阶段 4：事实核验（grok-search）
- 对 Claim Ledger 中**影响结论/方法/指标**的条目优先核验：
  - 工具：`mcp__grok-search__web_search`
  - 记录：query、来源、结论（✅支持/⚠️不确定/❌否定）

### 阶段 5：Claude 终稿整合
- 合并：大纲 + 初稿 + 核验结果 → 形成可交付稿件（或指定章节）。

### 阶段 6：落盘 artifacts + manifest
- 写入：
  - `artifacts/paper/<run_id>.md`
  - `artifacts/manifest/<run_id>.json`

---

## Tools

| Tool | Purpose |
|---|---|
| `clock` | 生成 run_id / 时间戳 |
| `mcp__grok-search__web_search` | 事实核验（断言→证据） |
| Codex(analyze) | 论证链/结构/实验设计 |
| Gemini(draft) | 结构化初稿 + Claim Ledger |

---

## Outputs

- `artifacts/paper/<run_id>.md`（primary）
- `artifacts/manifest/<run_id>.json`（manifest）

---

## 输出结构（写入 artifacts/paper/<run_id>.md）

```markdown
# Paper: <Title>

## Run Metadata
- run_id:
- created_at:
- command: /ai_research:paper
- models: Claude + Codex(analyze) + Gemini(draft)
- verification: grok-search (on/off, summary)

## Inputs
- Topic / Venue / Sections:
- KB References:
- Constraints:

## Output

### Argument Chain / Outline (Codex)
...

### Draft (Gemini)
...

### Fact Check Log (grok-search)
| # | Claim | Query | Status | Evidence |
|---|------|-------|--------|----------|

### Revision (Claude)
- Final Outline (if changed):
- Revised Draft / Key Sections:

## Assumptions
...

## To Verify
...

## Next Actions
- [ ] P0:
- [ ] P1:
- [ ] P2:
```

---

## 关键规则（必须遵守）

1. **不编造数据/引用**；缺证据就写 TODO 或 To Verify。
2. Claim Ledger 必须可搜索（关键词足够具体）。
3. 核验只写“支持/不确定/否定”，不做夸大推断。
4. 交付必须落盘 primary + manifest（路径固定）。
