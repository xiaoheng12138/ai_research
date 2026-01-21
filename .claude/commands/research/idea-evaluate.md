---
description: '想法评估完善 - 评估研究想法的可行性与创新性'
---

# /idea:evaluate - 想法评估

$ARGUMENTS

---

## 依赖能力

- `kb.query` - 知识库检索 (用户配置)
- `lit.search` - 文献检索 (mcp_semantic-scholar)

## 执行流程

### 1. 上下文检索
- 调用 `mcp__ace-tool__search_context` 检查相关研究背景

### 2. 参数校验
检查输入是否包含:
- **想法描述**: 研究想法的核心内容
- **评估维度**: 技术可行性、创新性、应用价值
- **领域背景**: 相关研究领域

### 3. 计划预览

```markdown
## 📋 执行计划

| 步骤 | 操作 | 风险等级 |
|------|------|----------|
| 1 | 检索相关文献与专利 | low |
| 2 | 双模型评估 (Codex 技术可行性 + Gemini 表达清晰度) | low |
| 3 | 生成评估报告 | low |
| 4 | 提供完善建议 | low |

**预计影响**:
- 生成评估报告: `artifacts/reports/idea-evaluation.md`
```

### 4. 确认门控
- **风险等级**: low
- **行为**: auto - 自动执行

### 5. 执行

#### Step 1: 检索相关研究

```javascript
// 检索相关文献
papers = mcp_semantic_scholar.search_papers({
  query: "[想法关键词]",
  year: "2020-2025",
  limit: 30
})

// 检索知识库
kb_results = kb.query({
  query: "[想法关键词]",
  limit: 10
})

// 检索相关专利 (评估创新性)
patents = patent_search({
  query: "[技术关键词]",
  limit: 20
})
```

#### Step 2: 双模型交叉验证

**并行调用 Codex + Gemini** (`run_in_background: true`):

##### Codex Brief (技术可行性评估)
```bash
C:/Users/ljh/.claude/bin/codeagent-wrapper.exe --backend codex - "$PWD" <<'EOF'
ROLE_FILE: C:/Users/ljh/.claude/.ccg/prompts/codex/analyzer.md
<TASK>
任务类型: 研究想法技术可行性评估
需求: 评估想法的技术可行性、创新性、潜在风险
上下文:
- 想法描述: [想法内容]
- 相关文献: [文献摘要列表]
- 相关专利: [专利摘要列表]
- 研究领域: [领域背景]
评估内容:
1. 技术可行性
   - 技术成熟度 (TRL 评级)
   - 所需技术栈
   - 实现难度估计
   - 技术瓶颈识别
2. 创新性评估
   - 与现有研究的区别
   - 新颖性评分 (1-10)
   - 创造性贡献
3. 风险分析
   - 技术风险
   - 资源风险
   - 时间风险
4. 可行路径
   - 分阶段实现方案
   - 关键里程碑
5. 潜在漏洞
   - 逻辑漏洞
   - 假设验证需求
</TASK>
OUTPUT: JSON 格式评估结果
{
  "feasibility": {
    "trl_level": 3,
    "tech_stack": ["技术1", "技术2"],
    "difficulty": "medium",
    "bottlenecks": ["瓶颈1", "瓶颈2"]
  },
  "innovation": {
    "novelty_score": 7,
    "distinguishing_points": ["区别点1", "区别点2"],
    "contribution": "贡献描述"
  },
  "risks": {
    "technical": ["技术风险1"],
    "resource": ["资源风险1"],
    "timeline": ["时间风险1"]
  },
  "roadmap": [
    {"phase": 1, "milestone": "...", "deliverable": "..."},
    ...
  ],
  "weaknesses": ["漏洞1", "漏洞2"]
}
EOF
```

##### Gemini Brief (表达与呈现评估)
```bash
C:/Users/ljh/.claude/bin/codeagent-wrapper.exe --backend gemini - "$PWD" <<'EOF'
ROLE_FILE: C:/Users/ljh/.claude/.ccg/prompts/gemini/analyzer.md
<TASK>
任务类型: 研究想法表达评估
需求: 评估想法的表达清晰度，提供优化建议
上下文:
- 想法描述: [想法内容]
- 目标受众: [学术同行/投资者/普通读者]
评估内容:
1. 表达清晰度
   - 核心价值是否明确
   - 逻辑是否通顺
   - 术语使用是否恰当
2. 故事性
   - 问题-解决方案叙事
   - 吸引力评估
3. 可视化建议
   - 概念图设计
   - 流程图建议
4. 电梯演讲版本
   - 30 秒版本
   - 2 分钟版本
5. 表达优化建议
</TASK>
OUTPUT: Markdown 格式评估与建议
## 清晰度评分
[评分与理由]
## 故事性评估
[评估内容]
## 可视化建议
[建议内容]
## 电梯演讲
### 30秒版本
[精简描述]
### 2分钟版本
[展开描述]
## 优化建议
[具体建议]
EOF
```

##### 整合策略
等待两个模型返回后 (`TaskOutput`):
1. **采纳 Codex** 的技术评估 (可行性、创新性、风险)
2. **采纳 Gemini** 的表达建议 (清晰度、故事性)
3. Claude 整合生成完整评估报告

#### Step 3: 生成评估报告

```markdown
# 研究想法评估报告
**想法**: [想法标题]
**评估时间**: 2026-01-17

---

## 想法概述
[想法描述]

## 综合评分
| 维度 | 评分 | 说明 |
|------|------|------|
| 技术可行性 | 7/10 | TRL-3，技术栈成熟 |
| 创新性 | 8/10 | 具有显著区别特征 |
| 应用价值 | 7/10 | 有明确应用场景 |
| 表达清晰度 | 6/10 | 需要优化核心价值表述 |
| **综合** | **7/10** | 值得进一步探索 |

## 技术可行性分析 (Codex)

### 技术成熟度
- **TRL 等级**: 3 (概念验证阶段)
- **所需技术栈**: Python, TensorFlow, ABAQUS
- **实现难度**: 中等

### 技术瓶颈
1. [瓶颈1描述及解决思路]
2. [瓶颈2描述及解决思路]

### 实现路径
| 阶段 | 里程碑 | 交付物 | 预估周期 |
|------|--------|--------|----------|
| 1 | 概念验证 | Demo | 1个月 |
| 2 | 原型开发 | Prototype | 2个月 |
| 3 | 系统集成 | Alpha版 | 3个月 |

## 创新性评估 (Codex)

### 新颖性评分: 8/10

### 与现有研究对比
| 现有方法 | 本想法 | 优势 |
|----------|--------|------|
| 方法A | 改进点 | 提升X% |
| 方法B | 改进点 | 解决Y问题 |

### 区别技术特征
1. [区别特征1]
2. [区别特征2]

## 风险分析 (Codex)

### 技术风险
| 风险 | 概率 | 影响 | 缓解措施 |
|------|------|------|----------|
| 风险1 | 中 | 高 | 措施1 |
| 风险2 | 低 | 中 | 措施2 |

### 潜在漏洞
1. [漏洞1] - 建议验证方式
2. [漏洞2] - 建议验证方式

## 表达优化建议 (Gemini)

### 当前表达问题
- [问题1]
- [问题2]

### 优化后的电梯演讲

#### 30秒版本
> [精炼描述]

#### 2分钟版本
> [展开描述]

### 可视化建议
建议绘制以下图表：
1. 系统架构图
2. 技术路线图
3. 效果对比图

## 完善建议

### 短期 (1周内)
- [ ] 完善核心价值表述
- [ ] 补充技术细节
- [ ] 制作概念图

### 中期 (1个月)
- [ ] 验证关键假设
- [ ] 开展初步实验
- [ ] 撰写研究计划

### 长期 (3个月)
- [ ] 完成概念验证
- [ ] 撰写论文/专利
- [ ] 申请项目资助

## 相关文献
[自动生成的相关文献列表]

## 相关专利
[检索到的相关专利列表]
```

### 6. 结果呈现

```markdown
## ✅ 想法评估完成

### 综合评分: 7/10 (值得探索)

### 技术可行性 (Codex)
- TRL 等级: 3
- 技术难度: 中等
- 关键瓶颈: 2 项

### 创新性 (Codex)
- 新颖性: 8/10
- 区别特征: 2 项

### 表达清晰度 (Gemini)
- 当前评分: 6/10
- 优化建议: 3 项

### 生成文件
- 评估报告: `artifacts/reports/idea-evaluation.md`
- 相关文献: `artifacts/reports/related-papers.bib`

### 后续操作
- 头脑风暴: `/idea:brainstorm --extend`
- 撰写论文: `/write:paper --based-on idea-evaluation.md`
- 撰写专利: `/write:patent --based-on idea-evaluation.md`
```

---

## 评估维度

### 全面评估
```bash
/idea:evaluate "想法描述" --full
```

### 单维度评估
```bash
/idea:evaluate "想法描述" --focus feasibility
/idea:evaluate "想法描述" --focus innovation
/idea:evaluate "想法描述" --focus value
/idea:evaluate "想法描述" --focus expression
```

### 对比评估
```bash
/idea:evaluate --compare "想法A" "想法B"
```

---

## 多模型协作

**协作模式**: 双模型交叉验证

| 模型 | 职责 | 输出 |
|------|------|------|
| **Codex** | 技术可行性、创新性、风险分析、路径规划 | JSON 结构化评估 |
| **Gemini** | 表达清晰度、故事性、可视化、电梯演讲 | Markdown 建议 |
| **Claude** | 整合仲裁、文献检索、报告生成 | 完整评估报告 |

---

## 错误处理

| 错误类型 | 处理策略 |
|----------|----------|
| 想法描述不清晰 | 进入澄清模式，引导用户补充细节 |
| 无相关文献 | 扩大检索范围，标记为新兴领域 |
| 评估维度缺失 | 使用默认评估框架 |
| 模型意见分歧 | 按领域权威仲裁并标注分歧点 |

---

## 参考

- 共享协议: `.claude/commands/research/_protocol.md`
- 能力配置: `.claude/.research/capabilities.yaml`
- 头脑风暴: `/idea:brainstorm`
- 论文撰写: `/write:paper`
- 专利撰写: `/write:patent`
