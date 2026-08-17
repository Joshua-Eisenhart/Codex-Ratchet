"""CB-owned, receipt-bound adapter for one bounded Grok CLI prompt call.

The vendor adapter defines argv mechanics. The requested model is supplied in
the run request and is never an admission rule or package-level preference.
"""

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
from constraintbox.hook_adapter import issue_dispatch_lease

REQUEST_SCHEMA = "constraintbox.grok-cli-request.v1"
RECEIPT_SCHEMA = "constraintbox.grok-cli-receipt.v1"
AUTH_RECEIPT_SCHEMA = "constraintbox.grok-cli-auth-receipt.v1"
MAX_REQUEST_BYTES = 32_768
MAX_PROMPT_BYTES = 1_048_576
MAX_CAPTURE_BYTES = 8_388_608
MAX_TURNS = 16
SAFE_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}\Z")
SAFE_MODEL = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:/-]{0,127}\Z")
HIERARCHY_FIELDS = {"hierarchy_bound", "parent_id", "wave_id", "round", "depth"}


class GrokCliAdapterError(ValueError):
    """Typed refusal raised before the provider process starts."""


def _hierarchy(request: dict[str, Any]) -> dict[str, Any]:
    """Validate the optional ZIP leaf lineage as one all-or-none surface."""
    present = set(request) & HIERARCHY_FIELDS
    if not present:
        return {"hierarchy_bound": False}
    if present == {"hierarchy_bound"} and request["hierarchy_bound"] is False:
        return {"hierarchy_bound": False}
    if present != HIERARCHY_FIELDS or request.get("hierarchy_bound") is not True:
        raise GrokCliAdapterError("hierarchy fields differ")
    parent_id = request.get("parent_id")
    wave_id = request.get("wave_id")
    round_index = request.get("round")
    depth = request.get("depth")
    if not isinstance(parent_id, str) or SAFE_ID.fullmatch(parent_id) is None:
        raise GrokCliAdapterError("parent_id is invalid")
    if not isinstance(wave_id, str) or SAFE_ID.fullmatch(wave_id) is None:
        raise GrokCliAdapterError("wave_id is invalid")
    if isinstance(round_index, bool) or not isinstance(round_index, int) or not 0 <= round_index <= 999:
        raise GrokCliAdapterError("round is invalid")
    if isinstance(depth, bool) or not isinstance(depth, int) or not 1 <= depth <= 8:
        raise GrokCliAdapterError("depth is invalid")
    return {
        "hierarchy_bound": True,
        "parent_id": parent_id,
        "wave_id": wave_id,
        "round": round_index,
        "depth": depth,
    }


def _canonical(value: Any) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode("utf-8")


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _read_regular(path: Path, maximum: int, label: str) -> bytes:
    descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_CLOEXEC", 0))
    try:
        metadata = os.fstat(descriptor)
        if not stat.S_ISREG(metadata.st_mode):
            raise GrokCliAdapterError(f"{label} must be a regular file")
        with os.fdopen(descriptor, "rb", closefd=True) as stream:
            descriptor = -1
            raw = stream.read(maximum + 1)
    finally:
        if descriptor >= 0:
            os.close(descriptor)
    if len(raw) > maximum:
        raise GrokCliAdapterError(f"{label} exceeds maximum size")
    return raw


def _load_request(path: Path) -> tuple[dict[str, Any], bytes, bytes]:
    raw = _read_regular(path, MAX_REQUEST_BYTES, "request")
    try:
        request = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise GrokCliAdapterError(f"request is not valid JSON: {exc}") from exc
    fields = {
        "schema",
        "request_id",
        "runner_path",
        "model",
        "prompt_path",
        "cwd",
        "max_turns",
        "permission_mode",
        "mmm_packs",
        "mmm_sha256",
    }
    if not isinstance(request, dict):
        raise GrokCliAdapterError("request fields differ")
    optional = set(request) - fields
    if optional not in (set(), {"hierarchy_bound"}, HIERARCHY_FIELDS):
        raise GrokCliAdapterError("request fields differ")
    if request["schema"] != REQUEST_SCHEMA:
        raise GrokCliAdapterError("request schema differs")
    if not isinstance(request["request_id"], str) or SAFE_ID.fullmatch(
        request["request_id"]
    ) is None:
        raise GrokCliAdapterError("request_id is invalid")
    if not isinstance(request["model"], str) or SAFE_MODEL.fullmatch(
        request["model"]
    ) is None:
        raise GrokCliAdapterError("model is invalid")
    if (
        isinstance(request["max_turns"], bool)
        or not isinstance(request["max_turns"], int)
        or not 1 <= request["max_turns"] <= MAX_TURNS
    ):
        raise GrokCliAdapterError(f"max_turns must be in 1..{MAX_TURNS}")
    if request["permission_mode"] not in {"plan", "bypassPermissions"}:
        raise GrokCliAdapterError("permission_mode is invalid")
    _hierarchy(request)
    prompt_path = Path(request["prompt_path"]).expanduser()
    if not prompt_path.is_absolute():
        raise GrokCliAdapterError("prompt_path must be absolute")
    prompt = _read_regular(prompt_path, MAX_PROMPT_BYTES, "prompt")
    if not prompt:
        raise GrokCliAdapterError("prompt must be nonempty")
    return request, raw, prompt


def _resolve_runner(raw_path: object) -> Path:
    if not isinstance(raw_path, str):
        raise GrokCliAdapterError("runner_path must be a string")
    supplied = Path(raw_path).expanduser()
    if not supplied.is_absolute():
        raise GrokCliAdapterError("runner_path must be absolute")
    try:
        resolved = supplied.resolve(strict=True)
        metadata = resolved.stat()
    except OSError as exc:
        raise GrokCliAdapterError(f"runner is unavailable: {exc}") from exc
    if not stat.S_ISREG(metadata.st_mode) or not os.access(resolved, os.X_OK):
        raise GrokCliAdapterError("runner must resolve to an executable regular file")
    return resolved


def _resolve_cwd(raw_path: object) -> Path:
    if not isinstance(raw_path, str):
        raise GrokCliAdapterError("cwd must be a string")
    path = Path(raw_path).expanduser()
    if not path.is_absolute():
        raise GrokCliAdapterError("cwd must be absolute")
    try:
        resolved = path.resolve(strict=True)
    except OSError as exc:
        raise GrokCliAdapterError(f"cwd is unavailable: {exc}") from exc
    if not resolved.is_dir():
        raise GrokCliAdapterError("cwd must be a directory")
    return resolved


def _observed_models(raw: bytes) -> list[str]:
    try:
        value = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError):
        return []
    found: set[str] = set()

    def visit(item: Any) -> None:
        if isinstance(item, dict):
            for key, child in item.items():
                if key in {"model", "model_id", "modelId"} and isinstance(child, str):
                    found.add(child)
                if key == "modelUsage" and isinstance(child, dict):
                    found.update(name for name in child if isinstance(name, str))
                visit(child)
        elif isinstance(item, list):
            for child in item:
                visit(child)

    visit(value)
    return sorted(found)


def _terminal_observation(raw: bytes) -> tuple[str | None, bytes]:
    try:
        value = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None, b""
    if not isinstance(value, dict):
        return None, b""
    stop_reason = value.get("stopReason")
    text = value.get("text")
    if not isinstance(stop_reason, str) or not isinstance(text, str):
        return None, b""
    return stop_reason, text.encode("utf-8")


def _model_binding(requested: str, observed: list[str]) -> tuple[bool, str]:
    """Bind a public Grok CLI model ID to the provider's usage label.

    The authenticated CLI currently reports an exact requested public ID in
    argv/model discovery but may suffix the usage-meter key with ``-build``.
    This provider-wide transformation is recorded explicitly; unrelated names
    remain a refusal and no model slug is embedded in CB source.
    """

    if observed == [requested]:
        return True, "exact"
    if observed == [f"{requested}-build"]:
        return True, "provider_build_usage_suffix"
    return False, "mismatch"


def _write_atomic(path: Path, raw: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_bytes(raw)
    os.replace(temporary, path)


def authenticate(
    runner_path: Path,
    *,
    mode: str,
    auth_path: Path | None = None,
    timeout_seconds: float = 600.0,
) -> dict[str, Any]:
    """Run an explicit interactive Grok OAuth flow through this CB-owned adapter.

    Authentication is maintenance of a provider route, not model execution.
    The ambient API key is deliberately removed so a depleted API-key account
    cannot silently substitute for the requested Grok subscription/OAuth route.
    Token bytes are never read into or written into the receipt.
    """

    if mode not in {"oauth", "device-code"}:
        raise GrokCliAdapterError("login mode must be oauth or device-code")
    runner = _resolve_runner(str(runner_path))
    target = auth_path or (Path.home() / ".grok" / "auth.json")
    if not target.is_absolute():
        raise GrokCliAdapterError("auth_path must be absolute")
    child_env = dict(os.environ)
    child_env.pop("XAI_API_KEY", None)
    flag = "--oauth" if mode == "oauth" else "--device-code"
    argv = [str(runner), "login", flag]
    started = time.monotonic()
    try:
        completed = subprocess.run(
            argv,
            env=child_env,
            stdin=None,
            stdout=None,
            stderr=None,
            timeout=timeout_seconds,
            check=False,
        )
        returncode: int | None = completed.returncode
        reason = "GROK_CLI_AUTH_COMPLETED" if returncode == 0 else "HOLD_GROK_CLI_AUTH_NONZERO"
    except subprocess.TimeoutExpired:
        returncode = None
        reason = "HOLD_GROK_CLI_AUTH_TIMEOUT"

    auth_present = False
    auth_owner_only = False
    try:
        metadata = target.stat()
        auth_present = stat.S_ISREG(metadata.st_mode) and metadata.st_size > 0
        auth_owner_only = stat.S_IMODE(metadata.st_mode) & 0o077 == 0
    except OSError:
        pass
    authenticated = returncode == 0 and auth_present and auth_owner_only
    if returncode == 0 and not auth_present:
        reason = "HOLD_GROK_AUTH_FILE_MISSING"
    elif returncode == 0 and auth_present and not auth_owner_only:
        reason = "HOLD_GROK_AUTH_FILE_PERMISSIONS"
    receipt = {
        "schema": AUTH_RECEIPT_SCHEMA,
        "operation": "grok_cli_authenticate",
        "mode": mode,
        "runner_resolved_path": str(runner),
        "runner_sha256": _sha256(runner.read_bytes()),
        "argv": argv,
        "ambient_api_key_withheld": True,
        "auth_file": str(target),
        "auth_file_present": auth_present,
        "auth_file_owner_only": auth_owner_only,
        "returncode": returncode,
        "duration_ms": int((time.monotonic() - started) * 1000),
        "disposition": "AUTHENTICATED" if authenticated else "HOLD",
        "reason_code": reason,
        "claim_ceiling": "local Grok CLI authentication route only; no model call or semantic claim",
        "promotion_allowed": False,
    }
    receipt["receipt_sha256"] = _sha256(_canonical(receipt))
    return receipt


def run(
    request_path: Path,
    *,
    response_path: Path,
    timeout_seconds: float = 600.0,
) -> dict[str, Any]:
    request, request_raw, prompt = _load_request(request_path)
    mmm = confirm_mmm_load(request, prompt)
    hierarchy = _hierarchy(request)
    runner = _resolve_runner(request["runner_path"])
    cwd = _resolve_cwd(request["cwd"])
    prompt_path = Path(request["prompt_path"]).expanduser().resolve(strict=True)
    argv = [
        str(runner),
        "--model",
        request["model"],
        "--prompt-file",
        str(prompt_path),
        "--output-format",
        "json",
        "--max-turns",
        str(request["max_turns"]),
        "--no-subagents",
        "--no-memory",
        "--disable-web-search",
        "--permission-mode",
        request["permission_mode"],
        "--verbatim",
    ]
    started = time.monotonic()
    with issue_dispatch_lease(request["request_id"]) as (lease_env, lease):
        child_env = os.environ.copy()
        child_env.update(lease_env)
        try:
            completed = subprocess.run(
                argv,
                cwd=cwd,
                env=child_env,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=timeout_seconds,
                check=False,
            )
            stdout = completed.stdout[:MAX_CAPTURE_BYTES]
            stderr = completed.stderr[:MAX_CAPTURE_BYTES]
            returncode: int | None = completed.returncode
            reason = "GROK_CLI_COMPLETED" if returncode == 0 else "HOLD_GROK_CLI_NONZERO"
        except subprocess.TimeoutExpired as exc:
            stdout = (exc.stdout or b"")[:MAX_CAPTURE_BYTES]
            stderr = (exc.stderr or b"")[:MAX_CAPTURE_BYTES]
            returncode = None
            reason = "HOLD_GROK_CLI_TIMEOUT"
    _write_atomic(response_path, stdout)
    observed_models = _observed_models(stdout)
    stop_reason, result_text = _terminal_observation(stdout)
    model_binding_confirmed, model_binding_basis = _model_binding(
        request["model"], observed_models
    )
    semantic_completion_confirmed = stop_reason == "end_turn" and bool(result_text.strip())
    if returncode == 0 and not semantic_completion_confirmed:
        reason = "HOLD_GROK_CLI_INCOMPLETE"
    elif returncode == 0 and not model_binding_confirmed:
        reason = "HOLD_GROK_MODEL_BINDING"
    observed = returncode == 0 and semantic_completion_confirmed and model_binding_confirmed
    receipt = {
        **hierarchy,
        "schema": RECEIPT_SCHEMA,
        "request_id": request["request_id"],
        "request_sha256": _sha256(request_raw),
        "prompt_sha256": _sha256(prompt),
        **mmm,
        "runner_resolved_path": str(runner),
        "runner_sha256": _sha256(runner.read_bytes()),
        "cwd": str(cwd),
        "model_requested": request["model"],
        "models_observed_in_output": observed_models,
        "model_binding_confirmed": model_binding_confirmed,
        "model_binding_basis": model_binding_basis,
        "stop_reason": stop_reason,
        "result_text_sha256": _sha256(result_text) if result_text else None,
        "result_text_nonempty": bool(result_text.strip()),
        "semantic_completion_confirmed": semantic_completion_confirmed,
        "max_turns": request["max_turns"],
        "permission_mode_requested": request["permission_mode"],
        "dispatch_lease": {**lease, "revoked": True},
        "argv": argv,
        "returncode": returncode,
        "stdout_sha256": _sha256(stdout),
        "stderr_sha256": _sha256(stderr),
        "stderr": stderr.decode("utf-8", errors="replace"),
        "response_path": str(response_path.resolve()),
        "response_sha256": _sha256(stdout),
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
    parser = argparse.ArgumentParser(prog="python -m constraintbox.grok_cli_adapter")
    parser.add_argument("--request", type=Path)
    parser.add_argument("--response", type=Path)
    parser.add_argument("--receipt", required=True, type=Path)
    parser.add_argument("--login", choices=("oauth", "device-code"))
    parser.add_argument("--runner", type=Path)
    parser.add_argument("--timeout", type=float, default=600.0)
    args = parser.parse_args(argv)
    try:
        if args.login is not None:
            if args.runner is None or args.request is not None or args.response is not None:
                raise GrokCliAdapterError(
                    "login requires --runner and forbids --request/--response"
                )
            receipt = authenticate(
                args.runner,
                mode=args.login,
                timeout_seconds=args.timeout,
            )
            exit_code = 0 if receipt["disposition"] == "AUTHENTICATED" else 5
        else:
            if args.request is None or args.response is None or args.runner is not None:
                raise GrokCliAdapterError(
                    "model call requires --request and --response and forbids --runner"
                )
            receipt = run(
                args.request,
                response_path=args.response,
                timeout_seconds=args.timeout,
            )
            exit_code = 0 if receipt["disposition"] == "OBSERVED" else 5
    except MmmLoadError as exc:
        receipt = {
            "schema": RECEIPT_SCHEMA,
            "disposition": "REFUSED",
            "reason_code": exc.reason_code,
            "detail": str(exc),
            "promotion_allowed": False,
        }
        exit_code = 2
    except (OSError, GrokCliAdapterError, ValueError) as exc:
        receipt = {
            "schema": RECEIPT_SCHEMA,
            "disposition": "REFUSED",
            "reason_code": "REFUSE_GROK_CLI_REQUEST",
            "detail": str(exc),
            "promotion_allowed": False,
        }
        exit_code = 2
    rendered = json.dumps(receipt, sort_keys=True, indent=2) + "\n"
    _write_atomic(args.receipt, rendered.encode("utf-8"))
    print(rendered, end="")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
