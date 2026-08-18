# Specialist object F — current source r4

Audit provider-response ZIP output and premortem ZIP candidate. Find response extraction, exact invocation-owned model identity, failure retention, retry, MMM/skill delivery claims, ancestry, and advisory-as-gate failures.

Use exact source bytes below. Passing tests is not admission. Return bounded corrections and finite falsifiers; preserve unknowns and disagreements.

===== FILE constraint_box/src/constraintbox/claude_bridge_adapter.py sha256=2ee3fcc2c01001a144e5db677ee81af338860d6232f87726812c5d47bf0f222b bytes=14266 =====
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


===== FILE constraint_box/tests/test_claude_bridge_adapter.py sha256=60d04c35faf70ec96d15592bf88112006e5f8b19905eb193dc4d87da28af4fc9 bytes=8292 =====
from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from constraintbox.claude_bridge_adapter import ClaudeBridgeAdapterError, REQUEST_SCHEMA, run
from constraintbox.mmm_load_gate import MmmLoadError

from test_mmm_load_gate import mmm_bind


def _bridge(path: Path) -> Path:
    path.write_text(
        """from __future__ import annotations
import argparse
import json
from pathlib import Path
p = argparse.ArgumentParser()
p.add_argument('--model'); p.add_argument('--prompt-file'); p.add_argument('--budget')
p.add_argument('--timeout-sec'); p.add_argument('--tools'); p.add_argument('--cwd')
p.add_argument('--out-dir'); p.add_argument('--name'); p.add_argument('--effort')
a = p.parse_args()
out = Path(a.out_dir); out.mkdir(parents=True, exist_ok=True)
output = out / 'output.json'; receipt = out / 'receipt.json'
output.write_text(json.dumps({'ok': True}))
receipt.write_text(json.dumps({'model': 'claude-sonnet-5'}))
print(json.dumps({'parsed': {'models': ['claude-sonnet-5'], 'total_cost_usd': 0.01}, 'output_path': str(output), 'receipt_path': str(receipt)}))
""",
        encoding="utf-8",
    )
    return path


def _request(
    tmp_path: Path,
    *,
    tools: str = "",
    hierarchy: bool = False,
    bind_mmm: bool = True,
    model_observed_allowlist: list[str] | None = ["claude-sonnet-5"],
) -> Path:
    prompt = tmp_path / "prompt.md"
    path = tmp_path / "request.json"
    request = {
                "schema": REQUEST_SCHEMA,
                "request_id": "claude-adapter-test",
                "bridge_path": str(_bridge(tmp_path / "bridge.py")),
                "model": "sonnet",
                "effort": "high",
                "budget_usd": 0.1,
                "timeout_seconds": 30,
                "prompt_path": str(prompt),
                "cwd": str(tmp_path),
                "out_dir": str(tmp_path / "out"),
                "tools": tools,
            }
    if bind_mmm:
        request.update(mmm_bind(prompt, extra="bounded prompt"))
    else:
        prompt.write_text("bounded prompt", encoding="utf-8")
    if hierarchy:
        request.update(
            {
                "hierarchy_bound": True,
                "parent_id": "child-council",
                "wave_id": "wave-1",
                "round": 1,
                "depth": 2,
            }
        )
    if model_observed_allowlist is not None:
        request["model_observed_allowlist"] = model_observed_allowlist
    path.write_text(
        json.dumps(request, sort_keys=True),
        encoding="utf-8",
    )
    return path


def test_write_tools_are_explicit_request_data(tmp_path: Path) -> None:
    receipt = run(_request(tmp_path, tools="Read,Write,Edit"))
    assert receipt["disposition"] == "OBSERVED"
    assert receipt["model_binding_confirmed"] is True
    assert receipt["models_observed"] == ["claude-sonnet-5"]
    assert receipt["model_identity_match_kind"] == "declared_alias"
    assert receipt["alias_resolution_source"] == "invocation.model_observed_allowlist"
    assert receipt["model_observed_values"] == ["claude-sonnet-5"]
    assert receipt["model_observed_allowlist"] == ["claude-sonnet-5"]
    assert receipt["tools_requested"] == "Read,Write,Edit"
    tool_index = receipt["argv"].index("--tools")
    assert receipt["argv"][tool_index + 1] == "Read,Write,Edit"


def test_zip_leaf_hierarchy_is_accepted_and_bound(tmp_path: Path) -> None:
    receipt = run(_request(tmp_path, tools="Read,Write,Edit", hierarchy=True))
    assert {key: receipt[key] for key in ("hierarchy_bound", "parent_id", "wave_id", "round", "depth")} == {
        "hierarchy_bound": True,
        "parent_id": "child-council",
        "wave_id": "wave-1",
        "round": 1,
        "depth": 2,
    }


def test_unbounded_tool_string_is_refused(tmp_path: Path) -> None:
    request = _request(tmp_path)
    body = json.loads(request.read_text(encoding="utf-8"))
    body["tools"] = "Bash,WebSearch"
    request.write_text(json.dumps(body), encoding="utf-8")
    with pytest.raises(ClaudeBridgeAdapterError, match="tools is invalid"):
        run(request)


def test_output_outside_declared_directory_is_hold(monkeypatch, tmp_path: Path) -> None:
    request = _request(tmp_path)
    outside = tmp_path / "outside.md"
    outside.write_text("do not ingest\n", encoding="utf-8")
    stdout = json.dumps(
        {
            "parsed": {"models": ["claude-sonnet-5"]},
            "output_path": str(outside),
            "receipt_path": str(outside),
        }
    ).encode()
    monkeypatch.setattr(
        "constraintbox.claude_bridge_adapter.subprocess.run",
        lambda *args, **kwargs: SimpleNamespace(returncode=0, stdout=stdout, stderr=b""),
    )
    receipt = run(request)
    assert receipt["disposition"] == "HOLD"
    assert receipt["reason_code"] == "HOLD_CLAUDE_OUTPUT_UNCONTAINED"
    assert receipt["nested_output_sha256"] is None


def test_unbound_model_is_hold(monkeypatch, tmp_path: Path) -> None:
    request = _request(tmp_path)
    out_dir = tmp_path / "out"
    out_dir.mkdir(exist_ok=True)
    output = out_dir / "result.md"
    output.write_text("bounded result\n", encoding="utf-8")
    stdout = json.dumps(
        {"parsed": {"models": ["claude-haiku-4-5"]}, "output_path": str(output)}
    ).encode()
    monkeypatch.setattr(
        "constraintbox.claude_bridge_adapter.subprocess.run",
        lambda *args, **kwargs: SimpleNamespace(returncode=0, stdout=stdout, stderr=b""),
    )
    receipt = run(request)
    assert receipt["disposition"] == "HOLD"
    assert receipt["reason_code"] == "HOLD_CLAUDE_MODEL_BINDING"
    assert receipt["model_binding_confirmed"] is False


def test_alias_without_allowlist_is_hold(monkeypatch, tmp_path: Path) -> None:
    request = _request(tmp_path, model_observed_allowlist=None)
    out_dir = tmp_path / "out"
    out_dir.mkdir(exist_ok=True)
    output = out_dir / "result.md"
    output.write_text("bounded result\n", encoding="utf-8")
    stdout = json.dumps(
        {"parsed": {"models": ["claude-sonnet-5"]}, "output_path": str(output)}
    ).encode()
    monkeypatch.setattr(
        "constraintbox.claude_bridge_adapter.subprocess.run",
        lambda *args, **kwargs: SimpleNamespace(returncode=0, stdout=stdout, stderr=b""),
    )
    receipt = run(request)
    assert receipt["disposition"] == "HOLD"
    assert receipt["reason_code"] == "HOLD_CLAUDE_MODEL_BINDING"
    assert receipt["model_identity_match_kind"] == "unverified"


def test_exact_requested_model_does_not_need_allowlist(tmp_path: Path) -> None:
    request = _request(tmp_path, model_observed_allowlist=None)
    body = json.loads(request.read_text(encoding="utf-8"))
    body["model"] = "claude-sonnet-5"
    request.write_text(json.dumps(body), encoding="utf-8")
    receipt = run(request)
    assert receipt["disposition"] == "OBSERVED"
    assert receipt["model_identity_match_kind"] == "exact"
    assert receipt["alias_resolution_source"] is None


@pytest.mark.parametrize(
    "allowlist",
    [[], ["claude-sonnet-5", "claude-sonnet-5"], ["not safe"], [{"model": "x"}]],
)
def test_model_observed_allowlist_is_strictly_validated(
    tmp_path: Path, allowlist: object
) -> None:
    request = _request(tmp_path, model_observed_allowlist=allowlist)  # type: ignore[arg-type]
    with pytest.raises(ClaudeBridgeAdapterError, match="model_observed_allowlist is invalid"):
        run(request)


def test_missing_mmm_refuses_before_spawn(tmp_path: Path, monkeypatch) -> None:
    spawned = {"called": False}

    def _boom(*_args, **_kwargs):
        spawned["called"] = True
        raise AssertionError("LLM spawn must not run without confirmed MMM load")

    monkeypatch.setattr("constraintbox.claude_bridge_adapter.subprocess.run", _boom)
    with pytest.raises(MmmLoadError) as caught:
        run(_request(tmp_path, bind_mmm=False))
    assert caught.value.reason_code == "REFUSE_MMM_LOAD_MISSING"
    assert spawned["called"] is False


def test_confirmed_mmm_is_bound_on_observed_receipt(tmp_path: Path) -> None:
    receipt = run(_request(tmp_path))
    assert receipt["disposition"] == "OBSERVED"
    assert receipt["mmm_load_confirmed"] is True
    assert receipt["mmm_packs"] == ["nominalist", "smt"]
    assert receipt["mmm_sha256"]


===== FILE constraint_box/zip_agent/src/constraintbox_zip_agent/provider_task.py sha256=9e537279a195fd679bf3642f223ab4ff8686e34806b852d85674d5ad042d5725 bytes=35968 =====
from __future__ import annotations

import math
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

from .protocol import (
    TaskSpec,
    ZipJobRefusal,
    canonical_json_bytes,
    declared_controller_src,
    materialize_controller_bound_prompt,
    sha256_bytes,
    strict_json_loads,
)

REQUEST_SCHEMA = "constraintbox.provider-zip-task-request.v1"
SOURCE_RECEIPT_SCHEMA = "constraintbox.provider-zip-task-source-receipt.v1"
PROVIDER_CALL_SCHEMA = "constraintbox.provider-call.v1"
REQUIRED_OUTPUT = "output/finding.md"
PROVIDER_EVIDENCE = "meta/provider_evidence.json"
_ADAPTER_MODULES = {
    "codex-cli": "constraintbox.codex_cli_adapter",
    "grok-cli": "constraintbox.grok_cli_adapter",
    "claude-code": "constraintbox.claude_bridge_adapter",
}
_GROK_EFFORTS = {"", "low", "medium", "high", "max"}
_SAFE_MODEL = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:/-]{0,127}\Z")
_MAX_MODEL_OBSERVED_ALLOWLIST = 32
_PROVIDER_ENV_COMMON = (
    "PATH",
    "HOME",
    "USER",
    "LOGNAME",
    "LANG",
    "LC_ALL",
    "LC_CTYPE",
    "TMPDIR",
    "TMP",
    "TEMP",
    "TERM",
    "TZ",
    "SSL_CERT_FILE",
    "SSL_CERT_DIR",
    "REQUESTS_CA_BUNDLE",
    "CURL_CA_BUNDLE",
    "CB_DISPATCH_NONCE",
    "CB_DISPATCH_NONCE_FILE",
    "CB_REQUIRE_HOST_HOOK",
    "CB_BOX_ROOT",
    "CB_CONTROLLER_SRC",
    "CB_MMM_PACKS_ROOT",
)
_PROVIDER_ENV_EXTRA = {
    "fixture-subprocess": (),
    "codex-cli": ("CODEX_HOME", "OPENAI_API_KEY"),
    "grok-cli": (),
    "claude-code": ("ANTHROPIC_API_KEY", "CLAUDE_CODE_OAUTH_TOKEN"),
}


def _text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ZipJobRefusal("REFUSE_PROVIDER_REQUEST_SCHEMA", label)
    return value


def _int(value: object, label: str, *, minimum: int, maximum: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or not minimum <= value <= maximum:
        raise ZipJobRefusal("REFUSE_PROVIDER_REQUEST_SCHEMA", label)
    return value


def _object(raw: bytes, label: str) -> dict[str, Any]:
    value = strict_json_loads(raw, label=label)
    if not isinstance(value, dict):
        raise ZipJobRefusal("REFUSE_PROVIDER_REQUEST_SCHEMA", label)
    return value


def _sha256_json(value: Any) -> str:
    return sha256_bytes(canonical_json_bytes(value))


def _validate_model_observed_allowlist(raw: object) -> list[str]:
    """Validate invocation-owned exact identities without a model roster."""

    if not isinstance(raw, list) or not raw or len(raw) > _MAX_MODEL_OBSERVED_ALLOWLIST:
        raise ZipJobRefusal("REFUSE_PROVIDER_REQUEST_SCHEMA", "model_observed_allowlist")
    if any(not isinstance(value, str) or _SAFE_MODEL.fullmatch(value) is None for value in raw):
        raise ZipJobRefusal("REFUSE_PROVIDER_REQUEST_SCHEMA", "model_observed_allowlist")
    if len(raw) != len(set(raw)):
        raise ZipJobRefusal("REFUSE_PROVIDER_REQUEST_SCHEMA", "model_observed_allowlist")
    return list(raw)


def _model_identity_contract(
    request: dict[str, Any], *, observed: str, evidence: dict[str, Any]
) -> tuple[str, str | None]:
    """Resolve exact/declared-alias identity from invocation data."""

    requested = request["model_requested"]
    allowlist = request.get("model_observed_allowlist")
    if allowlist is not None:
        allowlist = _validate_model_observed_allowlist(allowlist)
    if observed == requested:
        match_kind = "exact"
        alias_source = None
    elif allowlist is not None and observed in allowlist:
        match_kind = "declared_alias"
        alias_source = "invocation.model_observed_allowlist"
    else:
        raise ZipJobRefusal("REFUSE_PROVIDER_MODEL_MISMATCH", observed)
    if "model_observed_allowlist" in evidence:
        receipt_allowlist = evidence["model_observed_allowlist"]
        if receipt_allowlist != allowlist:
            raise ZipJobRefusal(
                "REFUSE_PROVIDER_EVIDENCE_INVALID", "model_observed_allowlist"
            )
    elif request["provider"] == "claude-code":
        # Claude receipts are produced by the owned adapter and must carry the
        # invocation contract explicitly.  Grok's current adapter predates
        # this field; provider_task still binds the contract in its own source
        # receipt after checking the exact observed value.
        raise ZipJobRefusal(
            "REFUSE_PROVIDER_EVIDENCE_INVALID", "model_observed_allowlist"
        )
    receipt_kind = evidence.get("model_identity_match_kind")
    if receipt_kind is not None and receipt_kind != match_kind:
        raise ZipJobRefusal("REFUSE_PROVIDER_EVIDENCE_INVALID", "model_identity_match_kind")
    receipt_source = evidence.get("alias_resolution_source")
    if match_kind == "declared_alias":
        if receipt_source is not None and receipt_source != alias_source:
            raise ZipJobRefusal(
                "REFUSE_PROVIDER_EVIDENCE_INVALID", "alias_resolution_source"
            )
    elif receipt_source is not None:
        raise ZipJobRefusal("REFUSE_PROVIDER_EVIDENCE_INVALID", "alias_resolution_source")
    return match_kind, alias_source


def _write_workspace(work: Path, *, agent: bytes, object_bytes: bytes, prompt: bytes) -> Path:
    (work / "AGENTS").mkdir(parents=True, exist_ok=True)
    (work / "input").mkdir(parents=True, exist_ok=True)
    (work / "output").mkdir(parents=True, exist_ok=True)
    (work / "meta").mkdir(parents=True, exist_ok=True)
    (work / "AGENTS" / "write_one.md").write_bytes(agent)
    (work / "input" / "OBJECT.md").write_bytes(object_bytes)
    prompt_path = work / "meta" / "WORKER_PROMPT.md"
    prompt_path.write_bytes(prompt)
    return prompt_path


def _provider_file(value: object, label: str, *, executable: bool) -> Path:
    """Resolve a provider runner/bridge supplied by the packet request.

    The provider adapters own the final path checks too.  This early check keeps
    the ZIP operation strict and prevents an adapter request from silently
    falling back to a PATH lookup or a different executable.
    """

    raw = _text(value, label)
    path = Path(raw).expanduser()
    if not path.is_absolute():
        raise ZipJobRefusal("REFUSE_PROVIDER_REQUEST_SCHEMA", label)
    try:
        resolved = path.resolve(strict=True)
    except OSError as exc:
        raise ZipJobRefusal("HOLD_PROVIDER_EXECUTABLE_MISSING", raw) from exc
    if not resolved.is_file():
        raise ZipJobRefusal("HOLD_PROVIDER_EXECUTABLE_MISSING", raw)
    if executable and not os.access(resolved, os.X_OK):
        raise ZipJobRefusal("HOLD_PROVIDER_EXECUTABLE_MISSING", raw)
    if not executable and not os.access(resolved, os.R_OK):
        raise ZipJobRefusal("HOLD_PROVIDER_EXECUTABLE_MISSING", raw)
    return resolved


def _adapter_path(provider: str, controller_src: object | None = None) -> Path:
    """Locate the existing CB adapter without importing or invoking a raw CLI."""

    module_name = _ADAPTER_MODULES[provider]
    controller = declared_controller_src(controller_src)
    candidate = controller / "constraintbox" / f"{module_name.rsplit('.', 1)[-1]}.py"
    if candidate.is_file():
        return candidate.resolve()
    raise ZipJobRefusal("HOLD_PROVIDER_ADAPTER_MISSING", module_name)


def _provider_options(request: dict[str, Any]) -> None:
    """Validate provider-specific optional fields before dispatch.

    The request envelope remains one schema.  Only the adapter inputs below are
    admitted for each provider; a field for another route is not silently
    ignored.
    """

    provider = request["provider"]
    common = {
        "schema",
        "run_id",
        "agent_id",
        "parent_id",
        "wave_id",
        "round_index",
        "depth",
        "preload_receipt_sha256",
        "provider",
        "route_id",
        "model_requested",
        "model_observed_allowlist",
        "expected_marker",
        "timeout_seconds",
        "controller_src",
    }
    provider_fields = {
        "fixture-subprocess": {"fixture_script"},
        "codex-cli": {"executable", "codex_home", "reasoning_effort"},
        "grok-cli": {"runner_path", "max_turns"},
        "claude-code": {"bridge_path", "budget_usd", "effort"},
    }
    if provider not in provider_fields:
        return
    allowed = common | provider_fields[provider]
    if set(request) - allowed:
        raise ZipJobRefusal("REFUSE_PROVIDER_REQUEST_SCHEMA", "provider_fields")
    if provider in _ADAPTER_MODULES:
        # The overlay is a request dependency, not an inferred sibling checkout.
        declared_controller_src(request.get("controller_src"))
    if "model_observed_allowlist" in request:
        request["model_observed_allowlist"] = _validate_model_observed_allowlist(
            request["model_observed_allowlist"]
        )
    if provider == "codex-cli":
        _provider_file(request.get("executable"), "executable", executable=True)
        codex_home = _text(request.get("codex_home"), "codex_home")
        home_path = Path(codex_home).expanduser()
        if not home_path.is_absolute() or not home_path.is_dir():
            raise ZipJobRefusal("HOLD_CODEX_HOME_UNBOUND", "codex_home")
    elif provider == "grok-cli":
        _provider_file(request.get("runner_path"), "runner_path", executable=True)
        if "max_turns" in request:
            _int(request.get("max_turns"), "max_turns", minimum=1, maximum=16)
    elif provider == "claude-code":
        _provider_file(request.get("bridge_path"), "bridge_path", executable=False)
        if "budget_usd" in request:
            budget = request.get("budget_usd")
            try:
                finite = math.isfinite(float(budget))
            except (OverflowError, TypeError, ValueError):
                finite = False
            if (
                isinstance(budget, bool)
                or not isinstance(budget, (int, float))
                or not finite
                or not 0.01 <= budget <= 5
            ):
                raise ZipJobRefusal("REFUSE_PROVIDER_REQUEST_SCHEMA", "budget_usd")
        if "effort" in request and request.get("effort") not in _GROK_EFFORTS:
            raise ZipJobRefusal("REFUSE_PROVIDER_REQUEST_SCHEMA", "effort")
        # The Claude adapter requires a ten-second lower bound.  The leaf's
        # common timeout ceiling remains 600 seconds.
        if request.get("timeout_seconds", 0) < 10:
            raise ZipJobRefusal("REFUSE_PROVIDER_REQUEST_SCHEMA", "timeout_seconds")


def _bind_adapter_mmm(work: Path, prompt_path: Path, request: dict[str, Any]) -> dict[str, Any]:
    del work
    controller_src = request.pop("controller_src", None)
    try:
        fields = materialize_controller_bound_prompt(prompt_path, prompt_path, controller_src)
    except ZipJobRefusal:
        raise
    request = dict(request)
    request["prompt_path"] = str(prompt_path)
    request["mmm_packs"] = list(fields["mmm_packs"])
    request["mmm_sha256"] = fields["mmm_sha256"]
    return request


def _provider_env(provider: str, controller_src: object | None = None) -> dict[str, str]:
    """Expose only runtime and route-specific credentials to a provider leaf."""

    names = [*_PROVIDER_ENV_COMMON, *_PROVIDER_ENV_EXTRA.get(provider, ())]
    env = {name: os.environ[name] for name in names if os.environ.get(name)}
    env["PYTHONNOUSERSITE"] = "1"
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    if controller_src is not None:
        controller = declared_controller_src(controller_src)
        env["CB_CONTROLLER_SRC"] = str(controller)
        env["PYTHONPATH"] = str(controller)
    return env


def _verify_preload(
    request: dict[str, Any],
    *,
    receipt_raw: bytes,
    prompt: bytes,
    bundle: bytes,
    task_bytes: bytes,
) -> dict[str, Any]:
    receipt = _object(receipt_raw, "inputs/preload_receipt.json")
    checksum = receipt.get("receipt_self_checksum")
    checksum_body = dict(receipt)
    checksum_body.pop("receipt_self_checksum", None)
    if checksum != _sha256_json(checksum_body):
        raise ZipJobRefusal("REFUSE_PROVIDER_PRELOAD_BINDING", "receipt_self_checksum")
    if (
        receipt.get("schema") != "constraintbox.mmm-preload.v2"
        or receipt.get("disposition") != "CONTENT_BOUND"
    ):
        raise ZipJobRefusal("REFUSE_PROVIDER_PRELOAD_BINDING", "envelope")
    if sha256_bytes(receipt_raw) != request["preload_receipt_sha256"]:
        raise ZipJobRefusal("REFUSE_PROVIDER_PRELOAD_BINDING", "receipt_sha256")
    context = {
        "run_id": request["run_id"],
        "agent_id": request["agent_id"],
        "parent_id": request.get("parent_id"),
        "wave_id": request["wave_id"],
        "round": request["round_index"],
        "depth": request["depth"],
    }
    for key, expected in context.items():
        if receipt.get(key) != expected:
            raise ZipJobRefusal("REFUSE_PROVIDER_PRELOAD_BINDING", key)
    bindings = (
        (prompt, "composed_prompt"),
        (bundle, "bundle"),
        (task_bytes, "task"),
    )
    for data, label in bindings:
        if receipt.get(f"{label}_sha256") != sha256_bytes(data):
            raise ZipJobRefusal("REFUSE_PROVIDER_PRELOAD_BINDING", f"{label}_sha256")
        expected_bytes = receipt.get(f"{label}_bytes")
        if label != "task" and expected_bytes != len(data):
            raise ZipJobRefusal("REFUSE_PROVIDER_PRELOAD_BINDING", f"{label}_bytes")
    rebuilt = b"# MMM SALIENCE PRELOAD\n" + bundle + b"\n\n# TASK\n" + task_bytes
    if rebuilt != prompt:
        raise ZipJobRefusal("REFUSE_PROVIDER_PRELOAD_BINDING", "prompt_source_binding")
    sources = receipt.get("sources")
    if not isinstance(sources, list) or not sources:
        raise ZipJobRefusal("REFUSE_PROVIDER_PRELOAD_BINDING", "sources")
    primary_ids = [row.get("primary_id") for row in sources if isinstance(row, dict)]
    if len(primary_ids) != len(sources) or len(primary_ids) != len(set(primary_ids)):
        raise ZipJobRefusal("REFUSE_PROVIDER_PRELOAD_BINDING", "source_identity")
    return receipt


def _argv(
    request: dict[str, Any], work: Path, prompt_path: Path
) -> tuple[list[str], dict[str, str], Path]:
    provider = _text(request.get("provider"), "provider")
    if provider == "fixture-subprocess":
        env = _provider_env(provider)
        script = _text(request.get("fixture_script"), "fixture_script")
        return [sys.executable, "-c", script], env, work / PROVIDER_EVIDENCE
    controller = declared_controller_src(request.get("controller_src"))
    env = _provider_env(provider, controller)
    if provider == "codex-cli":
        executable = _provider_file(request.get("executable"), "executable", executable=True)
        codex_home = Path(_text(request.get("codex_home"), "codex_home")).expanduser()
        if not codex_home.is_absolute() or not codex_home.is_dir():
            raise ZipJobRefusal("HOLD_CODEX_HOME_UNBOUND", "codex_home")
        _adapter_path(provider, controller)
        env["CODEX_HOME"] = str(codex_home.resolve())
        request_path = work / "meta" / "codex_request.json"
        response_path = work / "meta" / "codex_response.jsonl"
        receipt_path = work / PROVIDER_EVIDENCE
        adapter_request = _bind_adapter_mmm(work, prompt_path, {
            "schema": "constraintbox.codex-cli-request.v1",
            "request_id": request["route_id"],
            "runner_path": str(executable),
            "model": request["model_requested"],
            "reasoning_effort": request.get("reasoning_effort") or "max",
            "sandbox_mode": "workspace-write",
            "prompt_path": str(prompt_path),
            "cwd": str(work),
            "controller_src": str(controller),
        })
        request_path.write_bytes(canonical_json_bytes(adapter_request))
        return (
            [
                sys.executable,
                "-m",
                _ADAPTER_MODULES["codex-cli"],
                "--request",
                str(request_path),
                "--response",
                str(response_path),
                "--receipt",
                str(receipt_path),
                "--timeout",
                str(request["timeout_seconds"]),
            ],
            env,
            receipt_path,
        )
    if provider == "grok-cli":
        runner = _provider_file(request.get("runner_path"), "runner_path", executable=True)
        _adapter_path(provider, controller)
        request_path = work / "meta" / "grok_request.json"
        response_path = work / "meta" / "grok_response.json"
        receipt_path = work / PROVIDER_EVIDENCE
        adapter_request = _bind_adapter_mmm(work, prompt_path, {
            "schema": "constraintbox.grok-cli-request.v1",
            "request_id": request["route_id"],
            "runner_path": str(runner),
            "model": request["model_requested"],
            "prompt_path": str(prompt_path),
            "cwd": str(work),
            "max_turns": request.get("max_turns", 8),
            # The adapter makes this explicit in its request schema.  It is
            # not exposed as a free-form provider-task field.
            "tools": "",
            "permission_mode": "bypassPermissions",
            "controller_src": str(controller),
        })
        request_path.write_bytes(canonical_json_bytes(adapter_request))
        return (
            [
                sys.executable,
                "-m",
                _ADAPTER_MODULES["grok-cli"],
                "--request",
                str(request_path),
                "--response",
                str(response_path),
                "--receipt",
                str(receipt_path),
                "--timeout",
                str(request["timeout_seconds"]),
            ],
            env,
            receipt_path,
        )
    if provider == "claude-code":
        bridge = _provider_file(request.get("bridge_path"), "bridge_path", executable=False)
        _adapter_path(provider, controller)
        request_path = work / "meta" / "claude_request.json"
        receipt_path = work / PROVIDER_EVIDENCE
        adapter_request = _bind_adapter_mmm(work, prompt_path, {
            "schema": "constraintbox.claude-bridge-request.v1",
            "request_id": request["route_id"],
            "bridge_path": str(bridge),
            "model": request["model_requested"],
            "effort": request.get("effort", "high"),
            "budget_usd": request.get("budget_usd", 1.0),
            "timeout_seconds": request["timeout_seconds"],
            "prompt_path": str(prompt_path),
            "cwd": str(work),
            "out_dir": str(work / "meta" / "claude-output"),
            "tools": "Read,Write,Edit",
            "controller_src": str(controller),
        })
        if "model_observed_allowlist" in request:
            adapter_request["model_observed_allowlist"] = list(
                request["model_observed_allowlist"]
            )
        request_path.write_bytes(canonical_json_bytes(adapter_request))
        return (
            [
                sys.executable,
                "-m",
                _ADAPTER_MODULES["claude-code"],
                "--request",
                str(request_path),
                "--receipt",
                str(receipt_path),
            ],
            env,
            receipt_path,
        )
    raise ZipJobRefusal("REFUSE_PROVIDER_UNSUPPORTED", provider)


def _adapter_evidence(
    request: dict[str, Any], *, evidence_raw: bytes, prompt_bytes: bytes
) -> tuple[str, dict[str, Any]]:
    """Normalize one existing adapter receipt into a singular observed model."""

    provider = request["provider"]
    evidence = _object(evidence_raw, PROVIDER_EVIDENCE)
    expected_schema = {
        "grok-cli": "constraintbox.grok-cli-receipt.v1",
        "claude-code": "constraintbox.claude-bridge-adapter-receipt.v1",
    }[provider]
    if evidence.get("schema") != expected_schema:
        raise ZipJobRefusal("REFUSE_PROVIDER_EVIDENCE_INVALID", "schema")
    disposition = evidence.get("disposition")
    if disposition == "HOLD":
        raise ZipJobRefusal(
            "HOLD_PROVIDER_ADAPTER",
            str(evidence.get("reason_code") or provider),
        )
    if disposition == "REFUSED":
        raise ZipJobRefusal(
            "REFUSE_PROVIDER_ADAPTER",
            str(evidence.get("reason_code") or provider),
        )
    if disposition != "OBSERVED":
        raise ZipJobRefusal("REFUSE_PROVIDER_EVIDENCE_INVALID", "disposition")
    checksum = evidence.get("receipt_sha256")
    if not isinstance(checksum, str):
        raise ZipJobRefusal("REFUSE_PROVIDER_EVIDENCE_INVALID", "receipt_sha256")
    checksum_body = dict(evidence)
    checksum_body.pop("receipt_sha256", None)
    if checksum != _sha256_json(checksum_body):
        raise ZipJobRefusal("REFUSE_PROVIDER_EVIDENCE_INVALID", "receipt_sha256")
    if evidence.get("request_id") != request["route_id"]:
        raise ZipJobRefusal("REFUSE_PROVIDER_EVIDENCE_INVALID", "request_id")
    if evidence.get("prompt_sha256") != sha256_bytes(prompt_bytes):
        raise ZipJobRefusal("REFUSE_PROVIDER_EVIDENCE_INVALID", "prompt_sha256")
    if evidence.get("model_requested") != request["model_requested"]:
        raise ZipJobRefusal("REFUSE_PROVIDER_MODEL_MISMATCH", "requested")
    if evidence.get("model_binding_confirmed") is not True:
        raise ZipJobRefusal("REFUSE_PROVIDER_EVIDENCE_INVALID", "model_binding_confirmed")
    observed_key = (
        "models_observed_in_output" if provider == "grok-cli" else "models_observed"
    )
    observed_values = evidence.get(observed_key)
    if (
        not isinstance(observed_values, list)
        or len(observed_values) != 1
        or not isinstance(observed_values[0], str)
        or not observed_values[0]
    ):
        raise ZipJobRefusal("REFUSE_PROVIDER_EVIDENCE_INVALID", "model_observed")
    observed = observed_values[0]
    _model_identity_contract(request, observed=observed, evidence=evidence)
    return observed, evidence


def _adapter_noncompletion(evidence_path: Path, provider: str) -> None:
    """Turn an adapter HOLD/REFUSED receipt into a leaf refusal."""

    if not evidence_path.is_file() or evidence_path.stat().st_size == 0:
        return
    evidence = _object(evidence_path.read_bytes(), PROVIDER_EVIDENCE)
    if evidence.get("schema") not in {
        "constraintbox.grok-cli-receipt.v1",
        "constraintbox.claude-bridge-adapter-receipt.v1",
    }:
        return
    disposition = evidence.get("disposition")
    if disposition == "HOLD":
        raise ZipJobRefusal(
            "HOLD_PROVIDER_ADAPTER",
            str(evidence.get("reason_code") or provider),
        )
    if disposition == "REFUSED":
        raise ZipJobRefusal(
            "REFUSE_PROVIDER_ADAPTER",
            str(evidence.get("reason_code") or provider),
        )


def _observed_model(
    request: dict[str, Any], *, evidence_path: Path, prompt_bytes: bytes
) -> tuple[str, bytes]:
    if not evidence_path.is_file() or evidence_path.stat().st_size == 0:
        raise ZipJobRefusal("REFUSE_PROVIDER_EVIDENCE_MISSING", str(evidence_path.name))
    evidence_raw = evidence_path.read_bytes()
    evidence = _object(evidence_raw, PROVIDER_EVIDENCE)
    provider = request["provider"]
    if provider in _ADAPTER_MODULES:
        observed, _ = _adapter_evidence(
            request, evidence_raw=evidence_raw, prompt_bytes=prompt_bytes
        )
        return observed, evidence_raw
    if provider == "codex-cli":
        if evidence.get("schema") != "constraintbox.codex-cli-receipt.v1":
            raise ZipJobRefusal("REFUSE_PROVIDER_EVIDENCE_INVALID", "schema")
        if evidence.get("prompt_sha256") != sha256_bytes(prompt_bytes):
            raise ZipJobRefusal("REFUSE_PROVIDER_EVIDENCE_INVALID", "prompt_sha256")
        if evidence.get("terminal_completion_confirmed") is not True:
            raise ZipJobRefusal("REFUSE_PROVIDER_EVIDENCE_INVALID", "terminal_completion")
    elif provider == "fixture-subprocess":
        if evidence.get("schema") != "constraintbox.fixture-provider-evidence.v1":
            raise ZipJobRefusal("REFUSE_PROVIDER_EVIDENCE_INVALID", "schema")
    else:
        raise ZipJobRefusal("REFUSE_PROVIDER_UNSUPPORTED", provider)
    if evidence.get("disposition") != "OBSERVED":
        raise ZipJobRefusal("REFUSE_PROVIDER_EVIDENCE_INVALID", "disposition")
    if evidence.get("model_requested") != request["model_requested"]:
        raise ZipJobRefusal("REFUSE_PROVIDER_MODEL_MISMATCH", "requested")
    observed = evidence.get("model_observed")
    if not isinstance(observed, str) or not observed:
        raise ZipJobRefusal("REFUSE_PROVIDER_EVIDENCE_INVALID", "model_observed")
    if observed != request["model_requested"]:
        raise ZipJobRefusal("REFUSE_PROVIDER_MODEL_MISMATCH", observed)
    if evidence.get("model_binding_confirmed") is not True:
        raise ZipJobRefusal("REFUSE_PROVIDER_EVIDENCE_INVALID", "model_binding_confirmed")
    return observed, evidence_raw


def _build_receipts(
    *,
    request: dict[str, Any],
    prompt_bytes: bytes,
    agent_bytes: bytes,
    object_bytes: bytes,
    argv: list[str],
    returncode: int,
    stdout: str,
    stderr: str,
    finding: bytes,
    model_observed: str,
    provider_evidence: bytes,
    preload_receipt_sha256: str,
) -> tuple[bytes, bytes]:
    provider_evidence_value = _object(provider_evidence, PROVIDER_EVIDENCE)
    model_identity_match_kind, alias_resolution_source = _model_identity_contract(
        request, observed=model_observed, evidence=provider_evidence_value
    )
    response_binding = {
        "stdout_sha256": sha256_bytes(stdout.encode("utf-8")),
        "stderr_sha256": sha256_bytes(stderr.encode("utf-8")),
        "finding_sha256": sha256_bytes(finding),
        "provider_evidence_sha256": sha256_bytes(provider_evidence),
    }
    request_binding = {
        "provider": request["provider"],
        "route_id": request["route_id"],
        "model_requested": request["model_requested"],
        "model_observed_allowlist": request.get("model_observed_allowlist"),
        "prompt_sha256": sha256_bytes(prompt_bytes),
        "agent_sha256": sha256_bytes(agent_bytes),
        "object_sha256": sha256_bytes(object_bytes),
        "argv_sha256": _sha256_json(argv),
    }
    source: dict[str, Any] = {
        "schema": SOURCE_RECEIPT_SCHEMA,
        "run_id": request["run_id"],
        "agent_id": request["agent_id"],
        "provider": request["provider"],
        "route_id": request["route_id"],
        "model_requested": request["model_requested"],
        "model_observed": model_observed,
        "model_observed_values": [model_observed],
        "model_observed_allowlist": request.get("model_observed_allowlist"),
        "model_binding_confirmed": True,
        "model_identity_match_kind": model_identity_match_kind,
        "model_match_kind": model_identity_match_kind,
        "alias_resolution_source": alias_resolution_source,
        "prompt_sha256": sha256_bytes(prompt_bytes),
        "request_sha256": _sha256_json(request_binding),
        "response_sha256": _sha256_json(response_binding),
        "returncode": returncode,
        "terminal_state": "COMPLETED",
        "output_path": REQUIRED_OUTPUT,
        "output_sha256": sha256_bytes(finding),
        "stdout_sha256": response_binding["stdout_sha256"],
        "stderr_sha256": response_binding["stderr_sha256"],
        "promotion_allowed": False,
        "claim_ceiling": (
            "one provider subprocess observed inside a ZIP task; "
            "not semantic correctness or release"
        ),
    }
    source["receipt_sha256"] = _sha256_json(source)
    source_bytes = canonical_json_bytes(source)
    provider_call: dict[str, Any] = {
        "schema": PROVIDER_CALL_SCHEMA,
        "run_id": request["run_id"],
        "agent_id": request["agent_id"],
        "parent_id": request.get("parent_id"),
        "wave_id": request["wave_id"],
        "round": request["round_index"],
        "depth": request["depth"],
        "preload_receipt_sha256": preload_receipt_sha256,
        "composed_prompt_sha256": source["prompt_sha256"],
        "provider_request_id": request["route_id"],
        "provider": request["provider"],
        "route": request["route_id"],
        "model_requested": request["model_requested"],
        "model_observed": model_observed,
        "model_observed_values": [model_observed],
        "model_observed_allowlist": request.get("model_observed_allowlist"),
        "model_identity_match_kind": model_identity_match_kind,
        "model_match_kind": model_identity_match_kind,
        "alias_resolution_source": alias_resolution_source,
        "terminal_state": "COMPLETED",
        "source_receipt_sha256": sha256_bytes(source_bytes),
        "claim_ceiling": "provider-call envelope bound to one in-ZIP subprocess receipt only",
        "promotion_allowed": False,
    }
    provider_call["provider_call_sha256"] = _sha256_json(provider_call)
    return source_bytes, canonical_json_bytes(provider_call)


def run_provider_call(task: TaskSpec, workspace: dict[str, bytes]) -> dict[str, bytes]:
    if len(task.input_paths) != 7 or set(task.output_paths) != {
        REQUIRED_OUTPUT,
        "output/source_receipt.json",
        "output/provider_call.json",
    }:
        raise ZipJobRefusal("REFUSE_OPERATION_ARITY", task.task_id)
    (
        request_path,
        agent_path,
        object_path,
        preload_path,
        prompt_member,
        bundle_path,
        task_source_path,
    ) = task.input_paths
    request = _object(workspace[request_path], request_path)
    if set(request) - {
        "schema",
        "run_id",
        "agent_id",
        "parent_id",
        "wave_id",
        "round_index",
        "depth",
        "preload_receipt_sha256",
        "provider",
        "route_id",
        "model_requested",
        "model_observed_allowlist",
        "expected_marker",
        "timeout_seconds",
        "fixture_script",
        "executable",
        "codex_home",
        "reasoning_effort",
        "runner_path",
        "bridge_path",
        "max_turns",
        "budget_usd",
        "effort",
        "controller_src",
    }:
        raise ZipJobRefusal("REFUSE_PROVIDER_REQUEST_SCHEMA", "extra_fields")
    if request.get("schema") != REQUEST_SCHEMA:
        raise ZipJobRefusal("REFUSE_PROVIDER_REQUEST_SCHEMA", "schema")
    for key in (
        "run_id",
        "agent_id",
        "wave_id",
        "preload_receipt_sha256",
        "provider",
        "route_id",
        "model_requested",
    ):
        request[key] = _text(request.get(key), key)
    request["round_index"] = _int(request.get("round_index"), "round_index", minimum=0, maximum=999)
    request["depth"] = _int(request.get("depth"), "depth", minimum=0, maximum=8)
    parent_id = request.get("parent_id")
    if parent_id is not None:
        request["parent_id"] = _text(parent_id, "parent_id")
    if request["depth"] > 0 and parent_id is None:
        raise ZipJobRefusal("REFUSE_PROVIDER_REQUEST_SCHEMA", "parent_id")
    request["timeout_seconds"] = _int(
        request.get("timeout_seconds"), "timeout_seconds", minimum=1, maximum=600
    )
    _provider_options(request)
    marker = _text(request.get("expected_marker"), "expected_marker")
    prompt = workspace[prompt_member]
    _verify_preload(
        request,
        receipt_raw=workspace[preload_path],
        prompt=prompt,
        bundle=workspace[bundle_path],
        task_bytes=workspace[task_source_path],
    )
    with tempfile.TemporaryDirectory(prefix="cb-zip-provider-") as tmp:
        work = Path(tmp)
        prompt_path = _write_workspace(
            work,
            agent=workspace[agent_path],
            object_bytes=workspace[object_path],
            prompt=prompt,
        )
        argv, env, evidence_path = _argv(request, work, prompt_path)
        try:
            proc = subprocess.run(
                argv,
                cwd=str(work),
                env=env,
                text=True,
                capture_output=True,
                timeout=request["timeout_seconds"] + 5,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            raise ZipJobRefusal("REFUSE_PROVIDER_TIMEOUT", str(request["timeout_seconds"])) from exc
        if proc.returncode != 0:
            if request["provider"] in _ADAPTER_MODULES:
                _adapter_noncompletion(evidence_path, request["provider"])
            raise ZipJobRefusal("REFUSE_PROVIDER_SUBPROCESS_FAILED", str(proc.returncode))
        model_observed, provider_evidence = _observed_model(
            request,
            evidence_path=evidence_path,
            prompt_bytes=prompt_path.read_bytes(),
        )
        finding_path = work / REQUIRED_OUTPUT
        if not finding_path.is_file() or finding_path.stat().st_size == 0:
            raise ZipJobRefusal("REFUSE_PROVIDER_MISSING_OUTPUT", REQUIRED_OUTPUT)
        finding = finding_path.read_bytes()
        if marker.encode("utf-8") not in finding:
            raise ZipJobRefusal("REFUSE_PROVIDER_MARKER_MISSING", REQUIRED_OUTPUT)
        source, provider_call = _build_receipts(
            request=request,
            prompt_bytes=prompt_path.read_bytes(),
            agent_bytes=workspace[agent_path],
            object_bytes=workspace[object_path],
            argv=argv,
            returncode=proc.returncode,
            stdout=proc.stdout or "",
            stderr=proc.stderr or "",
            finding=finding,
            model_observed=model_observed,
            provider_evidence=provider_evidence,
            preload_receipt_sha256=sha256_bytes(workspace[preload_path]),
        )
        return {
            REQUIRED_OUTPUT: finding,
            "output/source_receipt.json": source,
            "output/provider_call.json": provider_call,
        }


def build_provider_call_packet(
    *,
    request: bytes,
    agent: bytes,
    object_bytes: bytes,
    preload_receipt: bytes,
    composed_prompt: bytes,
    mmm_bundle: bytes,
    task_source: bytes,
) -> bytes:
    from .failure_wave import _task
    from .protocol import build_packet

    task_path = "tasks/00_provider_call.task.json"
    files = {
        "00_RUN_ME_FIRST.md": (
            b"# Provider call ZIP task\n\n"
            b"Run exactly one provider route and bind receipts.\n"
        ),
        "inputs/provider_request.json": request,
        "AGENTS/write_one.md": agent,
        "input/OBJECT.md": object_bytes,
        "inputs/preload_receipt.json": preload_receipt,
        "inputs/composed_prompt.md": composed_prompt,
        "inputs/mmm_bundle.md": mmm_bundle,
        "inputs/task.md": task_source,
        task_path: _task(
            task_id="provider-call",
            sequence=0,
            operation="run_provider_call_v1",
            inputs=[
                "inputs/provider_request.json",
                "AGENTS/write_one.md",
                "input/OBJECT.md",
                "inputs/preload_receipt.json",
                "inputs/composed_prompt.md",
                "inputs/mmm_bundle.md",
                "inputs/task.md",
            ],
            outputs=[REQUIRED_OUTPUT, "output/source_receipt.json", "output/provider_call.json"],
        ),
    }
    return build_packet(
        {
            "schema": "constraintbox.zip_job.v1",
            "job_id": "provider-call-smoke",
            "task_execution_order": [task_path],
            "required_output_file_list": [
                REQUIRED_OUTPUT,
                "output/source_receipt.json",
                "output/provider_call.json",
            ],
            "allowed_operations": ["run_provider_call_v1"],
            "allowed_child_job_ids": [],
            "max_child_depth": 0,
            "claim_ceiling": "local_zip_execution_with_one_provider_subprocess;not_admission;not_release",
        },
        files,
    )


===== FILE constraint_box/zip_agent/tests/test_provider_task.py sha256=25860a7dced37cac19b2bbcdc93743a540ba4cdb5dfb8101ffb157756dfe6b0a bytes=21361 =====
from __future__ import annotations

import io
import json
from pathlib import Path
import zipfile

import pytest

from constraintbox_zip_agent.protocol import (
    ZipJobRefusal,
    canonical_json_bytes,
    deterministic_zip,
    sha256_bytes,
    strict_json_loads,
    validate_return_zip,
)
from constraintbox_zip_agent.provider_task import build_provider_call_packet
from constraintbox_zip_agent.runtime import execute_packet

MARKER = "ZIP_PROVIDER_CALL_LIVE"
AGENT = b"role: write_one\noutput: output/finding.md\nWrite the marker.\n"
OBJECT = b"Write one finding line.\n"
TASK_SOURCE = b"# Provider fixture task\nWrite the declared finding.\n"
MMM_BUNDLE = b"\n\n<!-- MMM voice:test:compact -->\n# Test mini MMM\n"
COMPOSED_PROMPT = b"# MMM SALIENCE PRELOAD\n" + MMM_BUNDLE + b"\n\n# TASK\n" + TASK_SOURCE
BOX_ROOT = Path(__file__).resolve().parents[2]
CONTROLLER_SRC = BOX_ROOT / "src"
if not CONTROLLER_SRC.is_dir():
    CONTROLLER_SRC = BOX_ROOT / "integrated_system" / "runtime" / "controller_src"


def _preload() -> bytes:
    receipt = {
        "schema": "constraintbox.mmm-preload.v2",
        "disposition": "CONTENT_BOUND",
        "run_id": "provider-unit",
        "agent_id": "AGENTS/write_one.md",
        "parent_id": "root",
        "wave_id": "route-smoke",
        "round": 0,
        "depth": 0,
        "bundle_sha256": sha256_bytes(MMM_BUNDLE),
        "bundle_bytes": len(MMM_BUNDLE),
        "composed_prompt_sha256": sha256_bytes(COMPOSED_PROMPT),
        "composed_prompt_bytes": len(COMPOSED_PROMPT),
        "task_sha256": sha256_bytes(TASK_SOURCE),
        "sources": [{"primary_id": "voice:test:compact"}],
    }
    receipt["receipt_self_checksum"] = sha256_bytes(canonical_json_bytes(receipt))
    return canonical_json_bytes(receipt)


def _evidence(*, observed: str = "fixture-model") -> str:
    payload = {
        "schema": "constraintbox.fixture-provider-evidence.v1",
        "disposition": "OBSERVED",
        "model_requested": "fixture-model",
        "model_observed": observed,
        "model_binding_confirmed": observed == "fixture-model",
    }
    return repr(json.dumps(payload, sort_keys=True))


def _script(body: str, *, observed: str = "fixture-model", exit_code: int = 0) -> str:
    return (
        "import json\n"
        "from pathlib import Path\n"
        "Path('output').mkdir(exist_ok=True)\n"
        "Path('meta').mkdir(exist_ok=True)\n"
        f"{body}\n"
        f"Path('meta/provider_evidence.json').write_text({_evidence(observed=observed)}, encoding='utf-8')\n"
        f"raise SystemExit({exit_code})\n"
    )


def _request(
    *,
    script: str | None = None,
    preload: bytes | None = None,
    provider: str = "fixture-subprocess",
    model_requested: str = "fixture-model",
    **provider_fields: object,
) -> bytes:
    preload_raw = _preload() if preload is None else preload
    request: dict[str, object] = {
        "schema": "constraintbox.provider-zip-task-request.v1",
        "run_id": "provider-unit",
        "agent_id": "AGENTS/write_one.md",
        "parent_id": "root",
        "wave_id": "route-smoke",
        "round_index": 0,
        "depth": 0,
        "preload_receipt_sha256": sha256_bytes(preload_raw),
        "provider": provider,
        "route_id": "fixture-local" if provider == "fixture-subprocess" else f"{provider}-local",
        "model_requested": model_requested,
        "expected_marker": MARKER,
        "timeout_seconds": 30,
    }
    if provider != "fixture-subprocess":
        # Live provider adapters are an explicit overlay dependency.  Tests
        # bind the current source tree just as a real request must.
        request["controller_src"] = str(CONTROLLER_SRC)
    if provider == "claude-code" and model_requested == "sonnet":
        request["model_observed_allowlist"] = ["claude-sonnet-5"]
    if provider == "fixture-subprocess":
        request["fixture_script"] = script or _script(
            "Path('output/finding.md').write_text('finding: ZIP_PROVIDER_CALL_LIVE\\n', encoding='utf-8')"
        )
    request.update(provider_fields)
    return json.dumps(request, sort_keys=True).encode("utf-8")


def _packet(
    *,
    script: str | None = None,
    preload: bytes | None = None,
    composed_prompt: bytes = COMPOSED_PROMPT,
    request: bytes | None = None,
) -> bytes:
    preload_raw = _preload() if preload is None else preload
    return build_provider_call_packet(
        request=request or _request(script=script, preload=preload_raw),
        agent=AGENT,
        object_bytes=OBJECT,
        preload_receipt=preload_raw,
        composed_prompt=composed_prompt,
        mmm_bundle=MMM_BUNDLE,
        task_source=TASK_SOURCE,
    )


def _grok_runner(
    path: Path,
    *,
    observed_model: str,
    stop_reason: str = "end_turn",
    exit_code: int = 0,
) -> Path:
    response = json.dumps(
        {"model": observed_model, "text": "bounded result", "stopReason": stop_reason}
    )
    path.write_text(
        "#!/bin/sh\n"
        f"printf '%s\\n' '{response}'\n"
        "mkdir -p output && printf '%s\\n' 'finding: ZIP_PROVIDER_CALL_LIVE' > output/finding.md\n"
        f"exit {exit_code}\n",
        encoding="utf-8",
    )
    path.chmod(0o700)
    return path


def _claude_bridge(path: Path, *, observed_model: str, exit_code: int = 0) -> Path:
    path.write_text(
        "import argparse, json\n"
        "from pathlib import Path\n"
        "p = argparse.ArgumentParser()\n"
        "p.add_argument('--model'); p.add_argument('--prompt-file')\n"
        "p.add_argument('--budget'); p.add_argument('--timeout-sec')\n"
        "p.add_argument('--tools'); p.add_argument('--cwd')\n"
        "p.add_argument('--out-dir'); p.add_argument('--name'); p.add_argument('--effort')\n"
        "a = p.parse_args()\n"
        "cwd = Path(a.cwd); out_dir = Path(a.out_dir)\n"
        "(cwd / 'output').mkdir(parents=True, exist_ok=True)\n"
        "out_dir.mkdir(parents=True, exist_ok=True)\n"
        "(cwd / 'output' / 'finding.md').write_text('finding: ZIP_PROVIDER_CALL_LIVE\\n', encoding='utf-8')\n"
        "output = out_dir / 'output.json'; receipt = out_dir / 'receipt.json'\n"
        "output.write_text(json.dumps({'ok': True}), encoding='utf-8')\n"
        "receipt.write_text(json.dumps({'model': "
        + repr(observed_model)
        + "}), encoding='utf-8')\n"
        "print(json.dumps({'parsed': {'models': ["
        + repr(observed_model)
        + "], 'total_cost_usd': 0.01}, 'output_path': str(output), 'receipt_path': str(receipt)}))\n"
        f"raise SystemExit({exit_code})\n",
        encoding="utf-8",
    )
    path.chmod(0o700)
    return path


def _members(return_zip: bytes) -> dict[str, bytes]:
    with zipfile.ZipFile(io.BytesIO(return_zip), "r") as archive:
        return {name: archive.read(name) for name in archive.namelist()}


def _json(return_zip: bytes, path: str) -> dict[str, object]:
    return strict_json_loads(_members(return_zip)[path], label=path)


def test_provider_call_zip_task_runs_subprocess_and_binds_receipts() -> None:
    packet = _packet()
    result = execute_packet(packet)
    validate_return_zip(
        result.return_zip_bytes,
        expected_input_sha256=result.input_packet_sha256,
        input_packet_bytes=packet,
    )
    members = _members(result.return_zip_bytes)
    assert members["output/finding.md"] == b"finding: ZIP_PROVIDER_CALL_LIVE\n"
    source = _json(result.return_zip_bytes, "output/source_receipt.json")
    call = _json(result.return_zip_bytes, "output/provider_call.json")
    assert source["terminal_state"] == "COMPLETED"
    assert source["model_observed"] == "fixture-model"
    assert source["output_sha256"] == sha256_bytes(members["output/finding.md"])
    assert call["source_receipt_sha256"] == sha256_bytes(members["output/source_receipt.json"])
    assert call["schema"] == "constraintbox.provider-call.v1"
    assert call["provider_request_id"] == "fixture-local"
    assert call["composed_prompt_sha256"] == sha256_bytes(COMPOSED_PROMPT)
    assert call["preload_receipt_sha256"] == sha256_bytes(_preload())
    assert call["terminal_state"] == "COMPLETED"
    assert call["promotion_allowed"] is False


def test_provider_call_zip_task_replays_byte_identically_for_deterministic_fixture() -> None:
    packet = _packet()
    assert execute_packet(packet).return_zip_bytes == execute_packet(packet).return_zip_bytes


def test_provider_leaf_does_not_inherit_undeclared_host_secret(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CB_TEST_HOST_SECRET", "must-not-cross-provider-boundary")
    packet = _packet(
        script=_script(
            "import os\n"
            "assert 'CB_TEST_HOST_SECRET' not in os.environ\n"
            "assert os.environ.get('PYTHONNOUSERSITE') == '1'\n"
            "Path('output/finding.md').write_text("
            "'finding: ZIP_PROVIDER_CALL_LIVE\\n', encoding='utf-8')"
        )
    )
    execute_packet(packet)


def test_nested_provider_leaf_requires_parent_identity() -> None:
    request = json.loads(_request())
    request["depth"] = 1
    request["parent_id"] = None
    packet = _packet(request=canonical_json_bytes(request))
    with pytest.raises(ZipJobRefusal) as caught:
        execute_packet(packet)
    assert caught.value.reason_code == "REFUSE_PROVIDER_REQUEST_SCHEMA"
    assert caught.value.detail == "parent_id"


def test_provider_call_zip_task_refuses_missing_output() -> None:
    packet = _packet(script=_script("pass"))
    with pytest.raises(ZipJobRefusal) as caught:
        execute_packet(packet)
    assert caught.value.reason_code == "REFUSE_PROVIDER_MISSING_OUTPUT"


def test_provider_call_zip_task_refuses_marker_missing() -> None:
    packet = _packet(
        script=_script(
            "Path('output/finding.md').write_text('finding: wrong\\n', encoding='utf-8')"
        )
    )
    with pytest.raises(ZipJobRefusal) as caught:
        execute_packet(packet)
    assert caught.value.reason_code == "REFUSE_PROVIDER_MARKER_MISSING"


def test_provider_call_zip_task_refuses_nonzero_subprocess() -> None:
    packet = _packet(script=_script("pass", exit_code=7))
    with pytest.raises(ZipJobRefusal) as caught:
        execute_packet(packet)
    assert caught.value.reason_code == "REFUSE_PROVIDER_SUBPROCESS_FAILED"


def test_provider_call_zip_task_refuses_forged_observed_model() -> None:
    packet = _packet(
        script=_script(
            "Path('output/finding.md').write_text('finding: ZIP_PROVIDER_CALL_LIVE\\n', encoding='utf-8')",
            observed="forged-model",
        )
    )
    with pytest.raises(ZipJobRefusal) as caught:
        execute_packet(packet)
    assert caught.value.reason_code == "REFUSE_PROVIDER_MODEL_MISMATCH"


def test_provider_call_zip_task_refuses_missing_model_evidence() -> None:
    packet = _packet(
        script=(
            "from pathlib import Path\n"
            "Path('output').mkdir(exist_ok=True)\n"
            "Path('output/finding.md').write_text("
            "'finding: ZIP_PROVIDER_CALL_LIVE\\n', encoding='utf-8')\n"
        )
    )
    with pytest.raises(ZipJobRefusal) as caught:
        execute_packet(packet)
    assert caught.value.reason_code == "REFUSE_PROVIDER_EVIDENCE_MISSING"


def test_provider_call_zip_task_refuses_request_supplied_observed_model() -> None:
    request = json.loads(_request())
    request["model_observed"] = "fixture-model"
    packet = _packet(request=json.dumps(request, sort_keys=True).encode())
    with pytest.raises(ZipJobRefusal) as caught:
        execute_packet(packet)
    assert caught.value.reason_code == "REFUSE_PROVIDER_REQUEST_SCHEMA"


def test_provider_call_zip_task_refuses_preload_prompt_tamper() -> None:
    packet = _packet(composed_prompt=COMPOSED_PROMPT + b"tamper")
    with pytest.raises(ZipJobRefusal) as caught:
        execute_packet(packet)
    assert caught.value.reason_code == "REFUSE_PROVIDER_PRELOAD_BINDING"


def test_provider_call_zip_task_refuses_preload_receipt_tamper() -> None:
    preload = json.loads(_preload())
    preload["agent_id"] = "forged"
    preload_raw = canonical_json_bytes(preload)
    packet = _packet(preload=preload_raw)
    with pytest.raises(ZipJobRefusal) as caught:
        execute_packet(packet)
    assert caught.value.reason_code == "REFUSE_PROVIDER_PRELOAD_BINDING"


def test_tampered_provider_receipt_return_is_refused() -> None:
    result = execute_packet(_packet())
    entries = _members(result.return_zip_bytes)
    source = json.loads(entries["output/source_receipt.json"])
    source["model_observed"] = "forged-model"
    entries["output/source_receipt.json"] = json.dumps(source, sort_keys=True).encode("utf-8")
    forged = deterministic_zip(entries)
    with pytest.raises(ZipJobRefusal) as caught:
        validate_return_zip(forged, expected_input_sha256=result.input_packet_sha256)
    assert caught.value.reason_code == "REFUSE_RETURN_DIGEST_MISMATCH"


def test_grok_adapter_receipt_is_normalized_into_provider_call(tmp_path: Path) -> None:
    runner = _grok_runner(tmp_path / "grok-runner", observed_model="grok-test")
    packet = _packet(
        request=_request(
            provider="grok-cli",
            model_requested="grok-test",
            runner_path=str(runner),
            max_turns=2,
        )
    )
    result = execute_packet(packet)
    members = _members(result.return_zip_bytes)
    source = _json(result.return_zip_bytes, "output/source_receipt.json")
    call = _json(result.return_zip_bytes, "output/provider_call.json")
    assert members["output/finding.md"] == b"finding: ZIP_PROVIDER_CALL_LIVE\n"
    assert source["provider"] == "grok-cli"
    assert source["model_requested"] == "grok-test"
    assert source["model_observed"] == "grok-test"
    assert call["provider_request_id"] == "grok-cli-local"
    assert call["model_requested"] == "grok-test"
    assert call["model_observed"] == "grok-test"
    assert call["terminal_state"] == "COMPLETED"
    assert call["source_receipt_sha256"] == sha256_bytes(members["output/source_receipt.json"])


def test_live_provider_without_declared_controller_is_held(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("CB_CONTROLLER_SRC", raising=False)
    runner = _grok_runner(tmp_path / "grok-runner", observed_model="grok-test")
    request = json.loads(
        _request(
            provider="grok-cli",
            model_requested="grok-test",
            runner_path=str(runner),
        )
    )
    request.pop("controller_src", None)
    with pytest.raises(ZipJobRefusal) as caught:
        execute_packet(_packet(request=canonical_json_bytes(request)))
    assert caught.value.reason_code == "HOLD_PROVIDER_CONTROLLER_UNBOUND"


def test_codex_route_requires_explicit_runner_and_home(tmp_path: Path) -> None:
    request = json.loads(_request(provider="codex-cli", model_requested="codex-test"))
    with pytest.raises(ZipJobRefusal) as caught:
        execute_packet(_packet(request=canonical_json_bytes(request)))
    assert caught.value.reason_code == "REFUSE_PROVIDER_REQUEST_SCHEMA"
    assert caught.value.detail == "executable"


def test_grok_adapter_model_mismatch_holds_without_return_zip(tmp_path: Path) -> None:
    runner = _grok_runner(tmp_path / "grok-runner", observed_model="other-model")
    packet = _packet(
        request=_request(
            provider="grok-cli",
            model_requested="grok-test",
            runner_path=str(runner),
        )
    )
    with pytest.raises(ZipJobRefusal) as caught:
        execute_packet(packet)
    assert caught.value.reason_code == "HOLD_PROVIDER_ADAPTER"
    assert "MODEL_BINDING" in caught.value.detail


def test_grok_adapter_hold_has_no_declared_finding(tmp_path: Path) -> None:
    runner = _grok_runner(
        tmp_path / "grok-runner",
        observed_model="grok-test",
        stop_reason="cancelled",
    )
    packet = _packet(
        request=_request(
            provider="grok-cli",
            model_requested="grok-test",
            runner_path=str(runner),
        )
    )
    with pytest.raises(ZipJobRefusal) as caught:
        execute_packet(packet)
    assert caught.value.reason_code == "HOLD_PROVIDER_ADAPTER"
    assert "INCOMPLETE" in caught.value.detail


def test_claude_adapter_receipt_is_normalized_into_provider_call(tmp_path: Path) -> None:
    bridge = _claude_bridge(tmp_path / "claude-bridge.py", observed_model="claude-sonnet-5")
    packet = _packet(
        request=_request(
            provider="claude-code",
            model_requested="sonnet",
            bridge_path=str(bridge),
            budget_usd=0.1,
            effort="high",
        )
    )
    result = execute_packet(packet)
    members = _members(result.return_zip_bytes)
    source = _json(result.return_zip_bytes, "output/source_receipt.json")
    call = _json(result.return_zip_bytes, "output/provider_call.json")
    assert members["output/finding.md"] == b"finding: ZIP_PROVIDER_CALL_LIVE\n"
    assert source["provider"] == "claude-code"
    assert source["model_requested"] == "sonnet"
    assert source["model_observed"] == "claude-sonnet-5"
    assert source["model_observed_values"] == ["claude-sonnet-5"]
    assert source["model_observed_allowlist"] == ["claude-sonnet-5"]
    assert source["model_identity_match_kind"] == "declared_alias"
    assert source["alias_resolution_source"] == "invocation.model_observed_allowlist"
    assert call["provider_request_id"] == "claude-code-local"
    assert call["model_requested"] == "sonnet"
    assert call["model_observed"] == "claude-sonnet-5"
    assert call["model_observed_allowlist"] == ["claude-sonnet-5"]
    assert call["model_identity_match_kind"] == "declared_alias"
    assert call["terminal_state"] == "COMPLETED"
    assert call["source_receipt_sha256"] == sha256_bytes(members["output/source_receipt.json"])


def test_claude_adapter_model_mismatch_holds_without_return_zip(tmp_path: Path) -> None:
    bridge = _claude_bridge(tmp_path / "claude-bridge.py", observed_model="claude-haiku-4-5")
    packet = _packet(
        request=_request(
            provider="claude-code",
            model_requested="sonnet",
            bridge_path=str(bridge),
            budget_usd=0.1,
            effort="high",
        )
    )
    with pytest.raises(ZipJobRefusal) as caught:
        execute_packet(packet)
    assert caught.value.reason_code == "HOLD_PROVIDER_ADAPTER"
    assert "MODEL_BINDING" in caught.value.detail


def test_provider_task_alias_without_allowlist_holds(tmp_path: Path) -> None:
    bridge = _claude_bridge(tmp_path / "claude-bridge.py", observed_model="claude-sonnet-5")
    request = json.loads(
        _request(
            provider="claude-code",
            model_requested="sonnet",
            bridge_path=str(bridge),
            budget_usd=0.1,
            effort="high",
        )
    )
    request.pop("model_observed_allowlist")
    with pytest.raises(ZipJobRefusal) as caught:
        execute_packet(_packet(request=canonical_json_bytes(request)))
    assert caught.value.reason_code == "HOLD_PROVIDER_ADAPTER"
    assert "MODEL_BINDING" in caught.value.detail


def test_provider_task_alias_allowlist_rejects_arbitrary_observed_id(tmp_path: Path) -> None:
    bridge = _claude_bridge(tmp_path / "claude-bridge.py", observed_model="not-sonnet-model")
    request = _request(
        provider="claude-code",
        model_requested="sonnet",
        bridge_path=str(bridge),
        budget_usd=0.1,
        effort="high",
    )
    with pytest.raises(ZipJobRefusal) as caught:
        execute_packet(_packet(request=request))
    assert caught.value.reason_code == "HOLD_PROVIDER_ADAPTER"
    assert "MODEL_BINDING" in caught.value.detail


def test_grok_alias_allowlist_is_required_and_receipted(tmp_path: Path) -> None:
    runner = _grok_runner(tmp_path / "grok-runner", observed_model="grok-test-build")
    without = _request(
        provider="grok-cli",
        model_requested="grok-test",
        runner_path=str(runner),
        max_turns=2,
    )
    with pytest.raises(ZipJobRefusal) as caught:
        execute_packet(_packet(request=without))
    assert caught.value.reason_code == "REFUSE_PROVIDER_MODEL_MISMATCH"

    with_allowlist = _request(
        provider="grok-cli",
        model_requested="grok-test",
        runner_path=str(runner),
        max_turns=2,
        model_observed_allowlist=["grok-test-build"],
    )
    result = execute_packet(_packet(request=with_allowlist))
    source = _json(result.return_zip_bytes, "output/source_receipt.json")
    assert source["model_identity_match_kind"] == "declared_alias"
    assert source["alias_resolution_source"] == "invocation.model_observed_allowlist"
    assert source["model_observed_allowlist"] == ["grok-test-build"]


def test_claude_adapter_hold_has_no_declared_finding(tmp_path: Path) -> None:
    bridge = _claude_bridge(tmp_path / "claude-bridge.py", observed_model="claude-sonnet-5", exit_code=3)
    packet = _packet(
        request=_request(
            provider="claude-code",
            model_requested="sonnet",
            bridge_path=str(bridge),
            budget_usd=0.1,
            effort="high",
        )
    )
    with pytest.raises(ZipJobRefusal) as caught:
        execute_packet(packet)
    assert caught.value.reason_code == "HOLD_PROVIDER_ADAPTER"
    assert "NONZERO" in caught.value.detail


===== FILE constraint_box/zip_agent/src/constraintbox_zip_agent/md_agent_roster.py sha256=31faebf3f8588b869d6d3b0be73d7717115fc682ebc68d8c3421892987e8218e bytes=76375 =====
from __future__ import annotations

import os
import json
import base64
import re
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

from .protocol import (
    TaskSpec,
    ZipJobRefusal,
    build_packet,
    canonical_json_bytes,
    declared_controller_src,
    materialize_controller_bound_prompt,
    sha256_bytes,
    strict_json_loads,
)

ROSTER_SCHEMA = "constraintbox.md-agent-roster.v1"
RECEIPT_SCHEMA = "constraintbox.md-agent-roster-receipt.v1"
CLAIM_CEILING = "local_zip_execution_with_declared_md_agents;not_host_hook;not_mmm_read;not_skill_exec;not_admission;not_release"
TOOL_EVIDENCE_PATH = "output/tool_evidence.json"
TOOL_PAYLOAD_PATH = "inputs/tool_payload.json"
TOOL_REQUEST_PATH = "output/tool_request.json"
TOOL_REQUEST_SCHEMA = "constraintbox.md-agent-tool-request.v1"
DEFAULT_TOOL_PAYLOAD = {
    "schema": "constraintbox.md-agent-tool-payload.v1",
    "probe": "canonicalize",
    "items": [3, 1, 2],
}
_ADAPTER_MODULES = {
    "codex-cli": "constraintbox.codex_cli_adapter",
    "grok-cli": "constraintbox.grok_cli_adapter",
    "claude-code": "constraintbox.claude_bridge_adapter",
}
_ROSTER_FIELDS = frozenset(
    {
        "schema",
        "run_id",
        "seed",
        "required_marker",
        "max_attempts",
        "timeout_seconds",
        "max_workers",
        "shared_paths",
        "agents",
    }
)
_HIERARCHY_FIELDS = frozenset({"parent_id", "wave_id", "round", "depth"})
_OUTPUT_DELIVERIES = frozenset({"workspace_file", "provider_response"})
_OUTPUT_FORMATS = frozenset({"text", "strict_json_object"})
_LIVE_PROVIDERS = frozenset(_ADAPTER_MODULES)
_MAX_PROVIDER_RESPONSE_BYTES = 16 * 1024 * 1024
_MAX_EMBEDDED_PROVIDER_INPUT_BYTES = 2 * 1024 * 1024
_MODEL_MATCH_EXACT = "exact"
_MODEL_MATCH_DECLARED_ALIAS = "declared_alias"
_MODEL_MATCH_UNVERIFIED = "unverified"
_SAFE_MODEL = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:/-]{0,127}\Z")
_MAX_MODEL_OBSERVED_ALLOWLIST = 32


def _text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ZipJobRefusal("REFUSE_MD_AGENT_ROSTER_SCHEMA", label)
    return value


def _int(value: object, label: str, *, minimum: int, maximum: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or not minimum <= value <= maximum:
        raise ZipJobRefusal("REFUSE_MD_AGENT_ROSTER_SCHEMA", label)
    return value


def _nonnegative_int(value: object, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ZipJobRefusal("REFUSE_MD_AGENT_ROSTER_SCHEMA", label)
    return value


def _hierarchy_binding(roster: dict[str, Any]) -> dict[str, Any] | None:
    """Validate and return the optional all-or-none roster hierarchy binding."""
    present = set(roster) & _HIERARCHY_FIELDS
    if not present:
        return None
    if present != _HIERARCHY_FIELDS:
        raise ZipJobRefusal("REFUSE_MD_AGENT_ROSTER_SCHEMA", "hierarchy_fields")
    if set(roster) != _ROSTER_FIELDS | _HIERARCHY_FIELDS:
        raise ZipJobRefusal("REFUSE_MD_AGENT_ROSTER_SCHEMA", "fields")

    parent_id = roster["parent_id"]
    if parent_id is not None:
        parent_id = _text(parent_id, "parent_id")
    wave_id = _text(roster["wave_id"], "wave_id")
    round_value = _nonnegative_int(roster["round"], "round")
    depth = _int(roster["depth"], "depth", minimum=0, maximum=8)
    if depth > 0 and parent_id is None:
        raise ZipJobRefusal("REFUSE_MD_AGENT_ROSTER_SCHEMA", "parent_id")
    return {
        "parent_id": parent_id,
        "wave_id": wave_id,
        "round": round_value,
        "depth": depth,
    }


def _bind_adapter_mmm(work: Path, prompt_path: Path, request: dict[str, Any]) -> dict[str, Any]:
    del work
    controller_src = request.pop("controller_src", None)
    try:
        fields = materialize_controller_bound_prompt(prompt_path, prompt_path, controller_src)
    except ZipJobRefusal:
        raise
    request = dict(request)
    request["prompt_path"] = str(prompt_path)
    request["mmm_packs"] = list(fields["mmm_packs"])
    request["mmm_sha256"] = fields["mmm_sha256"]
    request["mmm_material_role"] = fields["mmm_material_role"]
    return request


def _hierarchy_surface(binding: dict[str, Any] | None) -> dict[str, Any]:
    if binding is None:
        return {"hierarchy_bound": False}
    return {"hierarchy_bound": True, **binding}


def _object(raw: bytes, label: str) -> dict[str, Any]:
    value = strict_json_loads(raw, label=label)
    if not isinstance(value, dict):
        raise ZipJobRefusal("REFUSE_MD_AGENT_ROSTER_SCHEMA", label)
    return value


def _path_list(value: object, label: str, *, minimum: int = 0, maximum: int = 64) -> list[str]:
    if not isinstance(value, list) or not minimum <= len(value) <= maximum:
        raise ZipJobRefusal("REFUSE_MD_AGENT_ROSTER_SCHEMA", label)
    if any(not isinstance(path, str) or not path for path in value) or len(value) != len(set(value)):
        raise ZipJobRefusal("REFUSE_MD_AGENT_ROSTER_SCHEMA", label)
    return list(value)


def _model_observed_allowlist(value: object, label: str = "model_observed_allowlist") -> list[str] | None:
    """Validate invocation-owned exact observed identities, if declared."""

    if value is None:
        return None
    if (
        not isinstance(value, list)
        or not value
        or len(value) > _MAX_MODEL_OBSERVED_ALLOWLIST
        or any(not isinstance(item, str) or _SAFE_MODEL.fullmatch(item) is None for item in value)
        or len(value) != len(set(value))
    ):
        raise ZipJobRefusal("REFUSE_MD_AGENT_ROSTER_SCHEMA", label)
    return list(value)


def _attempt_receipt_summary(
    attempts: list[dict[str, Any]], *, accepted_attempt: int | None
) -> dict[str, Any]:
    """Summarize retry history without treating a refusal as semantic output.

    ``accepted_attempt`` is the one-based number of attempts consumed before
    acceptance (zero when the member exhausted its retry budget).  The full
    attempt rows remain in the roster receipt; these derived fields make the
    retry/refusal history available to parent consumers without flattening it.
    """

    refusal_reasons = [
        reason
        for attempt in attempts
        if isinstance(attempt, dict)
        for reason in [attempt.get("refusal_reason")]
        if isinstance(reason, str) and reason
    ]
    reason_counts: dict[str, int] = {}
    for reason in refusal_reasons:
        reason_counts[reason] = reason_counts.get(reason, 0) + 1
    return {
        "attempt_count": len(attempts),
        "accepted_attempt_count": accepted_attempt or 0,
        "attempts_until_acceptance": accepted_attempt,
        "accepted_attempts": 1 if accepted_attempt is not None else 0,
        "refusal_reasons": refusal_reasons,
        "attempt_refusal_reasons": refusal_reasons,
        "refusal_reason_summary": reason_counts,
        "attempt_refusal_reason_summary": reason_counts,
    }


def _output_delivery(agent: dict[str, Any]) -> str:
    """Return the per-agent delivery mode without changing the old default."""

    value = agent.get("output_delivery", "workspace_file")
    if not isinstance(value, str) or value not in _OUTPUT_DELIVERIES:
        raise ZipJobRefusal("REFUSE_MD_AGENT_OUTPUT_DELIVERY", "output_delivery")
    if value == "provider_response" and agent.get("provider") not in _LIVE_PROVIDERS:
        raise ZipJobRefusal("REFUSE_MD_AGENT_OUTPUT_DELIVERY", "provider_response")
    return value


def _output_format(agent: dict[str, Any]) -> str:
    """Return the deterministic member-output shape required by the roster.

    Existing workspace-file and provider-response callers default to text so
    the roster remains backwards-compatible.  A candidate that consumes a
    structured provider response declares ``strict_json_object`` explicitly;
    the member gate then checks the bytes before returning an accepted row.
    """

    value = agent.get("output_format", "text")
    if not isinstance(value, str) or value not in _OUTPUT_FORMATS:
        raise ZipJobRefusal("REFUSE_MD_AGENT_OUTPUT_FORMAT", "output_format")
    return value


def _embedded_provider_inputs(
    workspace: dict[str, bytes], ordered_paths: list[str]
) -> str:
    """Render only declared ZIP inputs into one bounded provider prompt."""

    total = sum(len(workspace[path]) for path in ordered_paths)
    if total > _MAX_EMBEDDED_PROVIDER_INPUT_BYTES:
        raise ZipJobRefusal("REFUSE_MD_AGENT_PROVIDER_PROMPT_SIZE", str(total))
    blocks: list[str] = ["BEGIN DECLARED ZIP INPUTS"]
    for path in ordered_paths:
        raw = workspace[path]
        try:
            body = raw.decode("utf-8")
            encoding = "utf-8"
        except UnicodeDecodeError:
            body = base64.b64encode(raw).decode("ascii")
            encoding = "base64"
        header = {
            "path": path,
            "bytes": len(raw),
            "sha256": sha256_bytes(raw),
            "encoding": encoding,
        }
        blocks.extend(
            [
                canonical_json_bytes(header).decode("ascii"),
                body,
                "END DECLARED ZIP INPUT",
            ]
        )
    blocks.append("END DECLARED ZIP INPUTS")
    return "\n".join(blocks) + "\n"


def _attempt_seed(
    *,
    run_id: str,
    roster_seed: int,
    agent_id: str,
    attempt: int,
    hierarchy: dict[str, Any] | None = None,
) -> str:
    identity = {
        "schema": "constraintbox.md-agent-attempt-seed.v1",
        "run_id": run_id,
        "roster_seed": roster_seed,
        "agent_id": agent_id,
        "attempt": attempt,
    }
    if hierarchy is not None:
        identity.update(_hierarchy_surface(hierarchy))
    return sha256_bytes(canonical_json_bytes(identity))


def _prompt(
    agent_rel: str,
    output_rel: str,
    marker: str,
    *,
    mmm_paths: list[str],
    skill_paths: list[str],
    context_paths: list[str],
    required_fragments: list[str],
    forbidden_fragments: list[str],
    attempt: int,
    attempt_seed: str,
    prior_refusal: str | None,
    output_delivery: str = "workspace_file",
    output_format: str = "text",
    embedded_inputs: str | None = None,
    hierarchy: dict[str, Any] | None = None,
) -> str:
    ordered = [agent_rel, *mmm_paths, *skill_paths, *context_paths]
    if TOOL_EVIDENCE_PATH not in ordered:
        ordered.append(TOOL_EVIDENCE_PATH)
    files = "\n".join(f"{index}. {path}" for index, path in enumerate(ordered, start=1))
    fragments = "\n".join(f"- {fragment}" for fragment in required_fragments)
    forbidden = "\n".join(f"- {fragment}" for fragment in forbidden_fragments)
    hierarchy_line = ""
    if hierarchy is not None:
        hierarchy_line = (
            "Hierarchy binding (include these exact values in provider request identity): "
            f"{canonical_json_bytes(_hierarchy_surface(hierarchy)).decode('ascii')}\n"
        )
    if output_delivery == "provider_response":
        if not embedded_inputs:
            raise ZipJobRefusal(
                "REFUSE_MD_AGENT_PROVIDER_PROMPT_MISSING", "embedded_inputs"
            )
        delivery_line = (
            "Return exactly one bounded response through the declared provider adapter. "
            f"Do not create {output_rel}; CB will materialize the adapter response as that file.\n"
            "Every declared ZIP input is embedded below; do not rely on filesystem tools.\n"
        )
    else:
        delivery_line = f"Write ONLY {output_rel}. Create parent directories if needed.\n"
    format_line = ""
    if output_format == "strict_json_object":
        format_line = (
            "The delivered result must be exactly one strict JSON object. Do not use "
            "single quotes, trailing commas, markdown fences, or a prose wrapper.\n"
        )
    return (
        f"You are the markdown file {agent_rel}. That file is the agent.\n"
        "Read these files in this exact order before doing the task:\n"
        f"{files}\n"
        f"This is fresh attempt {attempt}. Deterministic attempt seed: {attempt_seed}\n"
        f"Prior deterministic refusal: {prior_refusal or 'none'}\n"
        f"{hierarchy_line}"
        + delivery_line
        + format_line
        + f"The file must contain this exact marker: {marker}\n"
        "The file must also contain every literal fragment below exactly as written:\n"
        f"{fragments or '- none'}\n"
        "The file must not contain any forbidden literal fragment below:\n"
        f"{forbidden or '- none'}\n"
        f"Also copy the canonical_sha256 value from {TOOL_EVIDENCE_PATH} into the file.\n"
        f"To ask CB to run a declared TOOLS/*.py, also write {TOOL_REQUEST_PATH} "
        f"with schema {TOOL_REQUEST_SCHEMA}, script_path, and optional payload object.\n"
        "CB runs that script after this attempt and retries you with the new evidence. "
        "On the retry, do not repeat the request; copy the new canonical_sha256 into your file.\n"
        "If you do not write that file correctly, the result is refused and you may be retried.\n"
        "Prose is not the result. The file is the result.\n"
        + (embedded_inputs or "")
    )


_PROVIDER_ENV_COMMON = (
    "PATH",
    "HOME",
    "USER",
    "LOGNAME",
    "LANG",
    "LC_ALL",
    "LC_CTYPE",
    "TMPDIR",
    "TMP",
    "TEMP",
    "TERM",
    "TZ",
    "SSL_CERT_FILE",
    "SSL_CERT_DIR",
    "REQUESTS_CA_BUNDLE",
    "CURL_CA_BUNDLE",
)
_PROVIDER_ENV_EXTRA = {
    "codex-cli": ("CODEX_HOME", "OPENAI_API_KEY"),
    "grok-cli": (),
    "claude-code": ("ANTHROPIC_API_KEY", "CLAUDE_CODE_OAUTH_TOKEN"),
}


def _provider_env(provider: str, controller_src: object | None = None) -> dict[str, str]:
    names = list(_PROVIDER_ENV_COMMON)
    names.extend(_PROVIDER_ENV_EXTRA.get(provider, ()))
    env = {name: os.environ[name] for name in names if name in os.environ and os.environ[name]}
    env["PYTHONNOUSERSITE"] = "1"
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    if controller_src is not None:
        controller = declared_controller_src(controller_src)
        env["CB_CONTROLLER_SRC"] = str(controller)
        env["PYTHONPATH"] = str(controller)
    return env


def _declared_file(agent: dict[str, Any], field: str, *, executable: bool) -> Path:
    raw = _text(agent.get(field), field)
    path = Path(raw).expanduser()
    if not path.is_absolute():
        raise ZipJobRefusal("REFUSE_MD_AGENT_ROSTER_SCHEMA", field)
    try:
        resolved = path.resolve(strict=True)
    except OSError as exc:
        raise ZipJobRefusal("HOLD_PROVIDER_EXECUTABLE_MISSING", raw) from exc
    if not resolved.is_file() or (executable and not os.access(resolved, os.X_OK)):
        raise ZipJobRefusal("HOLD_PROVIDER_EXECUTABLE_MISSING", raw)
    return resolved


def _adapter_path(provider: str, controller_src: object | None = None) -> Path:
    module_name = _ADAPTER_MODULES[provider]
    controller = declared_controller_src(controller_src)
    path = controller / "constraintbox" / f"{module_name.rsplit('.', 1)[-1]}.py"
    if path.is_file():
        return path.resolve()
    raise ZipJobRefusal("HOLD_PROVIDER_ADAPTER_MISSING", module_name)


def _argv(
    agent: dict[str, Any],
    work: Path,
    prompt_path: Path,
    *,
    request_id: str,
    timeout_seconds: int,
    output_delivery: str = "workspace_file",
    hierarchy: dict[str, Any] | None = None,
) -> tuple[list[str], dict[str, str], Path | None]:
    provider = _text(agent.get("provider"), "provider")
    if provider == "fixture-subprocess":
        env = {
            "PATH": os.pathsep.join([str(Path(sys.executable).resolve().parent), "/usr/bin", "/bin"]),
            "HOME": str(work / "home"),
            "TMPDIR": str(work / "tmp"),
            "PYTHONNOUSERSITE": "1",
            "PYTHONDONTWRITEBYTECODE": "1",
            "LANG": "C",
        }
        (work / "home").mkdir(parents=True, exist_ok=True)
        (work / "tmp").mkdir(parents=True, exist_ok=True)
        return [sys.executable, "-c", _text(agent.get("fixture_script"), "fixture_script")], env, None
    if os.environ.get("CB_REQUIRE_HOST_HOOK") == "1" or not os.environ.get("CB_DISPATCH_NONCE"):
        raise ZipJobRefusal("HOLD_HOST_HOOK_REQUIRED", provider)
    nonce = os.environ.get("CB_DISPATCH_NONCE", "").strip()
    nonce_file = os.environ.get("CB_DISPATCH_NONCE_FILE") or ""
    if not nonce_file:
        raise ZipJobRefusal("HOLD_DISPATCH_NONCE_UNBOUND", "CB_DISPATCH_NONCE_FILE")
    try:
        disk = Path(nonce_file).read_text(encoding="utf-8").strip()
    except OSError as exc:
        raise ZipJobRefusal("HOLD_DISPATCH_NONCE_UNBOUND", nonce_file) from exc
    if disk != nonce:
        raise ZipJobRefusal("HOLD_DISPATCH_NONCE_MISMATCH", nonce_file)
    controller: Path | None = None
    if provider in _ADAPTER_MODULES:
        controller = declared_controller_src(agent.get("controller_src"))
    if output_delivery not in _OUTPUT_DELIVERIES:
        raise ZipJobRefusal("REFUSE_MD_AGENT_OUTPUT_DELIVERY", "output_delivery")
    env = _provider_env(provider, controller)
    model = _text(agent.get("model_requested"), "model_requested")
    request_path = work / "meta" / "provider_request.json"
    response_path = work / "meta" / "provider_response.json"
    receipt_path = work / "meta" / "provider_receipt.json"
    hierarchy_request = _hierarchy_surface(hierarchy) if hierarchy is not None else {}
    if provider == "codex-cli":
        if agent.get("codex_home") is None:
            raise ZipJobRefusal("HOLD_CODEX_HOME_UNBOUND", "CODEX_HOME")
        runner = _declared_file(agent, "runner_path", executable=True)
        _adapter_path(provider, controller)
        codex_home = Path(_text(agent.get("codex_home"), "codex_home")).expanduser()
        if not codex_home.is_absolute() or not codex_home.is_dir():
            raise ZipJobRefusal("REFUSE_MD_AGENT_ROSTER_SCHEMA", "codex_home")
        env["CODEX_HOME"] = str(codex_home.resolve())
        request_path.write_bytes(canonical_json_bytes(_bind_adapter_mmm(work, prompt_path, {
            "schema": "constraintbox.codex-cli-request.v1",
            "request_id": request_id,
            **hierarchy_request,
            "runner_path": str(runner),
            "model": model,
            "reasoning_effort": str(agent.get("reasoning_effort") or "max"),
            "sandbox_mode": "read-only" if output_delivery == "provider_response" else "workspace-write",
            "prompt_path": str(prompt_path),
            "cwd": str(work),
            "controller_src": str(controller),
        })))
        return (
            [sys.executable, "-m", _ADAPTER_MODULES[provider], "--request", str(request_path),
             "--response", str(response_path), "--receipt", str(receipt_path),
             "--timeout", str(timeout_seconds)],
            env, receipt_path,
        )
    if provider == "grok-cli":
        runner = _declared_file(agent, "runner_path", executable=True)
        _adapter_path(provider, controller)
        request_path.write_bytes(canonical_json_bytes(_bind_adapter_mmm(work, prompt_path, {
            "schema": "constraintbox.grok-cli-request.v1",
            "request_id": request_id,
            **hierarchy_request,
            "runner_path": str(runner),
            "model": model,
            "prompt_path": str(prompt_path),
            "cwd": str(work),
            "max_turns": int(agent.get("max_turns") or 8),
            "tools": "",
            "permission_mode": "bypassPermissions",
            "controller_src": str(controller),
        })))
        return (
            [sys.executable, "-m", _ADAPTER_MODULES[provider], "--request", str(request_path),
             "--response", str(response_path), "--receipt", str(receipt_path),
             "--timeout", str(timeout_seconds)],
            env, receipt_path,
        )
    if provider == "claude-code":
        _declared_file(agent, "runner_path", executable=True)
        _adapter_path(provider, controller)
        bridge = _declared_file(agent, "bridge_path", executable=False)
        budget = agent.get("budget_usd", 1.0)
        if isinstance(budget, bool) or not isinstance(budget, (int, float)) or not 0.01 <= budget <= 5:
            raise ZipJobRefusal("REFUSE_MD_AGENT_ROSTER_SCHEMA", "budget_usd")
        adapter_request = _bind_adapter_mmm(work, prompt_path, {
            "schema": "constraintbox.claude-bridge-request.v1",
            "request_id": request_id,
            **hierarchy_request,
            "bridge_path": str(bridge),
            "model": model,
            "effort": str(agent.get("reasoning_effort") or "high"),
            "budget_usd": budget,
            "timeout_seconds": timeout_seconds,
            "prompt_path": str(prompt_path),
            "cwd": str(work),
            "out_dir": str(work / "meta" / "claude-output"),
            "tools": "" if output_delivery == "provider_response" else "Read,Write,Edit",
            "controller_src": str(controller),
        })
        allowlist = agent.get("model_observed_allowlist")
        if allowlist is not None:
            adapter_request["model_observed_allowlist"] = _model_observed_allowlist(allowlist)
        request_path.write_bytes(canonical_json_bytes(adapter_request))
        return (
            [sys.executable, "-m", _ADAPTER_MODULES[provider], "--request", str(request_path),
             "--receipt", str(receipt_path)],
            env, receipt_path,
        )
    raise ZipJobRefusal("REFUSE_MD_AGENT_PROVIDER_UNSUPPORTED", provider)


def _copy_workspace(work: Path, workspace: dict[str, bytes], keep: list[str]) -> None:
    for path in keep:
        if not path or path.startswith("/") or ".." in Path(path).parts:
            raise ZipJobRefusal("REFUSE_MD_AGENT_PATH", path)
        dest = (work / path).resolve()
        try:
            dest.relative_to(work.resolve())
        except ValueError as exc:
            raise ZipJobRefusal("REFUSE_MD_AGENT_PATH", path) from exc
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(workspace[path])
    (work / "output").mkdir(parents=True, exist_ok=True)
    (work / "meta").mkdir(parents=True, exist_ok=True)


def _apply_tool_request(workspace: dict[str, bytes], raw: bytes) -> bytes:
    request = _object(raw, TOOL_REQUEST_PATH)
    if request.get("schema") != TOOL_REQUEST_SCHEMA:
        raise ZipJobRefusal("REFUSE_MD_AGENT_TOOL_REQUEST", "schema")
    script_path = _text(request.get("script_path"), "script_path")
    if not script_path.startswith("TOOLS/") or not script_path.endswith(".py") or ".." in Path(script_path).parts:
        raise ZipJobRefusal("REFUSE_MD_AGENT_TOOL_REQUEST", script_path)
    if script_path not in workspace:
        raise ZipJobRefusal("REFUSE_MD_AGENT_TOOL_REQUEST", "missing_script")
    payload = request.get("payload")
    if payload is None:
        if TOOL_PAYLOAD_PATH not in workspace:
            raise ZipJobRefusal("REFUSE_MD_AGENT_TOOL_REQUEST", "missing_payload")
    elif not isinstance(payload, dict):
        raise ZipJobRefusal("REFUSE_MD_AGENT_TOOL_REQUEST", "payload")
    else:
        workspace[TOOL_PAYLOAD_PATH] = canonical_json_bytes(payload)
    from .zip_python_tool import run_zip_python_tool

    task = TaskSpec.model_validate(
        {
            "schema": "constraintbox.zip_task.v1",
            "task_id": "worker-tool",
            "sequence": 0,
            "operation": "run_zip_python_tool_v1",
            "input_paths": [script_path, TOOL_PAYLOAD_PATH],
            "output_paths": [TOOL_EVIDENCE_PATH],
        }
    )
    produced = run_zip_python_tool(task, workspace)
    evidence = produced[TOOL_EVIDENCE_PATH]
    workspace[TOOL_EVIDENCE_PATH] = evidence
    return evidence


def _provider_evidence(
    *,
    provider: str,
    evidence_path: Path | None,
    request_id: str,
    model_requested: str | None,
    prompt: bytes,
    model_observed_allowlist: list[str] | None = None,
) -> dict[str, Any]:
    model_observed_allowlist = _model_observed_allowlist(model_observed_allowlist)
    if provider == "fixture-subprocess":
        return {
            "provider_request_id": None,
            "model_observed": ["fixture-observed"],
            "model_observed_values": ["fixture-observed"],
            "model_binding_confirmed": False,
            "model_identity_match_kind": _MODEL_MATCH_UNVERIFIED,
            "model_match_kind": _MODEL_MATCH_UNVERIFIED,
            "model_alias_admitted": False,
            "alias_resolution_source": None,
            "model_observed_allowlist": model_observed_allowlist,
            "identity_source": "fixture",
            "composed_prompt_sha256": sha256_bytes(prompt),
            "provider_source_receipt_sha256": None,
            "provider_source_receipt": None,
        }
    if evidence_path is None or not evidence_path.is_file():
        raise ZipJobRefusal("REFUSE_MD_AGENT_PROVIDER_EVIDENCE", "missing")
    raw = evidence_path.read_bytes()
    source = _object(raw, "provider_receipt")
    if source.get("disposition") != "OBSERVED":
        raise ZipJobRefusal("REFUSE_MD_AGENT_PROVIDER_EVIDENCE", "disposition")
    if source.get("request_id") != request_id:
        raise ZipJobRefusal("REFUSE_MD_AGENT_PROVIDER_EVIDENCE", "request_id")
    if source.get("model_requested") != model_requested:
        raise ZipJobRefusal("REFUSE_MD_AGENT_PROVIDER_EVIDENCE", "model_requested")
    if source.get("prompt_sha256") != sha256_bytes(prompt):
        raise ZipJobRefusal("REFUSE_MD_AGENT_PROVIDER_EVIDENCE", "prompt_sha256")
    if source.get("model_binding_confirmed") is not True:
        raise ZipJobRefusal("REFUSE_MD_AGENT_PROVIDER_EVIDENCE", "model_binding")
    if provider == "codex-cli":
        observed = [source.get("model_observed")]
    elif provider == "grok-cli":
        observed = source.get("models_observed_in_output")
    else:
        observed = source.get("models_observed")
    if not isinstance(observed, list) or not observed or any(
        not isinstance(value, str) or not value for value in observed
    ):
        raise ZipJobRefusal("REFUSE_MD_AGENT_PROVIDER_EVIDENCE", "model_observed")
    # A provider receipt represents one observed route identity.  Multiple
    # observed values are ambiguous (even if one happens to contain the
    # requested alias) and must not become an admission through ``all(...)``.
    if len(observed) != 1:
        raise ZipJobRefusal("REFUSE_MD_AGENT_PROVIDER_EVIDENCE", "model_observed")
    observed_value = observed[0]
    if "model_observed_allowlist" in source:
        if source["model_observed_allowlist"] != model_observed_allowlist:
            raise ZipJobRefusal(
                "REFUSE_MD_AGENT_PROVIDER_EVIDENCE", "model_observed_allowlist"
            )
    elif provider == "claude-code" and observed != [model_requested]:
        raise ZipJobRefusal(
            "REFUSE_MD_AGENT_PROVIDER_EVIDENCE", "model_observed_allowlist"
        )
    model_identity_match_kind = _MODEL_MATCH_EXACT
    alias_resolution_source: str | None = None
    if observed == [model_requested]:
        model_matches = True
    elif model_observed_allowlist is not None and observed_value in model_observed_allowlist:
        model_matches = True
        model_identity_match_kind = _MODEL_MATCH_DECLARED_ALIAS
        alias_resolution_source = "invocation.model_observed_allowlist"
    else:
        model_matches = False
    if not model_matches:
        raise ZipJobRefusal("REFUSE_MD_AGENT_PROVIDER_EVIDENCE", "model_observed")
    source_kind = source.get("model_identity_match_kind")
    if (
        provider == "claude-code" and source_kind != model_identity_match_kind
    ) or (source_kind is not None and source_kind != model_identity_match_kind):
        raise ZipJobRefusal(
            "REFUSE_MD_AGENT_PROVIDER_EVIDENCE", "model_identity_match_kind"
        )
    source_alias = source.get("alias_resolution_source")
    if model_identity_match_kind == _MODEL_MATCH_DECLARED_ALIAS:
        if (
            provider == "claude-code"
            and source_alias != alias_resolution_source
        ) or (source_alias is not None and source_alias != alias_resolution_source):
            raise ZipJobRefusal(
                "REFUSE_MD_AGENT_PROVIDER_EVIDENCE", "alias_resolution_source"
            )
    elif source_alias is not None:
        raise ZipJobRefusal(
            "REFUSE_MD_AGENT_PROVIDER_EVIDENCE", "alias_resolution_source"
        )
    return {
        "provider_request_id": request_id,
        "model_observed": observed,
        "model_observed_values": observed,
        "model_binding_confirmed": True,
        "model_identity_match_kind": model_identity_match_kind,
        "model_match_kind": model_identity_match_kind,
        "model_alias_admitted": model_identity_match_kind == _MODEL_MATCH_DECLARED_ALIAS,
        "alias_resolution_source": alias_resolution_source,
        "model_observed_allowlist": model_observed_allowlist,
        "identity_source": "provider_adapter_receipt",
        "composed_prompt_sha256": sha256_bytes(prompt),
        "provider_source_receipt_sha256": sha256_bytes(raw),
        "provider_source_receipt": source,
    }


def _contained_provider_artifact(work: Path, raw_path: object, label: str) -> tuple[Path, bytes]:
    """Read one adapter artifact only when it remains inside this temp workdir."""

    if not isinstance(raw_path, str) or not raw_path:
        raise ZipJobRefusal("REFUSE_MD_AGENT_PROVIDER_RESPONSE_MISSING", label)
    supplied = Path(raw_path).expanduser()
    if not supplied.is_absolute() or supplied.is_symlink():
        raise ZipJobRefusal("REFUSE_MD_AGENT_PROVIDER_RESPONSE_UNCONTAINED", label)
    try:
        resolved = supplied.resolve(strict=True)
        resolved.relative_to(work.resolve())
        stat_result = resolved.stat()
    except (OSError, ValueError) as exc:
        raise ZipJobRefusal("REFUSE_MD_AGENT_PROVIDER_RESPONSE_UNCONTAINED", label) from exc
    if not resolved.is_file() or stat_result.st_size > _MAX_PROVIDER_RESPONSE_BYTES:
        raise ZipJobRefusal("REFUSE_MD_AGENT_PROVIDER_RESPONSE_MALFORMED", label)
    try:
        raw = resolved.read_bytes()
    except OSError as exc:
        raise ZipJobRefusal("REFUSE_MD_AGENT_PROVIDER_RESPONSE_MISSING", label) from exc
    if not raw:
        raise ZipJobRefusal("REFUSE_MD_AGENT_PROVIDER_RESPONSE_MISSING", label)
    return resolved, raw


def _extract_provider_response(
    *,
    provider: str,
    source: dict[str, Any],
    work: Path,
) -> tuple[bytes, str, str]:
    """Extract the exact bounded response bytes from a current adapter artifact."""

    if provider == "codex-cli":
        path, raw = _contained_provider_artifact(work, source.get("response_path"), "codex.response_path")
        expected_raw = source.get("stdout_sha256")
        if not isinstance(expected_raw, str) or expected_raw != sha256_bytes(raw):
            raise ZipJobRefusal("REFUSE_MD_AGENT_PROVIDER_RESPONSE_TAMPER", "codex.response")
        try:
            text = raw.decode("utf-8")
            messages: list[str] = []
            for line in text.splitlines():
                event = json.loads(line)
                if not isinstance(event, dict) or event.get("type") != "item.completed":
                    continue
                item = event.get("item")
                if isinstance(item, dict) and item.get("type") == "agent_message":
                    message = item.get("text")
                    if not isinstance(message, str) or not message:
                        raise ValueError("invalid Codex agent message")
                    messages.append(message)
        except (UnicodeDecodeError, json.JSONDecodeError, TypeError, ValueError) as exc:
            raise ZipJobRefusal("REFUSE_MD_AGENT_PROVIDER_RESPONSE_MALFORMED", "codex.response") from exc
        if not messages or source.get("agent_messages") != messages:
            raise ZipJobRefusal("REFUSE_MD_AGENT_PROVIDER_RESPONSE_MALFORMED", "codex.agent_messages")
        response = messages[-1].encode("utf-8")
        if source.get("final_agent_message_sha256") != sha256_bytes(response):
            raise ZipJobRefusal("REFUSE_MD_AGENT_PROVIDER_RESPONSE_TAMPER", "codex.agent_message")
        return response, f"codex-cli:{path.name}:item.completed.agent_message[-1]", sha256_bytes(raw)

    if provider == "grok-cli":
        path, raw = _contained_provider_artifact(work, source.get("response_path"), "grok.response_path")
        expected_raw = source.get("response_sha256")
        if not isinstance(expected_raw, str) or expected_raw != sha256_bytes(raw):
            raise ZipJobRefusal("REFUSE_MD_AGENT_PROVIDER_RESPONSE_TAMPER", "grok.response")
        try:
            value = json.loads(raw)
            stop_reason = value.get("stopReason") if isinstance(value, dict) else None
            response_value = value.get("text") if isinstance(value, dict) else None
            if stop_reason != "end_turn" or not isinstance(response_value, str) or not response_value.strip():
                raise ValueError("invalid Grok terminal response")
            response = response_value.encode("utf-8")
        except (UnicodeDecodeError, json.JSONDecodeError, TypeError, ValueError) as exc:
            raise ZipJobRefusal("REFUSE_MD_AGENT_PROVIDER_RESPONSE_MALFORMED", "grok.response") from exc
        if source.get("result_text_sha256") != sha256_bytes(response):
            raise ZipJobRefusal("REFUSE_MD_AGENT_PROVIDER_RESPONSE_TAMPER", "grok.result_text")
        return response, f"grok-cli:{path.name}:text", sha256_bytes(raw)

    if provider == "claude-code":
        path, raw = _contained_provider_artifact(
            work, source.get("nested_output_path"), "claude.nested_output_path"
        )
        if source.get("nested_output_sha256") != sha256_bytes(raw):
            raise ZipJobRefusal("REFUSE_MD_AGENT_PROVIDER_RESPONSE_TAMPER", "claude.nested_output")
        try:
            value = json.loads(raw)
            result = value.get("result") if isinstance(value, dict) else None
            if (
                not isinstance(result, str)
                or not result.strip()
                or value.get("is_error") is not False
                or value.get("subtype") != "success"
                or value.get("terminal_reason") != "completed"
            ):
                raise ValueError("invalid Claude terminal result")
            response = result.encode("utf-8")
        except (UnicodeDecodeError, json.JSONDecodeError, TypeError, ValueError) as exc:
            raise ZipJobRefusal(
                "REFUSE_MD_AGENT_PROVIDER_RESPONSE_MALFORMED",
                "claude.nested_output",
            ) from exc
        return response, f"claude-code:{path.name}:result", sha256_bytes(raw)

    raise ZipJobRefusal("REFUSE_MD_AGENT_PROVIDER_RESPONSE_UNSUPPORTED", provider)


def _run_one(
    *,
    agent: dict[str, Any],
    workspace: dict[str, bytes],
    shared_paths: list[str],
    marker: str,
    timeout_seconds: int,
    max_attempts: int,
    run_id: str,
    roster_seed: int,
    hierarchy: dict[str, Any] | None = None,
) -> dict[str, Any]:
    agent_id = _text(agent.get("agent_id"), "agent_id")
    agent_path = _text(agent.get("agent_path"), "agent_path")
    output_path = _text(agent.get("output_path"), "output_path")
    output_delivery = _output_delivery(agent)
    output_format = _output_format(agent)
    model_observed_allowlist = _model_observed_allowlist(agent.get("model_observed_allowlist"))
    if not agent_path.startswith("AGENTS/") or not agent_path.endswith(".md"):
        raise ZipJobRefusal("REFUSE_MD_AGENT_PATH", agent_path)
    if not output_path.startswith("output/") or not output_path.endswith(".md"):
        raise ZipJobRefusal("REFUSE_MD_AGENT_OUTPUT_PATH", output_path)
    if agent_path not in workspace:
        raise ZipJobRefusal("REFUSE_MD_AGENT_FILE_MISSING", agent_path)
    if TOOL_EVIDENCE_PATH not in workspace:
        raise ZipJobRefusal("REFUSE_MD_AGENT_TOOL_EVIDENCE_MISSING", TOOL_EVIDENCE_PATH)
    workspace = dict(workspace)
    hierarchy_surface = _hierarchy_surface(hierarchy)
    tool_request_observed = False
    cb_tool_executed = False
    tool_result_consumed_on_later_attempt = False
    applied_request_sha256: str | None = None
    provider_response_sha256: str | None = None
    response_extraction_source: str | None = None
    provider_response_materialized = False
    mmm_paths = _path_list(agent.get("mmm_paths"), "mmm_paths", minimum=1, maximum=9)
    skill_paths = _path_list(agent.get("skill_paths"), "skill_paths", minimum=1, maximum=16)
    context_paths = _path_list(agent.get("context_paths") or [], "context_paths", maximum=32)
    required_fragments = _path_list(
        agent.get("required_fragments") or [], "required_fragments", maximum=24
    )
    forbidden_fragments = _path_list(
        agent.get("forbidden_fragments") or [], "forbidden_fragments", maximum=32
    )
    max_output_bytes = _int(
        agent.get("max_output_bytes", 262144), "max_output_bytes", minimum=1, maximum=1048576
    )
    delivered_paths = [agent_path, *mmm_paths, *skill_paths, *context_paths, *shared_paths]
    delivered_paths = list(dict.fromkeys(delivered_paths))
    if TOOL_EVIDENCE_PATH not in delivered_paths:
        delivered_paths.append(TOOL_EVIDENCE_PATH)
    for path in delivered_paths:
        if path not in workspace:
            raise ZipJobRefusal("REFUSE_MD_AGENT_FILE_MISSING", path)
    delivered_sha256 = {path: sha256_bytes(workspace[path]) for path in sorted(delivered_paths)}
    tool_evidence_sha256 = delivered_sha256[TOOL_EVIDENCE_PATH]
    skill_bytes_delivered = all(path in delivered_sha256 for path in skill_paths)
    try:
        tool_evidence = strict_json_loads(workspace[TOOL_EVIDENCE_PATH], label=TOOL_EVIDENCE_PATH)
        tool_token = tool_evidence.get("canonical_sha256")
    except (ZipJobRefusal, AttributeError):
        raise ZipJobRefusal("REFUSE_MD_AGENT_TOOL_EVIDENCE_MISSING", "canonical_sha256")
    if not isinstance(tool_token, str) or len(tool_token) != 64:
        raise ZipJobRefusal("REFUSE_MD_AGENT_TOOL_EVIDENCE_MISSING", "canonical_sha256")
    attempts: list[dict[str, Any]] = []
    last_error: str | None = None
    for attempt in range(1, max_attempts + 1):
        provider_response_sha256 = None
        response_extraction_source = None
        provider_response_materialized = False
        with tempfile.TemporaryDirectory(prefix=f"cb-md-agent-{agent_id}-") as tmp:
            work = Path(tmp)
            _copy_workspace(work, workspace, delivered_paths)
            seed = _attempt_seed(
                run_id=run_id,
                roster_seed=roster_seed,
                agent_id=agent_id,
                attempt=attempt,
                hierarchy=hierarchy,
            )
            prompt_path = work / "meta" / "WORKER_PROMPT.md"
            embedded_inputs = (
                _embedded_provider_inputs(workspace, delivered_paths)
                if output_delivery == "provider_response"
                else None
            )
            prompt_path.write_text(
                _prompt(
                    agent_path,
                    output_path,
                    marker,
                    mmm_paths=mmm_paths,
                    skill_paths=skill_paths,
                    context_paths=context_paths,
                    required_fragments=required_fragments,
                    forbidden_fragments=forbidden_fragments,
                    attempt=attempt,
                    attempt_seed=seed,
                    prior_refusal=last_error,
                    output_delivery=output_delivery,
                    output_format=output_format,
                    embedded_inputs=embedded_inputs,
                    hierarchy=hierarchy,
                ),
                encoding="utf-8",
            )
            request_identity = {
                "run_id": run_id,
                "agent_id": agent_id,
                "attempt": attempt,
                "model_observed_allowlist": model_observed_allowlist,
            }
            if hierarchy is not None:
                request_identity.update(hierarchy_surface)
            request_id = "zip-" + sha256_bytes(canonical_json_bytes(request_identity))[:32]
            argv, env, evidence_path = _argv(
                agent,
                work,
                prompt_path,
                request_id=request_id,
                timeout_seconds=timeout_seconds,
                output_delivery=output_delivery,
                hierarchy=hierarchy,
            )
            # Live adapters bind their MMM header into this exact file.  Read
            # after _argv so the roster verifies the bytes actually delivered
            # to the provider rather than the pre-binding worker prompt.
            prompt_bytes = prompt_path.read_bytes()
            env["CB_ZIP_ATTEMPT"] = str(attempt)
            env["CB_ZIP_ATTEMPT_SEED"] = seed
            env["CB_ZIP_PRIOR_REFUSAL"] = last_error or ""
            try:
                proc = subprocess.run(
                    argv,
                    cwd=str(work),
                    env=env,
                    text=True,
                    capture_output=True,
                    timeout=timeout_seconds,
                    check=False,
                )
            except subprocess.TimeoutExpired:
                last_error = "REFUSE_MD_AGENT_TIMEOUT"
                attempts.append(
                    {
                        **hierarchy_surface,
                        "attempt": attempt,
                        "attempt_seed": seed,
                        "provider_request_id": request_id,
                        "returncode": None,
                        "output_present": False,
                        "marker_present": False,
                        "format_present": False,
                        "refusal_reason": last_error,
                        "output_sha256": None,
                        "model_identity_match_kind": _MODEL_MATCH_UNVERIFIED,
                        "model_match_kind": _MODEL_MATCH_UNVERIFIED,
                        "alias_resolution_source": None,
                        "model_alias_admitted": False,
                        "skill_bytes_delivered": skill_bytes_delivered,
                        "skill_read_proved": False,
                        "skill_executed": False,
                        "skill_bytes_consumed": None,
                    }
                )
                continue
            produced = work / output_path
            exists = produced.is_file() and produced.stat().st_size > 0
            body = produced.read_bytes() if exists else b""
            request_file = work / TOOL_REQUEST_PATH
            if request_file.is_file() and request_file.stat().st_size > 0:
                try:
                    request_raw = request_file.read_bytes()
                    request_sha256 = sha256_bytes(request_raw)
                    tool_request_observed = True
                    if request_sha256 == applied_request_sha256:
                        raise ZipJobRefusal("REFUSE_MD_AGENT_TOOL_REQUEST_REPEATED")
                    new_evidence = _apply_tool_request(workspace, request_raw)
                    cb_tool_executed = True
                    applied_request_sha256 = request_sha256
                    tool_evidence = strict_json_loads(new_evidence, label=TOOL_EVIDENCE_PATH)
                    next_token = tool_evidence.get("canonical_sha256")
                    if not isinstance(next_token, str) or len(next_token) != 64:
                        raise ZipJobRefusal("REFUSE_MD_AGENT_TOOL_REQUEST", "canonical_sha256")
                    tool_token = next_token
                    tool_evidence_sha256 = sha256_bytes(new_evidence)
                    delivered_sha256[TOOL_EVIDENCE_PATH] = tool_evidence_sha256
                    last_error = "HOLD_MD_AGENT_TOOL_APPLIED_NEED_REWRITE"
                    attempts.append(
                        {
                            **hierarchy_surface,
                            "attempt": attempt,
                            "attempt_seed": seed,
                            "provider_request_id": request_id,
                            "returncode": proc.returncode,
                            "output_present": exists,
                            "marker_present": False,
                            "format_present": False,
                            "refusal_reason": last_error,
                            "output_sha256": sha256_bytes(body) if exists else None,
                            "tool_requested": True,
                            "tool_request_sha256": request_sha256,
                            "cb_tool_executed": True,
                            "model_identity_match_kind": _MODEL_MATCH_UNVERIFIED,
                            "model_match_kind": _MODEL_MATCH_UNVERIFIED,
                            "alias_resolution_source": None,
                            "model_alias_admitted": False,
                            "skill_bytes_delivered": skill_bytes_delivered,
                            "skill_read_proved": False,
                            "skill_executed": False,
                            "skill_bytes_consumed": None,
                        }
                    )
                    continue
                except ZipJobRefusal as exc:
                    last_error = exc.reason_code
                    attempts.append(
                        {
                            **hierarchy_surface,
                            "attempt": attempt,
                            "attempt_seed": seed,
                            "provider_request_id": request_id,
                            "returncode": proc.returncode,
                            "output_present": exists,
                            "marker_present": False,
                            "format_present": False,
                            "refusal_reason": last_error,
                            "output_sha256": sha256_bytes(body) if exists else None,
                            "tool_requested": True,
                            "model_identity_match_kind": _MODEL_MATCH_UNVERIFIED,
                            "model_match_kind": _MODEL_MATCH_UNVERIFIED,
                            "alias_resolution_source": None,
                            "model_alias_admitted": False,
                            "skill_bytes_delivered": skill_bytes_delivered,
                            "skill_read_proved": False,
                            "skill_executed": False,
                            "skill_bytes_consumed": None,
                        }
                    )
                    continue
            evidence_failure: str | None = None
            provider_receipt_summary: dict[str, Any] | None = None
            response_refusal: str | None = None
            evidence: dict[str, Any] = {
                "provider_request_id": request_id,
                "model_observed": [],
                "model_observed_values": [],
                "model_binding_confirmed": False,
                "model_identity_match_kind": _MODEL_MATCH_UNVERIFIED,
                "model_match_kind": _MODEL_MATCH_UNVERIFIED,
                "model_alias_admitted": False,
                "alias_resolution_source": None,
                "identity_source": None,
                "composed_prompt_sha256": sha256_bytes(prompt_bytes),
                "provider_source_receipt_sha256": None,
                "provider_source_receipt": None,
            }
            if output_delivery == "provider_response":
                # A provider-response leaf must not accept a file the model
                # wrote.  The only permitted output bytes are materialized by
                # this controller after adapter evidence passes.
                if exists:
                    response_refusal = "REFUSE_MD_AGENT_PROVIDER_OUTPUT_WRITE"
                else:
                    try:
                        evidence = _provider_evidence(
                            provider=str(agent.get("provider")),
                            evidence_path=evidence_path,
                            request_id=request_id,
                            model_requested=agent.get("model_requested"),
                            prompt=prompt_bytes,
                            model_observed_allowlist=model_observed_allowlist,
                        )
                        response, response_extraction_source, provider_response_sha256 = (
                            _extract_provider_response(
                                provider=str(agent.get("provider")),
                                source=evidence["provider_source_receipt"],
                                work=work,
                            )
                        )
                        produced.parent.mkdir(parents=True, exist_ok=True)
                        produced.write_bytes(response)
                        body = produced.read_bytes()
                        exists = True
                        provider_response_materialized = True
                    except ZipJobRefusal as exc:
                        response_refusal = exc.reason_code
                        evidence_failure = exc.detail or exc.reason_code
                        source = evidence.get("provider_source_receipt")
                        if isinstance(source, dict):
                            provider_receipt_summary = {
                                key: source.get(key)
                                for key in (
                                    "schema",
                                    "disposition",
                                    "reason_code",
                                    "request_id",
                                    "model_requested",
                                    "model_observed",
                                    "models_observed",
                                    "models_observed_in_output",
                                    "model_binding_confirmed",
                                    "returncode",
                                )
                                if key in source
                            }
                        if evidence.get("provider_source_receipt") is None:
                            evidence = {
                                **evidence,
                                "provider_source_receipt": None,
                                "model_identity_match_kind": _MODEL_MATCH_UNVERIFIED,
                                "model_match_kind": _MODEL_MATCH_UNVERIFIED,
                                "model_alias_admitted": False,
                                "alias_resolution_source": None,
                            }
            marker_ok = marker.encode("utf-8") in body
            size_ok = exists and len(body) <= max_output_bytes
            try:
                text = body.decode("utf-8") if exists else ""
                utf8_ok = True
            except UnicodeDecodeError:
                text = ""
                utf8_ok = False
            json_valid: bool | None = True if output_format != "strict_json_object" else None
            json_error: str | None = None
            if output_format == "strict_json_object" and exists and utf8_ok:
                try:
                    parsed_output = strict_json_loads(body, label=output_path)
                    if not isinstance(parsed_output, dict):
                        json_valid = False
                        json_error = "expected_json_object"
                    else:
                        json_valid = True
                except ZipJobRefusal as exc:
                    json_valid = False
                    json_error = exc.detail or exc.reason_code
            fragments_ok = utf8_ok and all(fragment in text for fragment in required_fragments)
            missing_fragments = [fragment for fragment in required_fragments if fragment not in text]
            forbidden_ok = utf8_ok and all(fragment not in text for fragment in forbidden_fragments)
            present_forbidden_fragments = [fragment for fragment in forbidden_fragments if fragment in text]
            json_ok = output_format != "strict_json_object" or json_valid is True
            format_ok = size_ok and fragments_ok and forbidden_ok and json_ok
            token_ok = utf8_ok and tool_token in text
            skill_ok = utf8_ok and all(
                delivered_sha256[path] in text for path in skill_paths
            )
            extra_outputs = []
            modified_protected = []
            allowed_new_files = {
                output_path,
                TOOL_REQUEST_PATH,
                "meta/WORKER_PROMPT.md",
                "meta/provider_request.json",
                "meta/provider_response.json",
                "meta/provider_receipt.json",
                "meta/provider_evidence.json",
            }
            allowed_new_prefixes = ("meta/claude-output/",)
            for path in work.rglob("*"):
                if not path.is_file():
                    continue
                rel = path.relative_to(work).as_posix()
                if rel in delivered_sha256:
                    if sha256_bytes(path.read_bytes()) != delivered_sha256[rel]:
                        modified_protected.append(rel)
                    continue
                if rel in allowed_new_files or any(rel.startswith(prefix) for prefix in allowed_new_prefixes):
                    continue
                extra_outputs.append(rel)
            if response_refusal is not None:
                refusal = response_refusal
            elif not exists:
                refusal = "REFUSE_MD_AGENT_MISSING_OUTPUT"
            elif not size_ok:
                refusal = "REFUSE_MD_AGENT_OUTPUT_SIZE"
            elif not utf8_ok:
                refusal = "REFUSE_MD_AGENT_OUTPUT_UTF8"
            elif not marker_ok:
                refusal = "REFUSE_MD_AGENT_MARKER_MISSING"
            elif not json_ok:
                refusal = "REFUSE_MD_AGENT_OUTPUT_JSON"
            elif not fragments_ok:
                refusal = "REFUSE_MD_AGENT_FORMAT_MISSING"
            elif not forbidden_ok:
                refusal = "REFUSE_MD_AGENT_FORBIDDEN_FRAGMENT"
            elif not token_ok:
                refusal = "REFUSE_MD_AGENT_TOOL_TOKEN_MISSING"
            elif not skill_ok:
                refusal = "REFUSE_MD_AGENT_SKILL_TOKEN_MISSING"
            elif extra_outputs or modified_protected:
                refusal = "REFUSE_MD_AGENT_EXTRA_OUTPUT"
            else:
                refusal = None
            if output_delivery != "provider_response":
                try:
                    evidence = _provider_evidence(
                        provider=str(agent.get("provider")),
                        evidence_path=evidence_path,
                        request_id=request_id,
                        model_requested=agent.get("model_requested"),
                        prompt=prompt_bytes,
                        model_observed_allowlist=model_observed_allowlist,
                    )
                except ZipJobRefusal as exc:
                    evidence_failure = exc.detail or exc.reason_code
                    if evidence_path is not None and evidence_path.is_file():
                        try:
                            raw_receipt = _object(evidence_path.read_bytes(), "provider_receipt")
                            provider_receipt_summary = {
                                key: raw_receipt.get(key)
                                for key in (
                                    "schema",
                                    "disposition",
                                    "reason_code",
                                    "request_id",
                                    "model_requested",
                                    "model_observed",
                                    "models_observed",
                                    "models_observed_in_output",
                                    "model_binding_confirmed",
                                    "returncode",
                                )
                                if key in raw_receipt
                            }
                        except ZipJobRefusal:
                            provider_receipt_summary = {"invalid_provider_receipt": True}
                    evidence = {
                        "provider_request_id": request_id,
                        "model_observed": [],
                        "model_observed_values": [],
                        "model_binding_confirmed": False,
                        "model_identity_match_kind": _MODEL_MATCH_UNVERIFIED,
                        "model_match_kind": _MODEL_MATCH_UNVERIFIED,
                        "model_alias_admitted": False,
                        "alias_resolution_source": None,
                        "identity_source": None,
                        "composed_prompt_sha256": sha256_bytes(prompt_bytes),
                        "provider_source_receipt_sha256": None,
                        "provider_source_receipt": None,
                    }
            if refusal is None and proc.returncode != 0:
                refusal = "REFUSE_MD_AGENT_PROVIDER_PROCESS"
            if refusal is None and evidence_failure is not None:
                refusal = "REFUSE_MD_AGENT_PROVIDER_EVIDENCE"
            row = {
                **hierarchy_surface,
                "attempt": attempt,
                "attempt_seed": seed,
                "provider_request_id": request_id,
                "returncode": proc.returncode,
                "stdout_sha256": sha256_bytes((proc.stdout or "").encode("utf-8")),
                "stderr_sha256": sha256_bytes((proc.stderr or "").encode("utf-8")),
                "output_present": exists,
                "marker_present": marker_ok,
                "format_present": format_ok,
                "refusal_reason": refusal,
                "output_sha256": sha256_bytes(body) if exists else None,
                "output_delivery": output_delivery,
                "output_format": output_format,
                "json_valid": json_valid,
                "json_error": json_error,
                "response_extraction_source": response_extraction_source,
                "provider_response_sha256": provider_response_sha256,
                "provider_response_materialized": provider_response_materialized,
                "controller_materialized_output": provider_response_materialized,
                "models_observed": evidence["model_observed"],
                "model_observed_values": evidence.get(
                    "model_observed_values", evidence["model_observed"]
                ),
                "model_observed": evidence["model_observed"][0] if evidence["model_observed"] else None,
                "model_binding_confirmed": evidence["model_binding_confirmed"],
                "model_identity_match_kind": evidence.get(
                    "model_identity_match_kind", _MODEL_MATCH_UNVERIFIED
                ),
                "model_match_kind": evidence.get(
                    "model_match_kind",
                    evidence.get("model_identity_match_kind", _MODEL_MATCH_UNVERIFIED),
                ),
                "model_alias_admitted": bool(evidence.get("model_alias_admitted", False)),
                "alias_resolution_source": evidence.get("alias_resolution_source"),
                "model_observed_allowlist": evidence.get(
                    "model_observed_allowlist", model_observed_allowlist
                ),
                "identity_source": evidence["identity_source"],
                "composed_prompt_sha256": evidence["composed_prompt_sha256"],
                "provider_source_receipt_sha256": evidence["provider_source_receipt_sha256"],
                "provider_evidence_failure": evidence_failure,
                "provider_receipt_summary": provider_receipt_summary,
                "missing_fragments": missing_fragments,
                "forbidden_fragments_present": present_forbidden_fragments,
                "extra_outputs": extra_outputs,
                "modified_protected_paths": modified_protected,
                "tool_token_present": token_ok,
                "skill_tokens_present": skill_ok,
                "skill_bytes_delivered": skill_bytes_delivered,
                "skill_read_proved": False,
                "skill_executed": False,
                "skill_bytes_consumed": None,
                "output_preview": text[:4096] if exists and utf8_ok else None,
            }
            attempts.append(row)
            if refusal is None:
                tool_result_consumed_on_later_attempt = cb_tool_executed
                attempt_summary = _attempt_receipt_summary(
                    attempts, accepted_attempt=attempt
                )
                return {
                    **hierarchy_surface,
                    "agent_id": agent_id,
                    "agent_path": agent_path,
                    "output_path": output_path,
                    "output_delivery": output_delivery,
                    "output_format": output_format,
                    "provider": agent["provider"],
                    "model_requested": agent.get("model_requested"),
                    "provider_request_id": evidence["provider_request_id"],
                    "models_observed": evidence["model_observed"],
                    "model_observed_values": evidence.get(
                        "model_observed_values", evidence["model_observed"]
                    ),
                    "model_observed": evidence["model_observed"][0],
                    "model_binding_confirmed": evidence["model_binding_confirmed"],
                    "model_identity_match_kind": evidence.get(
                        "model_identity_match_kind", _MODEL_MATCH_UNVERIFIED
                    ),
                    "model_match_kind": evidence.get(
                        "model_match_kind",
                        evidence.get("model_identity_match_kind", _MODEL_MATCH_UNVERIFIED),
                    ),
                    "model_alias_admitted": bool(evidence.get("model_alias_admitted", False)),
                    "alias_resolution_source": evidence.get("alias_resolution_source"),
                    "model_observed_allowlist": evidence.get(
                        "model_observed_allowlist", model_observed_allowlist
                    ),
                    "identity_source": evidence["identity_source"],
                    "composed_prompt_sha256": evidence["composed_prompt_sha256"],
                    "provider_source_receipt_sha256": evidence["provider_source_receipt_sha256"],
                    "provider_source_receipt": evidence["provider_source_receipt"],
                    "tool_evidence_sha256": tool_evidence_sha256,
                    "llm_invoked_tool": False,
                    "tool_request_observed": tool_request_observed,
                    "cb_tool_executed": cb_tool_executed,
                    "tool_result_consumed_on_later_attempt": tool_result_consumed_on_later_attempt,
                    "accepted": True,
                    "accepted_attempt": attempt,
                    **attempt_summary,
                    "delivered_file_sha256": delivered_sha256,
                    "skill_bytes_delivered": skill_bytes_delivered,
                    "skill_read_proved": False,
                    "skill_executed": False,
                    "skill_bytes_consumed": None,
                    "output_sha256": sha256_bytes(body),
                    "response_extraction_source": response_extraction_source,
                    "provider_response_sha256": provider_response_sha256,
                    "provider_response_materialized": provider_response_materialized,
                    "controller_materialized_output": provider_response_materialized,
                    "required_fragments": required_fragments,
                    "attempts": attempts,
                    "output_bytes": body,
                }
            last_error = refusal
    attempt_summary = _attempt_receipt_summary(attempts, accepted_attempt=None)
    return {
        **hierarchy_surface,
        "agent_id": agent_id,
        "agent_path": agent_path,
        "output_path": output_path,
        "output_delivery": output_delivery,
        "output_format": output_format,
        "provider": agent["provider"],
        "model_requested": agent.get("model_requested"),
        "model_identity_match_kind": _MODEL_MATCH_UNVERIFIED,
        "model_match_kind": _MODEL_MATCH_UNVERIFIED,
        "model_alias_admitted": False,
        "model_observed_allowlist": model_observed_allowlist,
        "accepted": False,
        "accepted_attempt": None,
        **attempt_summary,
        "delivered_file_sha256": delivered_sha256,
        "skill_bytes_delivered": skill_bytes_delivered,
        "skill_read_proved": False,
        "skill_executed": False,
        "skill_bytes_consumed": None,
        "output_sha256": None,
        "response_extraction_source": response_extraction_source,
        "provider_response_sha256": provider_response_sha256,
        "provider_response_materialized": provider_response_materialized,
        "controller_materialized_output": provider_response_materialized,
        "required_fragments": required_fragments,
        "llm_invoked_tool": False,
        "tool_request_observed": tool_request_observed,
        "cb_tool_executed": cb_tool_executed,
        "tool_result_consumed_on_later_attempt": tool_result_consumed_on_later_attempt,
        "attempts": attempts,
        "terminal_refusal": last_error or "REFUSE_MD_AGENT_MISSING_OUTPUT",
        "output_bytes": b"",
    }


def run_md_agent_roster(task: TaskSpec, workspace: dict[str, bytes]) -> dict[str, bytes]:
    if not task.input_paths or task.input_paths[0] != "inputs/roster.json":
        raise ZipJobRefusal("REFUSE_OPERATION_ARITY", task.task_id)
    roster = _object(workspace["inputs/roster.json"], "inputs/roster.json")
    if roster.get("schema") != ROSTER_SCHEMA:
        raise ZipJobRefusal("REFUSE_MD_AGENT_ROSTER_SCHEMA", "schema")
    if set(roster) not in (_ROSTER_FIELDS, _ROSTER_FIELDS | _HIERARCHY_FIELDS):
        raise ZipJobRefusal("REFUSE_MD_AGENT_ROSTER_SCHEMA", "fields")
    hierarchy = _hierarchy_binding(roster)
    hierarchy_surface = _hierarchy_surface(hierarchy)
    run_id = _text(roster.get("run_id"), "run_id")
    roster_seed = _int(roster.get("seed"), "seed", minimum=0, maximum=2**63 - 1)
    marker = _text(roster.get("required_marker"), "required_marker")
    max_attempts = _int(roster.get("max_attempts"), "max_attempts", minimum=1, maximum=5)
    timeout_seconds = _int(roster.get("timeout_seconds"), "timeout_seconds", minimum=1, maximum=600)
    max_workers = _int(roster.get("max_workers"), "max_workers", minimum=1, maximum=32)
    agents = roster.get("agents")
    if not isinstance(agents, list) or not 1 <= len(agents) <= 256:
        raise ZipJobRefusal("REFUSE_MD_AGENT_ROSTER_SCHEMA", "agents")
    shared = _path_list(roster.get("shared_paths") or [], "shared_paths", maximum=64)
    for path in shared:
        if path not in workspace:
            raise ZipJobRefusal("REFUSE_MD_AGENT_FILE_MISSING", path)
    if any(not isinstance(row, dict) for row in agents):
        raise ZipJobRefusal("REFUSE_MD_AGENT_ROSTER_SCHEMA", "agent")
    allowed_agent_fields = {
        "agent_id", "agent_path", "output_path", "provider", "model_requested",
        "fixture_script", "mmm_paths", "skill_paths", "context_paths",
        "required_fragments", "forbidden_fragments", "max_output_bytes", "reasoning_effort", "budget_usd",
        "max_turns", "runner_path", "bridge_path", "codex_home", "controller_src",
        "output_delivery", "output_format", "model_observed_allowlist"
    }
    if any(set(row) - allowed_agent_fields for row in agents):
        raise ZipJobRefusal("REFUSE_MD_AGENT_ROSTER_SCHEMA", "agent_fields")
    for row in agents:
        provider = row.get("provider")
        if provider in _ADAPTER_MODULES:
            if not row.get("runner_path"):
                raise ZipJobRefusal("HOLD_LIVE_RUNNER_UNBOUND", str(provider))
            if provider == "codex-cli" and not row.get("codex_home"):
                raise ZipJobRefusal("HOLD_CODEX_HOME_UNBOUND", "CODEX_HOME")
            if provider == "claude-code" and not row.get("bridge_path"):
                raise ZipJobRefusal("HOLD_CLAUDE_BRIDGE_UNBOUND", "bridge_path")
    agent_ids = [_text(row.get("agent_id"), "agent_id") for row in agents]
    expected_outputs = [_text(row.get("output_path"), "output_path") for row in agents]
    agent_paths = [_text(row.get("agent_path"), "agent_path") for row in agents]
    if any(len(values) != len(set(values)) for values in (agent_ids, expected_outputs, agent_paths)):
        raise ZipJobRefusal("REFUSE_MD_AGENT_ROSTER_SCHEMA", "duplicate_agent_identity")
    expected_outputs.append("output/roster_receipt.json")
    if set(task.output_paths) != set(expected_outputs):
        raise ZipJobRefusal("REFUSE_OPERATION_ARITY", "output_set")
    def run_row(row: dict[str, Any]) -> dict[str, Any]:
        return _run_one(
            agent=row, workspace=workspace, shared_paths=list(shared), marker=marker,
            timeout_seconds=timeout_seconds, max_attempts=max_attempts,
            run_id=run_id, roster_seed=roster_seed, hierarchy=hierarchy,
        )

    with ThreadPoolExecutor(max_workers=min(max_workers, len(agents))) as pool:
        results = list(pool.map(run_row, agents))
    exhausted = [result for result in results if not result["accepted"]]
    if exhausted:
        refusal_reason_summary: dict[str, int] = {}
        for result in results:
            for reason, count in result.get("refusal_reason_summary", {}).items():
                refusal_reason_summary[reason] = refusal_reason_summary.get(reason, 0) + int(count)
        refusal = {
            **hierarchy_surface,
            "schema": "constraintbox.md-agent-roster-refusal.v1",
            "run_id": run_id,
            "seed": roster_seed,
            "max_attempts": max_attempts,
            "accepted_agent_ids": [result["agent_id"] for result in results if result["accepted"]],
            "accepted_attempt_count": sum(
                int(result.get("accepted_attempts", 0)) for result in results
            ),
            "accepted_attempts_consumed": sum(
                int(result.get("accepted_attempt_count", 0)) for result in results
            ),
            "refusal_reason_summary": refusal_reason_summary,
            "exhausted_agents": [
                {
                    **hierarchy_surface,
                    "agent_id": result["agent_id"],
                    "terminal_refusal": result["terminal_refusal"],
                    "accepted_attempt_count": result.get("accepted_attempt_count", 0),
                    "refusal_reason_summary": result.get("refusal_reason_summary", {}),
                    "attempts": result["attempts"],
                }
                for result in exhausted
            ],
            "return_zip_emitted": False,
            "host_hooks_used": False,
            "promotion_allowed": False,
        }
        raise ZipJobRefusal(
            "REFUSE_MD_AGENT_ROSTER_EXHAUSTED",
            canonical_json_bytes(refusal).decode("ascii"),
        )
    produced: dict[str, bytes] = {}
    receipts: list[dict[str, Any]] = []
    for result in results:
        produced[result["output_path"]] = result["output_bytes"]
        receipts.append({k: v for k, v in result.items() if k != "output_bytes"})
    refusal_reason_summary: dict[str, int] = {}
    for result in receipts:
        for reason, count in result.get("refusal_reason_summary", {}).items():
            refusal_reason_summary[reason] = refusal_reason_summary.get(reason, 0) + int(count)
    produced["output/roster_receipt.json"] = canonical_json_bytes(
        {
            **hierarchy_surface,
            "schema": RECEIPT_SCHEMA,
            "run_id": run_id,
            "seed": roster_seed,
            "required_marker": marker,
            "max_attempts": max_attempts,
            "max_workers": max_workers,
            "accepted_agent_ids": [row["agent_id"] for row in receipts],
            "accepted_attempt_count": sum(
                int(row.get("accepted_attempts", 0)) for row in receipts
            ),
            "accepted_attempts_consumed": sum(
                int(row.get("accepted_attempt_count", 0)) for row in receipts
            ),
            "attempt_count": sum(int(row.get("attempt_count", 0)) for row in receipts),
            "refusal_reason_summary": refusal_reason_summary,
            "agents": receipts,
            "execution_authorized_beyond_declared_outputs": False,
            "host_hooks_used": False,
            "mmm_read_proved": False,
            "skill_executed": False,
            "skill_bytes_delivered": all(
                bool(row.get("skill_bytes_delivered")) for row in receipts
            ),
            "skill_read_proved": False,
            # Deprecated legacy field.  Delivery is observed; consumption is
            # intentionally not inferred from a digest echo.
            "skill_bytes_consumed": None,
            "llm_invoked_tool": any(bool(row.get("llm_invoked_tool")) for row in receipts),
            "tool_request_observed": any(bool(row.get("tool_request_observed")) for row in receipts),
            "cb_tool_executed": any(bool(row.get("cb_tool_executed")) for row in receipts),
            "tool_result_consumed_on_later_attempt": any(
                bool(row.get("tool_result_consumed_on_later_attempt")) for row in receipts
            ),
            "provider_env_allowlisted": True,
            "promotion_allowed": False,
            "claim_ceiling": CLAIM_CEILING,
        }
    )
    return produced


def build_md_agent_roster_packet(
    *,
    roster: dict[str, Any],
    files: dict[str, bytes],
) -> bytes:
    from .failure_wave import _task

    if roster.get("schema") != ROSTER_SCHEMA:
        raise ZipJobRefusal("REFUSE_MD_AGENT_ROSTER_SCHEMA", "schema")
    _hierarchy_binding(roster)
    outputs = [str(row["output_path"]) for row in roster["agents"]]
    outputs.extend([TOOL_EVIDENCE_PATH, "output/roster_receipt.json"])
    packet_files = dict(files)
    if TOOL_PAYLOAD_PATH not in packet_files:
        packet_files[TOOL_PAYLOAD_PATH] = canonical_json_bytes(DEFAULT_TOOL_PAYLOAD)
    if "TOOLS/make_token.py" not in packet_files:
        from .zip_python_tool import DEFAULT_MAKE_TOKEN_PY

        packet_files["TOOLS/make_token.py"] = DEFAULT_MAKE_TOKEN_PY
    tool_task = "tasks/00_tool_evidence.task.json"
    roster_task = "tasks/01_run_md_agents.task.json"
    packet_files = {
        **packet_files,
        "00_RUN_ME_FIRST.md": (
            b"# MD agent roster ZIP\n\n"
            b"Each AGENTS/*.md file is an agent. CB launches it. "
            b"Only declared output files count. Missing or wrong files are refused.\n"
        ),
        "inputs/roster.json": canonical_json_bytes(roster),
        tool_task: _task(
            task_id="tool-evidence",
            sequence=0,
            operation="run_zip_python_tool_v1",
            inputs=["TOOLS/make_token.py", TOOL_PAYLOAD_PATH],
            outputs=[TOOL_EVIDENCE_PATH],
        ),
        roster_task: _task(
            task_id="run-md-agents",
            sequence=1,
            operation="run_md_agent_roster_v1",
            inputs=["inputs/roster.json", TOOL_EVIDENCE_PATH, *sorted(files)],
            outputs=[path for path in outputs if path != TOOL_EVIDENCE_PATH],
            depends_on=["tool-evidence"],
        ),
    }
    return build_packet(
        {
            "schema": "constraintbox.zip_job.v1",
            "job_id": "md-agent-roster",
            "task_execution_order": [tool_task, roster_task],
            "required_output_file_list": outputs,
            "allowed_operations": ["run_zip_python_tool_v1", "run_md_agent_roster_v1"],
            "allowed_child_job_ids": [],
            "max_child_depth": 0,
            "claim_ceiling": CLAIM_CEILING,
        },
        packet_files,
    )


===== FILE constraint_box/zip_agent/tests/test_md_agent_roster.py sha256=8b9a7ea853a3aa981c0304f3e69bbae99539a43a0a78730b17fafa9eb8d44dfb bytes=42950 =====
from __future__ import annotations

import io
import json
import zipfile

import pytest

import constraintbox_zip_agent.md_agent_roster as roster_module

from constraintbox_zip_agent.md_agent_roster import (
    _extract_provider_response,
    _output_delivery,
    _provider_env,
    _provider_evidence,
    _run_one,
    build_md_agent_roster_packet,
)
from constraintbox_zip_agent.protocol import ZipJobRefusal, sha256_bytes, validate_return_zip
from constraintbox_zip_agent.runtime import execute_packet

MARKER = "ZIP_MD_AGENT_LIVE"


def _response_workspace() -> dict[str, bytes]:
    tool_token = "a" * 64
    return {
        "AGENTS/one.md": b"Return the declared strict output.\n",
        "REFERENCES/mmm/voice.md": b"particular evidence only\n",
        "SKILLS/write-finding.md": b"write one bounded finding\n",
        "input/OBJECT.md": b"bounded object\n",
        "output/tool_evidence.json": json.dumps(
            {"schema": "constraintbox.tool-evidence.v1", "canonical_sha256": tool_token}
        ).encode(),
    }


def _response_agent() -> dict:
    return {
        "agent_id": "one",
        "agent_path": "AGENTS/one.md",
        "output_path": "output/one.md",
        "provider": "grok-cli",
        "model_requested": "grok-4.6",
        "output_delivery": "provider_response",
        "mmm_paths": ["REFERENCES/mmm/voice.md"],
        "skill_paths": ["SKILLS/write-finding.md"],
        "context_paths": ["input/OBJECT.md"],
        "required_fragments": ["finding:"],
        "forbidden_fragments": ["promotion_allowed: true"],
        "max_output_bytes": 8192,
    }


def _script(body: str) -> str:
    return (
        "from pathlib import Path\n"
        "import json, os, hashlib\n"
        "Path('output').mkdir(exist_ok=True)\n"
        "Path('meta').mkdir(exist_ok=True)\n"
        "Path('meta/provider_evidence.json').write_text(\n"
        "    json.dumps({'schema':'constraintbox.fixture-provider-evidence.v1',"
        "'disposition':'OBSERVED','model_observed':'fixture-observed'}) + '\\n',\n"
        "    encoding='utf-8',\n"
        ")\n"
        "token = json.loads(Path('output/tool_evidence.json').read_text(encoding='utf-8'))['canonical_sha256']\n"
        + body
        + "\n"
    )


def _roster(*agents: dict) -> dict:
    return {
        "schema": "constraintbox.md-agent-roster.v1",
        "run_id": "md-roster-unit",
        "seed": 42042,
        "required_marker": MARKER,
        "max_attempts": 2,
        "timeout_seconds": 30,
        "max_workers": 8,
        "shared_paths": ["input/OBJECT.md", "REFERENCES/mmm/voice.md"],
        "agents": list(agents),
    }


def _files() -> dict[str, bytes]:
    return {
        "AGENTS/one.md": b"role: one\noutput: output/one.md\nWrite the marker.\n",
        "AGENTS/two.md": b"role: two\noutput: output/two.md\nWrite the marker.\n",
        "input/OBJECT.md": b"Write the declared output file.\n",
        "REFERENCES/mmm/voice.md": b"plain particulars only\n",
        "SKILLS/write-finding.md": b"write only the declared markdown output\n",
    }


def _agent(agent_id: str, script: str, model: str = "fixture-model") -> dict:
    return {
        "agent_id": agent_id,
        "agent_path": f"AGENTS/{agent_id}.md",
        "output_path": f"output/{agent_id}.md",
        "provider": "fixture-subprocess",
        "model_requested": model,
        "fixture_script": _script(script),
        "mmm_paths": ["REFERENCES/mmm/voice.md"],
        "skill_paths": ["SKILLS/write-finding.md"],
        "context_paths": ["input/OBJECT.md"],
        "required_fragments": ["finding:"],
        "max_output_bytes": 4096,
    }


def _packet(*scripts: str) -> bytes:
    ids = ("one", "two")
    agents = [_agent(agent_id, script) for agent_id, script in zip(ids, scripts, strict=True)]
    return build_md_agent_roster_packet(roster=_roster(*agents), files=_files())


def _hierarchy_roster(*agents: dict, **binding: object) -> dict:
    roster = _roster(*agents)
    roster.update(
        {
            "parent_id": "parent-run",
            "wave_id": "wave-7",
            "round": 3,
            "depth": 2,
            **binding,
        }
    )
    return roster


def _receipt_for(roster: dict) -> dict:
    packet = build_md_agent_roster_packet(roster=roster, files=_files())
    result = execute_packet(packet)
    with zipfile.ZipFile(io.BytesIO(result.return_zip_bytes)) as archive:
        return json.loads(archive.read("output/roster_receipt.json"))


def _ok(agent_id: str) -> str:
    return (
        "skill = hashlib.sha256(Path('SKILLS/write-finding.md').read_bytes()).hexdigest()\n"
        f"Path('output/{agent_id}.md').write_text("
        f"'finding: ZIP_MD_AGENT_LIVE\\ntool-token: ' + token + '\\nskill-token: ' + skill + '\\n', encoding='utf-8')"
    )


def test_two_md_agents_write_declared_files() -> None:
    packet = _packet(_ok("one"), _ok("two"))
    result = execute_packet(packet)
    validate_return_zip(
        result.return_zip_bytes,
        expected_input_sha256=result.input_packet_sha256,
        input_packet_bytes=packet,
    )
    with zipfile.ZipFile(io.BytesIO(result.return_zip_bytes)) as archive:
        one = archive.read("output/one.md").decode("utf-8")
        two = archive.read("output/two.md").decode("utf-8")
        assert one.startswith("finding: ZIP_MD_AGENT_LIVE")
        assert two.startswith("finding: ZIP_MD_AGENT_LIVE")
        assert "tool-token:" in one and "tool-token:" in two
        receipt = archive.read("output/roster_receipt.json")
    assert b'"accepted_agent_ids":["one","two"]' in receipt.replace(b" ", b"")
    assert result.return_zip_bytes == execute_packet(packet).return_zip_bytes
    with zipfile.ZipFile(io.BytesIO(result.return_zip_bytes)) as archive:
        surface = json.loads(archive.read("output/roster_receipt.json"))
        assert archive.read("output/tool_evidence.json")
        assert all(row["model_observed"] == "fixture-observed" for row in surface["agents"])
        assert all(row["identity_source"] == "fixture" for row in surface["agents"])
        assert all(row["tool_evidence_sha256"] for row in surface["agents"])
        assert surface["hierarchy_bound"] is False


def test_hierarchy_bound_depth_two_receipt_binds_every_row() -> None:
    receipt = _receipt_for(_hierarchy_roster(_agent("one", _ok("one"))))

    assert receipt["hierarchy_bound"] is True
    assert receipt["parent_id"] == "parent-run"
    assert receipt["wave_id"] == "wave-7"
    assert receipt["round"] == 3
    assert receipt["depth"] == 2
    for agent in receipt["agents"]:
        assert agent["hierarchy_bound"] is True
        assert agent["parent_id"] == receipt["parent_id"]
        assert agent["wave_id"] == receipt["wave_id"]
        assert agent["round"] == receipt["round"]
        assert agent["depth"] == receipt["depth"]
        for attempt in agent["attempts"]:
            assert attempt["hierarchy_bound"] is True
            assert attempt["parent_id"] == receipt["parent_id"]
            assert attempt["wave_id"] == receipt["wave_id"]
            assert attempt["round"] == receipt["round"]
            assert attempt["depth"] == receipt["depth"]


@pytest.mark.parametrize(
    "binding",
    [
        {"parent_id": "parent-run", "wave_id": "wave-7", "round": 3},
        {"parent_id": None, "wave_id": "wave-7", "round": 3, "depth": 2},
        {"parent_id": "parent-run", "wave_id": "wave-7", "round": -1, "depth": 2},
        {"parent_id": "parent-run", "wave_id": "wave-7", "round": 3, "depth": 9},
    ],
)
def test_hierarchy_binding_missing_or_invalid_fields_is_refused(binding: dict[str, object]) -> None:
    roster = _roster(_agent("one", _ok("one")))
    roster.update(binding)
    with pytest.raises(ZipJobRefusal) as caught:
        build_md_agent_roster_packet(roster=roster, files=_files())
    assert caught.value.reason_code == "REFUSE_MD_AGENT_ROSTER_SCHEMA"


def test_hierarchy_parent_and_depth_change_provider_request_identity() -> None:
    parent = _receipt_for(_hierarchy_roster(_agent("one", _ok("one")), parent_id="parent-a"))
    other_parent = _receipt_for(
        _hierarchy_roster(_agent("one", _ok("one")), parent_id="parent-b")
    )
    other_depth = _receipt_for(
        _hierarchy_roster(_agent("one", _ok("one")), depth=3)
    )

    parent_request_id = parent["agents"][0]["attempts"][0]["provider_request_id"]
    assert parent_request_id != other_parent["agents"][0]["attempts"][0]["provider_request_id"]
    assert parent_request_id != other_depth["agents"][0]["attempts"][0]["provider_request_id"]


def test_failed_first_attempt_retries_then_accepts() -> None:
    retry = (
        "if os.environ.get('CB_ZIP_ATTEMPT') == '1':\n"
        "    raise SystemExit(1)\n"
        "skill = hashlib.sha256(Path('SKILLS/write-finding.md').read_bytes()).hexdigest()\n"
        "Path('output/one.md').write_text('finding: ZIP_MD_AGENT_LIVE\\ntool-token: ' + token + '\\nskill-token: ' + skill + '\\n', encoding='utf-8')"
    )
    packet = _packet(retry, _ok("two"))
    result = execute_packet(packet)
    validate_return_zip(result.return_zip_bytes, expected_input_sha256=result.input_packet_sha256)
    with zipfile.ZipFile(io.BytesIO(result.return_zip_bytes)) as archive:
        import json

        receipt = json.loads(archive.read("output/roster_receipt.json"))
    assert receipt["agents"][0]["attempts"][0]["output_present"] is False
    assert receipt["agents"][0]["attempts"][1]["marker_present"] is True


def test_missing_output_after_retries_is_refused() -> None:
    packet = _packet("pass", _ok("two"))
    with pytest.raises(ZipJobRefusal) as caught:
        execute_packet(packet)
    assert caught.value.reason_code == "REFUSE_MD_AGENT_ROSTER_EXHAUSTED"
    refusal = json.loads(caught.value.detail)
    assert refusal["return_zip_emitted"] is False
    assert refusal["exhausted_agents"][0]["terminal_refusal"] == "REFUSE_MD_AGENT_MISSING_OUTPUT"
    assert len(refusal["exhausted_agents"][0]["attempts"]) == 2


def test_wrong_marker_is_refused() -> None:
    packet = _packet(
        "Path('output/one.md').write_text('finding: nope\\n', encoding='utf-8')",
        _ok("two"),
    )
    with pytest.raises(ZipJobRefusal) as caught:
        execute_packet(packet)
    assert caught.value.reason_code == "REFUSE_MD_AGENT_ROSTER_EXHAUSTED"
    refusal = json.loads(caught.value.detail)
    assert refusal["exhausted_agents"][0]["terminal_refusal"] == "REFUSE_MD_AGENT_MARKER_MISSING"


def test_missing_required_format_retries_then_refuses() -> None:
    packet = _packet(
        "Path('output/one.md').write_text('ZIP_MD_AGENT_LIVE\\n', encoding='utf-8')",
        _ok("two"),
    )
    with pytest.raises(ZipJobRefusal) as caught:
        execute_packet(packet)
    assert caught.value.reason_code == "REFUSE_MD_AGENT_ROSTER_EXHAUSTED"
    refusal = json.loads(caught.value.detail)
    assert refusal["exhausted_agents"][0]["terminal_refusal"] == "REFUSE_MD_AGENT_FORMAT_MISSING"
    attempt = refusal["exhausted_agents"][0]["attempts"][0]
    assert attempt["missing_fragments"]
    assert attempt["output_preview"] == "ZIP_MD_AGENT_LIVE\n"


def test_controller_prompt_lists_every_required_fragment() -> None:
    from constraintbox_zip_agent.md_agent_roster import _prompt

    prompt = _prompt(
        "AGENTS/one.md",
        "output/one.md",
        MARKER,
        mmm_paths=["REFERENCES/mmm/voice.md"],
        skill_paths=["SKILLS/write-finding.md"],
        context_paths=["input/OBJECT.md"],
        required_fragments=["evidence:", "limit:"],
        forbidden_fragments=[],
        attempt=1,
        attempt_seed="abc",
        prior_refusal=None,
    )
    assert "- evidence:" in prompt
    assert "- limit:" in prompt


def test_128_stateless_fixture_agents_are_gated_and_replay_identically() -> None:
    count = 128
    agents = []
    files = {
        "input/OBJECT.md": b"Write the declared output file.\n",
        "REFERENCES/mmm/voice.md": b"plain particulars only\n",
        "SKILLS/write-finding.md": b"write only the declared markdown output\n",
    }
    for index in range(count):
        agent_id = f"agent-{index:03d}"
        output_path = f"output/{agent_id}.md"
        files[f"AGENTS/{agent_id}.md"] = (
            f"role: {agent_id}\noutput: {output_path}\nWrite the marker.\n".encode()
        )
        agents.append(
            {
                "agent_id": agent_id,
                "agent_path": f"AGENTS/{agent_id}.md",
                "output_path": output_path,
                "provider": "fixture-subprocess",
                "model_requested": "fixture-model",
                "fixture_script": _script(
                    (
                        "if os.environ.get('CB_ZIP_ATTEMPT') == '1':\n"
                        f"    Path('{output_path}').write_text('finding: wrong {agent_id}\\n', encoding='utf-8')\n"
                        "else:\n"
                        f"    Path('{output_path}').write_text('finding: {MARKER} {agent_id}\\ntool-token: ' + token + '\\nskill-token: ' + hashlib.sha256(Path('SKILLS/write-finding.md').read_bytes()).hexdigest() + '\\n', encoding='utf-8')"
                    )
                    if index == count - 1
                    else f"Path('{output_path}').write_text('finding: {MARKER} {agent_id}\\ntool-token: ' + token + '\\nskill-token: ' + hashlib.sha256(Path('SKILLS/write-finding.md').read_bytes()).hexdigest() + '\\n', encoding='utf-8')"
                ),
                "mmm_paths": ["REFERENCES/mmm/voice.md"],
                "skill_paths": ["SKILLS/write-finding.md"],
                "context_paths": ["input/OBJECT.md"],
                "required_fragments": ["finding:", agent_id],
                "max_output_bytes": 4096,
            }
        )
    roster = {
        "schema": "constraintbox.md-agent-roster.v1",
        "run_id": "md-roster-128",
        "seed": 128042,
        "required_marker": MARKER,
        "max_attempts": 2,
        "timeout_seconds": 30,
        "max_workers": 16,
        "shared_paths": [],
        "agents": agents,
    }
    packet = build_md_agent_roster_packet(roster=roster, files=files)
    first = execute_packet(packet)
    second = execute_packet(packet)
    assert first.return_zip_bytes == second.return_zip_bytes
    with zipfile.ZipFile(io.BytesIO(first.return_zip_bytes)) as archive:
        receipt = json.loads(archive.read("output/roster_receipt.json"))
        assert len(receipt["accepted_agent_ids"]) == count
        assert len(receipt["agents"]) == count
        assert all(row["attempts"][0]["refusal_reason"] is None for row in receipt["agents"][:-1])
        assert receipt["agents"][-1]["attempts"][0]["refusal_reason"] == "REFUSE_MD_AGENT_MARKER_MISSING"
        assert receipt["agents"][-1]["accepted_attempt"] == 2
        assert all(len(row["delivered_file_sha256"]) == 5 for row in receipt["agents"])


def test_required_agent_exhaustion_rejects_parent_with_structured_attempt_evidence() -> None:
    agents = [
        _agent("one", _ok("one")),
        _agent("two", "pass"),
    ]
    packet = build_md_agent_roster_packet(roster=_roster(*agents), files=_files())
    with pytest.raises(ZipJobRefusal) as caught:
        execute_packet(packet)
    assert caught.value.reason_code == "REFUSE_MD_AGENT_ROSTER_EXHAUSTED"
    refusal = json.loads(caught.value.detail)
    assert refusal["accepted_agent_ids"] == ["one"]
    assert refusal["return_zip_emitted"] is False
    assert [row["agent_id"] for row in refusal["exhausted_agents"]] == ["two"]
    assert len(refusal["exhausted_agents"][0]["attempts"]) == 2


def test_agent_file_digest_is_bound_into_the_packet() -> None:
    packet = _packet(_ok("one"), _ok("two"))
    files = _files()
    assert sha256_bytes(files["AGENTS/one.md"])
    result = execute_packet(packet)
    assert result.input_packet_sha256 == sha256_bytes(packet)


def test_adapter_receipt_binds_request_model_prompt_and_source_bytes(tmp_path) -> None:
    prompt = b"exact composed prompt\n"
    source = {
        "schema": "constraintbox.codex-cli-receipt.v1",
        "request_id": "zip-request-1",
        "model_requested": "gpt-5.6-luna",
        "model_observed": "gpt-5.6-luna",
        "model_binding_confirmed": True,
        "prompt_sha256": sha256_bytes(prompt),
        "disposition": "OBSERVED",
    }
    receipt_path = tmp_path / "provider.json"
    receipt_path.write_text(json.dumps(source), encoding="utf-8")
    evidence = _provider_evidence(
        provider="codex-cli",
        evidence_path=receipt_path,
        request_id="zip-request-1",
        model_requested="gpt-5.6-luna",
        prompt=prompt,
    )
    assert evidence["model_observed"] == ["gpt-5.6-luna"]
    assert evidence["model_binding_confirmed"] is True
    assert evidence["provider_source_receipt_sha256"] == sha256_bytes(receipt_path.read_bytes())
    assert evidence["provider_source_receipt"] == source


@pytest.mark.parametrize("field,value", [
    ("request_id", "wrong"),
    ("model_binding_confirmed", False),
    ("prompt_sha256", "0" * 64),
])
def test_adapter_receipt_mismatch_is_refused(tmp_path, field: str, value: object) -> None:
    prompt = b"exact composed prompt\n"
    source = {
        "schema": "constraintbox.grok-cli-receipt.v1",
        "request_id": "zip-request-2",
        "model_requested": "grok-4.6",
        "models_observed_in_output": ["grok-4.6-build"],
        "model_binding_confirmed": True,
        "prompt_sha256": sha256_bytes(prompt),
        "disposition": "OBSERVED",
    }
    source[field] = value
    receipt_path = tmp_path / "provider.json"
    receipt_path.write_text(json.dumps(source), encoding="utf-8")
    with pytest.raises(ZipJobRefusal) as caught:
        _provider_evidence(
            provider="grok-cli",
            evidence_path=receipt_path,
            request_id="zip-request-2",
            model_requested="grok-4.6",
            prompt=prompt,
        )
    assert caught.value.reason_code == "REFUSE_MD_AGENT_PROVIDER_EVIDENCE"


def test_tool_pretask_output_is_delivered_and_bound_to_each_worker() -> None:
    files = _files()
    files["inputs/tool_payload.json"] = b'{"z":1,"a":[3,2,1]}'
    packet = build_md_agent_roster_packet(
        roster=_roster(_agent("one", _ok("one")), _agent("two", _ok("two"))),
        files=files,
    )
    result = execute_packet(packet)
    with zipfile.ZipFile(io.BytesIO(result.return_zip_bytes)) as archive:
        evidence = archive.read("output/tool_evidence.json")
        receipt = json.loads(archive.read("output/roster_receipt.json"))
    digest = sha256_bytes(evidence)
    assert all(
        row["delivered_file_sha256"]["output/tool_evidence.json"] == digest
        for row in receipt["agents"]
    )
    assert receipt["host_hooks_used"] is False
    assert receipt["mmm_read_proved"] is False
    assert receipt["skill_executed"] is False
    assert receipt["llm_invoked_tool"] is False
    assert "not_host_hook" in receipt["claim_ceiling"]
    assert result.return_zip_bytes == execute_packet(packet).return_zip_bytes


def test_missing_tool_token_is_refused_even_when_file_and_marker_exist() -> None:
    one = _agent(
        "one",
        "Path('output/one.md').write_text('finding: ZIP_MD_AGENT_LIVE\\n', encoding='utf-8')",
    )
    packet = build_md_agent_roster_packet(
        roster=_roster(one, _agent("two", _ok("two"))),
        files=_files(),
    )
    with pytest.raises(ZipJobRefusal) as caught:
        execute_packet(packet)
    assert caught.value.reason_code == "REFUSE_MD_AGENT_ROSTER_EXHAUSTED"
    refusal = json.loads(caught.value.detail)
    assert refusal["exhausted_agents"][0]["terminal_refusal"] == "REFUSE_MD_AGENT_TOOL_TOKEN_MISSING"
    assert refusal["host_hooks_used"] is False


def test_wrong_run_tool_token_is_refused() -> None:
    one = _agent(
        "one",
        "Path('output/one.md').write_text("
        "'finding: ZIP_MD_AGENT_LIVE\\ntool-token: ' + ('0' * 64) + '\\n', encoding='utf-8')",
    )
    packet = build_md_agent_roster_packet(
        roster=_roster(one, _agent("two", _ok("two"))),
        files=_files(),
    )
    with pytest.raises(ZipJobRefusal) as caught:
        execute_packet(packet)
    assert caught.value.reason_code == "REFUSE_MD_AGENT_ROSTER_EXHAUSTED"
    refusal = json.loads(caught.value.detail)
    assert refusal["exhausted_agents"][0]["terminal_refusal"] == "REFUSE_MD_AGENT_TOOL_TOKEN_MISSING"


def test_live_provider_env_does_not_copy_host_secrets(monkeypatch) -> None:
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "should-not-pass")
    monkeypatch.setenv("GH_TOKEN", "should-not-pass")
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "should-not-pass")
    monkeypatch.setenv("OPENAI_API_KEY", "codex-ok")
    env = _provider_env("codex-cli")
    assert "AWS_SECRET_ACCESS_KEY" not in env
    assert "GH_TOKEN" not in env
    assert "TELEGRAM_BOT_TOKEN" not in env
    assert env["OPENAI_API_KEY"] == "codex-ok"
    assert "CODEX_HOME" not in env
    grok_env = _provider_env("grok-cli")
    assert "OPENAI_API_KEY" not in grok_env
    assert "AWS_SECRET_ACCESS_KEY" not in grok_env
    monkeypatch.setenv("XAI_API_KEY", "should-not-pass")
    monkeypatch.setenv("GROK_API_KEY", "should-not-pass")
    grok_env = _provider_env("grok-cli")
    assert "XAI_API_KEY" not in grok_env
    assert "GROK_API_KEY" not in grok_env


def test_worker_tool_request_requires_later_attempt_to_consume_result() -> None:
    asked = (
        "payload = {'asked': True, 'n': 7}\n"
        "if os.environ['CB_ZIP_ATTEMPT'] == '1':\n"
        "    Path('output/tool_request.json').write_text(\n"
        "        json.dumps({'schema': 'constraintbox.md-agent-tool-request.v1',"
        " 'script_path': 'TOOLS/make_token.py', 'payload': payload}),\n"
        "        encoding='utf-8',\n"
        "    )\n"
        "skill = hashlib.sha256(Path('SKILLS/write-finding.md').read_bytes()).hexdigest()\n"
        "Path('output/one.md').write_text("
        "'finding: ZIP_MD_AGENT_LIVE\\ntool-token: ' + token + '\\nskill-token: ' + skill + '\\n', encoding='utf-8')\n"
    )
    packet = build_md_agent_roster_packet(
        roster=_roster(_agent("one", asked), _agent("two", _ok("two"))),
        files=_files(),
    )
    result = execute_packet(packet)
    with zipfile.ZipFile(io.BytesIO(result.return_zip_bytes)) as archive:
        receipt = json.loads(archive.read("output/roster_receipt.json"))
        one = archive.read("output/one.md").decode("utf-8")
    assert receipt["llm_invoked_tool"] is False
    assert receipt["tool_request_observed"] is True
    assert receipt["cb_tool_executed"] is True
    assert receipt["tool_result_consumed_on_later_attempt"] is True
    assert receipt["agents"][0]["accepted_attempt"] == 2
    assert receipt["agents"][0]["attempts"][0]["refusal_reason"] == "HOLD_MD_AGENT_TOOL_APPLIED_NEED_REWRITE"
    assert receipt["agents"][0]["llm_invoked_tool"] is False
    assert receipt["agents"][0]["cb_tool_executed"] is True
    assert receipt["agents"][0]["tool_result_consumed_on_later_attempt"] is True
    assert receipt["agents"][1]["llm_invoked_tool"] is False
    assert "tool-token:" in one


def test_worker_cannot_precompute_tool_result_and_accept_same_attempt() -> None:
    asked = (
        "payload = {'asked': True, 'n': 7}\n"
        "Path('output/tool_request.json').write_text(\n"
        "    json.dumps({'schema': 'constraintbox.md-agent-tool-request.v1',"
        " 'script_path': 'TOOLS/make_token.py', 'payload': payload}), encoding='utf-8')\n"
        "canonical = json.dumps(payload, sort_keys=True, separators=(',', ':'), ensure_ascii=True)\n"
        "predicted = hashlib.sha256(canonical.encode('utf-8')).hexdigest()\n"
        "skill = hashlib.sha256(Path('SKILLS/write-finding.md').read_bytes()).hexdigest()\n"
        "Path('output/one.md').write_text("
        "'finding: ZIP_MD_AGENT_LIVE\\ntool-token: ' + predicted + '\\nskill-token: ' + skill + '\\n', encoding='utf-8')\n"
    )
    roster = _roster(_agent("one", asked), _agent("two", _ok("two")))
    roster["max_attempts"] = 1
    packet = build_md_agent_roster_packet(roster=roster, files=_files())
    with pytest.raises(ZipJobRefusal) as caught:
        execute_packet(packet)
    refusal = json.loads(caught.value.detail)
    assert caught.value.reason_code == "REFUSE_MD_AGENT_ROSTER_EXHAUSTED"
    assert refusal["exhausted_agents"][0]["terminal_refusal"] == "HOLD_MD_AGENT_TOOL_APPLIED_NEED_REWRITE"


def test_worker_tool_request_missing_script_is_refused() -> None:
    bad = (
        "Path('output/tool_request.json').write_text(\n"
        "    json.dumps({'schema': 'constraintbox.md-agent-tool-request.v1',"
        " 'script_path': 'TOOLS/missing.py', 'payload': {'x': 1}}),\n"
        "    encoding='utf-8',\n"
        ")\n"
        "Path('output/one.md').write_text('finding: ZIP_MD_AGENT_LIVE\\ntool-token: ' + token + '\\n', encoding='utf-8')\n"
    )
    packet = build_md_agent_roster_packet(
        roster=_roster(_agent("one", bad), _agent("two", _ok("two"))),
        files=_files(),
    )
    with pytest.raises(ZipJobRefusal) as caught:
        execute_packet(packet)
    assert caught.value.reason_code == "REFUSE_MD_AGENT_ROSTER_EXHAUSTED"
    refusal = json.loads(caught.value.detail)
    assert refusal["exhausted_agents"][0]["terminal_refusal"] == "REFUSE_MD_AGENT_TOOL_REQUEST"


def test_missing_skill_token_is_refused() -> None:
    one = _agent(
        "one",
        "Path('output/one.md').write_text('finding: ZIP_MD_AGENT_LIVE\\ntool-token: ' + token + '\\n', encoding='utf-8')",
    )
    packet = build_md_agent_roster_packet(
        roster=_roster(one, _agent("two", _ok("two"))),
        files=_files(),
    )
    with pytest.raises(ZipJobRefusal) as caught:
        execute_packet(packet)
    assert json.loads(caught.value.detail)["exhausted_agents"][0]["terminal_refusal"] == "REFUSE_MD_AGENT_SKILL_TOKEN_MISSING"


def test_extra_undeclared_workspace_file_is_refused() -> None:
    extra = (
        "skill = hashlib.sha256(Path('SKILLS/write-finding.md').read_bytes()).hexdigest()\n"
        "Path('output/one.md').write_text('finding: ZIP_MD_AGENT_LIVE\\ntool-token: ' + token + '\\nskill-token: ' + skill + '\\n', encoding='utf-8')\n"
        "Path('meta').mkdir(exist_ok=True)\n"
        "Path('meta/sneak.md').write_text('nope\\n', encoding='utf-8')\n"
    )
    packet = build_md_agent_roster_packet(
        roster=_roster(_agent("one", extra), _agent("two", _ok("two"))),
        files=_files(),
    )
    with pytest.raises(ZipJobRefusal) as caught:
        execute_packet(packet)
    assert json.loads(caught.value.detail)["exhausted_agents"][0]["terminal_refusal"] == "REFUSE_MD_AGENT_EXTRA_OUTPUT"


def test_extra_undeclared_output_is_refused() -> None:
    extra = (
        "skill = hashlib.sha256(Path('SKILLS/write-finding.md').read_bytes()).hexdigest()\n"
        "Path('output/one.md').write_text('finding: ZIP_MD_AGENT_LIVE\\ntool-token: ' + token + '\\nskill-token: ' + skill + '\\n', encoding='utf-8')\n"
        "Path('output/sneak.md').write_text('nope\\n', encoding='utf-8')\n"
    )
    packet = build_md_agent_roster_packet(
        roster=_roster(_agent("one", extra), _agent("two", _ok("two"))),
        files=_files(),
    )
    with pytest.raises(ZipJobRefusal) as caught:
        execute_packet(packet)
    assert json.loads(caught.value.detail)["exhausted_agents"][0]["terminal_refusal"] == "REFUSE_MD_AGENT_EXTRA_OUTPUT"


def test_host_hook_requirement_holds_live_provider(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("CB_REQUIRE_HOST_HOOK", "1")
    from constraintbox_zip_agent.md_agent_roster import _argv

    with pytest.raises(ZipJobRefusal) as caught:
        _argv(
            {"provider": "codex-cli", "model_requested": "gpt-5.6-luna"},
            tmp_path,
            tmp_path / "prompt.md",
            request_id="x",
            timeout_seconds=5,
        )
    assert caught.value.reason_code == "HOLD_HOST_HOOK_REQUIRED"


def test_unmanaged_live_launch_holds_without_process_box_nonce(tmp_path) -> None:
    from constraintbox_zip_agent.md_agent_roster import _argv

    with pytest.raises(ZipJobRefusal) as caught:
        _argv(
            {"provider": "grok-cli", "model_requested": "grok-4.6"},
            tmp_path,
            tmp_path / "prompt.md",
            request_id="x",
            timeout_seconds=5,
        )
    assert caught.value.reason_code == "HOLD_HOST_HOOK_REQUIRED"


def test_forged_dispatch_nonce_without_file_is_held(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("CB_DISPATCH_NONCE", "forged")
    monkeypatch.delenv("CB_DISPATCH_NONCE_FILE", raising=False)
    from constraintbox_zip_agent.md_agent_roster import _argv

    with pytest.raises(ZipJobRefusal) as caught:
        _argv(
            {"provider": "grok-cli", "model_requested": "grok-4.6"},
            tmp_path,
            tmp_path / "prompt.md",
            request_id="x",
            timeout_seconds=5,
        )
    assert caught.value.reason_code == "HOLD_DISPATCH_NONCE_UNBOUND"


def test_dispatch_nonce_mismatch_is_held(monkeypatch, tmp_path) -> None:
    nonce = tmp_path / "dispatch.nonce"
    nonce.write_text("box-nonce\n", encoding="utf-8")
    monkeypatch.setenv("CB_DISPATCH_NONCE", "forged")
    monkeypatch.setenv("CB_DISPATCH_NONCE_FILE", str(nonce))
    from constraintbox_zip_agent.md_agent_roster import _argv

    with pytest.raises(ZipJobRefusal) as caught:
        _argv(
            {"provider": "grok-cli", "model_requested": "grok-4.6"},
            tmp_path,
            tmp_path / "prompt.md",
            request_id="x",
            timeout_seconds=5,
        )
    assert caught.value.reason_code == "HOLD_DISPATCH_NONCE_MISMATCH"


def test_codex_home_unbound_is_held(monkeypatch, tmp_path) -> None:
    monkeypatch.delenv("CODEX_HOME", raising=False)
    nonce = tmp_path / "dispatch.nonce"
    nonce.write_text("test-nonce\n", encoding="utf-8")
    monkeypatch.setenv("CB_DISPATCH_NONCE", "test-nonce")
    monkeypatch.setenv("CB_DISPATCH_NONCE_FILE", str(nonce))
    from constraintbox_zip_agent.md_agent_roster import _argv

    with pytest.raises(ZipJobRefusal) as caught:
        _argv(
            {
                "provider": "codex-cli",
                "model_requested": "gpt-5.6-luna",
                "runner_path": "/usr/local/bin/codex",
            },
            tmp_path,
            tmp_path / "prompt.md",
            request_id="x",
            timeout_seconds=5,
        )
    assert caught.value.reason_code == "HOLD_PROVIDER_CONTROLLER_UNBOUND"


def test_live_provider_without_runner_is_held(monkeypatch, tmp_path) -> None:
    nonce = tmp_path / "dispatch.nonce"
    nonce.write_text("test-nonce\n", encoding="utf-8")
    monkeypatch.setenv("CB_DISPATCH_NONCE", "test-nonce")
    monkeypatch.setenv("CB_DISPATCH_NONCE_FILE", str(nonce))
    from constraintbox_zip_agent.md_agent_roster import _argv

    with pytest.raises(ZipJobRefusal) as caught:
        _argv(
            {
                "provider": "grok-cli",
                "model_requested": "grok-4.6",
            },
            tmp_path,
            tmp_path / "prompt.md",
            request_id="x",
            timeout_seconds=5,
        )
    assert caught.value.reason_code == "HOLD_PROVIDER_CONTROLLER_UNBOUND"


def test_provider_response_extractors_bind_current_adapter_artifacts(tmp_path) -> None:
    codex_path = (tmp_path / "codex.jsonl").resolve()
    codex_message = "codex response"
    codex_path.write_text(
        json.dumps(
            {
                "type": "item.completed",
                "item": {"type": "agent_message", "text": codex_message},
            }
        )
        + "\n",
        encoding="utf-8",
    )
    codex_raw = codex_path.read_bytes()
    body, source, raw_sha = _extract_provider_response(
        provider="codex-cli",
        source={
            "response_path": str(codex_path),
            "stdout_sha256": sha256_bytes(codex_raw),
            "agent_messages": [codex_message],
            "final_agent_message_sha256": sha256_bytes(codex_message.encode()),
        },
        work=tmp_path,
    )
    assert body == codex_message.encode()
    assert "agent_message" in source
    assert raw_sha == sha256_bytes(codex_raw)

    grok_path = (tmp_path / "grok.json").resolve()
    grok_message = "grok response"
    grok_path.write_text(
        json.dumps({"text": grok_message, "stopReason": "end_turn"}),
        encoding="utf-8",
    )
    grok_raw = grok_path.read_bytes()
    body, source, raw_sha = _extract_provider_response(
        provider="grok-cli",
        source={
            "response_path": str(grok_path),
            "response_sha256": sha256_bytes(grok_raw),
            "result_text_sha256": sha256_bytes(grok_message.encode()),
        },
        work=tmp_path,
    )
    assert body == grok_message.encode()
    assert source.endswith(":text")
    assert raw_sha == sha256_bytes(grok_raw)

    claude_path = (tmp_path / "claude.txt").resolve()
    claude_path.write_text(
        json.dumps(
            {
                "is_error": False,
                "subtype": "success",
                "terminal_reason": "completed",
                "result": "claude response",
            }
        ),
        encoding="utf-8",
    )
    body, source, raw_sha = _extract_provider_response(
        provider="claude-code",
        source={
            "nested_output_path": str(claude_path),
            "nested_output_sha256": sha256_bytes(claude_path.read_bytes()),
        },
        work=tmp_path,
    )
    assert body == b"claude response"
    assert source.endswith(":result")
    assert raw_sha == sha256_bytes(claude_path.read_bytes())


def test_provider_response_extractor_refuses_tamper_and_uncontained_path(tmp_path) -> None:
    response = (tmp_path / "grok.json").resolve()
    response.write_text(json.dumps({"text": "x", "stopReason": "end_turn"}), encoding="utf-8")
    with pytest.raises(ZipJobRefusal) as tampered:
        _extract_provider_response(
            provider="grok-cli",
            source={
                "response_path": str(response),
                "response_sha256": "0" * 64,
                "result_text_sha256": sha256_bytes(b"x"),
            },
            work=tmp_path,
        )
    assert tampered.value.reason_code == "REFUSE_MD_AGENT_PROVIDER_RESPONSE_TAMPER"
    outside = (tmp_path.parent / "outside-response.json").resolve()
    outside.write_text(json.dumps({"text": "x", "stopReason": "end_turn"}), encoding="utf-8")
    with pytest.raises(ZipJobRefusal) as uncontained:
        _extract_provider_response(
            provider="grok-cli",
            source={
                "response_path": str(outside),
                "response_sha256": sha256_bytes(outside.read_bytes()),
                "result_text_sha256": sha256_bytes(b"x"),
            },
            work=tmp_path,
        )
    assert uncontained.value.reason_code == "REFUSE_MD_AGENT_PROVIDER_RESPONSE_UNCONTAINED"


def test_provider_response_is_materialized_by_cb_and_replays(monkeypatch) -> None:
    workspace = _response_workspace()
    agent = _response_agent()

    def fake_argv(agent_row, work, prompt_path, **kwargs):
        prompt_text = prompt_path.read_text(encoding="utf-8")
        assert "BEGIN DECLARED ZIP INPUTS" in prompt_text
        assert "bounded object" in prompt_text
        assert sha256_bytes(workspace["input/OBJECT.md"]) in prompt_text
        assert "END DECLARED ZIP INPUTS" in prompt_text
        tool = json.loads((work / "output/tool_evidence.json").read_text())["canonical_sha256"]
        skill = sha256_bytes((work / "SKILLS/write-finding.md").read_bytes())
        text = (
            f"finding: {MARKER}\n"
            f"tool-token: {tool}\n"
            f"skill-token: {skill}\n"
        )
        response = work / "meta/provider_response.json"
        response.write_text(json.dumps({"text": text, "stopReason": "end_turn"}), encoding="utf-8")
        receipt = work / "meta/provider_receipt.json"
        receipt.write_text("{}", encoding="utf-8")
        return [roster_module.sys.executable, "-c", "pass"], dict(roster_module.os.environ), receipt

    def fake_evidence(*, evidence_path, request_id, model_requested, prompt, **_kwargs):
        response = evidence_path.with_name("provider_response.json")
        raw = response.read_bytes()
        text = json.loads(raw)["text"]
        source = {
            "response_path": str(response.resolve()),
            "response_sha256": sha256_bytes(raw),
            "result_text_sha256": sha256_bytes(text.encode()),
        }
        return {
            "provider_request_id": request_id,
            "model_observed": [model_requested],
            "model_binding_confirmed": True,
            "identity_source": "fixture-adapter-receipt",
            "composed_prompt_sha256": sha256_bytes(prompt),
            "provider_source_receipt_sha256": sha256_bytes(json.dumps(source, sort_keys=True).encode()),
            "provider_source_receipt": source,
        }

    monkeypatch.setattr(roster_module, "_argv", fake_argv)
    monkeypatch.setattr(roster_module, "_provider_evidence", fake_evidence)
    first = _run_one(
        agent=agent,
        workspace=workspace,
        shared_paths=[],
        marker=MARKER,
        timeout_seconds=10,
        max_attempts=2,
        run_id="provider-response-test",
        roster_seed=7,
    )
    second = _run_one(
        agent=agent,
        workspace=workspace,
        shared_paths=[],
        marker=MARKER,
        timeout_seconds=10,
        max_attempts=2,
        run_id="provider-response-test",
        roster_seed=7,
    )
    assert first["accepted"] is True
    assert first["output_delivery"] == "provider_response"
    assert first["provider_response_materialized"] is True
    assert first["controller_materialized_output"] is True
    assert first["response_extraction_source"].endswith(":text")
    assert first["output_sha256"] == second["output_sha256"]
    assert first["attempts"][0]["provider_response_materialized"] is True
    assert first["attempts"][0]["controller_materialized_output"] is True


def test_provider_response_evidence_failure_retries_then_refuses(monkeypatch) -> None:
    workspace = _response_workspace()
    agent = _response_agent()

    def fake_argv(agent_row, work, prompt_path, **kwargs):
        response = work / "meta/provider_response.json"
        response.write_text(json.dumps({"text": "unbound", "stopReason": "end_turn"}), encoding="utf-8")
        receipt = work / "meta/provider_receipt.json"
        receipt.write_text("{}", encoding="utf-8")
        return [roster_module.sys.executable, "-c", "pass"], dict(roster_module.os.environ), receipt

    def refuse_evidence(**_kwargs):
        raise ZipJobRefusal("REFUSE_MD_AGENT_PROVIDER_EVIDENCE", "model mismatch")

    monkeypatch.setattr(roster_module, "_argv", fake_argv)
    monkeypatch.setattr(roster_module, "_provider_evidence", refuse_evidence)
    result = _run_one(
        agent=agent,
        workspace=workspace,
        shared_paths=[],
        marker=MARKER,
        timeout_seconds=10,
        max_attempts=2,
        run_id="provider-response-refusal",
        roster_seed=9,
    )
    assert result["accepted"] is False
    assert len(result["attempts"]) == 2
    assert all(
        attempt["refusal_reason"] == "REFUSE_MD_AGENT_PROVIDER_EVIDENCE"
        for attempt in result["attempts"]
    )
    assert result["provider_response_materialized"] is False


def test_model_identity_match_kind_marks_declared_alias_without_rejecting_legacy_route(tmp_path) -> None:
    prompt = b"exact composed prompt\n"
    source = {
        "schema": "constraintbox.grok-cli-receipt.v1",
        "request_id": "zip-alias-1",
        "model_requested": "grok-4.6",
        "models_observed_in_output": ["grok-4.6-build"],
        "model_binding_confirmed": True,
        "prompt_sha256": sha256_bytes(prompt),
        "disposition": "OBSERVED",
    }
    receipt_path = tmp_path / "provider.json"
    receipt_path.write_text(json.dumps(source), encoding="utf-8")

    evidence = _provider_evidence(
        provider="grok-cli",
        evidence_path=receipt_path,
        request_id="zip-alias-1",
        model_requested="grok-4.6",
        prompt=prompt,
        model_observed_allowlist=["grok-4.6-build"],
    )

    assert evidence["model_binding_confirmed"] is True
    assert evidence["model_identity_match_kind"] == "declared_alias"
    assert evidence["model_alias_admitted"] is True
    assert evidence["alias_resolution_source"] == "invocation.model_observed_allowlist"
    assert evidence["model_observed_values"] == ["grok-4.6-build"]


@pytest.mark.parametrize(
    "observed",
    [
        ["not-sonnet-model"],
        ["prefix-sonnet-suffix"],
        ["claude-sonnet-5", "claude-haiku-4-5"],
    ],
)
def test_claude_alias_resolution_rejects_unlisted_or_mixed_observed_models(
    tmp_path, observed: list[str]
) -> None:
    prompt = b"exact composed prompt\n"
    source = {
        "schema": "constraintbox.claude-bridge-adapter-receipt.v1",
        "request_id": "zip-alias-adversarial",
        "model_requested": "sonnet",
        "models_observed": observed,
        "model_binding_confirmed": True,
        "prompt_sha256": sha256_bytes(prompt),
        "disposition": "OBSERVED",
    }
    receipt_path = tmp_path / "provider.json"
    receipt_path.write_text(json.dumps(source), encoding="utf-8")

    with pytest.raises(ZipJobRefusal) as caught:
        _provider_evidence(
            provider="claude-code",
            evidence_path=receipt_path,
            request_id="zip-alias-adversarial",
            model_requested="sonnet",
            prompt=prompt,
        )
    assert caught.value.reason_code == "REFUSE_MD_AGENT_PROVIDER_EVIDENCE"


def test_roster_receipt_separates_skill_delivery_from_read_or_execution() -> None:
    receipt = _receipt_for(_roster(_agent("one", _ok("one"))))
    row = receipt["agents"][0]

    assert receipt["skill_bytes_delivered"] is True
    assert receipt["skill_read_proved"] is False
    assert receipt["skill_executed"] is False
    assert receipt["skill_bytes_consumed"] is None
    assert row["skill_bytes_delivered"] is True
    assert row["skill_read_proved"] is False
    assert row["skill_executed"] is False


def test_roster_receipt_preserves_accepted_attempt_and_refusal_summary() -> None:
    retry = (
        "if os.environ.get('CB_ZIP_ATTEMPT') == '1':\n"
        "    Path('output/one.md').write_text('finding: wrong\\n', encoding='utf-8')\n"
        "else:\n"
        + "    " + _ok("one").replace("\n", "\n    ").rstrip()
        + "\n"
    )
    receipt = _receipt_for(_roster(_agent("one", retry)))
    row = receipt["agents"][0]

    assert row["accepted_attempt"] == 2
    assert row["accepted_attempt_count"] == 2
    assert row["accepted_attempts"] == 1
    assert row["refusal_reason_summary"] == {
        "REFUSE_MD_AGENT_MARKER_MISSING": 1,
    }


===== FILE constraint_box/integrated_system/skills/cb-premortem-wave/scripts/run_premortem_zip_wave.py sha256=8acc1ba566572d3cb06adff1ca9cee51a666d233730c160bb118d6db6a160f9a bytes=49393 =====
#!/usr/bin/env python3
"""Build, execute, and verify one ZIP-native premortem wave.

This module is deliberately a candidate runner.  It composes the existing
ZIP_JOB and Markdown-agent roster operations; it does not fan out provider
adapters itself.  Provider/model rows, route paths, and budgets are run data.
The runner's only semantic work is structural validation and preservation of
disagreement.  It never votes for a finding or grants authority.
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import re
import tempfile
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Mapping

from constraintbox_zip_agent.failure_wave import _task
from constraintbox_zip_agent.md_agent_roster import (
    CLAIM_CEILING as ROSTER_MANIFEST_CLAIM_CEILING,
    build_md_agent_roster_packet,
)
from constraintbox_zip_agent.operation_ids import KNOWN_OPERATION_IDS
from constraintbox_zip_agent.protocol import (
    ZipJobRefusal,
    build_packet,
    canonical_json_bytes,
    deterministic_zip,
    sha256_bytes,
    strict_json_loads,
    validate_packet,
    validate_return_zip,
)
from constraintbox_zip_agent.runtime import execute_packet


CONFIG_SCHEMA = "constraintbox.premortem-zip-wave-run.v1"
WAVE_SCHEMA = "constraintbox.premortem-zip-wave.v1"
CELL_SCHEMA = "constraintbox.premortem-cell-result.v1"
ROSTER_SCHEMA = "constraintbox.md-agent-roster.v1"
OUTPUT_DELIVERY = "provider_response"
LENSES = ("likely_failure", "dangerous_failure", "hidden_assumption")
STOP_REASONS = (
    "no_material_delta",
    "repair_callback_absent",
    "falsifiers_settled",
    "cancelled",
    "max_rounds",
    "provider_refused",
    "repair_callback_refused",
)
CLAIM_CEILING = (
    "bounded ZIP premortem observations with exact target, route, MMM, skill, "
    "ancestry, retry, and return bindings; not semantic consensus, authority, "
    "promotion, release, or proof of model comprehension"
)
_SAFE_MODEL = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:/-]{0,127}\Z")
_MAX_MODEL_OBSERVED_ALLOWLIST = 32


@dataclass(frozen=True)
class PremortemZipPacket:
    packet_bytes: bytes
    target_sha256: str
    child_job_ids: tuple[str, ...]
    mmm_combos: dict[str, tuple[str, ...]]

    @property
    def packet_sha256(self) -> str:
        return sha256_bytes(self.packet_bytes)


class PremortemConfigError(ZipJobRefusal):
    """Configuration was not admissible as run data."""


def _canonical(value: Any) -> bytes:
    return canonical_json_bytes(value)


def _object(raw: bytes, label: str) -> dict[str, Any]:
    value = strict_json_loads(raw, label=label)
    if not isinstance(value, dict):
        raise ZipJobRefusal("REFUSE_PREMORTEM_SCHEMA", label)
    return value


def _text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ZipJobRefusal("REFUSE_PREMORTEM_SCHEMA", label)
    return value


def _bounded_int(value: object, label: str, minimum: int, maximum: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or not minimum <= value <= maximum:
        raise ZipJobRefusal("REFUSE_PREMORTEM_SCHEMA", label)
    return value


def _model_observed_allowlist(value: object, label: str) -> list[str] | None:
    if value is None:
        return None
    if not isinstance(value, list) or not value or len(value) > _MAX_MODEL_OBSERVED_ALLOWLIST:
        raise ZipJobRefusal("REFUSE_PREMORTEM_MEMBER_SCHEMA", label)
    if any(not isinstance(item, str) or _SAFE_MODEL.fullmatch(item) is None for item in value):
        raise ZipJobRefusal("REFUSE_PREMORTEM_MEMBER_SCHEMA", label)
    if len(value) != len(set(value)):
        raise ZipJobRefusal("REFUSE_PREMORTEM_MEMBER_SCHEMA", label)
    return list(value)


def _bytes(value: object, label: str, *, maximum: int = 2 * 1024 * 1024) -> bytes:
    if not isinstance(value, (bytes, bytearray)):
        raise ZipJobRefusal("REFUSE_PREMORTEM_BYTES", label)
    raw = bytes(value)
    if not raw or len(raw) > maximum:
        raise ZipJobRefusal("REFUSE_PREMORTEM_BYTES", label)
    return raw


def _entries(data: bytes, *, label: str) -> dict[str, bytes]:
    try:
        with zipfile.ZipFile(io.BytesIO(data), "r") as archive:
            result: dict[str, bytes] = {}
            for info in archive.infolist():
                if info.is_dir() or info.filename in result:
                    raise ZipJobRefusal("REFUSE_PREMORTEM_ZIP_SHAPE", info.filename)
                result[info.filename] = archive.read(info)
            return result
    except ZipJobRefusal:
        raise
    except (OSError, RuntimeError, zipfile.BadZipFile, KeyError) as exc:
        raise ZipJobRefusal("REFUSE_PREMORTEM_ZIP_SHAPE", label) from exc


def _task_bytes(task_id: str, sequence: int, operation: str, inputs: list[str], outputs: list[str], depends_on: list[str] | None = None) -> bytes:
    return _canonical(
        {
            "schema": "constraintbox.zip_task.v1",
            "task_id": task_id,
            "sequence": sequence,
            "operation": operation,
            "input_paths": inputs,
            "output_paths": outputs,
            "depends_on": depends_on or [],
            "parameters": {},
            "preload_files": [],
        }
    )


def _validate_config(config: Mapping[str, Any]) -> dict[str, Any]:
    value = dict(config)
    if value.get("schema") != CONFIG_SCHEMA:
        raise ZipJobRefusal("REFUSE_PREMORTEM_CONFIG", "schema")
    for field in ("parent_job_id", "run_id", "wave_id"):
        _text(value.get(field), field)
    _bounded_int(value.get("round"), "round", 0, 1_000_000)
    _bounded_int(value.get("seed"), "seed", 0, 2**63 - 1)
    max_rounds = _bounded_int(value.get("max_rounds", 1), "max_rounds", 1, 4)
    max_attempts = _bounded_int(value.get("max_attempts", 2), "max_attempts", 1, 5)
    # Normalize defaults into the checked run data so every downstream
    # manifest and validator binds the same retry ceiling.
    value["max_rounds"] = max_rounds
    value["max_attempts"] = max_attempts
    members = value.get("members")
    if not isinstance(members, dict) or set(members) != set(LENSES):
        raise ZipJobRefusal("REFUSE_PREMORTEM_LENS_ROSTER", "lenses")
    seen: set[str] = set()
    for lens in LENSES:
        rows = members[lens]
        if not isinstance(rows, list) or not 2 <= len(rows) <= 4:
            raise ZipJobRefusal("REFUSE_PREMORTEM_MEMBER_COUNT", lens)
        for row in rows:
            if not isinstance(row, dict):
                raise ZipJobRefusal("REFUSE_PREMORTEM_MEMBER_SCHEMA", lens)
            member_id = _text(row.get("member_id"), f"{lens}.member_id")
            if member_id in seen:
                raise ZipJobRefusal("REFUSE_PREMORTEM_MEMBER_IDENTITY", member_id)
            seen.add(member_id)
            _text(row.get("provider"), f"{member_id}.provider")
            _text(row.get("model_requested"), f"{member_id}.model_requested")
            if "model_observed_allowlist" in row:
                row["model_observed_allowlist"] = _model_observed_allowlist(
                    row["model_observed_allowlist"], f"{member_id}.model_observed_allowlist"
                )
            if row.get("output_delivery") != OUTPUT_DELIVERY:
                raise ZipJobRefusal("REFUSE_PREMORTEM_OUTPUT_DELIVERY", member_id)
            provider = row["provider"]
            if provider == "fixture-subprocess":
                _text(row.get("fixture_script"), f"{member_id}.fixture_script")
            elif provider not in {"codex-cli", "grok-cli", "claude-code"}:
                raise ZipJobRefusal("REFUSE_PREMORTEM_PROVIDER", str(provider))
    if not seen:
        raise ZipJobRefusal("REFUSE_PREMORTEM_MEMBER_COUNT", "empty")
    return value


def _select_combo(seed: int, lens: str, member_id: str, voices: list[str], salt: int = 0) -> tuple[str, ...]:
    if len(voices) < 2:
        raise ZipJobRefusal("REFUSE_PREMORTEM_MMM_ASSIGNMENT", "fewer_than_two_sources")
    seed_bytes = f"{seed}:{lens}:{member_id}:mmm:{salt}".encode("utf-8")
    digest = hashlib.sha256(seed_bytes).digest()
    count = min(len(voices), 2 + digest[0] % 3)
    ordered = sorted(
        voices,
        key=lambda voice: hashlib.sha256(
            seed_bytes + b":" + voice.encode("utf-8")
        ).digest(),
    )
    return tuple(ordered[:count])


def _assign_combos(config: Mapping[str, Any], mmm_sources: Mapping[str, bytes]) -> dict[str, tuple[str, ...]]:
    voices = sorted(_text(key, "mmm_voice") for key in mmm_sources)
    if len(voices) > 9:
        raise ZipJobRefusal("REFUSE_PREMORTEM_MMM_ASSIGNMENT", "more_than_nine_sources")
    used: set[tuple[str, ...]] = set()
    assigned: dict[str, tuple[str, ...]] = {}
    seed = int(config["seed"])
    for lens in LENSES:
        for row in config["members"][lens]:
            member_id = str(row["member_id"])
            combo: tuple[str, ...] = ()
            for salt in range(65):
                combo = _select_combo(seed, lens, member_id, voices, salt)
                if combo not in used:
                    break
            if not combo or combo in used:
                raise ZipJobRefusal("REFUSE_PREMORTEM_MMM_ASSIGNMENT", member_id)
            used.add(combo)
            assigned[f"{lens}:{member_id}"] = combo
    return assigned


def _agent_instruction(lens: str, member_id: str, target_digest: str, combo: tuple[str, ...]) -> bytes:
    return (
        f"You are premortem member {member_id}. Assigned lens: {lens}.\n"
        "Read input/target.bin, input/lens_manifest.json, every assigned MMMS file, "
        "and SKILLS/cb-premortem-cell/SKILL.md before responding.\n"
        f"The target_sha256 must be exactly {target_digest}.\n"
        f"Your compact MMM combo is exactly: {', '.join(combo)}.\n"
        "Return ONLY one strict JSON object in the declared output channel. No "
        "markdown fence, preface, vote, promotion, or authority claim.\n"
        "Required keys exactly: schema, lens, target_sha256, failure_mechanisms, "
        "evidence, limits, falsifier, warning, finite_repair, rerun_operation, "
        "claim_ceiling.\n"
        "Use arrays of strings for failure_mechanisms, evidence, and limits. "
        "Keep rival findings separate; the parent preserves disagreement.\n"
    ).encode("utf-8")


def _route_for_roster(row: Mapping[str, Any], *, output_path: str, agent_path: str, mmm_paths: list[str], skill_path: str, context_paths: list[str], required_fragments: list[str], config: Mapping[str, Any]) -> dict[str, Any]:
    """Translate candidate run data to the existing roster's run-data shape."""

    member = dict(row)
    member_id = _text(member.pop("member_id", None), "member_id")
    # This field is part of the roster's provider-response contract.  It must
    # survive into the child packet; silently dropping it would route the
    # worker through the legacy workspace-file path.
    member.pop("require_model_binding", None)
    member.update(
        {
            "agent_id": member_id,
            "agent_path": agent_path,
            "output_path": output_path,
            "mmm_paths": mmm_paths,
            "skill_paths": [skill_path],
            "context_paths": context_paths,
            "required_fragments": required_fragments,
            "forbidden_fragments": ["promotion_allowed: true", '"promotion_allowed":true'],
            "max_output_bytes": int(row.get("max_output_bytes") or 131072),
        }
    )
    member["output_delivery"] = OUTPUT_DELIVERY
    member["output_format"] = "strict_json_object"
    # These are deliberately not passed as provider policy.  The route and
    # output mode remain recorded in input/lens_manifest.json and verified
    # against the resulting receipt.
    return member


def _rename_packet_job(packet_bytes: bytes, job_id: str) -> bytes:
    entries = _entries(packet_bytes, label="child_packet")
    manifest = _object(entries.pop("ZIP_JOB_MANIFEST.json"), "ZIP_JOB_MANIFEST.json")
    manifest["job_id"] = job_id
    return build_packet(manifest, entries)


def _build_lens_packet(*, config: Mapping[str, Any], lens: str, target: bytes, skill: bytes, mmm_sources: Mapping[str, bytes], combos: Mapping[str, tuple[str, ...]]) -> tuple[bytes, dict[str, Any]]:
    target_digest = sha256_bytes(target)
    parent_id = str(config["parent_job_id"])
    wave_id = str(config["wave_id"])
    round_value = int(config["round"])
    max_attempts = int(config["max_attempts"])
    child_id = f"{parent_id}-{lens}"
    skill_path = "SKILLS/cb-premortem-cell/SKILL.md"
    delivery_path = "input/output_delivery.json"
    context_paths = ["input/target.bin", "input/lens_manifest.json", delivery_path]
    members_manifest: list[dict[str, Any]] = []
    files: dict[str, bytes] = {
        "input/target.bin": target,
        skill_path: skill,
        delivery_path: _canonical(
            {
                "schema": "constraintbox.output-delivery.v1",
                "output_delivery": OUTPUT_DELIVERY,
                "provider_response_required": True,
            }
        ),
    }
    agents: list[dict[str, Any]] = []
    for row in config["members"][lens]:
        member_id = str(row["member_id"])
        combo = combos[f"{lens}:{member_id}"]
        mmm_paths = [f"MMMS/{voice}.md" for voice in combo]
        mmm_digests: dict[str, str] = {}
        for voice in combo:
            path = f"MMMS/{voice}.md"
            raw = _bytes(mmm_sources[voice], path)
            files[path] = raw
            mmm_digests[voice] = sha256_bytes(raw)
        agent_path = f"AGENTS/{member_id}.md"
        output_path = f"output/{member_id}.md"
        files[agent_path] = _agent_instruction(lens, member_id, target_digest, combo)
        required = [
            '"schema"',
            f'"lens"',
            f'"target_sha256"',
            '"failure_mechanisms"',
            '"falsifier"',
            target_digest,
        ]
        agent = _route_for_roster(
            row,
            output_path=output_path,
            agent_path=agent_path,
            mmm_paths=mmm_paths,
            skill_path=skill_path,
            context_paths=context_paths,
            required_fragments=required,
            config=config,
        )
        agents.append(agent)
        members_manifest.append(
            {
                "member_id": member_id,
                "agent_path": agent_path,
                "output_path": output_path,
                "provider": row["provider"],
                "model_requested": row["model_requested"],
                "model_observed_allowlist": list(row["model_observed_allowlist"])
                if row.get("model_observed_allowlist") is not None
                else None,
                "model_binding_required": bool(row.get("require_model_binding", row["provider"] != "fixture-subprocess")),
                "output_delivery": OUTPUT_DELIVERY,
                "output_format": "strict_json_object",
                "mmm_ids": list(combo),
                "mmm_paths": mmm_paths,
                "mmm_sha256": mmm_digests,
                "skill_path": skill_path,
                "skill_sha256": sha256_bytes(skill),
            }
        )
    lens_manifest = {
        "schema": "constraintbox.premortem-lens-manifest.v1",
        "parent_id": parent_id,
        "parent_job_id": parent_id,
        "job_id": child_id,
        "wave_id": wave_id,
        "round": round_value,
        "depth": 1,
        "max_attempts": max_attempts,
        "lens": lens,
        "target_sha256": target_digest,
        "target_bytes": len(target),
        "output_delivery": OUTPUT_DELIVERY,
        "output_delivery_required": True,
        "output_delivery_binding": "run-data-and-return-verifier",
        "skill_sha256": sha256_bytes(skill),
        "members": members_manifest,
        "selection": {
            "algorithm": "cb-premortem-distinct-compact-combos-v1",
            "seed": int(config["seed"]),
            "distinct_within_wave": True,
        },
        "claim_ceiling": CLAIM_CEILING,
    }
    files["input/lens_manifest.json"] = _canonical(lens_manifest)
    roster = {
        "schema": ROSTER_SCHEMA,
        "run_id": f"{config['run_id']}-{lens}",
        "seed": int(config["seed"]),
        "required_marker": CELL_SCHEMA,
        "max_attempts": max_attempts,
        "timeout_seconds": int(config.get("timeout_seconds", 120)),
        "max_workers": len(agents),
        "shared_paths": context_paths,
        "agents": agents,
        "parent_id": parent_id,
        "wave_id": wave_id,
        "round": round_value,
        "depth": 1,
    }
    child = build_md_agent_roster_packet(roster=roster, files=files)
    child = _rename_packet_job(child, child_id)
    return child, lens_manifest


def build_premortem_zip_wave_packet(*, config: Mapping[str, Any], target: bytes, skill: bytes, mmm_sources: Mapping[str, bytes]) -> PremortemZipPacket:
    """Build a root ZIP_JOB containing one md-agent child per premortem lens."""

    checked = _validate_config(config)
    target_raw = _bytes(target, "target")
    skill_raw = _bytes(skill, "skill")
    if not isinstance(mmm_sources, Mapping) or not mmm_sources:
        raise ZipJobRefusal("REFUSE_PREMORTEM_MMM_ASSIGNMENT", "empty_sources")
    source_bytes = {str(key): _bytes(raw, str(key)) for key, raw in mmm_sources.items()}
    combos = _assign_combos(checked, source_bytes)
    child_packets: dict[str, bytes] = {}
    child_manifests: dict[str, dict[str, Any]] = {}
    for lens in LENSES:
        child, lens_manifest = _build_lens_packet(
            config=checked,
            lens=lens,
            target=target_raw,
            skill=skill_raw,
            mmm_sources=source_bytes,
            combos=combos,
        )
        child_packets[lens] = child
        child_manifests[lens] = lens_manifest
    parent_id = str(checked["parent_job_id"])
    child_ids = tuple(f"{parent_id}-{lens}" for lens in LENSES)
    child_records = [
        {
            "job_id": child_ids[index],
            "lens": lens,
            "packet_path": f"children/{lens}.zip",
            "return_path": f"output/{lens}.return.zip",
            "packet_sha256": sha256_bytes(child_packets[lens]),
            "target_sha256": sha256_bytes(target_raw),
            "target_bytes": len(target_raw),
            "member_ids": [row["member_id"] for row in checked["members"][lens]],
            "depth": 1,
            "max_attempts": int(checked["max_attempts"]),
        }
        for index, lens in enumerate(LENSES)
    ]
    wave_manifest = {
        "schema": WAVE_SCHEMA,
        "parent_id": parent_id,
        "parent_job_id": parent_id,
        "run_id": checked["run_id"],
        "wave_id": checked["wave_id"],
        "round": checked["round"],
        "depth": 0,
        "max_attempts": int(checked["max_attempts"]),
        "target_sha256": sha256_bytes(target_raw),
        "target_bytes": len(target_raw),
        "output_delivery": OUTPUT_DELIVERY,
        "output_delivery_required": True,
        "lenses": child_records,
        "selection_algorithm": "cb-premortem-distinct-compact-combos-v1",
        "claim_ceiling": CLAIM_CEILING,
        "promotion_allowed": False,
    }
    task_paths: list[str] = []
    files: dict[str, bytes] = {
        "00_RUN_ME_FIRST.md": (
            b"# ConstraintBox ZIP premortem wave\n\n"
            b"CB runs one declared child ZIP for each lens. The parent preserves "
            b"all child returns and never selects a semantic winner.\n"
        ),
        "inputs/target.bin": target_raw,
        "inputs/wave_manifest.json": _canonical(wave_manifest),
    }
    for index, lens in enumerate(LENSES):
        child_path = f"children/{lens}.zip"
        return_path = f"output/{lens}.return.zip"
        task_path = f"tasks/{index:02d}_{lens}.task.json"
        files[child_path] = child_packets[lens]
        files[task_path] = _task_bytes(
            f"run-{lens}", index, "run_child_zip_v1", [child_path], [return_path]
        )
        task_paths.append(task_path)
    parent_manifest = {
        "schema": "constraintbox.zip_job.v1",
        "job_id": parent_id,
        "task_execution_order": task_paths,
        "required_output_file_list": [f"output/{lens}.return.zip" for lens in LENSES],
        "allowed_operations": ["run_child_zip_v1"],
        "allowed_child_job_ids": list(child_ids),
        "max_child_depth": 1,
        "claim_ceiling": ROSTER_MANIFEST_CLAIM_CEILING,
    }
    packet = build_packet(parent_manifest, files)
    validate_packet(packet, known_operations=set(KNOWN_OPERATION_IDS))
    return PremortemZipPacket(
        packet_bytes=packet,
        target_sha256=sha256_bytes(target_raw),
        child_job_ids=child_ids,
        mmm_combos=combos,
    )


def _cell_fields(value: Mapping[str, Any], *, lens: str, target_digest: str) -> None:
    required = {
        "schema", "lens", "target_sha256", "failure_mechanisms", "evidence",
        "limits", "falsifier", "warning", "finite_repair", "rerun_operation",
        "claim_ceiling",
    }
    if set(value) != required:
        raise ZipJobRefusal("REFUSE_PREMORTEM_OUTPUT_SCHEMA", "field_set")
    if value.get("schema") != CELL_SCHEMA or value.get("lens") != lens or value.get("target_sha256") != target_digest:
        raise ZipJobRefusal("REFUSE_PREMORTEM_OUTPUT_BINDING", lens)
    for key in ("failure_mechanisms", "evidence", "limits"):
        values = value.get(key)
        if not isinstance(values, list) or not values or any(not isinstance(item, str) or not item.strip() for item in values):
            raise ZipJobRefusal("REFUSE_PREMORTEM_OUTPUT_SCHEMA", key)
    for key in ("falsifier", "warning", "finite_repair", "rerun_operation", "claim_ceiling"):
        if not isinstance(value.get(key), str) or not value[key].strip():
            raise ZipJobRefusal("REFUSE_PREMORTEM_OUTPUT_SCHEMA", key)
    ceiling = value["claim_ceiling"].lower()
    if any(term in ceiling for term in ("promotion_allowed: true", "authority granted", "release approved")):
        raise ZipJobRefusal("REFUSE_PREMORTEM_OUTPUT_CLAIM_CEILING", lens)


def _attempt_history_summary(
    *, member_id: str, attempts: list[Mapping[str, Any]], accepted_attempt: int
) -> dict[str, Any]:
    """Copy retry facts into the parent surface without semantic flattening."""

    refusal_reasons = [
        str(attempt["refusal_reason"])
        for attempt in attempts
        if isinstance(attempt.get("refusal_reason"), str)
        and attempt.get("refusal_reason")
    ]
    reason_counts: dict[str, int] = {}
    for reason in refusal_reasons:
        reason_counts[reason] = reason_counts.get(reason, 0) + 1
    return {
        "member_id": member_id,
        "attempt_count": len(attempts),
        # This is the one-based number of attempts consumed before the
        # accepted output, not a claim that every attempt was accepted.
        "accepted_attempt_count": accepted_attempt,
        "attempts_until_acceptance": accepted_attempt,
        "accepted_attempts": 1,
        "refusal_reasons": refusal_reasons,
        "attempt_refusal_reasons": refusal_reasons,
        "refusal_reason_summary": reason_counts,
        "attempt_refusal_reason_summary": reason_counts,
    }


def _validate_lens_return(*, lens: str, target: bytes, child_packet: bytes, child_return: bytes, expected: Mapping[str, Any], wave: Mapping[str, Any]) -> dict[str, Any]:
    max_attempts = wave.get("max_attempts")
    if isinstance(max_attempts, bool) or not isinstance(max_attempts, int) or not 1 <= max_attempts <= 5:
        raise ZipJobRefusal("REFUSE_PREMORTEM_RETRY_RECEIPT", lens)
    if expected.get("max_attempts") != max_attempts:
        raise ZipJobRefusal("REFUSE_PREMORTEM_RETRY_RECEIPT", lens)
    child = validate_packet(child_packet, known_operations=set(KNOWN_OPERATION_IDS))
    child_entries = _entries(child_packet, label=f"{lens}.packet")
    child_return_manifest = validate_return_zip(
        child_return,
        expected_input_sha256=sha256_bytes(child_packet),
        input_packet_bytes=child_packet,
    )
    return_entries = _entries(child_return, label=f"{lens}.return")
    lens_manifest = _object(child_entries.get("input/lens_manifest.json", b""), f"{lens}.lens_manifest")
    if lens_manifest.get("lens") != lens or lens_manifest.get("target_sha256") != sha256_bytes(target):
        raise ZipJobRefusal("REFUSE_PREMORTEM_TARGET_BINDING", lens)
    if lens_manifest.get("output_delivery") != OUTPUT_DELIVERY:
        raise ZipJobRefusal("REFUSE_PREMORTEM_OUTPUT_DELIVERY", lens)
    if lens_manifest.get("max_attempts") != max_attempts:
        raise ZipJobRefusal("REFUSE_PREMORTEM_RETRY_RECEIPT", lens)
    if child.manifest.job_id != expected.get("job_id"):
        raise ZipJobRefusal("REFUSE_PREMORTEM_ANCESTRY", lens)
    if lens_manifest.get("parent_id") != wave.get("parent_id") or lens_manifest.get("wave_id") != wave.get("wave_id") or lens_manifest.get("round") != wave.get("round") or lens_manifest.get("depth") != 1:
        raise ZipJobRefusal("REFUSE_PREMORTEM_ANCESTRY", lens)
    if child_entries.get("input/target.bin") != target:
        raise ZipJobRefusal("REFUSE_PREMORTEM_TARGET_BINDING", lens)
    if sha256_bytes(child_entries.get("input/target.bin", b"")) != wave.get("target_sha256"):
        raise ZipJobRefusal("REFUSE_PREMORTEM_TARGET_BINDING", lens)
    delivery = _object(child_entries.get("input/output_delivery.json", b""), f"{lens}.output_delivery")
    if delivery.get("output_delivery") != OUTPUT_DELIVERY or delivery.get("provider_response_required") is not True:
        raise ZipJobRefusal("REFUSE_PREMORTEM_OUTPUT_DELIVERY", lens)
    roster = _object(return_entries.get("output/roster_receipt.json", b""), f"{lens}.roster_receipt")
    if roster.get("max_attempts") != max_attempts:
        raise ZipJobRefusal("REFUSE_PREMORTEM_RETRY_RECEIPT", lens)
    expected_members = list(expected.get("member_ids") or [])
    if roster.get("accepted_agent_ids") != expected_members:
        raise ZipJobRefusal("REFUSE_PREMORTEM_MEMBER_MISSING", lens)
    rows = roster.get("agents")
    if not isinstance(rows, list) or len(rows) != len(expected_members):
        raise ZipJobRefusal("REFUSE_PREMORTEM_MEMBER_MISSING", lens)
    expected_by_id = {str(row["member_id"]): row for row in lens_manifest.get("members", [])}
    records: list[dict[str, Any]] = []
    attempt_summaries: list[dict[str, Any]] = []
    refusal_reason_summary: dict[str, int] = {}
    for row in rows:
        if not isinstance(row, dict):
            raise ZipJobRefusal("REFUSE_PREMORTEM_ROSTER_RECEIPT", lens)
        member_id = _text(row.get("agent_id"), "agent_id")
        expected_member = expected_by_id.get(member_id)
        if expected_member is None or row.get("accepted") is not True:
            raise ZipJobRefusal("REFUSE_PREMORTEM_MEMBER_MISSING", member_id)
        if row.get("output_delivery") != OUTPUT_DELIVERY:
            raise ZipJobRefusal("REFUSE_PREMORTEM_OUTPUT_DELIVERY", member_id)
        if row.get("controller_materialized_output") is not True:
            raise ZipJobRefusal("REFUSE_PREMORTEM_OUTPUT_DELIVERY", member_id)
        if row.get("provider") != expected_member.get("provider") or row.get("model_requested") != expected_member.get("model_requested"):
            raise ZipJobRefusal("REFUSE_PREMORTEM_MODEL_MISMATCH", member_id)
        if row.get("model_observed_allowlist") != expected_member.get(
            "model_observed_allowlist"
        ):
            raise ZipJobRefusal("REFUSE_PREMORTEM_MODEL_BINDING", member_id)
        attempts = row.get("attempts")
        if not isinstance(attempts, list) or not 1 <= len(attempts) <= max_attempts:
            raise ZipJobRefusal("REFUSE_PREMORTEM_RETRY_RECEIPT", member_id)
        if not isinstance(row.get("accepted_attempt"), int) or not 1 <= row["accepted_attempt"] <= len(attempts):
            raise ZipJobRefusal("REFUSE_PREMORTEM_RETRY_RECEIPT", member_id)
        accepted_attempt = attempts[row["accepted_attempt"] - 1]
        for attempt_index, attempt in enumerate(attempts, start=1):
            if not isinstance(attempt, dict) or not attempt.get("provider_request_id"):
                raise ZipJobRefusal("REFUSE_PREMORTEM_REQUEST_BINDING", member_id)
            if attempt.get("attempt") != attempt_index:
                raise ZipJobRefusal("REFUSE_PREMORTEM_RETRY_RECEIPT", member_id)
            if "output_delivery" in attempt and attempt.get("output_delivery") != OUTPUT_DELIVERY:
                raise ZipJobRefusal("REFUSE_PREMORTEM_OUTPUT_DELIVERY", member_id)
        attempt_summary = _attempt_history_summary(
            member_id=member_id, attempts=attempts, accepted_attempt=row["accepted_attempt"]
        )
        # Delivery is derived from the child packet bytes below, not from a
        # member's echoed digest or a copied receipt flag.
        attempt_summary["skill_bytes_delivered"] = True
        attempt_summary["skill_read_proved"] = False
        attempt_summary["skill_executed"] = False
        attempt_summary["max_attempts"] = max_attempts
        attempt_summaries.append(attempt_summary)
        for reason, count in attempt_summary["refusal_reason_summary"].items():
            refusal_reason_summary[reason] = refusal_reason_summary.get(reason, 0) + int(count)
        if accepted_attempt.get("controller_materialized_output") is not True:
            raise ZipJobRefusal("REFUSE_PREMORTEM_OUTPUT_DELIVERY", member_id)
        require_binding = bool(expected_member.get("model_binding_required"))
        match_kind = row.get(
            "model_identity_match_kind",
            row.get("model_match_kind", "unverified"),
        )
        if match_kind not in {"exact", "declared_alias", "unverified"}:
            raise ZipJobRefusal("REFUSE_PREMORTEM_MODEL_MISMATCH", member_id)
        if require_binding and match_kind not in {"exact", "declared_alias"}:
            # A provider receipt's boolean binding flag is not enough: an
            # unverified route must never satisfy a required identity bind.
            raise ZipJobRefusal("REFUSE_PREMORTEM_MODEL_BINDING", member_id)
        if require_binding and (row.get("model_binding_confirmed") is not True or not row.get("models_observed")):
            raise ZipJobRefusal("REFUSE_PREMORTEM_MODEL_BINDING", member_id)
        if require_binding and (
            not row.get("composed_prompt_sha256")
            or not row.get("provider_source_receipt_sha256")
        ):
            raise ZipJobRefusal("REFUSE_PREMORTEM_REQUEST_BINDING", member_id)
        observed_values = row.get(
            "model_observed_values", row.get("models_observed", [])
        )
        if not isinstance(observed_values, list) or any(
            not isinstance(value, str) or not value for value in observed_values
        ):
            raise ZipJobRefusal("REFUSE_PREMORTEM_MODEL_BINDING", member_id)
        if len(observed_values) != 1:
            raise ZipJobRefusal("REFUSE_PREMORTEM_MODEL_BINDING", member_id)
        if match_kind == "declared_alias" and row.get(
            "alias_resolution_source"
        ) != "invocation.model_observed_allowlist":
            raise ZipJobRefusal("REFUSE_PREMORTEM_MODEL_BINDING", member_id)
        if match_kind == "exact":
            if observed_values != [expected_member.get("model_requested")]:
                raise ZipJobRefusal("REFUSE_PREMORTEM_MODEL_BINDING", member_id)
        elif match_kind == "declared_alias":
            allowlist = expected_member.get("model_observed_allowlist")
            if not isinstance(allowlist, list) or observed_values[0] not in allowlist:
                raise ZipJobRefusal("REFUSE_PREMORTEM_MODEL_BINDING", member_id)
        attempt_summary["model_identity_match_kind"] = match_kind
        attempt_summary["model_match_kind"] = match_kind
        attempt_summary["model_alias_admitted"] = match_kind == "declared_alias"
        attempt_summary["alias_resolution_source"] = row.get("alias_resolution_source")
        attempt_summary["model_observed_values"] = list(observed_values)
        output_path = str(expected_member["output_path"])
        body = return_entries.get(output_path)
        if body is None:
            raise ZipJobRefusal("REFUSE_PREMORTEM_MEMBER_MISSING", output_path)
        cell = _object(body, output_path)
        _cell_fields(cell, lens=lens, target_digest=sha256_bytes(target))
        if row.get("output_sha256") != sha256_bytes(body):
            raise ZipJobRefusal("REFUSE_PREMORTEM_OUTPUT_BINDING", member_id)
        if accepted_attempt.get("output_sha256") != sha256_bytes(body):
            raise ZipJobRefusal("REFUSE_PREMORTEM_OUTPUT_BINDING", member_id)
        if row.get("output_path") != output_path:
            raise ZipJobRefusal("REFUSE_PREMORTEM_OUTPUT_BINDING", member_id)
        skill_digest = str(expected_member["skill_sha256"])
        if sha256_bytes(child_entries.get(str(expected_member["skill_path"]), b"")) != skill_digest:
            raise ZipJobRefusal("REFUSE_PREMORTEM_SKILL_BINDING", member_id)
        if skill_digest not in body.decode("utf-8", errors="replace"):
            raise ZipJobRefusal("REFUSE_PREMORTEM_SKILL_BINDING", member_id)
        for digest in dict(expected_member.get("mmm_sha256") or {}).values():
            voice = next(
                name for name, value in dict(expected_member.get("mmm_sha256") or {}).items()
                if value == digest
            )
            if sha256_bytes(child_entries.get(f"MMMS/{voice}.md", b"")) != digest:
                raise ZipJobRefusal("REFUSE_PREMORTEM_MMM_BINDING", member_id)
            if digest not in body.decode("utf-8", errors="replace"):
                raise ZipJobRefusal("REFUSE_PREMORTEM_MMM_BINDING", member_id)
        tool_raw = return_entries.get("output/tool_evidence.json")
        if not tool_raw:
            raise ZipJobRefusal("REFUSE_PREMORTEM_TOOL_RECEIPT", lens)
        tool = _object(tool_raw, "output/tool_evidence.json")
        tool_digest = _text(tool.get("canonical_sha256"), "tool.canonical_sha256")
        if tool_digest not in body.decode("utf-8", errors="replace"):
            raise ZipJobRefusal("REFUSE_PREMORTEM_TOOL_BINDING", member_id)
        records.append(cell)
    return {
        "lens": lens,
        "max_attempts": max_attempts,
        "packet_sha256": sha256_bytes(child_packet),
        "return_sha256": sha256_bytes(child_return),
        "return_runtime_source_sha256": child_return_manifest.runtime_source_sha256,
        "target_sha256": sha256_bytes(target),
        "member_records": records,
        "attempt_summaries": attempt_summaries,
        "member_attempt_receipts": attempt_summaries,
        "accepted_attempt_count": sum(
            int(summary["accepted_attempts"]) for summary in attempt_summaries
        ),
        "accepted_attempts_consumed": sum(
            int(summary["accepted_attempt_count"]) for summary in attempt_summaries
        ),
        "refusal_reason_summary": refusal_reason_summary,
        "mmm_read_proved": False,
        "skill_bytes_delivered": all(
            bool(summary.get("skill_bytes_delivered")) for summary in attempt_summaries
        ),
        "skill_read_proved": False,
        "skill_executed": False,
        "accepted_member_ids": expected_members,
        "output_delivery": OUTPUT_DELIVERY,
        "claim_ceiling": CLAIM_CEILING,
    }


def validate_premortem_zip_wave_return(packet_bytes: bytes, return_bytes: bytes) -> dict[str, Any]:
    """Validate root/child ZIPs and return only a disagreement-preserving receipt."""

    packet = validate_packet(packet_bytes, known_operations=set(KNOWN_OPERATION_IDS))
    if packet.manifest.allowed_operations != ["run_child_zip_v1"] or packet.manifest.max_child_depth != 1:
        raise ZipJobRefusal("REFUSE_PREMORTEM_PACKET_SHAPE", packet.manifest.job_id)
    validate_return_zip(return_bytes, expected_input_sha256=sha256_bytes(packet_bytes), input_packet_bytes=packet_bytes)
    root_entries = _entries(return_bytes, label="premortem.root_return")
    packet_entries = _entries(packet_bytes, label="premortem.root_packet")
    wave = _object(packet_entries.get("inputs/wave_manifest.json", b""), "inputs/wave_manifest.json")
    target = packet_entries.get("inputs/target.bin")
    if target is None or wave.get("target_sha256") != sha256_bytes(target):
        raise ZipJobRefusal("REFUSE_PREMORTEM_TARGET_BINDING", "root")
    if wave.get("output_delivery") != OUTPUT_DELIVERY or wave.get("lenses") is None:
        raise ZipJobRefusal("REFUSE_PREMORTEM_OUTPUT_DELIVERY", "root")
    child_rows = {str(row.get("lens")): row for row in wave["lenses"] if isinstance(row, dict)}
    if set(child_rows) != set(LENSES):
        raise ZipJobRefusal("REFUSE_PREMORTEM_LENS_ROSTER", "return")
    lens_receipts: list[dict[str, Any]] = []
    all_records: list[dict[str, Any]] = []
    all_attempt_summaries: list[dict[str, Any]] = []
    for lens in LENSES:
        child_path = f"children/{lens}.zip"
        return_path = f"output/{lens}.return.zip"
        child_packet = packet_entries.get(child_path)
        child_return = root_entries.get(return_path)
        if child_packet is None or child_return is None:
            raise ZipJobRefusal("REFUSE_PREMORTEM_CHILD_RETURN_MISSING", lens)
        row = child_rows[lens]
        if sha256_bytes(child_packet) != row.get("packet_sha256") or row.get("target_sha256") != sha256_bytes(target):
            raise ZipJobRefusal("REFUSE_PREMORTEM_CHILD_REBOUND", lens)
        receipt = _validate_lens_return(
            lens=lens,
            target=target,
            child_packet=child_packet,
            child_return=child_return,
            expected=row,
            wave=wave,
        )
        lens_receipts.append(receipt)
        all_records.extend(receipt["member_records"])
        all_attempt_summaries.extend(receipt["attempt_summaries"])
    compiled = compile_disagreement_receipt(
        all_records, attempt_summaries=all_attempt_summaries
    )
    return {
        "schema": WAVE_SCHEMA,
        "disposition": "PREMORTEM_ZIP_WAVE_COMPLETED",
        "parent_job_id": packet.manifest.job_id,
        "wave_id": wave.get("wave_id"),
        "run_id": wave.get("run_id"),
        "round": wave.get("round"),
        "target_sha256": sha256_bytes(target),
        "packet_sha256": sha256_bytes(packet_bytes),
        "return_sha256": sha256_bytes(return_bytes),
        "max_attempts": wave.get("max_attempts"),
        "lens_receipts": lens_receipts,
        "attempt_summaries": all_attempt_summaries,
        "compiled": compiled,
        # These are copied from the freshly compiled, validated receipt.  No
        # member text can raise a read/execution claim at this surface.
        "mmm_read_proved": bool(compiled.get("mmm_read_proved", False)),
        "skill_read_proved": bool(compiled.get("skill_read_proved", False)),
        "skill_executed": bool(compiled.get("skill_executed", False)),
        "accepted_attempt_count": int(compiled.get("accepted_attempt_count", 0)),
        "accepted_attempts_consumed": int(
            compiled.get("accepted_attempts_consumed", 0)
        ),
        "refusal_reason_summary": dict(
            compiled.get("refusal_reason_summary") or {}
        ),
        "semantic_vote": None,
        "authority_disposition": None,
        "promotion_allowed": False,
        "claim_ceiling": CLAIM_CEILING,
    }


def compile_disagreement_receipt(
    records: list[Mapping[str, Any]],
    *,
    attempt_summaries: list[Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    """Group exact records and expose contradictions without choosing a winner."""

    fingerprints: dict[str, list[dict[str, Any]]] = {}
    for record in records:
        value = dict(record)
        digest = sha256_bytes(_canonical(value))
        fingerprints.setdefault(digest, []).append(value)
    groups = [
        {"fingerprint": digest, "count": len(values), "records": values}
        for digest, values in sorted(fingerprints.items())
    ]
    mechanisms = {str(item) for record in records for item in record.get("failure_mechanisms", [])}
    contradictions = []
    if len(mechanisms) > 1:
        contradictions.append(
            {
                "field": "failure_mechanisms",
                "distinct_values": sorted(mechanisms),
                "semantic_resolution": None,
            }
        )
    max_count = max((len(values) for values in fingerprints.values()), default=0)
    minority = [group for group in groups if group["count"] < max_count]
    attempt_rows = [dict(summary) for summary in (attempt_summaries or [])]
    refusal_reason_summary: dict[str, int] = {}
    for summary in attempt_rows:
        for reason, count in dict(summary.get("refusal_reason_summary") or {}).items():
            refusal_reason_summary[str(reason)] = refusal_reason_summary.get(str(reason), 0) + int(count)
    return {
        "schema": "constraintbox.premortem-disagreement.v1",
        "max_attempts": max(
            (int(summary.get("max_attempts", 0)) for summary in attempt_rows),
            default=0,
        ),
        "member_count": len(records),
        "exact_groups": groups,
        "contradictions": contradictions,
        "minority_findings": minority,
        "attempt_summaries": attempt_rows,
        "accepted_attempt_count": sum(
            int(summary.get("accepted_attempts", 0)) for summary in attempt_rows
        ),
        "accepted_attempts_consumed": sum(
            int(summary.get("accepted_attempt_count", 0)) for summary in attempt_rows
        ),
        "refusal_reason_summary": refusal_reason_summary,
        "mmm_read_proved": False,
        "skill_bytes_delivered": bool(attempt_rows)
        and all(bool(summary.get("skill_bytes_delivered", True)) for summary in attempt_rows),
        "skill_read_proved": False,
        "skill_executed": False,
        "winner": None,
        "semantic_vote": None,
        "preserved_without_collapse": True,
        "claim_ceiling": "disagreement inventory only; not semantic consensus or authority",
    }


def run_premortem_zip_wave(*, config: Mapping[str, Any], target: bytes, skill: bytes, mmm_sources: Mapping[str, bytes], repair_workspace: Path | None = None, repair_callback: Callable[[dict[str, Any], Path], bytes | None] | None = None, cancel: bool = False) -> dict[str, Any]:
    """Run bounded rounds; callback receives a temporary repair workspace only."""

    checked = _validate_config(config)
    original_target = _bytes(target, "target")
    if cancel:
        return {
            "schema": WAVE_SCHEMA,
            "disposition": "CANCELLED",
            "stop_reason": "cancelled",
            "max_attempts": int(checked["max_attempts"]),
            "target_sha256": sha256_bytes(original_target),
            "rounds": [],
            "mmm_read_proved": False,
            "skill_read_proved": False,
            "skill_executed": False,
            "accepted_attempt_count": 0,
            "accepted_attempts_consumed": 0,
            "refusal_reason_summary": {},
            "promotion_allowed": False,
            "claim_ceiling": CLAIM_CEILING,
        }
    if repair_callback is not None and repair_workspace is None:
        raise ZipJobRefusal("REFUSE_PREMORTEM_REPAIR_WORKSPACE", "required_for_callback")
    current = original_target
    rounds: list[dict[str, Any]] = []
    max_rounds = int(checked.get("max_rounds", 1))
    start_round = int(checked["round"])
    stop_reason = "max_rounds"
    for offset in range(max_rounds):
        round_config = dict(checked)
        round_config["round"] = start_round + offset
        packet = build_premortem_zip_wave_packet(
            config=round_config, target=current, skill=skill, mmm_sources=mmm_sources
        )
        try:
            result = execute_packet(packet.packet_bytes)
            receipt = validate_premortem_zip_wave_return(packet.packet_bytes, result.return_zip_bytes)
        except ZipJobRefusal as exc:
            rounds.append(
                {
                    "round": round_config["round"],
                    "packet_sha256": packet.packet_sha256,
                    "target_sha256": packet.target_sha256,
                    "disposition": "REFUSED",
                    "reason_code": exc.reason_code,
                    "detail": exc.detail,
                }
            )
            stop_reason = "provider_refused"
            break
        rounds.append(receipt)
        if repair_callback is None:
            # No probe ran, so no observation supports a material-delta
            # conclusion.  Keep no_material_delta for a callback that ran and
            # returned an unchanged/no candidate target.
            stop_reason = "repair_callback_absent"
            break
        if offset + 1 >= max_rounds:
            stop_reason = "max_rounds"
            break
        workspace_root = Path(repair_workspace).expanduser().resolve()
        workspace_root.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix=f"premortem-r{round_config['round']}-", dir=workspace_root) as tmp:
            work = Path(tmp)
            (work / "target.bin").write_bytes(current)
            (work / "receipt.json").write_bytes(_canonical(receipt))
            candidate = repair_callback(receipt, work)
        if candidate is None:
            stop_reason = "no_material_delta"
            break
        try:
            candidate_bytes = _bytes(candidate, "repair_candidate")
        except ZipJobRefusal:
            stop_reason = "repair_callback_refused"
            break
        if candidate_bytes == current:
            stop_reason = "no_material_delta"
            break
        current = candidate_bytes
    latest_valid = next(
        (
            round_receipt
            for round_receipt in reversed(rounds)
            if isinstance(round_receipt, dict)
            and isinstance(round_receipt.get("compiled"), dict)
        ),
        {},
    )
    compiled = latest_valid.get("compiled", {})
    return {
        "schema": WAVE_SCHEMA,
        "disposition": "PREMORTEM_ZIP_WAVE_COMPLETED" if rounds and rounds[-1].get("disposition") != "REFUSED" else "REFUSED",
        "stop_reason": stop_reason,
        "max_attempts": int(checked["max_attempts"]),
        "target_sha256": sha256_bytes(original_target),
        "final_target_sha256": sha256_bytes(current),
        "rounds": rounds,
        "mmm_read_proved": bool(compiled.get("mmm_read_proved", False)),
        "skill_read_proved": bool(compiled.get("skill_read_proved", False)),
        "skill_executed": bool(compiled.get("skill_executed", False)),
        "accepted_attempt_count": int(compiled.get("accepted_attempt_count", 0)),
        "accepted_attempts_consumed": int(
            compiled.get("accepted_attempts_consumed", 0)
        ),
        "refusal_reason_summary": dict(
            compiled.get("refusal_reason_summary") or {}
        ),
        "semantic_vote": None,
        "authority_disposition": None,
        "promotion_allowed": False,
        "claim_ceiling": CLAIM_CEILING,
    }


def _read_mmm_args(values: list[str]) -> dict[str, bytes]:
    result: dict[str, bytes] = {}
    for value in values:
        if "=" not in value:
            raise ValueError("MMM must be VOICE=PATH")
        voice, raw_path = value.split("=", 1)
        result[_text(voice, "mmm_voice")] = Path(raw_path).read_bytes()
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="run_premortem_zip_wave")
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--target", type=Path, required=True)
    parser.add_argument("--skill", type=Path, required=True)
    parser.add_argument("--mmm", action="append", default=[], help="VOICE=PATH (repeat)")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--cancel", action="store_true")
    args = parser.parse_args(argv)
    try:
        config = _object(args.config.read_bytes(), str(args.config))
        receipt = run_premortem_zip_wave(
            config=config,
            target=args.target.read_bytes(),
            skill=args.skill.read_bytes(),
            mmm_sources=_read_mmm_args(args.mmm),
            cancel=args.cancel,
        )
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_bytes(_canonical(receipt) + b"\n")
        print(json.dumps(receipt, sort_keys=True, separators=(",", ":")))
        return 0 if receipt.get("disposition") != "REFUSED" else 2
    except (OSError, ValueError, ZipJobRefusal) as exc:
        reason = exc.reason_code if isinstance(exc, ZipJobRefusal) else "REFUSE_PREMORTEM_IO"
        detail = exc.detail if isinstance(exc, ZipJobRefusal) else str(exc)
        print(json.dumps({"schema": WAVE_SCHEMA, "disposition": "REFUSE", "reason_code": reason, "detail": detail, "promotion_allowed": False}, sort_keys=True, separators=(",", ":")))
        return 2


__all__ = [
    "CELL_SCHEMA",
    "CONFIG_SCHEMA",
    "LENSES",
    "OUTPUT_DELIVERY",
    "PremortemZipPacket",
    "build_premortem_zip_wave_packet",
    "compile_disagreement_receipt",
    "run_premortem_zip_wave",
    "validate_premortem_zip_wave_return",
]


if __name__ == "__main__":
    raise SystemExit(main())


===== FILE constraint_box/integrated_system/skills/cb-premortem-wave/tests/test_premortem_zip_wave.py sha256=0869968dc7630890c1eca5af8504e6c4d581fd322d784fff6760b2627fe6375f bytes=20469 =====
from __future__ import annotations

import hashlib
import importlib.util
import io
import json
import sys
import zipfile
from pathlib import Path

import pytest

ZIP_SRC = Path(__file__).resolve().parents[4] / "zip_agent" / "src"
sys.path.insert(0, str(ZIP_SRC))
import constraintbox_zip_agent.md_agent_roster as roster_module
SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "run_premortem_zip_wave.py"
SPEC = importlib.util.spec_from_file_location("premortem_zip_wave_candidate", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
runner = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = runner
SPEC.loader.exec_module(runner)


def _fixture_script(*, member_id: str, mode: str = "valid") -> str:
    # The fixture models a live adapter's response artifact.  It deliberately
    # never creates output/<member>.md; the roster must materialize that file.
    return f'''
import hashlib
import json
import os
from pathlib import Path

if {mode!r} == "missing":
    raise SystemExit(0)
if {mode!r} == "retry" and os.environ.get("CB_ZIP_ATTEMPT") == "1":
    Path("meta/claude-output").mkdir(parents=True, exist_ok=True)
    Path("meta/claude-output/provider_response.txt").write_text("not-json\\n", encoding="utf-8")
    raise SystemExit(0)
target = hashlib.sha256(Path("input/target.bin").read_bytes()).hexdigest()
lens = json.loads(Path("input/lens_manifest.json").read_text(encoding="utf-8"))
me = next(row for row in lens["members"] if row["member_id"] == {member_id!r})
tool = json.loads(Path("output/tool_evidence.json").read_text(encoding="utf-8"))["canonical_sha256"]
evidence = [
    "provider response fixture observed",
    "skill-token: " + hashlib.sha256(Path("SKILLS/cb-premortem-cell/SKILL.md").read_bytes()).hexdigest(),
    "tool-token: " + tool,
]
evidence.extend("mmm-token: " + digest for digest in me["mmm_sha256"].values())
value = {{
    "schema": "constraintbox.premortem-cell-result.v1",
    "lens": lens["lens"],
    "target_sha256": target,
    "failure_mechanisms": ["declared provider response may be absent"],
    "evidence": evidence,
    "limits": ["fixture route only"],
    "falsifier": "delete the declared provider response and require refusal",
    "warning": "a missing provider response must not become a prose success",
    "finite_repair": "retain the response channel and rerun the same packet",
    "rerun_operation": "run_child_zip_v1:{member_id}",
    "claim_ceiling": "advisory premortem observation only; no authority or promotion",
}}
Path("meta/claude-output").mkdir(parents=True, exist_ok=True)
envelope = {{
    "is_error": False,
    "subtype": "success",
    "terminal_reason": "completed",
    "result": (
        json.dumps(value, sort_keys=True).replace(
            '"limits": ["fixture route only"]',
            '"limits": [NaN]',
        ) + "\\n"
        if {mode!r} == "invalid-json" and os.environ.get("CB_ZIP_ATTEMPT") == "1"
        else json.dumps(value, sort_keys=True) + "\\n"
    ),
}}
Path("meta/claude-output/provider_response.txt").write_text(json.dumps(envelope, sort_keys=True), encoding="utf-8")
'''


@pytest.fixture(autouse=True)
def _fake_live_provider_response(monkeypatch: pytest.MonkeyPatch) -> None:
    """Run a model-free live-shaped adapter through provider_response mode."""

    def fake_argv(agent, work, prompt_path, *, request_id, timeout_seconds, output_delivery, hierarchy=None):
        del prompt_path, request_id, timeout_seconds, output_delivery, hierarchy
        evidence_path = work / "meta" / "provider_receipt.json"
        script = agent["fixture_script"]
        env = {
            "PATH": str(Path(sys.executable).resolve().parent),
            "HOME": str(work / "home"),
            "TMPDIR": str(work / "tmp"),
            "PYTHONNOUSERSITE": "1",
            "PYTHONDONTWRITEBYTECODE": "1",
        }
        (work / "home").mkdir(exist_ok=True)
        (work / "tmp").mkdir(exist_ok=True)
        return [sys.executable, "-c", script], env, evidence_path

    def fake_evidence(
        *, provider, evidence_path, request_id, model_requested, prompt,
        model_observed_allowlist=None,
    ):
        del provider
        response_path = evidence_path.parent / "claude-output" / "provider_response.txt"
        if not response_path.is_file():
            raise roster_module.ZipJobRefusal(
                "REFUSE_MD_AGENT_PROVIDER_RESPONSE_MISSING",
                str(response_path),
            )
        response_raw = response_path.read_bytes()
        return {
            "provider_request_id": request_id,
            "model_observed": ["fixture-observed"],
            "model_observed_values": ["fixture-observed"],
            "model_observed_allowlist": model_observed_allowlist,
            # Deliberately forge the legacy boolean without a match kind; the
            # parent validator must still refuse a required binding.
            "model_binding_confirmed": True,
            "model_identity_match_kind": "unverified",
            "model_match_kind": "unverified",
            "alias_resolution_source": None,
            "identity_source": "fixture-provider-response",
            "composed_prompt_sha256": hashlib.sha256(prompt).hexdigest(),
            "provider_source_receipt_sha256": "a" * 64,
            "provider_source_receipt": {
                "nested_output_path": str(response_path),
                "nested_output_sha256": hashlib.sha256(response_raw).hexdigest(),
                "model_requested": model_requested,
            },
        }

    monkeypatch.setattr(roster_module, "_argv", fake_argv)
    monkeypatch.setattr(roster_module, "_provider_evidence", fake_evidence)


def _config(*, mode: str = "valid", require_binding: bool = False, member_count: int = 2) -> dict:
    members: dict[str, list[dict]] = {}
    for lens in runner.LENSES:
        rows = []
        for index in range(member_count):
            member_id = f"{lens[:3]}-{index}"
            rows.append(
                {
                    "member_id": member_id,
                    "provider": "claude-code",
                    "model_requested": f"fixture-{lens}-{index}",
                    "output_delivery": "provider_response",
                    "require_model_binding": require_binding,
                    "fixture_script": _fixture_script(member_id=member_id, mode=mode),
                    "runner_path": sys.executable,
                    "bridge_path": __file__,
                }
            )
        members[lens] = rows
    return {
        "schema": runner.CONFIG_SCHEMA,
        "parent_job_id": "premortem-fixture-parent",
        "run_id": "premortem-fixture-run",
        "wave_id": "premortem-fixture-wave",
        "round": 0,
        "seed": 420461,
        "max_rounds": 2,
        "max_attempts": 2,
        "timeout_seconds": 30,
        "members": members,
    }


def _inputs() -> tuple[bytes, bytes, dict[str, bytes]]:
    target = b"CB target bytes remain immutable.\n"
    skill = b"# contained cb-premortem-cell\nreturn strict JSON only\n"
    mmms = {
        "popper": b"# Popper compact\nfalsifier and finite test\n",
        "pushback": b"# Pushback compact\nboundary and hold\n",
        "zhuangzi": b"# Zhuangzi compact\nplural readings without collapse\n",
        "hume": b"# Hume compact\nparticular evidence only\n",
    }
    return target, skill, mmms


def _entries(data: bytes) -> dict[str, bytes]:
    with zipfile.ZipFile(io.BytesIO(data), "r") as archive:
        return {name: archive.read(name) for name in archive.namelist() if not name.endswith("/")}


def _packet() -> tuple[object, dict, bytes, bytes, dict[str, bytes]]:
    target, skill, mmms = _inputs()
    config = _config()
    packet = runner.build_premortem_zip_wave_packet(
        config=config, target=target, skill=skill, mmm_sources=mmms
    )
    return packet, config, target, skill, mmms


def test_build_has_three_real_zip_children_and_explicit_provider_response() -> None:
    packet, config, target, _skill, _mmms = _packet()
    root = _entries(packet.packet_bytes)
    wave = json.loads(root["inputs/wave_manifest.json"])
    assert set(wave["lenses"][0]) >= {"lens", "packet_sha256", "target_sha256"}
    assert wave["target_sha256"] == hashlib.sha256(target).hexdigest()
    assert wave["output_delivery"] == "provider_response"
    assert set(root) >= {
        "ZIP_JOB_MANIFEST.json",
        "inputs/target.bin",
        "inputs/wave_manifest.json",
        "children/likely_failure.zip",
        "children/dangerous_failure.zip",
        "children/hidden_assumption.zip",
    }
    combos = packet.mmm_combos
    assert len(combos) == 6
    assert all(2 <= len(combo) <= 4 for combo in combos.values())
    assert len(set(combos.values())) == len(combos)
    assert config["members"]["likely_failure"][0]["output_delivery"] == "provider_response"


def test_fixture_wave_executes_through_nested_zip_and_preserves_disagreement() -> None:
    packet, _config_value, _target, _skill, _mmms = _packet()
    result = runner.execute_packet(packet.packet_bytes)
    receipt = runner.validate_premortem_zip_wave_return(
        packet.packet_bytes, result.return_zip_bytes
    )
    assert receipt["disposition"] == "PREMORTEM_ZIP_WAVE_COMPLETED"
    assert receipt["semantic_vote"] is None
    assert receipt["authority_disposition"] is None
    assert receipt["promotion_allowed"] is False
    assert receipt["compiled"]["preserved_without_collapse"] is True
    assert len(receipt["lens_receipts"]) == 3
    assert all(len(row["member_records"]) == 2 for row in receipt["lens_receipts"])


def test_replay_is_independently_bound_and_preserves_output_digests() -> None:
    packet, _config_value, _target, _skill, _mmms = _packet()
    first = runner.execute_packet(packet.packet_bytes)
    second = runner.execute_packet(packet.packet_bytes)
    left = runner.validate_premortem_zip_wave_return(
        packet.packet_bytes, first.return_zip_bytes
    )
    right = runner.validate_premortem_zip_wave_return(
        packet.packet_bytes, second.return_zip_bytes
    )
    assert left["target_sha256"] == right["target_sha256"]
    assert [
        [hashlib.sha256(runner.canonical_json_bytes(member)).hexdigest() for member in lens["member_records"]]
        for lens in left["lens_receipts"]
    ] == [
        [hashlib.sha256(runner.canonical_json_bytes(member)).hexdigest() for member in lens["member_records"]]
        for lens in right["lens_receipts"]
    ]


def test_provider_response_retry_receipt_is_bound() -> None:
    target, skill, mmms = _inputs()
    config = _config(mode="retry")
    packet = runner.build_premortem_zip_wave_packet(config=config, target=target, skill=skill, mmm_sources=mmms)
    result = runner.execute_packet(packet.packet_bytes)
    receipt = runner.validate_premortem_zip_wave_return(packet.packet_bytes, result.return_zip_bytes)
    # The lens receipt retains accepted member records; the nested roster
    # remains independently available in the child return for full attempt
    # inspection.  A successful second attempt is therefore not flattened.
    assert receipt["lens_receipts"][0]["accepted_member_ids"] == ["lik-0", "lik-1"]


def test_invalid_strict_json_member_retries_at_member_gate() -> None:
    target, skill, mmms = _inputs()
    config = _config(mode="invalid-json")
    packet = runner.build_premortem_zip_wave_packet(
        config=config, target=target, skill=skill, mmm_sources=mmms
    )
    result = runner.execute_packet(packet.packet_bytes)
    receipt = runner.validate_premortem_zip_wave_return(
        packet.packet_bytes, result.return_zip_bytes
    )
    assert receipt["disposition"] == "PREMORTEM_ZIP_WAVE_COMPLETED"

    root = _entries(result.return_zip_bytes)
    child = _entries(root["output/likely_failure.return.zip"])
    roster = json.loads(child["output/roster_receipt.json"])
    first = roster["agents"][0]
    assert first["output_format"] == "strict_json_object"
    assert first["accepted_attempt"] == 2
    assert first["attempts"][0]["json_valid"] is False
    assert first["attempts"][0]["refusal_reason"] == "REFUSE_MD_AGENT_OUTPUT_JSON"
    assert first["attempts"][1]["json_valid"] is True


def test_invalid_strict_json_exhaustion_refuses_whole_child_wave() -> None:
    target, skill, mmms = _inputs()
    config = _config(mode="invalid-json")
    config["max_attempts"] = 1
    packet = runner.build_premortem_zip_wave_packet(
        config=config, target=target, skill=skill, mmm_sources=mmms
    )
    with pytest.raises(Exception) as caught:
        runner.execute_packet(packet.packet_bytes)
    assert getattr(caught.value, "reason_code", "") == "REFUSE_MD_AGENT_ROSTER_EXHAUSTED"
    detail = json.loads(caught.value.detail)
    assert detail["exhausted_agents"][0]["terminal_refusal"] == "REFUSE_MD_AGENT_OUTPUT_JSON"


def test_target_is_repeated_exactly_for_each_lens_and_member() -> None:
    packet, _config_value, target, _skill, _mmms = _packet()
    root = _entries(packet.packet_bytes)
    for lens in runner.LENSES:
        child = _entries(root[f"children/{lens}.zip"])
        assert child["input/target.bin"] == target
        manifest = json.loads(child["input/lens_manifest.json"])
        assert manifest["target_sha256"] == hashlib.sha256(target).hexdigest()
        roster = json.loads(child["inputs/roster.json"])
        assert all("input/target.bin" in row["context_paths"] for row in roster["agents"])


def test_missing_lens_member_is_refused() -> None:
    target, skill, mmms = _inputs()
    config = _config(member_count=1)
    with pytest.raises(Exception) as caught:
        runner.build_premortem_zip_wave_packet(config=config, target=target, skill=skill, mmm_sources=mmms)
    assert getattr(caught.value, "reason_code", "") == "REFUSE_PREMORTEM_MEMBER_COUNT"


def test_wrong_output_delivery_is_refused_before_build() -> None:
    target, skill, mmms = _inputs()
    config = _config()
    config["members"]["likely_failure"][0]["output_delivery"] = "worker_file"
    with pytest.raises(Exception) as caught:
        runner.build_premortem_zip_wave_packet(config=config, target=target, skill=skill, mmm_sources=mmms)
    assert getattr(caught.value, "reason_code", "") == "REFUSE_PREMORTEM_OUTPUT_DELIVERY"


def test_model_binding_mismatch_is_refused_after_provider_return() -> None:
    target, skill, mmms = _inputs()
    config = _config(require_binding=True)
    packet = runner.build_premortem_zip_wave_packet(config=config, target=target, skill=skill, mmm_sources=mmms)
    result = runner.execute_packet(packet.packet_bytes)
    with pytest.raises(Exception) as caught:
        runner.validate_premortem_zip_wave_return(packet.packet_bytes, result.return_zip_bytes)
    assert getattr(caught.value, "reason_code", "") == "REFUSE_PREMORTEM_MODEL_BINDING"


def test_retry_exhaustion_is_a_refusal_and_emits_no_wave_return() -> None:
    target, skill, mmms = _inputs()
    config = _config(mode="missing")
    packet = runner.build_premortem_zip_wave_packet(config=config, target=target, skill=skill, mmm_sources=mmms)
    with pytest.raises(Exception) as caught:
        runner.execute_packet(packet.packet_bytes)
    assert getattr(caught.value, "reason_code", "") == "REFUSE_MD_AGENT_ROSTER_EXHAUSTED"


def test_cancellation_does_not_build_or_call_children() -> None:
    target, skill, mmms = _inputs()
    receipt = runner.run_premortem_zip_wave(config=_config(), target=target, skill=skill, mmm_sources=mmms, cancel=True)
    assert receipt["disposition"] == "CANCELLED"
    assert receipt["stop_reason"] == "cancelled"
    assert receipt["rounds"] == []


def test_repair_callback_gets_temp_workspace_and_never_live_target(tmp_path: Path) -> None:
    target, skill, mmms = _inputs()
    original = bytes(target)
    seen: list[Path] = []

    def repair(receipt: dict, work: Path) -> bytes | None:
        seen.append(work)
        assert (work / "target.bin").read_bytes() == original
        assert (work / "receipt.json").is_file()
        return None

    result = runner.run_premortem_zip_wave(
        config=_config(), target=target, skill=skill, mmm_sources=mmms,
        repair_workspace=tmp_path, repair_callback=repair,
    )
    assert result["stop_reason"] == "no_material_delta"
    assert seen and all(path.parent == tmp_path for path in seen)
    assert target == original


def test_tampered_return_is_refused() -> None:
    packet, _config_value, _target, _skill, _mmms = _packet()
    result = runner.execute_packet(packet.packet_bytes)
    root = _entries(result.return_zip_bytes)
    child_entries = _entries(root["output/likely_failure.return.zip"])
    child_entries["output/lik-0.md"] += b"tamper\n"
    root["output/likely_failure.return.zip"] = runner.deterministic_zip(child_entries)
    tampered = runner.deterministic_zip(root)
    with pytest.raises(Exception) as caught:
        runner.validate_premortem_zip_wave_return(packet.packet_bytes, tampered)
    assert getattr(caught.value, "reason_code", "") == "REFUSE_RETURN_DIGEST_MISMATCH"


def test_malformed_cell_json_is_refused_by_cell_validator() -> None:
    with pytest.raises(Exception) as caught:
        runner._cell_fields({"schema": runner.CELL_SCHEMA}, lens="likely_failure", target_digest="a" * 64)
    assert getattr(caught.value, "reason_code", "") == "REFUSE_PREMORTEM_OUTPUT_SCHEMA"


def test_config_max_attempts_is_bound_in_wave_lens_and_roster_manifests() -> None:
    target, skill, mmms = _inputs()
    config = _config()
    config["max_attempts"] = 1
    packet = runner.build_premortem_zip_wave_packet(
        config=config, target=target, skill=skill, mmm_sources=mmms
    )
    root = _entries(packet.packet_bytes)
    wave = json.loads(root["inputs/wave_manifest.json"])

    assert wave["max_attempts"] == 1
    for lens in runner.LENSES:
        assert wave["lenses"][runner.LENSES.index(lens)]["max_attempts"] == 1
        child = _entries(root[f"children/{lens}.zip"])
        assert json.loads(child["input/lens_manifest.json"])["max_attempts"] == 1
        assert json.loads(child["inputs/roster.json"])["max_attempts"] == 1


def test_parent_lens_and_compiled_receipts_preserve_retry_summaries() -> None:
    target, skill, mmms = _inputs()
    config = _config(mode="invalid-json")
    packet = runner.build_premortem_zip_wave_packet(
        config=config, target=target, skill=skill, mmm_sources=mmms
    )
    result = runner.execute_packet(packet.packet_bytes)
    receipt = runner.validate_premortem_zip_wave_return(
        packet.packet_bytes, result.return_zip_bytes
    )

    assert receipt["max_attempts"] == config["max_attempts"]
    assert len(receipt["attempt_summaries"]) == 6
    assert len(receipt["compiled"]["attempt_summaries"]) == 6
    assert all(
        lens["max_attempts"] == config["max_attempts"]
        for lens in receipt["lens_receipts"]
    )
    assert receipt["compiled"]["max_attempts"] == config["max_attempts"]
    assert receipt["compiled"]["refusal_reason_summary"] == {
        "REFUSE_MD_AGENT_OUTPUT_JSON": 6,
    }
    assert receipt["mmm_read_proved"] is False
    assert receipt["skill_read_proved"] is False
    assert receipt["skill_executed"] is False
    assert receipt["accepted_attempt_count"] == 6
    assert receipt["accepted_attempts_consumed"] == 12
    assert receipt["refusal_reason_summary"] == {
        "REFUSE_MD_AGENT_OUTPUT_JSON": 6,
    }
    for lens in receipt["lens_receipts"]:
        assert len(lens["attempt_summaries"]) == 2
        assert all(
            summary["accepted_attempt_count"] == 2
            and summary["refusal_reason_summary"] == {"REFUSE_MD_AGENT_OUTPUT_JSON": 1}
            for summary in lens["attempt_summaries"]
        )
        assert lens["mmm_read_proved"] is False
        assert lens["skill_bytes_delivered"] is True
        assert lens["skill_read_proved"] is False
        assert lens["skill_executed"] is False


def test_absent_repair_callback_has_distinct_stop_reason() -> None:
    target, skill, mmms = _inputs()
    result = runner.run_premortem_zip_wave(
        config=_config(), target=target, skill=skill, mmm_sources=mmms
    )

    assert result["stop_reason"] == "repair_callback_absent"
    assert result["mmm_read_proved"] is False
    assert result["skill_read_proved"] is False
    assert result["skill_executed"] is False
    assert result["accepted_attempt_count"] == 6
    assert result["accepted_attempts_consumed"] == 6
    assert result["refusal_reason_summary"] == {}


===== FILE constraint_box/integrated_system/skills/cb-premortem-wave/wave.json sha256=770918546f6f2ed279c21b2208cf61b731b45a3aed3d8548be87ba147aee3be3 bytes=1236 =====
{
  "schema": "constraintbox.wave-definition.v1",
  "wave_id": "cb-premortem-wave-v1",
  "purpose": "Find prospective failure mechanisms, try finite repairs, and rerun the same lenses.",
  "children": [
    {"id": "likely_failure", "skill": "cb-premortem-cell", "operation": "likely_failure", "tools": ["source_inspection", "test_runner"]},
    {"id": "dangerous_failure", "skill": "cb-premortem-cell", "operation": "dangerous_failure", "tools": ["dependency_graph", "negative_tests"]},
    {"id": "hidden_assumption", "skill": "cb-premortem-cell", "operation": "hidden_assumption", "tools": ["contract_diff", "mutation_probe"]}
  ],
  "mmm_profile": {"loader_skill": "mmm-preload", "mini_voices_only": true, "voice_count_range": [2, 4], "distinct_sets_within_round": true},
  "loop": {"max_rounds": 3, "repair_then_exact_rerun": true, "stop_reasons": ["no_material_delta", "falsifiers_settled", "cancelled", "max_rounds"]},
  "completion": {"required_evidence": ["child_receipts", "preload_receipts", "provider_call_receipt", "cancellation_state", "disagreement_state", "output_digest", "repair_digest", "rerun_delta"]},
  "claim_ceiling": "Embedded prospective failure evidence only; no execution, promotion, or release authority."
}


===== FILE constraint_box/integrated_system/skills/cb-premortem-cell/SKILL.md sha256=96ed08391824d8a90b73bf93ee8af191c7b69eff49a55e7d5cc0095b0ccacc33 bytes=1926 =====
---
name: cb-premortem-cell
description: Run one digest-bound premortem lens inside a ConstraintBox ZIP cell.
---

# CB Premortem Cell

This is an embedded worker procedure, not a decision-maker. It receives one
exact target byte string, one assigned lens, one bounded compact mini-MMM
combination, and this skill file. The target bytes are immutable input.

The worker must return exactly one JSON object through the declared
`output_delivery=provider_response` route. The object must contain exactly:

```text
schema
lens
target_sha256
failure_mechanisms
evidence
limits
falsifier
warning
finite_repair
rerun_operation
claim_ceiling
```

`failure_mechanisms`, `evidence`, and `limits` are non-empty arrays of plain
strings. The other fields are non-empty strings. `lens` and `target_sha256`
must match the packet manifest. The response must not claim promotion,
authority, semantic consensus, or release.

The three admitted lenses are:

- `likely_failure`: the most likely concrete repeated-use failure;
- `dangerous_failure`: the most damaging authority, custody, or evidence
  failure, even if uncommon;
- `hidden_assumption`: an assumption that lets a passing receipt overstate
  what actually happened.

Use the supplied target and packet files only. Name direct evidence, a finite
falsifier, an early warning, a bounded repair, and the exact operation that
would rerun the check. Keep competing findings separate. Do not vote, select
a winner, edit live source, launch a child, or write an authoritative receipt.

The parent ZIP wave validates the JSON shape, target digest, provider/model
request binding, MMM and skill byte binding, ancestry, retry history, and
negative controls. A fluent answer without the exact JSON object is a refusal.

Claim ceiling: one bounded premortem observation for one packet target; not a
truth disposition, gate, promotion, release, or proof that a model understood
the MMM or skill.
