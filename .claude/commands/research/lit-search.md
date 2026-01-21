---
description: '文献检索 - 基于关键词、作者、年份等条件搜索论文'
---

# /lit:search - 文献检索

$ARGUMENTS

---

## 依赖能力

- `lit.search` - 论文检索 (mcp__semantic-scholar__papers-search-basic)

## 执行流程

### 1. 上下文检索
- 调用 `mcp__ace-tool__search_context` 检查是否有相关的历史检索记录

### 2. 参数解析
支持的检索参数:
- **关键词**: `keywords:"ice load identification"`
- **作者**: `author:"Zhang Wei"`
- **年份范围**: `year:2020-2025`
- **期刊/会议**: `venue:"Journal of Structural Engineering"`
- **引用数阈值**: `min_citations:10`
- **开放获取**: `open_access:true`

### 3. 计划预览

```markdown
## 📋 执行计划

| 步骤 | 操作 | 风险等级 |
|------|------|----------|
| 1 | 解析检索参数 | none |
| 2 | 调用 Semantic Scholar API | medium |
| 3 | 过滤与排序结果 | low |
| 4 | 生成结果摘要 | low |

**预计影响**:
- 检索结果数量: 1-50 篇
- 仅读取操作，无文件创建
```

### 4. 确认门控
- **风险等级**: medium (调用外部 API)
- **行为**: confirm - 展示计划，等待用户确认

### 5. 执行

#### Step 1: 解析参数
从 `$ARGUMENTS` 提取检索条件:
```python
{
  "query": "ice load identification",
  "year_min": 2020,
  "year_max": 2025,
  "min_citations": 10,
  "open_access": True
}
```

#### Step 2: 调用 Semantic Scholar API
```javascript
// 使用 mcp__semantic-scholar__papers-search-basic
mcp__semantic-scholar__papers-search-basic({
  query: "ice load identification",
  year: "2020-2025",
  min_citations: 10,
  limit: 50
})
// 或使用高级检索
mcp__semantic-scholar__paper-search-advanced({
  query: "ice load identification",
  year: "2020-2025",
  fields_of_study: ["Engineering"],
  open_access_only: true,
  limit: 50
})
```

#### Step 3: 过滤与排序
- 按引用数降序排列
- 过滤掉非英文论文 (可选)
- 优先显示开放获取论文

#### Step 4: 生成结果摘要
```markdown
## 🔍 检索结果

### 检索条件
- 关键词: "ice load identification"
- 年份: 2020-2025
- 最低引用数: 10
- 仅开放获取: 是

### 结果统计
- 共找到 **23 篇**相关论文
- 开放获取: 12 篇
- 平均引用数: 15.3

### Top 10 论文

| # | 标题 | 作者 | 年份 | 引用数 | 开放获取 |
|---|------|------|------|--------|----------|
| 1 | [论文标题1] | Zhang et al. | 2023 | 45 | ✅ |
| 2 | [论文标题2] | Li et al. | 2022 | 32 | ✅ |
| ... | ... | ... | ... | ... | ... |

### 快捷操作
- 导入第 1 篇: `/lit:ingest arxiv:2301.12345`
- 对比前 3 篇: `/lit:compare arxiv:2301.12345,arxiv:2201.67890,arxiv:2112.34567`
- 查看引用网络: `/lit:cite arxiv:2301.12345`
```

### 6. 结果呈现

输出格式:
```markdown
## ✅ 检索完成

### 论文列表
[详细的表格或列表]

### 推荐阅读
基于引用数和相关性，推荐以下 3 篇:
1. [论文1] - [理由]
2. [论文2] - [理由]
3. [论文3] - [理由]

### 导出选项
- 导出为 BibTeX: `/lit:search --export bibtex`
- 导出为 CSV: `/lit:search --export csv`
- 保存到知识库: `/lit:ingest [paper-ids]`
```

---

## 高级检索

### 组合查询
```bash
# 多关键词 AND 逻辑
/lit:search keywords:"ice load" AND "machine learning" year:2020-2025

# 排除关键词
/lit:search keywords:"structural health monitoring" NOT "bridge" year:2022-2025

# 作者精确匹配
/lit:search author:"Zhang Wei" venue:"Engineering Structures"
```

### 引用网络检索
```bash
# 查找引用了某篇论文的文献
/lit:search citing:arxiv:2301.12345

# 查找某篇论文引用的文献
/lit:search cited_by:arxiv:2301.12345
```

---

## 示例

### 示例 1: 基础关键词检索
```bash
/lit:search ice load identification
```

### 示例 2: 高级条件检索
```bash
/lit:search keywords:"ABAQUS simulation" year:2020-2025 min_citations:20 open_access:true
```

### 示例 3: 作者检索
```bash
/lit:search author:"Zhang Wei" year:2022-2025
```

### 示例 4: 引用网络检索
```bash
/lit:search citing:10.1016/j.engstruct.2023.115678
```

---

## 输出格式

### 表格格式 (默认)
适合快速浏览，包含关键信息。

### 详细格式
```bash
/lit:search --format detailed keywords:"ice load"
```
输出包含摘要、关键词、DOI、PDF 链接等完整信息。

### 导出格式
```bash
# BibTeX
/lit:search --export bibtex keywords:"ice load" > references.bib

# CSV
/lit:search --export csv keywords:"ice load" > papers.csv

# JSON
/lit:search --export json keywords:"ice load" > papers.json
```

---

## 错误处理

| 错误类型 | 处理策略 |
|----------|----------|
| API 限流 | 等待并重试，或建议缩小检索范围 |
| 无检索结果 | 建议放宽检索条件，提供相关关键词推荐 |
| 网络连接失败 | 使用本地知识库缓存 (若有) |
| 参数格式错误 | 提示正确的参数格式示例 |

---

## 与其他命令的集成

检索结果可直接传递给其他命令:
```bash
# 检索 → 导入
/lit:search keywords:"ice load" | head -5 | /lit:ingest

# 检索 → 对比
/lit:search keywords:"ice load" year:2023 | select 1,2,3 | /lit:compare

# 检索 → 引用分析
/lit:search author:"Zhang Wei" | select 1 | /lit:cite
```

---

## 参考

- 共享协议: `.claude/commands/research/_protocol.md`
- 能力配置: `.claude/.research/capabilities.yaml`
- Semantic Scholar API: https://www.semanticscholar.org/product/api
