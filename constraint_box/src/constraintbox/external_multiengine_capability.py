"""One fixed external diagnostic profile with a real Python DLPack lane and
an independent strict-Julia DifferentialEquations lane.

This is deliberately not a generic engine runner.  The controller fixes the
only challenge shape, executables, worker sources, numerical checks, two-node
Mini-Lev flow, and terminal mapping.  A request cannot choose an engine,
function, worker, tolerance, or transition.  The result is external to the
ConstraintBox kernel and cannot release or promote anything.
"""

from __future__ import annotations

import argparse
import hashlib
import math
import os
import re
import secrets
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .intake import IntakeError, canonical_json, parse_json_object
from .mini_levos import (
    CONTROLLER_METADATA_KEY,
    CONTROLLER_METADATA_SCHEMA,
    FlowNode,
    FlowPolicy,
    FlowTransition,
    HookKind,
    HookRegistration,
    HookResult,
    HookSignal,
    MiniLevError,
    MiniLevRuntime,
    handler_code_sha256,
    verify_flow_receipt,
)


CAPABILITY_ID = "multiengine-dlpack-diffeq-v1"
CAPABILITY_SCHEMA = "constraintbox.multiengine-capability-receipt.v1"
BINDING_SCHEMA = "constraintbox.multiengine-binding.v1"
FLOW_RESULT_SCHEMA = "constraintbox.external-capability-flow-result.v1"
WORKER_INPUT_SCHEMA = "constraintbox.multiengine-worker-input.v1"
TOOL_STEP_ID = "multiengine-dlpack-diffeq-tool"
FLOW_RECEIPT_NAME = "multiengine_dlpack_diffeq_flow_receipt.json"
FLOW_LEDGER_NAME = "multiengine_dlpack_diffeq_flow_events.jsonl"
CAPABILITY_RECEIPT_NAME = "multiengine_dlpack_diffeq_capability_receipt.json"
CANONICAL_PYTHON = Path(
    os.environ.get(
        "CONSTRAINTBOX_WORKER_PYTHON",
        "/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3",
    )
)
JULIA_EXECUTABLE = Path(os.environ.get("CONSTRAINTBOX_JULIA_BIN", "/opt/homebrew/bin/julia"))
_MODULE_PATH = Path(__file__).resolve()
_CONSTRAINT_BOX_ROOT = _MODULE_PATH.parents[2]
_REPOSITORY_ROOT = _MODULE_PATH.parents[3]
PYTHON_WORKER = _CONSTRAINT_BOX_ROOT / "workers" / "multiengine_dlpack_worker.py"
JULIA_WORKER = _CONSTRAINT_BOX_ROOT / "workers" / "multiengine_diffeq_worker.jl"
JULIA_PROJECT = Path(
    os.environ.get(
        "CONSTRAINTBOX_JULIA_PROJECT",
        str(_REPOSITORY_ROOT / "system_v5" / "julia_carrier"),
    )
)
CLAIM_CEILING = (
    "one fresh controller-bound external diagnostic that locally exercised "
    "torch.func.jacrev, torch.utils.dlpack.to_dlpack, jax.dlpack.from_dlpack, "
    "jax.jit, jax.vmap, and an independent strict-carrier "
    "DifferentialEquations.ODEProblem/solve/Tsit5 worker with positive, "
    "wrong, boundary, operation-severance, and replay controls; not general "
    "engine readiness, a CR/canonical sim, CR truth, scientific proof, "
    "hostile-code containment, release, or promotion. SMT remains a separate "
    "CB-core boundary and is neither run nor claimed by this profile."
)
_SHA256 = hashlib.sha256
_SAFE_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}")
_HEX = re.compile(r"[0-9a-f]{64}")
_PYTHON_APIS = [
    "torch.func.jacrev",
    "torch.utils.dlpack.to_dlpack",
    "jax.dlpack.from_dlpack",
    "jax.jit",
    "jax.vmap",
]
_JULIA_APIS = [
    "DifferentialEquations.ODEProblem",
    "DifferentialEquations.solve",
    "DifferentialEquations.Tsit5",
]
_RESULT_FIELDS = frozenset(
    {
        "schema",
        "capability_id",
        "request_id",
        "request_sha256",
        "run_id",
        "flow_policy_sha256",
        "disposition",
        "reason",
        "capability_receipt_sha256",
        "flow_receipt_sha256",
        "artifacts",
        "external_system",
        "kernel_membership",
        "release_allowed",
        "engine_readiness_claim",
        "cr_truth_claim",
        "promotion_allowed",
        "claim_ceiling",
    }
)


class MultiEngineCapabilityError(RuntimeError):
    """The fixed multi-engine profile could not produce a verified receipt."""


class _WorkerUnavailable(MultiEngineCapabilityError):
    """One controller-fixed runtime is unavailable."""


@dataclass(frozen=True)
class MultiEngineBinding:
    """All values that bind a single controller-selected profile invocation."""

    capability_id: str
    run_id: str
    flow_policy_sha256: str
    request_sha256: str
    step_id: str
    challenge_seed_hex: str

    def to_dict(self) -> dict[str, str]:
        return {
            "schema": BINDING_SCHEMA,
            "capability_id": self.capability_id,
            "run_id": self.run_id,
            "flow_policy_sha256": self.flow_policy_sha256,
            "request_sha256": self.request_sha256,
            "step_id": self.step_id,
            "challenge_seed_hex": self.challenge_seed_hex,
        }


def _sha256_file(path: Path) -> str:
    return _SHA256(path.read_bytes()).hexdigest()


def _valid_sha256(value: object) -> bool:
    return isinstance(value, str) and _HEX.fullmatch(value) is not None


def _safe_identifier(value: object, label: str) -> str:
    if not isinstance(value, str) or _SAFE_ID.fullmatch(value) is None:
        raise MultiEngineCapabilityError(f"{label} is not a safe identifier")
    return value


def _finite_number(value: object) -> bool:
    return (
        not isinstance(value, bool)
        and isinstance(value, (int, float))
        and math.isfinite(float(value))
    )


def _close(left: object, right: object, tolerance: float = 2.0e-9) -> bool:
    return (
        _finite_number(left)
        and _finite_number(right)
        and math.isclose(float(left), float(right), rel_tol=tolerance, abs_tol=tolerance)
    )


def _vector_close(left: object, right: object) -> bool:
    return (
        isinstance(left, list)
        and isinstance(right, list)
        and len(left) == len(right)
        and all(_close(a, b) for a, b in zip(left, right, strict=True))
    )


def _matrix_close(left: object, right: object) -> bool:
    return (
        isinstance(left, list)
        and isinstance(right, list)
        and len(left) == len(right)
        and all(_vector_close(a, b) for a, b in zip(left, right, strict=True))
    )


def _source_digests() -> dict[str, str]:
    try:
        return {
            "profile": _sha256_file(_MODULE_PATH),
            "python_worker": _sha256_file(PYTHON_WORKER),
            "julia_worker": _sha256_file(JULIA_WORKER),
        }
    except OSError as exc:
        raise MultiEngineCapabilityError(
            f"controller-owned source is unavailable: {exc}"
        ) from exc


def validate_multiengine_binding(binding: MultiEngineBinding) -> dict[str, str]:
    """Validate exactly one frozen controller-owned binding."""

    if type(binding) is not MultiEngineBinding:
        raise MultiEngineCapabilityError("binding has an unexpected type")
    if binding.capability_id != CAPABILITY_ID:
        raise MultiEngineCapabilityError("binding capability id mismatch")
    if binding.step_id != TOOL_STEP_ID:
        raise MultiEngineCapabilityError("binding step id mismatch")
    for name, value in (
        ("capability_id", binding.capability_id),
        ("run_id", binding.run_id),
        ("step_id", binding.step_id),
    ):
        _safe_identifier(value, f"binding {name}")
    for name, value in (
        ("flow_policy_sha256", binding.flow_policy_sha256),
        ("request_sha256", binding.request_sha256),
        ("challenge_seed_hex", binding.challenge_seed_hex),
    ):
        if not _valid_sha256(value):
            raise MultiEngineCapabilityError(f"binding {name} is not a SHA-256")
    return binding.to_dict()


def multiengine_binding_from_dict(value: object) -> MultiEngineBinding:
    keys = {
        "schema",
        "capability_id",
        "run_id",
        "flow_policy_sha256",
        "request_sha256",
        "step_id",
        "challenge_seed_hex",
    }
    if not isinstance(value, dict) or set(value) != keys:
        raise MultiEngineCapabilityError("binding keys mismatch")
    if value.get("schema") != BINDING_SCHEMA:
        raise MultiEngineCapabilityError("binding schema mismatch")
    try:
        binding = MultiEngineBinding(
            capability_id=value["capability_id"],
            run_id=value["run_id"],
            flow_policy_sha256=value["flow_policy_sha256"],
            request_sha256=value["request_sha256"],
            step_id=value["step_id"],
            challenge_seed_hex=value["challenge_seed_hex"],
        )
    except (KeyError, TypeError) as exc:
        raise MultiEngineCapabilityError("binding is malformed") from exc
    validate_multiengine_binding(binding)
    return binding


def _unit(seed: bytes, index: int) -> float:
    raw = _SHA256(seed + index.to_bytes(2, "big")).digest()
    return int.from_bytes(raw[:8], "big") / float((1 << 64) - 1)


def derive_multiengine_challenge(seed_hex: str) -> dict[str, Any]:
    """Derive one fixed-shape, non-degenerate challenge from a fresh seed."""

    if not _valid_sha256(seed_hex):
        raise MultiEngineCapabilityError("challenge seed must be a SHA-256")
    seed = bytes.fromhex(seed_hex)
    alpha = round(0.45 + 0.45 * _unit(seed, 0), 12)
    beta = round(-1.35 + 0.55 * _unit(seed, 1), 12)
    gamma = round(0.35 + 0.45 * _unit(seed, 2), 12)
    x0 = round(0.55 + 1.05 * _unit(seed, 3), 12)
    x1 = round(-0.80 + 1.45 * _unit(seed, 4), 12)
    growth = round(0.20 + 0.55 * _unit(seed, 5), 12)
    initial = round(0.75 + 0.65 * _unit(seed, 6), 12)
    t_final = round(0.35 + 0.75 * _unit(seed, 7), 12)
    return {
        "python": {
            "alpha": alpha,
            "beta": beta,
            "gamma": gamma,
            "point": [x0, x1],
            "boundary_point": [0.0, 0.0],
            "wrong_jacobian": [[1.0, 0.0], [0.0, 1.0]],
            "severance_shift": 0.375,
        },
        "julia": {
            "growth": growth,
            "initial": initial,
            "t_final": t_final,
            "boundary_initial": 0.0,
            "wrong_offset": 0.125,
        },
    }


def _expected_python(case: dict[str, Any]) -> dict[str, Any]:
    alpha = float(case["alpha"])
    beta = float(case["beta"])
    gamma = float(case["gamma"])
    x0, x1 = (float(value) for value in case["point"])
    b0, b1 = (float(value) for value in case["boundary_point"])
    values = [alpha * x0 * x0 + beta * x1, x0 * x1 + gamma]
    boundary_values = [alpha * b0 * b0 + beta * b1, b0 * b1 + gamma]
    shift = float(case["severance_shift"])

    def jax_result(values_to_map: list[float]) -> list[float]:
        return [value * value + 0.5 * gamma for value in values_to_map]

    return {
        "torch_values": values,
        "jacobian": [[2.0 * alpha * x0, beta], [x1, x0]],
        "jax_values": values,
        "jax_output": jax_result(values),
        "boundary_jacobian": [[2.0 * alpha * b0, beta], [b1, b0]],
        "boundary_jax_output": jax_result(boundary_values),
        "severed_jax_output": jax_result([value + shift for value in values]),
    }


def _expected_julia(case: dict[str, Any]) -> dict[str, float]:
    growth = float(case["growth"])
    initial = float(case["initial"])
    t_final = float(case["t_final"])
    return {
        "terminal": initial * math.exp(growth * t_final),
        "boundary_terminal": 0.0,
        "wrong_terminal": initial * math.exp(growth * t_final)
        + float(case["wrong_offset"]),
        "severed_terminal": initial,
    }


def _worker_command(lane: str) -> list[str]:
    if lane == "python_dlpack_jax":
        return [str(CANONICAL_PYTHON), "-I", str(PYTHON_WORKER)]
    if lane == "julia_diffeq":
        return [
            str(JULIA_EXECUTABLE),
            "--startup-file=no",
            f"--project={JULIA_PROJECT}",
            str(JULIA_WORKER),
        ]
    raise MultiEngineCapabilityError("unknown fixed worker lane")


def _worker_environment(lane: str) -> tuple[dict[str, str], dict[str, str]]:
    environment = dict(os.environ)
    environment.pop("PYTHONPATH", None)
    environment.pop("PYTHONHOME", None)
    if lane == "python_dlpack_jax":
        declared = {
            "JAX_ENABLE_X64": "true",
            "JAX_PLATFORM_NAME": "cpu",
            "PYTHONNOUSERSITE": "1",
        }
    elif lane == "julia_diffeq":
        declared = {"JULIA_LOAD_PATH": "@:@stdlib"}
    else:
        raise MultiEngineCapabilityError("unknown fixed worker lane")
    environment.update(declared)
    return environment, declared


def _worker_input(
    lane: str, binding: dict[str, str], case: dict[str, Any]
) -> dict[str, Any]:
    return {
        "schema": WORKER_INPUT_SCHEMA,
        "lane": lane,
        "binding": binding,
        "challenge": case,
        "input_origin": "controller-derived",
    }


def _run_worker(
    lane: str, binding: dict[str, str], case: dict[str, Any]
) -> dict[str, Any]:
    """Run one fixed child and preserve its complete strict-JSON witness."""

    command = _worker_command(lane)
    source_path = PYTHON_WORKER if lane == "python_dlpack_jax" else JULIA_WORKER
    input_body = _worker_input(lane, binding, case)
    input_bytes = canonical_json(input_body)
    environment, declared = _worker_environment(lane)
    executable = Path(command[0])
    try:
        resolved_executable = executable.resolve(strict=True)
        executable_sha256 = _sha256_file(resolved_executable)
        source_sha256 = _sha256_file(source_path)
    except OSError as exc:
        raise _WorkerUnavailable(f"{lane} fixed runtime/source unavailable: {exc}") from exc
    started = time.monotonic()
    try:
        child = subprocess.Popen(
            command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=environment,
        )
    except OSError as exc:
        raise _WorkerUnavailable(f"{lane} child could not start: {exc}") from exc
    try:
        stdout, stderr = child.communicate(input_bytes, timeout=45)
    except subprocess.TimeoutExpired as exc:
        child.kill()
        stdout, stderr = child.communicate()
        raise MultiEngineCapabilityError(
            f"{lane} child exceeded the fixed 45-second bound"
        ) from exc
    elapsed = time.monotonic() - started
    if len(stdout) > 131_072 or len(stderr) > 16_384:
        raise MultiEngineCapabilityError(f"{lane} child exceeded output bound")
    if child.returncode != 0:
        raise _WorkerUnavailable(
            f"{lane} child returned {child.returncode}: {stderr.decode('utf-8', 'replace')[:1024]}"
        )
    if stderr:
        raise MultiEngineCapabilityError(f"{lane} child wrote stderr")
    try:
        stdout_text = stdout.decode("utf-8")
        witness = parse_json_object(stdout)
    except (UnicodeDecodeError, IntakeError) as exc:
        raise MultiEngineCapabilityError(f"{lane} child did not emit strict JSON") from exc
    return {
        "lane": lane,
        "command": command,
        "environment": declared,
        "input_sha256": _SHA256(input_bytes).hexdigest(),
        "worker_source_sha256": source_sha256,
        "executable_path": str(executable),
        "executable_resolved_path": str(resolved_executable),
        "executable_sha256": executable_sha256,
        "elapsed_seconds": elapsed,
        "returncode": child.returncode,
        "child_pid": child.pid,
        "stdout": stdout_text,
        "stdout_sha256": _SHA256(stdout).hexdigest(),
        "stderr": "",
        "stderr_sha256": _SHA256(stderr).hexdigest(),
        "output_sha256": _SHA256(canonical_json(witness)).hexdigest(),
        "witness": witness,
    }


def _verify_common_row(
    row: object,
    *,
    lane: str,
    binding: dict[str, str],
    case: dict[str, Any],
) -> tuple[list[str], dict[str, Any] | None]:
    errors: list[str] = []
    expected_keys = {
        "lane",
        "command",
        "environment",
        "input_sha256",
        "worker_source_sha256",
        "executable_path",
        "executable_resolved_path",
        "executable_sha256",
        "elapsed_seconds",
        "returncode",
        "child_pid",
        "stdout",
        "stdout_sha256",
        "stderr",
        "stderr_sha256",
        "output_sha256",
        "witness",
    }
    if not isinstance(row, dict) or set(row) != expected_keys:
        return ["row_keys_mismatch"], None
    expected_input = _worker_input(lane, binding, case)
    if row["lane"] != lane:
        errors.append("lane_mismatch")
    if row["command"] != _worker_command(lane):
        errors.append("command_mismatch")
    _, expected_environment = _worker_environment(lane)
    if row["environment"] != expected_environment:
        errors.append("environment_mismatch")
    if row["input_sha256"] != _SHA256(canonical_json(expected_input)).hexdigest():
        errors.append("input_sha256_mismatch")
    source_path = PYTHON_WORKER if lane == "python_dlpack_jax" else JULIA_WORKER
    try:
        expected_source = _sha256_file(source_path)
        expected_executable = Path(_worker_command(lane)[0]).resolve(strict=True)
        expected_executable_sha256 = _sha256_file(expected_executable)
    except OSError:
        return errors + ["fixed_source_or_executable_unavailable"], None
    if row["worker_source_sha256"] != expected_source:
        errors.append("worker_source_mismatch")
    if row["executable_resolved_path"] != str(expected_executable):
        errors.append("executable_path_mismatch")
    if row["executable_sha256"] != expected_executable_sha256:
        errors.append("executable_sha256_mismatch")
    if row["returncode"] != 0:
        errors.append("returncode_mismatch")
    if not _finite_number(row["elapsed_seconds"]) or float(row["elapsed_seconds"]) < 0:
        errors.append("elapsed_seconds_invalid")
    if (
        isinstance(row["child_pid"], bool)
        or not isinstance(row["child_pid"], int)
        or row["child_pid"] <= 0
        or row["child_pid"] == os.getpid()
    ):
        errors.append("child_pid_invalid")
    if row["stderr"] != "" or row["stderr_sha256"] != _SHA256(b"").hexdigest():
        errors.append("stderr_not_empty")
    if not isinstance(row["stdout"], str):
        errors.append("stdout_not_text")
        return errors, None
    raw_stdout = row["stdout"].encode("utf-8")
    if row["stdout_sha256"] != _SHA256(raw_stdout).hexdigest():
        errors.append("stdout_sha256_mismatch")
    try:
        parsed = parse_json_object(raw_stdout)
    except IntakeError:
        errors.append("stdout_not_strict_json")
        return errors, None
    if parsed != row["witness"]:
        errors.append("stdout_witness_mismatch")
    if row["output_sha256"] != _SHA256(canonical_json(parsed)).hexdigest():
        errors.append("output_sha256_mismatch")
    return errors, parsed


def _evaluate_python_row(
    row: object, binding: dict[str, str], case: dict[str, Any]
) -> tuple[list[str], dict[str, bool]]:
    errors, witness = _verify_common_row(
        row, lane="python_dlpack_jax", binding=binding, case=case
    )
    controls = {
        "positive": False,
        "wrong": False,
        "boundary": False,
        "operation_severance": False,
        "dlpack_bridge": False,
    }
    if witness is None:
        return errors, controls
    expected_keys = {
        "schema",
        "lane",
        "exact_apis",
        "binding",
        "input_origin",
        "reads_peer_output",
        "pid",
        "runtime",
        "observed",
    }
    if set(witness) != expected_keys:
        return errors + ["python_witness_keys_mismatch"], controls
    if witness["schema"] != "constraintbox.multiengine-python-witness.v1":
        errors.append("python_schema_mismatch")
    if witness["lane"] != "python_dlpack_jax":
        errors.append("python_lane_mismatch")
    if witness["exact_apis"] != _PYTHON_APIS:
        errors.append("python_exact_api_mismatch")
    if witness["binding"] != binding:
        errors.append("python_binding_mismatch")
    if witness["input_origin"] != "controller-derived" or witness["reads_peer_output"] is not False:
        errors.append("python_peer_independence_mismatch")
    if witness["pid"] != row["child_pid"]:
        errors.append("python_pid_mismatch")
    runtime = witness["runtime"]
    expected_runtime = {
        "python_executable": str(CANONICAL_PYTHON.resolve()),
        "torch_version": "2.11.0",
        "jax_version": "0.10.1",
        "jaxlib_version": "0.10.1",
        "torch_dtype": "torch.float64",
        "jax_dtype": "float64",
        "device": "cpu",
    }
    if runtime != expected_runtime:
        errors.append("python_runtime_mismatch")
    observed = witness["observed"]
    required = {
        "torch_values",
        "jacobian",
        "jax_values",
        "jax_output",
        "boundary_jacobian",
        "boundary_jax_output",
        "wrong_jacobian",
        "severed_jax_output",
    }
    if not isinstance(observed, dict) or set(observed) != required:
        return errors + ["python_observed_keys_mismatch"], controls
    expected = _expected_python(case)
    controls["positive"] = (
        _vector_close(observed["torch_values"], expected["torch_values"])
        and _matrix_close(observed["jacobian"], expected["jacobian"])
        and _vector_close(observed["jax_output"], expected["jax_output"])
    )
    controls["dlpack_bridge"] = _vector_close(
        observed["jax_values"], expected["jax_values"]
    ) and _vector_close(observed["torch_values"], observed["jax_values"])
    controls["wrong"] = _matrix_close(
        observed["wrong_jacobian"], case["wrong_jacobian"]
    ) and not _matrix_close(observed["wrong_jacobian"], expected["jacobian"])
    controls["boundary"] = _matrix_close(
        observed["boundary_jacobian"], expected["boundary_jacobian"]
    ) and _vector_close(
        observed["boundary_jax_output"], expected["boundary_jax_output"]
    )
    controls["operation_severance"] = _vector_close(
        observed["severed_jax_output"], expected["severed_jax_output"]
    ) and not _vector_close(observed["severed_jax_output"], expected["jax_output"])
    return errors, controls


def _evaluate_julia_row(
    row: object, binding: dict[str, str], case: dict[str, Any]
) -> tuple[list[str], dict[str, bool]]:
    errors, witness = _verify_common_row(
        row, lane="julia_diffeq", binding=binding, case=case
    )
    controls = {
        "positive": False,
        "wrong": False,
        "boundary": False,
        "operation_severance": False,
    }
    if witness is None:
        return errors, controls
    expected_keys = {
        "schema",
        "lane",
        "exact_apis",
        "binding",
        "input_origin",
        "reads_peer_output",
        "pid",
        "runtime",
        "observed",
    }
    if set(witness) != expected_keys:
        return errors + ["julia_witness_keys_mismatch"], controls
    if witness["schema"] != "constraintbox.multiengine-julia-witness.v1":
        errors.append("julia_schema_mismatch")
    if witness["lane"] != "julia_diffeq":
        errors.append("julia_lane_mismatch")
    if witness["exact_apis"] != _JULIA_APIS:
        errors.append("julia_exact_api_mismatch")
    if witness["binding"] != binding:
        errors.append("julia_binding_mismatch")
    if witness["input_origin"] != "controller-derived" or witness["reads_peer_output"] is not False:
        errors.append("julia_peer_independence_mismatch")
    if witness["pid"] != row["child_pid"]:
        errors.append("julia_pid_mismatch")
    expected_runtime = {
        "julia_version": "1.12.6",
        "active_project": str(JULIA_PROJECT / "Project.toml"),
        "load_path": "@:@stdlib",
        "diffeq_version": "8.0.2",
    }
    if witness["runtime"] != expected_runtime:
        errors.append("julia_runtime_mismatch")
    observed = witness["observed"]
    if not isinstance(observed, dict) or set(observed) != {
        "terminal",
        "boundary_terminal",
        "wrong_terminal",
        "severed_terminal",
    }:
        return errors + ["julia_observed_keys_mismatch"], controls
    expected = _expected_julia(case)
    controls["positive"] = _close(observed["terminal"], expected["terminal"])
    controls["boundary"] = _close(
        observed["boundary_terminal"], expected["boundary_terminal"]
    )
    controls["wrong"] = _close(
        observed["wrong_terminal"], expected["wrong_terminal"]
    ) and not _close(observed["wrong_terminal"], expected["terminal"])
    controls["operation_severance"] = _close(
        observed["severed_terminal"], expected["severed_terminal"]
    ) and not _close(observed["severed_terminal"], expected["terminal"])
    return errors, controls


def _replay_projection(row: dict[str, Any]) -> dict[str, Any]:
    witness = row["witness"]
    return {
        "lane": row["lane"],
        "input_sha256": row["input_sha256"],
        "worker_source_sha256": row["worker_source_sha256"],
        "executable_resolved_path": row["executable_resolved_path"],
        "witness": {key: value for key, value in witness.items() if key != "pid"},
    }


class MultiEngineExternalProfile:
    """Fixed controller-owned profile; never accepts a user-selected workload."""

    def run(self, binding: MultiEngineBinding) -> dict[str, Any]:
        binding_body = validate_multiengine_binding(binding)
        challenge = derive_multiengine_challenge(binding.challenge_seed_hex)
        sources_before = _source_digests()
        lanes: dict[str, Any] | None = None
        controls = {
            "positive": False,
            "wrong": False,
            "boundary": False,
            "operation_severance": False,
            "replay": False,
            "dlpack_bridge": False,
        }
        try:
            python_primary = _run_worker(
                "python_dlpack_jax", binding_body, challenge["python"]
            )
            julia_primary = _run_worker(
                "julia_diffeq", binding_body, challenge["julia"]
            )
            python_replay = _run_worker(
                "python_dlpack_jax", binding_body, challenge["python"]
            )
            julia_replay = _run_worker(
                "julia_diffeq", binding_body, challenge["julia"]
            )
            lanes = {
                "python_dlpack_jax": {
                    "primary": python_primary,
                    "replay": python_replay,
                },
                "julia_diffeq": {
                    "primary": julia_primary,
                    "replay": julia_replay,
                },
            }
            python_errors, python_controls = _evaluate_python_row(
                python_primary, binding_body, challenge["python"]
            )
            julia_errors, julia_controls = _evaluate_julia_row(
                julia_primary, binding_body, challenge["julia"]
            )
            replay_ok = (
                _replay_projection(python_primary)
                == _replay_projection(python_replay)
                and _replay_projection(julia_primary)
                == _replay_projection(julia_replay)
            )
            controls = {
                "positive": (
                    python_controls["positive"]
                    and julia_controls["positive"]
                    and not python_errors
                    and not julia_errors
                ),
                "wrong": python_controls["wrong"] and julia_controls["wrong"],
                "boundary": (
                    python_controls["boundary"] and julia_controls["boundary"]
                ),
                "operation_severance": (
                    python_controls["operation_severance"]
                    and julia_controls["operation_severance"]
                ),
                "replay": replay_ok,
                "dlpack_bridge": python_controls["dlpack_bridge"],
            }
            status = "PASS" if all(controls.values()) else "FAIL"
            reason = (
                "controller_recomputed_multiengine_controls_passed"
                if status == "PASS"
                else "controller_recomputed_check_failed"
            )
        except _WorkerUnavailable as exc:
            status = "PARKED"
            reason = f"fixed_worker_unavailable:{type(exc).__name__}"
        except MultiEngineCapabilityError as exc:
            status = "FAIL"
            reason = f"fixed_worker_execution_failed:{type(exc).__name__}"
        sources_after = _source_digests()
        if sources_before != sources_after:
            status = "FAIL"
            reason = "controller_or_worker_source_changed_during_run"
            controls = {key: False for key in controls}
        body = {
            "schema": CAPABILITY_SCHEMA,
            "capability_id": CAPABILITY_ID,
            "status": status,
            "reason": reason,
            "external_system": True,
            "kernel_membership": "EXTERNAL_NOT_CB_KERNEL",
            "binding": binding_body,
            "binding_sha256": _SHA256(canonical_json(binding_body)).hexdigest(),
            "challenge": challenge,
            "challenge_sha256": _SHA256(canonical_json(challenge)).hexdigest(),
            "source_digests_before": sources_before,
            "source_digests_after": sources_after,
            "lanes": lanes,
            "controls": controls,
            "release_allowed": False,
            "engine_readiness_claim": False,
            "cr_truth_claim": False,
            "promotion_allowed": False,
            "claim_ceiling": CLAIM_CEILING,
        }
        receipt = {
            **body,
            "receipt_sha256": _SHA256(canonical_json(body)).hexdigest(),
        }
        errors = validate_multiengine_capability_receipt(
            receipt,
            expected_binding=binding,
            expected_receipt_sha256=receipt["receipt_sha256"],
            require_pass=status == "PASS",
        )
        if errors:
            raise MultiEngineCapabilityError(
                "profile self-verification failed: " + "; ".join(errors)
            )
        return receipt


def validate_multiengine_capability_receipt(
    receipt: object,
    *,
    expected_binding: MultiEngineBinding,
    expected_receipt_sha256: str,
    require_pass: bool = True,
) -> tuple[str, ...]:
    """Recompute a persisted receipt without trusting its worker claims."""

    errors: list[str] = []
    expected_keys = {
        "schema",
        "capability_id",
        "status",
        "reason",
        "external_system",
        "kernel_membership",
        "binding",
        "binding_sha256",
        "challenge",
        "challenge_sha256",
        "source_digests_before",
        "source_digests_after",
        "lanes",
        "controls",
        "release_allowed",
        "engine_readiness_claim",
        "cr_truth_claim",
        "promotion_allowed",
        "claim_ceiling",
        "receipt_sha256",
    }
    if not isinstance(receipt, dict) or set(receipt) != expected_keys:
        return ("receipt_keys_mismatch",)
    if receipt["receipt_sha256"] != expected_receipt_sha256:
        errors.append("receipt_root_mismatch")
    body = dict(receipt)
    supplied = body.pop("receipt_sha256")
    if not _valid_sha256(supplied) or supplied != _SHA256(canonical_json(body)).hexdigest():
        errors.append("receipt_sha256_mismatch")
    fixed = {
        "schema": CAPABILITY_SCHEMA,
        "capability_id": CAPABILITY_ID,
        "external_system": True,
        "kernel_membership": "EXTERNAL_NOT_CB_KERNEL",
        "release_allowed": False,
        "engine_readiness_claim": False,
        "cr_truth_claim": False,
        "promotion_allowed": False,
        "claim_ceiling": CLAIM_CEILING,
    }
    for key, expected in fixed.items():
        if receipt[key] != expected:
            errors.append(f"{key}_mismatch")
    expected_body = validate_multiengine_binding(expected_binding)
    if receipt["binding"] != expected_body:
        errors.append("binding_mismatch")
    if receipt["binding_sha256"] != _SHA256(canonical_json(expected_body)).hexdigest():
        errors.append("binding_sha256_mismatch")
    expected_challenge = derive_multiengine_challenge(
        expected_binding.challenge_seed_hex
    )
    if receipt["challenge"] != expected_challenge:
        errors.append("challenge_mismatch")
    if receipt["challenge_sha256"] != _SHA256(canonical_json(expected_challenge)).hexdigest():
        errors.append("challenge_sha256_mismatch")
    try:
        current_sources = _source_digests()
    except MultiEngineCapabilityError:
        return tuple(errors + ["current_sources_unavailable"])
    if receipt["source_digests_before"] != current_sources:
        errors.append("source_digests_before_mismatch")
    if receipt["source_digests_after"] != current_sources:
        errors.append("source_digests_after_mismatch")
    status = receipt["status"]
    if status not in {"PASS", "FAIL", "PARKED"}:
        errors.append("status_invalid")
    if require_pass and status != "PASS":
        errors.append("pass_required")
    controls = receipt["controls"]
    expected_control_keys = {
        "positive",
        "wrong",
        "boundary",
        "operation_severance",
        "replay",
        "dlpack_bridge",
    }
    if not isinstance(controls, dict) or set(controls) != expected_control_keys:
        return tuple(errors + ["controls_keys_mismatch"])
    if any(type(value) is not bool for value in controls.values()):
        errors.append("controls_not_bool")
    lanes = receipt["lanes"]
    if status != "PASS":
        if any(controls.values()):
            errors.append("nonpass_controls_not_all_false")
        return tuple(errors)
    if not isinstance(lanes, dict) or set(lanes) != {
        "python_dlpack_jax",
        "julia_diffeq",
    }:
        return tuple(errors + ["lanes_keys_mismatch"])
    try:
        python_primary = lanes["python_dlpack_jax"]["primary"]
        python_replay = lanes["python_dlpack_jax"]["replay"]
        julia_primary = lanes["julia_diffeq"]["primary"]
        julia_replay = lanes["julia_diffeq"]["replay"]
    except (KeyError, TypeError):
        return tuple(errors + ["lane_replay_shape_mismatch"])
    python_errors, python_controls = _evaluate_python_row(
        python_primary, expected_body, expected_challenge["python"]
    )
    julia_errors, julia_controls = _evaluate_julia_row(
        julia_primary, expected_body, expected_challenge["julia"]
    )
    try:
        replay = (
            _replay_projection(python_primary) == _replay_projection(python_replay)
            and _replay_projection(julia_primary) == _replay_projection(julia_replay)
        )
    except (KeyError, TypeError):
        replay = False
        errors.append("replay_projection_invalid")
    recomputed = {
        "positive": (
            python_controls["positive"]
            and julia_controls["positive"]
            and not python_errors
            and not julia_errors
        ),
        "wrong": python_controls["wrong"] and julia_controls["wrong"],
        "boundary": python_controls["boundary"] and julia_controls["boundary"],
        "operation_severance": (
            python_controls["operation_severance"]
            and julia_controls["operation_severance"]
        ),
        "replay": replay,
        "dlpack_bridge": python_controls["dlpack_bridge"],
    }
    if controls != recomputed:
        errors.append("controller_recomputed_controls_mismatch")
    if not all(recomputed.values()):
        errors.append("controller_recomputed_controls_failed")
    if receipt["reason"] != "controller_recomputed_multiengine_controls_passed":
        errors.append("pass_reason_mismatch")
    return tuple(errors)


def _binding_from_context(
    context: dict[str, Any],
    *,
    expected_node_id: str,
    expected_hook_id: str,
    expected_hook_kind: HookKind,
) -> MultiEngineBinding:
    metadata = context.get(CONTROLLER_METADATA_KEY)
    if not isinstance(metadata, dict) or metadata != {
        "schema": CONTROLLER_METADATA_SCHEMA,
        "run_id": metadata.get("run_id"),
        "policy_sha256": metadata.get("policy_sha256"),
        "node_id": expected_node_id,
        "hook_id": expected_hook_id,
        "hook_kind": expected_hook_kind.value,
    }:
        raise MultiEngineCapabilityError("flow controller metadata mismatch")
    text = context.get("binding_json")
    if not isinstance(text, str):
        raise MultiEngineCapabilityError("flow binding is absent")
    try:
        binding = multiengine_binding_from_dict(
            parse_json_object(text.encode("utf-8"))
        )
    except (IntakeError, MultiEngineCapabilityError) as exc:
        raise MultiEngineCapabilityError("flow binding is invalid") from exc
    if (
        binding.run_id != metadata["run_id"]
        or binding.flow_policy_sha256 != metadata["policy_sha256"]
    ):
        raise MultiEngineCapabilityError("flow binding/runtime mismatch")
    return binding


def _tool(context: dict[str, Any]) -> HookResult:
    binding = _binding_from_context(
        context,
        expected_node_id="multiengine-tool",
        expected_hook_id="multiengine-dlpack-diffeq-tool",
        expected_hook_kind=HookKind.TOOL,
    )
    receipt = MultiEngineExternalProfile().run(binding)
    text = canonical_json(receipt).decode("utf-8")
    return HookResult(
        HookSignal.OBSERVED,
        {
            "capability_state": receipt["status"],
            "capability_receipt_sha256": receipt["receipt_sha256"],
        },
        {
            "capability_state": receipt["status"],
            "capability_receipt_sha256": receipt["receipt_sha256"],
            "capability_receipt_json": text,
        },
    )


def _gate(context: dict[str, Any]) -> HookResult:
    binding = _binding_from_context(
        context,
        expected_node_id="multiengine-gate",
        expected_hook_id="multiengine-dlpack-diffeq-gate",
        expected_hook_kind=HookKind.GATE,
    )
    text = context.get("capability_receipt_json")
    digest = context.get("capability_receipt_sha256")
    state = context.get("capability_state")
    if not all(isinstance(value, str) for value in (text, digest, state)):
        raise MultiEngineCapabilityError("gate context types are invalid")
    try:
        receipt = parse_json_object(text.encode("utf-8"))
    except IntakeError as exc:
        raise MultiEngineCapabilityError("gate receipt is not strict JSON") from exc
    errors = validate_multiengine_capability_receipt(
        receipt,
        expected_binding=binding,
        expected_receipt_sha256=digest,
        require_pass=state == "PASS",
    )
    if errors or receipt["status"] != state:
        raise MultiEngineCapabilityError("gate receipt verification failed")
    signal = {
        "PASS": HookSignal.PASS,
        "FAIL": HookSignal.BLOCKED,
        "PARKED": HookSignal.PARKED,
    }.get(state)
    if signal is None:
        raise MultiEngineCapabilityError("gate receipt state is invalid")
    return HookResult(
        signal,
        {"capability_state": state, "capability_receipt_sha256": digest},
    )


def _registration(
    hook_id: str,
    kind: HookKind,
    handler,
    signals: tuple[HookSignal, ...],
    updates: tuple[str, ...] = (),
) -> HookRegistration:
    return HookRegistration(
        hook_id=hook_id,
        kind=kind,
        handler=handler,
        source_path=_MODULE_PATH,
        source_sha256=_sha256_file(_MODULE_PATH),
        code_sha256=handler_code_sha256(handler),
        allowed_signals=signals,
        allowed_update_keys=updates,
        max_output_bytes=1_048_576,
    )


def _build_flow(run_id: str, ledger_path: Path) -> MiniLevRuntime:
    tool = _registration(
        "multiengine-dlpack-diffeq-tool",
        HookKind.TOOL,
        _tool,
        (HookSignal.OBSERVED,),
        (
            "capability_state",
            "capability_receipt_sha256",
            "capability_receipt_json",
        ),
    )
    gate = _registration(
        "multiengine-dlpack-diffeq-gate",
        HookKind.GATE,
        _gate,
        (HookSignal.PASS, HookSignal.BLOCKED, HookSignal.PARKED),
    )
    policy = FlowPolicy(
        flow_id="constraintbox.multiengine-dlpack-diffeq-flow.v1",
        entry_node="multiengine-tool",
        nodes=(
            FlowNode("multiengine-tool", tool.hook_id),
            FlowNode("multiengine-gate", gate.hook_id),
        ),
        transitions=(
            FlowTransition("multiengine-tool", HookSignal.OBSERVED, "multiengine-gate"),
            FlowTransition("multiengine-tool", HookSignal.HOLD, "HOLD"),
            FlowTransition("multiengine-gate", HookSignal.PASS, "ELIGIBLE"),
            FlowTransition("multiengine-gate", HookSignal.BLOCKED, "BLOCKED"),
            FlowTransition("multiengine-gate", HookSignal.PARKED, "PARKED"),
            FlowTransition("multiengine-gate", HookSignal.HOLD, "HOLD"),
        ),
        terminal_nodes=("ELIGIBLE", "BLOCKED", "PARKED", "HOLD"),
        required_nodes=("multiengine-tool", "multiengine-gate"),
        max_steps=2,
        max_visits_per_node=1,
        max_retries=0,
        max_context_bytes=1_048_576,
        max_event_bytes=1_572_864,
        max_receipt_bytes=8_388_608,
        claim_ceiling=CLAIM_CEILING,
    )
    return MiniLevRuntime(policy, (tool, gate), run_id=run_id, ledger_path=ledger_path)


def _write_new_json(path: Path, value: dict[str, Any]) -> None:
    try:
        with path.open("x", encoding="utf-8") as stream:
            stream.write(canonical_json(value).decode("utf-8"))
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
    except OSError as exc:
        raise MultiEngineCapabilityError(f"could not persist receipt: {exc}") from exc


def run_multiengine_capability_flow(
    *, request_id: str, run_root: Path
) -> dict[str, Any]:
    """Run the one fixed profile and return capability_suite-compatible fields."""

    _safe_identifier(request_id, "request_id")
    if not isinstance(run_root, Path) or not run_root.is_absolute():
        raise MultiEngineCapabilityError("run_root must be an absolute pathlib.Path")
    try:
        run_root.mkdir(parents=True, exist_ok=False)
    except OSError as exc:
        raise MultiEngineCapabilityError(f"run root must be new: {exc}") from exc
    request = {
        "schema": "constraintbox.multiengine-request.v1",
        "capability_id": CAPABILITY_ID,
        "request_id": request_id,
    }
    request_sha256 = _SHA256(canonical_json(request)).hexdigest()
    seed = secrets.token_hex(32)
    run_id = "multiengine-" + _SHA256(
        canonical_json(
            {
                "request_sha256": request_sha256,
                "challenge_seed_hex": seed,
                "run_root": str(run_root),
            }
        )
    ).hexdigest()[:32]
    runtime = _build_flow(run_id, run_root / FLOW_LEDGER_NAME)
    binding = MultiEngineBinding(
        capability_id=CAPABILITY_ID,
        run_id=run_id,
        flow_policy_sha256=runtime.policy_sha256,
        request_sha256=request_sha256,
        step_id=TOOL_STEP_ID,
        challenge_seed_hex=seed,
    )
    try:
        flow = runtime.run(
            {"binding_json": canonical_json(binding.to_dict()).decode("utf-8")}
        )
    except MiniLevError as exc:
        raise MultiEngineCapabilityError(f"two-node flow failed: {exc}") from exc
    valid, reason = verify_flow_receipt(
        flow,
        expected_run_id=runtime.run_id,
        expected_policy_sha256=runtime.policy_sha256,
        expected_ledger_path=runtime.ledger_path,
        expected_retained_head_sha256=runtime.retained_head_sha256,
        expected_receipt_sha256=runtime.receipt_sha256,
    )
    if not valid:
        raise MultiEngineCapabilityError(f"flow receipt failed verification: {reason}")
    text = flow["final_context"].get("capability_receipt_json")
    digest = flow["final_context"].get("capability_receipt_sha256")
    if not isinstance(text, str) or not isinstance(digest, str):
        raise MultiEngineCapabilityError("tool did not produce a capability receipt")
    receipt = parse_json_object(text.encode("utf-8"))
    errors = validate_multiengine_capability_receipt(
        receipt,
        expected_binding=binding,
        expected_receipt_sha256=digest,
        require_pass=flow["terminal"] == "ELIGIBLE",
    )
    if errors:
        raise MultiEngineCapabilityError(
            "persisted capability receipt failed verification: " + "; ".join(errors)
        )
    expected_terminal = {
        "PASS": "ELIGIBLE",
        "FAIL": "BLOCKED",
        "PARKED": "PARKED",
    }[receipt["status"]]
    if flow["terminal"] != expected_terminal:
        raise MultiEngineCapabilityError("receipt state differs from flow terminal")
    _write_new_json(run_root / CAPABILITY_RECEIPT_NAME, receipt)
    _write_new_json(run_root / FLOW_RECEIPT_NAME, flow)
    result = {
        "schema": FLOW_RESULT_SCHEMA,
        "capability_id": CAPABILITY_ID,
        "request_id": request_id,
        "request_sha256": request_sha256,
        "run_id": run_id,
        "flow_policy_sha256": runtime.policy_sha256,
        "disposition": flow["terminal"],
        "reason": receipt["reason"],
        "capability_receipt_sha256": digest,
        "flow_receipt_sha256": runtime.receipt_sha256,
        "artifacts": {
            "capability_receipt": str(run_root / CAPABILITY_RECEIPT_NAME),
            "flow_receipt": str(run_root / FLOW_RECEIPT_NAME),
            "flow_ledger": str(run_root / FLOW_LEDGER_NAME),
            "flow_ledger_head": str(
                run_root / f"{FLOW_LEDGER_NAME}.head"
            ),
        },
        "external_system": True,
        "kernel_membership": "EXTERNAL_NOT_CB_KERNEL",
        "release_allowed": False,
        "engine_readiness_claim": False,
        "cr_truth_claim": False,
        "promotion_allowed": False,
        "claim_ceiling": CLAIM_CEILING,
    }
    if set(result) != _RESULT_FIELDS:
        raise MultiEngineCapabilityError("result shape drifted from capability suite")
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run the fixed external DLPack + DifferentialEquations profile."
    )
    parser.add_argument("--request-id", required=True)
    parser.add_argument("--run-root", required=True)
    args = parser.parse_args(argv)
    try:
        result = run_multiengine_capability_flow(
            request_id=args.request_id,
            run_root=Path(args.run_root),
        )
    except (OSError, ValueError, MultiEngineCapabilityError) as exc:
        print(
            canonical_json(
                {
                    "schema": "constraintbox.multiengine-command-error.v1",
                    "error": str(exc),
                    "promotion_allowed": False,
                }
            ).decode("utf-8"),
            file=sys.stderr,
        )
        return 5
    print(canonical_json(result).decode("utf-8"))
    return {"ELIGIBLE": 0, "BLOCKED": 1, "PARKED": 4, "HOLD": 5}[result["disposition"]]


if __name__ == "__main__":
    raise SystemExit(main())
