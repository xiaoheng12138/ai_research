"""SSE-based WebUI Server for Research Workflow Assistant.

Modeled after CCG WebUI (codeagent-wrapper/server.go), providing:
- Server-Sent Events (SSE) for real-time streaming
- Session management with backend-specific styling
- Auto-close window feature (3 seconds after completion)
- Three-model collaboration visualization (Claude/Codex/Gemini)
"""
from __future__ import annotations

import asyncio
import html
import json
import logging
import os
import subprocess
import sys
import threading
import webbrowser
from dataclasses import dataclass, field
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from queue import Empty, Queue
from typing import Any, Literal
from urllib.parse import parse_qs, urlparse

logger = logging.getLogger(__name__)

Backend = Literal["codex", "gemini", "claude"]
ContentType = Literal["reasoning", "command", "message", "error", "info"]

# Backend-specific colors (matching CCG WebUI)
BACKEND_COLORS: dict[str, dict[str, str]] = {
    "codex": {"primary": "#10b981", "bg": "rgba(16, 185, 129, 0.1)", "name": "Codex"},
    "gemini": {"primary": "#8b5cf6", "bg": "rgba(139, 92, 246, 0.1)", "name": "Gemini"},
    "claude": {"primary": "#f97316", "bg": "rgba(249, 115, 22, 0.1)", "name": "Claude"},
}


@dataclass
class ContentEvent:
    """Event sent to SSE clients."""
    session_id: str
    backend: str
    content: str = ""
    content_type: ContentType = "message"
    done: bool = False
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_json(self) -> str:
        return json.dumps({
            "session_id": self.session_id,
            "backend": self.backend,
            "content": self.content,
            "content_type": self.content_type,
            "done": self.done,
            "timestamp": self.timestamp,
        }, ensure_ascii=False)


@dataclass
class SessionState:
    """Tracks a running session."""
    session_id: str
    backend: str
    role: str
    task_preview: str
    started_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    done: bool = False


class UIServer:
    """SSE-based WebUI server for real-time model output streaming."""

    def __init__(self, port: int = 0, auto_open: bool = True, auto_close_delay: int = 3) -> None:
        self._port = port
        self._auto_open = auto_open
        self._auto_close_delay = auto_close_delay
        self._server: ThreadingHTTPServer | None = None
        self._thread: threading.Thread | None = None
        self._lock = threading.RLock()
        self._clients: dict[str, list[Queue[ContentEvent]]] = {}
        self._sessions: dict[str, SessionState] = {}
        self._running = False

    @property
    def port(self) -> int:
        return self._port

    @property
    def url(self) -> str:
        return f"http://127.0.0.1:{self._port}"

    def start(self) -> int:
        """Start the server, returns the actual port."""
        with self._lock:
            if self._running:
                return self._port

            handler = self._create_handler()
            self._server = ThreadingHTTPServer(("127.0.0.1", self._port), handler)
            self._port = self._server.server_address[1]
            self._running = True

            self._thread = threading.Thread(target=self._serve, daemon=True)
            self._thread.start()

            logger.info(f"UIServer started on {self.url}")
            return self._port

    def stop(self) -> None:
        """Stop the server."""
        with self._lock:
            if not self._running:
                return
            self._running = False
            if self._server:
                self._server.shutdown()
                self._server = None
            self._thread = None
            logger.info("UIServer stopped")

    def _serve(self) -> None:
        if self._server:
            self._server.serve_forever()

    def create_session(self, session_id: str, backend: str, role: str, task_preview: str) -> None:
        """Create a new session."""
        with self._lock:
            self._sessions[session_id] = SessionState(
                session_id=session_id,
                backend=backend,
                role=role,
                task_preview=task_preview[:200],
            )
            self._clients.setdefault(session_id, [])

    def close_session(self, session_id: str) -> None:
        """Mark session as done and send done event."""
        with self._lock:
            session = self._sessions.get(session_id)
            if session:
                session.done = True
            self.send_event(ContentEvent(
                session_id=session_id,
                backend=session.backend if session else "claude",
                content="",
                content_type="info",
                done=True,
            ))

    def send_event(self, event: ContentEvent) -> None:
        """Send event to all clients subscribed to the session."""
        with self._lock:
            queues = self._clients.get(event.session_id, [])
            for q in queues:
                try:
                    q.put_nowait(event)
                except Exception:
                    pass

    def open_browser(self, session_id: str) -> None:
        """Open browser to the session page."""
        if self._auto_open:
            url = f"{self.url}/?session_id={session_id}"
            try:
                webbrowser.open(url)
                logger.info(f"Opened browser: {url}")
            except Exception as e:
                logger.warning(f"Failed to open browser: {e}")

    def _create_handler(self) -> type[BaseHTTPRequestHandler]:
        server = self

        class Handler(BaseHTTPRequestHandler):
            protocol_version = "HTTP/1.1"

            def log_message(self, format: str, *args: Any) -> None:
                logger.debug(f"HTTP: {format % args}")

            def do_GET(self) -> None:
                parsed = urlparse(self.path)
                path = parsed.path
                query = parse_qs(parsed.query)

                if path == "/" or path == "/index.html":
                    session_id = query.get("session_id", [""])[0]
                    self._serve_html(session_id)
                elif path == "/api/sessions":
                    self._serve_sessions()
                elif path.startswith("/api/stream/"):
                    session_id = path[len("/api/stream/"):]
                    self._serve_sse(session_id)
                else:
                    self.send_error(404)

            def _serve_html(self, session_id: str) -> None:
                html_content = server._generate_html(session_id)
                content = html_content.encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(content)))
                self.send_header("Cache-Control", "no-cache")
                self.end_headers()
                self.wfile.write(content)

            def _serve_sessions(self) -> None:
                with server._lock:
                    data = [
                        {
                            "session_id": s.session_id,
                            "backend": s.backend,
                            "role": s.role,
                            "task_preview": s.task_preview,
                            "started_at": s.started_at,
                            "done": s.done,
                        }
                        for s in server._sessions.values()
                    ]
                content = json.dumps(data, ensure_ascii=False).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Length", str(len(content)))
                self.end_headers()
                self.wfile.write(content)

            def _serve_sse(self, session_id: str) -> None:
                self.send_response(200)
                self.send_header("Content-Type", "text/event-stream")
                self.send_header("Cache-Control", "no-cache")
                self.send_header("Connection", "keep-alive")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()

                q: Queue[ContentEvent] = Queue()
                with server._lock:
                    server._clients.setdefault(session_id, []).append(q)

                try:
                    while server._running:
                        try:
                            event = q.get(timeout=30)
                            data = f"data: {event.to_json()}\n\n"
                            self.wfile.write(data.encode("utf-8"))
                            self.wfile.flush()
                            if event.done:
                                break
                        except Empty:
                            # Send heartbeat
                            self.wfile.write(b": heartbeat\n\n")
                            self.wfile.flush()
                except (BrokenPipeError, ConnectionResetError):
                    pass
                finally:
                    with server._lock:
                        clients = server._clients.get(session_id, [])
                        if q in clients:
                            clients.remove(q)

        return Handler

    def _generate_html(self, session_id: str) -> str:
        """Generate the HTML page for a session."""
        auto_close_delay = self._auto_close_delay
        backend_colors_json = json.dumps(BACKEND_COLORS, ensure_ascii=False)

        return f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Research Workflow Assistant</title>
    <style>
        :root {{
            --bg-primary: #0d1117;
            --bg-secondary: #161b22;
            --bg-tertiary: #21262d;
            --text-primary: #c9d1d9;
            --text-secondary: #8b949e;
            --border-color: #30363d;
            --codex-color: #10b981;
            --gemini-color: #8b5cf6;
            --claude-color: #f97316;
        }}

        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            background: var(--bg-primary);
            color: var(--text-primary);
            min-height: 100vh;
            display: flex;
            flex-direction: column;
        }}

        .header {{
            background: var(--bg-secondary);
            border-bottom: 1px solid var(--border-color);
            padding: 16px 24px;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }}

        .header h1 {{
            font-size: 18px;
            font-weight: 600;
            display: flex;
            align-items: center;
            gap: 8px;
        }}

        .header .logo {{
            width: 24px;
            height: 24px;
            background: linear-gradient(135deg, var(--codex-color), var(--gemini-color), var(--claude-color));
            border-radius: 6px;
        }}

        .status {{
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 14px;
            color: var(--text-secondary);
        }}

        .status-dot {{
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: var(--codex-color);
            animation: pulse 2s infinite;
        }}

        .status-dot.done {{
            background: var(--text-secondary);
            animation: none;
        }}

        @keyframes pulse {{
            0%, 100% {{ opacity: 1; }}
            50% {{ opacity: 0.5; }}
        }}

        .content {{
            flex: 1;
            padding: 24px;
            overflow-y: auto;
        }}

        .message {{
            margin-bottom: 16px;
            padding: 16px;
            border-radius: 8px;
            background: var(--bg-secondary);
            border-left: 3px solid var(--text-secondary);
        }}

        .message.codex {{
            border-left-color: var(--codex-color);
            background: rgba(16, 185, 129, 0.05);
        }}

        .message.gemini {{
            border-left-color: var(--gemini-color);
            background: rgba(139, 92, 246, 0.05);
        }}

        .message.claude {{
            border-left-color: var(--claude-color);
            background: rgba(249, 115, 22, 0.05);
        }}

        .message-header {{
            display: flex;
            align-items: center;
            gap: 8px;
            margin-bottom: 8px;
            font-size: 12px;
            color: var(--text-secondary);
        }}

        .message-backend {{
            font-weight: 600;
            text-transform: uppercase;
        }}

        .message.codex .message-backend {{ color: var(--codex-color); }}
        .message.gemini .message-backend {{ color: var(--gemini-color); }}
        .message.claude .message-backend {{ color: var(--claude-color); }}

        .message-type {{
            padding: 2px 6px;
            border-radius: 4px;
            background: var(--bg-tertiary);
            font-size: 11px;
        }}

        .message-content {{
            font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace;
            font-size: 14px;
            line-height: 1.6;
            white-space: pre-wrap;
            word-break: break-word;
        }}

        .done-banner {{
            position: fixed;
            bottom: 24px;
            left: 50%;
            transform: translateX(-50%);
            background: var(--bg-secondary);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            padding: 16px 24px;
            display: none;
            align-items: center;
            gap: 12px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
        }}

        .done-banner.show {{
            display: flex;
        }}

        .done-icon {{
            width: 24px;
            height: 24px;
            background: var(--codex-color);
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: bold;
        }}

        .done-text {{
            font-size: 14px;
        }}

        .countdown {{
            color: var(--text-secondary);
            font-size: 12px;
        }}

        .empty-state {{
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            height: 100%;
            color: var(--text-secondary);
            gap: 16px;
        }}

        .empty-state svg {{
            width: 64px;
            height: 64px;
            opacity: 0.5;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>
            <div class="logo"></div>
            Research Workflow Assistant
        </h1>
        <div class="status">
            <div class="status-dot" id="statusDot"></div>
            <span id="statusText">连接中...</span>
        </div>
    </div>

    <div class="content" id="content">
        <div class="empty-state" id="emptyState">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                <path d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
            </svg>
            <div>等待模型输出...</div>
        </div>
    </div>

    <div class="done-banner" id="doneBanner">
        <div class="done-icon">✓</div>
        <div>
            <div class="done-text">任务完成</div>
            <div class="countdown" id="countdown">{auto_close_delay}秒后自动关闭</div>
        </div>
    </div>

    <script>
        const BACKEND_COLORS = {backend_colors_json};
        const sessionId = "{html.escape(session_id)}" || new URLSearchParams(location.search).get('session_id') || '';
        const autoCloseDelay = {auto_close_delay};

        const contentEl = document.getElementById('content');
        const emptyState = document.getElementById('emptyState');
        const statusDot = document.getElementById('statusDot');
        const statusText = document.getElementById('statusText');
        const doneBanner = document.getElementById('doneBanner');
        const countdown = document.getElementById('countdown');

        let messageCount = 0;

        function addMessage(event) {{
            if (!event.content && !event.done) return;

            if (emptyState) {{
                emptyState.remove();
            }}

            if (event.done) {{
                handleDone();
                return;
            }}

            const msg = document.createElement('div');
            msg.className = `message ${{event.backend || 'claude'}}`;

            const header = document.createElement('div');
            header.className = 'message-header';

            const backend = document.createElement('span');
            backend.className = 'message-backend';
            backend.textContent = (BACKEND_COLORS[event.backend]?.name || event.backend || 'Claude').toUpperCase();
            header.appendChild(backend);

            if (event.content_type) {{
                const type = document.createElement('span');
                type.className = 'message-type';
                type.textContent = event.content_type;
                header.appendChild(type);
            }}

            const time = document.createElement('span');
            time.textContent = new Date(event.timestamp).toLocaleTimeString();
            header.appendChild(time);

            msg.appendChild(header);

            const content = document.createElement('div');
            content.className = 'message-content';
            content.textContent = event.content;
            msg.appendChild(content);

            contentEl.appendChild(msg);
            contentEl.scrollTop = contentEl.scrollHeight;
            messageCount++;
        }}

        function handleDone() {{
            statusDot.classList.add('done');
            statusText.textContent = '已完成';
            doneBanner.classList.add('show');

            let remaining = autoCloseDelay;
            countdown.textContent = `${{remaining}}秒后自动关闭`;

            const timer = setInterval(() => {{
                remaining--;
                if (remaining > 0) {{
                    countdown.textContent = `${{remaining}}秒后自动关闭`;
                }} else {{
                    clearInterval(timer);
                    countdown.textContent = '正在关闭...';

                    // Auto-close window
                    window.close();

                    // If window.close() fails (user-opened window), show message
                    setTimeout(() => {{
                        countdown.textContent = '可以关闭此页面';
                    }}, 100);
                }}
            }}, 1000);
        }}

        function connect() {{
            if (!sessionId) {{
                statusText.textContent = '无会话ID';
                return;
            }}

            const eventSource = new EventSource(`/api/stream/${{sessionId}}`);

            eventSource.onopen = () => {{
                statusText.textContent = '已连接';
            }};

            eventSource.onmessage = (e) => {{
                try {{
                    const event = JSON.parse(e.data);
                    addMessage(event);
                }} catch (err) {{
                    console.error('Parse error:', err);
                }}
            }};

            eventSource.onerror = (e) => {{
                statusDot.classList.add('done');
                statusText.textContent = '连接断开';
                eventSource.close();
            }};
        }}

        connect();
    </script>
</body>
</html>'''


# Global server instance
_server: UIServer | None = None
_server_lock = threading.Lock()


def start_server(port: int = 0, auto_open: bool = True, auto_close_delay: int = 3) -> UIServer:
    """Start the global UI server."""
    global _server
    with _server_lock:
        if _server is None:
            _server = UIServer(port=port, auto_open=auto_open, auto_close_delay=auto_close_delay)
            _server.start()
        return _server


def stop_server() -> None:
    """Stop the global UI server."""
    global _server
    with _server_lock:
        if _server is not None:
            _server.stop()
            _server = None
