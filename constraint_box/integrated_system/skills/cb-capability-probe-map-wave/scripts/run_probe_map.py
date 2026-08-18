#!/usr/bin/env python3
"""Run the inactive capability/probe-map candidate.

The runner is deliberately an adapter around public operations.  It does not
reimplement structured probing or path-mass mathematics and it never writes an
active manifest, scheduler, launcher, or authority receipt.
"""

from __future__ import annotations

import argparse
import ast
import copy
import hashlib
import json
import os
import subprocess
import sys
import tempfile
from collections.abc import Mapping
from pathlib import Path
from typing import Any, Iterable


SCHEMA = "constraintbox.capability-probe-map-receipt.v1"
WAVE_ID = "cb-capability-probe-map-wave-v1"
CLAIM_CEILING = (
    "bounded capability binding and exact finite operation/replay evidence only; "
    "no manifold, basin, chirality, physical, provider, portability, activation, "
    "or promotion claim"
)
_CANDIDATE_DIR = Path(__file__).resolve().parents[1]
_DEFAULT_ROOT = Path(__file__).resolve().parents[5]
_EXTERNAL_IDENTITY = r'''
import importlib
import json
import sys

def module_identity(name):
    try:
        module = importlib.import_module(name)
        if name == "z3":
            version = str(module.get_version_string())
        else:
            version = str(getattr(module, "__version__", "unknown"))
        row = {"status": "BOUND", "version": version}
        if name == "jax":
            row["jaxlib_version"] = str(getattr(importlib.import_module("jaxlib"), "__version__", "unknown"))
            row["device_count"] = len(module.devices())
        return row
    except Exception as exc:
        return {"status": "HOLD", "reason": type(exc).__name__}

print(json.dumps({
    "python_version": sys.version.split()[0],
    "python_implementation": sys.implementation.name,
    "python_executable": sys.executable,
    "sys_prefix": sys.prefix,
    "sys_base_prefix": sys.base_prefix,
    "libraries": {
        "jax": module_identity("jax"),
        "z3": module_identity("z3"),
        "cvc5": module_identity("cvc5"),
    },
}, sort_keys=True))
'''

# The subprocess environment is intentionally an allowlist.  In particular,
# no inherited credentials, proxy settings, user paths, or model variables are
# passed to a public operation.
_SUBPROCESS_ENV = {
    "PYTHONNOUSERSITE": "1",
    "PYTHONDONTWRITEBYTECODE": "1",
    "JAX_PLATFORMS": "cpu",
    "JAX_ENABLE_X64": "true",
    "CUDA_VISIBLE_DEVICES": "",
}
REQUIRED_NEGATIVE_CONTROL_IDS = (
    "structured_missing_observation",
    "structured_promotion_true",
    "path_missing_row",
    "unknown_probe",
    "foreign_policy",
    "tampered_replay",
)
_PATH_NEGATIVE_ID_MAP = {
    "missing_observation_row": "path_missing_row",
    "unknown_probe_request": "unknown_probe",
    "foreign_policy_request": "foreign_policy",
}


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def digest(value: Any) -> str:
    return sha256_bytes(canonical_bytes(value))


def environment_projection() -> dict[str, Any]:
    variables = dict(_SUBPROCESS_ENV)
    return {
        "variables": variables,
        "sha256": digest(variables),
        "credentials_passed": False,
    }


def _runtime_source_sha256() -> str:
    return sha256_bytes(_EXTERNAL_IDENTITY.encode("utf-8"))


def file_digest(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def relative_path(root: Path, path: Path) -> str:
    """Use stable root-relative paths; external runtime paths stay explicit."""

    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return str(path.resolve())


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def parse_json_output(text: str) -> dict[str, Any] | None:
    """Parse a JSON object from a quiet public wrapper or its final line."""

    candidates = [text.strip()]
    candidates.extend(line.strip() for line in reversed(text.splitlines()))
    for candidate in candidates:
        if not candidate:
            continue
        try:
            value = json.loads(candidate)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            return value
    return None


def _run(
    command: list[str],
    *,
    cwd: Path,
    timeout: float = 120.0,
    input_text: str | None = None,
) -> dict[str, Any]:
    env_receipt = environment_projection()
    env = dict(env_receipt["variables"])
    try:
        completed = subprocess.run(
            command,
            cwd=str(cwd),
            input=input_text,
            capture_output=True,
            text=True,
            check=False,
            env=env,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout if isinstance(exc.stdout, str) else ""
        stderr = exc.stderr if isinstance(exc.stderr, str) else ""
        return {
            "returncode": None,
            "stdout": stdout,
            "stderr": stderr,
            "timed_out": True,
            "environment": env_receipt,
            "stdout_sha256": sha256_bytes(stdout.encode("utf-8")),
            "stderr_sha256": sha256_bytes(stderr.encode("utf-8")),
        }
    except OSError as exc:
        detail = f"{type(exc).__name__}:{exc}"
        return {
            "returncode": None,
            "stdout": "",
            "stderr": detail,
            "timed_out": False,
            "os_error": type(exc).__name__,
            "environment": env_receipt,
            "stdout_sha256": sha256_bytes(b""),
            "stderr_sha256": sha256_bytes(detail.encode("utf-8")),
        }
    return {
        "returncode": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
        "timed_out": False,
        "environment": env_receipt,
        "stdout_sha256": sha256_bytes(completed.stdout.encode("utf-8")),
        "stderr_sha256": sha256_bytes(completed.stderr.encode("utf-8")),
    }


def _candidate_fixture(name: str) -> Path:
    path = _CANDIDATE_DIR / "fixtures" / name
    if not path.is_file():
        raise FileNotFoundError(path)
    return path.resolve()


def _source_candidates(root: Path, relative: str) -> Iterable[Path]:
    direct = root / relative
    yield direct
    # The public path-mass wrapper uses the merged controller closure when the
    # normal source tree is absent.  Keep binding and execution on that same
    # selection rule.
    if relative.startswith("constraint_box/src/constraintbox/"):
        suffix = relative.removeprefix("constraint_box/src/constraintbox/")
        yield root / "constraint_box" / "integrated_system" / "runtime" / "controller_src" / "constraintbox" / suffix
        yield root / "constraint_box" / "light_runtime" / "src" / "constraintbox" / suffix


def resolve_source(root: Path, relative: str) -> Path | None:
    return next((candidate.resolve() for candidate in _source_candidates(root, relative) if candidate.is_file()), None)


def _ast_symbols(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    found: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            found.add(node.name)
    return found


def _source_binding(root: Path, capability_id: str, spec: dict[str, Any]) -> dict[str, Any]:
    source = resolve_source(root, str(spec["source"]))
    result: dict[str, Any] = {
        "capability": capability_id,
        "operation": spec.get("operation"),
        "kind": spec.get("kind"),
        "api": spec.get("api"),
        "declared_source": str(spec["source"]),
        "symbols_required": list(spec.get("symbols", [])),
        "status": "BOUND",
    }
    if source is None:
        result.update({"status": "REFUSE", "reason": "REFUSE_PUBLIC_SOURCE_MISSING"})
        return result
    result["source"] = {
        "path": relative_path(root, source),
        "sha256": file_digest(source),
    }
    wrapper_name = spec.get("wrapper")
    if wrapper_name:
        wrapper = resolve_source(root, str(wrapper_name))
        if wrapper is None:
            result.update({"status": "REFUSE", "reason": "REFUSE_PUBLIC_WRAPPER_MISSING"})
            return result
        wrapper_sha256 = file_digest(wrapper)
        expected_wrapper_sha256 = spec.get("wrapper_sha256")
        result["wrapper"] = {
            "path": relative_path(root, wrapper),
            "sha256": wrapper_sha256,
            "expected_sha256": expected_wrapper_sha256,
            "digest_match": expected_wrapper_sha256 == wrapper_sha256,
        }
        if expected_wrapper_sha256 != wrapper_sha256:
            result.update(
                {
                    "status": "REFUSE",
                    "reason": "REFUSE_PUBLIC_WRAPPER_DIGEST_MISMATCH",
                }
            )
            return result
    try:
        symbols = _ast_symbols(source)
    except (OSError, SyntaxError, UnicodeError) as exc:
        result.update(
            {
                "status": "REFUSE",
                "reason": "REFUSE_PUBLIC_SOURCE_UNREADABLE",
                "detail": type(exc).__name__,
            }
        )
        return result
    required = {str(item) for item in spec.get("symbols", [])}
    missing = sorted(required - symbols)
    result["symbols_present"] = sorted(required & symbols)
    if missing:
        result.update(
            {
                "status": "REFUSE",
                "reason": "REFUSE_PUBLIC_API_SYMBOL_MISSING",
                "missing_symbols": missing,
            }
        )
    return result


def _process_evidence(observed: dict[str, Any]) -> dict[str, Any]:
    return {
        key: observed[key]
        for key in (
            "returncode",
            "timed_out",
            "stdout_sha256",
            "stderr_sha256",
            "environment",
        )
        if key in observed
    }


def _runtime_identity(
    interpreter: Path,
    root: Path,
    *,
    capability: str,
    label: str,
    require_jax: bool,
) -> dict[str, Any]:
    result: dict[str, Any] = {
        "capability": capability,
        "operation": "runtime_identity.v1",
        "declared": True,
        "status": "HOLD",
        "api": "python -I -c runtime_identity",
        "runtime_label": label,
        "required_libraries": ["z3", "cvc5"] + (["jax"] if require_jax else []),
    }
    if not interpreter.is_absolute():
        result.update({"status": "REFUSE", "reason": "REFUSE_RUNTIME_INTERPRETER_NOT_ABSOLUTE"})
        return result
    if not interpreter.is_file():
        result["reason"] = "RUNTIME_INTERPRETER_NOT_REGULAR_FILE"
        return result
    try:
        resolved = interpreter.resolve(strict=True)
        result["interpreter"] = {
            "declared_path": str(interpreter),
            "resolved_path": str(resolved),
            "sha256": file_digest(resolved),
        }
    except OSError as exc:
        result.update({"reason": "RUNTIME_INTERPRETER_UNREADABLE", "detail": type(exc).__name__})
        return result
    invocation = [str(interpreter), "-I", "-c", "runtime_identity"]
    observed = _run(
        [str(interpreter), "-I", "-c", _EXTERNAL_IDENTITY],
        cwd=root,
        timeout=30.0,
    )
    result["invocation"] = {
        "argv": invocation,
        "argv_sha256": digest(invocation),
        "source_sha256": _runtime_source_sha256(),
        "process": _process_evidence(observed),
    }
    if observed["returncode"] != 0:
        result["reason"] = "RUNTIME_IDENTITY_FAILED"
        return result
    body = parse_json_output(str(observed["stdout"]))
    if not isinstance(body, dict):
        result["reason"] = "RUNTIME_IDENTITY_RESPONSE_INVALID"
        return result
    libraries = body.get("libraries")
    if not isinstance(libraries, dict):
        result["reason"] = "RUNTIME_IDENTITY_LIBRARIES_INVALID"
        return result
    missing = [
        name
        for name in result["required_libraries"]
        if not isinstance(libraries.get(name), dict)
        or libraries[name].get("status") != "BOUND"
    ]
    result["runtime"] = body
    result["runtime_sha256"] = digest(body)
    result["missing_libraries"] = missing
    if missing:
        result["reason"] = "RUNTIME_LIBRARY_NOT_BOUND"
        return result
    result["status"] = "BOUND"
    return result


def controller_runtime_identity(root: Path) -> dict[str, Any]:
    return _runtime_identity(
        Path(sys.executable).absolute(),
        root,
        capability="controller_runtime",
        label="controller",
        require_jax=False,
    )


def external_jax_identity(
    interpreter: Path | None,
    root: Path,
    controller: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if interpreter is None:
        return {
            "capability": "external_jax_identity",
            "operation": "declared_external_jax_interpreter.v1",
            "declared": False,
            "status": "HOLD",
            "reason": "JAX_INTERPRETER_UNDECLARED",
            "api": "declared-interpreter -I -c import jax,z3,cvc5",
        }
    if not interpreter.is_absolute():
        return {
            "capability": "external_jax_identity",
            "operation": "declared_external_jax_interpreter.v1",
            "declared": True,
            "status": "REFUSE",
            "reason": "REFUSE_JAX_INTERPRETER_NOT_ABSOLUTE",
            "api": "declared-interpreter -I -c import jax,z3,cvc5",
        }
    if interpreter.absolute() == Path(sys.executable).absolute():
        return {
            "capability": "external_jax_identity",
            "operation": "declared_external_jax_interpreter.v1",
            "declared": True,
            "status": "HOLD",
            "reason": "REFUSE_JAX_INTERPRETER_NOT_EXTERNAL",
            "api": "declared-interpreter -I -c import jax,z3,cvc5",
        }
    controller = controller or controller_runtime_identity(root)
    result = _runtime_identity(
        interpreter,
        root,
        capability="external_jax_identity",
        label="external_jax",
        require_jax=True,
    )
    controller_runtime = controller.get("runtime") if isinstance(controller, dict) else None
    external_runtime = result.get("runtime")
    controller_prefix = controller_runtime.get("sys_prefix") if isinstance(controller_runtime, dict) else sys.prefix
    external_prefix = external_runtime.get("sys_prefix") if isinstance(external_runtime, dict) else None
    same_prefix = external_prefix is not None and external_prefix == controller_prefix
    result["prefix_comparison"] = {
        "controller_sys_prefix": controller_prefix,
        "external_sys_prefix": external_prefix,
        "same_prefix": same_prefix,
        "separate": external_prefix is not None and not same_prefix,
    }
    if same_prefix:
        result["status"] = "HOLD"
        result["reason"] = "REFUSE_JAX_RUNTIME_SAME_PREFIX"
        return result
    if result.get("status") == "BOUND":
        result["prefix_comparison"]["separate"] = True
    return result


def bind_capabilities(root: Path, interpreter: Path | None) -> dict[str, Any]:
    registry_path = _CANDIDATE_DIR / "registry.json"
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    if registry.get("schema") != "constraintbox.capability-probe-map-registry.v1":
        raise ValueError("candidate capability registry schema")
    capabilities = registry.get("capabilities")
    if not isinstance(capabilities, dict):
        raise ValueError("candidate capability registry capabilities")
    controller = controller_runtime_identity(root)
    external = external_jax_identity(interpreter, root, controller)
    controller_libraries = controller.get("runtime", {}).get("libraries", {}) if isinstance(controller.get("runtime"), dict) else {}
    runtime_status = {
        "controller_runtime": controller.get("status"),
        "controller_z3_runtime": controller_libraries.get("z3", {}).get("status"),
        "controller_cvc5_runtime": controller_libraries.get("cvc5", {}).get("status"),
        "external_jax_runtime": external.get("status"),
    }
    rows: list[dict[str, Any]] = []
    for capability_id, spec in capabilities.items():
        if capability_id == "external_jax_identity":
            rows.append(external)
            continue
        if not isinstance(spec, dict):
            rows.append({"capability": capability_id, "status": "REFUSE", "reason": "REFUSE_REGISTRY_ROW"})
            continue
        row = _source_binding(root, capability_id, spec)
        if row["status"] == "BOUND" and spec.get("requires"):
            missing_runtime = [
                requirement
                for requirement in spec.get("requires", [])
                if (
                    requirement in runtime_status
                    and runtime_status[requirement] != "BOUND"
                )
                or (
                    requirement not in runtime_status
                    and not any(
                        item["capability"] == requirement and item["status"] == "BOUND"
                        for item in rows
                    )
                )
            ]
            if missing_runtime:
                row["status"] = "HOLD"
                row["reason"] = "RUNTIME_REQUIREMENT_NOT_BOUND"
                row["missing_runtime"] = missing_runtime
        if row["status"] == "BOUND" and capability_id == "path_mass_replay" and not any(
            item["capability"] == "path_mass" and item["status"] == "BOUND" for item in rows
        ):
            row["status"] = "HOLD"
            row["reason"] = "PATH_MASS_API_NOT_BOUND"
        rows.append(row)
    unbound = [
        {
            "capability": row.get("capability"),
            "status": row.get("status"),
            "reason": row.get("reason"),
        }
        for row in rows
        if row.get("status") != "BOUND"
    ]
    if any(row.get("status") == "REFUSE" for row in rows):
        status = "REFUSE"
    elif unbound:
        status = "HOLD"
    else:
        status = "BOUND"
    return {
        "schema": "constraintbox.capability-binding.v1",
        "status": status,
        "candidate_state": "NEW_CANDIDATE",
        "registry": {
            "path": relative_path(root, registry_path),
            "sha256": file_digest(registry_path),
        },
        "runtime_bindings": {
            "controller": controller,
            "external_jax": external,
            "requirements": runtime_status,
            "environment_projection": environment_projection(),
        },
        "capabilities": rows,
        "bound": [row for row in rows if row.get("status") == "BOUND"],
        "unbound": unbound,
        "promotion_allowed": False,
    }


def _run_structured(
    root: Path,
    fixture: Path,
    *,
    engine: str,
    interpreter: Path,
    temporary_root: Path,
    label: str,
) -> dict[str, Any]:
    script = resolve_source(root, "constraint_box/integrated_system/scripts/structured_open_bind_probe.py")
    if script is None:
        return {"status": "REFUSE", "reason": "REFUSE_STRUCTURED_SCRIPT_MISSING", "engine": engine}
    output = temporary_root / f"structured-{label}.json"
    command = [
        str(interpreter),
        "-I",
        str(script),
        "--input",
        str(fixture),
        "--output",
        str(output),
        "--engine",
        engine,
    ]
    observed = _run(command, cwd=root, timeout=120.0)
    body: dict[str, Any] | None = None
    if output.is_file():
        try:
            loaded = json.loads(output.read_text(encoding="utf-8"))
            body = loaded if isinstance(loaded, dict) else None
        except (OSError, UnicodeError, json.JSONDecodeError):
            body = None
    if body is None:
        body = parse_json_output(str(observed["stdout"]))
    status = str(body.get("status")) if body else "HOLD"
    if observed["returncode"] not in (0, 2):
        status = "HOLD"
    invocation = [
        "declared_external_jax_python" if engine == "dual" else "controller_python",
        "-I",
        relative_path(root, script),
        "--input",
        relative_path(root, fixture),
        "--output",
        "<temporary-output>",
        "--engine",
        engine,
    ]
    return {
        "operation": "structured_open_bind_probe.v1",
        "api": f"evaluate(raw, engine={engine!r})",
        "engine": engine,
        "runtime": "declared_external_jax_python" if engine == "dual" else "controller_python",
        "command": invocation,
        "invocation": {
            "argv": invocation,
            "argv_sha256": digest(invocation),
            "source_sha256": file_digest(script),
            "process": _process_evidence(observed),
        },
        "process": _process_evidence(observed),
        "status": status,
        "result": body,
        "result_sha256": digest(body) if body is not None else None,
        "source_sha256": body.get("source_sha256") if isinstance(body, dict) else None,
        "fixture_sha256": body.get("fixture_sha256") if isinstance(body, dict) else None,
    }


def _typed_path_mass_request(receipt: Any) -> Mapping[str, Any] | None:
    if not isinstance(receipt, Mapping):
        return None
    request = receipt.get("request")
    return request if isinstance(request, Mapping) else None


def _run_path_mass(
    root: Path,
    fixture: Path,
    interpreter: Path,
    temporary_root: Path,
) -> dict[str, Any]:
    wrapper = resolve_source(root, "constraint_box/integrated_system/scripts/run_constraint_path_mass.py")
    source = resolve_source(root, "constraint_box/src/constraintbox/constraint_path_mass.py")
    if wrapper is None or source is None:
        return {
            "operation": "constraint_path_mass.v1",
            "status": "REFUSE",
            "reason": "REFUSE_PATH_MASS_PUBLIC_SOURCE_MISSING",
        }
    output = temporary_root / "constraint-path-mass.json"
    command = [
        sys.executable,
        "-I",
        str(wrapper),
        "--out",
        str(output),
        "--fixture",
        str(fixture),
        "--jax-python",
        str(interpreter),
        "--require-jax",
    ]
    observed = _run(command, cwd=root, timeout=180.0)
    # The public wrapper's human summary includes the caller-selected output
    # path.  That path is intentionally temporary here, so bind a canonical
    # summary digest rather than leaking a per-run temp-directory name into
    # this deterministic candidate receipt.
    summary = parse_json_output(str(observed["stdout"]))
    if isinstance(summary, dict) and "out" in summary:
        stable_summary = dict(summary)
        stable_summary["out"] = "<temporary-output>"
        observed["stdout_sha256"] = digest(stable_summary)
    receipt: dict[str, Any] | None = None
    if output.is_file():
        try:
            loaded = json.loads(output.read_text(encoding="utf-8"))
            receipt = loaded if isinstance(loaded, dict) else None
        except (OSError, UnicodeError, json.JSONDecodeError):
            receipt = None
    request = _typed_path_mass_request(receipt)
    status = str(receipt.get("status")) if receipt else "HOLD"
    reason: str | None = None
    if receipt is not None and request is None:
        status = "HOLD"
        reason = "HOLD_PATH_MASS_RECEIPT_REQUEST_INVALID"
    if observed["returncode"] not in (0, 2):
        status = "HOLD"
    invocation = [
        "controller_python",
        "-I",
        relative_path(root, wrapper),
        "--out",
        "<temporary-output>",
        "--fixture",
        relative_path(root, fixture),
        "--jax-python",
        "declared_external_jax_python",
        "--require-jax",
    ]
    replay: dict[str, Any] | None = None
    tampered: dict[str, Any] | None = None
    replay_invocation: dict[str, Any] | None = None
    tampered_invocation: dict[str, Any] | None = None
    if receipt is not None and request is not None and status == "PASS":
        replay_command = [
            sys.executable,
            "-I",
            str(wrapper),
            "--replay",
            str(output),
            "--fixture",
            str(fixture),
            "--jax-python",
            str(interpreter),
        ]
        replay_process = _run(replay_command, cwd=root, timeout=180.0)
        replay_argv = [
            "controller_python",
            "-I",
            relative_path(root, wrapper),
            "--replay",
            "<temporary-output>",
            "--fixture",
            relative_path(root, fixture),
            "--jax-python",
            "declared_external_jax_python",
        ]
        replay_invocation = {
            "argv": replay_argv,
            "argv_sha256": digest(replay_argv),
            "source_sha256": file_digest(wrapper),
            "process": _process_evidence(replay_process),
        }
        replay = parse_json_output(str(replay_process["stdout"]))
        if replay is None:
            replay = {
                "status": "HOLD",
                "reason": "REPLAY_RESPONSE_INVALID",
                "process": {
                    **_process_evidence(replay_process),
                },
                "promotion_allowed": False,
            }
        else:
            replay["process"] = _process_evidence(replay_process)
            replay["original_receipt_sha256"] = receipt.get("receipt_sha256")
            if replay.get("status") == "PASS" and (
                replay_process.get("returncode") != 0
                or replay.get("stored_receipt_sha256") != receipt.get("receipt_sha256")
                or replay.get("stored_receipt_sha256") != replay.get("replayed_receipt_sha256")
            ):
                replay["status"] = "HOLD"
                replay["reason"] = "REPLAY_EXACTNESS_FAILED"

        tampered_file = temporary_root / "constraint-path-mass-tampered.json"
        tampered_body = copy.deepcopy(receipt)
        tampered_body["claim_ceiling"] = str(tampered_body.get("claim_ceiling", "")) + " [tampered]"
        write_json(tampered_file, tampered_body)
        tampered_process = _run(
            [
                sys.executable,
                "-I",
                str(wrapper),
                "--replay",
                str(tampered_file),
                "--fixture",
                str(fixture),
                "--jax-python",
                str(interpreter),
            ],
            cwd=root,
            timeout=180.0,
        )
        tampered_argv = [
            "controller_python",
            "-I",
            relative_path(root, wrapper),
            "--replay",
            "<temporary-tampered-output>",
            "--fixture",
            relative_path(root, fixture),
            "--jax-python",
            "declared_external_jax_python",
        ]
        tampered_invocation = {
            "argv": tampered_argv,
            "argv_sha256": digest(tampered_argv),
            "source_sha256": file_digest(wrapper),
            "process": _process_evidence(tampered_process),
        }
        tampered = parse_json_output(str(tampered_process["stdout"])) or {
            "status": "HOLD",
            "reason": "TAMPER_RESPONSE_INVALID",
            "promotion_allowed": False,
        }
        tampered["process"] = {
            **_process_evidence(tampered_process),
        }
    return {
        "operation": "constraint_path_mass.v1",
        "api": "ConstraintPathMassRequest + run_constraint_path_mass + write_receipt",
        "wrapper": relative_path(root, wrapper),
        "source": {
            "path": relative_path(root, source),
            "sha256": file_digest(source),
        },
        "runtime": "controller_python_with_declared_external_jax",
        "command": invocation,
        "invocation": {
            "argv": invocation,
            "argv_sha256": digest(invocation),
            "source_sha256": file_digest(wrapper),
            "process": _process_evidence(observed),
        },
        "process": _process_evidence(observed),
        "status": status,
        "reason": reason,
        "receipt": receipt,
        "source_sha256": receipt.get("source_sha256") if receipt else None,
        "fixture_sha256": request.get("fixture_sha256") if request is not None else None,
        "request_mapping_valid": request is not None,
        "wrapper_sha256": file_digest(wrapper),
        "replay_wrapper_sha256": file_digest(wrapper),
        "receipt_sha256": receipt.get("receipt_sha256") if receipt else None,
        "replay": replay,
        "replay_invocation": replay_invocation,
        "tampered_replay": tampered,
        "tampered_replay_invocation": tampered_invocation,
    }


def _structured_negative_controls(
    root: Path,
    fixture: Path,
    temporary_root: Path,
) -> list[dict[str, Any]]:
    try:
        raw = json.loads(fixture.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        return [{
            "id": "structured_fixture_load",
            "expected_status": "PASS",
            "status": "REFUSE",
            "reason": type(exc).__name__,
            "passed": False,
        }]
    controls: list[dict[str, Any]] = []
    missing = copy.deepcopy(raw)
    missing["observations"] = missing["observations"][:-1]
    missing_path = temporary_root / "structured-missing-observation.json"
    write_json(missing_path, missing)
    missing_result = _run_structured(
        root,
        missing_path,
        engine="exact",
        interpreter=Path(sys.executable),
        temporary_root=temporary_root,
        label="negative-missing",
    )
    missing_body = missing_result.get("result") or {}
    controls.append(
        {
            "id": "structured_missing_observation",
            "expected_status": "REFUSE",
            "expected_reason": "REFUSE_UNBOUND_OBSERVATION",
            "status": missing_body.get("status"),
            "reason": missing_body.get("reason_code"),
            "passed": (
                missing_body.get("status") == "REFUSE"
                and missing_body.get("reason_code") == "REFUSE_UNBOUND_OBSERVATION"
            ),
        }
    )
    promoted = copy.deepcopy(raw)
    promoted["promotion_allowed"] = True
    promoted_path = temporary_root / "structured-promotion-true.json"
    write_json(promoted_path, promoted)
    promoted_result = _run_structured(
        root,
        promoted_path,
        engine="exact",
        interpreter=Path(sys.executable),
        temporary_root=temporary_root,
        label="negative-promotion",
    )
    promoted_body = promoted_result.get("result") or {}
    controls.append(
        {
            "id": "structured_promotion_true",
            "expected_status": "REFUSE",
            "expected_reason": "REFUSE_FIXTURE_SCHEMA",
            "status": promoted_body.get("status"),
            "reason": promoted_body.get("reason_code"),
            "passed": (
                promoted_body.get("status") == "REFUSE"
                and promoted_body.get("reason_code") == "REFUSE_FIXTURE_SCHEMA"
            ),
        }
    )
    return controls


def _path_negative_controls(path_result: dict[str, Any]) -> list[dict[str, Any]]:
    controls: list[dict[str, Any]] = []
    receipt = path_result.get("receipt")
    for item in (receipt or {}).get("negative_controls", []):
        if not isinstance(item, dict):
            continue
        expected_status = item.get("expected_status")
        expected_reason = item.get("reason_code")
        observed_status = item.get("status")
        observed_reason = item.get("observed_reason", item.get("reason_code"))
        normalized_id = _PATH_NEGATIVE_ID_MAP.get(str(item.get("id")))
        if normalized_id is None:
            normalized_id = f"unexpected_path_control:{item.get('id', 'unknown')}"
        controls.append(
            {
                "id": normalized_id,
                "expected_status": expected_status,
                "expected_reason": expected_reason,
                "status": observed_status,
                "reason": observed_reason,
                "passed": observed_status == expected_status and (
                    observed_reason == expected_reason or expected_reason is None
                ),
            }
        )
    tampered = path_result.get("tampered_replay")
    if isinstance(tampered, dict):
        controls.append(
            {
                "id": "tampered_replay",
                "expected_status": "HOLD",
                "expected_reason": "REPLAY_RECEIPT_MISMATCH",
                "status": tampered.get("status"),
                "reason": tampered.get("reason"),
                "passed": tampered.get("status") == "HOLD" and tampered.get("reason") == "REPLAY_RECEIPT_MISMATCH",
            }
        )
    return controls


def canonical_json_file_digest(path: Path) -> str:
    """Match structured probe's canonical JSON fixture digest contract."""

    return digest(json.loads(path.read_text(encoding="utf-8")))


def _bound_source_sha256(binding: dict[str, Any], capability: str) -> str | None:
    for row in binding.get("capabilities", binding.get("bound", [])):
        if row.get("capability") == capability:
            source = row.get("source")
            if isinstance(source, dict) and isinstance(source.get("sha256"), str):
                return source["sha256"]
    return None


def _bound_wrapper_sha256(binding: dict[str, Any], capability: str) -> str | None:
    for row in binding.get("capabilities", binding.get("bound", [])):
        if row.get("capability") == capability:
            wrapper = row.get("wrapper")
            if isinstance(wrapper, Mapping) and isinstance(wrapper.get("sha256"), str):
                return wrapper["sha256"]
    return None


def check_source_fixture_bindings(
    binding: dict[str, Any],
    exact: dict[str, Any],
    dual: dict[str, Any],
    path_mass: dict[str, Any],
    structured_fixture: Path,
    path_fixture: Path,
) -> dict[str, Any]:
    """Cross-check child claims against the sources bound before execution."""

    expected_structured_source = _bound_source_sha256(binding, "structured_probe_exact")
    expected_dual_source = _bound_source_sha256(binding, "structured_probe_dual")
    expected_path_source = _bound_source_sha256(binding, "path_mass")
    expected_path_wrapper = _bound_wrapper_sha256(binding, "path_mass")
    expected_replay_wrapper = _bound_wrapper_sha256(binding, "path_mass_replay")
    expected_structured_fixture = canonical_json_file_digest(structured_fixture)
    expected_path_fixture = file_digest(path_fixture)
    exact_result = exact.get("result") if isinstance(exact.get("result"), Mapping) else {}
    dual_result = dual.get("result") if isinstance(dual.get("result"), Mapping) else {}
    path_receipt = path_mass.get("receipt") if isinstance(path_mass.get("receipt"), Mapping) else {}
    path_request = path_receipt.get("request") if isinstance(path_receipt.get("request"), Mapping) else {}
    observed = {
        "structured_exact_source": exact_result.get("source_sha256"),
        "structured_exact_fixture": exact_result.get("fixture_sha256"),
        "structured_dual_source": dual_result.get("source_sha256"),
        "structured_dual_fixture": dual_result.get("fixture_sha256"),
        "path_mass_source": path_receipt.get("source_sha256") or path_mass.get("source_sha256"),
        "path_mass_fixture": path_request.get("fixture_sha256") or path_mass.get("fixture_sha256"),
        "path_mass_wrapper": path_mass.get("wrapper_sha256"),
        "path_mass_replay_wrapper": path_mass.get("replay_wrapper_sha256"),
    }
    expected = {
        "structured_exact_source": expected_structured_source,
        "structured_exact_fixture": expected_structured_fixture,
        "structured_dual_source": expected_dual_source,
        "structured_dual_fixture": expected_structured_fixture,
        "path_mass_source": expected_path_source,
        "path_mass_fixture": expected_path_fixture,
        "path_mass_wrapper": expected_path_wrapper,
        "path_mass_replay_wrapper": expected_replay_wrapper,
    }
    checks = {
        key: isinstance(observed[key], str)
        and isinstance(expected[key], str)
        and observed[key] == expected[key]
        for key in expected
    }
    return {
        "status": "PASS" if all(checks.values()) else "HOLD",
        "all_pass": all(checks.values()),
        "checks": checks,
        "expected": expected,
        "observed": observed,
        "promotion_allowed": False,
    }


def structured_results_agree(exact: dict[str, Any], dual: dict[str, Any]) -> bool:
    """Compare only present structured mappings; absent values never agree."""

    exact_result = exact.get("result") if isinstance(exact.get("result"), Mapping) else None
    dual_result = dual.get("result") if isinstance(dual.get("result"), Mapping) else None
    exact_metrics = exact_result.get("structured") if isinstance(exact_result, Mapping) else None
    dual_metrics = dual_result.get("structured") if isinstance(dual_result, Mapping) else None
    return (
        isinstance(exact_metrics, Mapping)
        and isinstance(dual_metrics, Mapping)
        and exact_metrics == dual_metrics
    )


def validate_negative_control_matrix(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Require exactly the declared negative-control IDs, once each."""

    required = set(REQUIRED_NEGATIVE_CONTROL_IDS)
    observed_ids = [str(row.get("id")) for row in rows if isinstance(row, dict)]
    observed_set = set(observed_ids)
    duplicates = sorted({item for item in observed_ids if observed_ids.count(item) > 1})
    missing = sorted(required - observed_set)
    unexpected = sorted(observed_set - required)
    row_pass = bool(rows) and all(bool(row.get("passed")) for row in rows)
    if unexpected:
        status = "REFUSE"
    elif missing or duplicates or not row_pass:
        status = "HOLD"
    else:
        status = "PASS"
    return {
        "status": status,
        "all_pass": status == "PASS",
        "required_ids": list(REQUIRED_NEGATIVE_CONTROL_IDS),
        "observed_ids": observed_ids,
        "missing_ids": missing,
        "duplicate_ids": duplicates,
        "unexpected_ids": unexpected,
        "rows": rows,
        "promotion_allowed": False,
    }


def replay_result_passes(path_mass: Mapping[str, Any]) -> bool:
    """Require process success and a three-way receipt-hash equality."""

    original = path_mass.get("receipt_sha256")
    replay = path_mass.get("replay")
    if not isinstance(replay, Mapping):
        return False
    process = replay.get("process")
    if not isinstance(process, Mapping) or process.get("returncode") != 0:
        return False
    stored = replay.get("stored_receipt_sha256")
    replayed = replay.get("replayed_receipt_sha256")
    return (
        replay.get("status") == "PASS"
        and isinstance(original, str)
        and original == stored == replayed
    )


def _base_receipt(root: Path, binding: dict[str, Any]) -> dict[str, Any]:
    definition = _CANDIDATE_DIR / "wave.json"
    registry = _CANDIDATE_DIR / "registry.json"
    definition_body = json.loads(definition.read_text(encoding="utf-8"))
    runtime_bindings = binding.get("runtime_bindings")
    return {
        "schema": SCHEMA,
        "wave_id": WAVE_ID,
        "candidate_state": "NEW_CANDIDATE",
        "activated": False,
        "promotion_allowed": False,
        "claim_ceiling": CLAIM_CEILING,
        "root": {
            "path": "<repository-root>",
            "definition_sha256": file_digest(definition),
            "registry_sha256": file_digest(registry),
            "runner_sha256": file_digest(Path(__file__).resolve()),
        },
        "capability_binding": binding,
        "runtime_bindings": runtime_bindings,
        "tool_bindings": definition_body.get("tool_bindings"),
        "environment_projection": binding.get("runtime_bindings", {}).get("environment_projection"),
        "subprocess_environment": binding.get("runtime_bindings", {}).get("environment_projection"),
        "required_negative_control_ids": list(REQUIRED_NEGATIVE_CONTROL_IDS),
        "writes": {
            "active_manifest": False,
            "scheduler": False,
            "public_launcher": False,
            "existing_operations": False,
            "live_hooks": False,
            "authority_state": False,
        },
        "optional_manifold_6144_scratch": {
            "status": "NOT_CONSUMED",
            "rows": 6144,
            "portable": False,
            "claim_ceiling": "no scratch observation consumed; no manifold claim",
        },
        # This is a deterministic model-free wave.  Keep the standard wave
        # receipt fields explicit rather than letting a missing provider call
        # look like an omitted obligation.
        "child_receipts": [],
        "preload_receipts": [],
        "provider_call_receipt": None,
        "cancellation_state": "NOT_REQUESTED",
        "disagreement_state": "NOT_APPLICABLE",
        "output_digest": None,
    }


def _finish(receipt: dict[str, Any]) -> dict[str, Any]:
    unsigned = dict(receipt)
    unsigned.pop("receipt_sha256", None)
    unsigned.pop("result_sha256", None)
    value = digest(unsigned)
    receipt["receipt_sha256"] = value
    receipt["result_sha256"] = value
    return receipt


def verify_receipt(receipt: dict[str, Any]) -> bool:
    if not isinstance(receipt, dict):
        return False
    if receipt.get("schema") != SCHEMA:
        return False
    if receipt.get("promotion_allowed") is not False or receipt.get("activated") is not False:
        return False
    expected = receipt.get("receipt_sha256")
    if not isinstance(expected, str) or expected != receipt.get("result_sha256"):
        return False
    unsigned = dict(receipt)
    unsigned.pop("receipt_sha256", None)
    unsigned.pop("result_sha256", None)
    return digest(unsigned) == expected


def run_candidate(root: Path, jax_interpreter: Path | None) -> dict[str, Any]:
    root = root.expanduser().resolve()
    if not (root / "constraint_box").is_dir():
        return _finish(
            {
                "schema": SCHEMA,
                "wave_id": WAVE_ID,
                "status": "REFUSE",
                "reason": "REFUSE_REPOSITORY_ROOT",
                "candidate_state": "NEW_CANDIDATE",
                "activated": False,
                "promotion_allowed": False,
                "claim_ceiling": CLAIM_CEILING,
            }
        )
    binding = bind_capabilities(root, jax_interpreter)
    receipt = _base_receipt(root, binding)
    structured_fixture = _candidate_fixture("structured_open_bind_v1.json")
    path_fixture = _candidate_fixture("proposal_reference_policy_v1.json")
    with tempfile.TemporaryDirectory(prefix="cb-capability-probe-map-") as temp_dir:
        temporary_root = Path(temp_dir)
        bound = {row.get("capability") for row in binding.get("bound", []) if row.get("status") == "BOUND"}
        exact = (
            _run_structured(root, structured_fixture, engine="exact", interpreter=Path(sys.executable), temporary_root=temporary_root, label="exact")
            if "structured_probe_exact" in bound
            else {"operation": "structured_open_bind_probe.v1", "engine": "exact", "status": "HOLD", "reason": "STRUCTURED_EXACT_NOT_BOUND"}
        )
        dual = (
            _run_structured(root, structured_fixture, engine="dual", interpreter=jax_interpreter, temporary_root=temporary_root, label="dual")
            if "structured_probe_dual" in bound and jax_interpreter is not None
            else {"operation": "structured_open_bind_probe.v1", "engine": "dual", "status": "HOLD", "reason": "JAX_INTERPRETER_NOT_BOUND"}
        )
        path_mass = (
            _run_path_mass(root, path_fixture, jax_interpreter, temporary_root)
            if "path_mass" in bound and jax_interpreter is not None
            else {"operation": "constraint_path_mass.v1", "status": "HOLD", "reason": "PATH_MASS_EXTERNAL_JAX_NOT_BOUND"}
        )
        structured_controls = _structured_negative_controls(root, structured_fixture, temporary_root)
        path_controls = _path_negative_controls(path_mass)
        controls = validate_negative_control_matrix(structured_controls + path_controls)
        source_fixture_binding = check_source_fixture_bindings(
            binding,
            exact,
            dual,
            path_mass,
            structured_fixture,
            path_fixture,
        )
        structured_same = structured_results_agree(exact, dual)
        receipt["children"] = [
            {"id": "structured_exact", **exact},
            {"id": "structured_dual_external_jax", **dual},
            {"id": "path_mass_and_replay", **path_mass},
        ]
        receipt["child_receipts"] = [
            {
                "id": child["id"],
                "status": child.get("status"),
                "receipt_sha256": digest(child),
            }
            for child in receipt["children"]
        ]
        receipt["tool_api_evidence"] = {
            "runtime_bindings": binding.get("runtime_bindings"),
            "subprocess_environment": binding.get("runtime_bindings", {}).get("environment_projection"),
            "structured_exact": {
                "api": "evaluate(raw, engine='exact')",
                "source_sha256": exact.get("source_sha256"),
                "fixture_sha256": exact.get("fixture_sha256"),
                "invocation": exact.get("invocation"),
            },
            "structured_dual": {
                "api": "evaluate(raw, engine='dual')",
                "source_sha256": dual.get("source_sha256"),
                "fixture_sha256": dual.get("fixture_sha256"),
                "invocation": dual.get("invocation"),
                "jax": (dual.get("result") or {}).get("jax"),
            },
            "path_mass": {
                "api": "ConstraintPathMassRequest + run_constraint_path_mass + write_receipt",
                "source_sha256": path_mass.get("source_sha256"),
                "fixture_sha256": path_mass.get("fixture_sha256"),
                "wrapper_sha256": path_mass.get("wrapper_sha256"),
                "receipt_sha256": path_mass.get("receipt_sha256"),
                "invocation": path_mass.get("invocation"),
                "jax_crossing": (path_mass.get("receipt") or {}).get("jax_crossing"),
            },
            "path_mass_replay": {
                "api": "replay_receipt(path, jax_interpreter=..., fixture_path=...)",
                "status": (path_mass.get("replay") or {}).get("status"),
                "stored_receipt_sha256": (path_mass.get("replay") or {}).get("stored_receipt_sha256"),
                "replayed_receipt_sha256": (path_mass.get("replay") or {}).get("replayed_receipt_sha256"),
                "wrapper_sha256": path_mass.get("replay_wrapper_sha256"),
                "invocation": path_mass.get("replay_invocation"),
            },
        }
        receipt["capability_map"] = {
            "schema": "constraintbox.capability-map.v1",
            "entries": [
                {
                    "capability": "structured_probe_exact",
                    "operation": "structured_open_bind_probe.v1",
                    "status": exact.get("status"),
                    "api": "evaluate(raw, engine='exact')",
                },
                {
                    "capability": "structured_probe_dual",
                    "operation": "structured_open_bind_probe.v1",
                    "status": dual.get("status"),
                    "api": "evaluate(raw, engine='dual')",
                    "runtime": "declared_external_jax_python",
                },
                {
                    "capability": "path_mass",
                    "operation": "constraint_path_mass.v1",
                    "status": path_mass.get("status"),
                    "api": "run_constraint_path_mass + write_receipt",
                },
                {
                    "capability": "path_mass_replay",
                    "operation": "constraint_path_mass.replay.v1",
                    "status": (path_mass.get("replay") or {}).get("status"),
                    "api": "replay_receipt",
                },
            ],
            "promotion_allowed": False,
        }
        receipt["structured_crosscheck"] = {
            "exact_dual_structured_metrics_agree": structured_same,
            "source_fixture_binding": source_fixture_binding,
            "exact_finding": (exact.get("result") or {}).get("finding"),
            "dual_finding": (dual.get("result") or {}).get("finding"),
            "promotion_allowed": False,
        }
        receipt["source_fixture_binding"] = source_fixture_binding
        receipt["negative_controls"] = {
            **controls,
        }
        receipt["negative_control_matrix_exact"] = {
            "status": controls.get("status"),
            "required_ids": controls.get("required_ids"),
            "observed_ids": controls.get("observed_ids"),
            "missing_ids": controls.get("missing_ids"),
            "duplicate_ids": controls.get("duplicate_ids"),
            "unexpected_ids": controls.get("unexpected_ids"),
            "promotion_allowed": False,
        }
        receipt["output_digest"] = digest(
            {
                "children": receipt["children"],
                "tool_api_evidence": receipt["tool_api_evidence"],
                "capability_map": receipt["capability_map"],
                "negative_controls": receipt["negative_controls"],
                "source_fixture_binding": source_fixture_binding,
                "negative_control_matrix_exact": receipt["negative_control_matrix_exact"],
            }
        )
    positive_pass = all(
        child.get("status") == "PASS"
        for child in receipt.get("children", [])
    )
    controls_pass = bool(receipt["negative_controls"].get("all_pass"))
    crosscheck_pass = bool(receipt["structured_crosscheck"].get("exact_dual_structured_metrics_agree"))
    source_fixture_pass = bool(
        receipt["structured_crosscheck"].get("source_fixture_binding", {}).get("all_pass")
    )
    replay = receipt["children"][2].get("replay") or {}
    replay_pass = replay_result_passes(receipt["children"][2])
    if binding.get("status") == "REFUSE":
        status = "REFUSE"
        reason = "REFUSE_PUBLIC_OPERATION_BINDING"
    elif receipt["negative_controls"].get("status") == "REFUSE":
        status = "REFUSE"
        reason = "REFUSE_NEGATIVE_CONTROL_MATRIX"
    elif positive_pass and controls_pass and crosscheck_pass and source_fixture_pass and replay_pass:
        status = "PASS"
        reason = "BOUNDED_PUBLIC_OPERATIONS_AND_EXACT_REPLAY_PASSED"
    else:
        status = "HOLD"
        reason = "HOLD_REQUIRED_CHILD_OR_CONTROL_EVIDENCE"
    receipt.update(
        {
            "status": status,
            "reason": reason,
            "positive_children_pass": positive_pass,
            "negative_controls_pass": controls_pass,
            "structured_crosscheck_pass": crosscheck_pass,
            "source_fixture_binding_pass": source_fixture_pass,
            "path_mass_replay_pass": replay_pass,
            "disagreement_state": "NONE_OBSERVED" if crosscheck_pass else "STRUCTURED_EXACT_DUAL_DISAGREEMENT",
        }
    )
    return _finish(receipt)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="inactive CB capability/probe-map candidate")
    parser.add_argument("--root", type=Path, default=_DEFAULT_ROOT)
    parser.add_argument(
        "--jax-python",
        type=Path,
        default=Path(os.environ["CB_JAX_PYTHON"]) if os.environ.get("CB_JAX_PYTHON") else None,
        help="absolute declared external interpreter with JAX",
    )
    parser.add_argument("--out", type=Path, default=_CANDIDATE_DIR / "probe-map.receipt.json")
    args = parser.parse_args(argv)
    try:
        receipt = run_candidate(args.root, args.jax_python)
    except (OSError, UnicodeError, ValueError, json.JSONDecodeError) as exc:
        receipt = _finish(
            {
                "schema": SCHEMA,
                "wave_id": WAVE_ID,
                "status": "REFUSE",
                "reason": "REFUSE_CANDIDATE_RUNNER",
                "detail": f"{type(exc).__name__}:{exc}",
                "candidate_state": "NEW_CANDIDATE",
                "activated": False,
                "promotion_allowed": False,
                "claim_ceiling": CLAIM_CEILING,
            }
        )
    write_json(args.out, receipt)
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0 if receipt.get("status") == "PASS" else (3 if receipt.get("status") == "REFUSE" else 2)


if __name__ == "__main__":
    raise SystemExit(main())
