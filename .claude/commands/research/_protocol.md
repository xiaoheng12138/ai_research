# Research Skill Protocol

本文件定义 research-workflow-assistant Skills 系统的共享协议,供所有 `/research` 命令复用。

---

## 输入规范

### 标准输入变量
- `$ARGUMENTS`: 用户原始输入文本
- `$CONTEXT`: 上下文信息(上一结果 ID、当前文件路径等)

### 能力依赖声明
每个 Skill 应在文档头部声明依赖的能力:
```markdown
## 依赖能力
- `lit.search` - 论文检索
- `kb.index` - 知识库索引
```

---

## 输出规范

### Plan Card (执行计划预览)
```markdown
## 📋 执行计划

| 步骤 | 操作 | 风险等级 |
|------|------|----------|
| 1 | 检索相关文献 | low |
| 2 | 提取全文 PDF | low |
| 3 | 索引到知识库 | medium |

**预计影响**: 将创建 1-3 个知识库条目
```

### Result Card (执行结果)
```markdown
## ✅ 执行完成

### 结果摘要
- 检索到 5 篇相关论文
- 成功提取 3 篇全文 PDF
- 知识库新增 3 条记录

### 生成文件
- `artifacts/papers/paper-001.pdf`
- `.research/kb/index-2026-01-17.json`
```

### Artifact (生成的文件/数据)
- 文献 PDF: `artifacts/papers/`
- 分析报告: `artifacts/reports/`
- 数据集: `artifacts/data/`
- 配置文件: `.research/`

---

## 确认门控

根据风险等级决定执行行为:

| 风险等级 | 行为 | 说明 |
|----------|------|------|
| `none` | auto | 自动执行,无需确认 |
| `low` | auto | 自动执行,但记录日志 |
| `medium` | confirm | 展示计划,等待用户确认 |
| `high` | confirm + preview | 详细预览 + 显式警告 + 用户确认 |

### 风险等级判定规则
- `none`: 纯读取操作(检索、查询)
- `low`: 创建本地文件、索引知识库
- `medium`: 修改代码、批量操作、调用外部 API
- `high`: 提交 HPC 作业、ML 训练、批量删除

---

## 多模型协作模式

### 模式 A: 单模型主导

**适用场景**: 仿真/数据/ML (Codex)、纯 UX (Gemini)

```
用户输入 → Claude 路由 → Codex/Gemini 执行 → Claude 审核 → 应用
```

**调用示例**:
```bash
C:/Users/ljh/.claude/bin/codeagent-wrapper.exe --backend codex resume <SESSION_ID> - "$PWD" <<'EOF'
ROLE_FILE: C:/Users/ljh/.claude/.ccg/prompts/codex/architect.md
<TASK>
需求: 修改 ABAQUS 脚本的网格划分参数
上下文: [file paths + relevant code]
</TASK>
OUTPUT: Unified Diff Patch ONLY. Strictly prohibit any actual modifications.
EOF
```

### 模式 B: 双模型交叉验证 (新增)

**适用场景**: 文献分析、专利撰写、论文撰写、想法评估

```
用户输入 → Claude 路由 → Codex + Gemini 并行执行 → Claude 整合仲裁 → 交付
```

#### Codex Brief (理性分析)
```bash
ROLE_FILE: C:/Users/ljh/.claude/.ccg/prompts/codex/analyzer.md
<TASK>
任务类型: [文献分析|专利结构|论文论证|想法评估]
需求: ...
上下文: ...
关注点: 逻辑结构、可行性、潜在漏洞、创新点论证
</TASK>
OUTPUT: 结构化分析报告 (JSON 或 Markdown)
```

#### Gemini Brief (创意表达)
```bash
ROLE_FILE: C:/Users/ljh/.claude/.ccg/prompts/gemini/analyzer.md
<TASK>
任务类型: [文献叙事|专利措辞|论文可读性|想法呈现]
需求: ...
上下文: ...
关注点: 表达清晰度、可读性、受众适配、创意联想
</TASK>
OUTPUT: 优化建议或草稿
```

#### 整合规则
1. **一致观点** → 直接采纳
2. **分歧点** → 按领域权威仲裁:
   - 逻辑/结构/可行性 → 以 **Codex** 为准
   - 表达/润色/UX → 以 **Gemini** 为准

---

## Handoff 调用规范

### 基本语法
```bash
C:/Users/ljh/.claude/bin/codeagent-wrapper.exe --backend <codex|gemini> [resume <SESSION_ID>] - "$PWD" <<'EOF'
ROLE_FILE: <角色提示词路径>
<TASK>
需求: <任务描述>
上下文: <相关文件路径 + 代码片段>
</TASK>
OUTPUT: <输出格式要求>
EOF
```

### 必需参数
- `--backend`: `codex` 或 `gemini`
- `resume <SESSION_ID>`: (可选) 复用已有会话
- `ROLE_FILE`: 角色提示词文件路径
- `<TASK>...</TASK>`: 任务描述块
- `OUTPUT`: 输出格式约束

### 后台执行
对于长时间运行任务,使用 `run_in_background: true`:
```javascript
Bash({
  command: "...",
  run_in_background: true,
  timeout: 3600000,  // 60 分钟
  description: "简短描述"
})
```

等待结果:
```javascript
TaskOutput({
  task_id: "<task_id>",
  block: true,
  timeout: 600000  // 10 分钟
})
```

### 进度反馈机制

长时间运行任务应向用户提供进度反馈:

#### 任务启动通知
```markdown
## ⏳ 任务进行中

**任务**: [任务描述]
**模型**: Codex / Gemini / 双模型并行
**预计耗时**: 30-60 秒

正在执行...
```

#### 中间状态更新 (可选)
对于超过 30 秒的任务,可周期性检查状态:
```javascript
// 非阻塞检查
TaskOutput({
  task_id: "<task_id>",
  block: false,
  timeout: 1000
})
```

#### 完成通知
```markdown
## ✅ 任务完成

**耗时**: 45 秒
**结果**: [结果摘要]
```

#### 错误/超时处理
```markdown
## ❌ 任务失败

**错误类型**: timeout / error
**原因**: [错误信息]
**建议**: [恢复建议]
```

#### 超时阈值
| 任务类型 | 默认超时 | 最大超时 |
|----------|----------|----------|
| 文献分析 | 60s | 5min |
| 代码生成 | 120s | 10min |
| ML 训练 | 600s | 60min |
| HPC 提交 | 30s | 2min |

---

## 会话管理

### SESSION_ID 动态管理规则
1. **首次调用**: 省略 `resume` 参数，系统自动创建新会话
2. **后续调用**: 若工具返回 `SESSION_ID`，Claude 应存储并在后续相关任务中使用
3. **禁止硬编码**: 命令文档中不应包含固定的 SESSION_ID
4. **会话失效回退**: 若 resume 失败，自动创建新会话

### 调用示例
```bash
# 首次调用 (新会话)
C:/Users/ljh/.claude/bin/codeagent-wrapper.exe --backend codex - "$PWD" <<'EOF'
...
EOF

# 后续调用 (复用会话 - Claude 动态填入)
C:/Users/ljh/.claude/bin/codeagent-wrapper.exe --backend codex resume <SESSION_ID_FROM_PREVIOUS_CALL> - "$PWD" <<'EOF'
...
EOF
```

### 存储位置
Claude 可在以下位置记录 SESSION_ID 供后续复用:
- 计划文件 (如 `.claude/plan/*.md`)
- 任务上下文 (内存)
- 不推荐写入命令文档

---

## 能力抽象与 MCP 映射

### 能力声明
Skills 通过 **能力标识** 声明依赖,而非硬编码 MCP 名称:
```markdown
## 依赖能力
- `lit.search` - 论文检索
- `docs.query` - 代码文档查询
- `kb.index` - 知识库索引
```

### 运行时解析
Claude 根据 `.claude/.research/capabilities.yaml` 解析能力到 MCP 工具的映射:
```yaml
mappings:
  lit.search:
    mcp_server: semantic-scholar
    tools:
      - mcp__semantic-scholar__papers-search-basic
      - mcp__semantic-scholar__paper-search-advanced
    fallback: mcp__grok-search__web_search
  docs.query:
    mcp_server: context7
    tools:
      - mcp__context7__query-docs
    fallback: mcp__grok-search__web_search
```

### 降级策略
- 若 MCP 工具不可用,使用 `fallback` 工具
- 若无 `fallback`,向用户报告能力缺失并建议安装 MCP

---

## 示例

### 单模型执行示例 (`/sim:modify`)
```markdown
## 依赖能力
- `shell.run` - 本地命令执行
- `docs.query` - ABAQUS Python API 文档

## 执行流程
1. 调用 context7 获取 ABAQUS Python 最佳实践
2. 将文档注入 Codex Brief
3. Codex 生成 Unified Diff Patch
4. Claude 重构并应用变更
```

### 双模型交叉验证示例 (`/lit:summarize`)
```markdown
## 依赖能力
- `lit.pdf_extract` - PDF 全文提取

## 执行流程
1. 并行调用 Codex (逻辑结构分析) + Gemini (叙事组织)
2. 等待双方返回
3. Claude 整合:
   - 采纳 Codex 的论文结构分析
   - 采纳 Gemini 的摘要措辞
4. 输出整合后的论文总结
```

---

## 附录: 角色提示词文件路径

| 模型 | 角色 | 文件路径 |
|------|------|----------|
| Codex | 架构师 | `C:/Users/ljh/.claude/.ccg/prompts/codex/architect.md` |
| Codex | 分析师 | `C:/Users/ljh/.claude/.ccg/prompts/codex/analyzer.md` |
| Codex | 审查员 | `C:/Users/ljh/.claude/.ccg/prompts/codex/reviewer.md` |
| Gemini | 前端专家 | `C:/Users/ljh/.claude/.ccg/prompts/gemini/frontend.md` |
| Gemini | 分析师 | `C:/Users/ljh/.claude/.ccg/prompts/gemini/analyzer.md` |
| Gemini | 审查员 | `C:/Users/ljh/.claude/.ccg/prompts/gemini/reviewer.md` |
