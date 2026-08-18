"""CB-owned adapter for one bounded Codex CLI model observation."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import stat
import subprocess
import time
from pathlib import Path
from typing import Any

from constraintbox.mmm_load_gate import MmmLoadError, confirm_mmm_load

REQUEST_SCHEMA = "constraintbox.codex-cli-request.v1"
RECEIPT_SCHEMA = "constraintbox.codex-cli-receipt.v1"
SAFE_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}\Z")
SAFE_MODEL = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:/-]{0,127}\Z")
EFFORTS = {"low", "medium", "high", "xhigh", "max", "ultra"}
HIERARCHY_FIELDS = {"hierarchy_bound", "parent_id", "wave_id", "round", "depth"}
MAX_REQUEST_BYTES = 32_768
MAX_PROMPT_BYTES = 1_048_576
MAX_CAPTURE_BYTES = 16_777_216
ROLLOUT_LOOKUP_ATTEMPTS = 20
ROLLOUT_LOOKUP_DELAY_SECONDS = 0.1


class CodexCliAdapterError(ValueError):
    pass


def _hierarchy(request: dict[str, Any]) -> dict[str, Any]:
    """Validate the optional ZIP leaf lineage as one all-or-none surface."""
    present = set(request) & HIERARCHY_FIELDS
    if not present:
        return {"hierarchy_bound": False}
    if present == {"hierarchy_bound"} and request["hierarchy_bound"] is False:
        return {"hierarchy_bound": False}
    if present != HIERARCHY_FIELDS or request.get("hierarchy_bound") is not True:
        raise CodexCliAdapterError("hierarchy fields differ")
    parent_id = request.get("parent_id")
    wave_id = request.get("wave_id")
    round_index = request.get("round")
    depth = request.get("depth")
    if not isinstance(parent_id, str) or SAFE_ID.fullmatch(parent_id) is None:
        raise CodexCliAdapterError("parent_id is invalid")
    if not isinstance(wave_id, str) or SAFE_ID.fullmatch(wave_id) is None:
        raise CodexCliAdapterError("wave_id is invalid")
    if isinstance(round_index, bool) or not isinstance(round_index, int) or not 0 <= round_index <= 999:
        raise CodexCliAdapterError("round is invalid")
    if isinstance(depth, bool) or not isinstance(depth, int) or not 1 <= depth <= 8:
        raise CodexCliAdapterError("depth is invalid")
    return {
        "hierarchy_bound": True,
        "parent_id": parent_id,
        "wave_id": wave_id,
        "round": round_index,
        "depth": depth,
    }


def _sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()


def _regular(path: Path, maximum: int, label: str) -> bytes:
    descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_CLOEXEC", 0))
    try:
        info = os.fstat(descriptor)
        if not stat.S_ISREG(info.st_mode):
            raise CodexCliAdapterError(f"{label} must be a regular file")
        with os.fdopen(descriptor, "rb", closefd=True) as stream:
            descriptor = -1
            raw = stream.read(maximum + 1)
    finally:
        if descriptor >= 0:
            os.close(descriptor)
    if len(raw) > maximum:
        raise CodexCliAdapterError(f"{label} exceeds maximum size")
    return raw


def _load(path: Path) -> tuple[dict[str, Any], bytes, bytes]:
    raw = _regular(path, MAX_REQUEST_BYTES, "request")
    try:
        request = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CodexCliAdapterError(f"request is not valid JSON: {exc}") from exc
    fields = {
        "schema",
        "request_id",
        "runner_path",
        "model",
        "reasoning_effort",
        "prompt_path",
        "cwd",
        "mmm_packs",
        "mmm_sha256",
        "mmm_material_role",
    }
    if not isinstance(request, dict):
        raise CodexCliAdapterError("request fields differ")
    optional = set(request) - fields
    if optional not in (
        set(),
        {"sandbox_mode"},
        {"hierarchy_bound"},
        HIERARCHY_FIELDS,
        {"sandbox_mode", "hierarchy_bound"},
        HIERARCHY_FIELDS | {"sandbox_mode"},
    ):
        raise CodexCliAdapterError("request fields differ")
    if request["schema"] != REQUEST_SCHEMA:
        raise CodexCliAdapterError("request schema differs")
    if not isinstance(request["request_id"], str) or SAFE_ID.fullmatch(request["request_id"]) is None:
        raise CodexCliAdapterError("request_id is invalid")
    if not isinstance(request["model"], str) or SAFE_MODEL.fullmatch(request["model"]) is None:
        raise CodexCliAdapterError("model is invalid")
    if request["reasoning_effort"] not in EFFORTS:
        raise CodexCliAdapterError("reasoning_effort is invalid")
    sandbox_mode = request.get("sandbox_mode", "read-only")
    if sandbox_mode not in {"read-only", "workspace-write"}:
        raise CodexCliAdapterError("sandbox_mode is invalid")
    request["sandbox_mode"] = sandbox_mode
    _hierarchy(request)
    prompt_path = Path(request["prompt_path"]).expanduser()
    if not prompt_path.is_absolute():
        raise CodexCliAdapterError("prompt_path must be absolute")
    prompt = _regular(prompt_path, MAX_PROMPT_BYTES, "prompt")
    if not prompt:
        raise CodexCliAdapterError("prompt must be nonempty")
    return request, raw, prompt


def _executable(raw: object) -> Path:
    if not isinstance(raw, str) or not Path(raw).expanduser().is_absolute():
        raise CodexCliAdapterError("runner_path must be absolute")
    path = Path(raw).expanduser().resolve(strict=True)
    if not path.is_file() or not os.access(path, os.X_OK):
        raise CodexCliAdapterError("runner must be an executable regular file")
    return path


def _cwd(raw: object) -> Path:
    if not isinstance(raw, str) or not Path(raw).expanduser().is_absolute():
        raise CodexCliAdapterError("cwd must be absolute")
    path = Path(raw).expanduser().resolve(strict=True)
    if not path.is_dir():
        raise CodexCliAdapterError("cwd must be a directory")
    return path


def _stream_observation(stdout: bytes) -> tuple[list[str], int]:
    messages: list[str] = []
    completed_turns = 0
    for line in stdout.decode("utf-8", errors="replace").splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if event.get("type") == "item.completed":
            item = event.get("item") or {}
            if item.get("type") == "agent_message" and isinstance(item.get("text"), str):
                messages.append(item["text"])
        elif event.get("type") == "turn.completed":
            completed_turns += 1
    return messages, completed_turns


def _stream_model(stdout_text: str) -> str | None:
    for line in stdout_text.splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(event, dict):
            continue
        for key in ("model", "model_id"):
            value = event.get(key)
            if isinstance(value, str) and SAFE_MODEL.fullmatch(value):
                return value
        payload = event.get("payload")
        if isinstance(payload, dict):
            value = payload.get("model")
            if isinstance(value, str) and SAFE_MODEL.fullmatch(value):
                return value
        item = event.get("item")
        if isinstance(item, dict):
            value = item.get("model")
            if isinstance(value, str) and SAFE_MODEL.fullmatch(value):
                return value
    return None


def _codex_rollout_model(
    stdout_text: str, codex_home: Path
) -> tuple[str | None, str | None]:
    """Bind the answering model from Codex's rollout bytes.

    This deliberately lives in the adapter. Importing the helper from an
    ambient installed constraintbox package lets a current adapter execute a
    stale transitive parser when PYTHONPATH is scrubbed.
    """
    thread_id: str | None = None
    for line in stdout_text.splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(event, dict) and event.get("type") == "thread.started":
            candidate = event.get("thread_id")
            if isinstance(candidate, str) and candidate:
                thread_id = candidate
            break
    if thread_id is None:
        return None, None
    sessions_dir = codex_home / "sessions"
    if not sessions_dir.is_dir():
        return None, None
    pattern = f"**/*rollout-*-{thread_id}.jsonl"
    for rollout_file in sorted(sessions_dir.glob(pattern)):
        try:
            lines = rollout_file.read_text(encoding="utf-8").splitlines()
        except OSError:
            continue
        for line in lines:
            if '"turn_context"' not in line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue
            if not isinstance(record, dict) or record.get("type") != "turn_context":
                continue
            payload = record.get("payload")
            model = payload.get("model") if isinstance(payload, dict) else record.get("model")
            if isinstance(model, str) and model:
                return model, str(rollout_file)
    return None, None


def _write(path: Path, raw: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_bytes(raw)
    os.replace(temporary, path)


def _rollout_model_with_retry(
    stdout_text: str,
    codex_home: Path,
    *,
    attempts: int = ROLLOUT_LOOKUP_ATTEMPTS,
    delay_seconds: float = ROLLOUT_LOOKUP_DELAY_SECONDS,
) -> tuple[str | None, str | None, int]:
    for index in range(1, attempts + 1):
        model, rollout = _codex_rollout_model(stdout_text, codex_home)
        if model is not None:
            return model, rollout, index
        if index < attempts:
            time.sleep(delay_seconds)
    return None, None, attempts


def run(request_path: Path, *, response_path: Path, timeout_seconds: float = 600.0) -> dict[str, Any]:
    request, request_raw, prompt = _load(request_path)
    mmm = confirm_mmm_load(request, prompt)
    hierarchy = _hierarchy(request)
    runner = _executable(request["runner_path"])
    cwd = _cwd(request["cwd"])
    argv = [
        str(runner), "exec", "-m", request["model"],
        "-c", f'model_reasoning_effort="{request["reasoning_effort"]}"',
        "--json", "--skip-git-repo-check", "--sandbox", request["sandbox_mode"],
        "-C", str(cwd), "-",
    ]
    started = time.monotonic()
    try:
        completed = subprocess.run(
            argv, input=prompt, cwd=cwd,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            timeout=timeout_seconds, check=False,
        )
        stdout = completed.stdout[:MAX_CAPTURE_BYTES]
        stderr = completed.stderr[:MAX_CAPTURE_BYTES]
        returncode: int | None = completed.returncode
        reason = "CODEX_CLI_COMPLETED" if returncode == 0 else "HOLD_CODEX_CLI_NONZERO"
    except subprocess.TimeoutExpired as exc:
        stdout = (exc.stdout or b"")[:MAX_CAPTURE_BYTES]
        stderr = (exc.stderr or b"")[:MAX_CAPTURE_BYTES]
        returncode = None
        reason = "HOLD_CODEX_CLI_TIMEOUT"
    _write(response_path, stdout)
    messages, completed_turns = _stream_observation(stdout)
    observed_model: str | None = None
    rollout_path: str | None = None
    rollout_lookup_attempts = 0
    if returncode == 0 and stdout:
        stdout_text = stdout.decode("utf-8", errors="replace")
        try:
            observed_model, observed_rollout, rollout_lookup_attempts = _rollout_model_with_retry(
                stdout_text,
                Path(os.environ.get("CODEX_HOME", str(Path.home() / ".codex"))),
            )
            rollout_path = str(observed_rollout) if observed_rollout is not None else None
        except Exception:
            observed_model = None
            rollout_path = None
        if observed_model is None:
            observed_model = _stream_model(stdout_text)
    model_binding_confirmed = observed_model == request["model"]
    terminal_completion_confirmed = completed_turns == 1 and bool(messages and messages[-1].strip())
    if returncode == 0 and not terminal_completion_confirmed:
        reason = "HOLD_CODEX_CLI_INCOMPLETE"
    elif returncode == 0 and not model_binding_confirmed:
        reason = "HOLD_CODEX_MODEL_BINDING"
    observed = returncode == 0 and terminal_completion_confirmed and model_binding_confirmed
    final_message = messages[-1] if messages else ""
    receipt = {
        **hierarchy,
        "schema": RECEIPT_SCHEMA,
        "request_id": request["request_id"],
        "request_sha256": _sha256(request_raw),
        "prompt_sha256": _sha256(prompt),
        **mmm,
        "runner_resolved_path": str(runner),
        "runner_sha256": _sha256(runner.read_bytes()),
        "model_requested": request["model"],
        "model_observed": observed_model,
        "model_binding_confirmed": model_binding_confirmed,
        "reasoning_effort_requested": request["reasoning_effort"],
        "sandbox_mode_requested": request["sandbox_mode"],
        "agent_messages": messages,
        "agent_message_count": len(messages),
        "exactly_one_agent_message": len(messages) == 1,
        "completed_turn_count": completed_turns,
        "terminal_completion_confirmed": terminal_completion_confirmed,
        "final_agent_message_sha256": _sha256(final_message.encode()) if final_message else None,
        "rollout_path": rollout_path,
        "rollout_lookup_attempts": rollout_lookup_attempts,
        "argv": argv,
        "returncode": returncode,
        "stdout_sha256": _sha256(stdout),
        "stderr_sha256": _sha256(stderr),
        "stderr": stderr.decode("utf-8", errors="replace"),
        "response_path": str(response_path.resolve()),
        "response_nonempty": bool(stdout),
        "duration_ms": int((time.monotonic() - started) * 1000),
        "disposition": "OBSERVED" if observed else "HOLD",
        "reason_code": reason,
        "claim_ceiling": "one external model observation; no CB admission or authority",
        "promotion_allowed": False,
    }
    receipt["receipt_sha256"] = _sha256(_canonical(receipt))
    return receipt


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m constraintbox.codex_cli_adapter")
    parser.add_argument("--request", required=True, type=Path)
    parser.add_argument("--response", required=True, type=Path)
    parser.add_argument("--receipt", required=True, type=Path)
    parser.add_argument("--timeout", type=float, default=600.0)
    args = parser.parse_args(argv)
    try:
        receipt = run(args.request, response_path=args.response, timeout_seconds=args.timeout)
        code = 0 if receipt["disposition"] == "OBSERVED" else 5
    except MmmLoadError as exc:
        receipt = {
            "schema": RECEIPT_SCHEMA,
            "disposition": "REFUSED",
            "reason_code": exc.reason_code,
            "detail": str(exc),
            "promotion_allowed": False,
        }
        code = 2
    except (OSError, CodexCliAdapterError, ValueError) as exc:
        receipt = {"schema": RECEIPT_SCHEMA, "disposition": "REFUSED", "reason_code": "REFUSE_CODEX_CLI_REQUEST", "detail": str(exc), "promotion_allowed": False}
        code = 2
    rendered = json.dumps(receipt, sort_keys=True, indent=2) + "\n"
    _write(args.receipt, rendered.encode())
    print(rendered, end="")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
