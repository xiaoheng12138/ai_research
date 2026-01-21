from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from .model_bridge import ModelBridge
from .session_store import SessionStore


def _is_safe_relpath(p: Path) -> bool:
    s = str(p).replace("\\", "/")
    if p.is_absolute() or p.drive or s.startswith(("/", "\\", "//")):
        return False
    if any(part == ".." for part in p.parts):
        return False
    return True


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=True, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="rwa-bridge")
    parser.add_argument("--request", required=True, help="Relative path to request.json")
    parser.add_argument("--out", required=True, help="Relative path to out.json")
    args = parser.parse_args(argv)

    request_path = Path(args.request)
    out_path = Path(args.out)
    if not _is_safe_relpath(request_path):
        raise ValueError("--request must be a safe relative path")
    if not _is_safe_relpath(out_path):
        raise ValueError("--out must be a safe relative path")

    req = _load_json(request_path)
    if not isinstance(req, dict):
        raise ValueError("request JSON must be an object")

    task_id = req.get("task_id")
    run_id = req.get("run_id")
    backend = req.get("backend")
    role = req.get("role")
    role_file = req.get("role_file")
    task = req.get("task")
    context = req.get("context") or {}
    output_format = req.get("output_format") or "json"
    trace = bool(req.get("trace", True))
    trace_level = req.get("trace_level") or "brief"
    session = req.get("session") or {"mode": "auto"}

    if not isinstance(backend, str) or not backend:
        raise ValueError("request.backend must be a non-empty string")
    if not isinstance(role, str) or not role:
        raise ValueError("request.role must be a non-empty string")
    if not isinstance(task, str) or not task:
        raise ValueError("request.task must be a non-empty string")
    if not isinstance(context, dict):
        raise ValueError("request.context must be an object")

    expected_role_file = Path(".claude/.research/prompts") / backend.lower() / f"{role}.md"
    if not isinstance(role_file, str) or not role_file:
        raise ValueError("request.role_file must be a non-empty string")
    role_file_path = Path(role_file)
    if not _is_safe_relpath(role_file_path):
        raise ValueError("request.role_file must be a safe relative path")
    if role_file_path.parts[:3] != (".claude", ".research", "prompts"):
        raise ValueError("request.role_file must be under .claude/.research/prompts/")
    if role_file_path != expected_role_file:
        raise ValueError("request.role_file does not match backend/role convention")

    mode = None
    if isinstance(session, dict):
        mode = session.get("mode")
    if mode is None:
        mode = "auto"
    if mode not in ("auto", "new"):
        raise ValueError("request.session.mode must be 'auto' or 'new'")

    store = SessionStore()
    if mode == "new":
        backend_norm = backend.strip().lower()
        if backend_norm in ("codex", "gemini"):
            store.clear_session(backend_norm)  # type: ignore[arg-type]

    bridge = ModelBridge(session_store=store)
    result = bridge.run(
        backend=backend,
        role=role,
        task=task,
        context=context,
        output_format=output_format,
        run_id=run_id,
        task_id=task_id,
        trace=trace,
        trace_level=trace_level,
    )

    out_rel = str(out_path).replace("\\", "/")
    artifact_refs = [out_rel]
    for a in result.artifact_refs:
        if isinstance(a, str) and a.strip() and a.strip() not in artifact_refs:
            artifact_refs.append(a.strip())

    out_obj: dict[str, Any] = {
        "ok": result.ok,
        "task_id": task_id,
        "run_id": run_id,
        "backend": backend,
        "role": role,
        "session_id": result.session_id,
        "output": result.output,
        "artifact_refs": artifact_refs,
    }

    _write_json(out_path, out_obj)
    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
