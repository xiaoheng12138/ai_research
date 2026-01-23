---
description: '代码实现与评审（顺序+并行）'
---

# /ai_research:code - 多模型代码实现与审查

面向**功能开发 / Bug 修复 / 重构 / 测试补齐**的工程化实现流程：先用 Context7 拉取库/框架最佳实践，再由 Codex 产出可应用的 Unified Diff 原型 patch，随后由 Claude 做“可维护/可上线”的落地完善，最后并行发起 Codex(review) 与 Gemini(review) 做双重审查，输出**可追溯 artifacts + manifest**。

> 本命令以 **patch + 实施说明**交付；**不得伪造运行结果/测试通过**。若未实际执行，请使用“建议/待验证”的表述。

---

## 使用方法

```bash
/ai_research:code <实现需求或改动说明>
```

---

## 你的角色

你是**代码实现协调者**，负责把“需求 → 最佳实践 → 原型 patch → 落地实现 → 审查裁决 → 可追溯产物”串成一个可复盘流程，并确保：

- **可执行**：补齐接口、错误处理、测试建议与运行方式
- **可维护**：最小改动、清晰边界、文档与注释到位
- **可追溯**：产出 patch、实现说明、审查结论与 manifest
- **不夸大**：未运行不声称通过；对风险/未知明确标注

---

## 多模型调用规范（顺序 + 并行）

> 总体顺序：Context7 → Codex(code) → Claude 落地 → [Codex(review) ∥ Gemini(review)] → Claude 裁决 → 落盘 artifacts。

### 统一调用语法（示例）

> 说明：以下为 Bridge Call Card 示例；根据你的仓库与输入材料，填充 `上下文` 与 `约束`。

```
Bash({
  command: "~/.claude/bin/codeagent-wrapper {{LITE_MODE_FLAG}}--backend <codex|gemini> - "$PWD" <<'EOF'
ROLE_FILE: <角色提示词路径>
<TASK>
run_id: <由 clock 生成>
需求：<实现需求/验收标准>
目标文件：<用户指定或自动推断>
上下文：<相关代码片段/目录树/现有接口约定/错误堆栈(如有)>
约束：<兼容性/性能/安全/代码风格/测试/依赖限制>
</TASK>
OUTPUT: 期望输出格式（见下方“模型输出契约”）
EOF",
  run_in_background: true,
  timeout: 3600000,
  description: "简短描述"
})
```

### 并行 review 的等待方式

```
TaskOutput({ task_id: "<task_id>", block: true, timeout: 600000 })
```

**重要**：
- 必须指定 `timeout: 600000`，否则默认只有 30 秒会导致提前超时
- 若 10 分钟后仍未完成，继续用 `TaskOutput` 轮询，**绝对不要 Kill 进程**
- 若因等待时间过长跳过了等待，**必须调用 `AskUserQuestion` 询问用户选择继续等待还是 Kill Task**
---

## 角色提示词

| 模型 | role | ROLE_FILE |
|---|---|---|
| Codex | code | `.claude/.ai_research/prompts/codex/code.md` |
| Codex | review | `.claude/.ai_research/prompts/codex/review.md` |
| Gemini | review | `.claude/.ai_research/prompts/gemini/review.md` |

---

## 模型输出契约

为保证可应用、可审查、可追溯，要求各模型输出遵循以下骨架。

### Codex(code) 输出格式（必须包含 patch）

- **Patch（Unified Diff）**：可直接 `git apply` 的最小改动集（必要时可多文件）
- **变更摘要（3–7条）**：改了什么、为什么这样改
- **接口/行为契约**：输入输出、错误码/异常、边界条件
- **测试建议**：单测/集成测试要点（给出用例列表即可）
- **风险与回滚点**：潜在破坏性变更、需要关注的兼容点
- **Assumptions / To Verify**：假设与待核对项（没有也要写 None）

> Codex(code) 只负责“原型 patch + 关键说明”，不需要长篇文档。

### Codex(review) 输出格式（偏安全/正确性）

- **Finding 列表（最多 12 条）**：每条包含 `Severity(P0/P1/P2)`、定位、原因、修复建议
- **测试缺口**：最可能漏掉的用例
- **回归风险**：哪些现有行为可能被破坏

### Gemini(review) 输出格式（偏可读性/边界/工程体验）

- **可读性与可维护性**：命名、抽象层次、注释/文档、重复逻辑
- **边界条件**：空值、并发、时序、资源释放、错误传播
- **API/UX 体验**：调用方是否易用、错误信息是否可诊断
- **建议的最小改动**：优先给“低风险高收益”调整

---

## 执行工作流

**实现任务**：`$ARGUMENTS`

### 🔍 阶段 0：生成 run_id + 输入规范化与验收标准

1. 调用 `clock` agent 生成 `run_id`（格式：`YYYYMMDD-HHMMSS-<short>`），并在后续所有模型调用与落盘中复用。
2. 从 `$ARGUMENTS` 抽取并明确：
   - 目标行为（What）：要实现/修复什么
   - 验收标准（How to verify）：成功/失败判据
   - 约束（Constraints）：兼容性、性能、安全、依赖、风格
2. 生成 **Implementation Plan（1 屏以内）**：
   - 影响面（文件/模块）
   - 风险点
   - 测试策略（最小集）

---

### 📦 阶段 1：上下文构建 + Context7 最佳实践

1. 收集仓库上下文（最少集即可）：
   - 相关文件片段、现有 API、配置、错误日志（如有）
2. 调用 `mcp__context7__query-docs`：
   - 以“库名/框架名 + 场景关键词”查询（例如：`fastapi background tasks`, `pandas read_csv dtype`）
3. 产出 **Best Practices Block**（供后续 Codex/Claude 共享）。

---

### 🧠 阶段 2：Codex 原型 patch

1. 用 Codex(code) 生成 Unified Diff patch（尽量最小改动）。
2. 要求 Codex 同时输出：
   - 变更摘要
   - 测试建议
   - 风险点与假设

---

### 🛠️ 阶段 3：Claude 落地实现与工程化完善

Claude 基于 Codex patch 与 Best Practices Block：

- 修正不一致/不完整处（导入、类型、边界、错误处理）
- 对齐仓库约定（目录结构、命名、日志、配置）
- 补齐必要的测试/示例（若不写代码，也要写清测试点）
- 生成“运行/验证方式”（命令、环境变量、输入样例）

---

### ⚡ 阶段 4：并行代码审查

并行发起：
1. **Codex(review)**：偏 correctness/security/perf
2. **Gemini(review)**：偏 readability/edge cases/ergonomics

等待两者完整返回（见“并行 review 的等待方式”）。

---

### ✅ 阶段 5：最终裁决与验证指引

1. 合并两份 review，去重聚合为 Findings 列表。
2. Claude 对每条 finding 做裁决：
   - **Accept**：采纳并落实到最终 patch / 实施说明
   - **Reject**：明确理由（不相关/风险更大/超出范围）
   - **Defer**：进入 Next Actions（P1/P2）
3. 输出 **Validation Checklist**（可手动执行）：
   - 构建/静态检查
   - 单测/集成测试
   - 回归点/冒烟测试

---

### 🧾 阶段 6：写入 artifacts + manifest

1. 使用阶段 0 生成的 `run_id` 写入：
   - `artifacts/code/<run_id>.md`
   - `artifacts/code/<run_id>.patch`（Unified Diff，必有）
   - `artifacts/manifest/<run_id>.json`

manifest 至少包含：
- run_id / created_at / command = `ai_research:code`
- inputs（用户需求、目标文件、依赖/库）
- models_used（Codex(code)、Codex(review)、Gemini(review)）
- mcp_used（context7 是否调用、用于什么）
- outputs（md/patch/manifest 路径）
- next_actions（<= 5 条）

---

## 输出结构（写入 artifacts/code/<run_id>.md）

```markdown
# Code: <任务标题>

## Run Metadata
- run_id: <...>
- created_at: <...>
- command: /ai_research:code
- models: Claude + Codex(code) + Codex(review) + Gemini(review)
- mcp: context7=<on/off>

## Inputs
- Task: ...
- Target Files: ...
- Constraints: ...
- Context7 Queries:
  - ...

## Output

### Context7 Best Practices (Summary)
- ...

### Prototype Strategy (Codex)
- ...

### Implementation Notes (Claude)
- Scope:
- Key Changes:
- How to Run / Validate:
- Tests Added / Suggested:

### Reviews
#### Codex(review)
- ...

#### Gemini(review)
- ...

### Final Decisions
| Finding | Decision (Accept/Reject/Defer) | Rationale | Patch Impact |
|---|---|---|---|
| ... | ... | ... | ... |

## Assumptions
- ...

## To Verify
- ...

## Next Actions
- [ ] P0: ...
- [ ] P1: ...
- [ ] P2: ...
```

---

## Patch 文件要求（artifacts/code/<run_id>.patch）

- 必须是 **Unified Diff**（可 `git apply`）
- 只包含必要改动（避免顺手格式化全仓库）
- 若涉及破坏性变更，在 `.md` 中写清迁移/兼容策略
- 不在 patch 内写长篇解释；解释放在 `.md` 的 `Implementation Notes`

---

## 关键规则（必须遵守）

1. **不伪造运行结果**：未实际运行/未实际测到的结果，必须写为“建议/待验证”。
2. **Patch 最小化**：避免无关改动；保持可审查性与可回滚性。
3. **安全优先**：输入校验、错误处理、资源释放、敏感信息不落日志。
4. **记录假设与待核对**：Assumptions / To Verify 不可省略。
5. **必须落盘**：`.md` + `.patch` + `manifest` 三件套齐全，保证可追溯。
