---
description: 'ABAQUS 仿真脚本修改 - 修改网格、材料、边界条件等参数'
---

# /sim:modify - 仿真脚本修改

$ARGUMENTS

---

## 依赖能力

- `shell.run` - 本地命令执行 (Bash)
- `abaqus.check` - ABAQUS 许可检查 (可选)
- `docs.query` - ABAQUS Python API 文档 (context7)

## 执行流程

### 1. 上下文检索
- 调用 `mcp__ace-tool__search_context` 定位项目中的 ABAQUS 脚本

### 2. 参数校验
检查输入是否包含:
- **脚本路径**: 目标 Python 脚本 (`.py`)
- **修改目标**: 网格、材料、边界条件、分析步等
- **修改参数**: 具体的参数值或调整策略

### 3. 计划预览

```markdown
## 📋 执行计划

| 步骤 | 操作 | 风险等级 |
|------|------|----------|
| 1 | 读取脚本 + 获取 ABAQUS API 文档 | low |
| 2 | Codex 生成修改方案 (Unified Diff) | medium |
| 3 | Claude 重构并应用变更 | medium |
| 4 | 语法检查 + 可选的 dryrun 测试 | medium |

**预计影响**:
- 修改文件: `[script-path]`
- 备份原文件: `[script-path].backup-[timestamp]`
- 可能影响后续仿真作业
```

### 4. 确认门控
- **风险等级**: medium (会修改仿真脚本)
- **行为**: confirm - 展示计划，等待用户确认

### 5. 执行

#### Step 1: 预检索 ABAQUS API 文档
在调用 Codex 之前，使用 context7 获取最佳实践:
```javascript
// 1. 解析库 ID
mcp__context7__resolve-library-id({
  libraryName: "abaqus-python",
  query: "ABAQUS Python scripting API for [修改目标]"
})

// 2. 查询文档
mcp__context7__query-docs({
  libraryId: "/abaqus/python",
  query: "如何修改 [具体参数]? 示例代码"
})
```

获取的文档示例:
```python
# ABAQUS Mesh Modification Example
part = mdb.models['Model-1'].parts['Part-1']
part.seedPart(size=0.05, deviationFactor=0.1)
part.generateMesh()
```

#### Step 2: Codex 生成修改方案

**调用 Codex** (`run_in_background: true`):

```bash
C:/Users/ljh/.claude/bin/codeagent-wrapper.exe --backend codex - "$PWD" <<'EOF'
ROLE_FILE: C:/Users/ljh/.claude/.ccg/prompts/codex/architect.md
<TASK>
任务类型: ABAQUS 脚本修改
需求: [用户修改需求]
上下文:
- 脚本路径: [script-path]
- 脚本内容: [完整 Python 代码]
- ABAQUS API 文档 (from context7):
  [context7 返回的最佳实践和 API 文档]
修改目标:
- [网格大小调整为 0.05]
- [材料属性修改为 E=2e11, nu=0.3]
- [边界条件添加新的约束]
</TASK>
OUTPUT: Unified Diff Patch ONLY. Strictly prohibit any actual modifications.
注意事项:
1. 保持原有代码结构
2. 使用 ABAQUS Python API 最佳实践
3. 添加必要的错误检查
4. 注释修改原因 (仅在复杂修改时)
EOF
```

等待 Codex 返回 (`TaskOutput`, timeout: 600000):
```diff
--- a/simulation/mesh_model.py
+++ b/simulation/mesh_model.py
@@ -15,7 +15,7 @@
 part = mdb.models['Model-1'].parts['Part-1']

 # Mesh seeding
-part.seedPart(size=0.1, deviationFactor=0.1)
+part.seedPart(size=0.05, deviationFactor=0.1)  # 细化网格以提高精度
 part.generateMesh()

@@ -23,8 +23,8 @@
 material = mdb.models['Model-1'].Material(name='Steel')
-material.Elastic(table=((2.0e11, 0.25), ))
+material.Elastic(table=((2.0e11, 0.3), ))  # 更新泊松比
```

#### Step 3: Claude 重构并应用变更

1. **思维沙箱**: 模拟应用 Diff,检查逻辑一致性
2. **重构清理**:
   - 确保符合项目现有代码规范
   - 去除冗余注释 (若Codex过度注释)
   - 验证变量名和函数调用正确性
3. **创建备份**:
   ```bash
   cp [script-path] [script-path].backup-$(date +%Y%m%d-%H%M%S)
   ```
4. **应用变更**: 使用 Edit 工具修改文件

#### Step 4: 语法检查 + Dryrun 测试

##### 语法检查
```bash
python -m py_compile [script-path]
```

##### Dryrun 测试 (可选)
```bash
# ABAQUS CAE noGUI 模式测试脚本
abaqus cae noGUI=[script-path] -- --dryrun
```

若测试失败:
- 回滚到备份
- 分析错误日志
- 修正后重试

### 6. 结果呈现

```markdown
## ✅ 脚本修改完成

### 修改摘要
| 文件 | 修改内容 | 行数 |
|------|----------|------|
| `simulation/mesh_model.py` | 网格细化: 0.1 → 0.05 | +1, -1 |
| `simulation/mesh_model.py` | 泊松比: 0.25 → 0.3 | +1, -1 |

### 变更详情
```diff
[显示完整 Unified Diff]
```

### 备份文件
- `simulation/mesh_model.py.backup-20260117-103045`

### 验证结果
- ✅ 语法检查通过
- ✅ Dryrun 测试通过 (若启用)

### 后续操作
- 运行仿真: `abaqus job=[job-name] input=[inp-file]`
- 批量提交: `/sim:batch --script [script-path]`
- 调试仿真: `/sim:debug [job-name]`
```

---

## 修改目标示例

### 网格修改
```bash
/sim:modify mesh_model.py --target mesh --size 0.05

/sim:modify mesh_model.py --target mesh --element-type C3D8R
```

### 材料参数修改
```bash
/sim:modify material_def.py --target material --E 2.1e11 --nu 0.28

/sim:modify material_def.py --target material --density 7850
```

### 边界条件修改
```bash
/sim:modify boundary.py --target bc --add-constraint "encastre at SET-1"

/sim:modify boundary.py --target bc --modify-load "pressure 1000Pa at SURF-1"
```

### 分析步修改
```bash
/sim:modify analysis.py --target step --add-static-step --duration 1.0

/sim:modify analysis.py --target step --modify-increment --initial 0.01 --max 0.1
```

---

## 高级功能

### 批量修改多个脚本
```bash
/sim:modify --batch scripts/*.py --target mesh --size 0.05
```

### 模板化修改
```bash
# 使用预定义的修改模板
/sim:modify mesh_model.py --template refine-mesh-3x

/sim:modify material_def.py --template steel-grade-Q345
```

### 交互式修改
```bash
# 启动交互式修改向导
/sim:modify --interactive mesh_model.py
```

---

## Context7 集成

### 预检索流程
```
1. Claude 识别修改目标 (如 "网格划分")
2. 调用 context7.resolve-library-id("abaqus-python", "mesh seeding")
3. 调用 context7.query-docs("/abaqus/python", "seedPart method examples")
4. 获取最佳实践:
   - API 函数签名
   - 参数说明
   - 代码示例
5. 将文档注入 Codex Brief
```

### 文档注入示例
```markdown
<CONTEXT>
## ABAQUS Python API Reference (from context7)

### Mesh Seeding
```python
part.seedPart(size=<float>, deviationFactor=<float>, minSizeFactor=<float>)
```
- `size`: 全局网格尺寸
- `deviationFactor`: 曲率偏差因子 (0.1 推荐)
- `minSizeFactor`: 最小尺寸因子

### Example
```python
part = mdb.models['Model-1'].parts['Part-1']
part.seedPart(size=0.05, deviationFactor=0.1)
part.generateMesh()
```
</CONTEXT>
```

---

## 多模型协作

**协作模式**: Codex 主导

| 模型 | 职责 | 输出 |
|------|------|------|
| **Context7** | 提供 ABAQUS API 文档和最佳实践 | API 文档 + 示例代码 |
| **Codex** | 生成脚本修改方案 | Unified Diff Patch |
| **Claude** | 预检索文档、重构代码、应用变更、验证 | 最终修改后的脚本 |

---

## 错误处理

| 错误类型 | 处理策略 |
|----------|----------|
| 脚本未找到 | 提示用户提供正确路径或使用 Glob 搜索 |
| 语法错误 | 显示错误行号，建议修复方案 |
| ABAQUS 许可不可用 | 跳过 dryrun,仅进行语法检查 |
| Codex 修改不合理 | Claude 重构时标记可疑修改，向用户报告 |
| Dryrun 失败 | 回滚到备份，分析日志，提供修复建议 |

---

## 安全机制

1. **自动备份**: 修改前自动创建带时间戳的备份文件
2. **Diff 预览**: 应用前展示完整 Unified Diff
3. **语法验证**: 修改后强制进行 Python 语法检查
4. **Dryrun 测试**: 可选的 ABAQUS noGUI 模式测试
5. **回滚支持**: 若验证失败，自动回滚到备份

---

## 参考

- 共享协议: `.claude/commands/research/_protocol.md`
- 能力配置: `.claude/.research/capabilities.yaml`
- ABAQUS Scripting Reference: (由 context7 动态获取)
- 批量提交: `/sim:batch`
- 调试诊断: `/sim:debug`
