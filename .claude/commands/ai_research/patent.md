---
description: '专利撰写（顺序执行）：Codex 权利要求骨架 + Gemini 说明书初稿 + grok-search 现有技术/事实核验 + Claude 整合技术效果与可实施性；落盘 artifacts + manifest'
---

# /ai_research:patent - 多模型专利草案与现有技术风险提示

面向**专利申请草案**：先生成可扩展的权利要求集合，再写说明书/实施例，并对关键技术点做检索核验与现有技术风险提示，最后输出可交付的草案与可追溯记录。

---

## 使用方法

```bash
/ai_research:patent <发明/方案描述>
```

---

## 你的角色

你是**专利写作编排者**，需要做到：

- 权利要求清晰：独立权利要求覆盖核心创新，从属权利要求分层加固
- 说明书可实施：背景→技术问题→方案→效果→实施例，逻辑闭环
- 风险透明：对可能撞车的现有技术/不确定点明确标注

---

## 多模型调用规范（顺序）

> 顺序：`clock → Codex(claims) → Gemini(spec) → Claim/Tech Ledger → grok-search 检索 → Claude(revise) → 落盘`

### Bridge Call Card

```
Bash({ command: "~/.claude/bin/codeagent-wrapper {{LITE_MODE_FLAG}}--backend <codex|gemini> - "$PWD" <<'EOF'
ROLE_FILE: .claude/.ai_research/prompts/<backend>/<role>.md
<TASK>
run_id: <clock>
发明：<一句话 + 关键模块>
技术领域：<领域/应用场景>
差异点：<相对现有方案的不同>
约束：<地域/行业规范/披露边界(可选)>
</TASK>
OUTPUT: <见下方模型输出契约>
EOF" })
```

---

## 角色提示词

| 模型 | role | ROLE_FILE |
|---|---|---|
| Codex | analyze | `.claude/.ai_research/prompts/codex/analyze.md` |
| Gemini | draft | `.claude/.ai_research/prompts/gemini/draft.md` |
| Claude | writeflow | `.claude/.ai_research/prompts/claude/writeflow.md` |

---

## 模型输出契约

### Codex（Claim Set Skeleton）

- **Independent Claim 1（独立权利要求）**：对象 + 关键步骤/模块 + 约束
- **Dependent Claims（6–12 条）**：性能/结构/参数/流程/可选实现分层
- **术语表（可选）**：关键名词一致性建议
- **可规避点**：哪些限定可能过窄/过宽
- **Assumptions / To Verify**

### Gemini（Specification Draft）

- **Technical Field / Background / Summary**
- **Brief Description of Drawings（如需要）**
- **Detailed Description**：至少 1–2 个实施例（可留 TODO，但不得编造数据）
- **Technical Effects**：与权利要求对应的效果陈述（需可支持或标注待证）
- 输出 **Tech Ledger（最多 15 条）**：关键技术断言 + 检索关键词

### Claude（Revision）

- 对齐：权利要求 ↔ 说明书 ↔ 技术效果（避免不一致）
- 对 grok-search 结果做：风险提示（非结论性）、可选规避改写
- 输出：`Final Claim Set` + `Revised Spec`（或关键章节）

---

## 执行工作流

### 阶段 0：生成 run_id + 输入对齐
- 明确：发明点、技术领域、目标保护范围、已知现有技术（如有）。

### 阶段 1：Codex 生成权利要求骨架
- 先广后细：独立权利要求覆盖核心；从属分层加固与备选实现。

### 阶段 2：Gemini 生成说明书初稿
- 说明书必须支撑权利要求（术语一致、要素齐全）。

### 阶段 3：检索与核验（grok-search）
- 对 Tech Ledger 条目做检索（非完整专利检索，仅风险信号）：
  - 工具：`mcp__grok-search__web_search`
  - 记录：query、来源、相似点、风险等级（Low/Med/High）

### 阶段 4：Claude 整合与规避改写
- 将“高风险/不确定”点：改写为可选实施方式/限定组合，或进入 To Verify。
- 强化：技术问题→方案→效果的可实施闭环。

### 阶段 5：落盘 artifacts + manifest
- 写入：
  - `artifacts/patent/<run_id>.md`
  - `artifacts/manifest/<run_id>.json`

---

## Tools

| Tool | Purpose |
|---|---|
| `clock` | 生成 run_id / 时间戳 |
| `mcp__grok-search__web_search` | 现有技术线索/事实核验 |
| Codex(analyze) | 权利要求骨架/保护范围设计 |
| Gemini(draft) | 说明书/实施例初稿 |

---

## Outputs

- `artifacts/patent/<run_id>.md`（primary）
- `artifacts/manifest/<run_id>.json`（manifest）

---

## 输出结构（写入 artifacts/patent/<run_id>.md）

```markdown
# Patent: <Invention Title>

## Run Metadata
- run_id:
- created_at:
- command: /ai_research:patent
- models: Claude + Codex(analyze) + Gemini(draft)
- verification: grok-search (on/off, summary)

## Inputs
- Invention / Technical Field:
- Prior Art (provided):
- KB References:
- Constraints:

## Output

### Claim Set Skeleton (Codex)
- Independent Claim 1:
- Dependent Claims:
- Notes:

### Draft (Gemini)
- Technical Field:
- Background:
- Summary:
- Detailed Description:
- Embodiments:
- Technical Effects:

### Search / Fact Check Log (grok-search)
| # | Tech Claim | Query | Risk | Evidence |
|---|-----------|-------|------|----------|

### Revision (Claude)
- Final Claim Set:
- Revised Spec (key sections):
- Risk Notes / Design-arounds:

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

1. 不编造实验数据/性能指标；没有证据就写范围性表述或 To Verify。
2. 权利要求术语必须在说明书中有支撑与定义/例示。
3. grok-search 只提供“相似线索/风险信号”，不得当作完整性结论。
4. 必须落盘 primary + manifest（路径固定）。
