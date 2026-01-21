---
description: 'ABAQUS 仿真调试诊断 - 分析错误、警告、收敛问题'
---

# /sim:debug - 仿真调试

$ARGUMENTS

---

## 依赖能力

- `shell.run` - 本地命令执行 (Bash)
- `docs.query` - ABAQUS 错误代码文档 (context7)

## 执行流程

### 1. 上下文检索
- 调用 `mcp__ace-tool__search_context` 定位作业日志和错误文件

### 2. 参数校验
检查输入是否包含:
- **作业名称**: ABAQUS 作业名 (job-name)
- 或 **日志文件路径**: `.msg`, `.dat`, `.sta` 文件

### 3. 计划预览

```markdown
## 📋 执行计划

| 步骤 | 操作 | 风险等级 |
|------|------|----------|
| 1 | 收集日志文件 (.msg, .dat, .sta) | low |
| 2 | 提取错误与警告信息 | low |
| 3 | Codex 诊断错误原因 | low |
| 4 | 生成修复建议 | low |

**预计影响**:
- 生成诊断报告: `artifacts/debug/debug-[job-name].md`
- 仅读取操作,不修改文件
```

### 4. 确认门控
- **风险等级**: low (仅读取日志分析,不修改文件)
- **行为**: auto - 自动执行

### 5. 执行

#### Step 1: 收集日志文件
查找作业相关文件:
```bash
# 查找日志文件
find . -name "[job-name].*" -type f | grep -E "\.(msg|dat|sta|log)$"
```

关键文件:
- `.msg` - 主要消息文件 (错误、警告)
- `.dat` - 数据文件 (详细输出)
- `.sta` - 状态文件 (迭代收敛信息)
- `.log` - 日志文件

#### Step 2: 提取错误与警告信息
解析日志文件,提取:
- **错误** (ERROR, ABORTED)
- **警告** (WARNING)
- **收敛问题** (NOT CONVERGED, DIVERGENCE)
- **异常退出** (SEGMENTATION FAULT)

示例提取:
```bash
grep -E "(ERROR|WARNING|ABORTED|NOT CONVERGED)" [job-name].msg
```

#### Step 3: 预检索 ABAQUS 错误代码文档
对每个错误代码,使用 context7 查询文档:
```javascript
mcp__context7__query-docs({
  libraryId: "/abaqus/documentation",
  query: "ABAQUS error code [错误代码] 原因与解决方案"
})
```

#### Step 4: Codex 诊断错误原因

**调用 Codex** (`run_in_background: true`):

```bash
C:/Users/ljh/.claude/bin/codeagent-wrapper.exe --backend codex - "$PWD" <<'EOF'
ROLE_FILE: C:/Users/ljh/.claude/.ccg/prompts/codex/analyzer.md
<TASK>
任务类型: ABAQUS 仿真错误诊断
需求: 分析仿真失败原因并提供修复建议
上下文:
- 作业名: [job-name]
- 错误日志: [提取的错误与警告]
- MSG 文件内容: [完整 .msg 文件]
- STA 文件内容: [迭代收敛信息]
- ABAQUS 错误文档 (from context7):
  [错误代码说明与解决方案]
关注点:
- 错误根因分析 (网格问题? 材料定义? 边界条件?)
- 收敛问题诊断 (时间步过大? 接触问题?)
- 修复优先级 (先修什么,后修什么)
- 具体修复步骤 (参数调整、脚本修改)
</TASK>
OUTPUT: JSON 格式诊断报告
{
  "summary": "问题概述",
  "errors": [
    {
      "code": "错误代码",
      "message": "错误信息",
      "root_cause": "根因分析",
      "severity": "critical|high|medium|low",
      "fix_priority": 1
    }
  ],
  "warnings": [
    {
      "message": "警告信息",
      "impact": "影响评估",
      "recommendation": "建议"
    }
  ],
  "convergence_issues": {
    "status": "收敛状态",
    "last_converged_increment": 123,
    "failure_increment": 125,
    "analysis": "收敛失败原因"
  },
  "fix_recommendations": [
    {
      "step": 1,
      "action": "修改网格尺寸从 0.1 到 0.05",
      "file": "mesh_model.py",
      "rationale": "网格过粗导致应力奇异"
    },
    {
      "step": 2,
      "action": "调整时间步从 0.1 到 0.01",
      "file": "analysis.py",
      "rationale": "时间步过大导致接触不稳定"
    }
  ]
}
EOF
```

等待 Codex 返回 (`TaskOutput`, timeout: 600000)。

#### Step 5: 生成诊断报告

```markdown
# ABAQUS 仿真诊断报告
**作业名**: [job-name]
**诊断时间**: 2026-01-17 10:30:45

---

## 问题概述 (Codex 分析)
[问题概述]

---

## 错误列表
| 优先级 | 错误代码 | 错误信息 | 根因 |
|--------|----------|----------|------|
| 1 | ERROR-123 | Element distortion | 网格质量差 |
| 2 | ERROR-456 | Contact not converged | 时间步过大 |

### 错误 #1: Element distortion (高优先级)
**错误代码**: ERROR-123
**错误信息**: Excessive element distortion in element 12345
**根因分析** (Codex):
- 网格尺寸过大,在高应力区域导致单元畸变
- 可能由于几何形状复杂但网格过粗

**修复建议**:
1. 细化网格: 将全局尺寸从 0.1 改为 0.05
2. 局部加密: 在高应力区域使用 mesh refinement
3. 修改文件: `mesh_model.py`

**参考文档** (Context7):
[ABAQUS Element Distortion 解决方案]

---

### 错误 #2: Contact not converged (中优先级)
[类似格式]

---

## 警告列表
| 警告信息 | 影响 | 建议 |
|----------|------|------|
| Large displacement detected | 可能导致结果不准确 | 启用 NLGEOM |

---

## 收敛分析 (Codex 诊断)
**收敛状态**: 失败
**最后收敛增量步**: 123
**失败增量步**: 125

**失败原因**:
- 接触压力突变,导致接触算法无法收敛
- 时间步 0.1 过大,建议减小到 0.01

**收敛曲线** (从 .sta 文件提取):
```
Increment  Time     Force Residual  Displacement Residual
120        12.0     1.23e-05        5.67e-06
121        12.1     2.34e-05        8.90e-06
122        12.2     4.56e-05        1.23e-05
123        12.3     7.89e-05        2.34e-05
124        12.4     NOT CONVERGED
125        12.5     DIVERGENCE DETECTED
```

---

## 修复步骤 (优先级排序)

### Step 1: 细化网格 (高优先级)
**文件**: `mesh_model.py`
**修改**:
```python
# 修改前
part.seedPart(size=0.1, deviationFactor=0.1)

# 修改后
part.seedPart(size=0.05, deviationFactor=0.1)
# 局部加密高应力区域
region = part.sets['HighStressRegion']
part.seedEdgeBySize(edges=region.edges, size=0.02)
```

**执行命令**:
```bash
/sim:modify mesh_model.py --target mesh --size 0.05 --refine-region HighStressRegion --refine-size 0.02
```

---

### Step 2: 调整时间步 (中优先级)
**文件**: `analysis.py`
**修改**:
```python
# 修改前
step.setValues(initialInc=0.1, maxInc=0.1)

# 修改后
step.setValues(initialInc=0.01, maxInc=0.05)
```

**执行命令**:
```bash
/sim:modify analysis.py --target step --initial-inc 0.01 --max-inc 0.05
```

---

### Step 3: 启用几何非线性 (低优先级)
**文件**: `analysis.py`
**修改**:
```python
step.setValues(nlgeom=ON)
```

---

## 快速修复脚本
以下脚本自动应用所有修复:
```bash
#!/bin/bash
# auto_fix_[job-name].sh

/sim:modify mesh_model.py --target mesh --size 0.05
/sim:modify analysis.py --target step --initial-inc 0.01 --max-inc 0.05
/sim:modify analysis.py --target step --nlgeom ON

echo "修复完成,重新运行作业:"
echo "abaqus job=[job-name] input=[job-name].inp cpus=4 interactive"
```

---

## 附录: 完整日志
[可选: 附加完整 .msg 和 .sta 文件内容]
```

### 6. 结果呈现

```markdown
## ✅ 诊断完成

### 问题统计
- 错误: 2 个 (高优先级: 1, 中优先级: 1)
- 警告: 3 个
- 收敛问题: 是 (增量步 125 失败)

### 生成文件
- 诊断报告: `artifacts/debug/debug-[job-name].md`
- 快速修复脚本: `artifacts/debug/auto_fix_[job-name].sh`

### 后续操作
- 自动修复: `bash artifacts/debug/auto_fix_[job-name].sh`
- 手动修复: 按报告中的 Step 1-3 逐步执行
- 重新运行: `abaqus job=[job-name] input=[job-name].inp cpus=4 interactive`
```

---

## 常见问题诊断

### 网格问题
```bash
/sim:debug [job-name] --focus mesh
```
- 单元畸变
- 网格质量差
- 局部过粗/过细

### 收敛问题
```bash
/sim:debug [job-name] --focus convergence
```
- 时间步过大
- 接触不稳定
- 材料非线性

### 接触问题
```bash
/sim:debug [job-name] --focus contact
```
- 接触压力突变
- 穿透检测
- 摩擦系数不合理

### 材料定义问题
```bash
/sim:debug [job-name] --focus material
```
- 材料参数缺失
- 非物理材料属性
- 本构模型不适用

---

## 批量诊断

```bash
# 诊断所有失败的作业
/sim:debug --batch --status ABORTED

# 诊断特定模式的作业
/sim:debug --batch --pattern "model_param_*"
```

---

## 多模型协作

**协作模式**: Codex 主导

| 模型 | 职责 | 输出 |
|------|------|------|
| **Context7** | 提供 ABAQUS 错误代码文档 | 错误说明 + 解决方案 |
| **Codex** | 错误根因分析、修复建议 | JSON 诊断报告 |
| **Claude** | 预检索文档、解析日志、生成报告 | 完整诊断报告 + 修复脚本 |

---

## 错误处理

| 错误类型 | 处理策略 |
|----------|----------|
| 日志文件未找到 | 提示用户提供正确的作业名或日志路径 |
| 日志文件过大 | 仅提取错误与警告部分 |
| 错误代码未知 | 使用 context7 搜索,若仍无结果,建议用户查阅手册 |
| Codex 分析超时 | 使用简化版诊断 (仅错误列表) |

---

## 参考

- 共享协议: `.claude/commands/research/_protocol.md`
- 能力配置: `.research/capabilities.yaml`
- 脚本修改: `/sim:modify`
- 批量提交: `/sim:batch`
