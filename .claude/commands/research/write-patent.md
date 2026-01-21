---
description: '专利文稿撰写 - 协助撰写专利申请文稿'
---

# /write:patent - 专利撰写

$ARGUMENTS

---

## 依赖能力

- `kb.query` - 知识库检索 (用户配置)
- `lit.search` - 现有技术检索 (mcp_semantic-scholar / 专利数据库)

## 执行流程

### 1. 上下文检索
- 调用 `mcp__ace-tool__search_context` 检查技术方案相关文档

### 2. 参数校验
检查输入是否包含:
- **技术方案**: 发明内容描述
- **专利类型**: 发明专利 / 实用新型
- **撰写部分**: 权利要求 / 说明书 / 摘要 / 附图说明
- **技术领域**: 领域分类

### 3. 计划预览

```markdown
## 📋 执行计划

| 步骤 | 操作 | 风险等级 |
|------|------|----------|
| 1 | 技术方案分析 + 现有技术检索 | low |
| 2 | 双模型分析 (Codex 权利要求逻辑 + Gemini 措辞润色) | medium |
| 3 | 生成专利文稿 | medium |
| 4 | 格式检查 | low |

**预计影响**:
- 生成专利文稿: `artifacts/writing/patent-draft.md`
- 生成权利要求书: `artifacts/writing/claims.md`

**警告**: 专利文稿仅供参考，请专业代理人审核
```

### 4. 确认门控
- **风险等级**: medium (专利文稿需专业审核)
- **行为**: confirm - 展示计划，等待用户确认

### 5. 执行

#### Step 1: 技术方案分析与现有技术检索

```javascript
// 检索现有技术 (专利数据库)
patent_search({
  query: "[技术方案关键词]",
  type: "invention",
  date_range: "近10年"
})

// 检索相关论文
mcp_semantic_scholar.search_papers({
  query: "[技术方案关键词]",
  limit: 20
})
```

#### Step 2: 双模型交叉验证

**并行调用 Codex + Gemini** (`run_in_background: true`):

##### Codex Brief (权利要求逻辑构建)
```bash
C:/Users/ljh/.claude/bin/codeagent-wrapper.exe --backend codex - "$PWD" <<'EOF'
ROLE_FILE: C:/Users/ljh/.claude/.ccg/prompts/codex/analyzer.md
<TASK>
任务类型: 专利权利要求逻辑构建
需求: 为技术方案构建严谨的权利要求层次结构
上下文:
- 技术方案: [技术描述]
- 专利类型: [发明专利/实用新型]
- 现有技术: [检索到的相关专利/论文摘要]
- 技术领域: [领域分类]
分析内容:
1. 核心创新点提取 (区别于现有技术)
2. 技术特征分解 (必要技术特征 vs 附加技术特征)
3. 权利要求层次设计:
   - 独立权利要求 (最大保护范围)
   - 从属权利要求 (逐步限缩)
4. 技术效果论证链
5. 规避设计风险点
6. 建议的权利要求数量和结构
</TASK>
OUTPUT: JSON 格式权利要求结构
{
  "innovation_points": ["创新点1", "创新点2"],
  "technical_features": {
    "essential": ["必要特征1", "必要特征2"],
    "additional": ["附加特征1", "附加特征2"]
  },
  "claims_structure": {
    "independent_claim": {
      "preamble": "一种...",
      "characterizing_portion": "其特征在于...",
      "features": ["特征1", "特征2"]
    },
    "dependent_claims": [
      {"base": 1, "additional_feature": "..."},
      ...
    ]
  },
  "technical_effects": ["效果1", "效果2"],
  "risks": ["风险点1", "风险点2"]
}
EOF
```

##### Gemini Brief (措辞润色)
```bash
C:/Users/ljh/.claude/bin/codeagent-wrapper.exe --backend gemini - "$PWD" <<'EOF'
ROLE_FILE: C:/Users/ljh/.claude/.ccg/prompts/gemini/analyzer.md
<TASK>
任务类型: 专利措辞润色
需求: 优化专利文稿的表达清晰度和规范性
上下文:
- 技术方案: [技术描述]
- 专利类型: [发明专利/实用新型]
- 语言要求: [中文/英文]
优化内容:
1. 权利要求措辞:
   - 使用标准专利用语 ("包括"、"设置于"、"用于"等)
   - 避免歧义表达
   - 保持术语一致性
2. 说明书撰写:
   - 背景技术描述 (客观中立)
   - 技术问题表述 (现有技术缺陷)
   - 技术方案描述 (清晰完整)
   - 有益效果 (具体量化)
3. 摘要撰写 (简明扼要)
4. 附图说明模板
</TASK>
OUTPUT: Markdown 格式润色建议 + 撰写模板
## 权利要求措辞建议
[具体建议]
## 说明书模板
[模板内容]
## 摘要模板
[模板内容]
## 常用表达替换
| 原表达 | 建议表达 |
|--------|----------|
| ... | ... |
EOF
```

##### 整合策略
等待两个模型返回后 (`TaskOutput`):
1. **采纳 Codex** 的权利要求结构 (创新点、特征分解、层次设计)
2. **采纳 Gemini** 的措辞建议 (标准用语、模板)
3. Claude 整合生成完整专利文稿

#### Step 3: 生成专利文稿

##### 权利要求书
```markdown
# 权利要求书

1. 一种[技术名称]，其特征在于，包括：
   [必要技术特征1]；
   [必要技术特征2]；
   [必要技术特征3]。

2. 根据权利要求1所述的[技术名称]，其特征在于，所述[特征1]包括[附加特征]。

3. 根据权利要求1或2所述的[技术名称]，其特征在于，[进一步限定]。

...

10. 一种[方法名称]，其特征在于，包括以下步骤：
    S1：[步骤1]；
    S2：[步骤2]；
    S3：[步骤3]。
```

##### 说明书
```markdown
# 说明书

## 技术领域
本发明涉及[领域]，具体涉及一种[技术名称]。

## 背景技术
[现有技术描述]

[现有技术存在的问题]

## 发明内容

### 技术问题
本发明要解决的技术问题是[问题描述]。

### 技术方案
为解决上述技术问题，本发明提供一种[技术名称]，包括：
[技术方案详细描述]

### 有益效果
与现有技术相比，本发明具有以下有益效果：
1. [效果1，具体数据支撑]
2. [效果2，具体数据支撑]

## 附图说明
图1为本发明[描述]的结构示意图；
图2为本发明[描述]的流程图；
...

## 具体实施方式

### 实施例1
[详细实施描述]

### 实施例2
[变体实施描述]

### 对比实验
[效果对比数据]
```

##### 摘要
```markdown
# 摘要

本发明公开了一种[技术名称]，涉及[技术领域]。该[装置/方法]包括[核心技术特征]。通过[技术手段]，实现了[技术效果]，解决了现有技术中[技术问题]的问题。本发明具有[优点1]、[优点2]等优点，适用于[应用场景]。

摘要附图：图1
```

### 6. 结果呈现

```markdown
## ✅ 专利文稿生成完成

### 生成内容
- **专利类型**: 发明专利
- **权利要求**: 10 项 (独立2项 + 从属8项)
- **说明书**: 约 5,000 字

### 创新点 (Codex 分析)
1. [核心创新点1]
2. [核心创新点2]

### 权利要求结构
- 独立权利要求 1：装置权利要求 (最大保护范围)
- 独立权利要求 10：方法权利要求
- 从属权利要求 2-9：逐步限缩

### 措辞优化 (Gemini)
- 使用标准专利用语
- 术语统一一致
- 表达清晰无歧义

### 生成文件
- 权利要求书: `artifacts/writing/claims.md`
- 说明书: `artifacts/writing/specification.md`
- 摘要: `artifacts/writing/abstract.md`
- 完整文稿: `artifacts/writing/patent-draft.md`

### ⚠️ 重要提示
专利文稿仅供参考，请专业代理人审核后提交

### 后续操作
- 专利检索: `/write:patent-search --claims claims.md`
- 修订润色: `/write:patent --revise patent-draft.md`
- 生成附图: `/write:patent --figures`
```

---

## 专利类型

### 发明专利
```bash
/write:patent --type invention --solution "技术方案描述"
```

### 实用新型
```bash
/write:patent --type utility-model --solution "技术方案描述"
```

### 外观设计
```bash
/write:patent --type design --images "设计图片路径"
```

---

## 撰写部分

### 完整文稿
```bash
/write:patent --full --solution "技术方案描述"
```

### 单独部分
```bash
/write:patent --part claims --solution "..."
/write:patent --part specification --solution "..."
/write:patent --part abstract --solution "..."
/write:patent --part drawings --solution "..."
```

### 修订润色
```bash
/write:patent --revise draft.md --focus clarity
/write:patent --revise claims.md --focus scope
```

---

## 多模型协作

**协作模式**: 双模型交叉验证

| 模型 | 职责 | 输出 |
|------|------|------|
| **Codex** | 权利要求逻辑、创新点提取、层次设计 | JSON 结构 |
| **Gemini** | 措辞润色、标准用语、模板生成 | Markdown 建议 |
| **Claude** | 整合仲裁、生成文稿、格式检查 | 完整专利文稿 |

**特殊流程**:
```
1. Codex：分析技术方案 → 提取创新点 → 构建权利要求层次结构
2. Gemini：基于 Codex 结构 → 润色权利要求措辞 → 撰写说明书
3. Claude：整合校验 → 确保逻辑与表达一致
```

---

## 错误处理

| 错误类型 | 处理策略 |
|----------|----------|
| 技术方案不清晰 | 进入澄清模式，引导用户补充细节 |
| 现有技术冲突 | 提示用户调整技术方案，标记风险点 |
| 权利要求过宽 | 建议增加限定特征 |
| 术语不一致 | 自动统一术语，生成术语表 |

---

## 安全机制

1. **免责声明**: 每次输出都标注"仅供参考，请专业代理人审核"
2. **现有技术检索**: 自动检索相关专利，提示潜在冲突
3. **结构检查**: 验证权利要求格式符合专利法要求
4. **术语一致性**: 确保全文术语统一

---

## 参考

- 共享协议: `.claude/commands/research/_protocol.md`
- 能力配置: `.claude/.research/capabilities.yaml`
- 专利检索: `/write:patent-search`
- 论文撰写: `/write:paper`
- 想法评估: `/idea:evaluate`
