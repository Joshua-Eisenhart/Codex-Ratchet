"""Controller-owned bounded SciPy and Diffrax capability primitives.

The two profiles in this module are deliberately small external tools.  The
controller derives their cases, selects its own compatible runtime and records
runtime/source observations, calls the worker in a separate process, recomputes
the analytic answers, requires a
replay, and requires an operation-severance run.  A passing receipt remains an
external observation: it never releases work or claims engine readiness.
"""

from __future__ import annotations

import hashlib
import math
import os
import re
import subprocess
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


INPUT_SCHEMA = "constraintbox.bounded-numerics-input.v1"
WITNESS_SCHEMA = "constraintbox.bounded-numerics-witness.v1"
BINDING_SCHEMA = "constraintbox.external-capability-binding.v1"
RECEIPT_SCHEMA = "constraintbox.bounded-numerics-capability-receipt.v1"
SEVERED_EXIT_CODE = 86
SEVERED_PREFIX = b"constraintbox.bounded-numerics.operation-severed.v1:"
_SHA256 = hashlib.sha256
_SAFE_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}")
_LOWER_SHA256 = re.compile(r"[0-9a-f]{64}")
_EMPTY_SHA256 = _SHA256(b"").hexdigest()


class ExternalBoundedNumericsError(RuntimeError):
    """A controller-owned bounded numeric capability failed validation."""


@dataclass(frozen=True)
class BoundedNumericsBinding:
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


@dataclass(frozen=True)
class BoundedNumericsProfile:
    capability_id: str
    step_id: str
    worker_selector: str
    exact_api: tuple[str, ...]
    python_distribution_requirements: tuple[
        tuple[str, tuple[str, ...], tuple[int, int, int], tuple[int, int, int]],
        ...,
    ]
    profile_source_path: Path
    claim_ceiling: str


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def worker_path() -> Path:
    return (
        Path(__file__).resolve().parents[2]
        / "external_capabilities"
        / "bounded_numerics_v1"
        / "workers"
        / "bounded_numerics_worker.py"
    )


def _sha256_file(path: Path) -> str:
    return _SHA256(path.read_bytes()).hexdigest()


def _valid_sha256(value: object) -> bool:
    return isinstance(value, str) and _LOWER_SHA256.fullmatch(value) is not None


def _number(value: object) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    converted = float(value)
    return converted if math.isfinite(converted) else None


def _runtime_pin() -> dict[str, object]:
    """Retain the profile under the legacy receipt key without host pins."""

    return runtime_profile_dict("python")


def _runtime_identity() -> dict[str, Any]:
    """Inspect the controller process runtime; never choose a second Python."""

    return inspect_external_runtime("python")


def _package_artifacts(profile: BoundedNumericsProfile) -> dict[str, Any]:
    """Check version/API ownership, not one local wheel's path or digest."""

    runtime = _runtime_identity()
    artifacts = inspect_python_distributions(
        profile.python_distribution_requirements
    )
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


def _required_distribution_versions(profile: BoundedNumericsProfile) -> dict[str, str] | None:
    inspected = _package_artifacts(profile)
    if inspected["status"] != "PASS":
        return None
    versions: dict[str, str] = {}
    for row in inspected["artifacts"]:
        if not isinstance(row, dict):
            return None
        name = row.get("distribution")
        version = row.get("version")
        if not isinstance(name, str) or not isinstance(version, str):
            return None
        versions[name] = version
    return versions


def validate_bounded_numerics_binding(
    profile: BoundedNumericsProfile,
    binding: BoundedNumericsBinding,
) -> dict[str, str]:
    if type(binding) is not BoundedNumericsBinding:
        raise ExternalBoundedNumericsError("binding must be BoundedNumericsBinding")
    if binding.capability_id != profile.capability_id:
        raise ExternalBoundedNumericsError("binding capability id mismatch")
    if binding.step_id != profile.step_id:
        raise ExternalBoundedNumericsError("binding step id mismatch")
    for field in ("capability_id", "run_id", "step_id"):
        value = getattr(binding, field)
        if not isinstance(value, str) or _SAFE_ID.fullmatch(value) is None:
            raise ExternalBoundedNumericsError(f"binding {field} is invalid")
    for field in ("flow_policy_sha256", "request_sha256", "challenge_seed_hex"):
        if not _valid_sha256(getattr(binding, field)):
            raise ExternalBoundedNumericsError(f"binding {field} is invalid")
    return binding.to_dict()


def bounded_numerics_binding_from_dict(
    profile: BoundedNumericsProfile, value: object
) -> BoundedNumericsBinding:
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
        raise ExternalBoundedNumericsError("binding keys mismatch")
    if value.get("schema") != BINDING_SCHEMA:
        raise ExternalBoundedNumericsError("binding schema mismatch")
    try:
        binding = BoundedNumericsBinding(
            capability_id=value["capability_id"],
            run_id=value["run_id"],
            flow_policy_sha256=value["flow_policy_sha256"],
            request_sha256=value["request_sha256"],
            step_id=value["step_id"],
            challenge_seed_hex=value["challenge_seed_hex"],
        )
    except (KeyError, TypeError) as exc:
        raise ExternalBoundedNumericsError("binding malformed") from exc
    validate_bounded_numerics_binding(profile, binding)
    return binding


def _challenge_unit(seed: bytes, index: int) -> float:
    digest = _SHA256(seed + index.to_bytes(2, "big")).digest()
    return int.from_bytes(digest[:8], "big") / float((1 << 64) - 1)


def derive_bounded_numerics_case(
    profile: BoundedNumericsProfile, challenge_seed_hex: str
) -> dict[str, float]:
    if not _valid_sha256(challenge_seed_hex):
        raise ExternalBoundedNumericsError("challenge seed is invalid")
    seed = bytes.fromhex(challenge_seed_hex)
    if profile.worker_selector == "scipy_expm_rotation":
        angular_rate = round(0.35 + 1.15 * _challenge_unit(seed, 0), 12)
        duration = round(0.35 + 1.15 * _challenge_unit(seed, 1), 12)
        wrong_angular_rate = round(
            angular_rate + 0.18 + 0.12 * _challenge_unit(seed, 2), 12
        )
        return {
            "angular_rate": angular_rate,
            "duration": duration,
            "wrong_angular_rate": wrong_angular_rate,
            "boundary_duration": 0.0,
        }
    if profile.worker_selector == "diffrax_tsit5_affine":
        rate = round(-0.35 - 1.15 * _challenge_unit(seed, 0), 12)
        initial = round(0.75 + 1.25 * _challenge_unit(seed, 1), 12)
        duration = round(0.45 + 1.10 * _challenge_unit(seed, 2), 12)
        wrong_rate = round(rate - 0.18 - 0.12 * _challenge_unit(seed, 3), 12)
        boundary_initial = round(0.65 + 1.10 * _challenge_unit(seed, 4), 12)
        boundary_duration = round(0.35 + 0.90 * _challenge_unit(seed, 5), 12)
        return {
            "rate": rate,
            "initial": initial,
            "duration": duration,
            "wrong_rate": wrong_rate,
            "boundary_rate": 0.0,
            "boundary_initial": boundary_initial,
            "boundary_duration": boundary_duration,
        }
    raise ExternalBoundedNumericsError("unknown bounded numeric profile")


def _expected_observation(
    profile: BoundedNumericsProfile, case: dict[str, float]
) -> tuple[dict[str, Any], dict[str, Any]]:
    if profile.worker_selector == "scipy_expm_rotation":
        def rotation(rate: float, duration: float) -> list[list[float]]:
            angle = rate * duration
            return [
                [math.cos(angle), -math.sin(angle)],
                [math.sin(angle), math.cos(angle)],
            ]

        return (
            {
                "matrix": rotation(case["angular_rate"], case["duration"]),
                "boundary_matrix": rotation(
                    case["angular_rate"], case["boundary_duration"]
                ),
            },
            {"matrix": rotation(case["wrong_angular_rate"], case["duration"])},
        )
    if profile.worker_selector == "diffrax_tsit5_affine":
        def terminal(rate: float, initial: float, duration: float) -> float:
            return initial * math.exp(rate * duration)

        return (
            {
                "terminal": terminal(case["rate"], case["initial"], case["duration"]),
                "boundary_terminal": terminal(
                    case["boundary_rate"],
                    case["boundary_initial"],
                    case["boundary_duration"],
                ),
            },
            {
                "terminal": terminal(
                    case["wrong_rate"], case["initial"], case["duration"]
                )
            },
        )
    raise ExternalBoundedNumericsError("unknown bounded numeric profile")


def _close_number(left: object, right: object, tolerance: float) -> bool:
    left_number = _number(left)
    right_number = _number(right)
    return (
        left_number is not None
        and right_number is not None
        and abs(left_number - right_number) <= tolerance
    )


def _close_matrix(left: object, right: object, tolerance: float) -> bool:
    if not isinstance(left, list) or not isinstance(right, list) or len(left) != 2 or len(right) != 2:
        return False
    return all(
        isinstance(left_row, list)
        and isinstance(right_row, list)
        and len(left_row) == 2
        and len(right_row) == 2
        and all(
            _close_number(left_row[column], right_row[column], tolerance)
            for column in range(2)
        )
        for left_row, right_row in zip(left, right)
    )


def _witness_errors(
    profile: BoundedNumericsProfile,
    witness: object,
    binding: dict[str, str],
    *,
    controller_pid: int,
) -> tuple[str, ...]:
    errors: list[str] = []
    if not isinstance(witness, dict):
        return ("witness_not_object",)
    expected_keys = {
        "schema",
        "profile_id",
        "exact_api",
        "observed",
        "runtime",
        "pid",
        "binding",
    }
    if set(witness) != expected_keys:
        errors.append("witness_keys_mismatch")
    if witness.get("schema") != WITNESS_SCHEMA:
        errors.append("witness_schema_mismatch")
    if witness.get("profile_id") != profile.capability_id:
        errors.append("witness_profile_id_mismatch")
    if witness.get("exact_api") != list(profile.exact_api):
        errors.append("exact_api_mismatch")
    if witness.get("binding") != binding:
        errors.append("execution_binding_mismatch")
    pid = witness.get("pid")
    if isinstance(pid, bool) or not isinstance(pid, int) or pid <= 0 or pid == controller_pid:
        errors.append("worker_pid_invalid_or_not_separate")
    runtime = witness.get("runtime")
    identity = _runtime_identity()
    versions = _required_distribution_versions(profile)
    expected_runtime_keys = {
        "python_executable_resolved_path",
        "package_versions",
    }
    if profile.worker_selector == "diffrax_tsit5_affine":
        expected_runtime_keys |= {"x64", "platform"}
    if (
        not isinstance(runtime, dict)
        or set(runtime) != expected_runtime_keys
        or not identity.get("eligible")
        or versions is None
        or runtime.get("python_executable_resolved_path")
        != identity.get("executable_resolved_path")
        or runtime.get("package_versions") != versions
        or (
            profile.worker_selector == "diffrax_tsit5_affine"
            and (runtime.get("x64") is not True or runtime.get("platform") != "cpu")
        )
    ):
        errors.append("runtime_profile_or_distribution_mismatch")
    observed = witness.get("observed")
    if profile.worker_selector == "scipy_expm_rotation":
        if not isinstance(observed, dict) or set(observed) != {"matrix", "boundary_matrix"}:
            errors.append("observed_keys_mismatch")
    elif not isinstance(observed, dict) or set(observed) != {"terminal", "boundary_terminal"}:
        errors.append("observed_keys_mismatch")
    return tuple(errors)


def _worker_environment(*, poisoned_operation: str | None = None) -> dict[str, str]:
    environment = os.environ.copy()
    environment.pop("PYTHONPATH", None)
    environment.pop("PYTHONHOME", None)
    # The operation-severance selector is a controller-owned negative-control
    # input.  Never inherit it from the process that launched ConstraintBox:
    # otherwise an ambient shell setting can turn a normal capability run into
    # a false non-pass.
    environment.pop("CONSTRAINTBOX_SEVER_OPERATION", None)
    environment["PYTHONHASHSEED"] = "0"
    if poisoned_operation is not None:
        environment["CONSTRAINTBOX_SEVER_OPERATION"] = poisoned_operation
    return environment


def _run_worker(
    profile: BoundedNumericsProfile,
    case: dict[str, float],
    binding: dict[str, str],
    *,
    poisoned_operation: str | None = None,
) -> dict[str, Any]:
    transport = {
        "schema": INPUT_SCHEMA,
        "profile_id": profile.capability_id,
        "case": case,
        "binding": binding,
    }
    input_bytes = canonical_json(transport)
    executable = selected_runtime_executable("python")
    if executable is None:
        raise ExternalBoundedNumericsError("controller-selected Python is unavailable")
    command = [str(executable), "-I", str(worker_path()), profile.worker_selector]
    started = time.monotonic()
    try:
        process = subprocess.run(
            command,
            input=input_bytes,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=_repo_root(),
            env=_worker_environment(poisoned_operation=poisoned_operation),
            timeout=180.0,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        return {
            "command": command,
            "input_sha256": _SHA256(input_bytes).hexdigest(),
            "elapsed_seconds": time.monotonic() - started,
            "timeout": True,
            "stdout_sha256": _SHA256(exc.stdout or b"").hexdigest(),
            "stderr_sha256": _SHA256(exc.stderr or b"").hexdigest(),
        }
    return {
        "command": command,
        "input_sha256": _SHA256(input_bytes).hexdigest(),
        "elapsed_seconds": time.monotonic() - started,
        "timeout": False,
        "returncode": process.returncode,
        "stdout_sha256": _SHA256(process.stdout).hexdigest(),
        "stderr_sha256": _SHA256(process.stderr).hexdigest(),
        "stdout": process.stdout,
        "stderr": process.stderr,
    }


def _parse_successful_worker_run(
    row: dict[str, Any],
    profile: BoundedNumericsProfile,
    binding: dict[str, str],
) -> tuple[dict[str, Any] | None, tuple[str, ...]]:
    if row.get("timeout") is not False:
        return None, ("worker_timeout",)
    if row.get("returncode") != 0:
        return None, ("worker_nonzero_exit",)
    stdout = row.get("stdout")
    stderr = row.get("stderr")
    if not isinstance(stdout, bytes) or not isinstance(stderr, bytes):
        return None, ("worker_stream_missing",)
    if stderr:
        return None, ("worker_stderr_not_empty",)
    try:
        witness = parse_json_object(stdout)
    except IntakeError as exc:
        return None, (f"worker_witness_not_strict_json={exc}",)
    if canonical_json(witness) + b"\n" != stdout:
        return None, ("worker_witness_not_canonical",)
    errors = _witness_errors(profile, witness, binding, controller_pid=os.getpid())
    if errors:
        return witness, errors
    return witness, ()


def _public_worker_row(row: dict[str, Any], witness: dict[str, Any] | None) -> dict[str, Any]:
    public = {
        key: value
        for key, value in row.items()
        if key not in {"stdout", "stderr"}
    }
    public["witness"] = witness
    return public


def _controls(
    profile: BoundedNumericsProfile,
    case: dict[str, float],
    normal: dict[str, Any] | None,
    replay: dict[str, Any] | None,
    severance: dict[str, Any],
) -> tuple[dict[str, bool], dict[str, Any]]:
    expected, wrong = _expected_observation(profile, case)
    normal_observed = normal.get("observed") if isinstance(normal, dict) else None
    replay_observed = replay.get("observed") if isinstance(replay, dict) else None
    tolerance = 1e-10 if profile.worker_selector == "scipy_expm_rotation" else 5e-8
    if profile.worker_selector == "scipy_expm_rotation":
        positive = _close_matrix(normal_observed.get("matrix") if isinstance(normal_observed, dict) else None, expected["matrix"], tolerance)
        boundary = _close_matrix(normal_observed.get("boundary_matrix") if isinstance(normal_observed, dict) else None, expected["boundary_matrix"], tolerance)
        wrong_match = _close_matrix(normal_observed.get("matrix") if isinstance(normal_observed, dict) else None, wrong["matrix"], tolerance)
        expected_wrong_distinct = not _close_matrix(expected["matrix"], wrong["matrix"], tolerance)
        replay_ok = _close_matrix(
            normal_observed.get("matrix") if isinstance(normal_observed, dict) else None,
            replay_observed.get("matrix") if isinstance(replay_observed, dict) else None,
            tolerance,
        ) and _close_matrix(
            normal_observed.get("boundary_matrix") if isinstance(normal_observed, dict) else None,
            replay_observed.get("boundary_matrix") if isinstance(replay_observed, dict) else None,
            tolerance,
        )
    else:
        positive = _close_number(normal_observed.get("terminal") if isinstance(normal_observed, dict) else None, expected["terminal"], tolerance)
        boundary = _close_number(normal_observed.get("boundary_terminal") if isinstance(normal_observed, dict) else None, expected["boundary_terminal"], tolerance)
        wrong_match = _close_number(normal_observed.get("terminal") if isinstance(normal_observed, dict) else None, wrong["terminal"], tolerance)
        expected_wrong_distinct = not _close_number(expected["terminal"], wrong["terminal"], tolerance)
        replay_ok = _close_number(
            normal_observed.get("terminal") if isinstance(normal_observed, dict) else None,
            replay_observed.get("terminal") if isinstance(replay_observed, dict) else None,
            tolerance,
        ) and _close_number(
            normal_observed.get("boundary_terminal") if isinstance(normal_observed, dict) else None,
            replay_observed.get("boundary_terminal") if isinstance(replay_observed, dict) else None,
            tolerance,
        )
    marker = SEVERED_PREFIX + profile.exact_api[-1].encode("utf-8") + b"\n"
    severance_ok = (
        severance.get("timeout") is False
        and severance.get("returncode") == SEVERED_EXIT_CODE
        and severance.get("stdout_sha256") == _EMPTY_SHA256
        and severance.get("stderr_sha256") == _SHA256(marker).hexdigest()
    )
    return (
        {
            "positive": positive,
            "targeted_negative": bool(not wrong_match and expected_wrong_distinct),
            "boundary": boundary,
            "replay": replay_ok,
            "severance": severance_ok,
        },
        {"expected": expected, "wrong_expected": wrong},
    )


def _source_pins(profile: BoundedNumericsProfile) -> dict[str, str]:
    common = Path(__file__).resolve()
    profile_path = profile.profile_source_path.resolve(strict=True)
    worker = worker_path().resolve(strict=True)
    return {
        "capability_source_sha256": _sha256_file(common),
        "profile_source_sha256": _sha256_file(profile_path),
        "worker_source_sha256": _sha256_file(worker),
    }


def _receipt_body(
    *,
    profile: BoundedNumericsProfile,
    binding: dict[str, str],
    case: dict[str, float],
    runtime: dict[str, Any],
    source_pins: dict[str, str],
    artifacts_before: dict[str, Any],
    artifacts_after: dict[str, Any],
    normal: dict[str, Any] | None,
    replay: dict[str, Any] | None,
    severance: dict[str, Any] | None,
    controls: dict[str, bool],
    expectations: dict[str, Any],
    status: str,
    reason: str,
) -> dict[str, Any]:
    return {
        "schema": RECEIPT_SCHEMA,
        "capability_id": profile.capability_id,
        "status": status,
        "reason": reason,
        "external_system": True,
        "kernel_membership": "EXTERNAL_NOT_CB_KERNEL",
        "binding": binding,
        "binding_sha256": _SHA256(canonical_json(binding)).hexdigest(),
        "challenge_case": case,
        "challenge_case_sha256": _SHA256(canonical_json(case)).hexdigest(),
        "runtime": runtime,
        **source_pins,
        "worker_source_sha256_expected": source_pins["worker_source_sha256"],
        "package_artifacts_before": artifacts_before,
        "package_artifacts_after": artifacts_after,
        "normal": normal,
        "replay": replay,
        "severance": severance,
        "controls": controls,
        "expectations": expectations,
        "release_allowed": False,
        "engine_readiness_claim": False,
        "cr_truth_claim": False,
        "promotion_allowed": False,
        "claim_ceiling": profile.claim_ceiling,
    }


class BoundedNumericsCapabilityBroker:
    """Run one fixed external numeric profile; never make a release decision.

    ``controller_replay_poisoned_operation`` is deliberately narrower than a
    general worker override.  It exists for one source-owned failure
    rehearsal: the controller may ask the *replay* of the profile's own exact
    operation to take the already-defined severance path.  It cannot select a
    worker, executable, profile, tolerance, or arbitrary operation, and the
    normal and ordinary severance calls remain fixed.
    """

    def __init__(
        self,
        profile: BoundedNumericsProfile,
        *,
        controller_replay_poisoned_operation: str | None = None,
    ) -> None:
        if (
            controller_replay_poisoned_operation is not None
            and controller_replay_poisoned_operation != profile.exact_api[-1]
        ):
            raise ExternalBoundedNumericsError(
                "controller replay poison must be the profile's exact operation"
            )
        self.profile = profile
        self._controller_replay_poisoned_operation = (
            controller_replay_poisoned_operation
        )

    def run(self, binding: BoundedNumericsBinding) -> dict[str, Any]:
        binding_body = validate_bounded_numerics_binding(self.profile, binding)
        case = derive_bounded_numerics_case(self.profile, binding.challenge_seed_hex)
        runtime = _runtime_identity()
        artifacts_before = _package_artifacts(self.profile)
        try:
            source_pins = _source_pins(self.profile)
        except OSError as exc:
            raise ExternalBoundedNumericsError(
                f"capability source pin unavailable: {exc}"
            ) from exc

        normal_public: dict[str, Any] | None = None
        replay_public: dict[str, Any] | None = None
        severance_public: dict[str, Any] | None = None
        normal_witness: dict[str, Any] | None = None
        replay_witness: dict[str, Any] | None = None
        controls = {
            "positive": False,
            "targeted_negative": False,
            "boundary": False,
            "replay": False,
            "severance": False,
        }
        expectations: dict[str, Any] = {"expected": {}, "wrong_expected": {}}
        status = runtime["disposition"]
        reason = runtime["reason"]
        if status == "PASS" and artifacts_before["status"] != "PASS":
            status = artifacts_before["status"]
            reason = artifacts_before["reason"]
        if status == "PASS":
            normal_row = _run_worker(self.profile, case, binding_body)
            normal_witness, normal_errors = _parse_successful_worker_run(
                normal_row, self.profile, binding_body
            )
            normal_public = _public_worker_row(normal_row, normal_witness)
            replay_row = _run_worker(
                self.profile,
                case,
                binding_body,
                poisoned_operation=self._controller_replay_poisoned_operation,
            )
            replay_witness, replay_errors = _parse_successful_worker_run(
                replay_row, self.profile, binding_body
            )
            replay_public = _public_worker_row(replay_row, replay_witness)
            severance_row = _run_worker(
                self.profile,
                case,
                binding_body,
                poisoned_operation=self.profile.exact_api[-1],
            )
            severance_public = _public_worker_row(severance_row, None)
            controls, expectations = _controls(
                self.profile,
                case,
                normal_witness,
                replay_witness,
                severance_row,
            )
            if normal_errors or replay_errors or not all(controls.values()):
                status = "FAIL"
                reason = "controller_recomputed_check_failed"
            else:
                status = "PASS"
                reason = "exact_operation_controls_passed"
        artifacts_after = _package_artifacts(self.profile)
        if artifacts_after != artifacts_before:
            status = "FAIL"
            reason = "package_artifacts_changed_during_operation"
        elif artifacts_after["status"] != "PASS":
            status = artifacts_after["status"]
            reason = artifacts_after["reason"]
        body = _receipt_body(
            profile=self.profile,
            binding=binding_body,
            case=case,
            runtime=runtime,
            source_pins=source_pins,
            artifacts_before=artifacts_before,
            artifacts_after=artifacts_after,
            normal=normal_public,
            replay=replay_public,
            severance=severance_public,
            controls=controls,
            expectations=expectations,
            status=status,
            reason=reason,
        )
        receipt = body | {"receipt_sha256": _SHA256(canonical_json(body)).hexdigest()}
        errors = validate_bounded_numerics_receipt(
            self.profile,
            receipt,
            expected_binding=binding,
            expected_receipt_sha256=receipt["receipt_sha256"],
            require_pass=status == "PASS",
        )
        if errors:
            raise ExternalBoundedNumericsError(
                "capability self-verification failed: " + "; ".join(errors)
            )
        return receipt


def _recompute_public_controls(
    profile: BoundedNumericsProfile,
    case: dict[str, float],
    normal: object,
    replay: object,
    severance: object,
) -> tuple[dict[str, bool], dict[str, Any], list[str]]:
    errors: list[str] = []
    normal_witness = normal.get("witness") if isinstance(normal, dict) else None
    replay_witness = replay.get("witness") if isinstance(replay, dict) else None
    if not isinstance(severance, dict):
        errors.append("severance_not_object")
        severance = {}
    controls, expectations = _controls(
        profile,
        case,
        normal_witness if isinstance(normal_witness, dict) else None,
        replay_witness if isinstance(replay_witness, dict) else None,
        severance,
    )
    return controls, expectations, errors


def validate_bounded_numerics_receipt(
    profile: BoundedNumericsProfile,
    receipt: dict[str, Any],
    *,
    expected_binding: BoundedNumericsBinding,
    expected_receipt_sha256: str,
    require_pass: bool = True,
) -> tuple[str, ...]:
    """Verify a receipt against current controller, source, and runtime pins."""

    errors: list[str] = []

    def expect(observed: object, expected: object, path: str) -> None:
        if observed != expected:
            errors.append(f"{path}:mismatch")

    try:
        body = parse_json_object(canonical_json(receipt))
    except (IntakeError, TypeError, ValueError) as exc:
        return (f"$:noncanonical={exc}",)
    expected_keys = {
        "schema", "capability_id", "status", "reason", "external_system",
        "kernel_membership", "binding", "binding_sha256", "challenge_case",
        "challenge_case_sha256", "runtime", "capability_source_sha256",
        "profile_source_sha256", "worker_source_sha256",
        "worker_source_sha256_expected", "package_artifacts_before",
        "package_artifacts_after", "normal", "replay", "severance", "controls",
        "expectations", "release_allowed", "engine_readiness_claim",
        "cr_truth_claim", "promotion_allowed", "claim_ceiling", "receipt_sha256",
    }
    if set(body) != expected_keys:
        return ("$:receipt_keys_mismatch",)
    root = body["receipt_sha256"]
    if not _valid_sha256(root):
        errors.append("$.receipt_sha256:invalid")
    expect(root, expected_receipt_sha256, "$.receipt_root")
    root_body = dict(body)
    root_body.pop("receipt_sha256")
    expect(root, _SHA256(canonical_json(root_body)).hexdigest(), "$.receipt_sha256")
    expect(body["schema"], RECEIPT_SCHEMA, "$.schema")
    expect(body["capability_id"], profile.capability_id, "$.capability_id")
    expect(body["external_system"], True, "$.external_system")
    expect(body["kernel_membership"], "EXTERNAL_NOT_CB_KERNEL", "$.kernel_membership")
    expect(body["release_allowed"], False, "$.release_allowed")
    expect(body["engine_readiness_claim"], False, "$.engine_readiness_claim")
    expect(body["cr_truth_claim"], False, "$.cr_truth_claim")
    expect(body["promotion_allowed"], False, "$.promotion_allowed")
    expect(body["claim_ceiling"], profile.claim_ceiling, "$.claim_ceiling")
    if body["status"] not in {"PASS", "FAIL", "PARKED"}:
        errors.append("$.status:invalid")
    if require_pass and body["status"] != "PASS":
        errors.append("$.status:pass_required")

    binding_body = validate_bounded_numerics_binding(profile, expected_binding)
    try:
        observed_binding = bounded_numerics_binding_from_dict(profile, body["binding"])
    except ExternalBoundedNumericsError as exc:
        errors.append(f"$.binding:{exc}")
    else:
        expect(observed_binding, expected_binding, "$.binding")
    expect(body["binding_sha256"], _SHA256(canonical_json(binding_body)).hexdigest(), "$.binding_sha256")
    case = derive_bounded_numerics_case(profile, expected_binding.challenge_seed_hex)
    expect(body["challenge_case"], case, "$.challenge_case")
    expect(body["challenge_case_sha256"], _SHA256(canonical_json(case)).hexdigest(), "$.challenge_case_sha256")
    runtime = _runtime_identity()
    expect(body["runtime"], runtime, "$.runtime")
    try:
        source_pins = _source_pins(profile)
    except OSError as exc:
        errors.append(f"$.sources:unavailable={exc}")
        return tuple(errors)
    for field, value in source_pins.items():
        expect(body[field], value, f"$.{field}")
    expect(
        body["worker_source_sha256_expected"],
        source_pins["worker_source_sha256"],
        "$.worker_source_sha256_expected",
    )
    artifacts = _package_artifacts(profile)
    expect(
        body["package_artifacts_before"],
        body["package_artifacts_after"],
        "$.package_artifacts_stability",
    )
    expect(
        body["package_artifacts_after"],
        artifacts,
        "$.package_artifacts_current",
    )

    # A runtime/artifact/source problem is itself a bounded non-pass outcome.
    # There is no worker evidence to validate in those cases, and treating it
    # as though there were would turn a correctly parked receipt into an
    # exception.  The one non-pass receipt that *does* contain a complete
    # worker triplet is the controller-recomputed failure below.  It must be
    # checked as rigorously as a PASS receipt; otherwise rehashing a changed
    # row would let a fake failure become a self-validating replay input.
    controlled_recomputed_failure = (
        body["status"] == "FAIL"
        and body["reason"] == "controller_recomputed_check_failed"
    )
    if body["status"] != "PASS" and not controlled_recomputed_failure:
        return tuple(errors)

    expected_transport = {
        "schema": INPUT_SCHEMA,
        "profile_id": profile.capability_id,
        "case": case,
        "binding": binding_body,
    }
    executable = selected_runtime_executable("python")
    if executable is None:
        errors.append("$.runtime:controller_executable_unavailable")
        return tuple(errors)
    expected_command = [str(executable), "-I", str(worker_path()), profile.worker_selector]
    expected_input_sha256 = _SHA256(canonical_json(expected_transport)).hexdigest()

    def validate_worker_row(field: str, *, require_success: bool) -> None:
        """Validate a public worker row without assuming its operation passed.

        A controlled failure can have a real nonzero or malformed worker run.
        Those rows do not carry raw process output, so their output hashes can
        only be type-checked.  When a worker did produce a witness, however,
        its canonical bytes and all semantic/runtime bindings remain fully
        checkable.
        """

        row = body[field]
        if not isinstance(row, dict):
            errors.append(f"$.{field}:not_object")
            return
        timeout = row.get("timeout")
        if type(timeout) is not bool:
            errors.append(f"$.{field}.timeout:invalid")
        expected_row_keys = {
            "command",
            "input_sha256",
            "elapsed_seconds",
            "timeout",
            "stdout_sha256",
            "stderr_sha256",
            "witness",
        }
        if timeout is False:
            expected_row_keys.add("returncode")
        if set(row) != expected_row_keys:
            errors.append(f"$.{field}:row_keys_mismatch")
        expect(row.get("command"), expected_command, f"$.{field}.command")
        expect(row.get("input_sha256"), expected_input_sha256, f"$.{field}.input_sha256")
        elapsed = _number(row.get("elapsed_seconds"))
        if elapsed is None or elapsed < 0.0:
            errors.append(f"$.{field}.elapsed_seconds:invalid")
        for hash_field in ("stdout_sha256", "stderr_sha256"):
            if not _valid_sha256(row.get(hash_field)):
                errors.append(f"$.{field}.{hash_field}:invalid")

        returncode = row.get("returncode")
        if timeout is False and (type(returncode) is not int):
            errors.append(f"$.{field}.returncode:invalid")
        if require_success:
            expect(timeout, False, f"$.{field}.timeout")
            expect(returncode, 0, f"$.{field}.returncode")

        witness = row.get("witness")
        if witness is None:
            if require_success:
                errors.append(f"$.{field}.witness_not_object")
            return
        if not isinstance(witness, dict):
            errors.append(f"$.{field}.witness_not_object")
            return
        if timeout is not False:
            errors.append(f"$.{field}.witness_timeout_mismatch")
        if returncode != 0:
            errors.append(f"$.{field}.witness_nonzero_exit")
        witness_errors = _witness_errors(
            profile, witness, binding_body, controller_pid=os.getpid()
        )
        for error in witness_errors:
            errors.append(f"$.{field}.{error}")
        expect(
            row.get("stdout_sha256"),
            _SHA256(canonical_json(witness) + b"\n").hexdigest(),
            f"$.{field}.stdout_sha256",
        )
        expect(row.get("stderr_sha256"), _EMPTY_SHA256, f"$.{field}.stderr_sha256")

    require_success = body["status"] == "PASS"
    for field in ("normal", "replay"):
        validate_worker_row(field, require_success=require_success)

    # Severance is never merely an error-looking row.  It is the exact,
    # controller-selected operation poison and therefore has a fixed command,
    # transport, exit code, streams, and no success witness in both PASS and
    # controlled-failure receipts.
    validate_worker_row("severance", require_success=False)
    severance = body["severance"]
    if isinstance(severance, dict):
        marker = SEVERED_PREFIX + profile.exact_api[-1].encode("utf-8") + b"\n"
        expect(severance.get("timeout"), False, "$.severance.timeout")
        expect(severance.get("returncode"), SEVERED_EXIT_CODE, "$.severance.returncode")
        expect(severance.get("stdout_sha256"), _EMPTY_SHA256, "$.severance.stdout_sha256")
        expect(
            severance.get("stderr_sha256"),
            _SHA256(marker).hexdigest(),
            "$.severance.stderr_sha256",
        )
        expect(severance.get("witness"), None, "$.severance.witness")

    recomputed_controls, expectations, recompute_errors = _recompute_public_controls(
        profile, case, body["normal"], body["replay"], body["severance"]
    )
    errors.extend(f"$.controls.{error}" for error in recompute_errors)
    expect(body["controls"], recomputed_controls, "$.controls")
    expect(body["expectations"], expectations, "$.expectations")
    controls = body["controls"]
    control_names = {
        "positive",
        "targeted_negative",
        "boundary",
        "replay",
        "severance",
    }
    if not isinstance(controls, dict) or set(controls) != control_names:
        errors.append("$.controls:shape_mismatch")
    elif any(type(value) is not bool for value in controls.values()):
        errors.append("$.controls:value_type_invalid")

    if controlled_recomputed_failure:
        # A controller-recomputed failure is meaningful only if the fixed
        # controls themselves show a failed obligation.  A rehashed all-true
        # record is a malformed PASS, not a legitimate failure receipt.
        if not isinstance(controls, dict) or not any(
            value is False for value in controls.values()
        ):
            errors.append("$.controls:controlled_failure_requires_false_control")
        if not isinstance(recomputed_controls, dict) or not any(
            value is False for value in recomputed_controls.values()
        ):
            errors.append(
                "$.controls:recomputed_failure_requires_false_control"
            )
        expect(body["status"], "FAIL", "$.status")
        expect(
            body["reason"],
            "controller_recomputed_check_failed",
            "$.reason",
        )
    else:
        if not isinstance(controls, dict) or not all(
            value is True for value in controls.values()
        ):
            errors.append("$.controls:not_all_true")
        expect(body["reason"], "exact_operation_controls_passed", "$.reason")
    return tuple(errors)
