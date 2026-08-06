"""A fixed, separately-process PySINDy capability for ConstraintBox.

This is deliberately an *external* workload capability.  ConstraintBox owns
the request binding, challenge, subprocess command, source/runtime pins, and
receipt checks; the child process only runs the fixed PySINDy API surface.
It is not a ConstraintBox kernel component and it carries no release,
engine-readiness, CR-truth, scientific, or promotion claim.
"""

from __future__ import annotations

import hashlib
import importlib.metadata
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


CAPABILITY_ID = "pysindy-affine-generator-v1"
CAPABILITY_SCHEMA = "constraintbox.external-pysindy-capability-receipt.v1"
BINDING_SCHEMA = "constraintbox.external-pysindy-capability-binding.v1"
ROW_SCHEMA = "constraintbox.external-pysindy-capability-row.v1"
WORKER_TRANSPORT_SCHEMA = "constraintbox.external-pysindy-worker-request.v1"
WORKER_WITNESS_SCHEMA = "constraintbox.external-pysindy-worker-witness.v1"
WORKER_FAILURE_SCHEMA = "constraintbox.external-pysindy-worker-failure.v1"
STEP_ID = "pysindy-affine-generator-tool"
EXACT_APIS = ("pysindy.SINDy.fit", "pysindy.SINDy.predict")
WORKER_ARGUMENT = "--constraintbox-internal-pysindy-worker-v1"
CONTROL_TOLERANCE = 1e-8
WORKER_TIMEOUT_SECONDS = 60.0
CAPABILITY_CLAIM_CEILING = (
    "one fresh controller-challenged PySINDy SINDy.fit and SINDy.predict "
    "operation on a bounded affine continuous generator with supplied exact "
    "x_dot plus positive, wrong-value, and boundary controls under the "
    "controller-selected compatible runtime; not PySINDy readiness, not sim-stack readiness, "
    "not CR truth, not scientific proof, hostile-code containment, not release, "
    "and not canonical promotion"
)

_SHA256 = hashlib.sha256
_SAFE_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}")
_LOWER_SHA256 = re.compile(r"[0-9a-f]{64}")
_EMPTY_SHA256 = _SHA256(b"").hexdigest()


class ExternalPySINDyCapabilityError(RuntimeError):
    """The fixed external PySINDy capability could not be verified."""


class _WorkerUnavailable(RuntimeError):
    """The fixed worker cannot honestly exercise its exact API."""


@dataclass(frozen=True)
class CapabilityBinding:
    """Controller-owned identity material for exactly one capability run."""

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


PYSINDY_VERSION_MINIMUM = (2, 1, 0)
PYSINDY_VERSION_MAXIMUM_EXCLUSIVE = (2, 2, 0)
NUMPY_VERSION_MINIMUM = (2, 3, 0)
NUMPY_VERSION_MAXIMUM_EXCLUSIVE = (2, 4, 0)
PYSINDY_RUNTIME_REQUIREMENTS = (
    (
        "pysindy",
        ("pysindy",),
        PYSINDY_VERSION_MINIMUM,
        PYSINDY_VERSION_MAXIMUM_EXCLUSIVE,
    ),
    ("numpy", ("numpy",), NUMPY_VERSION_MINIMUM, NUMPY_VERSION_MAXIMUM_EXCLUSIVE),
)
_FEATURE_LIBRARY = "PolynomialLibrary(degree=1,include_bias=True)"
_OPTIMIZER = "STLSQ(threshold=0.0,alpha=1e-12)"


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


def _runtime_witness_matches_profile(value: object) -> bool:
    """Validate worker runtime facts without pinning one wheel/venv build."""

    if not isinstance(value, dict) or set(value) != {
        "pysindy_version",
        "numpy_version",
        "python_executable_resolved_path",
        "feature_library",
        "optimizer",
    }:
        return False
    identity = inspect_external_runtime("python")
    return bool(
        identity.get("eligible")
        and _version_in_window(
            value["pysindy_version"],
            PYSINDY_VERSION_MINIMUM,
            PYSINDY_VERSION_MAXIMUM_EXCLUSIVE,
        )
        and _version_in_window(
            value["numpy_version"],
            NUMPY_VERSION_MINIMUM,
            NUMPY_VERSION_MAXIMUM_EXCLUSIVE,
        )
        and value["python_executable_resolved_path"]
        == identity.get("executable_resolved_path")
        and value["feature_library"] == _FEATURE_LIBRARY
        and value["optimizer"] == _OPTIMIZER
    )


def _finite_number(value: object, path: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ExternalPySINDyCapabilityError(f"{path} must be a finite number")
    converted = float(value)
    if not math.isfinite(converted):
        raise ExternalPySINDyCapabilityError(f"{path} must be finite")
    return converted


def _number_list(value: object, path: str, length: int) -> list[float]:
    if not isinstance(value, list) or len(value) != length:
        raise ExternalPySINDyCapabilityError(f"{path} must be a list of length {length}")
    return [
        _finite_number(item, f"{path}[{index}]")
        for index, item in enumerate(value)
    ]


def validate_capability_binding(binding: CapabilityBinding) -> dict[str, str]:
    """Reject all binding substitution before any process is launched."""

    if type(binding) is not CapabilityBinding:
        raise ExternalPySINDyCapabilityError(
            "capability binding must be one frozen CapabilityBinding"
        )
    if binding.capability_id != CAPABILITY_ID:
        raise ExternalPySINDyCapabilityError("capability binding id mismatch")
    if binding.step_id != STEP_ID:
        raise ExternalPySINDyCapabilityError("capability binding step mismatch")
    for key, value in (
        ("run_id", binding.run_id),
        ("capability_id", binding.capability_id),
        ("step_id", binding.step_id),
    ):
        if not isinstance(value, str) or _SAFE_ID.fullmatch(value) is None:
            raise ExternalPySINDyCapabilityError(
                f"capability binding {key} is invalid"
            )
    for key, value in (
        ("flow_policy_sha256", binding.flow_policy_sha256),
        ("request_sha256", binding.request_sha256),
        ("challenge_seed_hex", binding.challenge_seed_hex),
    ):
        if not _valid_sha256(value):
            raise ExternalPySINDyCapabilityError(
                f"capability binding {key} is invalid"
            )
    return binding.to_dict()


def capability_binding_from_dict(value: object) -> CapabilityBinding:
    if not isinstance(value, dict) or set(value) != {
        "schema",
        "capability_id",
        "run_id",
        "flow_policy_sha256",
        "request_sha256",
        "step_id",
        "challenge_seed_hex",
    }:
        raise ExternalPySINDyCapabilityError("capability binding keys mismatch")
    if value.get("schema") != BINDING_SCHEMA:
        raise ExternalPySINDyCapabilityError("capability binding schema mismatch")
    try:
        binding = CapabilityBinding(
            capability_id=value["capability_id"],
            run_id=value["run_id"],
            flow_policy_sha256=value["flow_policy_sha256"],
            request_sha256=value["request_sha256"],
            step_id=value["step_id"],
            challenge_seed_hex=value["challenge_seed_hex"],
        )
    except (KeyError, TypeError) as exc:
        raise ExternalPySINDyCapabilityError(
            "capability binding is malformed"
        ) from exc
    validate_capability_binding(binding)
    return binding


def _challenge_unit(seed: bytes, index: int) -> float:
    digest = _SHA256(seed + index.to_bytes(2, "big")).digest()
    return int.from_bytes(digest[:8], "big") / float((1 << 64) - 1)


def derive_pysindy_challenge_case(challenge_seed_hex: str) -> dict[str, Any]:
    """Derive the one bounded affine case from a controller-owned seed."""

    if not _valid_sha256(challenge_seed_hex):
        raise ExternalPySINDyCapabilityError(
            "challenge seed must be 32 lowercase hex bytes"
        )
    seed = bytes.fromhex(challenge_seed_hex)
    rate = round(0.60 + 0.60 * _challenge_unit(seed, 0), 12)
    magnitude = round(0.25 + 0.55 * _challenge_unit(seed, 1), 12)
    bias = -magnitude if _challenge_unit(seed, 2) < 0.5 else magnitude
    shift = round(-0.20 + 0.40 * _challenge_unit(seed, 3), 12)
    train_states = [
        round(value + shift, 12)
        for value in (-1.35, -0.85, -0.35, 0.15, 0.65, 1.15)
    ]
    heldout_states = [
        round(value - shift / 2.0, 12)
        for value in (-0.70, 0.30, 1.05)
    ]
    wrong_rate = round(rate - 0.35 if rate > 0.95 else rate + 0.35, 12)
    wrong_bias = round(bias + (0.31 if bias < 0 else -0.31), 12)
    return {
        "rate": rate,
        "bias": bias,
        "train_states": train_states,
        "heldout_states": heldout_states,
        "boundary_state": 0.0,
        "wrong_coefficients": [wrong_bias, wrong_rate],
    }


def _expected_from_case(case: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(case, dict) or set(case) != {
        "rate",
        "bias",
        "train_states",
        "heldout_states",
        "boundary_state",
        "wrong_coefficients",
    }:
        raise ExternalPySINDyCapabilityError("challenge case keys mismatch")
    rate = _finite_number(case["rate"], "$.rate")
    bias = _finite_number(case["bias"], "$.bias")
    train_states = _number_list(case["train_states"], "$.train_states", 6)
    heldout_states = _number_list(case["heldout_states"], "$.heldout_states", 3)
    boundary_state = _finite_number(case["boundary_state"], "$.boundary_state")
    wrong_coefficients = _number_list(
        case["wrong_coefficients"], "$.wrong_coefficients", 2
    )
    if len(set(train_states)) != len(train_states):
        raise ExternalPySINDyCapabilityError("training states must be distinct")
    expected_coefficients = [bias, rate]
    return {
        "coefficients": expected_coefficients,
        "heldout_derivatives": [
            rate * state + bias for state in heldout_states
        ],
        "boundary_derivative": rate * boundary_state + bias,
        "exact_train_derivatives": [
            rate * state + bias for state in train_states
        ],
        "wrong_coefficients": wrong_coefficients,
    }


def _runtime_pin_dict() -> dict[str, object]:
    """Portable runtime profile carried under the legacy receipt key."""

    return runtime_profile_dict("python")


def _inspect_pysindy_artifacts() -> dict[str, Any]:
    """Check a profile plus distribution ownership, without importing PySINDy."""

    runtime = inspect_external_runtime("python")
    artifacts = inspect_python_distributions(PYSINDY_RUNTIME_REQUIREMENTS)
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


def _flatten_numbers(value: object, path: str) -> list[float]:
    if isinstance(value, list):
        flattened: list[float] = []
        for index, item in enumerate(value):
            flattened.extend(_flatten_numbers(item, f"{path}[{index}]"))
        return flattened
    return [_finite_number(value, path)]


def _comparison(actual: object, expected: object) -> dict[str, Any]:
    try:
        actual_values = _flatten_numbers(actual, "$.actual")
        expected_values = _flatten_numbers(expected, "$.expected")
    except ExternalPySINDyCapabilityError as exc:
        return {"pass": False, "error": str(exc)}
    if len(actual_values) != len(expected_values):
        return {"pass": False, "error": "length_mismatch"}
    maximum = max(
        (abs(actual_value - expected_value) for actual_value, expected_value in zip(actual_values, expected_values)),
        default=0.0,
    )
    return {
        "pass": maximum <= CONTROL_TOLERANCE,
        "maximum_absolute_error": maximum,
        "tolerance": CONTROL_TOLERANCE,
    }


def evaluate_pysindy_affine_output(
    challenge_case: dict[str, Any], observed: dict[str, Any]
) -> dict[str, Any]:
    """Recompute the affine result and all controls in the controller."""

    expected = _expected_from_case(challenge_case)
    if not isinstance(observed, dict) or set(observed) != {
        "coefficients",
        "heldout_derivatives",
        "boundary_derivative",
    }:
        return {
            "controls": {
                "positive": False,
                "targeted_negative": False,
                "boundary": False,
            },
            "expected": expected,
            "comparisons": {},
            "errors": ["observed_keys_mismatch"],
        }
    coefficients = _comparison(observed["coefficients"], expected["coefficients"])
    heldout = _comparison(
        observed["heldout_derivatives"], expected["heldout_derivatives"]
    )
    boundary = _comparison(
        observed["boundary_derivative"], expected["boundary_derivative"]
    )
    wrong = _comparison(observed["coefficients"], expected["wrong_coefficients"])
    wrong_distinct = _comparison(
        expected["coefficients"], expected["wrong_coefficients"]
    )
    errors = [
        value["error"]
        for value in (coefficients, heldout, boundary, wrong, wrong_distinct)
        if "error" in value
    ]
    controls = {
        "positive": bool(coefficients.get("pass") and heldout.get("pass")),
        "targeted_negative": bool(
            not wrong.get("pass") and not wrong_distinct.get("pass")
        ),
        "boundary": bool(boundary.get("pass")),
    }
    return {
        "controls": controls,
        "expected": expected,
        "comparisons": {
            "coefficients": coefficients,
            "heldout": heldout,
            "boundary": boundary,
            "targeted_negative_wrong_coefficients_match": wrong,
            "targeted_negative_expected_coefficients_distinct": wrong_distinct,
        },
        "errors": errors,
    }


def _source_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _worker_command() -> list[str]:
    executable = selected_runtime_executable("python")
    if executable is None:
        raise ExternalPySINDyCapabilityError("controller python runtime unavailable")
    return [
        str(executable),
        "-B",
        "-m",
        "constraintbox.external_pysindy_capability",
        WORKER_ARGUMENT,
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


def _worker_witness(transport: dict[str, Any]) -> dict[str, Any]:
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
    if set(transport) != expected_keys:
        raise ExternalPySINDyCapabilityError("worker transport keys mismatch")
    if transport["schema"] != WORKER_TRANSPORT_SCHEMA:
        raise ExternalPySINDyCapabilityError("worker transport schema mismatch")
    if transport["capability_id"] != CAPABILITY_ID:
        raise ExternalPySINDyCapabilityError("worker transport id mismatch")
    if transport["exact_api"] != list(EXACT_APIS):
        raise ExternalPySINDyCapabilityError("worker transport API mismatch")
    binding = capability_binding_from_dict(transport["execution_binding"])
    binding_body = validate_capability_binding(binding)
    expected_case = derive_pysindy_challenge_case(binding.challenge_seed_hex)
    if transport["challenge_case"] != expected_case:
        raise ExternalPySINDyCapabilityError("worker challenge does not match binding")
    source_path = Path(__file__).resolve()
    source_sha256 = _sha256_file(source_path)
    if (
        transport["capability_source_path"] != str(source_path)
        or transport["capability_source_sha256"] != source_sha256
    ):
        raise ExternalPySINDyCapabilityError("worker source binding mismatch")
    if transport["runtime_pin"] != _runtime_pin_dict():
        raise ExternalPySINDyCapabilityError("worker runtime pin mismatch")
    pins = _inspect_pysindy_artifacts()
    if pins["status"] != "PASS":
        raise _WorkerUnavailable(pins["reason"])

    try:
        import numpy as np
        import pysindy as ps
    except (ImportError, ModuleNotFoundError) as exc:
        raise _WorkerUnavailable(f"pysindy import failed: {exc}") from exc
    try:
        pysindy_distribution = pins["artifacts"][0]
        expected_origin = Path(
            pysindy_distribution["module_origins"][0]["resolved_origin"]
        ).resolve(strict=True)
        imported_origin = Path(ps.__file__).resolve(strict=True)
    except (IndexError, KeyError, OSError, TypeError) as exc:
        raise ExternalPySINDyCapabilityError(
            "PySINDy distribution observation unavailable"
        ) from exc
    if imported_origin != expected_origin:
        raise ExternalPySINDyCapabilityError("imported PySINDy origin mismatch")
    for owner, name, qualified_name in (
        (ps, "SINDy", "pysindy.SINDy"),
        (ps.SINDy, "fit", "pysindy.SINDy.fit"),
        (ps.SINDy, "predict", "pysindy.SINDy.predict"),
        (ps, "PolynomialLibrary", "pysindy.PolynomialLibrary"),
        (ps, "STLSQ", "pysindy.STLSQ"),
    ):
        if not callable(getattr(owner, name, None)):
            raise _WorkerUnavailable(f"{qualified_name} unavailable")

    expected = _expected_from_case(expected_case)
    states = np.asarray(expected_case["train_states"], dtype=np.float64).reshape(-1, 1)
    derivatives = np.asarray(expected["exact_train_derivatives"], dtype=np.float64).reshape(-1, 1)
    library = ps.PolynomialLibrary(degree=1, include_bias=True)
    optimizer = ps.STLSQ(threshold=0.0, alpha=1e-12)
    model = ps.SINDy(feature_library=library, optimizer=optimizer)
    # This is the admitted external operation: exact derivative data is passed
    # explicitly to the genuine PySINDy API, rather than estimated from a path.
    model.fit(states, t=1.0, x_dot=derivatives)
    heldout_states = np.asarray(
        expected_case["heldout_states"], dtype=np.float64
    ).reshape(-1, 1)
    prediction = np.asarray(model.predict(heldout_states), dtype=np.float64).reshape(-1)
    boundary_state = np.asarray(
        [[expected_case["boundary_state"]]], dtype=np.float64
    )
    boundary_prediction = float(
        np.asarray(model.predict(boundary_state), dtype=np.float64).reshape(-1)[0]
    )
    coefficients = np.asarray(model.coefficients(), dtype=np.float64).reshape(1, -1)
    if coefficients.shape != (1, 2):
        raise ExternalPySINDyCapabilityError("unexpected affine coefficient shape")
    runtime = {
        "pysindy_version": importlib.metadata.version("pysindy"),
        "numpy_version": importlib.metadata.version("numpy"),
        "python_executable_resolved_path": str(Path(sys.executable).resolve()),
        "feature_library": _FEATURE_LIBRARY,
        "optimizer": _OPTIMIZER,
    }
    return {
        "schema": WORKER_WITNESS_SCHEMA,
        "capability_id": CAPABILITY_ID,
        "exact_api": list(EXACT_APIS),
        "execution_binding": binding_body,
        "capability_source_sha256": source_sha256,
        "runtime_pin": _runtime_pin_dict(),
        "observed": {
            "coefficients": [float(value) for value in coefficients[0]],
            "heldout_derivatives": [float(value) for value in prediction],
            "boundary_derivative": boundary_prediction,
        },
        "runtime": runtime,
        "pid": os.getpid(),
    }


def _worker_main() -> int:
    if sys.argv[1:] != [WORKER_ARGUMENT]:
        return 2
    try:
        transport = parse_json_object(sys.stdin.buffer.read())
        witness = _worker_witness(transport)
    except _WorkerUnavailable as exc:
        witness = {
            "schema": WORKER_FAILURE_SCHEMA,
            "capability_id": CAPABILITY_ID,
            "status": "PARKED",
            "reason": str(exc),
        }
        returncode = 3
    except Exception as exc:
        witness = {
            "schema": WORKER_FAILURE_SCHEMA,
            "capability_id": CAPABILITY_ID,
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
    """Run exactly the fixed child command and recompute its outcome."""

    transport = {
        "schema": WORKER_TRANSPORT_SCHEMA,
        "capability_id": CAPABILITY_ID,
        "exact_api": list(EXACT_APIS),
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
    returncode = None if process is None else process.returncode
    row: dict[str, Any] = {
        "schema": ROW_SCHEMA,
        "capability_id": CAPABILITY_ID,
        "external_system": True,
        "kernel_membership": "EXTERNAL_NOT_CB_KERNEL",
        "exact_api": list(EXACT_APIS),
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
        "returncode": returncode,
        "stdout_sha256": _SHA256(stdout).hexdigest(),
        "stderr_sha256": _SHA256(stderr).hexdigest(),
        "output_sha256": None,
        "worker_pid": None,
        "status": "FAIL",
        "reason": "worker_protocol_invalid",
        "controls": {
            "positive": False,
            "targeted_negative": False,
            "boundary": False,
        },
        "controller_evaluation": None,
        "observed": None,
        "runtime": None,
        "release_allowed": False,
        "engine_readiness_claim": False,
        "cr_truth_claim": False,
        "promotion_allowed": False,
        "claim_ceiling": CAPABILITY_CLAIM_CEILING,
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
        if response.get("capability_id") != CAPABILITY_ID:
            row["reason"] = "worker_failure_identity_mismatch"
            return row
        row["status"] = "PARKED" if response.get("status") == "PARKED" else "FAIL"
        row["reason"] = "exact_function_unavailable" if row["status"] == "PARKED" else "worker_reported_failure"
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
        and response["capability_id"] == CAPABILITY_ID
        and response["exact_api"] == list(EXACT_APIS)
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
    runtime = response["runtime"]
    if not _runtime_witness_matches_profile(runtime) or not isinstance(
        response["observed"], dict
    ):
        row["reason"] = "worker_runtime_or_observed_mismatch"
        return row
    evaluation = evaluate_pysindy_affine_output(challenge_case, response["observed"])
    witness_bytes = canonical_json(response)
    row.update(
        {
            "worker_source_sha256": response["capability_source_sha256"],
            "output_sha256": _SHA256(witness_bytes).hexdigest(),
            "worker_pid": pid,
            "controller_evaluation": evaluation,
            "controls": evaluation["controls"],
            "observed": response["observed"],
            "runtime": runtime,
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
    return {
        "schema": CAPABILITY_SCHEMA,
        "capability_id": CAPABILITY_ID,
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
        "pysindy_sources_before": sources_before,
        "pysindy_sources_after": sources_after,
        "row": row,
        "release_allowed": False,
        "engine_readiness_claim": False,
        "cr_truth_claim": False,
        "promotion_allowed": False,
        "claim_ceiling": CAPABILITY_CLAIM_CEILING,
    }


class PySINDyAffineCapabilityBroker:
    """Controller-owned broker for the fixed separate PySINDy process."""

    def __init__(self) -> None:
        self.source_path = Path(__file__).resolve()

    def run(self, binding: CapabilityBinding) -> dict[str, Any]:
        binding_body = validate_capability_binding(binding)
        capability_source_sha256 = _sha256_file(self.source_path)
        challenge_case = derive_pysindy_challenge_case(binding.challenge_seed_hex)
        sources_before = _inspect_pysindy_artifacts()
        row: dict[str, Any] | None = None
        status = sources_before["status"]
        reason = sources_before["reason"]
        if status == "PASS":
            row = _row_from_worker(
                binding=binding_body,
                challenge_case=challenge_case,
                capability_source_sha256=capability_source_sha256,
            )
            status = row["status"]
            reason = row["reason"]
        sources_after = _inspect_pysindy_artifacts()
        if sources_after != sources_before:
            status = "FAIL"
            reason = "pysindy_sources_changed_during_operation"
        elif sources_after["status"] != "PASS":
            status = sources_after["status"]
            reason = sources_after["reason"]
        body = _receipt_body(
            binding=binding_body,
            challenge_case=challenge_case,
            capability_source_sha256=capability_source_sha256,
            sources_before=sources_before,
            sources_after=sources_after,
            row=row,
            status=status,
            reason=reason,
        )
        receipt = {
            **body,
            "receipt_sha256": _SHA256(canonical_json(body)).hexdigest(),
        }
        errors = validate_pysindy_capability_receipt(
            receipt,
            expected_binding=binding,
            expected_receipt_sha256=receipt["receipt_sha256"],
            require_pass=status == "PASS",
        )
        if errors:
            raise ExternalPySINDyCapabilityError(
                "capability self-verification failed: " + "; ".join(errors)
            )
        return receipt


def validate_pysindy_capability_receipt(
    receipt: dict[str, Any],
    *,
    expected_binding: CapabilityBinding,
    expected_receipt_sha256: str,
    require_pass: bool = True,
) -> tuple[str, ...]:
    """Revalidate a PySINDy receipt against the current controller pins."""

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
        "pysindy_sources_before",
        "pysindy_sources_after",
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
    expect(body["capability_id"], CAPABILITY_ID, "$.capability_id")
    expect(body["external_system"], True, "$.external_system")
    expect(body["kernel_membership"], "EXTERNAL_NOT_CB_KERNEL", "$.kernel_membership")
    for key in (
        "release_allowed",
        "engine_readiness_claim",
        "cr_truth_claim",
        "promotion_allowed",
    ):
        expect(body[key], False, f"$.{key}")
    expect(body["claim_ceiling"], CAPABILITY_CLAIM_CEILING, "$.claim_ceiling")
    try:
        binding = capability_binding_from_dict(body["binding"])
        expected_binding_body = validate_capability_binding(expected_binding)
    except ExternalPySINDyCapabilityError as exc:
        error("$.binding", str(exc))
        binding = None
        expected_binding_body = None
    if binding is not None:
        expect(binding, expected_binding, "$.binding")
        expect(
            body["binding_sha256"],
            _SHA256(canonical_json(expected_binding_body)).hexdigest(),
            "$.binding_sha256",
        )
    try:
        expected_case = derive_pysindy_challenge_case(
            expected_binding.challenge_seed_hex
        )
    except ExternalPySINDyCapabilityError as exc:
        error("$.challenge_case", str(exc))
        expected_case = None
    if expected_case is not None:
        expect(body["challenge_case"], expected_case, "$.challenge_case")
        expect(
            body["challenge_case_sha256"],
            _SHA256(canonical_json(expected_case)).hexdigest(),
            "$.challenge_case_sha256",
        )
    try:
        current_source = _sha256_file(Path(__file__).resolve())
        current_pins = _inspect_pysindy_artifacts()
    except OSError as exc:
        error("$.current_sources", f"unavailable={type(exc).__name__}")
        return tuple(errors)
    expect(body["capability_source_path"], str(Path(__file__).resolve()), "$.capability_source_path")
    expect(body["capability_source_sha256"], current_source, "$.capability_source_sha256")
    expect(body["runtime_pin"], _runtime_pin_dict(), "$.runtime_pin")
    expect(body["pysindy_sources_before"], body["pysindy_sources_after"], "$.pysindy_sources_stability")
    expect(body["pysindy_sources_after"], current_pins, "$.pysindy_sources_current")

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
    expect(row["capability_id"], CAPABILITY_ID, "$.row.capability_id")
    expect(row["external_system"], True, "$.row.external_system")
    expect(row["kernel_membership"], "EXTERNAL_NOT_CB_KERNEL", "$.row.kernel_membership")
    expect(row["exact_api"], list(EXACT_APIS), "$.row.exact_api")
    expect(row["execution_binding"], expected_binding_body, "$.row.execution_binding")
    expect(
        row["challenge_case_sha256"],
        _SHA256(canonical_json(expected_case)).hexdigest(),
        "$.row.challenge_case_sha256",
    )
    expected_transport = {
        "schema": WORKER_TRANSPORT_SCHEMA,
        "capability_id": CAPABILITY_ID,
        "exact_api": list(EXACT_APIS),
        "execution_binding": expected_binding_body,
        "challenge_case": expected_case,
        "capability_source_path": str(Path(__file__).resolve()),
        "capability_source_sha256": current_source,
        "runtime_pin": _runtime_pin_dict(),
    }
    expect(
        row["input_sha256"],
        _SHA256(canonical_json(expected_transport)).hexdigest(),
        "$.row.input_sha256",
    )
    expect(row["controller_source_sha256"], current_source, "$.row.controller_source_sha256")
    expect(row["worker_source_sha256"], current_source, "$.row.worker_source_sha256")
    expect(row["worker_source_sha256_expected"], current_source, "$.row.worker_source_sha256_expected")
    expect(row["runtime_pin"], _runtime_pin_dict(), "$.row.runtime_pin")
    expect(row["command"], _worker_command(), "$.row.command")
    expect(row["cwd"], str(_source_root()), "$.row.cwd")
    for key in (
        "release_allowed",
        "engine_readiness_claim",
        "cr_truth_claim",
        "promotion_allowed",
    ):
        expect(row[key], False, f"$.row.{key}")
    expect(row["claim_ceiling"], CAPABILITY_CLAIM_CEILING, "$.row.claim_ceiling")
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
    if not _runtime_witness_matches_profile(row["runtime"]):
        error("$.row.runtime", "unsupported_or_mismatched")
    if not isinstance(row["observed"], dict):
        error("$.row.observed", "not_object")
        return tuple(errors)
    witness = {
        "schema": WORKER_WITNESS_SCHEMA,
        "capability_id": CAPABILITY_ID,
        "exact_api": list(EXACT_APIS),
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
    evaluation = evaluate_pysindy_affine_output(expected_case, row["observed"])
    expect(row["controller_evaluation"], evaluation, "$.row.controller_evaluation")
    expect(row["controls"], evaluation["controls"], "$.row.controls")
    if (
        set(row["controls"]) != {"positive", "targeted_negative", "boundary"}
        or not all(value is True for value in row["controls"].values())
        or evaluation["errors"]
    ):
        error("$.row.controls", "not_all_required_controls_true")
    return tuple(errors)


if __name__ == "__main__":
    raise SystemExit(_worker_main())
