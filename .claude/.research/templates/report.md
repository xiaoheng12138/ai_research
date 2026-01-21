# Report Template

## ✅ 执行完成

**任务 ID**: `{task_id}`
**完成时间**: {completed_at}
**总耗时**: {duration}

---

### 结果摘要

{summary}

---

### 执行过程

| 步骤 | 状态 | 执行模型 | 耗时 |
|------|------|----------|------|
| 1 | {status_1} | {model_1} | {duration_1} |
| 2 | {status_2} | {model_2} | {duration_2} |
| ... | ... | ... | ... |

---

### 生成产物

| 产物 | 路径 | 大小 |
|------|------|------|
| {artifact_1} | `{path_1}` | {size_1} |
| ... | ... | ... |

---

### Evidence Gate 结果

| 主张 | 类型 | 状态 | 来源 |
|------|------|------|------|
| {claim_1} | {type_1} | ✅/⚠️/❌ | {source_1} |
| ... | ... | ... | ... |

**统计**:
- ✅ Verified: {verified_count}
- ⚠️ Unverified: {unverified_count}
- ❌ Rejected: {rejected_count}

---

### 待核对点

1. {to_verify_1}
2. {to_verify_2}
3. ...

---

### 后续建议

- {recommendation_1}
- {recommendation_2}
- ...

---

### Trace 引用

- **Run ID**: `{run_id}`
- **Trace 文件**: `.research/logs/traces/{run_id}.jsonl`
- **Manifest**: `artifacts/manifest/{task_id}.json`
