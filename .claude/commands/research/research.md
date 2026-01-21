---
description: '科研辅助工作流统一入口 - 智能路由到具体 Skill'
---

# Research - 科研助手

$ARGUMENTS

---

## 路由逻辑

本命令是 **research-workflow-assistant** Skills 系统的统一入口,通过意图识别自动路由到具体功能。

### 可用命令域

| 域 | 前缀 | 主要用途 | 示例命令 |
|----|------|----------|----------|
| **文献** | `/lit` | 搜索、阅读、对比、总结论文 | `/lit:ingest`, `/lit:search`, `/lit:compare` |
| **仿真** | `/sim` | ABAQUS 脚本、作业提交、调试 | `/sim:modify`, `/sim:batch`, `/sim:debug` |
| **数据** | `/data` | 导入、预处理、时序分析、ML | `/data:process`, `/data:train` |
| **想法** | `/idea` | 头脑风暴、新颖性评估 | `/idea:evaluate`, `/idea:brainstorm` |
| **写作** | `/write` | 论文、专利、报告 | `/write:paper`, `/write:patent` |
| **帮助** | `/research:help` | 系统帮助与引导 | `/research:help` |

### 智能路由流程

1. **上下文检索**
   - 调用 `mcp__ace-tool__search_context` 获取项目相关上下文
   - 提取当前工作文件、知识库状态等信息

2. **意图识别**
   - 基于 12 类 62 子意图分类体系
   - 使用 `.claude/.research/intent-taxonomy.yaml` 和 `.claude/.research/intent-mapping.yaml`
   - 计算置信度分数

3. **场景匹配**
   - 根据意图匹配 17 个预定义场景 (A-O)
   - 参考 `.claude/.research/scenarios.yaml`

4. **命令推荐**
   - 输出建议的具体 Skill 命令
   - 若置信度 < 0.7,进入澄清模式

### 意图分类体系

| 分类 | 子意图示例 | 路由到 |
|------|------------|--------|
| **LITERATURE** | SEARCH, EXTRACT, COMPARE | `/lit:*` |
| **SIMULATION** | MODIFY_SCRIPT, SUBMIT_JOB, DEBUG | `/sim:*` |
| **INVERSE** | TRAIN_MODEL, CALIBRATE, SENSITIVITY | `/data:*` |
| **PATENT** | WRITE, SEARCH, DRAFT_CLAIMS | `/write:patent*` |
| **PAPER** | WRITE_SECTION, COMPOSE | `/write:paper` |
| **IDEA** | EVALUATE, BRAINSTORM | `/idea:*` |

完整分类请参考 `.claude/.research/intent-taxonomy.yaml`。

---

## 执行示例

### 示例 1: 文献检索
```bash
/research 帮我找最近5年关于冰荷载识别的论文
```

**输出**:
```markdown
## 🎯 路由结果

**识别意图**: LITERATURE.SEARCH (置信度: 0.92)
**匹配场景**: A2 - 文献检索对比
**建议命令**: `/lit:search`

### 推荐执行
\`\`\`bash
/lit:search 关键词:"ice load identification" 年份:2020-2025
\`\`\`
```

### 示例 2: 仿真脚本修改
```bash
/research 优化ABAQUS脚本的网格划分参数
```

**输出**:
```markdown
## 🎯 路由结果

**识别意图**: SIMULATION.MODIFY_SCRIPT (置信度: 0.88)
**匹配场景**: F - 仿真脚本修改
**建议命令**: `/sim:modify`

### 推荐执行
\`\`\`bash
/sim:modify --file your_script.py --target mesh
\`\`\`
```

### 示例 3: 低置信度澄清
```bash
/research 分析数据
```

**输出**:
```markdown
## ⚠️ 需要澄清

**识别意图**: DATA.* (置信度: 0.45)

您希望执行以下哪种操作?
1. 数据预处理 (`/data:process`)
2. 仿真-实测对比 (`/data:compare`)
3. 机器学习训练 (`/data:train`)
4. 其他 (请详细描述)
```

---

## 快捷命令清单

| 命令 | 场景 | 风险等级 | 说明 |
|------|------|----------|------|
| `/research:help` | - | none | 显示帮助信息 |
| `/lit:ingest` | A | low | 文献 PDF 导入与分析 |
| `/lit:search` | A2 | medium | 文献检索 |
| `/lit:compare` | A2 | low | 多文献对比分析 |
| `/lit:summarize` | A | low | 文献总结 |
| `/lit:cite` | A2 | low | 引用网络分析 |
| `/idea:evaluate` | B | low | 想法评估完善 |
| `/idea:brainstorm` | C | low | 想法头脑风暴 |
| `/sim:modify` | F | medium | 仿真脚本修改 |
| `/sim:batch` | G | high | 批量仿真提交 |
| `/sim:debug` | H | medium | 仿真调试诊断 |
| `/sim:odb` | I | low | ODB 数据提取 |
| `/data:process` | J | low | 传感器数据处理 |
| `/data:compare` | K | low | 仿真-实测对比 |
| `/data:train` | L | high | ML 载荷识别训练 |
| `/data:calibrate` | M | high | 敏感性与参数标定 |
| `/write:paper` | N | low | 论文章节撰写 |
| `/write:patent` | D | medium | 专利文稿撰写 |
| `/write:patent-search` | D2 | low | 专利检索分析 |

---

## 依赖能力

### 核心能力
- `mcp__ace-tool__search_context` - 上下文检索 (必需)

### 可选能力 (按需解析)
- `lit.*` - 文献相关能力 (mcp__semantic-scholar)
- `docs.*` - 代码文档能力 (context7)
- `kb.*` - 知识库能力 (用户配置)
- `shell.*` - 命令执行能力 (Bash)
- `data.*` - 数据处理能力 (用户配置)

能力到 MCP 工具的映射由 `.claude/.research/capabilities.yaml` 定义。

---

## 配置文件

| 文件 | 用途 |
|------|------|
| `.claude/.research/intent-taxonomy.yaml` | 意图分类体系 (12 类 62 子意图) |
| `.claude/.research/scenarios.yaml` | 场景定义 (17 个场景 A-O) |
| `.claude/.research/intent-mapping.yaml` | 意图到模块的映射 |
| `.claude/.research/capabilities.yaml` | 能力到 MCP 工具的映射 |

---

## 多模型协作

本系统支持 **Claude (编排) + Codex (后端/理性分析) + Gemini (UX/创意表达)** 三模型协作:

| 任务类型 | 协作模式 |
|----------|----------|
| 仿真/数据/ML | Codex 主导 |
| 文献分析、专利撰写、论文撰写、想法评估 | 双模型交叉验证 |
| 纯 UX/报告 | Gemini 主导 |

详细协作协议请参考 `.claude/commands/research/_protocol.md`。

---

## 需要帮助?

- 查看完整命令清单: `/research:help`
- 查看协作协议: 参考 `.claude/commands/research/_protocol.md`
- 配置 MCP 映射: 编辑 `.claude/.research/capabilities.yaml`
