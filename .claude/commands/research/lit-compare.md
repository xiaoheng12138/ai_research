---
description: '多文献对比分析 - 比较多篇论文的方法、结果、贡献'
---

# /lit:compare - 文献对比

$ARGUMENTS

---

## 依赖能力

- `kb.query` - 知识库检索 (用户配置)
- `lit.citation_graph` - 引用网络分析 (mcp_semantic-scholar)

## 执行流程

### 1. 上下文检索
- 调用 `mcp__ace-tool__search_context` 检查知识库中的论文记录

### 2. 参数校验
检查输入是否包含 2-5 篇论文标识:
- arXiv IDs: `arxiv:2301.12345,arxiv:2201.67890`
- DOIs: `10.1016/j.xxx.2023.01.001,10.1016/j.yyy.2022.12.002`
- 知识库 IDs: `kb-20260117-001,kb-20260117-002`

### 3. 计划预览

```markdown
## 📋 执行计划

| 步骤 | 操作 | 风险等级 |
|------|------|----------|
| 1 | 从知识库/API 获取论文详情 | low |
| 2 | 双模型对比分析 (Codex + Gemini) | low |
| 3 | 生成对比报告 | low |
| 4 | 可选: 生成引用网络图 | low |

**预计影响**:
- 生成对比报告: `artifacts/reports/compare-[timestamp].md`
- 可能生成引用网络图: `artifacts/figures/citation-graph.png`
```

### 4. 确认门控
- **风险等级**: low
- **行为**: auto - 自动执行

### 5. 执行

#### Step 1: 获取论文详情
对每篇论文:
1. 优先从知识库查询 (`kb.query`)
2. 若知识库无记录，调用 Semantic Scholar API
3. 提取关键信息: 标题、作者、年份、摘要、方法、结果

#### Step 2: 双模型交叉验证对比

**并行调用 Codex + Gemini** (`run_in_background: true`):

##### Codex Brief (技术对比分析)
```bash
C:/Users/ljh/.claude/bin/codeagent-wrapper.exe --backend codex - "$PWD" <<'EOF'
ROLE_FILE: C:/Users/ljh/.claude/.ccg/prompts/codex/analyzer.md
<TASK>
任务类型: 多文献技术对比
需求: 对比以下论文的技术方案、方法论、实验设计、结果有效性
上下文:
- 论文1: [标题, 摘要, 方法描述]
- 论文2: [标题, 摘要, 方法描述]
- 论文3: [标题, 摘要, 方法描述]
关注点:
- 研究方法的异同
- 实验设计的优劣
- 数据集与评估指标的可比性
- 结论的一致性与矛盾点
- 各自的创新点与局限性
</TASK>
OUTPUT: JSON 格式对比分析
{
  "methods_comparison": {
    "paper1": "方法A",
    "paper2": "方法B",
    "paper3": "方法C",
    "analysis": "对比分析"
  },
  "key_differences": ["差异1", "差异2"],
  "strengths_weaknesses": {
    "paper1": {"strengths": [...], "weaknesses": [...]},
    "paper2": {...},
    "paper3": {...}
  },
  "recommendation": "推荐论文及理由"
}
EOF
```

##### Gemini Brief (可读性对比框架)
```bash
C:/Users/ljh/.claude/bin/codeagent-wrapper.exe --backend gemini - "$PWD" <<'EOF'
ROLE_FILE: C:/Users/ljh/.claude/.ccg/prompts/gemini/analyzer.md
<TASK>
任务类型: 文献对比框架设计
需求: 设计一个清晰的对比框架，便于快速理解差异
上下文:
- 论文1: [标题, 摘要]
- 论文2: [标题, 摘要]
- 论文3: [标题, 摘要]
关注点:
- 设计易读的对比表格
- 提炼关键差异点
- 生成适合引用的总结句
- 建议可视化方案 (如对比图表)
</TASK>
OUTPUT: Markdown 格式对比框架
# 文献对比报告
## 基本信息对比
| 维度 | 论文1 | 论文2 | 论文3 |
|------|-------|-------|-------|
| ... | ... | ... | ... |
## 核心差异
[差异描述]
## 推荐阅读顺序
[阅读建议]
EOF
```

##### 整合策略
等待两个模型返回后 (`TaskOutput`):
1. **采纳 Codex** 的技术对比 (方法、实验、结论)
2. **采纳 Gemini** 的对比框架设计 (表格、可视化建议)
3. 合并为完整的对比报告

#### Step 3: 生成对比报告
输出 Markdown 格式报告，包含:
- 基本信息对比表
- 方法论对比
- 实验结果对比
- 创新点对比
- 优劣势总结
- 推荐阅读顺序

#### Step 4: 可选 - 生成引用网络图
若用户启用 (`--citation-graph`):
1. 调用 `lit.citation_graph` 获取引用关系
2. 生成可视化图表 (使用 Graphviz 或 matplotlib)
3. 保存到 `artifacts/figures/`

### 6. 结果呈现

```markdown
## ✅ 对比分析完成

### 对比论文
1. [论文1标题] (2023, 引用数: 45)
2. [论文2标题] (2022, 引用数: 32)
3. [论文3标题] (2021, 引用数: 28)

### 核心差异 (Codex 分析)
| 维度 | 论文1 | 论文2 | 论文3 |
|------|-------|-------|-------|
| 研究方法 | 机器学习 | 物理模型 | 混合方法 |
| 数据集 | 实测数据 | 仿真数据 | 实测+仿真 |
| 评估指标 | RMSE | MAE | R² |
| 创新点 | 算法A | 模型B | 框架C |

### 推荐阅读顺序 (Gemini 建议)
1. **先读论文3** - 提供了最全面的方法综述
2. **再读论文1** - 最新的机器学习方法
3. **最后读论文2** - 物理模型的理论基础

### 生成文件
- 对比报告: `artifacts/reports/compare-20260117-103045.md`
- 引用网络图: `artifacts/figures/citation-graph.png` (若启用)

### 后续操作
- 导入推荐论文: `/lit:ingest arxiv:2301.12345`
- 查看引用网络: `/lit:cite arxiv:2301.12345,arxiv:2201.67890,arxiv:2112.34567`
```

---

## 对比维度

### 默认对比维度
- 基本信息 (标题、作者、年份、引用数)
- 研究背景与动机
- 研究方法
- 数据集与实验设置
- 主要结果
- 创新点与贡献
- 局限性
- 未来工作

### 自定义对比维度
```bash
/lit:compare --dimensions "method,dataset,results" arxiv:2301.12345,arxiv:2201.67890
```

---

## 高级功能

### 时间序列对比
```bash
# 对比同一主题不同年份的进展
/lit:compare --timeline keywords:"ice load identification" year:2020,2022,2024
```

### 方法论对比
```bash
# 聚焦方法论差异
/lit:compare --focus method arxiv:2301.12345,arxiv:2201.67890,arxiv:2112.34567
```

### 引用网络分析
```bash
# 生成引用关系图
/lit:compare --citation-graph arxiv:2301.12345,arxiv:2201.67890
```

---

## 示例

### 示例 1: 对比 2 篇论文
```bash
/lit:compare arxiv:2301.12345,arxiv:2201.67890
```

### 示例 2: 对比知识库中的论文
```bash
/lit:compare kb-20260117-001,kb-20260117-002,kb-20260117-003
```

### 示例 3: 对比并生成引用网络
```bash
/lit:compare --citation-graph 10.1016/j.xxx.2023.01.001,10.1016/j.yyy.2022.12.002
```

---

## 多模型协作

**协作模式**: 双模型交叉验证

| 模型 | 职责 | 输出 |
|------|------|------|
| **Codex** | 技术对比、方法论评估、结论分析 | JSON 结构化对比 |
| **Gemini** | 对比框架设计、可读性优化、阅读建议 | Markdown 易读报告 |
| **Claude** | 整合仲裁、报告生成、可视化 | 完整对比报告 |

---

## 错误处理

| 错误类型 | 处理策略 |
|----------|----------|
| 论文数量 < 2 | 提示至少需要 2 篇论文 |
| 论文未找到 | 建议先使用 `/lit:search` 检索 |
| 对比维度不适用 | 建议使用默认维度或调整自定义维度 |
| 引用网络数据缺失 | 跳过可视化，仅输出文本对比 |

---

## 参考

- 共享协议: `.claude/commands/research/_protocol.md`
- 能力配置: `.claude/.research/capabilities.yaml`
- 引用网络分析: `/lit:cite`
