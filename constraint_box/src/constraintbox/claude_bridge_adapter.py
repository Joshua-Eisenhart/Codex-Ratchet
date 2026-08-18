"""CB-owned adapter around the receipt-producing Claude bridge script."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import stat
import subprocess
from pathlib import Path
from typing import Any

from constraintbox.mmm_load_gate import MmmLoadError, confirm_mmm_load

REQUEST_SCHEMA = "constraintbox.claude-bridge-request.v1"
RECEIPT_SCHEMA = "constraintbox.claude-bridge-adapter-receipt.v1"
SAFE_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}\Z")
SAFE_MODEL = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:/-]{0,127}\Z")
EFFORTS = {"", "low", "medium", "high", "max"}
HIERARCHY_FIELDS = {"hierarchy_bound", "parent_id", "wave_id", "round", "depth"}
MAX_REQUEST_BYTES = 32_768
MAX_PROMPT_BYTES = 1_048_576
MAX_CAPTURE_BYTES = 8_388_608
MAX_MODEL_OBSERVED_ALLOWLIST = 32


class ClaudeBridgeAdapterError(ValueError):
    pass


def _hierarchy(request: dict[str, Any]) -> dict[str, Any]:
    """Validate the optional ZIP leaf lineage as one all-or-none surface."""
    present = set(request) & HIERARCHY_FIELDS
    if not present:
        return {"hierarchy_bound": False}
    if present == {"hierarchy_bound"} and request["hierarchy_bound"] is False:
        return {"hierarchy_bound": False}
    if present != HIERARCHY_FIELDS or request.get("hierarchy_bound") is not True:
        raise ClaudeBridgeAdapterError("hierarchy fields differ")
    parent_id = request.get("parent_id")
    wave_id = request.get("wave_id")
    round_index = request.get("round")
    depth = request.get("depth")
    if not isinstance(parent_id, str) or SAFE_ID.fullmatch(parent_id) is None:
        raise ClaudeBridgeAdapterError("parent_id is invalid")
    if not isinstance(wave_id, str) or SAFE_ID.fullmatch(wave_id) is None:
        raise ClaudeBridgeAdapterError("wave_id is invalid")
    if isinstance(round_index, bool) or not isinstance(round_index, int) or not 0 <= round_index <= 999:
        raise ClaudeBridgeAdapterError("round is invalid")
    if isinstance(depth, bool) or not isinstance(depth, int) or not 1 <= depth <= 8:
        raise ClaudeBridgeAdapterError("depth is invalid")
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
            raise ClaudeBridgeAdapterError(f"{label} must be a regular file")
        with os.fdopen(descriptor, "rb", closefd=True) as stream:
            descriptor = -1
            raw = stream.read(maximum + 1)
    finally:
        if descriptor >= 0:
            os.close(descriptor)
    if len(raw) > maximum:
        raise ClaudeBridgeAdapterError(f"{label} exceeds maximum size")
    return raw


def _load(path: Path) -> tuple[dict[str, Any], bytes, bytes]:
    raw = _regular(path, MAX_REQUEST_BYTES, "request")
    try:
        request = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ClaudeBridgeAdapterError(f"request is not valid JSON: {exc}") from exc
    fields = {
        "schema",
        "request_id",
        "bridge_path",
        "model",
        "effort",
        "budget_usd",
        "timeout_seconds",
        "prompt_path",
        "cwd",
        "out_dir",
        "tools",
        "mmm_packs",
        "mmm_sha256",
        "mmm_material_role",
        "model_observed_allowlist",
    }
    if not isinstance(request, dict):
        raise ClaudeBridgeAdapterError("request fields differ")
    optional = set(request) - fields
    if optional not in (set(), {"hierarchy_bound"}, HIERARCHY_FIELDS):
        raise ClaudeBridgeAdapterError("request fields differ")
    if request["schema"] != REQUEST_SCHEMA:
        raise ClaudeBridgeAdapterError("request schema differs")
    if not isinstance(request["request_id"], str) or SAFE_ID.fullmatch(request["request_id"]) is None:
        raise ClaudeBridgeAdapterError("request_id is invalid")
    if not isinstance(request["model"], str) or SAFE_MODEL.fullmatch(request["model"]) is None:
        raise ClaudeBridgeAdapterError("model is invalid")
    if "model_observed_allowlist" in request:
        _validate_model_observed_allowlist(request["model_observed_allowlist"])
    if request["effort"] not in EFFORTS:
        raise ClaudeBridgeAdapterError("effort is invalid")
    if request["tools"] not in {"", "Read,Write,Edit"}:
        raise ClaudeBridgeAdapterError("tools is invalid")
    if isinstance(request["budget_usd"], bool) or not isinstance(request["budget_usd"], (int, float)) or not 0.01 <= request["budget_usd"] <= 5:
        raise ClaudeBridgeAdapterError("budget_usd is invalid")
    if isinstance(request["timeout_seconds"], bool) or not isinstance(request["timeout_seconds"], (int, float)) or not 10 <= request["timeout_seconds"] <= 1200:
        raise ClaudeBridgeAdapterError("timeout_seconds is invalid")
    _hierarchy(request)
    prompt_path = Path(request["prompt_path"]).expanduser()
    if not prompt_path.is_absolute():
        raise ClaudeBridgeAdapterError("prompt_path must be absolute")
    prompt = _regular(prompt_path, MAX_PROMPT_BYTES, "prompt")
    if not prompt:
        raise ClaudeBridgeAdapterError("prompt must be nonempty")
    return request, raw, prompt


def _path(raw: object, *, executable: bool, directory: bool, label: str) -> Path:
    if not isinstance(raw, str) or not Path(raw).expanduser().is_absolute():
        raise ClaudeBridgeAdapterError(f"{label} must be absolute")
    path = Path(raw).expanduser().resolve(strict=not directory)
    if executable and (not path.is_file() or not os.access(path, os.R_OK)):
        raise ClaudeBridgeAdapterError(f"{label} must be a readable regular file")
    if directory and path.exists() and not path.is_dir():
        raise ClaudeBridgeAdapterError(f"{label} must be a directory")
    return path


def _write(path: Path, raw: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_bytes(raw)
    os.replace(temporary, path)


def _validate_model_observed_allowlist(raw: object) -> list[str]:
    """Validate invocation-owned exact identities for an alias route."""

    if (
        not isinstance(raw, list)
        or not raw
        or len(raw) > MAX_MODEL_OBSERVED_ALLOWLIST
    ):
        raise ClaudeBridgeAdapterError("model_observed_allowlist is invalid")
    if any(not isinstance(value, str) or SAFE_MODEL.fullmatch(value) is None for value in raw):
        raise ClaudeBridgeAdapterError("model_observed_allowlist is invalid")
    if len(raw) != len(set(raw)):
        raise ClaudeBridgeAdapterError("model_observed_allowlist is invalid")
    return list(raw)


def _identity_match(
    requested: str,
    observed: list[str],
    model_observed_allowlist: list[str] | None,
) -> tuple[bool, str, str | None]:
    """Resolve one exact observed identity from invocation-owned route data."""

    if not isinstance(observed, list) or any(
        not isinstance(value, str) or not value for value in observed
    ):
        return False, "unverified", None
    if observed == [requested]:
        return True, "exact", None
    if (
        len(observed) == 1
        and model_observed_allowlist
        and observed[0] in model_observed_allowlist
    ):
        return True, "declared_alias", "invocation.model_observed_allowlist"
    return False, "unverified", None


def _binding(
    requested: str,
    observed: list[str],
    model_observed_allowlist: list[str] | None = None,
) -> bool:
    """Compatibility boolean over the exact invocation identity contract."""

    return _identity_match(requested, observed, model_observed_allowlist)[0]


def _contained_output(raw: object, out_dir: Path) -> tuple[str | None, bytes]:
    if not isinstance(raw, str):
        return None, b""
    try:
        path = Path(raw).expanduser().resolve(strict=True)
        path.relative_to(out_dir.resolve())
    except (OSError, ValueError):
        return None, b""
    if path.is_symlink() or not path.is_file():
        return None, b""
    return str(path), _regular(path, MAX_CAPTURE_BYTES, "nested output")


def run(request_path: Path) -> dict[str, Any]:
    request, request_raw, prompt = _load(request_path)
    mmm = confirm_mmm_load(request, prompt)
    hierarchy = _hierarchy(request)
    bridge = _path(request["bridge_path"], executable=True, directory=False, label="bridge_path")
    cwd = _path(request["cwd"], executable=False, directory=True, label="cwd")
    out_dir = _path(request["out_dir"], executable=False, directory=True, label="out_dir")
    out_dir.mkdir(parents=True, exist_ok=True)
    argv = [
        os.environ.get("PYTHON", "python3"), str(bridge),
        "--model", request["model"], "--prompt-file", request["prompt_path"],
        "--budget", str(request["budget_usd"]), "--timeout-sec", str(request["timeout_seconds"]),
        "--tools", request["tools"], "--cwd", str(cwd), "--out-dir", str(out_dir), "--name", request["request_id"],
    ]
    if request["effort"]:
        argv.extend(["--effort", request["effort"]])
    completed = subprocess.run(
        argv, cwd="/tmp", stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        timeout=request["timeout_seconds"] + 30, check=False,
    )
    stdout = completed.stdout[:MAX_CAPTURE_BYTES]
    stderr = completed.stderr[:MAX_CAPTURE_BYTES]
    try:
        nested = json.loads(stdout)
    except (UnicodeDecodeError, json.JSONDecodeError):
        nested = {}
    parsed = nested.get("parsed") if isinstance(nested, dict) else {}
    observed = parsed.get("models", []) if isinstance(parsed, dict) else []
    reported_receipt_path = nested.get("receipt_path") if isinstance(nested, dict) else None
    reported_output_path = nested.get("output_path") if isinstance(nested, dict) else None
    nested_receipt_path, nested_receipt_raw = _contained_output(reported_receipt_path, out_dir)
    nested_output_path, nested_output_raw = _contained_output(reported_output_path, out_dir)
    paths_contained = (
        (reported_receipt_path is None or nested_receipt_path is not None)
        and (reported_output_path is None or nested_output_path is not None)
    )
    allowlist = request.get("model_observed_allowlist")
    model_binding_confirmed, model_identity_match_kind, alias_resolution_source = _identity_match(
        request["model"], observed, allowlist
    )
    observed_ok = completed.returncode == 0 and bool(nested_output_raw) and paths_contained and model_binding_confirmed
    if completed.returncode != 0:
        reason_code = "HOLD_CLAUDE_BRIDGE_NONZERO"
    elif not paths_contained:
        reason_code = "HOLD_CLAUDE_OUTPUT_UNCONTAINED"
    elif not model_binding_confirmed:
        reason_code = "HOLD_CLAUDE_MODEL_BINDING"
    elif not nested_output_raw:
        reason_code = "HOLD_CLAUDE_OUTPUT_MISSING"
    else:
        reason_code = "CLAUDE_BRIDGE_COMPLETED"
    receipt = {
        **hierarchy,
        "schema": RECEIPT_SCHEMA,
        "request_id": request["request_id"],
        "request_sha256": _sha256(request_raw),
        "prompt_sha256": _sha256(prompt),
        **mmm,
        "bridge_path": str(bridge),
        "bridge_sha256": _sha256(bridge.read_bytes()),
        "model_requested": request["model"],
        "models_observed": observed,
        "model_observed_values": observed,
        "model_observed_allowlist": allowlist,
        "model_binding_confirmed": model_binding_confirmed,
        "model_identity_match_kind": model_identity_match_kind,
        "model_match_kind": model_identity_match_kind,
        "alias_resolution_source": alias_resolution_source,
        "tools_requested": request["tools"],
        "returncode": completed.returncode,
        "stdout_sha256": _sha256(stdout),
        "stderr_sha256": _sha256(stderr),
        "stderr": stderr.decode("utf-8", errors="replace"),
        "nested_receipt_path": nested_receipt_path,
        "nested_receipt_sha256": _sha256(nested_receipt_raw) if nested_receipt_raw else None,
        "nested_output_path": nested_output_path,
        "nested_output_sha256": _sha256(nested_output_raw) if nested_output_raw else None,
        "response_nonempty": bool(nested_output_raw),
        "total_cost_usd": parsed.get("total_cost_usd") if isinstance(parsed, dict) else None,
        "argv": argv,
        "disposition": "OBSERVED" if observed_ok else "HOLD",
        "reason_code": reason_code,
        "claim_ceiling": "one external model observation; no CB admission or authority",
        "promotion_allowed": False,
    }
    receipt["receipt_sha256"] = _sha256(_canonical(receipt))
    return receipt


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m constraintbox.claude_bridge_adapter")
    parser.add_argument("--request", required=True, type=Path)
    parser.add_argument("--receipt", required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        receipt = run(args.request)
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
    except (OSError, subprocess.TimeoutExpired, ClaudeBridgeAdapterError, ValueError) as exc:
        receipt = {"schema": RECEIPT_SCHEMA, "disposition": "REFUSED", "reason_code": "REFUSE_CLAUDE_BRIDGE_REQUEST", "detail": str(exc), "promotion_allowed": False}
        code = 2
    rendered = json.dumps(receipt, sort_keys=True, indent=2) + "\n"
    _write(args.receipt, rendered.encode())
    print(rendered, end="")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
