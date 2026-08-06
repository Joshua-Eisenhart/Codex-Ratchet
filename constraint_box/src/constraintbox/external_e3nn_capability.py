"""Bounded external e3nn Wigner-3j capability probe for ConstraintBox.

The profile in this module is intentionally an external workload.  The
controller owns the challenge seed, fixed triple family, controller-selected
compatible interpreter, package-version windows, worker command, receipt
recomputation, and final status.  A worker only executes the fixed package
API.  The profile is not a ConstraintBox kernel component, an engine-readiness
claim, a release mechanism, or a promotion mechanism.
"""

from __future__ import annotations

import hashlib
import importlib.metadata
import inspect
import math
import os
import re
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .external_runtime_profiles import (
    inspect_external_runtime,
    inspect_python_distributions,
    runtime_profile_dict,
    selected_runtime_executable,
)
from .intake import IntakeError, canonical_json, parse_json_object


CAPABILITY_SCHEMA = "constraintbox.external-e3nn-capability-receipt.v1"
BINDING_SCHEMA = "constraintbox.external-e3nn-capability-binding.v1"
ROW_SCHEMA = "constraintbox.external-e3nn-capability-row.v1"
WORKER_TRANSPORT_SCHEMA = "constraintbox.external-e3nn-worker-request.v1"
WORKER_WITNESS_SCHEMA = "constraintbox.external-e3nn-worker-witness.v1"
WORKER_FAILURE_SCHEMA = "constraintbox.external-e3nn-worker-failure.v1"
WORKER_ARGUMENT = "--constraintbox-internal-e3nn-worker-v1"
WORKER_TIMEOUT_SECONDS = 120.0
CONTROL_TOLERANCE = 1e-10

_SHA256 = hashlib.sha256
_SAFE_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}")
_LOWER_SHA256 = re.compile(r"[0-9a-f]{64}")
_EMPTY_SHA256 = _SHA256(b"").hexdigest()

_DIAGONAL_110 = 1.0 / math.sqrt(3.0)
_WRONG_DIAGONAL = 1.0 / math.sqrt(2.0)


class ExternalE3nnCapabilityError(RuntimeError):
    """The fixed external e3nn capability could not be verified."""


class _WorkerUnavailable(RuntimeError):
    """The fixed worker cannot honestly exercise its admitted API."""


@dataclass(frozen=True)
class E3nnCapabilityProfile:
    """A static, controller-owned external capability definition."""

    capability_id: str
    step_id: str
    flow_id: str
    exact_apis: tuple[str, ...]
    runtime: dict[str, Any]
    claim_ceiling: str


@dataclass(frozen=True)
class E3nnCapabilityBinding:
    """Identity material that binds exactly one controller-owned run."""

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


E3NN_VERSION_MINIMUM = (0, 6, 0)
E3NN_VERSION_MAXIMUM_EXCLUSIVE = (0, 7, 0)
TORCH_VERSION_MINIMUM = (2, 11, 0)
TORCH_VERSION_MAXIMUM_EXCLUSIVE = (2, 12, 0)

E3NN_RUNTIME_REQUIREMENTS = (
    ("e3nn", ("e3nn",), E3NN_VERSION_MINIMUM, E3NN_VERSION_MAXIMUM_EXCLUSIVE),
    ("torch", ("torch",), TORCH_VERSION_MINIMUM, TORCH_VERSION_MAXIMUM_EXCLUSIVE),
)

_OPERATION = "o3.wigner_3j(1,1,0)+o3.wigner_3j(1,1,2) cpu float64"

E3NN_WIGNER_PROFILE = E3nnCapabilityProfile(
    capability_id="e3nn-wigner-crosscheck-v1",
    step_id="e3nn-wigner-crosscheck-tool",
    flow_id="constraintbox.e3nn-wigner-crosscheck-capability-flow.v1",
    exact_apis=("e3nn.o3.wigner_3j",),
    runtime={
        "operation": _OPERATION,
    },
    claim_ceiling=(
        "one fresh controller-challenged e3nn.o3.wigner_3j operation on the "
        "two controller-selected coupling triples (1,1,0) and (1,1,2) with "
        "positive, wrong-value, and selection-rule boundary controls under "
        "the controller-selected compatible runtime; not e3nn readiness, not "
        "sim-stack readiness, not CR truth, not scientific proof, not "
        "hostile-code containment, not release, and not canonical promotion"
    ),
)


def _sha256_file(path: Path) -> str:
    return _SHA256(path.read_bytes()).hexdigest()


def _valid_sha256(value: object) -> bool:
    return isinstance(value, str) and _LOWER_SHA256.fullmatch(value) is not None


def _version_in_window(
    value: object,
    minimum: tuple[int, int, int],
    maximum: tuple[int, int, int],
) -> bool:
    if not isinstance(value, str):
        return False
    match = re.fullmatch(r"(\d+)\.(\d+)\.(\d+)(?:\D.*)?", value)
    if match is None:
        return False
    version = tuple(int(match.group(index)) for index in (1, 2, 3))
    return minimum <= version < maximum


def _runtime_witness_matches_profile(
    profile: E3nnCapabilityProfile, value: object
) -> bool:
    """Check worker facts against portable policy, never a machine pin."""

    if profile is not E3NN_WIGNER_PROFILE:
        return False
    identity = inspect_external_runtime("python")
    if not identity.get("eligible") or not isinstance(value, dict):
        return False
    executable = identity.get("executable_resolved_path")
    return bool(
        set(value)
        == {
            "e3nn_version",
            "torch_version",
            "torch_default_dtype",
            "python_executable_resolved_path",
            "operation",
        }
        and _version_in_window(
            value["e3nn_version"],
            E3NN_VERSION_MINIMUM,
            E3NN_VERSION_MAXIMUM_EXCLUSIVE,
        )
        and _version_in_window(
            value["torch_version"],
            TORCH_VERSION_MINIMUM,
            TORCH_VERSION_MAXIMUM_EXCLUSIVE,
        )
        and value["torch_default_dtype"] == "torch.float64"
        and value["python_executable_resolved_path"] == executable
        and value["operation"] == profile.runtime["operation"]
    )


def _finite_number(value: object, path: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ExternalE3nnCapabilityError(f"{path} must be a finite number")
    result = float(value)
    if not math.isfinite(result):
        raise ExternalE3nnCapabilityError(f"{path} must be finite")
    return result


def _profile_for(capability_id: object) -> E3nnCapabilityProfile:
    if capability_id != E3NN_WIGNER_PROFILE.capability_id:
        raise ExternalE3nnCapabilityError("unknown external e3nn capability")
    return E3NN_WIGNER_PROFILE


def validate_e3nn_capability_binding(binding: E3nnCapabilityBinding) -> dict[str, str]:
    """Reject binding substitution before a subprocess can be launched."""

    profile = E3NN_WIGNER_PROFILE
    if type(binding) is not E3nnCapabilityBinding:
        raise ExternalE3nnCapabilityError("capability binding must be frozen")
    if binding.capability_id != profile.capability_id:
        raise ExternalE3nnCapabilityError("capability binding id mismatch")
    if binding.step_id != profile.step_id:
        raise ExternalE3nnCapabilityError("capability binding step mismatch")
    for key, value in (
        ("run_id", binding.run_id),
        ("capability_id", binding.capability_id),
        ("step_id", binding.step_id),
    ):
        if not isinstance(value, str) or _SAFE_ID.fullmatch(value) is None:
            raise ExternalE3nnCapabilityError(f"capability binding {key} is invalid")
    for key, value in (
        ("flow_policy_sha256", binding.flow_policy_sha256),
        ("request_sha256", binding.request_sha256),
        ("challenge_seed_hex", binding.challenge_seed_hex),
    ):
        if not _valid_sha256(value):
            raise ExternalE3nnCapabilityError(f"capability binding {key} is invalid")
    return binding.to_dict()


def e3nn_capability_binding_from_dict(value: object) -> E3nnCapabilityBinding:
    expected_keys = {
        "schema",
        "capability_id",
        "run_id",
        "flow_policy_sha256",
        "request_sha256",
        "step_id",
        "challenge_seed_hex",
    }
    if not isinstance(value, dict) or set(value) != expected_keys:
        raise ExternalE3nnCapabilityError("capability binding keys mismatch")
    if value.get("schema") != BINDING_SCHEMA:
        raise ExternalE3nnCapabilityError("capability binding schema mismatch")
    try:
        binding = E3nnCapabilityBinding(
            capability_id=value["capability_id"],
            run_id=value["run_id"],
            flow_policy_sha256=value["flow_policy_sha256"],
            request_sha256=value["request_sha256"],
            step_id=value["step_id"],
            challenge_seed_hex=value["challenge_seed_hex"],
        )
    except (KeyError, TypeError) as exc:
        raise ExternalE3nnCapabilityError("capability binding is malformed") from exc
    validate_e3nn_capability_binding(binding)
    return binding


def _challenge_unit(seed: bytes, index: int) -> float:
    digest = _SHA256(seed + index.to_bytes(2, "big")).digest()
    return int.from_bytes(digest[:8], "big") / float((1 << 64) - 1)


def derive_e3nn_challenge_case(challenge_seed_hex: str) -> dict[str, Any]:
    """Derive the seed-scaled fixed-triple workload from a controller seed."""

    if not _valid_sha256(challenge_seed_hex):
        raise ExternalE3nnCapabilityError("challenge seed must be lowercase SHA-256")
    seed = bytes.fromhex(challenge_seed_hex)
    scale = round(1.25 + 0.50 * _challenge_unit(seed, 0), 12)
    return {
        "triples": [[1, 1, 0], [1, 1, 2]],
        "boundary_triple": [1, 1, 2],
        "scale": scale,
        "wrong_diagonal": _WRONG_DIAGONAL,
    }


def _validated_challenge(case: dict[str, Any]) -> float:
    if not isinstance(case, dict) or set(case) != {
        "triples",
        "boundary_triple",
        "scale",
        "wrong_diagonal",
    }:
        raise ExternalE3nnCapabilityError("e3nn challenge keys mismatch")
    if case["triples"] != [[1, 1, 0], [1, 1, 2]] or case["boundary_triple"] != [1, 1, 2]:
        raise ExternalE3nnCapabilityError("e3nn challenge triples mismatch")
    scale = _finite_number(case["scale"], "$.scale")
    if not 1.25 <= scale <= 1.75:
        raise ExternalE3nnCapabilityError("e3nn challenge is outside fixed bounds")
    wrong = _finite_number(case["wrong_diagonal"], "$.wrong_diagonal")
    if abs(wrong - _WRONG_DIAGONAL) > 0.0 or abs(wrong - _DIAGONAL_110) < 0.05:
        raise ExternalE3nnCapabilityError("e3nn challenge is not controller-derived")
    return scale


def _tensor_values(
    value: object, path: str, shape: tuple[int, int, int]
) -> list[list[list[float]]]:
    if not isinstance(value, list) or len(value) != shape[0]:
        raise ExternalE3nnCapabilityError(f"{path} must have shape {shape}")
    output: list[list[list[float]]] = []
    for i, plane in enumerate(value):
        if not isinstance(plane, list) or len(plane) != shape[1]:
            raise ExternalE3nnCapabilityError(f"{path}[{i}] must have shape {shape[1:]}")
        rows: list[list[float]] = []
        for j, row in enumerate(plane):
            if not isinstance(row, list) or len(row) != shape[2]:
                raise ExternalE3nnCapabilityError(
                    f"{path}[{i}][{j}] must have length {shape[2]}"
                )
            rows.append(
                [
                    _finite_number(item, f"{path}[{i}][{j}][{k}]")
                    for k, item in enumerate(row)
                ]
            )
        output.append(rows)
    return output


def _frobenius(tensor: list[list[list[float]]]) -> float:
    return math.sqrt(
        sum(item * item for plane in tensor for row in plane for item in row)
    )


def _check(name: str, error: float, checks: dict[str, Any]) -> bool:
    passed = error <= CONTROL_TOLERANCE
    checks[name] = {
        "pass": passed,
        "maximum_absolute_error": error,
        "tolerance": CONTROL_TOLERANCE,
    }
    return passed


def evaluate_e3nn_output(
    challenge_case: dict[str, Any], observed: object
) -> dict[str, Any]:
    """Recompute the Wigner-3j structural controls in the controller.

    The controller never imports e3nn here: every check is a closed-form
    property of the two admitted triples — the (1,1,0) diagonal relation,
    Frobenius normalization, exchange symmetry, tracelessness, and
    cross-channel orthogonality — plus the seed-derived scale binding.
    """

    scale = _validated_challenge(challenge_case)
    expected = {
        "diagonal_110": _DIAGONAL_110,
        "frobenius_norms": [1.0, 1.0],
        "scaled_frobenius_norms": [scale, scale],
        "wrong_diagonal": _WRONG_DIAGONAL,
    }
    expected_observed_keys = {
        "wigner_110",
        "wigner_112",
        "frobenius_norms",
        "scaled_frobenius_norms",
    }
    if not isinstance(observed, dict) or set(observed) != expected_observed_keys:
        return {
            "controls": {"positive": False, "targeted_negative": False, "boundary": False},
            "expected": expected,
            "comparisons": {},
            "errors": ["observed_keys_mismatch"],
        }
    checks: dict[str, Any] = {}
    errors: list[str] = []
    try:
        w110 = _tensor_values(observed["wigner_110"], "$.wigner_110", (3, 3, 1))
        w112 = _tensor_values(observed["wigner_112"], "$.wigner_112", (3, 3, 5))
        norms = observed["frobenius_norms"]
        scaled = observed["scaled_frobenius_norms"]
        if not isinstance(norms, list) or len(norms) != 2:
            raise ExternalE3nnCapabilityError("$.frobenius_norms must have length 2")
        if not isinstance(scaled, list) or len(scaled) != 2:
            raise ExternalE3nnCapabilityError(
                "$.scaled_frobenius_norms must have length 2"
            )
        norms = [_finite_number(item, f"$.frobenius_norms[{i}]") for i, item in enumerate(norms)]
        scaled = [
            _finite_number(item, f"$.scaled_frobenius_norms[{i}]")
            for i, item in enumerate(scaled)
        ]
    except ExternalE3nnCapabilityError as exc:
        return {
            "controls": {"positive": False, "targeted_negative": False, "boundary": False},
            "expected": expected,
            "comparisons": {},
            "errors": [str(exc)],
        }

    diagonal = _check(
        "diagonal_110",
        max(abs(w110[i][i][0] - _DIAGONAL_110) for i in range(3)),
        checks,
    )
    off_diagonal = _check(
        "off_diagonal_110_zero",
        max(abs(w110[i][j][0]) for i in range(3) for j in range(3) if i != j),
        checks,
    )
    frobenius_110 = _check("frobenius_110_unit", abs(_frobenius(w110) - 1.0), checks)
    frobenius_112 = _check("frobenius_112_unit", abs(_frobenius(w112) - 1.0), checks)
    reported_norms = _check(
        "reported_frobenius_norms",
        max(abs(norms[0] - _frobenius(w110)), abs(norms[1] - _frobenius(w112))),
        checks,
    )
    seed_scale = _check(
        "seed_scaled_frobenius_norms",
        max(abs(scaled[index] - scale * norms[index]) for index in range(2)),
        checks,
    )
    exchange = _check(
        "exchange_symmetry_112",
        max(
            abs(w112[i][j][k] - w112[j][i][k])
            for i in range(3)
            for j in range(3)
            for k in range(5)
        ),
        checks,
    )
    traceless = _check(
        "traceless_112",
        max(abs(sum(w112[i][i][k] for i in range(3))) for k in range(5)),
        checks,
    )
    cross = _check(
        "cross_channel_orthogonality",
        max(
            abs(sum(w110[i][j][0] * w112[i][j][k] for i in range(3) for j in range(3)))
            for k in range(5)
        ),
        checks,
    )
    wrong_error = max(abs(w110[i][i][0] - _WRONG_DIAGONAL) for i in range(3))
    checks["targeted_negative_wrong_diagonal_match"] = {
        "pass": wrong_error <= CONTROL_TOLERANCE,
        "maximum_absolute_error": wrong_error,
        "tolerance": CONTROL_TOLERANCE,
    }
    wrong_distinct_error = abs(_DIAGONAL_110 - _WRONG_DIAGONAL)
    checks["targeted_negative_expected_diagonal_distinct"] = {
        "pass": wrong_distinct_error <= CONTROL_TOLERANCE,
        "maximum_absolute_error": wrong_distinct_error,
        "tolerance": CONTROL_TOLERANCE,
    }
    controls = {
        "positive": bool(
            diagonal
            and off_diagonal
            and frobenius_110
            and frobenius_112
            and reported_norms
            and seed_scale
        ),
        "targeted_negative": bool(
            checks["targeted_negative_wrong_diagonal_match"]["pass"] is False
            and checks["targeted_negative_expected_diagonal_distinct"]["pass"] is False
        ),
        "boundary": bool(exchange and traceless and cross),
    }
    return {
        "controls": controls,
        "expected": expected,
        "comparisons": checks,
        "errors": errors,
    }


def _runtime_pin_dict() -> dict[str, object]:
    """Retain the receipt field name while carrying a portable policy."""

    return runtime_profile_dict("python")


def _inspect_profile_artifacts() -> dict[str, Any]:
    """Inspect portable runtime and distribution ownership without hard pins."""

    runtime = inspect_external_runtime("python")
    artifacts = inspect_python_distributions(E3NN_RUNTIME_REQUIREMENTS)
    if not runtime["eligible"]:
        return {
            "status": runtime["disposition"],
            "reason": runtime["reason"],
            "runtime": runtime,
            "artifacts": artifacts["artifacts"],
        }
    return {
        "status": artifacts["status"],
        "reason": artifacts["reason"],
        "runtime": runtime,
        "artifacts": artifacts["artifacts"],
    }


def _source_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _worker_command() -> list[str]:
    executable = selected_runtime_executable("python")
    if executable is None:
        raise ExternalE3nnCapabilityError("controller python runtime unavailable")
    return [
        str(executable),
        "-B",
        "-m",
        "constraintbox.external_e3nn_capability",
        WORKER_ARGUMENT,
        E3NN_WIGNER_PROFILE.capability_id,
    ]


def _worker_environment() -> dict[str, str]:
    environment = {
        key: value
        for key, value in os.environ.items()
        if key not in {"PYTHONHOME", "PYTHONPATH", "PYTHONUSERBASE"}
    }
    environment["PYTHONPATH"] = str(_source_root())
    environment["PYTHONNOUSERSITE"] = "1"
    return environment


def _assert_import_source(module_path: object, expected: Path, label: str) -> None:
    if not isinstance(module_path, str) or Path(module_path).resolve() != expected:
        raise ExternalE3nnCapabilityError(f"imported {label} source mismatch")


def _distribution_origin(pins: dict[str, Any], index: int, label: str) -> Path:
    """Read a controller-observed package origin without a static file pin."""

    try:
        origin = pins["artifacts"][index]["module_origins"][0]["resolved_origin"]
        return Path(origin).resolve(strict=True)
    except (IndexError, KeyError, OSError, TypeError) as exc:
        raise ExternalE3nnCapabilityError(
            f"{label} distribution observation unavailable"
        ) from exc


def _e3nn_worker_operation(
    case: dict[str, Any], pins: dict[str, Any]
) -> tuple[dict[str, Any], dict[str, Any]]:
    scale = _validated_challenge(case)
    import torch
    import e3nn
    from e3nn import o3
    from e3nn.o3 import _wigner

    e3nn_origin = _distribution_origin(pins, 0, "e3nn")
    _assert_import_source(e3nn.__file__, e3nn_origin, "e3nn")
    # Bind the implementation module rather than the public export.  The
    # public export is deliberately the actual call site below so the
    # operation-poison control can replace it and prove that this worker does
    # not merely serialize a known Wigner tensor.  Inspecting that poisoned
    # export first would make the control fail before the operation.
    source = inspect.getsourcefile(_wigner.wigner_3j)
    if not isinstance(source, str) or e3nn_origin.parent not in Path(source).resolve().parents:
        raise ExternalE3nnCapabilityError("imported e3nn wigner_3j source mismatch")
    if not callable(getattr(o3, "wigner_3j", None)):
        raise _WorkerUnavailable("e3nn.o3.wigner_3j unavailable")
    torch.set_default_dtype(torch.float64)
    (l1_a, l2_a, l3_a), (l1_b, l2_b, l3_b) = case["triples"]
    wigner_110 = o3.wigner_3j(l1_a, l2_a, l3_a)
    wigner_112 = o3.wigner_3j(l1_b, l2_b, l3_b)
    if tuple(wigner_110.shape) != (3, 3, 1) or tuple(wigner_112.shape) != (3, 3, 5):
        raise ExternalE3nnCapabilityError("e3nn wigner_3j shape mismatch")
    if wigner_110.dtype != torch.float64 or wigner_112.dtype != torch.float64:
        raise ExternalE3nnCapabilityError("e3nn wigner_3j dtype mismatch")
    norms = [
        float(torch.linalg.vector_norm(wigner_110)),
        float(torch.linalg.vector_norm(wigner_112)),
    ]
    return (
        {
            "wigner_110": wigner_110.tolist(),
            "wigner_112": wigner_112.tolist(),
            "frobenius_norms": norms,
            "scaled_frobenius_norms": [scale * norms[0], scale * norms[1]],
        },
        {
            "e3nn_version": importlib.metadata.version("e3nn"),
            "torch_version": importlib.metadata.version("torch"),
            "torch_default_dtype": str(torch.get_default_dtype()),
            "python_executable_resolved_path": str(Path(sys.executable).resolve()),
            "operation": E3NN_WIGNER_PROFILE.runtime["operation"],
        },
    )


def _worker_witness(
    profile: E3nnCapabilityProfile, transport: dict[str, Any]
) -> dict[str, Any]:
    expected_keys = {
        "schema",
        "capability_id",
        "exact_api",
        "execution_binding",
        "challenge_case",
        "capability_source_path",
        "capability_source_sha256",
        "runtime_pin",
    }
    if profile is not E3NN_WIGNER_PROFILE:
        raise ExternalE3nnCapabilityError("worker profile mismatch")
    if set(transport) != expected_keys:
        raise ExternalE3nnCapabilityError("worker transport keys mismatch")
    if transport["schema"] != WORKER_TRANSPORT_SCHEMA:
        raise ExternalE3nnCapabilityError("worker transport schema mismatch")
    if transport["capability_id"] != profile.capability_id:
        raise ExternalE3nnCapabilityError("worker transport id mismatch")
    if transport["exact_api"] != list(profile.exact_apis):
        raise ExternalE3nnCapabilityError("worker transport API mismatch")
    binding = e3nn_capability_binding_from_dict(transport["execution_binding"])
    binding_body = validate_e3nn_capability_binding(binding)
    expected_case = derive_e3nn_challenge_case(binding.challenge_seed_hex)
    if transport["challenge_case"] != expected_case:
        raise ExternalE3nnCapabilityError("worker challenge does not match binding")
    source_path = Path(__file__).resolve()
    source_sha256 = _sha256_file(source_path)
    if (
        transport["capability_source_path"] != str(source_path)
        or transport["capability_source_sha256"] != source_sha256
    ):
        raise ExternalE3nnCapabilityError("worker source binding mismatch")
    if transport["runtime_pin"] != _runtime_pin_dict():
        raise ExternalE3nnCapabilityError("worker runtime pin mismatch")
    pins = _inspect_profile_artifacts()
    if pins["status"] != "PASS":
        raise _WorkerUnavailable(pins["reason"])
    observed, runtime = _e3nn_worker_operation(expected_case, pins)
    if not _runtime_witness_matches_profile(profile, runtime):
        raise ExternalE3nnCapabilityError("worker runtime identity mismatch")
    return {
        "schema": WORKER_WITNESS_SCHEMA,
        "capability_id": profile.capability_id,
        "exact_api": list(profile.exact_apis),
        "execution_binding": binding_body,
        "capability_source_sha256": source_sha256,
        "runtime_pin": _runtime_pin_dict(),
        "observed": observed,
        "runtime": runtime,
        "pid": os.getpid(),
    }


def _worker_main() -> int:
    if len(sys.argv) != 3 or sys.argv[1] != WORKER_ARGUMENT:
        return 2
    try:
        profile = _profile_for(sys.argv[2])
        transport = parse_json_object(sys.stdin.buffer.read())
        witness = _worker_witness(profile, transport)
    except _WorkerUnavailable as exc:
        witness = {
            "schema": WORKER_FAILURE_SCHEMA,
            "capability_id": sys.argv[2] if len(sys.argv) == 3 else None,
            "status": "PARKED",
            "reason": str(exc),
        }
        returncode = 3
    except Exception as exc:
        witness = {
            "schema": WORKER_FAILURE_SCHEMA,
            "capability_id": sys.argv[2] if len(sys.argv) == 3 else None,
            "status": "FAIL",
            "reason": f"{type(exc).__name__}: {exc}",
        }
        returncode = 4
    else:
        returncode = 0
    sys.stdout.buffer.write(canonical_json(witness) + b"\n")
    sys.stdout.buffer.flush()
    return returncode


def _row_from_worker(
    *,
    binding: dict[str, str],
    challenge_case: dict[str, Any],
    capability_source_sha256: str,
) -> dict[str, Any]:
    profile = E3NN_WIGNER_PROFILE
    transport = {
        "schema": WORKER_TRANSPORT_SCHEMA,
        "capability_id": profile.capability_id,
        "exact_api": list(profile.exact_apis),
        "execution_binding": binding,
        "challenge_case": challenge_case,
        "capability_source_path": str(Path(__file__).resolve()),
        "capability_source_sha256": capability_source_sha256,
        "runtime_pin": _runtime_pin_dict(),
    }
    command = _worker_command()
    started = time.monotonic()
    process: subprocess.CompletedProcess[bytes] | None = None
    launch_error: str | None = None
    try:
        process = subprocess.run(
            command,
            input=canonical_json(transport),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=_source_root(),
            env=_worker_environment(),
            check=False,
            timeout=WORKER_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired:
        launch_error = "worker_timeout"
    except OSError as exc:
        launch_error = f"worker_launch_unavailable:{type(exc).__name__}"
    elapsed = time.monotonic() - started
    stdout = b"" if process is None else process.stdout
    stderr = b"" if process is None else process.stderr
    row: dict[str, Any] = {
        "schema": ROW_SCHEMA,
        "capability_id": profile.capability_id,
        "external_system": True,
        "kernel_membership": "EXTERNAL_NOT_CB_KERNEL",
        "exact_api": list(profile.exact_apis),
        "execution_binding": binding,
        "challenge_case_sha256": _SHA256(canonical_json(challenge_case)).hexdigest(),
        "input_sha256": _SHA256(canonical_json(transport)).hexdigest(),
        "controller_source_sha256": capability_source_sha256,
        "worker_source_sha256": None,
        "worker_source_sha256_expected": capability_source_sha256,
        "runtime_pin": _runtime_pin_dict(),
        "command": command,
        "cwd": str(_source_root()),
        "elapsed_seconds": elapsed,
        "returncode": None if process is None else process.returncode,
        "stdout_sha256": _SHA256(stdout).hexdigest(),
        "stderr_sha256": _SHA256(stderr).hexdigest(),
        "output_sha256": None,
        "worker_pid": None,
        "status": "FAIL",
        "reason": "worker_protocol_invalid",
        "controls": {"positive": False, "targeted_negative": False, "boundary": False},
        "controller_evaluation": None,
        "observed": None,
        "runtime": None,
        "release_allowed": False,
        "engine_readiness_claim": False,
        "cr_truth_claim": False,
        "promotion_allowed": False,
        "claim_ceiling": profile.claim_ceiling,
    }
    if launch_error is not None:
        row["status"] = "PARKED"
        row["reason"] = launch_error
        return row
    try:
        response = parse_json_object(stdout.rstrip(b"\n"))
    except IntakeError:
        row["reason"] = "worker_output_not_strict_json"
        return row
    if not isinstance(response, dict):
        row["reason"] = "worker_output_not_object"
        return row
    if response.get("schema") == WORKER_FAILURE_SCHEMA:
        if response.get("capability_id") != profile.capability_id:
            row["reason"] = "worker_failure_identity_mismatch"
            return row
        row["status"] = "PARKED" if response.get("status") == "PARKED" else "FAIL"
        row["reason"] = (
            "exact_function_unavailable"
            if row["status"] == "PARKED"
            else "worker_reported_failure"
        )
        return row
    expected_witness_keys = {
        "schema",
        "capability_id",
        "exact_api",
        "execution_binding",
        "capability_source_sha256",
        "runtime_pin",
        "observed",
        "runtime",
        "pid",
    }
    if set(response) != expected_witness_keys:
        row["reason"] = "worker_witness_keys_mismatch"
        return row
    if process is None or process.returncode != 0 or stderr:
        row["reason"] = "worker_process_not_clean"
        return row
    identity_valid = (
        response["schema"] == WORKER_WITNESS_SCHEMA
        and response["capability_id"] == profile.capability_id
        and response["exact_api"] == list(profile.exact_apis)
        and response["execution_binding"] == binding
        and response["capability_source_sha256"] == capability_source_sha256
        and response["runtime_pin"] == _runtime_pin_dict()
    )
    pid = response["pid"]
    if (
        not identity_valid
        or isinstance(pid, bool)
        or not isinstance(pid, int)
        or pid <= 0
        or pid == os.getpid()
    ):
        row["reason"] = "worker_witness_identity_mismatch"
        return row
    if not _runtime_witness_matches_profile(profile, response["runtime"]) or not isinstance(
        response["observed"], dict
    ):
        row["reason"] = "worker_runtime_or_observed_mismatch"
        return row
    evaluation = evaluate_e3nn_output(challenge_case, response["observed"])
    witness_bytes = canonical_json(response)
    row.update(
        {
            "worker_source_sha256": response["capability_source_sha256"],
            "output_sha256": _SHA256(witness_bytes).hexdigest(),
            "worker_pid": pid,
            "controller_evaluation": evaluation,
            "controls": evaluation["controls"],
            "observed": response["observed"],
            "runtime": response["runtime"],
        }
    )
    if not evaluation["errors"] and all(evaluation["controls"].values()):
        row["status"] = "PASS"
        row["reason"] = "exact_operation_controls_passed"
    else:
        row["reason"] = "controller_recomputed_check_failed"
    return row


def _receipt_body(
    *,
    binding: dict[str, str],
    challenge_case: dict[str, Any],
    capability_source_sha256: str,
    sources_before: dict[str, Any],
    sources_after: dict[str, Any],
    row: dict[str, Any] | None,
    status: str,
    reason: str,
) -> dict[str, Any]:
    profile = E3NN_WIGNER_PROFILE
    return {
        "schema": CAPABILITY_SCHEMA,
        "capability_id": profile.capability_id,
        "status": status,
        "reason": reason,
        "external_system": True,
        "kernel_membership": "EXTERNAL_NOT_CB_KERNEL",
        "binding": binding,
        "binding_sha256": _SHA256(canonical_json(binding)).hexdigest(),
        "challenge_case": challenge_case,
        "challenge_case_sha256": _SHA256(canonical_json(challenge_case)).hexdigest(),
        "capability_source_path": str(Path(__file__).resolve()),
        "capability_source_sha256": capability_source_sha256,
        "runtime_pin": _runtime_pin_dict(),
        "profile_sources_before": sources_before,
        "profile_sources_after": sources_after,
        "row": row,
        "release_allowed": False,
        "engine_readiness_claim": False,
        "cr_truth_claim": False,
        "promotion_allowed": False,
        "claim_ceiling": profile.claim_ceiling,
    }


class E3nnCapabilityBroker:
    """Fixed controller broker for the external e3nn Wigner-3j profile."""

    def __init__(self) -> None:
        self.profile = E3NN_WIGNER_PROFILE
        self.source_path = Path(__file__).resolve()

    def run(self, binding: E3nnCapabilityBinding) -> dict[str, Any]:
        binding_body = validate_e3nn_capability_binding(binding)
        source_sha256 = _sha256_file(self.source_path)
        challenge_case = derive_e3nn_challenge_case(binding.challenge_seed_hex)
        sources_before = _inspect_profile_artifacts()
        row: dict[str, Any] | None = None
        status = sources_before["status"]
        reason = sources_before["reason"]
        if status == "PASS":
            row = _row_from_worker(
                binding=binding_body,
                challenge_case=challenge_case,
                capability_source_sha256=source_sha256,
            )
            status = row["status"]
            reason = row["reason"]
        sources_after = _inspect_profile_artifacts()
        if sources_after != sources_before:
            status = "FAIL"
            reason = "profile_sources_changed_during_operation"
        elif sources_after["status"] != "PASS":
            status = sources_after["status"]
            reason = sources_after["reason"]
        body = _receipt_body(
            binding=binding_body,
            challenge_case=challenge_case,
            capability_source_sha256=source_sha256,
            sources_before=sources_before,
            sources_after=sources_after,
            row=row,
            status=status,
            reason=reason,
        )
        receipt = {**body, "receipt_sha256": _SHA256(canonical_json(body)).hexdigest()}
        errors = validate_e3nn_capability_receipt(
            receipt,
            expected_binding=binding,
            expected_receipt_sha256=receipt["receipt_sha256"],
            require_pass=status == "PASS",
        )
        if errors:
            raise ExternalE3nnCapabilityError(
                "capability self-verification failed: " + "; ".join(errors)
            )
        return receipt


def validate_e3nn_capability_receipt(
    receipt: dict[str, Any],
    *,
    expected_binding: E3nnCapabilityBinding,
    expected_receipt_sha256: str,
    require_pass: bool = True,
) -> tuple[str, ...]:
    """Revalidate an external e3nn receipt against current controller pins."""

    profile = E3NN_WIGNER_PROFILE
    errors: list[str] = []

    def error(path: str, reason: str) -> None:
        errors.append(f"{path}:{reason}")

    def expect(actual: object, expected: object, path: str) -> None:
        if actual != expected:
            error(path, "mismatch")

    try:
        body = parse_json_object(canonical_json(receipt))
    except (IntakeError, TypeError, ValueError) as exc:
        return (f"$:noncanonical={exc}",)
    expected_keys = {
        "schema",
        "capability_id",
        "status",
        "reason",
        "external_system",
        "kernel_membership",
        "binding",
        "binding_sha256",
        "challenge_case",
        "challenge_case_sha256",
        "capability_source_path",
        "capability_source_sha256",
        "runtime_pin",
        "profile_sources_before",
        "profile_sources_after",
        "row",
        "release_allowed",
        "engine_readiness_claim",
        "cr_truth_claim",
        "promotion_allowed",
        "claim_ceiling",
        "receipt_sha256",
    }
    if set(body) != expected_keys:
        return ("$:receipt_keys_mismatch",)
    try:
        expected_binding_body = validate_e3nn_capability_binding(expected_binding)
    except ExternalE3nnCapabilityError as exc:
        return (f"$.binding:{exc}",)
    supplied_digest = body["receipt_sha256"]
    if not _valid_sha256(supplied_digest):
        error("$.receipt_sha256", "invalid_sha256")
    expect(supplied_digest, expected_receipt_sha256, "$.receipt_root")
    digest_body = dict(body)
    digest_body.pop("receipt_sha256")
    expect(
        supplied_digest,
        _SHA256(canonical_json(digest_body)).hexdigest(),
        "$.receipt_sha256",
    )
    expect(body["schema"], CAPABILITY_SCHEMA, "$.schema")
    expect(body["capability_id"], profile.capability_id, "$.capability_id")
    expect(body["external_system"], True, "$.external_system")
    expect(body["kernel_membership"], "EXTERNAL_NOT_CB_KERNEL", "$.kernel_membership")
    for key in ("release_allowed", "engine_readiness_claim", "cr_truth_claim", "promotion_allowed"):
        expect(body[key], False, f"$.{key}")
    expect(body["claim_ceiling"], profile.claim_ceiling, "$.claim_ceiling")
    try:
        binding = e3nn_capability_binding_from_dict(body["binding"])
    except ExternalE3nnCapabilityError as exc:
        error("$.binding", str(exc))
        binding = None
    if binding is not None:
        expect(binding, expected_binding, "$.binding")
        expect(
            body["binding_sha256"],
            _SHA256(canonical_json(expected_binding_body)).hexdigest(),
            "$.binding_sha256",
        )
    expected_case = derive_e3nn_challenge_case(expected_binding.challenge_seed_hex)
    expect(body["challenge_case"], expected_case, "$.challenge_case")
    expect(
        body["challenge_case_sha256"],
        _SHA256(canonical_json(expected_case)).hexdigest(),
        "$.challenge_case_sha256",
    )
    try:
        current_source = _sha256_file(Path(__file__).resolve())
        current_pins = _inspect_profile_artifacts()
    except OSError as exc:
        error("$.current_sources", f"unavailable={type(exc).__name__}")
        return tuple(errors)
    expect(body["capability_source_path"], str(Path(__file__).resolve()), "$.capability_source_path")
    expect(body["capability_source_sha256"], current_source, "$.capability_source_sha256")
    expect(body["runtime_pin"], _runtime_pin_dict(), "$.runtime_pin")
    expect(body["profile_sources_before"], body["profile_sources_after"], "$.profile_sources_stability")
    expect(body["profile_sources_after"], current_pins, "$.profile_sources_current")
    status = body["status"]
    if status not in {"PASS", "PARKED", "FAIL"}:
        error("$.status", "invalid")
    if require_pass and status != "PASS":
        error("$.status", "pass_required")
    row = body["row"]
    if status != "PASS":
        if row is not None and (
            not isinstance(row, dict)
            or row.get("status") != status
            or row.get("reason") != body["reason"]
        ):
            error("$.row", "nonpass_status_mismatch")
        return tuple(errors)
    expected_row_keys = {
        "schema",
        "capability_id",
        "external_system",
        "kernel_membership",
        "exact_api",
        "execution_binding",
        "challenge_case_sha256",
        "input_sha256",
        "controller_source_sha256",
        "worker_source_sha256",
        "worker_source_sha256_expected",
        "runtime_pin",
        "command",
        "cwd",
        "elapsed_seconds",
        "returncode",
        "stdout_sha256",
        "stderr_sha256",
        "output_sha256",
        "worker_pid",
        "status",
        "reason",
        "controls",
        "controller_evaluation",
        "observed",
        "runtime",
        "release_allowed",
        "engine_readiness_claim",
        "cr_truth_claim",
        "promotion_allowed",
        "claim_ceiling",
    }
    if not isinstance(row, dict) or set(row) != expected_row_keys:
        error("$.row", "pass_row_keys_mismatch")
        return tuple(errors)
    expect(row["schema"], ROW_SCHEMA, "$.row.schema")
    expect(row["capability_id"], profile.capability_id, "$.row.capability_id")
    expect(row["external_system"], True, "$.row.external_system")
    expect(row["kernel_membership"], "EXTERNAL_NOT_CB_KERNEL", "$.row.kernel_membership")
    expect(row["exact_api"], list(profile.exact_apis), "$.row.exact_api")
    expect(row["execution_binding"], expected_binding_body, "$.row.execution_binding")
    expect(
        row["challenge_case_sha256"],
        _SHA256(canonical_json(expected_case)).hexdigest(),
        "$.row.challenge_case_sha256",
    )
    expected_transport = {
        "schema": WORKER_TRANSPORT_SCHEMA,
        "capability_id": profile.capability_id,
        "exact_api": list(profile.exact_apis),
        "execution_binding": expected_binding_body,
        "challenge_case": expected_case,
        "capability_source_path": str(Path(__file__).resolve()),
        "capability_source_sha256": current_source,
        "runtime_pin": _runtime_pin_dict(),
    }
    expect(row["input_sha256"], _SHA256(canonical_json(expected_transport)).hexdigest(), "$.row.input_sha256")
    expect(row["controller_source_sha256"], current_source, "$.row.controller_source_sha256")
    expect(row["worker_source_sha256"], current_source, "$.row.worker_source_sha256")
    expect(row["worker_source_sha256_expected"], current_source, "$.row.worker_source_sha256_expected")
    expect(row["runtime_pin"], _runtime_pin_dict(), "$.row.runtime_pin")
    expect(row["command"], _worker_command(), "$.row.command")
    expect(row["cwd"], str(_source_root()), "$.row.cwd")
    for key in ("release_allowed", "engine_readiness_claim", "cr_truth_claim", "promotion_allowed"):
        expect(row[key], False, f"$.row.{key}")
    expect(row["claim_ceiling"], profile.claim_ceiling, "$.row.claim_ceiling")
    elapsed = row["elapsed_seconds"]
    if isinstance(elapsed, bool) or not isinstance(elapsed, (int, float)) or elapsed < 0:
        error("$.row.elapsed_seconds", "invalid")
    expect(row["returncode"], 0, "$.row.returncode")
    expect(row["status"], "PASS", "$.row.status")
    expect(row["reason"], "exact_operation_controls_passed", "$.row.reason")
    expect(body["reason"], row["reason"], "$.reason")
    for field in ("stdout_sha256", "stderr_sha256", "output_sha256"):
        if not _valid_sha256(row[field]):
            error(f"$.row.{field}", "invalid_sha256")
    pid = row["worker_pid"]
    if isinstance(pid, bool) or not isinstance(pid, int) or pid <= 0 or pid == os.getpid():
        error("$.row.worker_pid", "invalid_or_not_separate")
    if not _runtime_witness_matches_profile(profile, row["runtime"]):
        error("$.row.runtime", "portable_runtime_profile_mismatch")
    if not isinstance(row["observed"], dict):
        error("$.row.observed", "not_object")
        return tuple(errors)
    witness = {
        "schema": WORKER_WITNESS_SCHEMA,
        "capability_id": profile.capability_id,
        "exact_api": list(profile.exact_apis),
        "execution_binding": expected_binding_body,
        "capability_source_sha256": current_source,
        "runtime_pin": _runtime_pin_dict(),
        "observed": row["observed"],
        "runtime": row["runtime"],
        "pid": pid,
    }
    witness_bytes = canonical_json(witness)
    expect(row["output_sha256"], _SHA256(witness_bytes).hexdigest(), "$.row.output_sha256")
    expect(row["stdout_sha256"], _SHA256(witness_bytes + b"\n").hexdigest(), "$.row.stdout_sha256")
    expect(row["stderr_sha256"], _EMPTY_SHA256, "$.row.stderr_sha256")
    evaluation = evaluate_e3nn_output(expected_case, row["observed"])
    expect(row["controller_evaluation"], evaluation, "$.row.controller_evaluation")
    expect(row["controls"], evaluation["controls"], "$.row.controls")
    if (
        set(row["controls"]) != {"positive", "targeted_negative", "boundary"}
        or not all(value is True for value in row["controls"].values())
        or evaluation["errors"]
    ):
        error("$.row.controls", "not_all_required_controls_true")
    return tuple(errors)


CAPABILITY_ID = E3NN_WIGNER_PROFILE.capability_id
STEP_ID = E3NN_WIGNER_PROFILE.step_id
FLOW_ID = E3NN_WIGNER_PROFILE.flow_id
EXACT_APIS = E3NN_WIGNER_PROFILE.exact_apis
CAPABILITY_CLAIM_CEILING = E3NN_WIGNER_PROFILE.claim_ceiling
RUNTIME_POLICY = runtime_profile_dict("python")


if __name__ == "__main__":
    raise SystemExit(_worker_main())
