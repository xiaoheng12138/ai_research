---
description: '想法头脑风暴 - 激发创意与探索新方向'
---

# /idea:brainstorm - 头脑风暴

$ARGUMENTS

---

## 依赖能力

- `kb.query` - 知识库检索 (用户配置)
- `lit.search` - 文献检索 (mcp_semantic-scholar)

## 执行流程

### 1. 上下文检索
- 调用 `mcp__ace-tool__search_context` 获取当前研究背景

### 2. 参数校验
检查输入是否包含:
- **主题/问题**: 头脑风暴的核心主题
- **约束条件**: 技术限制、资源限制
- **风暴模式**: 发散、聚焦、组合、逆向

### 3. 计划预览

```markdown
## 📋 执行计划

| 步骤 | 操作 | 风险等级 |
|------|------|----------|
| 1 | 检索相关研究激发灵感 | low |
| 2 | 双模型头脑风暴 (Codex 技术视角 + Gemini 创意视角) | low |
| 3 | 想法筛选与排序 | low |
| 4 | 生成头脑风暴报告 | low |

**预计影响**:
- 生成想法列表: `artifacts/reports/brainstorm-ideas.md`
```

### 4. 确认门控
- **风险等级**: low
- **行为**: auto - 自动执行

### 5. 执行

#### Step 1: 检索相关研究

```javascript
// 检索相关文献激发灵感
papers = mcp_semantic_scholar.search_papers({
  query: "[主题关键词]",
  year: "2020-2025",
  limit: 30
})

// 检索知识库
kb_results = kb.query({
  query: "[主题关键词]",
  limit: 10
})

// 检索跨领域文献
cross_domain_papers = mcp_semantic_scholar.search_papers({
  query: "[跨领域关键词]",
  limit: 20
})
```

#### Step 2: 双模型头脑风暴

**并行调用 Codex + Gemini** (`run_in_background: true`):

##### Codex Brief (技术驱动创意)
```bash
C:/Users/ljh/.claude/bin/codeagent-wrapper.exe --backend codex - "$PWD" <<'EOF'
ROLE_FILE: C:/Users/ljh/.claude/.ccg/prompts/codex/analyzer.md
<TASK>
任务类型: 技术驱动头脑风暴
需求: 从技术角度生成研究想法
上下文:
- 核心主题: [主题描述]
- 约束条件: [技术/资源限制]
- 相关文献: [文献摘要列表]
- 当前研究空白: [识别的研究空白]
生成内容:
1. 技术改进类想法 (5个)
   - 现有方法的优化
   - 性能提升方案
   - 效率改进
2. 技术融合类想法 (5个)
   - 跨领域技术迁移
   - 方法组合创新
3. 问题重构类想法 (3个)
   - 换个角度看问题
   - 问题分解与重组
4. 颠覆性想法 (2个)
   - 挑战现有假设
   - 范式转变
每个想法包含:
- 想法名称
- 核心描述 (50字)
- 技术可行性 (1-10)
- 创新性 (1-10)
- 实现路径简述
</TASK>
OUTPUT: JSON 格式想法列表
{
  "improvement_ideas": [...],
  "fusion_ideas": [...],
  "reframe_ideas": [...],
  "disruptive_ideas": [...]
}
EOF
```

##### Gemini Brief (创意驱动想法)
```bash
C:/Users/ljh/.claude/bin/codeagent-wrapper.exe --backend gemini - "$PWD" <<'EOF'
ROLE_FILE: C:/Users/ljh/.claude/.ccg/prompts/gemini/analyzer.md
<TASK>
任务类型: 创意驱动头脑风暴
需求: 从创意和用户视角生成研究想法
上下文:
- 核心主题: [主题描述]
- 约束条件: [技术/资源限制]
- 目标用户/受益者: [用户群体]
生成内容:
1. 用户需求驱动想法 (5个)
   - 未被满足的需求
   - 痛点解决方案
   - 体验提升
2. 类比迁移想法 (5个)
   - 从其他领域借鉴
   - 自然界启发
   - 生活经验类比
3. "如果..."假设想法 (3个)
   - 大胆假设
   - 突破常规
4. 未来趋势想法 (2个)
   - 技术趋势预判
   - 社会需求预测
每个想法包含:
- 想法名称 (吸引人的)
- 核心描述 (50字)
- 吸引力评分 (1-10)
- 差异化程度 (1-10)
- 故事化描述
</TASK>
OUTPUT: Markdown 格式想法列表
## 用户需求驱动
1. **[想法名称]**: [描述]
...
## 类比迁移
...
## 大胆假设
...
## 未来趋势
...
EOF
```

##### 整合策略
等待两个模型返回后 (`TaskOutput`):
1. **合并** Codex 和 Gemini 的想法列表
2. **去重** 相似想法
3. **交叉评估** Codex 评估 Gemini 想法的可行性，Gemini 评估 Codex 想法的吸引力
4. **排序** 按综合评分排序

#### Step 3: 想法筛选与排序

```python
# 综合评分计算
for idea in all_ideas:
    idea.score = (
        idea.feasibility * 0.3 +      # 可行性
        idea.innovation * 0.3 +        # 创新性
        idea.attractiveness * 0.2 +    # 吸引力
        idea.differentiation * 0.2     # 差异化
    )

# 按评分排序
sorted_ideas = sorted(all_ideas, key=lambda x: x.score, reverse=True)
```

#### Step 4: 生成头脑风暴报告

```markdown
# 头脑风暴报告
**主题**: [核心主题]
**时间**: 2026-01-17
**生成想法**: 30 个 → 筛选后 15 个

---

## 最佳想法 TOP 5

### 1. [想法名称] ⭐ 综合评分: 8.5/10
**类型**: 技术融合 | **来源**: Codex + Gemini 共识

**核心描述**:
[50字描述]

**详细说明**:
[展开说明]

| 维度 | 评分 | 说明 |
|------|------|------|
| 可行性 | 8/10 | [Codex评估] |
| 创新性 | 9/10 | [Codex评估] |
| 吸引力 | 8/10 | [Gemini评估] |
| 差异化 | 9/10 | [Gemini评估] |

**实现路径**:
1. [步骤1]
2. [步骤2]
3. [步骤3]

**后续建议**: `/idea:evaluate "[想法名称]"`

---

### 2. [想法名称] ⭐ 综合评分: 8.2/10
...

---

## 全部想法分类

### 技术改进类 (5个)
| 想法 | 可行性 | 创新性 | 综合 |
|------|--------|--------|------|
| 想法1 | 9 | 6 | 7.2 |
| ... | ... | ... | ... |

### 技术融合类 (5个)
...

### 用户需求驱动 (5个)
...

### 类比迁移 (5个)
...

### 大胆假设 (3个)
...

### 颠覆性想法 (2个)
...

## 想法矩阵

```
可行性
   10 │  ○想法3   ★想法1
      │      ○想法5
    5 │  ○想法7      ○想法2
      │          ○想法4
    0 └───────────────────
      0         5         10  创新性
```
★ = TOP 5, ○ = 其他

## 创意来源

### 参考文献
[激发灵感的关键文献]

### 跨领域借鉴
[跨领域类比来源]

## 后续步骤

### 立即行动
- [ ] 评估 TOP 3 想法: `/idea:evaluate`
- [ ] 文献深入调研: `/lit:search`

### 短期计划
- [ ] 概念验证实验设计
- [ ] 资源需求评估

### 长期规划
- [ ] 研究计划撰写
- [ ] 论文/专利准备
```

### 6. 结果呈现

```markdown
## ✅ 头脑风暴完成

### 生成想法
- **总数**: 30 个
- **筛选后**: 15 个
- **TOP 5**: 见下方

### TOP 5 想法速览
| 排名 | 想法 | 类型 | 综合评分 |
|------|------|------|----------|
| 1 | [想法1] | 技术融合 | 8.5 |
| 2 | [想法2] | 用户需求 | 8.2 |
| 3 | [想法3] | 类比迁移 | 8.0 |
| 4 | [想法4] | 技术改进 | 7.8 |
| 5 | [想法5] | 颠覆性 | 7.5 |

### 生成文件
- 完整报告: `artifacts/reports/brainstorm-ideas.md`
- 想法列表: `artifacts/reports/ideas-list.json`

### 后续操作
- 评估最佳想法: `/idea:evaluate "[TOP1想法]"`
- 继续头脑风暴: `/idea:brainstorm --extend`
- 撰写研究计划: `/write:paper --proposal`
```

---

## 风暴模式

### 发散模式 (默认)
```bash
/idea:brainstorm "主题" --mode divergent
```
尽可能多地生成想法，不做限制

### 聚焦模式
```bash
/idea:brainstorm "主题" --mode focused --constraint "约束条件"
```
在特定约束下生成想法

### 组合模式
```bash
/idea:brainstorm "主题" --mode combination --elements "元素1,元素2,元素3"
```
强制组合不同元素

### 逆向模式
```bash
/idea:brainstorm "主题" --mode reverse
```
逆向思考，从结果倒推

### 类比模式
```bash
/idea:brainstorm "主题" --mode analogy --domain "借鉴领域"
```
从其他领域寻找类比

---

## 高级功能

### 扩展已有想法
```bash
/idea:brainstorm --extend "已有想法描述"
```

### 多主题交叉
```bash
/idea:brainstorm --cross "主题A" "主题B"
```

### 约束创意
```bash
/idea:brainstorm "主题" --must-include "必须包含的元素"
/idea:brainstorm "主题" --must-avoid "必须避免的方向"
```

### 灵感注入
```bash
/idea:brainstorm "主题" --inspire-from "论文ID或专利号"
```

---

## 多模型协作

**协作模式**: 双模型交叉验证

| 模型 | 职责 | 输出 |
|------|------|------|
| **Codex** | 技术驱动想法、可行性评估、实现路径 | JSON 想法列表 |
| **Gemini** | 创意驱动想法、吸引力评估、故事化 | Markdown 想法列表 |
| **Claude** | 整合去重、交叉评估、排序筛选 | 完整头脑风暴报告 |

**交叉评估**:
- Codex 评估 Gemini 想法的技术可行性
- Gemini 评估 Codex 想法的用户吸引力
- 取交集为高质量想法

---

## 错误处理

| 错误类型 | 处理策略 |
|----------|----------|
| 主题过于宽泛 | 引导用户聚焦，提供细化问题 |
| 无相关文献 | 扩大检索范围，尝试跨领域 |
| 想法重复度高 | 强制使用不同思维模式 |
| 模型创意枯竭 | 注入外部灵感源 |

---

## 参考

- 共享协议: `.claude/commands/research/_protocol.md`
- 能力配置: `.claude/.research/capabilities.yaml`
- 想法评估: `/idea:evaluate`
- 文献检索: `/lit:search`
- 论文撰写: `/write:paper`
