from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

Backend = Literal["codex", "gemini"]


def _now_iso8601_utc() -> str:
    return (
        datetime.now(timezone.utc)
        .isoformat(timespec="milliseconds")
        .replace("+00:00", "Z")
    )


class SessionStore:
    def __init__(self, path: str | Path = ".research/tasks/sessions.json") -> None:
        self._path = Path(path)

    def get_session(self, backend: Backend) -> str | None:
        data = self._read()
        rec = data.get(backend)
        if not isinstance(rec, dict):
            return None
        session_id = rec.get("session_id")
        if isinstance(session_id, str) and session_id:
            return session_id
        return None

    def update_session(self, backend: Backend, session_id: str) -> None:
        if not isinstance(session_id, str) or not session_id:
            return
        data = self._read()
        data[backend] = {"session_id": session_id, "updated_at": _now_iso8601_utc()}
        self._write(data)

    def clear_session(self, backend: Backend) -> None:
        data = self._read()
        if backend not in data:
            return
        data.pop(backend, None)
        self._write(data)

    def _read(self) -> dict[str, Any]:
        try:
            raw = self._path.read_text(encoding="utf-8")
        except FileNotFoundError:
            return {}
        if not raw.strip():
            return {}
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            return {}
        return data if isinstance(data, dict) else {}

    def _write(self, data: dict[str, Any]) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self._path.with_suffix(self._path.suffix + ".tmp")
        tmp.write_text(
            json.dumps(data, ensure_ascii=True, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        os.replace(tmp, self._path)
