---
description: '系统帮助与引导 - 显示可用命令和使用指南'
---

# /research:help - 帮助与引导

$ARGUMENTS

---

## 依赖能力

- 无需外部依赖 (LLM native)

## 执行流程

### 1. 确认门控
- **风险等级**: none
- **行为**: auto - 自动执行

### 2. 执行
显示科研助手系统的帮助信息。

---

## 帮助内容

### 快速开始

科研助手是一个对话驱动的研究工作流系统，支持文献管理、ABAQUS 仿真、数据分析、ML 建模、论文/专利写作等功能。

**统一入口**: `/research <你的需求>`

系统会自动识别意图并路由到具体功能。

### 命令清单

#### 文献管理 (`/lit:*`)
| 命令 | 功能 | 风险等级 |
|------|------|----------|
| `/lit:ingest <PDF/arXiv/DOI>` | 导入文献并分析 | low |
| `/lit:search <关键词>` | 检索论文 | medium |
| `/lit:compare <论文1>,<论文2>` | 多文献对比 | low |
| `/lit:summarize <论文>` | 生成论文摘要 | low |
| `/lit:cite <论文>` | 引用网络分析 | low |

#### 研究想法 (`/idea:*`)
| 命令 | 功能 | 风险等级 |
|------|------|----------|
| `/idea:evaluate <想法描述>` | 评估可行性与创新性 | low |
| `/idea:brainstorm <主题>` | 头脑风暴生成想法 | low |

#### 仿真分析 (`/sim:*`)
| 命令 | 功能 | 风险等级 |
|------|------|----------|
| `/sim:modify <脚本>` | 修改 ABAQUS 脚本 | medium |
| `/sim:batch <参数范围>` | 批量仿真提交 | high |
| `/sim:debug <作业名>` | 仿真错误诊断 | low |
| `/sim:odb <ODB文件>` | ODB 数据提取 | low |

#### 数据处理 (`/data:*`)
| 命令 | 功能 | 风险等级 |
|------|------|----------|
| `/data:process <数据文件>` | 传感器数据处理 | low |
| `/data:compare <仿真>,<实测>` | 仿真-实测对比 | low |
| `/data:train <数据集>` | ML 模型训练 | high |
| `/data:calibrate <模型>` | 参数标定 | high |

#### 写作辅助 (`/write:*`)
| 命令 | 功能 | 风险等级 |
|------|------|----------|
| `/write:paper <章节>` | 论文章节撰写 | low |
| `/write:patent <技术方案>` | 专利文稿撰写 | medium |
| `/write:patent-search <关键词>` | 专利检索分析 | low |

### 风险等级说明

| 等级 | 行为 | 示例 |
|------|------|------|
| **none** | 自动执行 | 显示帮助 |
| **low** | 自动执行 | 生成报告、读取文件 |
| **medium** | 需确认 | 修改代码、调用外部 API |
| **high** | 需确认 + 预览 | HPC 提交、ML 训练 |

### 多模型协作

系统支持 Claude + Codex + Gemini 三模型协作:

| 任务类型 | 主导模型 |
|----------|----------|
| 仿真/数据/ML | Codex (后端逻辑) |
| 文献/专利/论文 | 双模型交叉验证 |
| 报告/可视化 | Gemini (UX/创意) |

### 配置文件

| 文件 | 用途 |
|------|------|
| `.claude/.research/capabilities.yaml` | 能力到 MCP 的映射 |
| `.claude/.research/scenarios.yaml` | 场景定义 |
| `.claude/.research/intent-taxonomy.yaml` | 意图分类 |
| `.claude/.research/intent-mapping.yaml` | 意图-模块映射 |

### 示例

```bash
# 文献检索
/research 帮我找关于冰荷载识别的最新论文

# 仿真修改
/research 优化 ABAQUS 脚本的网格划分

# 数据分析
/research 对比仿真结果和实测数据

# 想法评估
/research 评估我的研究想法：用机器学习识别覆冰类型
```

### 需要更多帮助?

- 协作协议: `.claude/commands/research/_protocol.md`
- 统一入口: `/research <需求>`
- 具体命令: `/lit:search --help`, `/sim:modify --help` 等

---

## 参考

- 共享协议: `.claude/commands/research/_protocol.md`
- 能力配置: `.claude/.research/capabilities.yaml`
