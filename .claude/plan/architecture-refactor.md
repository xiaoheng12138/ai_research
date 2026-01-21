---
id: plan-20260118-arch-refactor
scenario: system.refactor
risk: medium
created_at: 2026-01-18
models:
  - claude
  - codex
  - gemini
inputs:
  - Research_Workflow_Assistant_Development_Plan_CN.md
  - Research_Workflow_Assistant_Implementation_Tasks.md
outputs:
  - .claude/commands/research/*.md (21 files migrated)
  - .claude/agents/research/*.md (8 agents)
  - .claude/.research/* (config + prompts + schemas)
  - src/research_workflow_assistant/bridge/* (model runner)
  - artifacts/* (output directories)
---

# 📋 实施计划：Research Workflow Assistant 架构重构

## 任务类型
- [x] 后端 (→ Codex)
- [x] 前端 (→ Gemini)
- [x] 全栈 (→ 并行)

## 技术方案

采用 **Strangler 迁移策略**（先建新骨架 + 双路径兼容 + 分阶段切换）：
1. 先落地目录骨架 + 配置事实来源
2. 先实现 `rwa model run` 抽象层
3. 再改所有命令/协议去掉 `.ccg` 引用
4. 最后清理重复与旧目录

## 实施步骤

### Phase 0：目录骨架与基线整理（P0）

#### Step 0.1：创建目标目录结构
```
.claude/
├── commands/research/          # 21 个命令文件迁移目标
├── agents/research/            # 8 个 agent 文件
└── .research/
    ├── _protocol.md            # Protocol v2
    ├── capabilities.yaml       # 能力映射
    ├── scenarios.yaml          # 场景定义
    ├── intent-taxonomy.yaml    # 意图分类
    ├── intent-mapping.yaml     # 意图-模块映射
    ├── prompts/
    │   ├── registry.yaml       # 提示词注册表
    │   ├── codex/              # Codex 角色提示词
    │   │   ├── planner.md
    │   │   ├── reasoner.md
    │   │   ├── engineer.md
    │   │   └── reviewer.md
    │   └── gemini/             # Gemini 角色提示词
    │       ├── ideator.md
    │       ├── writer.md
    │       ├── explainer.md
    │       └── designer.md
    ├── schemas/
    │   ├── plan.schema.json
    │   ├── evidence.schema.json
    │   └── manifest.schema.json
    └── templates/
        ├── plan.md
        └── report.md

.research/                      # Runtime 目录（从配置目录转变）
├── tasks/
├── plans/
├── logs/
├── cache/
└── kb/

artifacts/                      # 产物目录
├── reports/
├── figures/
├── processed-data/
├── models/
├── papers/
├── writing/
└── manifest/
```

#### Step 0.2：迁移命令文件
从 `commands/research/*.md` → `.claude/commands/research/*.md`

需迁移的 21 个文件：
1. `_protocol.md` → 重写为 Protocol v2
2. `research.md`
3. `research-help.md`
4. `lit-search.md`
5. `lit-ingest.md`
6. `lit-summarize.md`
7. `lit-compare.md`
8. `lit-cite.md`
9. `idea-brainstorm.md`
10. `idea-evaluate.md`
11. `data-process.md`
12. `data-train.md`
13. `data-calibrate.md`
14. `data-compare.md`
15. `sim-modify.md`
16. `sim-batch.md`
17. `sim-debug.md`
18. `sim-odb.md`
19. `write-paper.md`
20. `write-patent.md`
21. `write-patent-search.md`

#### Step 0.3：迁移配置文件
从 `.research/*.yaml` → `.claude/.research/*.yaml`

需迁移的 4 个文件：
- `capabilities.yaml`
- `scenarios.yaml`
- `intent-taxonomy.yaml`
- `intent-mapping.yaml`

处理 `src/research_workflow_assistant/registry/data/*.yaml` 重复：
- 短期保留作为 fallback
- 中期统一到 `.claude/.research/`

#### Step 0.4：更新 .gitignore
```gitignore
# Runtime (不入库)
.research/cache/
.research/logs/
.research/tasks/*.state.json

# Artifacts (大文件不入库)
artifacts/**/*.pdf
artifacts/**/*.odb
artifacts/models/
artifacts/processed-data/

# 保留示例
!artifacts/reports/.gitkeep
!artifacts/figures/.gitkeep
```

---

### Phase 1：核心协议 + 模型桥接（P0）

#### Step 1.1：Protocol v2 重写
文件：`.claude/.research/_protocol.md`

核心内容：
- Plan Card / Result Card / Evidence Record / Artifact Manifest 格式
- 风险门控规则：none/low/medium/high → auto/confirm/confirm+preview
- 协作模式：S（单模型）/ X（交叉验证）/ T（三角协作）
- 外部模型不落盘原则
- 证据门控：主张分类（fact/inference/speculation）+ 状态（verified/unverified/rejected）

#### Step 1.2：Codex/Gemini 提示词体系
新建 8 个角色提示词：

**Codex 角色（结构化输出）：**
- `planner.md`：长期规划/里程碑/依赖拆解，默认 JSON
- `reasoner.md`：科研推理/论证链/风险矩阵，默认 JSON
- `engineer.md`：脚本/代码/实验可复现步骤；涉及改文件→diff-only
- `reviewer.md`：审计 Gemini 主张/检查漏洞/提出验证方案

**Gemini 角色（创意表达）：**
- `ideator.md`：创意发散；必须输出 Claims + Evidence Needed
- `writer.md`：写作润色；禁止编造 DOI/作者/年份；不确定要标注
- `explainer.md`：科普/叙事组织；必须给出"待核对点清单"
- `designer.md`：图表/呈现设计；给出可视化建议与标注策略

#### Step 1.3：结构化 Schema
新建 3 个 JSON Schema：

```json
// plan.schema.json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "type": "object",
  "required": ["id", "scenario", "risk", "steps"],
  "properties": {
    "id": {"type": "string", "pattern": "^plan-\\d{8}-\\d{3}$"},
    "scenario": {"type": "string"},
    "risk": {"enum": ["none", "low", "medium", "high"]},
    "steps": {"type": "array", "items": {"$ref": "#/$defs/step"}}
  }
}

// evidence.schema.json
{
  "type": "object",
  "required": ["task_id", "claims"],
  "properties": {
    "task_id": {"type": "string"},
    "claims": {"type": "array", "items": {"$ref": "#/$defs/claim"}}
  }
}

// manifest.schema.json
{
  "type": "object",
  "required": ["task_id", "timestamp", "inputs", "outputs"],
  "properties": {
    "task_id": {"type": "string"},
    "plan_id": {"type": "string"},
    "models_used": {"type": "array"},
    "inputs": {"type": "array"},
    "outputs": {"type": "array"}
  }
}
```

#### Step 1.4：Model Runner 抽象层
新建 Python 模块：`src/research_workflow_assistant/bridge/`

```python
# bridge/model_runner.py
class ModelRunner:
    def run(self, backend: str, role: str, task: str,
            context: dict, output_format: str = "json",
            session_id: str = None) -> ModelOutput:
        """
        统一模型调用接口
        - backend: codex | gemini
        - role: planner | reasoner | engineer | reviewer | ideator | writer | explainer | designer
        - output_format: json | diff | markdown
        """
        prompt = self._load_role_prompt(backend, role)
        request = self._render_request(prompt, task, context, output_format)
        impl = self._get_backend(backend)
        return impl.run(request, session_id)

# bridge/backends/codex_backend.py
class CodexBackend:
    def run(self, request: str, session_id: str = None) -> str:
        # 优先 MCP，fallback 到 CLI
        pass

# bridge/backends/gemini_backend.py
class GeminiBackend:
    def run(self, request: str, session_id: str = None) -> str:
        # 优先 MCP，fallback 到 CLI
        pass
```

#### Step 1.5：CLI 扩展
更新 `src/research_workflow_assistant/cli.py`：

```python
# 新增命令
rwa doctor          # 检查配置、MCP 可用性、目录可写
rwa model run       # 统一模型调用入口
rwa plan validate   # 校验计划文件
rwa evidence validate  # 校验证据文件
rwa manifest write  # 写入 manifest
```

#### Step 1.6：子智能体（Agents）
新建 8 个 agent 文件：`.claude/agents/research/`

| Agent | 职责 |
|-------|------|
| `orchestrator.md` | 总控编排、门控、产物落盘 |
| `intent-router.md` | 基于 taxonomy/mapping 识别意图 |
| `planner.md` | 生成可执行计划（偏工程化） |
| `verifier.md` | Evidence Gate：验证主张、标注风险 |
| `librarian.md` | 文献筛选、去重、聚类、引用管理 |
| `data-analyst.md` | 数据流程、指标、可视化建议 |
| `simulation-engineer.md` | 仿真脚本/作业/后处理策略 |
| `writer.md` | 论文/专利写作结构与一致性 |

#### Step 1.7：去 CCG 化全局清扫
需清理的 22 个文件中的 `.ccg`/`codeagent-wrapper`/绝对路径引用：

替换规则：
```
# 旧
C:/Users/ljh/.claude/bin/codeagent-wrapper.exe --backend codex - "$PWD" <<'EOF'
ROLE_FILE: C:/Users/ljh/.claude/.ccg/prompts/codex/analyzer.md
...
EOF

# 新
rwa model run --backend codex --role planner --task "..." --context "..."
```

---

### Phase 2：科研核心闭环（P0/P1）

#### Step 2.1：/research 入口改造
- 读取 `.claude/.research/*.yaml`
- 获取上下文：项目文件/最近 artifacts/plan/task ledger
- 输出：路由结果（intent+置信度）+ 推荐命令 + 下一步

#### Step 2.2：文献域命令升级
- `/lit:search`：检索 + 筛选 + 导出（csv/bibtex）
- `/lit:ingest`：PDF/DOI/arXiv → KB 条目
- `/lit:summarize`：Codex（结构化）+ Gemini（叙事）+ 合并
- `/lit:compare`：对比矩阵 + 推荐阅读顺序
- `/lit:cite`：引用网络图 + 分析报告

#### Step 2.3：想法域命令升级
- `/idea:brainstorm`（三角协作 T）：Gemini 发散 → Codex 评审 → TOP-N
- `/idea:evaluate`（交叉验证 X）：可行性/创新性/风险矩阵

#### Step 2.4：写作域命令升级
- `/write:paper`（交叉验证 X）：章节论证链 + 可读性建议
- `/write:patent-search`：检索策略 + 专利列表
- `/write:patent`（交叉验证 X）：权利要求结构 + 措辞规范化

#### Step 2.5：Evidence Gate v1
```python
# workflow/evidence_gate.py
def extract_claims(gemini_output: str) -> list[Claim]:
    """解析 Gemini 输出中的 Claims 段落"""
    pass

def verify_claims(claims: list[Claim], kb: KnowledgeBase) -> EvidenceReport:
    """验证主张，返回 verified/unverified/rejected 分类"""
    pass

def annotate_report(report: str, evidence: EvidenceReport) -> str:
    """在报告中标注 ✅已验证 / ⚠️待验证 / ❌证据不足"""
    pass
```

#### Step 2.6：Artifact Manifest v1
```python
# workflow/manifest.py
def write_manifest(task_id: str, plan_id: str,
                   inputs: list, outputs: list,
                   models_used: list) -> Path:
    """写入 artifacts/manifest/<task-id>.json"""
    pass
```

---

### Phase 3：数据/仿真深度集成（P1）

#### Step 3.1：数据域命令升级
- `/data:process`：处理脚本 + 数据质量检查 + 可视化
- `/data:train`（high-risk）：训练脚本 + 评估脚本 + 门控
- `/data:calibrate`（high-risk）：敏感性分析 + 参数标定

#### Step 3.2：仿真域命令升级
- `/sim:modify`（medium-risk）：Unified Diff + 自动备份
- `/sim:batch`（high-risk）：作业数量/资源预算/并发限制
- `/sim:debug`（medium-risk）：日志解析 → 诊断 → 建议
- `/sim:odb`（low-risk）：ODB 提取脚本 + 可视化

#### Step 3.3：会话路径迁移
更新 `src/research_workflow_assistant/integration/session.py`：
- 从 `~/.research_workflow/sessions` → `.research/tasks/`
- 添加迁移兼容逻辑

---

### Phase 4：工作流组合与长期任务管理（P2）

#### Step 4.1：/compose 命令
- 定义 `compose.schema.json`（steps、depends_on、cache_key、retry、risk）
- 实现 `workflow/dag_executor.py`

#### Step 4.2：Task Ledger
- `.research/tasks/task-ledger.jsonl`
- `/research:status` 命令

#### Step 4.3：Resume 增强
- 从 `state.json` 恢复
- high-risk 步骤恢复前强制再次确认

---

### Phase 5：测试与文档（P1/P2）

#### Step 5.1：守卫脚本
- `scripts/lint_no_ccg_refs.py`：扫描 `.ccg`/wrapper/绝对路径
- `scripts/validate_config.py`：校验 YAML 结构与一致性

#### Step 5.2：单元测试
- `tests/test_schema_validate.py`
- `tests/test_model_runner_mock.py`
- `tests/test_evidence_gate.py`

#### Step 5.3：文档
- `docs/quickstart.md`
- `examples/` 示例工程

---

## 关键文件

| 文件 | 操作 | 说明 |
|------|------|------|
| `.claude/commands/research/*.md` | 新建/迁移 | 21 个命令文件 |
| `.claude/agents/research/*.md` | 新建 | 8 个 agent 文件 |
| `.claude/.research/_protocol.md` | 新建 | Protocol v2 |
| `.claude/.research/prompts/**/*.md` | 新建 | 8 个角色提示词 |
| `.claude/.research/schemas/*.json` | 新建 | 3 个 JSON Schema |
| `src/research_workflow_assistant/bridge/` | 新建 | Model Runner 模块 |
| `src/research_workflow_assistant/workflow/` | 新建 | Evidence Gate + Manifest |
| `src/research_workflow_assistant/cli.py` | 修改 | 新增 CLI 命令 |
| `commands/research/*.md` | 删除 | 迁移后删除旧目录 |
| `.research/*.yaml` | 迁移 | 移动到 `.claude/.research/` |

## 风险与缓解

| 风险 | 缓解措施 |
|------|----------|
| 路径迁移导致命令找不到配置 | config loader 多路径回退 + deprecation 警告 |
| 旧 `.research/` 从配置变为 runtime 冲突 | 一次性迁移脚本 + 启动时检测冲突 |
| 仍依赖 wrapper 或本机绝对路径 | 封装到 `bridge/backends/*`，仓库只出现 `rwa model run` |
| 大量未实现模块导致路由后不可执行 | 短期以命令层工作流交付，中期补齐模块 |
| Windows 特殊文件名导致工具链异常 | 检查并重命名/删除 `nul` 等特殊文件 |

## SESSION_ID（供 /ccg:execute 使用）
- CODEX_SESSION: 019bd1d3-b23b-7670-a854-86712958553a
- GEMINI_SESSION: 8b6def97-ac12-4cbe-94c9-a6e5ad08c732
