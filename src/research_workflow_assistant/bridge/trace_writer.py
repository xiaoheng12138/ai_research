from __future__ import annotations

import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal, TypedDict

Backend = Literal["codex", "gemini"]
TraceLevel = Literal["brief", "full"]
TracePhase = Literal[
    "model_call.started",
    "model_call.completed",
    "model_call.failed",
    "session.refreshed",
]


class TraceEvent(TypedDict, total=False):
    ts: str
    run_id: str
    task_id: str | None
    backend: Backend
    role: str
    phase: TracePhase
    session_id: str | None
    content: dict[str, Any]
    artifacts: list[str]


_SECRET_REPLACEMENTS: list[tuple[re.Pattern[str], str]] = [
    (
        re.compile(r"(?i)\bauthorization\s*:\s*bearer\s+[A-Za-z0-9\-._~+/]+=*"),
        "Authorization: Bearer <redacted>",
    ),
    (re.compile(r"(?i)\bbearer\s+[A-Za-z0-9\-._~+/]+=*"), "Bearer <redacted>"),
    (
        re.compile(
            r"(?i)\b(api[_-]?key|token|secret|password|passwd)\s*[:=]\s*[^\s,'\"\]]+",
        ),
        r"\1=<redacted>",
    ),
    (re.compile(r"\bsk-[A-Za-z0-9]{20,}\b"), "sk-<redacted>"),
    (re.compile(r"\bghp_[A-Za-z0-9]{30,}\b"), "ghp_<redacted>"),
    (re.compile(r"\bAIza[0-9A-Za-z\-_]{35}\b"), "AIza<redacted>"),
    (re.compile(r"\bya29\.[0-9A-Za-z\-_]+\b"), "ya29.<redacted>"),
]

_DRIVE_PREFIX_RE = re.compile(r"^[A-Za-z]:")


def _now_iso8601_utc() -> str:
    return (
        datetime.now(timezone.utc)
        .isoformat(timespec="milliseconds")
        .replace("+00:00", "Z")
    )


def _sanitize_text(text: str) -> str:
    out = text
    for pattern, repl in _SECRET_REPLACEMENTS:
        out = pattern.sub(repl, out)
    return out


def _truncate(text: str, max_chars: int) -> str:
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + f"...<truncated {len(text) - max_chars} chars>"


def _sanitize_value(value: Any, *, max_chars: int, max_items: int, _depth: int = 0) -> Any:
    if _depth > 6:
        return "<truncated_depth>"
    if value is None:
        return None
    if isinstance(value, (bool, int, float)):
        return value
    if isinstance(value, str):
        return _truncate(_sanitize_text(value), max_chars)
    if isinstance(value, dict):
        out: dict[str, Any] = {}
        for i, (k, v) in enumerate(value.items()):
            if i >= max_items:
                out["<truncated>"] = f"<{len(value) - max_items} more keys>"
                break
            out[str(k)] = _sanitize_value(
                v, max_chars=max_chars, max_items=max_items, _depth=_depth + 1
            )
        return out
    if isinstance(value, (list, tuple)):
        out_list: list[Any] = []
        for i, item in enumerate(value):
            if i >= max_items:
                out_list.append(f"<truncated {len(value) - max_items} more items>")
                break
            out_list.append(
                _sanitize_value(
                    item, max_chars=max_chars, max_items=max_items, _depth=_depth + 1
                )
            )
        return out_list
    return _truncate(_sanitize_text(str(value)), max_chars)


def _normalize_relpath(p: str) -> str | None:
    s = p.strip().replace("\\", "/")
    if not s:
        return None
    if s.startswith(("/", "\\", "//")) or _DRIVE_PREFIX_RE.match(s):
        return "<redacted_path>"
    parts = [seg for seg in s.split("/") if seg not in ("", ".")]
    if any(seg == ".." for seg in parts):
        return "<redacted_path>"
    return "/".join(parts)


class TraceWriter:
    def __init__(
        self,
        run_id: str,
        base_dir: str | Path = ".research/logs/traces",
        trace_level: TraceLevel = "brief",
    ) -> None:
        self._run_id = run_id
        self._path = Path(base_dir) / f"{run_id}.jsonl"
        self._trace_level = trace_level
        if trace_level == "full":
            self._max_chars = 8000
            self._max_items = 200
        else:
            self._max_chars = 2000
            self._max_items = 30

    def write_event(self, event: TraceEvent) -> None:
        payload: dict[str, Any] = dict(event)
        payload["ts"] = payload.get("ts") or _now_iso8601_utc()
        payload["run_id"] = self._run_id

        if "content" not in payload or payload["content"] is None:
            payload["content"] = {}
        payload["content"] = _sanitize_value(
            payload["content"], max_chars=self._max_chars, max_items=self._max_items
        )

        artifacts_in = payload.get("artifacts") or []
        artifacts_out: list[str] = []
        for item in artifacts_in:
            norm = _normalize_relpath(str(item))
            if norm is None:
                continue
            artifacts_out.append(_truncate(_sanitize_text(norm), 512))
        payload["artifacts"] = artifacts_out

        for k in ("backend", "role", "phase", "task_id", "session_id"):
            v = payload.get(k)
            if isinstance(v, str):
                payload[k] = _truncate(_sanitize_text(v), 256)

        self._path.parent.mkdir(parents=True, exist_ok=True)
        line = json.dumps(
            payload, ensure_ascii=True, separators=(",", ":"), sort_keys=False, default=str
        )
        with self._path.open("a", encoding="utf-8", newline="\n") as f:
            f.write(line)
            f.write("\n")
            f.flush()
            os.fsync(f.fileno())
