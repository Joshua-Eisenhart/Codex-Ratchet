from __future__ import annotations

import math
import os
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
    requested = request["model_requested"]
    if provider == "grok-cli":
        # The Grok adapter explicitly permits only its provider build-usage
        # suffix; any other observed model is a mismatch, never a fallback.
        if observed not in {requested, f"{requested}-build"}:
            raise ZipJobRefusal("REFUSE_PROVIDER_MODEL_MISMATCH", observed)
    else:
        lowered = requested.lower()
        if lowered in {"sonnet", "haiku", "opus", "fable"}:
            matches = lowered in observed.lower()
        else:
            matches = observed == requested
        if not matches:
            raise ZipJobRefusal("REFUSE_PROVIDER_MODEL_MISMATCH", observed)
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
        "model_binding_confirmed": True,
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
