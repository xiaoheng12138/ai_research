# De-CCG 清理报告

## 扫描结果摘要

| 类别 | 文件数 | 需清理项数 |
|------|--------|------------|
| 命令文件 | 17 | 68 |
| 协议文件 | 1 | 14 |
| 设置文件 | 2 | 6 |
| 计划文件 | 2 | 18 (参考/示例，可保留) |
| 文档文件 | 2 | 2 (参考/示例，可保留) |
| **总计** | **24** | **108** |

## 详细清理清单

### 高优先级 - 命令文件 (`.claude/commands/research/*.md`)

需要替换的模式：

| 原始模式 | 替换为 |
|----------|--------|
| `C:/Users/ljh/.claude/bin/codeagent-wrapper.exe` | `codeagent-wrapper` |
| `C:/Users/ljh/.claude/.ccg/prompts/codex/` | `.claude/.research/prompts/codex/` |
| `C:/Users/ljh/.claude/.ccg/prompts/gemini/` | `.claude/.research/prompts/gemini/` |

**受影响文件**：
- data-calibrate.md (4 处)
- data-compare.md (4 处)
- data-process.md (2 处)
- data-train.md (2 处)
- idea-brainstorm.md (4 处)
- idea-evaluate.md (4 处)
- lit-cite.md (4 处)
- lit-compare.md (4 处)
- lit-ingest.md (4 处)
- lit-summarize.md (4 处)
- sim-batch.md (2 处)
- sim-debug.md (2 处)
- sim-modify.md (2 处)
- sim-odb.md (4 处)
- write-paper.md (4 处)
- write-patent.md (4 处)
- write-patent-search.md (4 处)
- _protocol.md (14 处)

### 中优先级 - 设置文件

| 文件 | 清理建议 |
|------|----------|
| `.claude/settings.local.json` | 移除或通配符化绝对路径 |
| `settings.local.json` | 移除或通配符化绝对路径 |

### 低优先级 - 文档/计划文件 (可保留作为历史参考)

| 文件 | 说明 |
|------|------|
| `docs/ui-compat.md:176` | CCG 参考路径，文档用途，可保留 |
| `output.md:399` | 历史输出，可保留 |
| `.claude/plan/architecture-refactor.md` | 计划文档，包含示例，可保留 |
| `.claude/plan/Research_Workflow_Assistant_Architecture_Refactor_Final_Updated.md` | 主计划文档，可保留 |

## 推荐清理策略

### Phase 1: Strangler 迁移 (当前阶段完成)
1. ✅ 创建新的 Protocol v2 (`.claude/.research/_protocol.md`)
2. ✅ 创建新的 prompts 目录 (`.claude/.research/prompts/`)
3. ✅ 创建 Model Bridge 模块
4. 🔄 保留旧命令文件，逐步迁移

### Phase 2: 命令文件迁移
1. 为每个命令创建新版本，使用相对路径
2. 旧命令标记为 deprecated
3. 测试验证后删除旧命令

### Phase 3: 完全清理
1. 删除所有旧命令文件
2. 更新设置文件
3. 运行 lint 脚本验证

## Lint 脚本位置

`scripts/lint_no_ccg_refs.py` - 用于 CI 验证

## 注意事项

1. **不要直接删除旧文件**：采用 Strangler 模式，保持向后兼容
2. **设置文件特殊处理**：权限规则中的路径可能需要保留
3. **计划/文档文件**：作为历史参考保留，不影响运行时
