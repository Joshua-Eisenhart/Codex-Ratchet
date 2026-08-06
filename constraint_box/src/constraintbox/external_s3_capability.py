"""Bounded external PyDMD and PyMDP capability probes for ConstraintBox.

The two profiles in this module are intentionally external workloads.  The
controller owns the challenge seed, fixed input family, controller-selected
compatible interpreter, package-version windows, worker command, receipt
recomputation, and final status.  A worker only executes the fixed package
API.  Neither profile is a ConstraintBox kernel component, an engine-readiness
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
import tempfile
import time
import warnings
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


CAPABILITY_SCHEMA = "constraintbox.external-s3-capability-receipt.v1"
BINDING_SCHEMA = "constraintbox.external-s3-capability-binding.v1"
ROW_SCHEMA = "constraintbox.external-s3-capability-row.v1"
WORKER_TRANSPORT_SCHEMA = "constraintbox.external-s3-worker-request.v1"
WORKER_WITNESS_SCHEMA = "constraintbox.external-s3-worker-witness.v1"
WORKER_FAILURE_SCHEMA = "constraintbox.external-s3-worker-failure.v1"
WORKER_ARGUMENT = "--constraintbox-internal-s3-worker-v1"
WORKER_TIMEOUT_SECONDS = 90.0
CONTROL_TOLERANCE = 1e-8

_SHA256 = hashlib.sha256
_SAFE_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}")
_LOWER_SHA256 = re.compile(r"[0-9a-f]{64}")
_EMPTY_SHA256 = _SHA256(b"").hexdigest()


class ExternalS3CapabilityError(RuntimeError):
    """A fixed external S3 capability could not be verified."""


class _WorkerUnavailable(RuntimeError):
    """The fixed worker cannot honestly exercise its admitted API."""


@dataclass(frozen=True)
class S3CapabilityProfile:
    """A static, controller-owned external capability definition."""

    capability_id: str
    step_id: str
    flow_id: str
    exact_apis: tuple[str, ...]
    runtime: dict[str, Any]
    claim_ceiling: str


@dataclass(frozen=True)
class S3CapabilityBinding:
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


PYDMD_VERSION_MINIMUM = (2025, 8, 0)
PYDMD_VERSION_MAXIMUM_EXCLUSIVE = (2026, 0, 0)
NUMPY_VERSION_MINIMUM = (2, 3, 0)
NUMPY_VERSION_MAXIMUM_EXCLUSIVE = (2, 4, 0)
PYMDP_VERSION_MINIMUM = (1, 0, 0)
PYMDP_VERSION_MAXIMUM_EXCLUSIVE = (1, 1, 0)
JAX_VERSION_MINIMUM = (0, 10, 0)
JAX_VERSION_MAXIMUM_EXCLUSIVE = (0, 11, 0)

PYDMD_RUNTIME_REQUIREMENTS = (
    ("PyDMD", ("pydmd",), PYDMD_VERSION_MINIMUM, PYDMD_VERSION_MAXIMUM_EXCLUSIVE),
    ("numpy", ("numpy",), NUMPY_VERSION_MINIMUM, NUMPY_VERSION_MAXIMUM_EXCLUSIVE),
)
PYMDP_RUNTIME_REQUIREMENTS = (
    (
        "inferactively-pymdp",
        ("pymdp",),
        PYMDP_VERSION_MINIMUM,
        PYMDP_VERSION_MAXIMUM_EXCLUSIVE,
    ),
    ("jax", ("jax",), JAX_VERSION_MINIMUM, JAX_VERSION_MAXIMUM_EXCLUSIVE),
)

PYDMD_PROFILE = S3CapabilityProfile(
    capability_id="pydmd-discrete-rate-v1",
    step_id="pydmd-discrete-rate-tool",
    flow_id="constraintbox.pydmd-discrete-rate-capability-flow.v1",
    exact_apis=("pydmd.DMD.fit", "pydmd.DMD.eigs", "pydmd.DMD.reconstructed_data"),
    runtime={
        "operation": "DMD(svd_rank=1,exact=True)",
    },
    claim_ceiling=(
        "one fresh controller-challenged PyDMD DMD.fit, DMD.eigs, and "
        "DMD.reconstructed_data operation on a bounded scalar discrete-rate "
        "sequence with positive, wrong-value, and horizon-boundary controls "
        "under the controller-selected compatible runtime; not PyDMD readiness, not sim-stack "
        "readiness, not CR truth, not scientific proof, not hostile-code "
        "containment, not release, and not canonical promotion"
    ),
)

PYMDP_PROFILE = S3CapabilityProfile(
    capability_id="pymdp-two-state-inference-v1",
    step_id="pymdp-two-state-inference-tool",
    flow_id="constraintbox.pymdp-two-state-inference-capability-flow.v1",
    exact_apis=("pymdp.Agent.infer_states", "pymdp.Agent.infer_policies"),
    runtime={
        "jax_x64_enabled": True,
        "operation": "Agent.infer_states + Agent.infer_policies",
    },
    claim_ceiling=(
        "one fresh controller-challenged PyMDP Agent.infer_states and "
        "Agent.infer_policies operation on a bounded two-state, two-action "
        "categorical model with positive, wrong-value, and alternate-observation "
        "boundary controls under the controller-selected compatible runtime; not PyMDP readiness, "
        "not sim-stack readiness, not CR truth, not scientific proof, not hostile-code "
        "containment, not release, and not canonical promotion"
    ),
)

_PROFILES = {
    PYDMD_PROFILE.capability_id: PYDMD_PROFILE,
    PYMDP_PROFILE.capability_id: PYMDP_PROFILE,
}


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


def _runtime_requirements(
    profile: S3CapabilityProfile,
) -> tuple[tuple[str, tuple[str, ...], tuple[int, int, int], tuple[int, int, int]], ...]:
    if profile is PYDMD_PROFILE:
        return PYDMD_RUNTIME_REQUIREMENTS
    if profile is PYMDP_PROFILE:
        return PYMDP_RUNTIME_REQUIREMENTS
    raise ExternalS3CapabilityError("unknown external S3 profile")


def _runtime_witness_matches_profile(
    profile: S3CapabilityProfile, value: object
) -> bool:
    """Check worker facts against portable policy, never a machine pin."""

    identity = inspect_external_runtime("python")
    if not identity.get("eligible") or not isinstance(value, dict):
        return False
    executable = identity.get("executable_resolved_path")
    if profile is PYDMD_PROFILE:
        return bool(
            set(value)
            == {
                "pydmd_version",
                "numpy_version",
                "python_executable_resolved_path",
                "operation",
            }
            and _version_in_window(
                value["pydmd_version"],
                PYDMD_VERSION_MINIMUM,
                PYDMD_VERSION_MAXIMUM_EXCLUSIVE,
            )
            and _version_in_window(
                value["numpy_version"],
                NUMPY_VERSION_MINIMUM,
                NUMPY_VERSION_MAXIMUM_EXCLUSIVE,
            )
            and value["python_executable_resolved_path"] == executable
            and value["operation"] == profile.runtime["operation"]
        )
    if profile is PYMDP_PROFILE:
        return bool(
            set(value)
            == {
                "pymdp_version",
                "jax_version",
                "jax_x64_enabled",
                "python_executable_resolved_path",
                "operation",
            }
            and _version_in_window(
                value["pymdp_version"],
                PYMDP_VERSION_MINIMUM,
                PYMDP_VERSION_MAXIMUM_EXCLUSIVE,
            )
            and _version_in_window(
                value["jax_version"],
                JAX_VERSION_MINIMUM,
                JAX_VERSION_MAXIMUM_EXCLUSIVE,
            )
            and value["jax_x64_enabled"] is True
            and value["python_executable_resolved_path"] == executable
            and value["operation"] == profile.runtime["operation"]
        )
    return False


def _finite_number(value: object, path: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ExternalS3CapabilityError(f"{path} must be a finite number")
    result = float(value)
    if not math.isfinite(result):
        raise ExternalS3CapabilityError(f"{path} must be finite")
    return result


def _number_list(value: object, path: str, length: int) -> list[float]:
    if not isinstance(value, list) or len(value) != length:
        raise ExternalS3CapabilityError(f"{path} must be a list of length {length}")
    return [_finite_number(item, f"{path}[{index}]") for index, item in enumerate(value)]


def _profile_for(capability_id: object) -> S3CapabilityProfile:
    if not isinstance(capability_id, str) or capability_id not in _PROFILES:
        raise ExternalS3CapabilityError("unknown external S3 capability")
    return _PROFILES[capability_id]


def validate_s3_capability_binding(
    profile: S3CapabilityProfile, binding: S3CapabilityBinding
) -> dict[str, str]:
    """Reject binding substitution before a subprocess can be launched."""

    if type(profile) is not S3CapabilityProfile:
        raise ExternalS3CapabilityError("capability profile must be frozen")
    if type(binding) is not S3CapabilityBinding:
        raise ExternalS3CapabilityError("capability binding must be frozen")
    if binding.capability_id != profile.capability_id:
        raise ExternalS3CapabilityError("capability binding id mismatch")
    if binding.step_id != profile.step_id:
        raise ExternalS3CapabilityError("capability binding step mismatch")
    for key, value in (
        ("run_id", binding.run_id),
        ("capability_id", binding.capability_id),
        ("step_id", binding.step_id),
    ):
        if not isinstance(value, str) or _SAFE_ID.fullmatch(value) is None:
            raise ExternalS3CapabilityError(f"capability binding {key} is invalid")
    for key, value in (
        ("flow_policy_sha256", binding.flow_policy_sha256),
        ("request_sha256", binding.request_sha256),
        ("challenge_seed_hex", binding.challenge_seed_hex),
    ):
        if not _valid_sha256(value):
            raise ExternalS3CapabilityError(f"capability binding {key} is invalid")
    return binding.to_dict()


def s3_capability_binding_from_dict(
    profile: S3CapabilityProfile, value: object
) -> S3CapabilityBinding:
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
        raise ExternalS3CapabilityError("capability binding keys mismatch")
    if value.get("schema") != BINDING_SCHEMA:
        raise ExternalS3CapabilityError("capability binding schema mismatch")
    try:
        binding = S3CapabilityBinding(
            capability_id=value["capability_id"],
            run_id=value["run_id"],
            flow_policy_sha256=value["flow_policy_sha256"],
            request_sha256=value["request_sha256"],
            step_id=value["step_id"],
            challenge_seed_hex=value["challenge_seed_hex"],
        )
    except (KeyError, TypeError) as exc:
        raise ExternalS3CapabilityError("capability binding is malformed") from exc
    validate_s3_capability_binding(profile, binding)
    return binding


def _challenge_unit(seed: bytes, index: int) -> float:
    digest = _SHA256(seed + index.to_bytes(2, "big")).digest()
    return int.from_bytes(digest[:8], "big") / float((1 << 64) - 1)


def derive_pydmd_challenge_case(challenge_seed_hex: str) -> dict[str, Any]:
    """Derive a non-degenerate one-mode sequence from a controller seed."""

    if not _valid_sha256(challenge_seed_hex):
        raise ExternalS3CapabilityError("challenge seed must be lowercase SHA-256")
    seed = bytes.fromhex(challenge_seed_hex)
    multiplier = round(0.45 + 0.35 * _challenge_unit(seed, 0), 12)
    initial = round(0.80 + 0.60 * _challenge_unit(seed, 1), 12)
    values = [round(initial * multiplier**index, 12) for index in range(7)]
    wrong_multiplier = round(
        multiplier + (0.17 if multiplier <= 0.62 else -0.17), 12
    )
    return {
        "initial": initial,
        "multiplier": multiplier,
        "values": values,
        "wrong_multiplier": wrong_multiplier,
        "boundary_index": 6,
    }


def derive_pymdp_challenge_case(challenge_seed_hex: str) -> dict[str, Any]:
    """Derive the two-state categorical model from a controller seed."""

    if not _valid_sha256(challenge_seed_hex):
        raise ExternalS3CapabilityError("challenge seed must be lowercase SHA-256")
    seed = bytes.fromhex(challenge_seed_hex)
    likelihood_high = round(0.72 + 0.16 * _challenge_unit(seed, 0), 12)
    prior_state0 = round(0.42 + 0.16 * _challenge_unit(seed, 1), 12)
    preferred_observation0 = round(0.35 + 0.55 * _challenge_unit(seed, 2), 12)
    preferred_observation1 = round(-0.80 + 0.35 * _challenge_unit(seed, 3), 12)
    return {
        "likelihood_high": likelihood_high,
        "prior_state0": prior_state0,
        "preferences": [preferred_observation0, preferred_observation1],
        "primary_observation": 0,
        "boundary_observation": 1,
    }


def derive_s3_challenge_case(
    profile: S3CapabilityProfile, challenge_seed_hex: str
) -> dict[str, Any]:
    if profile is PYDMD_PROFILE:
        return derive_pydmd_challenge_case(challenge_seed_hex)
    if profile is PYMDP_PROFILE:
        return derive_pymdp_challenge_case(challenge_seed_hex)
    raise ExternalS3CapabilityError("unknown external S3 profile")


def _pydmd_expected(case: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(case, dict) or set(case) != {
        "initial",
        "multiplier",
        "values",
        "wrong_multiplier",
        "boundary_index",
    }:
        raise ExternalS3CapabilityError("PyDMD challenge keys mismatch")
    initial = _finite_number(case["initial"], "$.initial")
    multiplier = _finite_number(case["multiplier"], "$.multiplier")
    values = _number_list(case["values"], "$.values", 7)
    wrong_multiplier = _finite_number(case["wrong_multiplier"], "$.wrong_multiplier")
    boundary_index = case["boundary_index"]
    if (
        isinstance(boundary_index, bool)
        or not isinstance(boundary_index, int)
        or boundary_index != 6
    ):
        raise ExternalS3CapabilityError("PyDMD boundary index mismatch")
    if not 0.40 < multiplier < 0.85 or not 0.70 < initial < 1.50:
        raise ExternalS3CapabilityError("PyDMD challenge is outside fixed bounds")
    recomputed = [round(initial * multiplier**index, 12) for index in range(7)]
    if values != recomputed or abs(wrong_multiplier - multiplier) < 0.05:
        raise ExternalS3CapabilityError("PyDMD challenge is not controller-derived")
    return {
        "eigenvalue_real": multiplier,
        "eigenvalue_imaginary": 0.0,
        "reconstructed_values": values,
        "boundary_terminal": values[boundary_index],
        "wrong_multiplier": wrong_multiplier,
    }


def _softmax(values: list[float]) -> list[float]:
    maximum = max(values)
    scaled = [math.exp(value - maximum) for value in values]
    total = sum(scaled)
    return [value / total for value in scaled]


def _pymdp_expected(case: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(case, dict) or set(case) != {
        "likelihood_high",
        "prior_state0",
        "preferences",
        "primary_observation",
        "boundary_observation",
    }:
        raise ExternalS3CapabilityError("PyMDP challenge keys mismatch")
    likelihood_high = _finite_number(case["likelihood_high"], "$.likelihood_high")
    prior_state0 = _finite_number(case["prior_state0"], "$.prior_state0")
    preferences = _number_list(case["preferences"], "$.preferences", 2)
    primary = case["primary_observation"]
    boundary = case["boundary_observation"]
    if (
        isinstance(primary, bool)
        or isinstance(boundary, bool)
        or primary != 0
        or boundary != 1
    ):
        raise ExternalS3CapabilityError("PyMDP observation boundary mismatch")
    if not 0.70 < likelihood_high < 0.90 or not 0.40 < prior_state0 < 0.60:
        raise ExternalS3CapabilityError("PyMDP challenge is outside fixed bounds")
    likelihood = (
        (likelihood_high, 1.0 - likelihood_high),
        (1.0 - likelihood_high, likelihood_high),
    )
    prior = (prior_state0, 1.0 - prior_state0)

    def result_for(observation: int) -> dict[str, list[float]]:
        raw = [likelihood[observation][state] * prior[state] for state in range(2)]
        normalizer = sum(raw)
        posterior = [value / normalizer for value in raw]
        policy_scores: list[float] = []
        for action in (0, 1):
            next_state = posterior if action == 0 else list(reversed(posterior))
            predicted_observation = [
                sum(likelihood[observation_index][state] * next_state[state] for state in range(2))
                for observation_index in range(2)
            ]
            policy_scores.append(
                sum(predicted_observation[index] * preferences[index] for index in range(2))
            )
        return {
            "posterior": posterior,
            "policy": _softmax(policy_scores),
            "negative_expected_free_energy": policy_scores,
        }

    primary_result = result_for(primary)
    boundary_result = result_for(boundary)
    wrong_policy = list(reversed(primary_result["policy"]))
    return {
        "primary": primary_result,
        "boundary": boundary_result,
        "wrong_policy": wrong_policy,
    }


def _expected_for(profile: S3CapabilityProfile, case: dict[str, Any]) -> dict[str, Any]:
    if profile is PYDMD_PROFILE:
        return _pydmd_expected(case)
    if profile is PYMDP_PROFILE:
        return _pymdp_expected(case)
    raise ExternalS3CapabilityError("unknown external S3 profile")


def _flatten_numbers(value: object, path: str) -> list[float]:
    if isinstance(value, list):
        output: list[float] = []
        for index, item in enumerate(value):
            output.extend(_flatten_numbers(item, f"{path}[{index}]"))
        return output
    return [_finite_number(value, path)]


def _comparison(actual: object, expected: object) -> dict[str, Any]:
    try:
        actual_values = _flatten_numbers(actual, "$.actual")
        expected_values = _flatten_numbers(expected, "$.expected")
    except ExternalS3CapabilityError as exc:
        return {"pass": False, "error": str(exc)}
    if len(actual_values) != len(expected_values):
        return {"pass": False, "error": "length_mismatch"}
    error = max(
        (abs(actual_value - expected_value) for actual_value, expected_value in zip(actual_values, expected_values)),
        default=0.0,
    )
    return {
        "pass": error <= CONTROL_TOLERANCE,
        "maximum_absolute_error": error,
        "tolerance": CONTROL_TOLERANCE,
    }


def evaluate_s3_output(
    profile: S3CapabilityProfile, challenge_case: dict[str, Any], observed: object
) -> dict[str, Any]:
    """Recompute a profile result and all required controls in the controller."""

    expected = _expected_for(profile, challenge_case)
    if profile is PYDMD_PROFILE:
        if not isinstance(observed, dict) or set(observed) != {
            "eigenvalue_real",
            "eigenvalue_imaginary",
            "reconstructed_values",
            "boundary_terminal",
        }:
            return {
                "controls": {"positive": False, "targeted_negative": False, "boundary": False},
                "expected": expected,
                "comparisons": {},
                "errors": ["observed_keys_mismatch"],
            }
        eigenvalue = _comparison(observed["eigenvalue_real"], expected["eigenvalue_real"])
        imaginary = _comparison(observed["eigenvalue_imaginary"], expected["eigenvalue_imaginary"])
        reconstruction = _comparison(observed["reconstructed_values"], expected["reconstructed_values"])
        boundary = _comparison(observed["boundary_terminal"], expected["boundary_terminal"])
        wrong = _comparison(observed["eigenvalue_real"], expected["wrong_multiplier"])
        wrong_distinct = _comparison(expected["eigenvalue_real"], expected["wrong_multiplier"])
        all_checks = (eigenvalue, imaginary, reconstruction, boundary, wrong, wrong_distinct)
        errors = [item["error"] for item in all_checks if "error" in item]
        controls = {
            "positive": bool(eigenvalue.get("pass") and imaginary.get("pass") and reconstruction.get("pass")),
            "targeted_negative": bool(
                wrong.get("pass") is False
                and "error" not in wrong
                and wrong_distinct.get("pass") is False
                and "error" not in wrong_distinct
            ),
            "boundary": bool(boundary.get("pass")),
        }
        return {
            "controls": controls,
            "expected": expected,
            "comparisons": {
                "eigenvalue": eigenvalue,
                "imaginary_component": imaginary,
                "reconstruction": reconstruction,
                "boundary_terminal": boundary,
                "targeted_negative_wrong_multiplier_match": wrong,
                "targeted_negative_expected_multiplier_distinct": wrong_distinct,
            },
            "errors": errors,
        }
    if not isinstance(observed, dict) or set(observed) != {"primary", "boundary"}:
        return {
            "controls": {"positive": False, "targeted_negative": False, "boundary": False},
            "expected": expected,
            "comparisons": {},
            "errors": ["observed_keys_mismatch"],
        }
    comparisons: dict[str, Any] = {}
    errors: list[str] = []
    for label in ("primary", "boundary"):
        actual = observed[label]
        expected_label = expected[label]
        if not isinstance(actual, dict) or set(actual) != {
            "posterior",
            "policy",
            "negative_expected_free_energy",
        }:
            comparisons[label] = {"error": "result_keys_mismatch"}
            errors.append(f"{label}_result_keys_mismatch")
            continue
        comparisons[label] = {
            key: _comparison(actual[key], expected_label[key])
            for key in ("posterior", "policy", "negative_expected_free_energy")
        }
        errors.extend(
            f"{label}.{key}:{value['error']}"
            for key, value in comparisons[label].items()
            if "error" in value
        )
    wrong = _comparison(
        observed.get("primary", {}).get("policy") if isinstance(observed.get("primary"), dict) else None,
        expected["wrong_policy"],
    )
    wrong_distinct = _comparison(expected["primary"]["policy"], expected["wrong_policy"])
    primary = comparisons.get("primary", {})
    boundary = comparisons.get("boundary", {})
    def all_pass(group: object) -> bool:
        return bool(
            isinstance(group, dict)
            and all(
                isinstance(value, dict) and value.get("pass") is True
                for value in group.values()
            )
        )

    controls = {
        "positive": all_pass(primary),
        "targeted_negative": bool(
            wrong.get("pass") is False
            and "error" not in wrong
            and wrong_distinct.get("pass") is False
            and "error" not in wrong_distinct
        ),
        "boundary": all_pass(boundary),
    }
    comparisons["targeted_negative_wrong_policy_match"] = wrong
    comparisons["targeted_negative_expected_policy_distinct"] = wrong_distinct
    if "error" in wrong:
        errors.append(f"wrong_policy:{wrong['error']}")
    if "error" in wrong_distinct:
        errors.append(f"wrong_policy_distinct:{wrong_distinct['error']}")
    return {
        "controls": controls,
        "expected": expected,
        "comparisons": comparisons,
        "errors": errors,
    }


def _runtime_pin_dict() -> dict[str, object]:
    """Retain the receipt field name while carrying a portable policy."""

    return runtime_profile_dict("python")


def _inspect_profile_artifacts(profile: S3CapabilityProfile) -> dict[str, Any]:
    """Inspect portable runtime and distribution ownership without hard pins."""

    runtime = inspect_external_runtime("python")
    artifacts = inspect_python_distributions(_runtime_requirements(profile))
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


def _worker_command(profile: S3CapabilityProfile) -> list[str]:
    executable = selected_runtime_executable("python")
    if executable is None:
        raise ExternalS3CapabilityError("controller python runtime unavailable")
    return [
        str(executable),
        "-B",
        "-m",
        "constraintbox.external_s3_capability",
        WORKER_ARGUMENT,
        profile.capability_id,
    ]


def _worker_environment(profile: S3CapabilityProfile, cache_directory: Path) -> dict[str, str]:
    environment = {
        key: value
        for key, value in os.environ.items()
        if key not in {"PYTHONHOME", "PYTHONPATH", "PYTHONUSERBASE", "MPLCONFIGDIR"}
    }
    environment["PYTHONPATH"] = str(_source_root())
    environment["PYTHONNOUSERSITE"] = "1"
    environment["MPLCONFIGDIR"] = str(cache_directory)
    if profile is PYMDP_PROFILE:
        environment["JAX_ENABLE_X64"] = "1"
    return environment


def _prepare_matplotlib_cache(profile: S3CapabilityProfile) -> tuple[Path | None, str | None]:
    """Warm only Matplotlib's disposable font cache before the witnessed worker.

    PyDMD imports Matplotlib through its package surface.  A fresh Matplotlib
    config directory emits a font-cache progress line on the first import,
    which would otherwise make the witnessed worker protocol non-clean.  This
    setup subprocess is not a capability operation and is never used as
    evidence; it merely gives the fixed worker a controller-owned temporary
    cache path.  A missing or failing setup parks the capability.
    """

    cache_directory = Path(tempfile.gettempdir()) / "constraintbox-s3-matplotlib-cache-v1"
    try:
        cache_directory.mkdir(mode=0o700, parents=True, exist_ok=True)
    except OSError as exc:
        return None, f"matplotlib_cache_unavailable:{type(exc).__name__}"
    if profile is not PYDMD_PROFILE:
        return cache_directory, None
    executable = selected_runtime_executable("python")
    if executable is None:
        return None, "controller_python_runtime_unavailable"
    try:
        setup = subprocess.run(
            [str(executable), "-B", "-c", "import matplotlib.font_manager"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=_source_root(),
            env=_worker_environment(profile, cache_directory),
            check=False,
            timeout=WORKER_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired:
        return None, "matplotlib_cache_timeout"
    except OSError as exc:
        return None, f"matplotlib_cache_launch_unavailable:{type(exc).__name__}"
    if setup.returncode != 0:
        return None, "matplotlib_cache_setup_failed"
    return cache_directory, None


def _assert_import_source(module_path: object, expected: Path, label: str) -> None:
    if not isinstance(module_path, str) or Path(module_path).resolve() != expected:
        raise ExternalS3CapabilityError(f"imported {label} source mismatch")


def _distribution_origin(pins: dict[str, Any], index: int, label: str) -> Path:
    """Read a controller-observed package origin without a static file pin."""

    try:
        origin = pins["artifacts"][index]["module_origins"][0]["resolved_origin"]
        return Path(origin).resolve(strict=True)
    except (IndexError, KeyError, OSError, TypeError) as exc:
        raise ExternalS3CapabilityError(
            f"{label} distribution observation unavailable"
        ) from exc


def _pydmd_worker_operation(
    case: dict[str, Any], pins: dict[str, Any]
) -> tuple[dict[str, Any], dict[str, Any]]:
    import numpy as np
    import pydmd
    from pydmd import DMD

    pydmd_origin = _distribution_origin(pins, 0, "PyDMD")
    _assert_import_source(pydmd.__file__, pydmd_origin, "PyDMD")
    source = inspect.getsourcefile(DMD)
    if not isinstance(source, str) or Path(source).resolve().parent != pydmd_origin.parent:
        raise ExternalS3CapabilityError("imported PyDMD DMD source mismatch")
    if not callable(getattr(DMD, "fit", None)):
        raise _WorkerUnavailable("pydmd.DMD.fit unavailable")
    expected = _pydmd_expected(case)
    snapshots = np.asarray(expected["reconstructed_values"], dtype=np.float64).reshape(1, -1)
    model = DMD(svd_rank=1, exact=True)
    model.fit(snapshots)
    eigenvalue = complex(model.eigs[0])
    reconstruction = np.asarray(model.reconstructed_data, dtype=np.complex128).reshape(-1)
    if reconstruction.shape != (7,):
        raise ExternalS3CapabilityError("PyDMD reconstruction shape mismatch")
    return (
        {
            "eigenvalue_real": float(eigenvalue.real),
            "eigenvalue_imaginary": float(eigenvalue.imag),
            "reconstructed_values": [float(value.real) for value in reconstruction],
            "boundary_terminal": float(reconstruction[6].real),
        },
        {
            "pydmd_version": importlib.metadata.version("PyDMD"),
            "numpy_version": importlib.metadata.version("numpy"),
            "python_executable_resolved_path": str(Path(sys.executable).resolve()),
            "operation": PYDMD_PROFILE.runtime["operation"],
        },
    )


def _pymdp_worker_operation(
    case: dict[str, Any], pins: dict[str, Any]
) -> tuple[dict[str, Any], dict[str, Any]]:
    warnings.filterwarnings(
        "ignore",
        message="A JAX array is being set as static!",
        category=UserWarning,
    )
    import jax

    jax.config.update("jax_enable_x64", True)
    import jax.numpy as jnp
    import pymdp
    from pymdp.agent import Agent

    pymdp_origin = _distribution_origin(pins, 0, "PyMDP")
    _assert_import_source(pymdp.__file__, pymdp_origin, "PyMDP")
    agent_source = inspect.getsourcefile(Agent)
    if not isinstance(agent_source, str) or Path(agent_source).resolve().parent != pymdp_origin.parent:
        raise ExternalS3CapabilityError("imported PyMDP Agent source mismatch")
    if not callable(getattr(Agent, "infer_states", None)) or not callable(
        getattr(Agent, "infer_policies", None)
    ):
        raise _WorkerUnavailable("PyMDP state or policy inference unavailable")
    expected = _pymdp_expected(case)
    likelihood_high = float(case["likelihood_high"])
    prior_state0 = float(case["prior_state0"])
    preferences = [float(value) for value in case["preferences"]]
    a = [
        jnp.asarray(
            [
                [likelihood_high, 1.0 - likelihood_high],
                [1.0 - likelihood_high, likelihood_high],
            ],
            dtype=jnp.float64,
        )
    ]
    b = [
        jnp.asarray(
            [
                [[1.0, 0.0], [0.0, 1.0]],
                [[0.0, 1.0], [1.0, 0.0]],
            ],
            dtype=jnp.float64,
        )
    ]
    c = [jnp.asarray(preferences, dtype=jnp.float64)]
    prior = [jnp.asarray([[prior_state0, 1.0 - prior_state0]], dtype=jnp.float64)]
    agent = Agent(
        A=a,
        B=b,
        C=c,
        gamma=1.0,
        policy_len=1,
        batch_size=1,
        use_utility=True,
        use_states_info_gain=False,
        use_param_info_gain=False,
        use_inductive=False,
    )

    def infer(observation: int) -> dict[str, list[float]]:
        qs, _info = agent.infer_states(
            [jnp.asarray([observation], dtype=jnp.int32)],
            empirical_prior=prior,
            return_info=True,
        )
        q_pi, neg_efe = agent.infer_policies(qs)
        return {
            "posterior": [float(value) for value in qs[0][0, -1]],
            "policy": [float(value) for value in q_pi[0]],
            "negative_expected_free_energy": [float(value) for value in neg_efe[0]],
        }

    observed = {
        "primary": infer(int(case["primary_observation"])),
        "boundary": infer(int(case["boundary_observation"])),
    }
    return (
        observed,
        {
            "pymdp_version": importlib.metadata.version("inferactively-pymdp"),
            "jax_version": importlib.metadata.version("jax"),
            "jax_x64_enabled": bool(jax.config.x64_enabled),
            "python_executable_resolved_path": str(Path(sys.executable).resolve()),
            "operation": PYMDP_PROFILE.runtime["operation"],
        },
    )


def _worker_witness(profile: S3CapabilityProfile, transport: dict[str, Any]) -> dict[str, Any]:
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
        raise ExternalS3CapabilityError("worker transport keys mismatch")
    if transport["schema"] != WORKER_TRANSPORT_SCHEMA:
        raise ExternalS3CapabilityError("worker transport schema mismatch")
    if transport["capability_id"] != profile.capability_id:
        raise ExternalS3CapabilityError("worker transport id mismatch")
    if transport["exact_api"] != list(profile.exact_apis):
        raise ExternalS3CapabilityError("worker transport API mismatch")
    binding = s3_capability_binding_from_dict(profile, transport["execution_binding"])
    binding_body = validate_s3_capability_binding(profile, binding)
    expected_case = derive_s3_challenge_case(profile, binding.challenge_seed_hex)
    if transport["challenge_case"] != expected_case:
        raise ExternalS3CapabilityError("worker challenge does not match binding")
    source_path = Path(__file__).resolve()
    source_sha256 = _sha256_file(source_path)
    if (
        transport["capability_source_path"] != str(source_path)
        or transport["capability_source_sha256"] != source_sha256
    ):
        raise ExternalS3CapabilityError("worker source binding mismatch")
    if transport["runtime_pin"] != _runtime_pin_dict():
        raise ExternalS3CapabilityError("worker runtime pin mismatch")
    pins = _inspect_profile_artifacts(profile)
    if pins["status"] != "PASS":
        raise _WorkerUnavailable(pins["reason"])
    if profile is PYDMD_PROFILE:
        observed, runtime = _pydmd_worker_operation(expected_case, pins)
    elif profile is PYMDP_PROFILE:
        observed, runtime = _pymdp_worker_operation(expected_case, pins)
    else:
        raise ExternalS3CapabilityError("worker profile mismatch")
    if not _runtime_witness_matches_profile(profile, runtime):
        raise ExternalS3CapabilityError("worker runtime identity mismatch")
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
    profile: S3CapabilityProfile,
    binding: dict[str, str],
    challenge_case: dict[str, Any],
    capability_source_sha256: str,
) -> dict[str, Any]:
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
    command = _worker_command(profile)
    cache_directory, setup_error = _prepare_matplotlib_cache(profile)
    started = time.monotonic()
    process: subprocess.CompletedProcess[bytes] | None = None
    launch_error: str | None = setup_error
    if launch_error is None and cache_directory is not None:
        try:
            process = subprocess.run(
                command,
                input=canonical_json(transport),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=_source_root(),
                env=_worker_environment(profile, cache_directory),
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
    evaluation = evaluate_s3_output(profile, challenge_case, response["observed"])
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
    profile: S3CapabilityProfile,
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


class ExternalS3CapabilityBroker:
    """Fixed controller broker for one external S3 package profile."""

    def __init__(self, profile: S3CapabilityProfile) -> None:
        if profile not in (PYDMD_PROFILE, PYMDP_PROFILE):
            raise ExternalS3CapabilityError("broker requires one fixed profile")
        self.profile = profile
        self.source_path = Path(__file__).resolve()

    def run(self, binding: S3CapabilityBinding) -> dict[str, Any]:
        binding_body = validate_s3_capability_binding(self.profile, binding)
        source_sha256 = _sha256_file(self.source_path)
        challenge_case = derive_s3_challenge_case(self.profile, binding.challenge_seed_hex)
        sources_before = _inspect_profile_artifacts(self.profile)
        row: dict[str, Any] | None = None
        status = sources_before["status"]
        reason = sources_before["reason"]
        if status == "PASS":
            row = _row_from_worker(
                profile=self.profile,
                binding=binding_body,
                challenge_case=challenge_case,
                capability_source_sha256=source_sha256,
            )
            status = row["status"]
            reason = row["reason"]
        sources_after = _inspect_profile_artifacts(self.profile)
        if sources_after != sources_before:
            status = "FAIL"
            reason = "profile_sources_changed_during_operation"
        elif sources_after["status"] != "PASS":
            status = sources_after["status"]
            reason = sources_after["reason"]
        body = _receipt_body(
            profile=self.profile,
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
        errors = validate_s3_capability_receipt(
            receipt,
            expected_binding=binding,
            expected_receipt_sha256=receipt["receipt_sha256"],
            require_pass=status == "PASS",
        )
        if errors:
            raise ExternalS3CapabilityError(
                "capability self-verification failed: " + "; ".join(errors)
            )
        return receipt


class PyDMDCapabilityBroker(ExternalS3CapabilityBroker):
    def __init__(self) -> None:
        super().__init__(PYDMD_PROFILE)


class PyMDPCapabilityBroker(ExternalS3CapabilityBroker):
    def __init__(self) -> None:
        super().__init__(PYMDP_PROFILE)


def validate_s3_capability_receipt(
    receipt: dict[str, Any],
    *,
    expected_binding: S3CapabilityBinding,
    expected_receipt_sha256: str,
    require_pass: bool = True,
) -> tuple[str, ...]:
    """Revalidate an external S3 receipt against current controller pins."""

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
        profile = _profile_for(expected_binding.capability_id)
        expected_binding_body = validate_s3_capability_binding(profile, expected_binding)
    except ExternalS3CapabilityError as exc:
        return (f"$.binding:{exc}",)
    supplied_digest = body["receipt_sha256"]
    if not _valid_sha256(supplied_digest):
        error("$.receipt_sha256", "invalid_sha256")
    expect(supplied_digest, expected_receipt_sha256, "$.receipt_root")
    digest_body = dict(body)
    digest_body.pop("receipt_sha256")
    expect(supplied_digest, _SHA256(canonical_json(digest_body)).hexdigest(), "$.receipt_sha256")
    expect(body["schema"], CAPABILITY_SCHEMA, "$.schema")
    expect(body["capability_id"], profile.capability_id, "$.capability_id")
    expect(body["external_system"], True, "$.external_system")
    expect(body["kernel_membership"], "EXTERNAL_NOT_CB_KERNEL", "$.kernel_membership")
    for key in ("release_allowed", "engine_readiness_claim", "cr_truth_claim", "promotion_allowed"):
        expect(body[key], False, f"$.{key}")
    expect(body["claim_ceiling"], profile.claim_ceiling, "$.claim_ceiling")
    try:
        binding = s3_capability_binding_from_dict(profile, body["binding"])
    except ExternalS3CapabilityError as exc:
        error("$.binding", str(exc))
        binding = None
    if binding is not None:
        expect(binding, expected_binding, "$.binding")
        expect(
            body["binding_sha256"],
            _SHA256(canonical_json(expected_binding_body)).hexdigest(),
            "$.binding_sha256",
        )
    expected_case = derive_s3_challenge_case(profile, expected_binding.challenge_seed_hex)
    expect(body["challenge_case"], expected_case, "$.challenge_case")
    expect(
        body["challenge_case_sha256"],
        _SHA256(canonical_json(expected_case)).hexdigest(),
        "$.challenge_case_sha256",
    )
    try:
        current_source = _sha256_file(Path(__file__).resolve())
        current_pins = _inspect_profile_artifacts(profile)
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
    expect(row["challenge_case_sha256"], _SHA256(canonical_json(expected_case)).hexdigest(), "$.row.challenge_case_sha256")
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
    expect(row["command"], _worker_command(profile), "$.row.command")
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
    evaluation = evaluate_s3_output(profile, expected_case, row["observed"])
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
