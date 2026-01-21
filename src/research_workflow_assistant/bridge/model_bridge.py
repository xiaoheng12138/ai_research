from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal, Mapping

from .session_store import SessionStore
from .trace_writer import TraceLevel, TracePhase, TraceWriter

Backend = Literal["codex", "gemini"]
OutputFormat = Literal["json", "markdown"]

_SESSION_ID_RE = re.compile(r"(?i)\bsession[_\s-]?id\b\s*[:=]\s*([0-9a-fA-F-]{8,})")


def _now_iso8601_utc() -> str:
    return (
        datetime.now(timezone.utc)
        .isoformat(timespec="milliseconds")
        .replace("+00:00", "Z")
    )


def _generate_run_id() -> str:
    ts = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    return f"run-{ts}-{uuid.uuid4().hex[:8]}"


def _truncate(text: str, max_chars: int) -> str:
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + f"...<truncated {len(text) - max_chars} chars>"


def _safe_preview(text: str, max_chars: int = 280) -> str:
    return _truncate(" ".join(text.strip().split()), max_chars)


def _json_dumps_compact(value: Any) -> str:
    return json.dumps(value, ensure_ascii=True, separators=(",", ":"), sort_keys=True, default=str)


def _extract_json_block(text: str) -> Any | None:
    s = text.strip()
    if (s.startswith("{") and s.endswith("}")) or (s.startswith("[") and s.endswith("]")):
        try:
            return json.loads(s)
        except json.JSONDecodeError:
            return None

    m = re.search(r"```(?:json)?\s*(\{.*?\}|\[.*?\])\s*```", text, flags=re.S | re.I)
    if m:
        try:
            return json.loads(m.group(1))
        except json.JSONDecodeError:
            return None

    first_obj = s.find("{")
    last_obj = s.rfind("}")
    if 0 <= first_obj < last_obj:
        candidate = s[first_obj : last_obj + 1]
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            pass

    first_arr = s.find("[")
    last_arr = s.rfind("]")
    if 0 <= first_arr < last_arr:
        candidate = s[first_arr : last_arr + 1]
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            pass
    return None


def _parse_jsonl_events(text: str) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    for line in text.splitlines():
        raw = line.strip()
        if not raw or not raw.startswith("{") or not raw.endswith("}"):
            continue
        try:
            obj = json.loads(raw)
        except json.JSONDecodeError:
            continue
        if isinstance(obj, dict):
            events.append(obj)
    return events


def _find_session_id(obj: Any) -> str | None:
    if isinstance(obj, str):
        m = _SESSION_ID_RE.search(obj)
        return m.group(1) if m else None
    if not isinstance(obj, dict):
        return None
    for key in ("session_id", "sessionId", "sessionID"):
        v = obj.get(key)
        if isinstance(v, str) and v:
            return v
    v = obj.get("session")
    if isinstance(v, str) and v:
        return v
    if isinstance(v, dict):
        for key in ("id", "session_id"):
            vv = v.get(key)
            if isinstance(vv, str) and vv:
                return vv
    return None


def _collect_artifacts(obj: Any) -> list[str]:
    if not isinstance(obj, dict):
        return []
    for key in ("artifact_refs", "artifacts", "artifactRefs"):
        v = obj.get(key)
        if isinstance(v, list):
            out: list[str] = []
            for item in v:
                if isinstance(item, str) and item.strip():
                    out.append(item.strip())
            return out
    return []


def _coerce_output_from_wrapper_payload(payload: Any, output_format: OutputFormat) -> Any:
    if output_format == "markdown":
        if isinstance(payload, dict) and isinstance(payload.get("output"), str):
            return payload["output"]
        if isinstance(payload, str):
            return payload
        return _json_dumps_compact(payload)

    if isinstance(payload, dict) and "output" in payload:
        return payload["output"]
    if isinstance(payload, dict):
        return payload
    if isinstance(payload, str):
        extracted = _extract_json_block(payload)
        return extracted if extracted is not None else {"raw": payload}
    return {"raw": payload}


@dataclass
class ModelOutput:
    ok: bool
    output: Any
    session_id: str | None = None
    artifact_refs: list[str] = field(default_factory=list)


class ModelBridge:
    def __init__(
        self,
        wrapper_exe: str | None = None,
        session_store: SessionStore | None = None,
        prompt_root: str | Path = ".claude/.research/prompts",
        trace_dir: str | Path = ".research/logs/traces",
    ) -> None:
        self._wrapper_exe = wrapper_exe or os.environ.get("RWA_CODEAGENT_WRAPPER", "codeagent-wrapper.exe")
        self._session_store = session_store or SessionStore()
        self._prompt_root = Path(prompt_root)
        self._trace_dir = Path(trace_dir)

    def run(
        self,
        backend: str,
        role: str,
        task: str,
        context: dict,
        output_format: str = "json",
        run_id: str | None = None,
        task_id: str | None = None,
        trace: bool = True,
        trace_level: str = "brief",
    ) -> ModelOutput:
        """Unified model invocation entrypoint (no intent recognition)."""
        backend_norm = backend.strip().lower()
        if backend_norm not in ("codex", "gemini"):
            raise ValueError(f"unsupported backend: {backend}")
        backend_lit: Backend = backend_norm  # type: ignore[assignment]

        ofmt = output_format.strip().lower()
        if ofmt not in ("json", "markdown"):
            raise ValueError(f"unsupported output_format: {output_format}")
        ofmt_lit: OutputFormat = ofmt  # type: ignore[assignment]

        tlvl = trace_level.strip().lower()
        if tlvl not in ("brief", "full"):
            raise ValueError(f"unsupported trace_level: {trace_level}")
        tlvl_lit: TraceLevel = tlvl  # type: ignore[assignment]

        run_id_eff = run_id or _generate_run_id()
        trace_writer = TraceWriter(run_id_eff, base_dir=self._trace_dir, trace_level=tlvl_lit) if trace else None

        prompt_path = self._prompt_root / backend_lit / f"{role}.md"
        role_prompt = prompt_path.read_text(encoding="utf-8")

        prompt_hash = hashlib.sha256(role_prompt.encode("utf-8", errors="replace")).hexdigest()[:12]
        files = context.get("files") if isinstance(context, dict) else None
        constraints = context.get("constraints") if isinstance(context, dict) else None
        input_summary = _truncate(
            _json_dumps_compact(
                {
                    "role_prompt": str(prompt_path).replace("\\", "/"),
                    "role_prompt_sha256_12": prompt_hash,
                    "task_preview": _safe_preview(task, 240),
                    "context_keys": sorted([str(k) for k in context.keys()]) if isinstance(context, dict) else [],
                    "files_count": len(files) if isinstance(files, list) else 0,
                    "constraints_count": len(constraints) if isinstance(constraints, list) else 0,
                    "output_format": ofmt_lit,
                }
            ),
            1800 if tlvl_lit == "brief" else 6000,
        )

        session_id_in = self._session_store.get_session(backend_lit)

        prompt_text = self._build_prompt(role_prompt=role_prompt, task=task, context=context, output_format=ofmt_lit)

        first = self._call_once(
            backend=backend_lit,
            role=role,
            task_id=task_id,
            run_id=run_id_eff,
            session_id=session_id_in,
            prompt_text=prompt_text,
            input_summary=input_summary,
            output_format=ofmt_lit,
            trace_writer=trace_writer,
        )
        if first.ok:
            if first.session_id and first.session_id != session_id_in:
                self._session_store.update_session(backend_lit, first.session_id)
            return first

        if session_id_in:
            self._session_store.clear_session(backend_lit)
            if trace_writer is not None:
                trace_writer.write_event(
                    {
                        "ts": _now_iso8601_utc(),
                        "task_id": task_id,
                        "backend": backend_lit,
                        "role": role,
                        "phase": "session.refreshed",
                        "session_id": session_id_in,
                        "content": {
                            "ok": False,
                            "output_summary": "cleared_stale_session; retry_without_session",
                        },
                        "artifacts": [],
                    }
                )

            second = self._call_once(
                backend=backend_lit,
                role=role,
                task_id=task_id,
                run_id=run_id_eff,
                session_id=None,
                prompt_text=prompt_text,
                input_summary=input_summary,
                output_format=ofmt_lit,
                trace_writer=trace_writer,
            )
            if second.ok and second.session_id:
                self._session_store.update_session(backend_lit, second.session_id)
            return second

        return first

    def _build_prompt(
        self,
        *,
        role_prompt: str,
        task: str,
        context: Mapping[str, Any],
        output_format: OutputFormat,
    ) -> str:
        # Keep the prompt deterministic and structured; do not embed large file contents here.
        ctx = json.dumps(context, ensure_ascii=False, indent=2, sort_keys=True, default=str)
        parts = [
            role_prompt.rstrip(),
            "",
            "## Task",
            task.strip(),
            "",
            "## Context (JSON)",
            ctx,
            "",
            f"## Output Format\n{output_format}",
            "",
        ]
        return "\n".join(parts)

    def _call_once(
        self,
        *,
        backend: Backend,
        role: str,
        task_id: str | None,
        run_id: str,
        session_id: str | None,
        prompt_text: str,
        input_summary: str,
        output_format: OutputFormat,
        trace_writer: TraceWriter | None,
    ) -> ModelOutput:
        if trace_writer is not None:
            trace_writer.write_event(
                {
                    "ts": _now_iso8601_utc(),
                    "task_id": task_id,
                    "backend": backend,
                    "role": role,
                    "phase": "model_call.started",
                    "session_id": session_id,
                    "content": {"input_summary": input_summary},
                    "artifacts": [],
                }
            )

        started = time.monotonic()
        try:
            proc = self._invoke_wrapper(
                backend=backend,
                role=role,
                session_id=session_id,
                output_format=output_format,
                prompt_text=prompt_text,
            )
        except Exception as e:
            duration_ms = int((time.monotonic() - started) * 1000)
            if trace_writer is not None:
                trace_writer.write_event(
                    {
                        "ts": _now_iso8601_utc(),
                        "task_id": task_id,
                        "backend": backend,
                        "role": role,
                        "phase": "model_call.failed",
                        "session_id": session_id,
                        "content": {
                            "ok": False,
                            "duration_ms": duration_ms,
                            "output_summary": _safe_preview(str(e), 400),
                        },
                        "artifacts": [],
                    }
                )
            return ModelOutput(ok=False, output={"error": str(e)}, session_id=session_id, artifact_refs=[])

        duration_ms = int((time.monotonic() - started) * 1000)
        ok, output_obj, session_id_out, artifact_refs, output_summary = self._parse_wrapper_result(
            proc=proc, output_format=output_format, fallback_session_id=session_id
        )
        phase: TracePhase = "model_call.completed" if ok else "model_call.failed"
        if trace_writer is not None:
            trace_writer.write_event(
                {
                    "ts": _now_iso8601_utc(),
                    "task_id": task_id,
                    "backend": backend,
                    "role": role,
                    "phase": phase,
                    "session_id": session_id_out,
                    "content": {
                        "ok": ok,
                        "duration_ms": duration_ms,
                        "output_summary": output_summary,
                    },
                    "artifacts": artifact_refs,
                }
            )
        return ModelOutput(ok=ok, output=output_obj, session_id=session_id_out, artifact_refs=artifact_refs)

    def _invoke_wrapper(
        self,
        *,
        backend: Backend,
        role: str,
        session_id: str | None,
        output_format: OutputFormat,
        prompt_text: str,
    ) -> subprocess.CompletedProcess[str]:
        cmd: list[str] = [
            self._wrapper_exe,
            "--backend",
            backend,
            "--role",
            role,
            "--output-format",
            output_format,
        ]
        if session_id:
            cmd.extend(["--session-id", session_id])

        timeout_s = float(os.environ.get("RWA_CODEAGENT_TIMEOUT_S", "900"))
        return subprocess.run(
            cmd,
            input=prompt_text,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout_s,
            cwd=".",
        )

    def _parse_wrapper_result(
        self,
        *,
        proc: subprocess.CompletedProcess[str],
        output_format: OutputFormat,
        fallback_session_id: str | None,
    ) -> tuple[bool, Any, str | None, list[str], str]:
        stdout = (proc.stdout or "").strip()
        stderr = (proc.stderr or "").strip()

        payload: Any | None = _extract_json_block(stdout)
        events: list[dict[str, Any]] = []
        if payload is None:
            events = _parse_jsonl_events(stdout)
            if events:
                payload = {"events": events}

        session_id = _find_session_id(payload) if payload is not None else None
        if session_id is None:
            session_id = _find_session_id(stdout) or _find_session_id(stderr) or fallback_session_id

        artifacts: list[str] = []
        if payload is not None:
            artifacts.extend(_collect_artifacts(payload))
        if events:
            for evt in events:
                artifacts.extend(_collect_artifacts(evt))

        output_obj: Any
        ok: bool
        if payload is None:
            ok = proc.returncode == 0
            output_obj = (
                stdout if output_format == "markdown" else (_extract_json_block(stdout) or {"raw": stdout})
            )
        elif isinstance(payload, dict) and "ok" in payload:
            ok_val = payload.get("ok")
            ok = bool(ok_val) and proc.returncode == 0
            output_obj = _coerce_output_from_wrapper_payload(payload, output_format)
        else:
            ok = proc.returncode == 0
            output_obj = _coerce_output_from_wrapper_payload(payload, output_format)

        if not ok and stderr:
            output_summary = _safe_preview(stderr, 800)
        else:
            if output_format == "markdown" and isinstance(output_obj, str):
                output_summary = _safe_preview(output_obj, 1200)
            else:
                try:
                    output_summary = _safe_preview(_json_dumps_compact(output_obj), 1200)
                except Exception:
                    output_summary = _safe_preview(str(output_obj), 1200)

        # Deduplicate while preserving order.
        dedup: list[str] = []
        seen: set[str] = set()
        for a in artifacts:
            k = a.strip()
            if not k or k in seen:
                continue
            seen.add(k)
            dedup.append(k)

        return ok, output_obj, session_id, dedup, output_summary
