"""One bounded, independently replayable PyKoopman capability for ConstraintBox.

The capability is deliberately outside the ConstraintBox kernel.  CPython owns
the request binding, source/runtime pins, challenge, child command, result
recomputation, and Mini-Lev transition.  The child can only execute one fixed
``Identity() + EDMD()`` trajectory operation; neither an LLM nor a request can
select an executable, observable, regressor, transition, or release outcome.
"""

from __future__ import annotations

import hashlib
import importlib.metadata
import inspect
import math
import os
import re
import secrets
import subprocess
import sys
import time
import warnings
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


CAPABILITY_ID = "pykoopman-identity-edmd-v1"
CAPABILITY_SCHEMA = "constraintbox.external-pykoopman-capability-receipt.v1"
BINDING_SCHEMA = "constraintbox.external-pykoopman-capability-binding.v1"
ROW_SCHEMA = "constraintbox.external-pykoopman-capability-row.v1"
WORKER_TRANSPORT_SCHEMA = "constraintbox.external-pykoopman-worker-request.v1"
WORKER_WITNESS_SCHEMA = "constraintbox.external-pykoopman-worker-witness.v1"
WORKER_FAILURE_SCHEMA = "constraintbox.external-pykoopman-worker-failure.v1"
FLOW_RESULT_SCHEMA = "constraintbox.external-pykoopman-capability-flow-result.v1"
STEP_ID = "pykoopman-identity-edmd-tool"
EXACT_APIS = (
    "pykoopman.Koopman.fit",
    "pykoopman.Koopman.predict",
    "pykoopman.regression.EDMD.fit",
)
WORKER_ARGUMENT = "--constraintbox-internal-pykoopman-worker-v1"
WORKER_TIMEOUT_SECONDS = 75.0
CONTROL_TOLERANCE = 1e-8
FLOW_RECEIPT_NAME = "pykoopman_identity_edmd_flow_receipt.json"
FLOW_LEDGER_NAME = "pykoopman_identity_edmd_flow_events.jsonl"
CAPABILITY_RECEIPT_NAME = "pykoopman_identity_edmd_capability_receipt.json"
CAPABILITY_CLAIM_CEILING = (
    "one fresh controller-challenged PyKoopman Koopman.fit and Koopman.predict "
    "operation with the controller-fixed Identity observable and EDMD regressor "
    "on a bounded scalar contraction trajectory, including positive, wrong-value, "
    "and zero-boundary controls under the pinned local runtime; not PyKoopman "
    "readiness, not sim-stack readiness, not CR truth, not scientific proof, "
    "not hostile-code containment, not release, and not canonical promotion"
)

_SHA256 = hashlib.sha256
_SAFE_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}")
_LOWER_SHA256 = re.compile(r"[0-9a-f]{64}")
_EMPTY_SHA256 = _SHA256(b"").hexdigest()
_CACHE_ROOT_NAME = ".constraintbox-pykoopman-cache"


class ExternalPyKoopmanCapabilityError(RuntimeError):
    """The one fixed external PyKoopman capability could not be verified."""


class ExternalPyKoopmanCapabilityFlowError(ValueError):
    """The two-node PyKoopman Mini-Lev flow could not run or verify."""


class _WorkerUnavailable(RuntimeError):
    """The fixed child cannot honestly exercise its exact API surface."""


@dataclass(frozen=True)
class CapabilityBinding:
    """Controller-owned identity material for one PyKoopman invocation."""

    capability_id: str
    run_id: str
    flow_policy_sha256: str
    request_sha256: str
    step_id: str
    challenge_seed_hex: str
    cache_root: str

    def to_dict(self) -> dict[str, str]:
        return {
            "schema": BINDING_SCHEMA,
            "capability_id": self.capability_id,
            "run_id": self.run_id,
            "flow_policy_sha256": self.flow_policy_sha256,
            "request_sha256": self.request_sha256,
            "step_id": self.step_id,
            "challenge_seed_hex": self.challenge_seed_hex,
            "cache_root": self.cache_root,
        }


@dataclass(frozen=True)
class RuntimePin:
    invoked_path: str
    resolved_path: str
    sha256: str

    def to_dict(self) -> dict[str, str]:
        return {
            "invoked_path": self.invoked_path,
            "resolved_path": self.resolved_path,
            "sha256": self.sha256,
        }


@dataclass(frozen=True)
class ArtifactPin:
    label: str
    path: str
    size_bytes: int
    sha256: str


# The alias is controller-selected.  It is intentionally not replaced by the
# interpreter that happens to import this module in a parent process.
RUNTIME_PIN = RuntimePin(
    invoked_path="/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3",
    resolved_path=(
        "/opt/homebrew/Cellar/python@3.13/3.13.6/Frameworks/"
        "Python.framework/Versions/3.13/bin/python3.13"
    ),
    sha256="0d1fc12cf4887074b3eb257241f152cb85ca5a135879120b7e8e3b9aa57d5094",
)

PYKOOPMAN_ARTIFACT_PINS = (
    ArtifactPin(
        "pykoopman/__init__.py",
        (
            "/Users/joshuaeisenhart/.local/share/codex-ratchet/envs/main/"
            "lib/python3.13/site-packages/pykoopman/__init__.py"
        ),
        450,
        "b65433d69f7bcf28ee38db700d9d48cf8f4e9e8f6d809349838ee7d13aaf450f",
    ),
    ArtifactPin(
        "pykoopman/koopman.py",
        (
            "/Users/joshuaeisenhart/.local/share/codex-ratchet/envs/main/"
            "lib/python3.13/site-packages/pykoopman/koopman.py"
        ),
        22_176,
        "d0efd07ed8f43e859f45e4511219dc3887e6da77a503464bad5dc1a55226cf85",
    ),
    ArtifactPin(
        "pykoopman/observables/_identity.py",
        (
            "/Users/joshuaeisenhart/.local/share/codex-ratchet/envs/main/"
            "lib/python3.13/site-packages/pykoopman/observables/_identity.py"
        ),
        2_880,
        "ac7b66024d9516b84e6f78b05c38449e156f2f82e8ccc7dd3af3702cd7256095",
    ),
    ArtifactPin(
        "pykoopman/regression/_edmd.py",
        (
            "/Users/joshuaeisenhart/.local/share/codex-ratchet/envs/main/"
            "lib/python3.13/site-packages/pykoopman/regression/_edmd.py"
        ),
        7_917,
        "99dec355e43439f65558b78c196fcc08a41d585d6c02eb5e4eadf5ccc441f4f6",
    ),
    ArtifactPin(
        "pykoopman-1.2.1.dist-info/RECORD",
        (
            "/Users/joshuaeisenhart/.local/share/codex-ratchet/envs/main/"
            "lib/python3.13/site-packages/pykoopman-1.2.1.dist-info/RECORD"
        ),
        5_895,
        "2ec2f04dbfb94beba6b2ca52fdf0b206e07948e306f37875a179aaf60bbceb73",
    ),
)
PYKOOPMAN_VERSION = "1.2.1"
NUMPY_VERSION = "2.3.4"
_OBSERVABLE_SPEC = "Identity()"
_REGRESSOR_SPEC = "EDMD(svd_rank=1.0,tlsq_rank=0)"


def _sha256_file(path: Path) -> str:
    return _SHA256(path.read_bytes()).hexdigest()


def _valid_sha256(value: object) -> bool:
    return isinstance(value, str) and _LOWER_SHA256.fullmatch(value) is not None


def _finite_number(value: object, path: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ExternalPyKoopmanCapabilityError(f"{path} must be a finite number")
    number = float(value)
    if not math.isfinite(number):
        raise ExternalPyKoopmanCapabilityError(f"{path} must be finite")
    return number


def _number_list(value: object, path: str, length: int) -> list[float]:
    if not isinstance(value, list) or len(value) != length:
        raise ExternalPyKoopmanCapabilityError(f"{path} must be a list of length {length}")
    return [_finite_number(item, f"{path}[{index}]") for index, item in enumerate(value)]


def _cache_root_from_text(value: object) -> Path:
    """Accept only the controller convention for a per-run private cache root."""

    if not isinstance(value, str):
        raise ExternalPyKoopmanCapabilityError("capability binding cache root is invalid")
    path = Path(value)
    if not path.is_absolute() or path.name != _CACHE_ROOT_NAME:
        raise ExternalPyKoopmanCapabilityError("capability binding cache root is invalid")
    resolved = path.resolve(strict=False)
    if str(path) != str(resolved):
        raise ExternalPyKoopmanCapabilityError("capability binding cache root is not normalized")
    return path


def validate_capability_binding(binding: CapabilityBinding) -> dict[str, str]:
    """Reject binding substitution before a worker can be launched."""

    if type(binding) is not CapabilityBinding:
        raise ExternalPyKoopmanCapabilityError(
            "capability binding must be one frozen CapabilityBinding"
        )
    if binding.capability_id != CAPABILITY_ID:
        raise ExternalPyKoopmanCapabilityError("capability binding id mismatch")
    if binding.step_id != STEP_ID:
        raise ExternalPyKoopmanCapabilityError("capability binding step mismatch")
    for key, value in (
        ("run_id", binding.run_id),
        ("capability_id", binding.capability_id),
        ("step_id", binding.step_id),
    ):
        if not isinstance(value, str) or _SAFE_ID.fullmatch(value) is None:
            raise ExternalPyKoopmanCapabilityError(
                f"capability binding {key} is invalid"
            )
    for key, value in (
        ("flow_policy_sha256", binding.flow_policy_sha256),
        ("request_sha256", binding.request_sha256),
        ("challenge_seed_hex", binding.challenge_seed_hex),
    ):
        if not _valid_sha256(value):
            raise ExternalPyKoopmanCapabilityError(
                f"capability binding {key} is invalid"
            )
    _cache_root_from_text(binding.cache_root)
    return binding.to_dict()


def capability_binding_from_dict(value: object) -> CapabilityBinding:
    expected_keys = {
        "schema",
        "capability_id",
        "run_id",
        "flow_policy_sha256",
        "request_sha256",
        "step_id",
        "challenge_seed_hex",
        "cache_root",
    }
    if not isinstance(value, dict) or set(value) != expected_keys:
        raise ExternalPyKoopmanCapabilityError("capability binding keys mismatch")
    if value.get("schema") != BINDING_SCHEMA:
        raise ExternalPyKoopmanCapabilityError("capability binding schema mismatch")
    try:
        binding = CapabilityBinding(
            capability_id=value["capability_id"],
            run_id=value["run_id"],
            flow_policy_sha256=value["flow_policy_sha256"],
            request_sha256=value["request_sha256"],
            step_id=value["step_id"],
            challenge_seed_hex=value["challenge_seed_hex"],
            cache_root=value["cache_root"],
        )
    except (KeyError, TypeError) as exc:
        raise ExternalPyKoopmanCapabilityError("capability binding is malformed") from exc
    validate_capability_binding(binding)
    return binding


def _challenge_unit(seed: bytes, index: int) -> float:
    digest = _SHA256(seed + index.to_bytes(2, "big")).digest()
    return int.from_bytes(digest[:8], "big") / float((1 << 64) - 1)


def derive_pykoopman_challenge_case(challenge_seed_hex: str) -> dict[str, Any]:
    """Derive one nondegenerate scalar EDMD trajectory from a controller seed."""

    if not _valid_sha256(challenge_seed_hex):
        raise ExternalPyKoopmanCapabilityError(
            "challenge seed must be 32 lowercase hex bytes"
        )
    seed = bytes.fromhex(challenge_seed_hex)
    rate = round(0.35 + 0.45 * _challenge_unit(seed, 0), 12)
    initial_state = round(0.90 + 0.50 * _challenge_unit(seed, 1), 12)
    probe_state = round(0.20 + 0.70 * _challenge_unit(seed, 2), 12)
    wrong_rate = round(rate + 0.17 if rate < 0.65 else rate - 0.17, 12)
    train_states = [round(initial_state * rate**index, 12) for index in range(7)]
    return {
        "rate": rate,
        "initial_state": initial_state,
        "train_states": train_states,
        "probe_state": probe_state,
        "boundary_state": 0.0,
        "wrong_operator": [[wrong_rate]],
    }


def _expected_from_case(case: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(case, dict) or set(case) != {
        "rate",
        "initial_state",
        "train_states",
        "probe_state",
        "boundary_state",
        "wrong_operator",
    }:
        raise ExternalPyKoopmanCapabilityError("challenge case keys mismatch")
    rate = _finite_number(case["rate"], "$.rate")
    initial_state = _finite_number(case["initial_state"], "$.initial_state")
    train_states = _number_list(case["train_states"], "$.train_states", 7)
    probe_state = _finite_number(case["probe_state"], "$.probe_state")
    boundary_state = _finite_number(case["boundary_state"], "$.boundary_state")
    wrong_operator = case["wrong_operator"]
    if (
        not isinstance(wrong_operator, list)
        or len(wrong_operator) != 1
        or not isinstance(wrong_operator[0], list)
        or len(wrong_operator[0]) != 1
    ):
        raise ExternalPyKoopmanCapabilityError("$.wrong_operator must be 1x1")
    wrong_rate = _finite_number(wrong_operator[0][0], "$.wrong_operator[0][0]")
    if not 0.35 <= rate <= 0.80:
        raise ExternalPyKoopmanCapabilityError("$.rate outside controller range")
    if not 0.90 <= initial_state <= 1.40:
        raise ExternalPyKoopmanCapabilityError("$.initial_state outside controller range")
    expected_train = [round(initial_state * rate**index, 12) for index in range(7)]
    if train_states != expected_train:
        raise ExternalPyKoopmanCapabilityError("$.train_states does not match seed case")
    if abs(wrong_rate - rate) <= CONTROL_TOLERANCE:
        raise ExternalPyKoopmanCapabilityError("wrong operator is not distinct")
    return {
        "operator": [[rate]],
        "prediction": [[rate * probe_state]],
        "boundary_prediction": [[rate * boundary_state]],
        "wrong_operator": [[wrong_rate]],
    }


def _runtime_pin_dict() -> dict[str, str]:
    return RUNTIME_PIN.to_dict()


def _worker_cache_environment(cache_root: Path) -> dict[str, str]:
    """Derive the only permitted cache/config environment from one binding."""

    root = _cache_root_from_text(str(cache_root))
    return {
        "MPLCONFIGDIR": str(root / "matplotlib"),
        "XDG_CACHE_HOME": str(root / "xdg-cache"),
        "NUMBA_CACHE_DIR": str(root / "numba-cache"),
        "MPLBACKEND": "Agg",
    }


def _create_private_cache_root(run_root: Path) -> Path:
    """Create cache state only after the caller's run root was created fresh."""

    cache_root = (run_root / _CACHE_ROOT_NAME).resolve(strict=False)
    try:
        cache_root.mkdir(mode=0o700, exist_ok=False)
        os.chmod(cache_root, 0o700)
        for value in _worker_cache_environment(cache_root).values():
            if value == "Agg":
                continue
            directory = Path(value)
            directory.mkdir(mode=0o700, exist_ok=False)
            os.chmod(directory, 0o700)
    except OSError as exc:
        raise ExternalPyKoopmanCapabilityFlowError(
            f"controller-private cache directory unavailable: {type(exc).__name__}: {exc}"
        ) from exc
    if cache_root.is_symlink() or not cache_root.is_dir():
        raise ExternalPyKoopmanCapabilityFlowError(
            "controller-private cache root is not a directory"
        )
    return cache_root


def _validate_cache_environment(
    value: object,
    *,
    cache_root: Path,
    require_exists: bool,
) -> dict[str, str]:
    expected = _worker_cache_environment(cache_root)
    if value != expected:
        raise ExternalPyKoopmanCapabilityError("worker cache environment mismatch")
    if require_exists:
        for key, path_text in expected.items():
            if key != "MPLBACKEND" and not Path(path_text).is_dir():
                raise ExternalPyKoopmanCapabilityError(
                    f"worker cache directory missing: {key}"
                )
    return expected


def _inspect_pykoopman_artifacts() -> dict[str, Any]:
    """Inspect exact runtime/source pins without importing PyKoopman here."""

    status = "PASS"
    reason = "pykoopman_runtime_and_sources_match_controller_pins"
    runtime: dict[str, Any] = {
        "invoked_path": RUNTIME_PIN.invoked_path,
        "expected_resolved_path": RUNTIME_PIN.resolved_path,
        "expected_sha256": RUNTIME_PIN.sha256,
    }
    try:
        resolved = Path(RUNTIME_PIN.invoked_path).resolve(strict=True)
        runtime_digest = _sha256_file(resolved)
    except OSError as exc:
        runtime.update({"observed": False, "error": f"{type(exc).__name__}: {exc}"})
        status = "PARKED"
        reason = "canonical_runtime_unavailable"
    else:
        runtime.update(
            {
                "observed": True,
                "observed_resolved_path": str(resolved),
                "observed_sha256": runtime_digest,
                "matches": (
                    str(resolved) == RUNTIME_PIN.resolved_path
                    and runtime_digest == RUNTIME_PIN.sha256
                ),
            }
        )
        if not runtime["matches"]:
            status = "FAIL"
            reason = "canonical_runtime_pin_mismatch"

    artifacts: list[dict[str, Any]] = []
    for pin in PYKOOPMAN_ARTIFACT_PINS:
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
            if status != "FAIL":
                status = "PARKED"
                reason = "pykoopman_source_unavailable"
        else:
            row.update(
                {
                    "observed": True,
                    "size_bytes": metadata.st_size,
                    "sha256": digest,
                    "matches": (
                        metadata.st_size == pin.size_bytes and digest == pin.sha256
                    ),
                }
            )
            if not row["matches"]:
                status = "FAIL"
                reason = "pykoopman_source_pin_mismatch"
        artifacts.append(row)
    return {"status": status, "reason": reason, "runtime": runtime, "artifacts": artifacts}


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
    except ExternalPyKoopmanCapabilityError as exc:
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


def evaluate_pykoopman_identity_edmd_output(
    challenge_case: dict[str, Any], observed: dict[str, Any]
) -> dict[str, Any]:
    """Controller-side numeric recomputation of the fixed EDMD controls."""

    expected = _expected_from_case(challenge_case)
    if not isinstance(observed, dict) or set(observed) != {
        "operator",
        "prediction",
        "boundary_prediction",
    }:
        return {
            "controls": {"positive": False, "targeted_negative": False, "boundary": False},
            "expected": expected,
            "comparisons": {},
            "errors": ["observed_keys_mismatch"],
        }
    operator = _comparison(observed["operator"], expected["operator"])
    prediction = _comparison(observed["prediction"], expected["prediction"])
    boundary = _comparison(
        observed["boundary_prediction"], expected["boundary_prediction"]
    )
    wrong = _comparison(observed["operator"], expected["wrong_operator"])
    wrong_distinct = _comparison(expected["operator"], expected["wrong_operator"])
    comparisons = (operator, prediction, boundary, wrong, wrong_distinct)
    errors = [comparison["error"] for comparison in comparisons if "error" in comparison]
    controls = {
        "positive": bool(operator.get("pass") and prediction.get("pass")),
        "targeted_negative": bool(
            not wrong.get("pass") and not wrong_distinct.get("pass")
        ),
        "boundary": bool(boundary.get("pass")),
    }
    return {
        "controls": controls,
        "expected": expected,
        "comparisons": {
            "operator": operator,
            "prediction": prediction,
            "boundary": boundary,
            "targeted_negative_wrong_operator_match": wrong,
            "targeted_negative_expected_operator_distinct": wrong_distinct,
        },
        "errors": errors,
    }


def _source_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _worker_command() -> list[str]:
    """Use isolated mode while adding only the controller-owned source root."""

    bootstrap = (
        "import sys; "
        f"sys.path.insert(0, {str(_source_root())!r}); "
        "from constraintbox.external_pykoopman_capability import _worker_main; "
        "raise SystemExit(_worker_main())"
    )
    return [RUNTIME_PIN.invoked_path, "-I", "-B", "-c", bootstrap, WORKER_ARGUMENT]


def _worker_environment(cache_environment: dict[str, str]) -> dict[str, str]:
    environment = {
        key: value
        for key, value in os.environ.items()
        if not key.startswith("PYTHON") and key not in cache_environment
    }
    environment.update(cache_environment)
    return environment


def _worker_transport(
    *,
    binding: dict[str, str],
    challenge_case: dict[str, Any],
    capability_source_sha256: str,
) -> dict[str, Any]:
    parsed_binding = capability_binding_from_dict(binding)
    cache_environment = _worker_cache_environment(
        _cache_root_from_text(parsed_binding.cache_root)
    )
    return {
        "schema": WORKER_TRANSPORT_SCHEMA,
        "capability_id": CAPABILITY_ID,
        "exact_api": list(EXACT_APIS),
        "execution_binding": binding,
        "challenge_case": challenge_case,
        "capability_source_path": str(Path(__file__).resolve()),
        "capability_source_sha256": capability_source_sha256,
        "runtime_pin": _runtime_pin_dict(),
        "cache_environment": cache_environment,
    }


def _worker_witness(transport: dict[str, Any]) -> dict[str, Any]:
    """Run the real fixed PyKoopman operation in the isolated child process."""

    expected_keys = {
        "schema",
        "capability_id",
        "exact_api",
        "execution_binding",
        "challenge_case",
        "capability_source_path",
        "capability_source_sha256",
        "runtime_pin",
        "cache_environment",
    }
    if set(transport) != expected_keys:
        raise ExternalPyKoopmanCapabilityError("worker transport keys mismatch")
    if transport["schema"] != WORKER_TRANSPORT_SCHEMA:
        raise ExternalPyKoopmanCapabilityError("worker transport schema mismatch")
    if transport["capability_id"] != CAPABILITY_ID:
        raise ExternalPyKoopmanCapabilityError("worker transport id mismatch")
    if transport["exact_api"] != list(EXACT_APIS):
        raise ExternalPyKoopmanCapabilityError("worker transport API mismatch")
    binding = capability_binding_from_dict(transport["execution_binding"])
    binding_body = validate_capability_binding(binding)
    expected_case = derive_pykoopman_challenge_case(binding.challenge_seed_hex)
    if transport["challenge_case"] != expected_case:
        raise ExternalPyKoopmanCapabilityError("worker challenge does not match binding")
    source_path = Path(__file__).resolve()
    source_sha256 = _sha256_file(source_path)
    if (
        transport["capability_source_path"] != str(source_path)
        or transport["capability_source_sha256"] != source_sha256
    ):
        raise ExternalPyKoopmanCapabilityError("worker source binding mismatch")
    if transport["runtime_pin"] != _runtime_pin_dict():
        raise ExternalPyKoopmanCapabilityError("worker runtime pin mismatch")
    cache_environment = _validate_cache_environment(
        transport["cache_environment"],
        cache_root=_cache_root_from_text(binding.cache_root),
        require_exists=True,
    )
    if any(os.environ.get(key) != value for key, value in cache_environment.items()):
        raise ExternalPyKoopmanCapabilityError("worker process cache environment mismatch")
    pins = _inspect_pykoopman_artifacts()
    if pins["status"] != "PASS":
        raise _WorkerUnavailable(pins["reason"])

    with warnings.catch_warnings():
        warnings.filterwarnings(
            "ignore",
            message=r"pkg_resources is deprecated as an API.*",
            category=UserWarning,
        )
        try:
            import numpy as np
            import pykoopman
            from pykoopman import Koopman
            from pykoopman.observables import Identity
            from pykoopman.regression import EDMD
        except (ImportError, ModuleNotFoundError) as exc:
            raise _WorkerUnavailable(f"pykoopman import failed: {exc}") from exc

    expected_paths = tuple(Path(pin.path) for pin in PYKOOPMAN_ARTIFACT_PINS)
    imported_paths = (
        Path(pykoopman.__file__).resolve(),
        Path(inspect.getsourcefile(Koopman)).resolve(),
        Path(inspect.getsourcefile(Identity)).resolve(),
        Path(inspect.getsourcefile(EDMD)).resolve(),
    )
    if imported_paths != expected_paths[:4]:
        raise ExternalPyKoopmanCapabilityError("imported PyKoopman source mismatch")
    for owner, name, qualified_name in (
        (Koopman, "fit", "pykoopman.Koopman.fit"),
        (Koopman, "predict", "pykoopman.Koopman.predict"),
        (EDMD, "fit", "pykoopman.regression.EDMD.fit"),
        (Identity, "transform", "pykoopman.observables.Identity.transform"),
    ):
        if not callable(getattr(owner, name, None)):
            raise _WorkerUnavailable(f"{qualified_name} unavailable")

    train_states = np.asarray(expected_case["train_states"], dtype=np.float64).reshape(-1, 1)
    model = Koopman(observables=Identity(), regressor=EDMD())
    # The process must call the real high-level API.  The controller's scalar
    # arithmetic only evaluates the returned values; it does not replace EDMD.
    model.fit(train_states)
    operator = np.asarray(model.A, dtype=np.float64)
    probe_state = np.asarray([[expected_case["probe_state"]]], dtype=np.float64)
    boundary_state = np.asarray(
        [[expected_case["boundary_state"]]], dtype=np.float64
    )
    prediction = np.asarray(model.predict(probe_state), dtype=np.float64)
    boundary_prediction = np.asarray(model.predict(boundary_state), dtype=np.float64)
    if operator.shape != (1, 1):
        raise ExternalPyKoopmanCapabilityError("unexpected EDMD operator shape")
    if prediction.shape != (1, 1) or boundary_prediction.shape != (1, 1):
        raise ExternalPyKoopmanCapabilityError("unexpected Koopman prediction shape")
    runtime = {
        "pykoopman_version": importlib.metadata.version("pykoopman"),
        "numpy_version": importlib.metadata.version("numpy"),
        "python_executable_resolved_path": str(Path(sys.executable).resolve()),
        "observable": _OBSERVABLE_SPEC,
        "regressor": _REGRESSOR_SPEC,
        "cache_environment": cache_environment,
    }
    return {
        "schema": WORKER_WITNESS_SCHEMA,
        "capability_id": CAPABILITY_ID,
        "exact_api": list(EXACT_APIS),
        "execution_binding": binding_body,
        "capability_source_sha256": source_sha256,
        "runtime_pin": _runtime_pin_dict(),
        "observed": {
            "operator": [[float(operator[0, 0])]],
            "prediction": [[float(prediction[0, 0])]],
            "boundary_prediction": [[float(boundary_prediction[0, 0])]],
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
    """Launch the one fixed child and recompute its exact bounded result."""

    transport = _worker_transport(
        binding=binding,
        challenge_case=challenge_case,
        capability_source_sha256=capability_source_sha256,
    )
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
            env=_worker_environment(transport["cache_environment"]),
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
        "cache_environment": transport["cache_environment"],
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
        "controls": {"positive": False, "targeted_negative": False, "boundary": False},
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
    if process is None or process.returncode != 0:
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
    expected_runtime = {
        "pykoopman_version": PYKOOPMAN_VERSION,
        "numpy_version": NUMPY_VERSION,
        "python_executable_resolved_path": RUNTIME_PIN.resolved_path,
        "observable": _OBSERVABLE_SPEC,
        "regressor": _REGRESSOR_SPEC,
        "cache_environment": transport["cache_environment"],
    }
    if runtime != expected_runtime or not isinstance(response["observed"], dict):
        row["reason"] = "worker_runtime_or_observed_mismatch"
        return row
    evaluation = evaluate_pykoopman_identity_edmd_output(
        challenge_case, response["observed"]
    )
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
        "pykoopman_sources_before": sources_before,
        "pykoopman_sources_after": sources_after,
        "row": row,
        "release_allowed": False,
        "engine_readiness_claim": False,
        "cr_truth_claim": False,
        "promotion_allowed": False,
        "claim_ceiling": CAPABILITY_CLAIM_CEILING,
    }


class PyKoopmanIdentityEDMDCapabilityBroker:
    """Controller-owned broker for the one separate PyKoopman child process."""

    def __init__(self) -> None:
        self.source_path = Path(__file__).resolve()

    def run(self, binding: CapabilityBinding) -> dict[str, Any]:
        binding_body = validate_capability_binding(binding)
        capability_source_sha256 = _sha256_file(self.source_path)
        challenge_case = derive_pykoopman_challenge_case(binding.challenge_seed_hex)
        sources_before = _inspect_pykoopman_artifacts()
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
        sources_after = _inspect_pykoopman_artifacts()
        if sources_after != sources_before:
            status = "FAIL"
            reason = "pykoopman_sources_changed_during_operation"
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
        receipt = {**body, "receipt_sha256": _SHA256(canonical_json(body)).hexdigest()}
        errors = validate_pykoopman_capability_receipt(
            receipt,
            expected_binding=binding,
            expected_receipt_sha256=receipt["receipt_sha256"],
            require_pass=status == "PASS",
        )
        if errors:
            raise ExternalPyKoopmanCapabilityError(
                "capability self-verification failed: " + "; ".join(errors)
            )
        return receipt


def validate_pykoopman_capability_receipt(
    receipt: dict[str, Any],
    *,
    expected_binding: CapabilityBinding,
    expected_receipt_sha256: str,
    require_pass: bool = True,
) -> tuple[str, ...]:
    """Revalidate a receipt against current source/runtime pins and controls."""

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
        "pykoopman_sources_before",
        "pykoopman_sources_after",
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
    except ExternalPyKoopmanCapabilityError as exc:
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
        expected_case = derive_pykoopman_challenge_case(expected_binding.challenge_seed_hex)
    except ExternalPyKoopmanCapabilityError as exc:
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
        current_pins = _inspect_pykoopman_artifacts()
    except OSError as exc:
        error("$.current_sources", f"unavailable={type(exc).__name__}")
        return tuple(errors)
    expect(body["capability_source_path"], str(Path(__file__).resolve()), "$.capability_source_path")
    expect(body["capability_source_sha256"], current_source, "$.capability_source_sha256")
    expect(body["runtime_pin"], _runtime_pin_dict(), "$.runtime_pin")
    expect(
        body["pykoopman_sources_before"],
        body["pykoopman_sources_after"],
        "$.pykoopman_sources_stability",
    )
    expect(body["pykoopman_sources_after"], current_pins, "$.pykoopman_sources_current")

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
        "cache_environment",
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
    try:
        cache_environment = _validate_cache_environment(
            row["cache_environment"],
            cache_root=_cache_root_from_text(expected_binding.cache_root),
            require_exists=False,
        )
    except ExternalPyKoopmanCapabilityError as exc:
        error("$.row.cache_environment", str(exc))
        return tuple(errors)
    expected_transport = _worker_transport(
        binding=expected_binding_body,
        challenge_case=expected_case,
        capability_source_sha256=current_source,
    )
    expect(cache_environment, expected_transport["cache_environment"], "$.row.cache_environment")
    expect(
        row["input_sha256"],
        _SHA256(canonical_json(expected_transport)).hexdigest(),
        "$.row.input_sha256",
    )
    expect(row["controller_source_sha256"], current_source, "$.row.controller_source_sha256")
    expect(row["worker_source_sha256"], current_source, "$.row.worker_source_sha256")
    expect(
        row["worker_source_sha256_expected"],
        current_source,
        "$.row.worker_source_sha256_expected",
    )
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
    expected_runtime = {
        "pykoopman_version": PYKOOPMAN_VERSION,
        "numpy_version": NUMPY_VERSION,
        "python_executable_resolved_path": RUNTIME_PIN.resolved_path,
        "observable": _OBSERVABLE_SPEC,
        "regressor": _REGRESSOR_SPEC,
        "cache_environment": expected_transport["cache_environment"],
    }
    expect(row["runtime"], expected_runtime, "$.row.runtime")
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
    # PyKoopman currently emits a third-party deprecation warning in some
    # environments.  stderr is receipt-bound but not made a false failure when
    # the child exits cleanly and stdout remains strict protocol JSON.
    evaluation = evaluate_pykoopman_identity_edmd_output(expected_case, row["observed"])
    expect(row["controller_evaluation"], evaluation, "$.row.controller_evaluation")
    expect(row["controls"], evaluation["controls"], "$.row.controls")
    if (
        set(row["controls"]) != {"positive", "targeted_negative", "boundary"}
        or not all(value is True for value in row["controls"].values())
        or evaluation["errors"]
    ):
        error("$.row.controls", "not_all_required_controls_true")
    return tuple(errors)


_PINNED_CAPABILITY_BROKER = PyKoopmanIdentityEDMDCapabilityBroker
_PINNED_BINDING_PARSER = capability_binding_from_dict
_PINNED_RECEIPT_VALIDATOR = validate_pykoopman_capability_receipt


def _verify_live_dependencies() -> None:
    if (
        PyKoopmanIdentityEDMDCapabilityBroker is not _PINNED_CAPABILITY_BROKER
        or capability_binding_from_dict is not _PINNED_BINDING_PARSER
        or validate_pykoopman_capability_receipt is not _PINNED_RECEIPT_VALIDATOR
    ):
        raise ExternalPyKoopmanCapabilityFlowError(
            "capability handler dependency binding drift"
        )


def _binding_from_context(
    context: dict[str, Any],
    *,
    expected_node_id: str,
    expected_hook_id: str,
    expected_hook_kind: HookKind,
) -> CapabilityBinding:
    _verify_live_dependencies()
    metadata = context.get(CONTROLLER_METADATA_KEY)
    if not isinstance(metadata, dict) or set(metadata) != {
        "schema",
        "run_id",
        "policy_sha256",
        "node_id",
        "hook_id",
        "hook_kind",
    }:
        raise ExternalPyKoopmanCapabilityFlowError(
            "capability flow controller metadata is missing"
        )
    if metadata != {
        "schema": CONTROLLER_METADATA_SCHEMA,
        "run_id": metadata.get("run_id"),
        "policy_sha256": metadata.get("policy_sha256"),
        "node_id": expected_node_id,
        "hook_id": expected_hook_id,
        "hook_kind": expected_hook_kind.value,
    }:
        raise ExternalPyKoopmanCapabilityFlowError(
            "capability flow controller metadata mismatch"
        )
    text = context.get("capability_binding_json")
    if not isinstance(text, str):
        raise ExternalPyKoopmanCapabilityFlowError(
            "capability flow binding must be canonical JSON text"
        )
    try:
        binding = capability_binding_from_dict(parse_json_object(text.encode("utf-8")))
    except (IntakeError, ExternalPyKoopmanCapabilityError) as exc:
        raise ExternalPyKoopmanCapabilityFlowError(
            f"capability flow binding is invalid: {exc}"
        ) from exc
    if (
        binding.run_id != metadata["run_id"]
        or binding.flow_policy_sha256 != metadata["policy_sha256"]
    ):
        raise ExternalPyKoopmanCapabilityFlowError(
            "capability binding differs from controller runtime metadata"
        )
    return binding


def _pykoopman_capability_tool(context: dict[str, Any]) -> HookResult:
    binding = _binding_from_context(
        context,
        expected_node_id="pykoopman-capability-tool",
        expected_hook_id="pykoopman-identity-edmd-capability-tool",
        expected_hook_kind=HookKind.TOOL,
    )
    receipt = PyKoopmanIdentityEDMDCapabilityBroker().run(binding)
    receipt_bytes = canonical_json(receipt)
    return HookResult(
        HookSignal.OBSERVED,
        {
            "capability_state": receipt["status"],
            "capability_receipt_sha256": receipt["receipt_sha256"],
        },
        {
            "capability_state": receipt["status"],
            "capability_receipt_sha256": receipt["receipt_sha256"],
            "capability_receipt_json": receipt_bytes.decode("utf-8"),
        },
    )


def _pykoopman_capability_gate(context: dict[str, Any]) -> HookResult:
    binding = _binding_from_context(
        context,
        expected_node_id="pykoopman-capability-gate",
        expected_hook_id="pykoopman-identity-edmd-capability-gate",
        expected_hook_kind=HookKind.GATE,
    )
    receipt_text = context.get("capability_receipt_json")
    expected_sha256 = context.get("capability_receipt_sha256")
    state = context.get("capability_state")
    if not all(isinstance(value, str) for value in (receipt_text, expected_sha256, state)):
        raise ExternalPyKoopmanCapabilityFlowError(
            "capability gate context fields must be strings"
        )
    try:
        receipt = parse_json_object(receipt_text.encode("utf-8"))
    except IntakeError as exc:
        raise ExternalPyKoopmanCapabilityFlowError(
            f"capability receipt is not strict JSON: {exc}"
        ) from exc
    if receipt.get("status") != state:
        raise ExternalPyKoopmanCapabilityFlowError("capability state binding mismatch")
    errors = validate_pykoopman_capability_receipt(
        receipt,
        expected_binding=binding,
        expected_receipt_sha256=expected_sha256,
        require_pass=state == "PASS",
    )
    if errors:
        raise ExternalPyKoopmanCapabilityFlowError(
            "capability receipt verification failed: " + "; ".join(errors)
        )
    signal = {
        "PASS": HookSignal.PASS,
        "PARKED": HookSignal.PARKED,
        "FAIL": HookSignal.BLOCKED,
    }.get(state)
    if signal is None:
        raise ExternalPyKoopmanCapabilityFlowError(
            f"capability broker returned an unknown state: {state}"
        )
    return HookResult(
        signal,
        {"capability_state": state, "capability_receipt_sha256": expected_sha256},
    )


def _source_registration(
    *,
    hook_id: str,
    kind: HookKind,
    handler,
    allowed_signals: tuple[HookSignal, ...],
    allowed_update_keys: tuple[str, ...] = (),
) -> HookRegistration:
    source_path = Path(__file__).resolve()
    try:
        source_sha256 = _sha256_file(source_path)
    except OSError as exc:
        raise ExternalPyKoopmanCapabilityFlowError(
            f"capability flow source unavailable: {exc}"
        ) from exc
    return HookRegistration(
        hook_id=hook_id,
        kind=kind,
        handler=handler,
        source_path=source_path,
        source_sha256=source_sha256,
        code_sha256=handler_code_sha256(handler),
        allowed_signals=allowed_signals,
        allowed_update_keys=allowed_update_keys,
        max_output_bytes=524_288,
    )


def _build_pykoopman_capability_flow(*, run_id: str, ledger_path: Path) -> MiniLevRuntime:
    tool = _source_registration(
        hook_id="pykoopman-identity-edmd-capability-tool",
        kind=HookKind.TOOL,
        handler=_pykoopman_capability_tool,
        allowed_signals=(HookSignal.OBSERVED,),
        allowed_update_keys=(
            "capability_state",
            "capability_receipt_sha256",
            "capability_receipt_json",
        ),
    )
    gate = _source_registration(
        hook_id="pykoopman-identity-edmd-capability-gate",
        kind=HookKind.GATE,
        handler=_pykoopman_capability_gate,
        allowed_signals=(HookSignal.PASS, HookSignal.BLOCKED, HookSignal.PARKED),
    )
    policy = FlowPolicy(
        flow_id="constraintbox.pykoopman-identity-edmd-capability-flow.v1",
        entry_node="pykoopman-capability-tool",
        nodes=(
            FlowNode("pykoopman-capability-tool", tool.hook_id),
            FlowNode("pykoopman-capability-gate", gate.hook_id),
        ),
        transitions=(
            FlowTransition(
                "pykoopman-capability-tool",
                HookSignal.OBSERVED,
                "pykoopman-capability-gate",
            ),
            FlowTransition("pykoopman-capability-tool", HookSignal.HOLD, "HOLD"),
            FlowTransition("pykoopman-capability-gate", HookSignal.PASS, "ELIGIBLE"),
            FlowTransition("pykoopman-capability-gate", HookSignal.BLOCKED, "BLOCKED"),
            FlowTransition("pykoopman-capability-gate", HookSignal.PARKED, "PARKED"),
            FlowTransition("pykoopman-capability-gate", HookSignal.HOLD, "HOLD"),
        ),
        terminal_nodes=("ELIGIBLE", "BLOCKED", "PARKED", "HOLD"),
        required_nodes=("pykoopman-capability-tool", "pykoopman-capability-gate"),
        max_steps=2,
        max_visits_per_node=1,
        max_retries=0,
        max_context_bytes=1_048_576,
        max_event_bytes=1_572_864,
        max_receipt_bytes=8_388_608,
        claim_ceiling=CAPABILITY_CLAIM_CEILING,
    )
    try:
        return MiniLevRuntime(policy, (tool, gate), run_id=run_id, ledger_path=ledger_path)
    except MiniLevError as exc:
        raise ExternalPyKoopmanCapabilityFlowError(
            f"capability flow construction failed: {exc}"
        ) from exc


def _persist_exclusive(path: Path, value: dict[str, Any]) -> None:
    try:
        with path.open("x", encoding="utf-8") as stream:
            stream.write(canonical_json(value).decode("utf-8"))
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
    except OSError as exc:
        raise ExternalPyKoopmanCapabilityFlowError(
            f"capability artifact persistence failed: {exc}"
        ) from exc


def run_pykoopman_capability_flow(*, request_id: str, run_root: Path) -> dict[str, Any]:
    """Run one fresh, controller-challenged fixed PyKoopman capability flow."""

    if not isinstance(request_id, str) or _SAFE_ID.fullmatch(request_id) is None:
        raise ExternalPyKoopmanCapabilityFlowError(
            "request_id must be one safe bounded identifier"
        )
    if not isinstance(run_root, Path) or not run_root.is_absolute():
        raise ExternalPyKoopmanCapabilityFlowError(
            "run_root must be one absolute pathlib.Path"
        )
    run_root = run_root.resolve(strict=False)
    try:
        run_root.mkdir(parents=True, exist_ok=False)
    except OSError as exc:
        raise ExternalPyKoopmanCapabilityFlowError(
            f"capability run directory must be new: {exc}"
        ) from exc
    cache_root = _create_private_cache_root(run_root)
    request_body = {
        "schema": "constraintbox.external-pykoopman-capability-request.v1",
        "capability_id": CAPABILITY_ID,
        "request_id": request_id,
    }
    request_sha256 = _SHA256(canonical_json(request_body)).hexdigest()
    challenge_seed_hex = secrets.token_hex(32)
    run_material = {
        "request_sha256": request_sha256,
        "challenge_seed_hex": challenge_seed_hex,
        "run_root": str(run_root),
        "cache_root": str(cache_root),
    }
    run_id = f"pykoopman-{_SHA256(canonical_json(run_material)).hexdigest()[:32]}"
    runtime = _build_pykoopman_capability_flow(
        run_id=run_id,
        ledger_path=run_root / FLOW_LEDGER_NAME,
    )
    binding = CapabilityBinding(
        capability_id=CAPABILITY_ID,
        run_id=run_id,
        flow_policy_sha256=runtime.policy_sha256,
        request_sha256=request_sha256,
        step_id=STEP_ID,
        challenge_seed_hex=challenge_seed_hex,
        cache_root=str(cache_root),
    )
    try:
        flow_receipt = runtime.run(
            {"capability_binding_json": canonical_json(binding.to_dict()).decode("utf-8")}
        )
    except MiniLevError as exc:
        raise ExternalPyKoopmanCapabilityFlowError(
            f"capability flow execution failed: {exc}"
        ) from exc
    valid, reason = verify_flow_receipt(
        flow_receipt,
        expected_run_id=runtime.run_id,
        expected_policy_sha256=runtime.policy_sha256,
        expected_ledger_path=runtime.ledger_path,
        expected_retained_head_sha256=runtime.retained_head_sha256,
        expected_receipt_sha256=runtime.receipt_sha256,
    )
    if not valid:
        raise ExternalPyKoopmanCapabilityFlowError(
            f"capability flow receipt failed verification: {reason}"
        )
    receipt_text = flow_receipt["final_context"].get("capability_receipt_json")
    receipt_sha256 = flow_receipt["final_context"].get("capability_receipt_sha256")
    if not isinstance(receipt_text, str) or not isinstance(receipt_sha256, str):
        raise ExternalPyKoopmanCapabilityFlowError(
            "capability flow produced no external receipt"
        )
    try:
        capability_receipt = parse_json_object(receipt_text.encode("utf-8"))
    except IntakeError as exc:
        raise ExternalPyKoopmanCapabilityFlowError(
            f"capability receipt is invalid: {exc}"
        ) from exc
    capability_errors = validate_pykoopman_capability_receipt(
        capability_receipt,
        expected_binding=binding,
        expected_receipt_sha256=receipt_sha256,
        require_pass=flow_receipt["terminal"] == "ELIGIBLE",
    )
    if capability_errors:
        raise ExternalPyKoopmanCapabilityFlowError(
            "persisted capability receipt failed verification: "
            + "; ".join(capability_errors)
        )
    expected_terminal = {"PASS": "ELIGIBLE", "FAIL": "BLOCKED", "PARKED": "PARKED"}.get(
        capability_receipt.get("status")
    )
    if expected_terminal != flow_receipt["terminal"]:
        raise ExternalPyKoopmanCapabilityFlowError(
            "capability receipt status differs from flow terminal"
        )
    _persist_exclusive(run_root / CAPABILITY_RECEIPT_NAME, capability_receipt)
    _persist_exclusive(run_root / FLOW_RECEIPT_NAME, flow_receipt)
    return {
        "schema": FLOW_RESULT_SCHEMA,
        "capability_id": CAPABILITY_ID,
        "request_id": request_id,
        "request_sha256": request_sha256,
        "run_id": run_id,
        "flow_policy_sha256": runtime.policy_sha256,
        "disposition": flow_receipt["terminal"],
        "reason": capability_receipt["reason"],
        "capability_receipt_sha256": receipt_sha256,
        "flow_receipt_sha256": runtime.receipt_sha256,
        "artifacts": {
            "capability_receipt": str(run_root / CAPABILITY_RECEIPT_NAME),
            "flow_receipt": str(run_root / FLOW_RECEIPT_NAME),
            "flow_ledger": str(run_root / FLOW_LEDGER_NAME),
            "flow_ledger_head": str(run_root / f"{FLOW_LEDGER_NAME}.head"),
        },
        "external_system": True,
        "kernel_membership": "EXTERNAL_NOT_CB_KERNEL",
        "release_allowed": False,
        "engine_readiness_claim": False,
        "cr_truth_claim": False,
        "promotion_allowed": False,
        "claim_ceiling": CAPABILITY_CLAIM_CEILING,
    }


if __name__ == "__main__":
    raise SystemExit(_worker_main())
