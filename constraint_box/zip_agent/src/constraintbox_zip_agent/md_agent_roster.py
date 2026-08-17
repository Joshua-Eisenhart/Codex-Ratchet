from __future__ import annotations

import os
import importlib.util
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

from constraintbox.mmm_load_gate import MmmLoadError, materialize_bound_prompt

from .protocol import TaskSpec, ZipJobRefusal, build_packet, canonical_json_bytes, sha256_bytes, strict_json_loads

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
    try:
        fields = materialize_bound_prompt(prompt_path, prompt_path)
    except MmmLoadError as exc:
        raise ZipJobRefusal(exc.reason_code, str(exc)) from exc
    request = dict(request)
    request["prompt_path"] = str(prompt_path)
    request["mmm_packs"] = list(fields["mmm_packs"])
    request["mmm_sha256"] = fields["mmm_sha256"]
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
    return (
        f"You are the markdown file {agent_rel}. That file is the agent.\n"
        "Read these files in this exact order before doing the task:\n"
        f"{files}\n"
        f"This is fresh attempt {attempt}. Deterministic attempt seed: {attempt_seed}\n"
        f"Prior deterministic refusal: {prior_refusal or 'none'}\n"
        f"{hierarchy_line}"
        f"Write ONLY {output_rel}. Create parent directories if needed.\n"
        f"The file must contain this exact marker: {marker}\n"
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


def _provider_env(provider: str) -> dict[str, str]:
    names = list(_PROVIDER_ENV_COMMON)
    names.extend(_PROVIDER_ENV_EXTRA.get(provider, ()))
    env = {name: os.environ[name] for name in names if name in os.environ and os.environ[name]}
    env["PYTHONNOUSERSITE"] = "1"
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["PYTHONPATH"] = str(Path(__file__).resolve().parents[3] / "src")
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


def _adapter_path(provider: str) -> Path:
    module_name = _ADAPTER_MODULES[provider]
    spec = importlib.util.find_spec(module_name)
    path = Path(spec.origin).resolve() if spec is not None and spec.origin else None
    if path is not None and path.is_file():
        return path
    sibling = (
        Path(__file__).resolve().parents[3]
        / "src"
        / "constraintbox"
        / f"{module_name.rsplit('.', 1)[-1]}.py"
    )
    if sibling.is_file():
        return sibling
    raise ZipJobRefusal("HOLD_PROVIDER_ADAPTER_MISSING", module_name)


def _argv(
    agent: dict[str, Any],
    work: Path,
    prompt_path: Path,
    *,
    request_id: str,
    timeout_seconds: int,
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
    env = _provider_env(provider)
    model = _text(agent.get("model_requested"), "model_requested")
    request_path = work / "meta" / "provider_request.json"
    response_path = work / "meta" / "provider_response.json"
    receipt_path = work / "meta" / "provider_receipt.json"
    hierarchy_request = _hierarchy_surface(hierarchy) if hierarchy is not None else {}
    if provider == "codex-cli":
        if agent.get("codex_home") is None:
            raise ZipJobRefusal("HOLD_CODEX_HOME_UNBOUND", "CODEX_HOME")
        runner = _declared_file(agent, "runner_path", executable=True)
        adapter = _adapter_path(provider)
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
            "sandbox_mode": "workspace-write",
            "prompt_path": str(prompt_path),
            "cwd": str(work),
        })))
        return (
            [sys.executable, "-m", _ADAPTER_MODULES[provider], "--request", str(request_path),
             "--response", str(response_path), "--receipt", str(receipt_path),
             "--timeout", str(timeout_seconds)],
            env, receipt_path,
        )
    if provider == "grok-cli":
        runner = _declared_file(agent, "runner_path", executable=True)
        adapter = _adapter_path(provider)
        request_path.write_bytes(canonical_json_bytes(_bind_adapter_mmm(work, prompt_path, {
            "schema": "constraintbox.grok-cli-request.v1",
            "request_id": request_id,
            **hierarchy_request,
            "runner_path": str(runner),
            "model": model,
            "prompt_path": str(prompt_path),
            "cwd": str(work),
            "max_turns": int(agent.get("max_turns") or 8),
            "permission_mode": "bypassPermissions",
        })))
        return (
            [sys.executable, "-m", _ADAPTER_MODULES[provider], "--request", str(request_path),
             "--response", str(response_path), "--receipt", str(receipt_path),
             "--timeout", str(timeout_seconds)],
            env, receipt_path,
        )
    if provider == "claude-code":
        _declared_file(agent, "runner_path", executable=True)
        adapter = _adapter_path(provider)
        bridge = _declared_file(agent, "bridge_path", executable=False)
        budget = agent.get("budget_usd", 1.0)
        if isinstance(budget, bool) or not isinstance(budget, (int, float)) or not 0.01 <= budget <= 5:
            raise ZipJobRefusal("REFUSE_MD_AGENT_ROSTER_SCHEMA", "budget_usd")
        request_path.write_bytes(canonical_json_bytes(_bind_adapter_mmm(work, prompt_path, {
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
            "tools": "Read,Write,Edit",
        })))
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
) -> dict[str, Any]:
    if provider == "fixture-subprocess":
        return {
            "provider_request_id": None,
            "model_observed": ["fixture-observed"],
            "model_binding_confirmed": False,
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
    return {
        "provider_request_id": request_id,
        "model_observed": observed,
        "model_binding_confirmed": True,
        "identity_source": "provider_adapter_receipt",
        "composed_prompt_sha256": sha256_bytes(prompt),
        "provider_source_receipt_sha256": sha256_bytes(raw),
        "provider_source_receipt": source,
    }


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
                    hierarchy=hierarchy,
                ),
                encoding="utf-8",
            )
            request_identity = {"run_id": run_id, "agent_id": agent_id, "attempt": attempt}
            if hierarchy is not None:
                request_identity.update(hierarchy_surface)
            request_id = "zip-" + sha256_bytes(canonical_json_bytes(request_identity))[:32]
            argv, env, evidence_path = _argv(
                agent,
                work,
                prompt_path,
                request_id=request_id,
                timeout_seconds=timeout_seconds,
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
                        }
                    )
                    continue
            marker_ok = marker.encode("utf-8") in body
            size_ok = exists and len(body) <= max_output_bytes
            try:
                text = body.decode("utf-8") if exists else ""
                utf8_ok = True
            except UnicodeDecodeError:
                text = ""
                utf8_ok = False
            fragments_ok = utf8_ok and all(fragment in text for fragment in required_fragments)
            missing_fragments = [fragment for fragment in required_fragments if fragment not in text]
            forbidden_ok = utf8_ok and all(fragment not in text for fragment in forbidden_fragments)
            present_forbidden_fragments = [fragment for fragment in forbidden_fragments if fragment in text]
            format_ok = size_ok and fragments_ok and forbidden_ok
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
            if not exists:
                refusal = "REFUSE_MD_AGENT_MISSING_OUTPUT"
            elif not size_ok:
                refusal = "REFUSE_MD_AGENT_OUTPUT_SIZE"
            elif not utf8_ok:
                refusal = "REFUSE_MD_AGENT_OUTPUT_UTF8"
            elif not marker_ok:
                refusal = "REFUSE_MD_AGENT_MARKER_MISSING"
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
            evidence_failure: str | None = None
            provider_receipt_summary: dict[str, Any] | None = None
            try:
                evidence = _provider_evidence(
                    provider=str(agent.get("provider")),
                    evidence_path=evidence_path,
                    request_id=request_id,
                    model_requested=agent.get("model_requested"),
                    prompt=prompt_bytes,
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
                    "model_binding_confirmed": False,
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
                "models_observed": evidence["model_observed"],
                "model_observed": evidence["model_observed"][0] if evidence["model_observed"] else None,
                "model_binding_confirmed": evidence["model_binding_confirmed"],
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
                "output_preview": text[:4096] if exists and utf8_ok else None,
            }
            attempts.append(row)
            if refusal is None:
                tool_result_consumed_on_later_attempt = cb_tool_executed
                return {
                    **hierarchy_surface,
                    "agent_id": agent_id,
                    "agent_path": agent_path,
                    "output_path": output_path,
                    "provider": agent["provider"],
                    "model_requested": agent.get("model_requested"),
                    "provider_request_id": evidence["provider_request_id"],
                    "models_observed": evidence["model_observed"],
                    "model_observed": evidence["model_observed"][0],
                    "model_binding_confirmed": evidence["model_binding_confirmed"],
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
                    "delivered_file_sha256": delivered_sha256,
                    "required_fragments": required_fragments,
                    "attempts": attempts,
                    "output_bytes": body,
                }
            last_error = refusal
    return {
        **hierarchy_surface,
        "agent_id": agent_id,
        "agent_path": agent_path,
        "output_path": output_path,
        "provider": agent["provider"],
        "model_requested": agent.get("model_requested"),
        "accepted": False,
        "accepted_attempt": None,
        "delivered_file_sha256": delivered_sha256,
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
        "max_turns", "runner_path", "bridge_path", "codex_home"
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
        refusal = {
            **hierarchy_surface,
            "schema": "constraintbox.md-agent-roster-refusal.v1",
            "run_id": run_id,
            "seed": roster_seed,
            "accepted_agent_ids": [result["agent_id"] for result in results if result["accepted"]],
            "exhausted_agents": [
                {
                    **hierarchy_surface,
                    "agent_id": result["agent_id"],
                    "terminal_refusal": result["terminal_refusal"],
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
            "agents": receipts,
            "execution_authorized_beyond_declared_outputs": False,
            "host_hooks_used": False,
            "mmm_read_proved": False,
            "skill_executed": False,
            "skill_bytes_consumed": True,
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
