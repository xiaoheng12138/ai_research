# CCG WebUI 兼容性分析文档

## 1. 概述

本文档分析 CCG (codeagent-wrapper) WebUI 与 Research Workflow Assistant (RWA) 的兼容性，
并提供集成方案建议。

## 2. CCG WebUI 架构分析

### 2.1 核心组件 (基于 `server.go`)

```
┌─────────────────────────────────────────────────────────────┐
│                      CCG WebServer                           │
├─────────────────────────────────────────────────────────────┤
│  WebServer struct:                                           │
│    - clients: map[string][]chan ContentEvent                │
│    - sessions: map[string]*SessionState                     │
│    - server: *http.Server                                   │
│    - port: int (动态分配)                                   │
│    - backend: string ("codex" | "gemini" | "claude")        │
├─────────────────────────────────────────────────────────────┤
│  API 端点:                                                  │
│    GET  /            → handleIndex (HTML 页面)              │
│    GET  /api/sessions → handleSessions (JSON 列表)          │
│    GET  /api/stream/{sessionId} → handleStream (SSE)        │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 数据结构

#### SessionState
```go
type SessionState struct {
    ID        string    `json:"id"`
    Backend   string    `json:"backend"`
    Task      string    `json:"task"`
    StartTime time.Time `json:"start_time"`
    Content   string    `json:"content"`
    Done      bool      `json:"done"`
}
```

#### ContentEvent (SSE 事件)
```go
type ContentEvent struct {
    SessionID   string `json:"session_id"`
    Backend     string `json:"backend"`
    Content     string `json:"content,omitempty"`
    ContentType string `json:"content_type,omitempty"` // "reasoning", "command", "message"
    Done        bool   `json:"done,omitempty"`
}
```

### 2.3 SSE 流程

1. 客户端通过 `/api/sessions` 获取活跃会话列表
2. 选择会话后连接 `/api/stream/{sessionId}`
3. 服务端通过 `SendContent()` / `SendContentWithType()` 推送内容
4. 会话结束时发送 `Done: true` 事件

## 3. RWA 集成方案

### 3.1 方案 A: 直接复用 CCG WebUI (推荐)

**优点**: 零开发成本，已验证的 SSE 实现
**实现**: Model Bridge 调用 codeagent-wrapper 时自动启动 WebUI

```python
# model_bridge.py 中已支持
# wrapper 内部会自动启动 WebServer 并输出 Web UI URL
proc = subprocess.run([
    self._wrapper_exe,
    "--backend", backend,
    ...
], ...)
# stderr 包含: "Web UI: http://localhost:{port}"
```

### 3.2 方案 B: 扩展 TraceWriter 输出兼容事件

若需自定义 WebUI，可扩展 `TraceWriter` 输出兼容 CCG 事件格式：

```python
# trace_writer.py 扩展
def write_sse_compatible_event(self, event: TraceEvent) -> None:
    """输出 CCG WebUI 兼容的事件格式"""
    sse_event = {
        "session_id": event.get("run_id"),
        "backend": event.get("backend"),
        "content": event.get("content", {}).get("output_summary", ""),
        "content_type": self._map_phase_to_content_type(event.get("phase")),
        "done": event.get("phase") == "model_call.completed",
    }
    # 写入 SSE 格式
    ...

def _map_phase_to_content_type(self, phase: str) -> str:
    mapping = {
        "model_call.started": "reasoning",
        "model_call.completed": "message",
        "model_call.failed": "message",
    }
    return mapping.get(phase, "message")
```

### 3.3 方案 C: 独立 RWA WebUI

若需完全自定义 UI，可基于以下架构：

```
┌─────────────────────────────────────────────────────────────┐
│                    RWA WebUI Server                         │
├─────────────────────────────────────────────────────────────┤
│  数据源:                                                    │
│    - .research/logs/traces/{run_id}.jsonl (JSONL 日志)     │
│    - .research/tasks/sessions.json (会话状态)              │
├─────────────────────────────────────────────────────────────┤
│  API 端点 (兼容 CCG):                                       │
│    GET  /api/sessions      → 从 sessions.json 读取         │
│    GET  /api/stream/{id}   → 监听 JSONL 文件变化 (SSE)     │
│    GET  /api/traces/{id}   → 获取完整 trace 日志           │
└─────────────────────────────────────────────────────────────┘
```

## 4. 事件类型映射

| RWA TraceEvent.phase    | CCG ContentEvent.content_type |
|-------------------------|-------------------------------|
| model_call.started      | reasoning                     |
| model_call.completed    | message                       |
| model_call.failed       | message                       |
| session.refreshed       | reasoning                     |
| plan_start              | reasoning                     |
| step_start              | command                       |
| step_complete           | message                       |

## 5. 兼容性矩阵

| 功能                    | CCG WebUI | RWA 扩展 | 状态     |
|-------------------------|-----------|----------|----------|
| 实时输出流              | ✅        | ✅       | 完全兼容 |
| 多 backend 支持         | ✅        | ✅       | 完全兼容 |
| Session 管理            | ✅        | ✅       | 完全兼容 |
| 任务显示                | ✅        | ✅       | 完全兼容 |
| 完成通知                | ✅        | ✅       | 完全兼容 |
| 自动关闭窗口            | ✅        | N/A      | CCG 独有 |
| Trace 日志持久化        | ❌        | ✅       | RWA 独有 |
| 多模型并行展示          | ❌        | 🔄       | 待实现   |
| 证据门控可视化          | ❌        | 🔄       | 待实现   |

## 6. 建议实施路径

### Phase 1 (当前): 直接复用 CCG WebUI
- 无需额外开发
- 通过 stderr 捕获 Web UI URL 并展示给用户

### Phase 2: 扩展 TraceWriter
- 添加 SSE 兼容输出方法
- 实现 JSONL → SSE 转换

### Phase 3: 独立 RWA WebUI (可选)
- 基于 FastAPI/Starlette 实现轻量 WebUI
- 支持多模型并行展示
- 集成证据门控可视化

## 7. 技术约束

1. **端口冲突**: CCG WebUI 使用动态端口 (`:0`)，不会与 RWA 冲突
2. **跨进程通信**: 当前通过 subprocess stdout/stderr 通信，无需额外 IPC
3. **浏览器兼容性**: SSE 需要现代浏览器支持 (IE 不支持)
4. **安全性**: 仅监听 localhost，无需额外认证

## 8. 参考文件

- CCG WebServer 实现: `D:\ccg-workflow-main\codeagent-wrapper\server.go`
- RWA Trace Schema: `.claude/.research/schemas/trace.schema.json`
- RWA Model Bridge: `src/research_workflow_assistant/bridge/model_bridge.py`
