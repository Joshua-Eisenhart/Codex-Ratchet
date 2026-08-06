"""Bounded, controller-owned Quimb and Cotengra external capability probes.

The two packages stay outside the ConstraintBox kernel.  This module owns one
fixed runtime, source/package pins, child-process environment policy, challenge
construction, and receipt verification.  The child worker can only return a
witness.  It cannot choose a profile, transition, retry, release, or claim
ceiling.

The profiles deliberately cover a tiny useful surface:

* ``quimb-density-v1`` creates two fixed 2-by-2 density matrices and calls
  ``quimb.qarray``, ``quimb.eigvalsh``, and ``quimb.trace``.
* ``cotengra-triangle-path-v1`` calls ``HyperOptimizer.search`` on one small
  triangle contraction.  A controller-side finite reference calculation
  checks its cost and intermediate size.

They are local execution evidence only.  This is not an engine-readiness,
simulation-readiness, release, promotion, CR-truth, or scientific claim.
"""

from __future__ import annotations

import hashlib
import math
import os
import re
import subprocess
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .intake import IntakeError, canonical_json, parse_json_object


CAPABILITY_ID = "quimb-cotengra-bounded-suite-v1"
CAPABILITY_SCHEMA = "constraintbox.external-quimb-cotengra-capability-receipt.v1"
BINDING_SCHEMA = "constraintbox.external-quimb-cotengra-capability-binding.v1"
ROW_SCHEMA = "constraintbox.external-quimb-cotengra-capability-row.v1"
WORKER_TRANSPORT_SCHEMA = "constraintbox.external-quimb-cotengra-worker-request.v1"
WORKER_WITNESS_SCHEMA = "constraintbox.external-quimb-cotengra-worker-witness.v1"
WORKER_POISON_SCHEMA = "constraintbox.external-quimb-cotengra-operation-poison.v1"
STEP_ID = "quimb-cotengra-bounded-tools"
QUIMB_PROFILE = "quimb-density-v1"
COTENGRA_PROFILE = "cotengra-triangle-path-v1"
PROFILE_IDS = (QUIMB_PROFILE, COTENGRA_PROFILE)
EXACT_APIS = {
    QUIMB_PROFILE: ("quimb.qarray", "quimb.eigvalsh", "quimb.trace"),
    COTENGRA_PROFILE: ("cotengra.HyperOptimizer", "cotengra.HyperOptimizer.search"),
}
PACKAGE_VERSIONS = {QUIMB_PROFILE: "1.14.0", COTENGRA_PROFILE: "0.8.0"}
COTENGRA_OPTIMIZER_CONFIG = {
    "max_repeats": 4,
    "progbar": False,
    "parallel": False,
    "minimize": "flops",
    "optlib_opts": {"sampler": "TPESampler", "sampler_opts": {"seed": 0}},
}
RUNTIME_INVOKED_PATH = "/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3"
RUNTIME_RESOLVED_PATH = (
    "/opt/homebrew/Cellar/python@3.13/3.13.6/Frameworks/"
    "Python.framework/Versions/3.13/bin/python3.13"
)
RUNTIME_SHA256 = "0d1fc12cf4887074b3eb257241f152cb85ca5a135879120b7e8e3b9aa57d5094"
WORKER_TIMEOUT_SECONDS = 90.0
CLAIM_CEILING = (
    "at most, one fresh controller-challenged Quimb density operation and one "
    "Cotengra triangle contraction-path operation under the pinned local "
    "runtime, with positive, wrong-value, boundary, operation-severance, and "
    "receipt-replay controls; not Quimb or Cotengra readiness, sim-stack "
    "readiness, CR truth, scientific proof, hostile-code containment, release, "
    "or canonical promotion"
)

_SHA256 = hashlib.sha256
_SAFE_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}")
_LOWER_SHA256 = re.compile(r"[0-9a-f]{64}")
_WORKER_RELATIVE_PATH = Path("workers/quimb_cotengra_capability_worker.py")

# This is filled from the reviewed worker source.  It makes a later change to
# the child program fail closed before any package API is invoked.
WORKER_SHA256 = "888694ed039a1fe12880d9bc36f0d68299f1dc22219f5ab4a818bae608b1707c"


@dataclass(frozen=True)
class ArtifactPin:
    """One exact package artifact expected in the selected Python runtime."""

    label: str
    path: str
    size_bytes: int
    sha256: str


ARTIFACT_PINS = (
    ArtifactPin(
        "quimb/__init__.py",
        "/Users/joshuaeisenhart/.local/share/codex-ratchet/envs/main/"
        "lib/python3.13/site-packages/quimb/__init__.py",
        8_230,
        "67f29c8a05a863a385fb990daa75f0f4aa6756e8cdfab0c453a01a90b7594eb0",
    ),
    ArtifactPin(
        "quimb/core.py",
        "/Users/joshuaeisenhart/.local/share/codex-ratchet/envs/main/"
        "lib/python3.13/site-packages/quimb/core.py",
        72_499,
        "826d1af98f43b3708b3d70db6cd01d177e2c49737f757d95bdf96a19ed724a9c",
    ),
    ArtifactPin(
        "quimb-1.14.0.dist-info/RECORD",
        "/Users/joshuaeisenhart/.local/share/codex-ratchet/envs/main/"
        "lib/python3.13/site-packages/quimb-1.14.0.dist-info/RECORD",
        17_546,
        "7821d2320e86a7cf2e918fd123a170f30aae083f85a1c061057b090e2da08c01",
    ),
    ArtifactPin(
        "cotengra/__init__.py",
        "/Users/joshuaeisenhart/.local/share/codex-ratchet/envs/main/"
        "lib/python3.13/site-packages/cotengra/__init__.py",
        9_156,
        "a45fe46283cb1f828301e9565e9cf92cd98ae5bdbb18419c7a027e3db99054e8",
    ),
    ArtifactPin(
        "cotengra-0.8.0.dist-info/RECORD",
        "/Users/joshuaeisenhart/.local/share/codex-ratchet/envs/main/"
        "lib/python3.13/site-packages/cotengra-0.8.0.dist-info/RECORD",
        9_223,
        "da2f6a450b7a4a12495a548c1a5295bcb5c5678f4aa721d4dd93be4e33ab022b",
    ),
)

# The actual per-run paths are made in a private controller-owned directory.
# This immutable policy, and then the instantiated values, are both bound into
# every transport and receipt.  A user or worker cannot substitute cache paths.
ENVIRONMENT_POLICY = {
    "schema": "constraintbox.external-quimb-cotengra-environment-policy.v1",
    "cache_root": "controller_private_temporary_directory",
    "PATH": "/usr/bin:/bin",
    "HOME": "cache_root/home",
    "NUMBA_CACHE_DIR": "cache_root/numba-cache",
    "MPLCONFIGDIR": "cache_root/matplotlib-cache",
    "PYTHONHASHSEED": "0",
    "PYTHONPATH": "removed",
    "PYTHONHOME": "removed",
}
ENVIRONMENT_POLICY_SHA256 = _SHA256(canonical_json(ENVIRONMENT_POLICY)).hexdigest()


class ExternalQuimbCotengraCapabilityError(RuntimeError):
    """A fixed Quimb/Cotengra external capability could not be verified."""


@dataclass(frozen=True)
class CapabilityBinding:
    """All caller-visible identity values for one controller-owned run."""

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
    return isinstance(value, str) and _LOWER_SHA256.fullmatch(value) is not None


def _finite_number(value: object, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ExternalQuimbCotengraCapabilityError(f"{label} must be finite")
    converted = float(value)
    if not math.isfinite(converted):
        raise ExternalQuimbCotengraCapabilityError(f"{label} must be finite")
    return converted


def _number_list(value: object, label: str, length: int) -> list[float]:
    if not isinstance(value, list) or len(value) != length:
        raise ExternalQuimbCotengraCapabilityError(
            f"{label} must be a list of length {length}"
        )
    return [_finite_number(item, f"{label}[{index}]") for index, item in enumerate(value)]


def validate_capability_binding(binding: CapabilityBinding) -> dict[str, str]:
    """Reject every binding substitution before any child process is launched."""

    if type(binding) is not CapabilityBinding:
        raise ExternalQuimbCotengraCapabilityError(
            "capability binding must be one frozen CapabilityBinding"
        )
    if binding.capability_id != CAPABILITY_ID:
        raise ExternalQuimbCotengraCapabilityError("capability binding id mismatch")
    if binding.step_id != STEP_ID:
        raise ExternalQuimbCotengraCapabilityError("capability binding step mismatch")
    for label, value in (
        ("run_id", binding.run_id),
        ("capability_id", binding.capability_id),
        ("step_id", binding.step_id),
    ):
        if not isinstance(value, str) or _SAFE_ID.fullmatch(value) is None:
            raise ExternalQuimbCotengraCapabilityError(
                f"capability binding {label} is invalid"
            )
    for label, value in (
        ("flow_policy_sha256", binding.flow_policy_sha256),
        ("request_sha256", binding.request_sha256),
        ("challenge_seed_hex", binding.challenge_seed_hex),
    ):
        if not _valid_sha256(value):
            raise ExternalQuimbCotengraCapabilityError(
                f"capability binding {label} is invalid"
            )
    return binding.to_dict()


def capability_binding_from_dict(value: object) -> CapabilityBinding:
    expected = {
        "schema",
        "capability_id",
        "run_id",
        "flow_policy_sha256",
        "request_sha256",
        "step_id",
        "challenge_seed_hex",
    }
    if not isinstance(value, dict) or set(value) != expected:
        raise ExternalQuimbCotengraCapabilityError("capability binding fields differ")
    if value.get("schema") != BINDING_SCHEMA:
        raise ExternalQuimbCotengraCapabilityError("capability binding schema mismatch")
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
        raise ExternalQuimbCotengraCapabilityError("capability binding malformed") from exc
    validate_capability_binding(binding)
    return binding


def _challenge_unit(seed: bytes, index: int) -> float:
    digest = _SHA256(seed + index.to_bytes(2, "big")).digest()
    return int.from_bytes(digest[:8], "big") / float((1 << 64) - 1)


def derive_challenge_cases(challenge_seed_hex: str) -> dict[str, dict[str, Any]]:
    """Derive the two fixed bounded cases without any model-authored input."""

    if not _valid_sha256(challenge_seed_hex):
        raise ExternalQuimbCotengraCapabilityError(
            "challenge seed must be 32 lowercase hex bytes"
        )
    seed = bytes.fromhex(challenge_seed_hex)
    diagonal = round(0.56 + 0.28 * _challenge_unit(seed, 0), 12)
    max_coherence = math.sqrt(diagonal * (1.0 - diagonal))
    coherence = round((0.12 + 0.32 * _challenge_unit(seed, 1)) * max_coherence, 12)
    expected = _quimb_expected([[diagonal, coherence], [coherence, 1.0 - diagonal]])
    wrong_eigenvalues = [
        round(expected["eigenvalues"][0] + 0.071, 12),
        round(expected["eigenvalues"][1] - 0.071, 12),
    ]
    return {
        QUIMB_PROFILE: {
            "rho": [[diagonal, coherence], [coherence, round(1.0 - diagonal, 12)]],
            "boundary_rho": [[1.0, 0.0], [0.0, 0.0]],
            "wrong_eigenvalues": wrong_eigenvalues,
        },
        COTENGRA_PROFILE: {
            "inputs": [[0, 1], [1, 2], [2, 0]],
            "sizes": {"0": 2, "1": 2, "2": 2},
            "boundary_sizes": {"0": 1, "1": 1, "2": 1},
            "wrong_observed": {"contraction_cost": 13, "max_size": 5},
        },
    }


def _quimb_expected(rho: object) -> dict[str, Any]:
    if not isinstance(rho, list) or len(rho) != 2:
        raise ExternalQuimbCotengraCapabilityError("Quimb rho must have two rows")
    row0 = _number_list(rho[0], "$.rho[0]", 2)
    row1 = _number_list(rho[1], "$.rho[1]", 2)
    a, b = row0
    c, d = row1
    if abs(b - c) > 1e-12:
        raise ExternalQuimbCotengraCapabilityError("Quimb rho must be real symmetric")
    discriminant = math.sqrt((a - d) ** 2 + 4.0 * b * c)
    return {
        "eigenvalues": sorted([(a + d - discriminant) / 2.0, (a + d + discriminant) / 2.0]),
        "trace": a + d,
    }


def _cotengra_reference(sizes: object) -> dict[str, int]:
    """Enumerate the three possible first contractions of the fixed triangle."""

    if not isinstance(sizes, dict) or set(sizes) != {"0", "1", "2"}:
        raise ExternalQuimbCotengraCapabilityError("Cotengra size fields differ")
    dimensions: dict[int, int] = {}
    for label in ("0", "1", "2"):
        item = sizes[label]
        if isinstance(item, bool) or not isinstance(item, int) or item not in {1, 2}:
            raise ExternalQuimbCotengraCapabilityError(
                "Cotengra dimensions must be one of the fixed finite values"
            )
        dimensions[int(label)] = item
    first_cost = dimensions[0] * dimensions[1] * dimensions[2]
    candidates = []
    for shared in (0, 1, 2):
        remaining = [dimension for index, dimension in dimensions.items() if index != shared]
        intermediate_size = remaining[0] * remaining[1]
        candidates.append((first_cost + intermediate_size, intermediate_size))
    contraction_cost, max_size = min(candidates)
    return {"contraction_cost": contraction_cost, "max_size": max_size}


def _runtime_and_artifact_state(worker_path: Path) -> dict[str, Any]:
    """Inspect controller-selected runtime/package/worker pins without imports."""

    state: dict[str, Any] = {
        "status": "PASS",
        "reason": "runtime_package_and_worker_pins_match",
        "runtime": {
            "invoked_path": RUNTIME_INVOKED_PATH,
            "expected_resolved_path": RUNTIME_RESOLVED_PATH,
            "expected_sha256": RUNTIME_SHA256,
        },
        "worker": {"path": str(worker_path), "expected_sha256": WORKER_SHA256},
        "artifacts": [],
    }
    try:
        invoked = Path(RUNTIME_INVOKED_PATH)
        resolved = invoked.resolve(strict=True)
        runtime_sha = _sha256_file(resolved)
        state["runtime"].update(
            {
                "observed": True,
                "resolved_path": str(resolved),
                "sha256": runtime_sha,
                "matches": str(resolved) == RUNTIME_RESOLVED_PATH and runtime_sha == RUNTIME_SHA256,
            }
        )
    except OSError as exc:
        state["runtime"].update({"observed": False, "error": f"{type(exc).__name__}: {exc}"})
        state.update({"status": "PARKED", "reason": "canonical_runtime_unavailable"})
    else:
        if not state["runtime"]["matches"]:
            state.update({"status": "FAIL", "reason": "canonical_runtime_pin_mismatch"})

    try:
        worker_sha = _sha256_file(worker_path)
        state["worker"].update({"observed": True, "sha256": worker_sha, "matches": worker_sha == WORKER_SHA256})
    except OSError as exc:
        state["worker"].update({"observed": False, "error": f"{type(exc).__name__}: {exc}"})
        if state["status"] == "PASS":
            state.update({"status": "PARKED", "reason": "worker_source_unavailable"})
    else:
        if not state["worker"]["matches"] and state["status"] == "PASS":
            state.update({"status": "FAIL", "reason": "worker_source_digest_mismatch"})

    for pin in ARTIFACT_PINS:
        path = Path(pin.path)
        row: dict[str, Any] = {
            "label": pin.label,
            "path": pin.path,
            "expected_size_bytes": pin.size_bytes,
            "expected_sha256": pin.sha256,
        }
        try:
            metadata = path.stat()
            digest = _sha256_file(path)
        except OSError as exc:
            row.update({"observed": False, "error": f"{type(exc).__name__}: {exc}"})
            if state["status"] == "PASS":
                state.update({"status": "PARKED", "reason": "package_artifact_unavailable"})
        else:
            matches = metadata.st_size == pin.size_bytes and digest == pin.sha256
            row.update({"observed": True, "size_bytes": metadata.st_size, "sha256": digest, "matches": matches})
            if not matches and state["status"] == "PASS":
                state.update({"status": "FAIL", "reason": "package_artifact_drift"})
        state["artifacts"].append(row)
    return state


def _environment_for(work_root: Path, *, poison: str | None = None) -> tuple[dict[str, str], dict[str, str | None]]:
    work_root.mkdir(mode=0o700)
    home = work_root / "home"
    numba_cache = work_root / "numba-cache"
    matplotlib_cache = work_root / "matplotlib-cache"
    home.mkdir(mode=0o700)
    numba_cache.mkdir(mode=0o700)
    matplotlib_cache.mkdir(mode=0o700)
    environment = {
        "PATH": "/usr/bin:/bin",
        "HOME": str(home),
        "NUMBA_CACHE_DIR": str(numba_cache),
        "MPLCONFIGDIR": str(matplotlib_cache),
        "PYTHONHASHSEED": "0",
    }
    if poison is not None:
        environment["CONSTRAINTBOX_OPERATION_POISON"] = poison
    descriptor: dict[str, str | None] = {
        "PATH": "/usr/bin:/bin",
        "HOME": str(home),
        "NUMBA_CACHE_DIR": str(numba_cache),
        "MPLCONFIGDIR": str(matplotlib_cache),
        "PYTHONHASHSEED": "0",
        "PYTHONPATH": None,
        "PYTHONHOME": None,
    }
    return environment, descriptor


def _response_json(stdout: bytes) -> dict[str, Any]:
    try:
        response = parse_json_object(stdout.strip())
    except IntakeError as exc:
        raise ExternalQuimbCotengraCapabilityError(
            f"worker output is not strict JSON: {exc}"
        ) from exc
    return response


def _close(actual: object, expected: object, tolerance: float = 1e-10) -> bool:
    if isinstance(expected, list):
        return isinstance(actual, list) and len(actual) == len(expected) and all(
            _close(item, target, tolerance) for item, target in zip(actual, expected, strict=True)
        )
    if isinstance(expected, (int, float)) and not isinstance(expected, bool):
        try:
            return math.isfinite(float(actual)) and abs(float(actual) - float(expected)) <= tolerance
        except (TypeError, ValueError):
            return False
    return actual == expected


def _evaluate_witness(
    *,
    profile_id: str,
    case: dict[str, Any],
    witness: dict[str, Any],
    binding: dict[str, str],
    environment: dict[str, str | None],
    controller_pid: int,
) -> dict[str, Any]:
    errors: list[str] = []
    if witness.get("schema") != WORKER_WITNESS_SCHEMA:
        errors.append("worker_witness_schema_mismatch")
    if witness.get("profile_id") != profile_id:
        errors.append("worker_profile_id_mismatch")
    if witness.get("exact_api") != list(EXACT_APIS[profile_id]):
        errors.append("worker_exact_api_mismatch")
    if witness.get("execution_binding") != binding:
        errors.append("worker_binding_mismatch")
    if witness.get("environment_policy_sha256") != ENVIRONMENT_POLICY_SHA256:
        errors.append("worker_environment_policy_mismatch")
    if witness.get("environment") != environment:
        errors.append("worker_environment_mismatch")
    worker_pid = witness.get("pid")
    if isinstance(worker_pid, bool) or not isinstance(worker_pid, int) or worker_pid <= 0:
        errors.append("worker_pid_invalid")
    elif worker_pid == controller_pid:
        errors.append("worker_not_separate_process")
    expected_runtime = {"package_version": PACKAGE_VERSIONS[profile_id]}
    if profile_id == COTENGRA_PROFILE:
        expected_runtime["optimizer_config"] = COTENGRA_OPTIMIZER_CONFIG
    runtime = witness.get("runtime")
    if not isinstance(runtime, dict) or runtime != expected_runtime:
        errors.append("worker_runtime_version_mismatch")
    observed = witness.get("observed")
    if not isinstance(observed, dict):
        errors.append("worker_observed_mismatch")
        observed = {}

    if profile_id == QUIMB_PROFILE:
        expected = _quimb_expected(case["rho"])
        boundary_expected = _quimb_expected(case["boundary_rho"])
        wrong = case["wrong_eigenvalues"]
        positive = _close(observed.get("eigenvalues"), expected["eigenvalues"]) and _close(observed.get("trace"), expected["trace"])
        boundary = _close(observed.get("boundary_eigenvalues"), boundary_expected["eigenvalues"]) and _close(observed.get("boundary_trace"), boundary_expected["trace"])
        targeted_negative = not _close(expected["eigenvalues"], wrong) and not _close(observed.get("eigenvalues"), wrong)
        expected_view = {
            "eigenvalues": expected["eigenvalues"],
            "trace": expected["trace"],
            "boundary_eigenvalues": boundary_expected["eigenvalues"],
            "boundary_trace": boundary_expected["trace"],
        }
    else:
        expected = _cotengra_reference(case["sizes"])
        boundary_expected = _cotengra_reference(case["boundary_sizes"])
        wrong = case["wrong_observed"]
        positive = _close(observed.get("contraction_cost"), expected["contraction_cost"], 0.0) and _close(observed.get("max_size"), expected["max_size"], 0.0)
        boundary = _close(observed.get("boundary_contraction_cost"), boundary_expected["contraction_cost"], 0.0) and _close(observed.get("boundary_max_size"), boundary_expected["max_size"], 0.0)
        targeted_negative = not _close(expected, wrong, 0.0) and not _close(
            {"contraction_cost": observed.get("contraction_cost"), "max_size": observed.get("max_size")}, wrong, 0.0
        )
        expected_view = {
            "contraction_cost": expected["contraction_cost"],
            "max_size": expected["max_size"],
            "boundary_contraction_cost": boundary_expected["contraction_cost"],
            "boundary_max_size": boundary_expected["max_size"],
        }
    controls = {"positive": positive, "targeted_negative": targeted_negative, "boundary": boundary}
    if errors:
        controls = {key: False for key in controls}
    return {"controls": controls, "expected": expected_view, "errors": errors}


def _validate_poison_witness(
    *,
    profile_id: str,
    poison: str,
    response: dict[str, Any],
    binding: dict[str, str],
    environment: dict[str, str | None],
    controller_pid: int,
) -> tuple[bool, str | None]:
    if response.get("schema") != WORKER_POISON_SCHEMA:
        return False, "poison_witness_schema_mismatch"
    if response.get("profile_id") != profile_id:
        return False, "poison_profile_mismatch"
    if response.get("poisoned_api") != poison:
        return False, "poison_target_mismatch"
    if response.get("exact_api") != list(EXACT_APIS[profile_id]):
        return False, "poison_exact_api_mismatch"
    if response.get("execution_binding") != binding:
        return False, "poison_binding_mismatch"
    if response.get("environment_policy_sha256") != ENVIRONMENT_POLICY_SHA256:
        return False, "poison_environment_policy_mismatch"
    if response.get("environment") != environment:
        return False, "poison_environment_mismatch"
    pid = response.get("pid")
    if isinstance(pid, bool) or not isinstance(pid, int) or pid <= 0 or pid == controller_pid:
        return False, "poison_worker_pid_mismatch"
    return True, None


class QuimbCotengraCapabilityBroker:
    """Controller for two source-pinned, separately-process workload checks."""

    def __init__(self, *, timeout_seconds: float = WORKER_TIMEOUT_SECONDS) -> None:
        if isinstance(timeout_seconds, bool) or not isinstance(timeout_seconds, (int, float)) or timeout_seconds <= 0:
            raise ExternalQuimbCotengraCapabilityError("worker timeout must be positive")
        self.timeout_seconds = float(timeout_seconds)
        self.controller_path = Path(__file__).resolve()
        self.constraint_box_root = self.controller_path.parents[2]
        self.worker_path = self.constraint_box_root / _WORKER_RELATIVE_PATH

    def _source_state(self) -> dict[str, str]:
        try:
            return {
                "controller_source_sha256": _sha256_file(self.controller_path),
                "worker_source_sha256": _sha256_file(self.worker_path),
            }
        except OSError as exc:
            raise ExternalQuimbCotengraCapabilityError(
                f"capability source unavailable: {exc}"
            ) from exc

    def _launch(
        self,
        *,
        payload: dict[str, Any],
        environment: dict[str, str],
    ) -> dict[str, Any]:
        command = [RUNTIME_INVOKED_PATH, "-I", str(self.worker_path)]
        input_bytes = canonical_json(payload)
        started = time.monotonic()
        try:
            process = subprocess.run(
                command,
                input=input_bytes,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=str(self.constraint_box_root),
                env=environment,
                timeout=self.timeout_seconds,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            return {
                "command": command,
                "input_sha256": _SHA256(input_bytes).hexdigest(),
                "status": "FAIL",
                "reason": "worker_timeout",
                "elapsed_seconds": time.monotonic() - started,
                "stdout_sha256": _SHA256(exc.stdout or b"").hexdigest(),
                "stderr_sha256": _SHA256(exc.stderr or b"").hexdigest(),
            }
        result: dict[str, Any] = {
            "command": command,
            "input_sha256": _SHA256(input_bytes).hexdigest(),
            "returncode": process.returncode,
            "elapsed_seconds": time.monotonic() - started,
            "stdout_sha256": _SHA256(process.stdout).hexdigest(),
            "stderr_sha256": _SHA256(process.stderr).hexdigest(),
        }
        if process.returncode != 0:
            result.update({"status": "FAIL", "reason": "worker_exit_nonzero"})
            return result
        try:
            response = _response_json(process.stdout)
        except ExternalQuimbCotengraCapabilityError as exc:
            result.update({"status": "FAIL", "reason": "worker_output_invalid", "detail": str(exc)})
            return result
        result.update(
            {
                "status": "PASS",
                "reason": "worker_returned_strict_witness",
                "response": response,
                "response_sha256": _SHA256(canonical_json(response)).hexdigest(),
            }
        )
        return result

    def _row(
        self,
        *,
        profile_id: str,
        case: dict[str, Any],
        binding: dict[str, str],
        work_root: Path,
        source_state: dict[str, str],
    ) -> dict[str, Any]:
        environment, descriptor = _environment_for(work_root / profile_id)
        payload_case = {key: value for key, value in case.items() if key not in {"wrong_eigenvalues", "wrong_observed"}}
        payload = {
            "schema": WORKER_TRANSPORT_SCHEMA,
            "profile_id": profile_id,
            "case": payload_case,
            "execution_binding": binding,
            "environment_policy_sha256": ENVIRONMENT_POLICY_SHA256,
        }
        normal = self._launch(payload=payload, environment=environment)
        row: dict[str, Any] = {
            "schema": ROW_SCHEMA,
            "profile_id": profile_id,
            "external_system": True,
            "kernel_membership": "EXTERNAL_NOT_CB_KERNEL",
            "exact_api": list(EXACT_APIS[profile_id]),
            "execution_binding": binding,
            "challenge_case": case,
            "challenge_case_sha256": _SHA256(canonical_json(case)).hexdigest(),
            "environment_policy": ENVIRONMENT_POLICY,
            "environment_policy_sha256": ENVIRONMENT_POLICY_SHA256,
            "environment": descriptor,
            "controller_source_sha256": source_state["controller_source_sha256"],
            "worker_source_sha256": source_state["worker_source_sha256"],
            "worker_source_sha256_expected": WORKER_SHA256,
            "runtime": {
                "invoked_path": RUNTIME_INVOKED_PATH,
                "resolved_path": RUNTIME_RESOLVED_PATH,
                "sha256": RUNTIME_SHA256,
                "package_version": PACKAGE_VERSIONS[profile_id],
            },
            "command": normal["command"],
            "input_sha256": normal["input_sha256"],
            "normal_launch": normal,
            "promotion_allowed": False,
            "engine_readiness_claim": False,
            "cr_truth_claim": False,
            "release_allowed": False,
            "claim_ceiling": CLAIM_CEILING,
        }
        if normal["status"] != "PASS":
            row.update({"status": "FAIL", "reason": normal["reason"], "controls": {"positive": False, "targeted_negative": False, "boundary": False, "operation_severance": False}})
            return row

        evaluation = _evaluate_witness(
            profile_id=profile_id,
            case=case,
            witness=normal["response"],
            binding=binding,
            environment=descriptor,
            controller_pid=os.getpid(),
        )
        poison_targets = (
            ("quimb.eigvalsh", "quimb.trace")
            if profile_id == QUIMB_PROFILE
            else ("cotengra.HyperOptimizer.search",)
        )
        poison_results: list[dict[str, Any]] = []
        poison_ok = True
        for poison in poison_targets:
            poison_environment, poison_descriptor = _environment_for(
                work_root / f"{profile_id}-{poison.replace('.', '_')}", poison=poison
            )
            poison_launch = self._launch(payload=payload, environment=poison_environment)
            accepted = False
            error: str | None = poison_launch.get("reason")
            if poison_launch["status"] == "PASS":
                accepted, error = _validate_poison_witness(
                    profile_id=profile_id,
                    poison=poison,
                    response=poison_launch["response"],
                    binding=binding,
                    environment=poison_descriptor,
                    controller_pid=os.getpid(),
                )
            poison_ok = poison_ok and accepted
            poison_results.append(
                {
                    "poisoned_api": poison,
                    "environment": poison_descriptor,
                    "launch": poison_launch,
                    "accepted": accepted,
                    "error": error,
                }
            )
        controls = dict(evaluation["controls"])
        controls["operation_severance"] = poison_ok
        passed = not evaluation["errors"] and all(controls.values())
        row.update(
            {
                "status": "PASS" if passed else "FAIL",
                "reason": "exact_operation_controls_passed" if passed else "exact_operation_controls_failed",
                "worker_witness": normal["response"],
                "worker_witness_sha256": normal["response_sha256"],
                "expected": evaluation["expected"],
                "controls": controls,
                "evaluation_errors": evaluation["errors"],
                "operation_severance": poison_results,
            }
        )
        return row

    def run(self, binding: CapabilityBinding) -> dict[str, Any]:
        """Run both controller-selected profiles and return a self-bound receipt."""

        binding_dict = validate_capability_binding(binding)
        source_before = self._source_state()
        pin_before = _runtime_and_artifact_state(self.worker_path)
        receipt: dict[str, Any] = {
            "schema": CAPABILITY_SCHEMA,
            "capability_id": CAPABILITY_ID,
            "binding": binding_dict,
            "binding_sha256": _SHA256(canonical_json(binding_dict)).hexdigest(),
            "source_before": source_before,
            "runtime_and_artifacts_before": pin_before,
            "external_system": True,
            "kernel_membership": "EXTERNAL_NOT_CB_KERNEL",
            "promotion_allowed": False,
            "engine_readiness_claim": False,
            "cr_truth_claim": False,
            "release_allowed": False,
            "claim_ceiling": CLAIM_CEILING,
            "environment_policy": ENVIRONMENT_POLICY,
            "environment_policy_sha256": ENVIRONMENT_POLICY_SHA256,
        }
        if pin_before["status"] != "PASS":
            receipt.update(
                {
                    "status": pin_before["status"],
                    "reason": pin_before["reason"],
                    "rows": [],
                    "source_after": self._source_state(),
                    "runtime_and_artifacts_after": _runtime_and_artifact_state(self.worker_path),
                }
            )
            return _with_receipt_sha256(receipt)

        cases = derive_challenge_cases(binding.challenge_seed_hex)
        try:
            with tempfile.TemporaryDirectory(prefix="constraintbox-quimb-cotengra-", dir="/private/tmp") as temporary:
                work_root = Path(temporary)
                rows = [
                    self._row(
                        profile_id=profile_id,
                        case=cases[profile_id],
                        binding=binding_dict,
                        work_root=work_root,
                        source_state=source_before,
                    )
                    for profile_id in PROFILE_IDS
                ]
        except OSError as exc:
            receipt.update(
                {
                    "status": "PARKED",
                    "reason": "controller_private_cache_unavailable",
                    "detail": f"{type(exc).__name__}: {exc}",
                    "rows": [],
                    "source_after": self._source_state(),
                    "runtime_and_artifacts_after": _runtime_and_artifact_state(self.worker_path),
                }
            )
            return _with_receipt_sha256(receipt)
        source_after = self._source_state()
        pin_after = _runtime_and_artifact_state(self.worker_path)
        stable_sources = source_after == source_before
        stable_pins = pin_after["status"] == "PASS"
        passed = stable_sources and stable_pins and len(rows) == len(PROFILE_IDS) and all(row["status"] == "PASS" for row in rows)
        receipt.update(
            {
                "status": "PASS" if passed else "FAIL",
                "reason": "exact_operation_controls_passed" if passed else "source_runtime_or_operation_control_failed",
                "rows": rows,
                "source_after": source_after,
                "runtime_and_artifacts_after": pin_after,
            }
        )
        return _with_receipt_sha256(receipt)


def _with_receipt_sha256(receipt: dict[str, Any]) -> dict[str, Any]:
    body = dict(receipt)
    body.pop("receipt_sha256", None)
    receipt["receipt_sha256"] = _SHA256(canonical_json(body)).hexdigest()
    return receipt


def validate_quimb_cotengra_capability_receipt(
    receipt: object,
    *,
    expected_binding: CapabilityBinding,
    expected_receipt_sha256: str | None = None,
    require_pass: bool = True,
) -> tuple[str, ...]:
    """Independently recheck a captured receipt; it never runs package APIs."""

    errors: list[str] = []
    if not isinstance(receipt, dict):
        return ("receipt_not_object",)
    expected_keys = {
        "schema", "capability_id", "binding", "binding_sha256", "source_before",
        "runtime_and_artifacts_before", "external_system", "kernel_membership",
        "promotion_allowed", "engine_readiness_claim", "cr_truth_claim", "release_allowed",
        "claim_ceiling", "environment_policy", "environment_policy_sha256", "status",
        "reason", "rows", "source_after", "runtime_and_artifacts_after", "receipt_sha256",
    }
    if set(receipt) != expected_keys:
        errors.append("receipt_fields_mismatch")
        return tuple(errors)
    if receipt.get("schema") != CAPABILITY_SCHEMA:
        errors.append("receipt_schema_mismatch")
    if receipt.get("capability_id") != CAPABILITY_ID:
        errors.append("receipt_capability_id_mismatch")
    try:
        binding = capability_binding_from_dict(receipt.get("binding"))
    except ExternalQuimbCotengraCapabilityError:
        errors.append("receipt_binding_invalid")
        binding = None
    expected_binding_dict = validate_capability_binding(expected_binding)
    if binding is None or binding.to_dict() != expected_binding_dict:
        errors.append("receipt_binding_mismatch")
    if receipt.get("binding_sha256") != _SHA256(canonical_json(expected_binding_dict)).hexdigest():
        errors.append("receipt_binding_digest_mismatch")
    body = dict(receipt)
    observed_root = body.pop("receipt_sha256")
    recomputed_root = _SHA256(canonical_json(body)).hexdigest()
    if observed_root != recomputed_root:
        errors.append("receipt_root_digest_mismatch")
    if expected_receipt_sha256 is not None and observed_root != expected_receipt_sha256:
        errors.append("receipt_expected_digest_mismatch")
    for key, value in (
        ("external_system", True),
        ("kernel_membership", "EXTERNAL_NOT_CB_KERNEL"),
        ("promotion_allowed", False),
        ("engine_readiness_claim", False),
        ("cr_truth_claim", False),
        ("release_allowed", False),
        ("claim_ceiling", CLAIM_CEILING),
        ("environment_policy", ENVIRONMENT_POLICY),
        ("environment_policy_sha256", ENVIRONMENT_POLICY_SHA256),
    ):
        if receipt.get(key) != value:
            errors.append(f"receipt_{key}_mismatch")
    if require_pass and receipt.get("status") != "PASS":
        errors.append("receipt_not_pass")
    if receipt.get("status") == "PASS":
        if receipt.get("reason") != "exact_operation_controls_passed":
            errors.append("receipt_pass_reason_mismatch")
        cases = derive_challenge_cases(expected_binding.challenge_seed_hex)
        rows = receipt.get("rows")
        if not isinstance(rows, list) or len(rows) != len(PROFILE_IDS):
            errors.append("receipt_rows_mismatch")
        else:
            for profile_id, row in zip(PROFILE_IDS, rows, strict=True):
                if not isinstance(row, dict) or row.get("profile_id") != profile_id:
                    errors.append(f"receipt_{profile_id}_row_mismatch")
                    continue
                if row.get("status") != "PASS" or row.get("reason") != "exact_operation_controls_passed":
                    errors.append(f"receipt_{profile_id}_not_pass")
                if row.get("challenge_case") != cases[profile_id]:
                    errors.append(f"receipt_{profile_id}_challenge_mismatch")
                if row.get("challenge_case_sha256") != _SHA256(canonical_json(cases[profile_id])).hexdigest():
                    errors.append(f"receipt_{profile_id}_challenge_digest_mismatch")
                if row.get("exact_api") != list(EXACT_APIS[profile_id]):
                    errors.append(f"receipt_{profile_id}_exact_api_mismatch")
                controls = row.get("controls")
                if not isinstance(controls, dict) or set(controls) != {"positive", "targeted_negative", "boundary", "operation_severance"} or not all(controls.values()):
                    errors.append(f"receipt_{profile_id}_controls_mismatch")
                if row.get("execution_binding") != expected_binding_dict:
                    errors.append(f"receipt_{profile_id}_binding_mismatch")
                if row.get("environment_policy_sha256") != ENVIRONMENT_POLICY_SHA256:
                    errors.append(f"receipt_{profile_id}_environment_policy_mismatch")
                if row.get("worker_source_sha256") != WORKER_SHA256 or row.get("worker_source_sha256_expected") != WORKER_SHA256:
                    errors.append(f"receipt_{profile_id}_worker_source_mismatch")
                environment = row.get("environment")
                if not isinstance(environment, dict) or set(environment) != {
                    "PATH", "HOME", "NUMBA_CACHE_DIR",
                    "MPLCONFIGDIR",
                    "PYTHONHASHSEED",
                    "PYTHONPATH",
                    "PYTHONHOME",
                }:
                    errors.append(f"receipt_{profile_id}_environment_mismatch")
                    continue
                payload_case = {
                    key: value
                    for key, value in cases[profile_id].items()
                    if key not in {"wrong_eigenvalues", "wrong_observed"}
                }
                expected_transport = {
                    "schema": WORKER_TRANSPORT_SCHEMA,
                    "profile_id": profile_id,
                    "case": payload_case,
                    "execution_binding": expected_binding_dict,
                    "environment_policy_sha256": ENVIRONMENT_POLICY_SHA256,
                }
                if row.get("input_sha256") != _SHA256(
                    canonical_json(expected_transport)
                ).hexdigest():
                    errors.append(f"receipt_{profile_id}_input_digest_mismatch")
                normal = row.get("normal_launch")
                witness = row.get("worker_witness")
                if not isinstance(normal, dict) or normal.get("status") != "PASS":
                    errors.append(f"receipt_{profile_id}_normal_launch_mismatch")
                elif normal.get("response") != witness:
                    errors.append(f"receipt_{profile_id}_normal_witness_mismatch")
                elif not isinstance(witness, dict):
                    errors.append(f"receipt_{profile_id}_witness_not_object")
                else:
                    evaluation = _evaluate_witness(
                        profile_id=profile_id,
                        case=cases[profile_id],
                        witness=witness,
                        binding=expected_binding_dict,
                        environment=environment,
                        controller_pid=-1,
                    )
                    expected_controls = dict(evaluation["controls"])
                    expected_controls["operation_severance"] = True
                    if evaluation["errors"]:
                        errors.append(f"receipt_{profile_id}_witness_evaluation_failed")
                    if row.get("expected") != evaluation["expected"]:
                        errors.append(f"receipt_{profile_id}_expected_mismatch")
                    if row.get("controls") != expected_controls:
                        errors.append(f"receipt_{profile_id}_control_replay_mismatch")
                    witness_sha = _SHA256(canonical_json(witness)).hexdigest()
                    if row.get("worker_witness_sha256") != witness_sha or normal.get("response_sha256") != witness_sha:
                        errors.append(f"receipt_{profile_id}_witness_digest_mismatch")
                poison_targets = (
                    ("quimb.eigvalsh", "quimb.trace")
                    if profile_id == QUIMB_PROFILE
                    else ("cotengra.HyperOptimizer.search",)
                )
                severance = row.get("operation_severance")
                if not isinstance(severance, list) or len(severance) != len(poison_targets):
                    errors.append(f"receipt_{profile_id}_severance_rows_mismatch")
                else:
                    for target, poison_row in zip(poison_targets, severance, strict=True):
                        if not isinstance(poison_row, dict) or poison_row.get("poisoned_api") != target:
                            errors.append(f"receipt_{profile_id}_severance_target_mismatch")
                            continue
                        poison_environment = poison_row.get("environment")
                        launch = poison_row.get("launch")
                        if not isinstance(poison_environment, dict) or not isinstance(launch, dict):
                            errors.append(f"receipt_{profile_id}_severance_shape_mismatch")
                            continue
                        accepted, detail = _validate_poison_witness(
                            profile_id=profile_id,
                            poison=target,
                            response=launch.get("response") if isinstance(launch.get("response"), dict) else {},
                            binding=expected_binding_dict,
                            environment=poison_environment,
                            controller_pid=-1,
                        )
                        if not accepted or poison_row.get("accepted") is not True or poison_row.get("error") is not None:
                            errors.append(
                                f"receipt_{profile_id}_severance_replay_failed:{detail or 'unaccepted'}"
                            )
    broker = QuimbCotengraCapabilityBroker()
    current_source = broker._source_state()
    current_pin_state = _runtime_and_artifact_state(broker.worker_path)
    if receipt.get("source_before") != current_source or receipt.get("source_after") != current_source:
        errors.append("receipt_source_replay_mismatch")
    if receipt.get("runtime_and_artifacts_before") != current_pin_state or receipt.get("runtime_and_artifacts_after") != current_pin_state:
        errors.append("receipt_runtime_pin_replay_mismatch")
    return tuple(errors)
