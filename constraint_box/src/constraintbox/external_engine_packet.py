from __future__ import annotations

import argparse
import hashlib
import math
import os
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .external_runtime_profiles import (
    inspect_external_runtime,
    runtime_profile_dict,
    selected_runtime_executable,
)
from .intake import IntakeError, canonical_json, parse_json_object


PACKET_SCHEMA = "constraintbox.external-engine-packet-receipt.v1"
ROW_SCHEMA = "constraintbox.external-engine-row-receipt.v1"
INPUT_SCHEMA = "constraintbox.external-engine-input.v1"
EXTERNAL_BOUNDARY = (
    "Exact local operation evidence only; not engine readiness, CR truth, "
    "scientific proof, or hostile-code containment."
)
FIXTURE_SHA256 = "687d90b8216ba7d3e12fd195f18a634d5e2a8a9f7514b52f36b3d68269f7fe8d"
WORKER_SHA256 = {
    "python": "1ad4ff742649e756affd4d30afe2d2e77bf097cfff9d9021017b69650c4a1d13",
    "julia": "45c51388b0137fdf08748baf23e3df06bc841c8aeaccc2e818ba16776b2aed7b",
}
EXACT_APIS = {
    "jax_autodiff": ["jax.grad", "jax.vmap", "jax.jit"],
    "pytorch_jacobian": ["torch.func.jacrev"],
    "pysindy_identification": ["pysindy.SINDy.fit", "pysindy.SINDy.predict"],
    "julia_diffeq": [
        "DifferentialEquations.ODEProblem",
        "DifferentialEquations.solve",
        "DifferentialEquations.Tsit5",
    ],
}
CASE_KEYS = {
    "jax_autodiff": "jax",
    "pytorch_jacobian": "pytorch",
    "pysindy_identification": "pysindy",
    "julia_diffeq": "julia",
}
INTEGRATION_ID = "pysindy_to_julia_rate"
INTEGRATION_SCHEMA = "constraintbox.external-engine-integration-receipt.v1"
INTEGRATION_APIS = EXACT_APIS["julia_diffeq"]


@dataclass(frozen=True)
class RuntimePin:
    """Legacy observation view kept for external adapters not migrated yet.

    This is intentionally computed from the controller-selected profile each
    time it is accessed.  It is no longer a static policy pin or a portable
    success criterion.
    """

    invoked_path: str
    resolved_path: str
    sha256: str


class _RuntimePins:
    """Compatibility mapping for sibling external adapters during migration."""

    def __getitem__(self, family: str) -> RuntimePin:
        identity = inspect_external_runtime(family)
        return RuntimePin(
            invoked_path=str(identity.get("executable_path") or ""),
            resolved_path=str(identity.get("executable_resolved_path") or ""),
            sha256=str(identity.get("executable_sha256") or ""),
        )


# This is a transitional import compatibility surface.  New external flows
# must use `_runtime_pin_dict()` / `_runtime_identity()` below, whose policy is
# the portable profile rather than this observation object.
RUNTIME_PINS = _RuntimePins()


class ExternalPacketError(ValueError):
    pass


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_file(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def _runtime_pin_dict(family: str) -> dict[str, object]:
    """Return the portable profile under the legacy receipt field name.

    ``runtime_pin`` remains in the v1 receipt schema so existing external
    validators can still parse the packet.  Its value is now a profile
    descriptor; local path and digest data lives in separate observed fields.
    """

    return runtime_profile_dict(family)


def _runtime_identity(
    executable: Path | None,
    family: str,
    *,
    explicit_override: bool = False,
) -> dict[str, Any]:
    """Inspect a controller-selected runtime against its portable profile."""

    return inspect_external_runtime(
        family,
        executable,
        explicit_override=explicit_override,
    )


def _worker_environment(*, julia: bool = False) -> dict[str, str]:
    environment = os.environ.copy()
    environment.pop("PYTHONPATH", None)
    environment.pop("PYTHONHOME", None)
    environment["PYTHONHASHSEED"] = "0"
    if julia:
        environment["JULIA_LOAD_PATH"] = "@:@stdlib"
    return environment


def _number(value: Any, path: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ExternalPacketError(f"{path} must be a finite number")
    converted = float(value)
    if not math.isfinite(converted):
        raise ExternalPacketError(f"{path} must be a finite number")
    return converted


def _number_list(value: Any, path: str, length: int | None = None) -> list[float]:
    if not isinstance(value, list):
        raise ExternalPacketError(f"{path} must be an array")
    if length is not None and len(value) != length:
        raise ExternalPacketError(f"{path} must contain {length} values")
    if not value:
        raise ExternalPacketError(f"{path} must not be empty")
    return [_number(item, f"{path}[{index}]") for index, item in enumerate(value)]


def _matrix(value: Any, path: str, rows: int, columns: int) -> list[list[float]]:
    if not isinstance(value, list) or len(value) != rows:
        raise ExternalPacketError(f"{path} must contain {rows} rows")
    return [
        _number_list(row, f"{path}[{index}]", columns)
        for index, row in enumerate(value)
    ]


def _exact_keys(value: Any, path: str, expected: set[str]) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ExternalPacketError(f"{path} must be an object")
    actual = set(value)
    if actual != expected:
        raise ExternalPacketError(
            f"{path} fields differ: missing={sorted(expected - actual)}, "
            f"extra={sorted(actual - expected)}"
        )
    return value


def validate_fixture(value: dict[str, Any]) -> None:
    _exact_keys(
        value,
        "$",
        {"schema", "purpose", "jax", "pytorch", "pysindy", "julia"},
    )
    if value["schema"] != "external-sim-estate.basic-packet-fixture.v1":
        raise ExternalPacketError("unsupported external fixture schema")
    if not isinstance(value["purpose"], str) or not value["purpose"].strip():
        raise ExternalPacketError("$.purpose must be non-empty text")

    jax = _exact_keys(
        value["jax"],
        "$.jax",
        {"cubic", "linear", "points", "wrong_derivatives", "boundary_point"},
    )
    _number(jax["cubic"], "$.jax.cubic")
    _number(jax["linear"], "$.jax.linear")
    points = _number_list(jax["points"], "$.jax.points")
    _number_list(
        jax["wrong_derivatives"], "$.jax.wrong_derivatives", len(points)
    )
    _number(jax["boundary_point"], "$.jax.boundary_point")

    pytorch = _exact_keys(
        value["pytorch"],
        "$.pytorch",
        {"alpha", "beta", "point", "wrong_jacobian", "boundary_point"},
    )
    _number(pytorch["alpha"], "$.pytorch.alpha")
    _number(pytorch["beta"], "$.pytorch.beta")
    _number_list(pytorch["point"], "$.pytorch.point", 2)
    _matrix(pytorch["wrong_jacobian"], "$.pytorch.wrong_jacobian", 2, 2)
    _number_list(pytorch["boundary_point"], "$.pytorch.boundary_point", 2)

    pysindy = _exact_keys(
        value["pysindy"],
        "$.pysindy",
        {
            "rate",
            "train_states",
            "heldout_states",
            "wrong_rate",
            "boundary_state",
        },
    )
    _number(pysindy["rate"], "$.pysindy.rate")
    if len(_number_list(pysindy["train_states"], "$.pysindy.train_states")) < 3:
        raise ExternalPacketError("$.pysindy.train_states needs at least 3 values")
    _number_list(pysindy["heldout_states"], "$.pysindy.heldout_states")
    _number(pysindy["wrong_rate"], "$.pysindy.wrong_rate")
    _number(pysindy["boundary_state"], "$.pysindy.boundary_state")

    julia = _exact_keys(
        value["julia"],
        "$.julia",
        {
            "rate",
            "initial",
            "duration",
            "wrong_rate",
            "boundary_rate",
            "boundary_initial",
            "boundary_duration",
        },
    )
    for key in julia:
        _number(julia[key], f"$.julia.{key}")
    if float(julia["duration"]) <= 0 or float(julia["boundary_duration"]) <= 0:
        raise ExternalPacketError("Julia durations must be positive")


def build_identified_rate_artifact(pysindy_row: dict[str, Any]) -> bytes:
    """Freeze only the admitted PySINDy coefficient into a canonical artifact."""

    if (
        pysindy_row.get("engine_id") != "pysindy_identification"
        or pysindy_row.get("status") != "PASS"
        or not all(pysindy_row.get("controls", {}).values())
    ):
        raise ExternalPacketError("PySINDy producer row is not a passing source")
    observed = pysindy_row.get("observed")
    if not isinstance(observed, dict):
        raise ExternalPacketError("PySINDy producer observation is missing")
    identified_rate = _number(
        observed.get("coefficient"), "$.pysindy.observed.coefficient"
    )
    artifact = {
        "schema": "external-sim-estate.identified-rate-artifact.v1",
        "external_system": True,
        "producer_engine_id": "pysindy_identification",
        "producer_exact_api": EXACT_APIS["pysindy_identification"],
        "producer_input_sha256": pysindy_row.get("input_sha256"),
        "producer_output_sha256": pysindy_row.get("output_sha256"),
        "producer_source_sha256": pysindy_row.get("worker_source_sha256"),
        "identified_rate": identified_rate,
        "engine_readiness_claim": False,
        "cr_truth_claim": False,
        "promotion_allowed": False,
        "claim_ceiling": EXTERNAL_BOUNDARY,
    }
    for key in (
        "producer_input_sha256",
        "producer_output_sha256",
        "producer_source_sha256",
    ):
        value = artifact[key]
        if (
            not isinstance(value, str)
            or len(value) != 64
            or any(character not in "0123456789abcdef" for character in value)
        ):
            raise ExternalPacketError(f"invalid producer binding: {key}")
    return canonical_json(artifact)


def validate_handoff_artifact(
    artifact_bytes: bytes | None,
    *,
    expected_sha256: str,
    expected_producer_output_sha256: str,
) -> dict[str, Any]:
    """Validate the exact frozen handoff; callers cannot substitute its rate."""

    if artifact_bytes is None:
        return {"accepted": False, "reason": "artifact_missing"}
    observed_sha256 = _sha256_bytes(artifact_bytes)
    if observed_sha256 != expected_sha256:
        return {
            "accepted": False,
            "reason": "artifact_digest_mismatch",
            "expected_sha256": expected_sha256,
            "observed_sha256": observed_sha256,
        }
    try:
        artifact = parse_json_object(artifact_bytes)
    except IntakeError as exc:
        return {
            "accepted": False,
            "reason": "artifact_not_strict_json",
            "detail": str(exc),
        }
    if canonical_json(artifact) != artifact_bytes:
        return {"accepted": False, "reason": "artifact_not_canonical_json"}
    expected_keys = {
        "schema",
        "external_system",
        "producer_engine_id",
        "producer_exact_api",
        "producer_input_sha256",
        "producer_output_sha256",
        "producer_source_sha256",
        "identified_rate",
        "engine_readiness_claim",
        "cr_truth_claim",
        "promotion_allowed",
        "claim_ceiling",
    }
    if set(artifact) != expected_keys:
        return {"accepted": False, "reason": "artifact_fields_mismatch"}
    fixed_fields_pass = (
        artifact.get("schema")
        == "external-sim-estate.identified-rate-artifact.v1"
        and artifact.get("external_system") is True
        and artifact.get("producer_engine_id") == "pysindy_identification"
        and artifact.get("producer_exact_api")
        == EXACT_APIS["pysindy_identification"]
        and artifact.get("producer_output_sha256")
        == expected_producer_output_sha256
        and artifact.get("engine_readiness_claim") is False
        and artifact.get("cr_truth_claim") is False
        and artifact.get("promotion_allowed") is False
        and artifact.get("claim_ceiling") == EXTERNAL_BOUNDARY
    )
    if not fixed_fields_pass:
        return {"accepted": False, "reason": "artifact_binding_mismatch"}
    try:
        _number(artifact.get("identified_rate"), "$.identified_rate")
    except ExternalPacketError as exc:
        return {
            "accepted": False,
            "reason": "artifact_rate_invalid",
            "detail": str(exc),
        }
    return {
        "accepted": True,
        "reason": "artifact_bound",
        "artifact": artifact,
        "artifact_sha256": observed_sha256,
    }


def _flatten(value: Any) -> list[float]:
    if isinstance(value, list):
        flattened: list[float] = []
        for item in value:
            flattened.extend(_flatten(item))
        return flattened
    return [_number(value, "$.observed")]


def _comparison(actual: Any, expected: Any, tolerance: float) -> dict[str, Any]:
    try:
        actual_values = _flatten(actual)
        expected_values = _flatten(expected)
    except ExternalPacketError as exc:
        return {"pass": False, "max_abs_error": None, "reason": str(exc)}
    if len(actual_values) != len(expected_values):
        return {
            "pass": False,
            "max_abs_error": None,
            "reason": "shape_length_mismatch",
        }
    errors = [
        abs(actual_item - expected_item)
        for actual_item, expected_item in zip(actual_values, expected_values)
    ]
    maximum = max(errors, default=0.0)
    return {
        "pass": maximum <= tolerance,
        "max_abs_error": maximum,
        "tolerance": tolerance,
    }


def _jax_evaluation(case: dict[str, Any], observed: dict[str, Any]) -> dict[str, Any]:
    cubic = float(case["cubic"])
    linear = float(case["linear"])
    expected = [
        3.0 * cubic * float(point) ** 2 + linear for point in case["points"]
    ]
    boundary_expected = 3.0 * cubic * float(case["boundary_point"]) ** 2 + linear
    positive = _comparison(observed.get("derivatives"), expected, 1e-10)
    boundary = _comparison(
        observed.get("boundary_derivative"), boundary_expected, 1e-10
    )
    wrong = _comparison(
        observed.get("derivatives"), case["wrong_derivatives"], 1e-10
    )
    wrong_distinct = _comparison(expected, case["wrong_derivatives"], 1e-10)
    controls = {
        "positive": bool(positive["pass"]),
        "targeted_negative": bool(
            not wrong["pass"] and not wrong_distinct["pass"]
        ),
        "boundary": bool(boundary["pass"]),
    }
    return {
        "controls": controls,
        "expected": {
            "derivatives": expected,
            "boundary_derivative": boundary_expected,
        },
        "comparisons": {
            "positive": positive,
            "targeted_negative_wrong_claim_match": wrong,
            "boundary": boundary,
        },
    }


def _pytorch_evaluation(
    case: dict[str, Any], observed: dict[str, Any]
) -> dict[str, Any]:
    alpha = float(case["alpha"])
    beta = float(case["beta"])
    x0, x1 = (float(value) for value in case["point"])
    expected = [[2.0 * alpha * x0, beta], [x1, x0]]
    bx0, bx1 = (float(value) for value in case["boundary_point"])
    boundary_expected = [[2.0 * alpha * bx0, beta], [bx1, bx0]]
    positive = _comparison(observed.get("jacobian"), expected, 1e-10)
    boundary = _comparison(
        observed.get("boundary_jacobian"), boundary_expected, 1e-10
    )
    wrong = _comparison(
        observed.get("jacobian"), case["wrong_jacobian"], 1e-10
    )
    wrong_distinct = _comparison(expected, case["wrong_jacobian"], 1e-10)
    controls = {
        "positive": bool(positive["pass"]),
        "targeted_negative": bool(
            not wrong["pass"] and not wrong_distinct["pass"]
        ),
        "boundary": bool(boundary["pass"]),
    }
    return {
        "controls": controls,
        "expected": {
            "jacobian": expected,
            "boundary_jacobian": boundary_expected,
        },
        "comparisons": {
            "positive": positive,
            "targeted_negative_wrong_claim_match": wrong,
            "boundary": boundary,
        },
    }


def _pysindy_evaluation(
    case: dict[str, Any], observed: dict[str, Any]
) -> dict[str, Any]:
    rate = float(case["rate"])
    heldout = [float(value) for value in case["heldout_states"]]
    expected = [rate * value for value in heldout]
    coefficient = _comparison(observed.get("coefficient"), rate, 1e-8)
    predictions = _comparison(
        observed.get("heldout_derivatives"), expected, 1e-8
    )
    boundary_expected = rate * float(case["boundary_state"])
    boundary = _comparison(
        observed.get("boundary_derivative"), boundary_expected, 1e-8
    )
    wrong_rate = float(case["wrong_rate"])
    wrong = _comparison(observed.get("coefficient"), wrong_rate, 1e-8)
    wrong_distinct = _comparison(rate, wrong_rate, 1e-8)
    try:
        actual_values = _flatten(observed.get("heldout_derivatives"))
        residual = sum(
            (actual - expected_value) ** 2
            for actual, expected_value in zip(actual_values, expected)
        ) / len(expected)
    except ExternalPacketError:
        residual = None
    controls = {
        "positive": bool(coefficient["pass"] and predictions["pass"]),
        "targeted_negative": bool(
            not wrong["pass"] and not wrong_distinct["pass"]
        ),
        "boundary": bool(boundary["pass"]),
    }
    return {
        "controls": controls,
        "expected": {
            "coefficient": rate,
            "heldout_derivatives": expected,
            "boundary_derivative": boundary_expected,
        },
        "comparisons": {
            "coefficient": coefficient,
            "heldout": predictions,
            "heldout_mean_squared_residual": residual,
            "targeted_negative_wrong_rate_match": wrong,
            "boundary": boundary,
        },
    }


def _julia_evaluation(
    case: dict[str, Any], observed: dict[str, Any]
) -> dict[str, Any]:
    rate = float(case["rate"])
    initial = float(case["initial"])
    duration = float(case["duration"])
    expected = initial * math.exp(rate * duration)
    boundary_expected = float(case["boundary_initial"]) * math.exp(
        float(case["boundary_rate"]) * float(case["boundary_duration"])
    )
    wrong_expected = initial * math.exp(float(case["wrong_rate"]) * duration)
    positive = _comparison(observed.get("terminal"), expected, 5e-8)
    boundary = _comparison(
        observed.get("boundary_terminal"), boundary_expected, 5e-8
    )
    wrong = _comparison(observed.get("terminal"), wrong_expected, 5e-8)
    wrong_distinct = _comparison(expected, wrong_expected, 5e-8)
    controls = {
        "positive": bool(positive["pass"]),
        "targeted_negative": bool(
            not wrong["pass"] and not wrong_distinct["pass"]
        ),
        "boundary": bool(boundary["pass"]),
    }
    return {
        "controls": controls,
        "expected": {
            "terminal": expected,
            "boundary_terminal": boundary_expected,
        },
        "comparisons": {
            "positive": positive,
            "targeted_negative_wrong_rate_terminal_match": wrong,
            "boundary": boundary,
        },
    }


def evaluate_worker_output(
    engine_id: str,
    fixture: dict[str, Any],
    witness: dict[str, Any],
    *,
    julia_project: Path | None = None,
    controller_pid: int | None = None,
    expected_execution_binding: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Recompute expectations in the broker; never trust worker pass fields."""

    errors: list[str] = []
    if witness.get("schema") != "constraintbox.external-engine-witness.v1":
        errors.append("witness_schema_mismatch")
    if witness.get("engine_id") != engine_id:
        errors.append("witness_engine_id_mismatch")
    if witness.get("exact_api") != EXACT_APIS.get(engine_id):
        errors.append("exact_api_mismatch")
    if expected_execution_binding is None:
        if "execution_binding" in witness:
            errors.append("unexpected_execution_binding")
    elif witness.get("execution_binding") != expected_execution_binding:
        errors.append("execution_binding_mismatch")
    if not isinstance(witness.get("runtime"), dict):
        errors.append("runtime_not_object")
    worker_pid = witness.get("pid")
    if (
        isinstance(worker_pid, bool)
        or not isinstance(worker_pid, int)
        or worker_pid <= 0
    ):
        errors.append("worker_pid_invalid")
    if controller_pid is not None and worker_pid == controller_pid:
        errors.append("worker_not_separate_process")
    observed = witness.get("observed")
    if not isinstance(observed, dict):
        return {
            "controls": {
                "positive": False,
                "targeted_negative": False,
                "boundary": False,
            },
            "errors": errors + ["observed_not_object"],
        }

    evaluators = {
        "jax_autodiff": _jax_evaluation,
        "pytorch_jacobian": _pytorch_evaluation,
        "pysindy_identification": _pysindy_evaluation,
        "julia_diffeq": _julia_evaluation,
    }
    if engine_id not in evaluators:
        raise ExternalPacketError(f"unknown engine id: {engine_id}")
    evaluation = evaluators[engine_id](fixture[CASE_KEYS[engine_id]], observed)
    if engine_id == "julia_diffeq":
        runtime = witness.get("runtime", {})
        expected_project = (
            (julia_project / "Project.toml").resolve()
            if julia_project is not None
            else None
        )
        try:
            active_project = Path(runtime.get("active_project", "")).resolve()
        except (OSError, TypeError):
            active_project = Path("")
        strict_carrier = (
            expected_project is not None
            and active_project == expected_project
            and runtime.get("load_path") == ["@", "@stdlib"]
        )
        evaluation["controls"]["strict_carrier"] = strict_carrier
        evaluation["strict_carrier"] = {
            "pass": strict_carrier,
            "expected_project": (
                str(expected_project) if expected_project is not None else None
            ),
            "observed_project": runtime.get("active_project"),
            "observed_load_path": runtime.get("load_path"),
        }
    if errors:
        evaluation["errors"] = errors
        for key in evaluation["controls"]:
            evaluation["controls"][key] = False
    else:
        evaluation["errors"] = []
    return evaluation


class ExternalEnginePacketBroker:
    """Narrow CB broker for a separate, source-pinned external sim packet."""

    def __init__(
        self,
        *,
        repo_root: Path | None = None,
        python_executable: Path | None = None,
        julia_executable: Path | None = None,
        timeout_seconds: float = 180.0,
    ) -> None:
        self.repo_root = (
            repo_root.resolve()
            if repo_root is not None
            else Path(__file__).resolve().parents[3]
        )
        # A contained CB source product may bind the separately installed
        # external sim estate explicitly. The default preserves repository
        # checkout behavior; no request or model can select this path.
        external_estate = os.environ.get("CONSTRAINTBOX_EXTERNAL_SIM_ESTATE")
        self.external_root = (
            Path(external_estate).expanduser().resolve() / "basic_packet_v1"
            if external_estate
            else self.repo_root / "external_sim_estate" / "basic_packet_v1"
        )
        self.fixture_path = (
            self.external_root / "fixtures" / "exact_operations_v1.json"
        )
        self.python_worker = (
            self.external_root / "workers" / "python_engine_worker.py"
        )
        self.julia_worker = (
            self.external_root / "workers" / "julia_diffeq_worker.jl"
        )
        julia_project = os.environ.get("CONSTRAINTBOX_JULIA_PROJECT")
        self.julia_project = (
            Path(julia_project).expanduser().resolve()
            if julia_project
            else self.repo_root / "system_v5" / "julia_carrier"
        )
        # The controller decides the executable.  Constructor parameters exist
        # only to exercise hostile/injected-runtime rejection in tests and are
        # never exposed as CLI or request inputs.
        self._python_runtime_override = python_executable is not None
        self._julia_runtime_override = julia_executable is not None
        self.python_executable = (
            Path(python_executable).absolute()
            if python_executable is not None
            else selected_runtime_executable("python")
        )
        self.julia_executable = (
            Path(julia_executable).absolute()
            if julia_executable is not None
            else selected_runtime_executable("julia")
        )
        self.timeout_seconds = timeout_seconds
        self.controller_path = Path(__file__).resolve()

    def _load_fixture(self) -> tuple[dict[str, Any], bytes, str]:
        raw = self.fixture_path.read_bytes()
        raw_digest = _sha256_bytes(raw)
        if raw_digest != FIXTURE_SHA256:
            raise ExternalPacketError(
                "external fixture source digest mismatch: "
                f"expected={FIXTURE_SHA256}, observed={raw_digest}"
            )
        try:
            fixture = parse_json_object(raw)
        except IntakeError as exc:
            raise ExternalPacketError(str(exc)) from exc
        validate_fixture(fixture)
        return fixture, canonical_json(fixture), raw_digest

    def _command(
        self, engine_id: str
    ) -> tuple[list[str], Path | None, Path, str, bool]:
        if engine_id == "julia_diffeq":
            if self.julia_executable is None:
                return [], None, self.julia_worker, "julia", self._julia_runtime_override
            return (
                [
                    str(self.julia_executable),
                    "--startup-file=no",
                    f"--project={self.julia_project}",
                    str(self.julia_worker),
                ],
                self.julia_executable,
                self.julia_worker,
                "julia",
                self._julia_runtime_override,
            )
        if self.python_executable is None:
            return [], None, self.python_worker, "python", self._python_runtime_override
        return (
            [
                str(self.python_executable),
                "-I",
                str(self.python_worker),
                engine_id,
            ],
            self.python_executable,
            self.python_worker,
            "python",
            self._python_runtime_override,
        )

    def _row_base(
        self,
        engine_id: str,
        *,
        fixture_sha256: str,
        input_sha256: str,
    ) -> dict[str, Any]:
        return {
            "schema": ROW_SCHEMA,
            "engine_id": engine_id,
            "external_system": True,
            "kernel_membership": "EXTERNAL_NOT_CB_KERNEL",
            "exact_api": EXACT_APIS[engine_id],
            "fixture_sha256": fixture_sha256,
            "input_sha256": input_sha256,
            "controller_sha256": _sha256_file(self.controller_path),
            "promotion_allowed": False,
            "engine_readiness_claim": False,
            "cr_truth_claim": False,
            "claim_ceiling": EXTERNAL_BOUNDARY,
            "runtime_pin": _runtime_pin_dict(
                "julia" if engine_id == "julia_diffeq" else "python"
            ),
        }

    def _run_row(
        self,
        engine_id: str,
        fixture: dict[str, Any],
        fixture_sha256: str,
        *,
        execution_binding: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        transport = {
            "schema": INPUT_SCHEMA,
            "engine_id": engine_id,
            "case": fixture[CASE_KEYS[engine_id]],
        }
        if execution_binding is not None:
            transport["execution_binding"] = execution_binding
        input_bytes = canonical_json(transport)
        row = self._row_base(
            engine_id,
            fixture_sha256=fixture_sha256,
            input_sha256=_sha256_bytes(input_bytes),
        )
        command, executable, worker, worker_family, explicit_override = self._command(
            engine_id
        )
        row["command"] = command
        if execution_binding is not None:
            row["execution_binding"] = execution_binding
        runtime_identity = _runtime_identity(
            executable,
            worker_family,
            explicit_override=explicit_override,
        )
        row.update(
            {
                key: value
                for key, value in runtime_identity.items()
                if key not in {"eligible", "disposition", "reason", "detail"}
            }
        )
        if not runtime_identity["eligible"]:
            row.update(
                {
                    "status": runtime_identity["disposition"],
                    "reason": runtime_identity["reason"],
                }
            )
            if "detail" in runtime_identity:
                row["detail"] = runtime_identity["detail"]
            return row
        if not worker.exists() or not worker.is_file():
            row.update({"status": "FAIL", "reason": "worker_source_missing"})
            return row
        observed_worker_sha = _sha256_file(worker)
        expected_worker_sha = WORKER_SHA256[worker_family]
        row["worker_source_sha256"] = observed_worker_sha
        row["worker_source_sha256_expected"] = expected_worker_sha
        if observed_worker_sha != expected_worker_sha:
            row.update({"status": "FAIL", "reason": "worker_source_digest_mismatch"})
            return row

        environment = _worker_environment(
            julia=engine_id == "julia_diffeq"
        )
        if engine_id == "julia_diffeq":
            if not self.julia_project.is_dir():
                row.update(
                    {
                        "status": "PARKED",
                        "reason": "strict_julia_carrier_unavailable",
                    }
                )
                return row
        started = time.monotonic()
        try:
            process = subprocess.run(
                command,
                input=input_bytes,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=self.repo_root,
                env=environment,
                timeout=self.timeout_seconds,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            stdout = exc.stdout or b""
            stderr = exc.stderr or b""
            row.update(
                {
                    "status": "FAIL",
                    "reason": "worker_timeout",
                    "elapsed_seconds": time.monotonic() - started,
                    "stdout_sha256": _sha256_bytes(stdout),
                    "stderr_sha256": _sha256_bytes(stderr),
                }
            )
            return row

        row["elapsed_seconds"] = time.monotonic() - started
        row["returncode"] = process.returncode
        row["stdout_sha256"] = _sha256_bytes(process.stdout)
        row["stderr_sha256"] = _sha256_bytes(process.stderr)
        try:
            witness = parse_json_object(process.stdout.strip())
            canonical_output = canonical_json(witness)
        except IntakeError as exc:
            row.update(
                {
                    "status": "FAIL",
                    "reason": "worker_output_not_strict_json",
                    "output_error": str(exc),
                    "stderr": process.stderr.decode("utf-8", errors="replace")[
                        :4096
                    ],
                }
            )
            return row
        row["output_sha256"] = _sha256_bytes(canonical_output)
        row["worker_pid"] = witness.get("pid")

        if process.returncode == 3:
            valid_unavailable = (
                witness.get("schema")
                == "constraintbox.external-engine-unavailable.v1"
                and witness.get("engine_id") == engine_id
                and witness.get("exact_api") == EXACT_APIS[engine_id]
                and witness.get("execution_binding") == execution_binding
                and isinstance(witness.get("reason"), str)
                and bool(witness["reason"].strip())
            )
            row.update(
                {
                    "status": "PARKED" if valid_unavailable else "FAIL",
                    "reason": (
                        "exact_function_unavailable"
                        if valid_unavailable
                        else "malformed_unavailable_witness"
                    ),
                    "worker_reason": witness.get("reason"),
                }
            )
            return row
        if process.returncode != 0:
            row.update(
                {
                    "status": "FAIL",
                    "reason": "worker_nonzero_exit",
                    "stderr": process.stderr.decode("utf-8", errors="replace")[
                        :4096
                    ],
                }
            )
            return row

        evaluation = evaluate_worker_output(
            engine_id,
            fixture,
            witness,
            julia_project=self.julia_project,
            controller_pid=os.getpid(),
            expected_execution_binding=execution_binding,
        )
        controls = evaluation["controls"]
        passed = all(controls.values()) and not evaluation["errors"]
        row.update(
            {
                "status": "PASS" if passed else "FAIL",
                "reason": (
                    "exact_operation_controls_passed"
                    if passed
                    else "controller_recomputed_check_failed"
                ),
                "controls": controls,
                "controller_evaluation": evaluation,
                "observed": witness.get("observed"),
                "runtime": witness.get("runtime"),
            }
        )
        return row

    def _run_integration(
        self,
        rows: list[dict[str, Any]],
        fixture: dict[str, Any],
        fixture_sha256: str,
    ) -> dict[str, Any]:
        by_engine = {row["engine_id"]: row for row in rows}
        producer = by_engine["pysindy_identification"]
        consumer_component = by_engine["julia_diffeq"]
        base: dict[str, Any] = {
            "schema": INTEGRATION_SCHEMA,
            "integration_id": INTEGRATION_ID,
            "external_system": True,
            "kernel_membership": "EXTERNAL_NOT_CB_KERNEL",
            "producer_engine_id": "pysindy_identification",
            "consumer_engine_id": "julia_diffeq",
            "exact_api": {
                "producer": EXACT_APIS["pysindy_identification"],
                "consumer": INTEGRATION_APIS,
            },
            "fixture_sha256": fixture_sha256,
            "controller_sha256": _sha256_file(self.controller_path),
            "promotion_allowed": False,
            "engine_readiness_claim": False,
            "cr_truth_claim": False,
            "claim_ceiling": EXTERNAL_BOUNDARY,
            "runtime_pin": _runtime_pin_dict("julia"),
        }
        if producer.get("status") != "PASS" or consumer_component.get(
            "status"
        ) != "PASS":
            base.update(
                {
                    "status": "PARKED",
                    "reason": "component_rows_not_both_pass",
                    "component_status": {
                        "pysindy_identification": producer.get("status"),
                        "julia_diffeq": consumer_component.get("status"),
                    },
                }
            )
            return base

        try:
            artifact_bytes = build_identified_rate_artifact(producer)
        except ExternalPacketError as exc:
            base.update(
                {
                    "status": "FAIL",
                    "reason": "producer_artifact_construction_failed",
                    "detail": str(exc),
                }
            )
            return base
        artifact_sha256 = _sha256_bytes(artifact_bytes)
        valid_handoff = validate_handoff_artifact(
            artifact_bytes,
            expected_sha256=artifact_sha256,
            expected_producer_output_sha256=producer["output_sha256"],
        )
        removal_check = validate_handoff_artifact(
            None,
            expected_sha256=artifact_sha256,
            expected_producer_output_sha256=producer["output_sha256"],
        )
        digest_mutation_check = validate_handoff_artifact(
            artifact_bytes + b" ",
            expected_sha256=artifact_sha256,
            expected_producer_output_sha256=producer["output_sha256"],
        )
        artifact = parse_json_object(artifact_bytes)
        substituted_artifact = dict(artifact)
        identified_rate = _number(
            artifact["identified_rate"], "$.identified_rate"
        )
        substituted_artifact["identified_rate"] = (
            -identified_rate if abs(identified_rate) > 1e-15 else 1.0
        )
        wrong_rate_check = validate_handoff_artifact(
            canonical_json(substituted_artifact),
            expected_sha256=artifact_sha256,
            expected_producer_output_sha256=producer["output_sha256"],
        )
        preflight_controls = {
            "producer_passed": True,
            "artifact_canonical": bool(valid_handoff["accepted"]),
            "removal_rejected": (
                not removal_check["accepted"]
                and removal_check["reason"] == "artifact_missing"
            ),
            "digest_mutation_rejected": (
                not digest_mutation_check["accepted"]
                and digest_mutation_check["reason"] == "artifact_digest_mismatch"
            ),
            "wrong_rate_substitution_rejected": (
                not wrong_rate_check["accepted"]
                and wrong_rate_check["reason"] == "artifact_digest_mismatch"
            ),
        }
        base["artifact"] = artifact
        base["artifact_sha256"] = artifact_sha256
        base["handoff_rejection_evidence"] = {
            "removal": removal_check,
            "digest_mutation": digest_mutation_check,
            "wrong_rate_substitution": wrong_rate_check,
        }
        if not all(preflight_controls.values()):
            base.update(
                {
                    "status": "FAIL",
                    "reason": "handoff_preflight_control_failed",
                    "controls": preflight_controls,
                }
            )
            return base

        transport = {
            "schema": "constraintbox.external-engine-handoff-input.v1",
            "engine_id": INTEGRATION_ID,
            "artifact_json": artifact_bytes.decode("utf-8"),
            "artifact_sha256": artifact_sha256,
            "case": {
                "initial": fixture["julia"]["initial"],
                "duration": fixture["julia"]["duration"],
            },
        }
        input_bytes = canonical_json(transport)
        base["input_sha256"] = _sha256_bytes(input_bytes)
        command, executable, worker, _worker_family, explicit_override = self._command(
            "julia_diffeq"
        )
        base["command"] = command
        runtime_identity = _runtime_identity(
            executable,
            "julia",
            explicit_override=explicit_override,
        )
        base.update(
            {
                key: value
                for key, value in runtime_identity.items()
                if key not in {
                    "eligible",
                    "disposition",
                    "reason",
                    "detail",
                    "runtime_pin",
                }
            }
        )
        if not runtime_identity["eligible"]:
            base.update(
                {
                    "status": runtime_identity["disposition"],
                    "reason": (
                        "consumer_" + str(runtime_identity["reason"])
                    ),
                }
            )
            if "detail" in runtime_identity:
                base["detail"] = runtime_identity["detail"]
            return base
        observed_worker_sha = _sha256_file(worker)
        base["worker_source_sha256"] = observed_worker_sha
        base["worker_source_sha256_expected"] = WORKER_SHA256["julia"]
        if observed_worker_sha != WORKER_SHA256["julia"]:
            base.update(
                {
                    "status": "FAIL",
                    "reason": "consumer_worker_source_digest_mismatch",
                }
            )
            return base
        environment = _worker_environment(julia=True)
        started = time.monotonic()
        try:
            process = subprocess.run(
                command,
                input=input_bytes,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=self.repo_root,
                env=environment,
                timeout=self.timeout_seconds,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            stdout = exc.stdout or b""
            stderr = exc.stderr or b""
            base.update(
                {
                    "status": "FAIL",
                    "reason": "integration_consumer_timeout",
                    "elapsed_seconds": time.monotonic() - started,
                    "stdout_sha256": _sha256_bytes(stdout),
                    "stderr_sha256": _sha256_bytes(stderr),
                    "controls": preflight_controls,
                }
            )
            return base

        base["elapsed_seconds"] = time.monotonic() - started
        base["returncode"] = process.returncode
        base["stdout_sha256"] = _sha256_bytes(process.stdout)
        base["stderr_sha256"] = _sha256_bytes(process.stderr)
        try:
            witness = parse_json_object(process.stdout.strip())
            canonical_output = canonical_json(witness)
        except IntakeError as exc:
            base.update(
                {
                    "status": "FAIL",
                    "reason": "integration_output_not_strict_json",
                    "output_error": str(exc),
                    "stderr": process.stderr.decode("utf-8", errors="replace")[
                        :4096
                    ],
                    "controls": preflight_controls,
                }
            )
            return base
        base["output_sha256"] = _sha256_bytes(canonical_output)
        base["worker_pid"] = witness.get("pid")
        if process.returncode == 3:
            valid_unavailable = (
                witness.get("schema")
                == "constraintbox.external-engine-unavailable.v1"
                and witness.get("engine_id") == INTEGRATION_ID
                and witness.get("exact_api") == INTEGRATION_APIS
                and isinstance(witness.get("reason"), str)
            )
            base.update(
                {
                    "status": "PARKED" if valid_unavailable else "FAIL",
                    "reason": (
                        "consumer_exact_function_unavailable"
                        if valid_unavailable
                        else "malformed_integration_unavailable_witness"
                    ),
                    "worker_reason": witness.get("reason"),
                    "controls": preflight_controls,
                }
            )
            return base
        if process.returncode != 0:
            base.update(
                {
                    "status": "FAIL",
                    "reason": "integration_consumer_nonzero_exit",
                    "stderr": process.stderr.decode("utf-8", errors="replace")[
                        :4096
                    ],
                    "controls": preflight_controls,
                }
            )
            return base

        header_errors: list[str] = []
        if (
            witness.get("schema")
            != "constraintbox.external-engine-integration-witness.v1"
        ):
            header_errors.append("integration_witness_schema_mismatch")
        if witness.get("integration_id") != INTEGRATION_ID:
            header_errors.append("integration_witness_id_mismatch")
        if witness.get("exact_api") != INTEGRATION_APIS:
            header_errors.append("integration_exact_api_mismatch")
        if witness.get("pid") == os.getpid() or not isinstance(
            witness.get("pid"), int
        ):
            header_errors.append("integration_not_separate_process")
        observed = witness.get("observed")
        runtime = witness.get("runtime")
        if not isinstance(observed, dict):
            observed = {}
            header_errors.append("integration_observed_not_object")
        if not isinstance(runtime, dict):
            runtime = {}
            header_errors.append("integration_runtime_not_object")
        initial = float(fixture["julia"]["initial"])
        duration = float(fixture["julia"]["duration"])
        expected_terminal = initial * math.exp(identified_rate * duration)
        terminal_check = _comparison(
            observed.get("terminal"), expected_terminal, 5e-8
        )
        rate_check = _comparison(
            observed.get("consumed_rate"), identified_rate, 1e-12
        )
        artifact_check = (
            observed.get("artifact_sha256") == artifact_sha256
        )
        expected_project = (self.julia_project / "Project.toml").resolve()
        try:
            active_project = Path(runtime.get("active_project", "")).resolve()
        except (OSError, TypeError):
            active_project = Path("")
        strict_carrier = (
            active_project == expected_project
            and runtime.get("load_path") == ["@", "@stdlib"]
        )
        controls = preflight_controls | {
            "artifact_digest_bound": artifact_check,
            "consumer_used_identified_rate": bool(rate_check["pass"]),
            "positive": bool(terminal_check["pass"]),
            "strict_carrier": strict_carrier,
            "separate_process": not header_errors,
        }
        if header_errors:
            for key in controls:
                controls[key] = False
        passed = all(controls.values())
        base.update(
            {
                "status": "PASS" if passed else "FAIL",
                "reason": (
                    "pysindy_artifact_consumed_by_julia"
                    if passed
                    else "integration_controller_check_failed"
                ),
                "controls": controls,
                "controller_evaluation": {
                    "expected": {
                        "identified_rate": identified_rate,
                        "terminal": expected_terminal,
                    },
                    "comparisons": {
                        "consumed_rate": rate_check,
                        "terminal": terminal_check,
                        "artifact_sha256_match": artifact_check,
                    },
                    "strict_carrier": {
                        "pass": strict_carrier,
                        "expected_project": str(expected_project),
                        "observed_project": runtime.get("active_project"),
                        "observed_load_path": runtime.get("load_path"),
                    },
                    "errors": header_errors,
                },
                "observed": observed,
                "runtime": runtime,
            }
        )
        return base

    def run(self) -> dict[str, Any]:
        started = time.monotonic()
        try:
            fixture, canonical_fixture, fixture_sha256 = self._load_fixture()
        except FileNotFoundError as exc:
            # An omitted external estate is not evidence that the packet failed
            # to compute.  It is an unavailable external workload and must park
            # rather than fall through to a host path or become a synthetic FAIL.
            return {
                "schema": PACKET_SCHEMA,
                "status": "PARKED",
                "reason": "external_fixture_unavailable",
                "detail": str(exc),
                "external_system": True,
                "kernel_membership": "EXTERNAL_NOT_CB_KERNEL",
                "promotion_allowed": False,
                "engine_readiness_claim": False,
                "claim_ceiling": EXTERNAL_BOUNDARY,
                "runtime_pins": {
                    family: _runtime_pin_dict(family)
                    for family in ("python", "julia")
                },
                "rows": [],
            }
        except (OSError, ExternalPacketError) as exc:
            return {
                "schema": PACKET_SCHEMA,
                "status": "FAIL",
                "reason": "external_fixture_integrity_failure",
                "detail": str(exc),
                "external_system": True,
                "kernel_membership": "EXTERNAL_NOT_CB_KERNEL",
                "promotion_allowed": False,
                "engine_readiness_claim": False,
                "claim_ceiling": EXTERNAL_BOUNDARY,
                "runtime_pins": {
                    family: _runtime_pin_dict(family)
                    for family in ("python", "julia")
                },
                "rows": [],
            }
        rows = [
            self._run_row(engine_id, fixture, fixture_sha256)
            for engine_id in EXACT_APIS
        ]
        integration = self._run_integration(rows, fixture, fixture_sha256)
        statuses = {row["status"] for row in rows} | {integration["status"]}
        if "FAIL" in statuses:
            status = "FAIL"
            reason = "one_or_more_component_or_integration_checks_failed"
        elif "PARKED" in statuses:
            status = "PARKED"
            reason = "one_or_more_component_or_integration_checks_parked"
        else:
            status = "PASS"
            reason = "all_component_and_integration_checks_passed"
        return {
            "schema": PACKET_SCHEMA,
            "status": status,
            "reason": reason,
            "external_system": True,
            "kernel_membership": "EXTERNAL_NOT_CB_KERNEL",
            "fixture_path": str(self.fixture_path),
            "fixture_sha256": fixture_sha256,
            "canonical_fixture_sha256": _sha256_bytes(canonical_fixture),
            "controller_sha256": _sha256_file(self.controller_path),
            "elapsed_seconds": time.monotonic() - started,
            "promotion_allowed": False,
            "engine_readiness_claim": False,
            "cr_truth_claim": False,
            "claim_ceiling": EXTERNAL_BOUNDARY,
            "runtime_pins": {
                family: _runtime_pin_dict(family)
                for family in ("python", "julia")
            },
            "integration": integration,
            "rows": rows,
        }


def validate_pass_receipt(receipt: dict[str, Any]) -> tuple[str, ...]:
    """Revalidate a claimed PASS packet against the current trusted boundary.

    This is deliberately narrower than a general receipt parser.  A non-PASS
    packet, a partial packet, or a packet from a different controller/runtime
    generation is never release-eligible.
    """

    errors: list[str] = []

    def error(path: str, reason: str) -> None:
        errors.append(f"{path}:{reason}")

    def exact_keys(
        value: Any, path: str, expected: set[str]
    ) -> dict[str, Any] | None:
        if not isinstance(value, dict):
            error(path, "not_object")
            return None
        actual = set(value)
        if actual != expected:
            if expected - actual:
                error(path, f"missing_fields={sorted(expected - actual)!r}")
            if actual - expected:
                error(path, f"extra_fields={sorted(actual - expected)!r}")
        return value

    def expect(value: Any, expected: Any, path: str) -> None:
        if value != expected:
            error(path, "value_mismatch")

    def validate_digest(value: Any, path: str) -> None:
        if (
            not isinstance(value, str)
            or len(value) != 64
            or any(character not in "0123456789abcdef" for character in value)
        ):
            error(path, "not_sha256")

    def validate_elapsed(value: Any, path: str) -> None:
        try:
            converted = _number(value, path)
        except ExternalPacketError:
            error(path, "not_finite_number")
            return
        if converted < 0:
            error(path, "negative")

    def validate_runtime(
        value: dict[str, Any],
        path: str,
        family: str,
    ) -> None:
        expect(value.get("runtime_pin"), _runtime_pin_dict(family), path + ".runtime_pin")
        identity = _runtime_identity(selected_runtime_executable(family), family)
        if not identity.get("eligible"):
            error(path + ".runtime_pin", "current_runtime_not_eligible")
            return
        expect(
            value.get("executable_path"),
            identity["executable_path"],
            path + ".executable_path",
        )
        expect(
            value.get("executable_resolved_path"),
            identity["executable_resolved_path"],
            path + ".executable_resolved_path",
        )
        expect(
            value.get("executable_sha256"),
            identity["executable_sha256"],
            path + ".executable_sha256",
        )
        expect(
            value.get("executable_sha256_is_policy_input"),
            False,
            path + ".executable_sha256_is_policy_input",
        )
        expect(
            value.get("runtime_version"),
            identity["runtime_version"],
            path + ".runtime_version",
        )
        expect(
            value.get("runtime_implementation"),
            identity["runtime_implementation"],
            path + ".runtime_implementation",
        )

    packet_keys = {
        "schema",
        "status",
        "reason",
        "external_system",
        "kernel_membership",
        "fixture_path",
        "fixture_sha256",
        "canonical_fixture_sha256",
        "controller_sha256",
        "elapsed_seconds",
        "promotion_allowed",
        "engine_readiness_claim",
        "cr_truth_claim",
        "claim_ceiling",
        "runtime_pins",
        "integration",
        "rows",
    }
    if exact_keys(receipt, "$", packet_keys) is None:
        return tuple(errors)
    expect(receipt.get("schema"), PACKET_SCHEMA, "$.schema")
    expect(receipt.get("status"), "PASS", "$.status")
    expect(
        receipt.get("reason"),
        "all_component_and_integration_checks_passed",
        "$.reason",
    )
    expect(receipt.get("external_system"), True, "$.external_system")
    expect(
        receipt.get("kernel_membership"),
        "EXTERNAL_NOT_CB_KERNEL",
        "$.kernel_membership",
    )
    expect(receipt.get("promotion_allowed"), False, "$.promotion_allowed")
    expect(
        receipt.get("engine_readiness_claim"),
        False,
        "$.engine_readiness_claim",
    )
    expect(receipt.get("cr_truth_claim"), False, "$.cr_truth_claim")
    expect(receipt.get("claim_ceiling"), EXTERNAL_BOUNDARY, "$.claim_ceiling")
    validate_elapsed(receipt.get("elapsed_seconds"), "$.elapsed_seconds")
    expect(
        receipt.get("runtime_pins"),
        {
            family: _runtime_pin_dict(family)
            for family in ("python", "julia")
        },
        "$.runtime_pins",
    )

    broker = ExternalEnginePacketBroker()
    try:
        fixture, canonical_fixture, fixture_digest = broker._load_fixture()
    except (OSError, ExternalPacketError) as exc:
        error("$.fixture", f"current_fixture_invalid={exc}")
        return tuple(errors)
    controller_digest = _sha256_file(broker.controller_path)
    expect(receipt.get("fixture_path"), str(broker.fixture_path), "$.fixture_path")
    expect(receipt.get("fixture_sha256"), fixture_digest, "$.fixture_sha256")
    expect(receipt.get("fixture_sha256"), FIXTURE_SHA256, "$.fixture_sha256_pin")
    expect(
        receipt.get("canonical_fixture_sha256"),
        _sha256_bytes(canonical_fixture),
        "$.canonical_fixture_sha256",
    )
    expect(
        receipt.get("controller_sha256"),
        controller_digest,
        "$.controller_sha256",
    )

    row_keys = {
        "schema",
        "engine_id",
        "external_system",
        "kernel_membership",
        "exact_api",
        "fixture_sha256",
        "input_sha256",
        "controller_sha256",
        "promotion_allowed",
        "engine_readiness_claim",
        "cr_truth_claim",
        "claim_ceiling",
        "runtime_pin",
        "command",
        "worker_source_sha256",
        "worker_source_sha256_expected",
        "executable_path",
        "executable_resolved_path",
        "executable_sha256",
        "executable_sha256_is_policy_input",
        "runtime_version",
        "runtime_implementation",
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
    }
    observed_keys = {
        "jax_autodiff": {"derivatives", "boundary_derivative"},
        "pytorch_jacobian": {"jacobian", "boundary_jacobian"},
        "pysindy_identification": {
            "coefficient",
            "heldout_derivatives",
            "boundary_derivative",
        },
        "julia_diffeq": {"terminal", "boundary_terminal"},
    }
    runtime_keys = {
        "jax_autodiff": {
            "package_version",
            "x64",
            "device",
            "platform",
        },
        "pytorch_jacobian": {"package_version", "dtype", "device"},
        "pysindy_identification": {
            "package_version",
            "numpy_version",
            "feature_library",
            "optimizer",
        },
        "julia_diffeq": {
            "julia_version",
            "package_version",
            "active_project",
            "load_path",
        },
    }
    rows_value = receipt.get("rows")
    rows: list[dict[str, Any]] = []
    expected_engine_ids = list(EXACT_APIS)
    if not isinstance(rows_value, list):
        error("$.rows", "not_array")
    else:
        observed_ids = [
            row.get("engine_id") if isinstance(row, dict) else None
            for row in rows_value
        ]
        expect(observed_ids, expected_engine_ids, "$.rows.engine_ids")
        for index, raw_row in enumerate(rows_value):
            path = f"$.rows[{index}]"
            row = exact_keys(raw_row, path, row_keys)
            if row is None:
                continue
            rows.append(row)
            engine_id = row.get("engine_id")
            if engine_id not in EXACT_APIS:
                error(path + ".engine_id", "unknown")
                continue
            family = "julia" if engine_id == "julia_diffeq" else "python"
            worker = (
                broker.julia_worker
                if family == "julia"
                else broker.python_worker
            )
            expect(row.get("schema"), ROW_SCHEMA, path + ".schema")
            expect(row.get("status"), "PASS", path + ".status")
            expect(
                row.get("reason"),
                "exact_operation_controls_passed",
                path + ".reason",
            )
            expect(row.get("external_system"), True, path + ".external_system")
            expect(
                row.get("kernel_membership"),
                "EXTERNAL_NOT_CB_KERNEL",
                path + ".kernel_membership",
            )
            expect(row.get("exact_api"), EXACT_APIS[engine_id], path + ".exact_api")
            expect(row.get("fixture_sha256"), fixture_digest, path + ".fixture_sha256")
            expect(
                row.get("controller_sha256"),
                controller_digest,
                path + ".controller_sha256",
            )
            expect(row.get("promotion_allowed"), False, path + ".promotion_allowed")
            expect(
                row.get("engine_readiness_claim"),
                False,
                path + ".engine_readiness_claim",
            )
            expect(row.get("cr_truth_claim"), False, path + ".cr_truth_claim")
            expect(row.get("claim_ceiling"), EXTERNAL_BOUNDARY, path + ".claim_ceiling")
            validate_runtime(row, path, family)
            expected_command = broker._command(engine_id)[0]
            expect(row.get("command"), expected_command, path + ".command")
            expected_worker_digest = WORKER_SHA256[family]
            try:
                current_worker_digest = _sha256_file(worker)
            except OSError:
                error(path + ".worker_source_sha256", "current_worker_missing")
                current_worker_digest = None
            expect(
                current_worker_digest,
                expected_worker_digest,
                path + ".worker_source_current_pin",
            )
            expect(
                row.get("worker_source_sha256"),
                expected_worker_digest,
                path + ".worker_source_sha256",
            )
            expect(
                row.get("worker_source_sha256_expected"),
                expected_worker_digest,
                path + ".worker_source_sha256_expected",
            )
            transport = {
                "schema": INPUT_SCHEMA,
                "engine_id": engine_id,
                "case": fixture[CASE_KEYS[engine_id]],
            }
            expect(
                row.get("input_sha256"),
                _sha256_bytes(canonical_json(transport)),
                path + ".input_sha256",
            )
            validate_elapsed(row.get("elapsed_seconds"), path + ".elapsed_seconds")
            expect(row.get("returncode"), 0, path + ".returncode")
            for name in ("stdout_sha256", "stderr_sha256", "output_sha256"):
                validate_digest(row.get(name), path + "." + name)
            worker_pid = row.get("worker_pid")
            if (
                isinstance(worker_pid, bool)
                or not isinstance(worker_pid, int)
                or worker_pid <= 0
            ):
                error(path + ".worker_pid", "invalid")
            observed = exact_keys(
                row.get("observed"),
                path + ".observed",
                observed_keys[engine_id],
            )
            runtime = exact_keys(
                row.get("runtime"),
                path + ".runtime",
                runtime_keys[engine_id],
            )
            if observed is None or runtime is None:
                continue
            if engine_id == "jax_autodiff":
                expect(runtime.get("x64"), True, path + ".runtime.x64")
            elif engine_id == "pytorch_jacobian":
                expect(runtime.get("dtype"), "torch.float64", path + ".runtime.dtype")
                expect(runtime.get("device"), "cpu", path + ".runtime.device")
            elif engine_id == "pysindy_identification":
                expect(
                    runtime.get("feature_library"),
                    "PolynomialLibrary(degree=1,include_bias=False)",
                    path + ".runtime.feature_library",
                )
                expect(
                    runtime.get("optimizer"),
                    "STLSQ(threshold=0.0,alpha=1e-12)",
                    path + ".runtime.optimizer",
                )
            witness = {
                "schema": "constraintbox.external-engine-witness.v1",
                "engine_id": engine_id,
                "exact_api": EXACT_APIS[engine_id],
                "observed": observed,
                "runtime": runtime,
                "pid": worker_pid,
            }
            expect(
                row.get("output_sha256"),
                _sha256_bytes(canonical_json(witness)),
                path + ".output_sha256_binding",
            )
            evaluation = evaluate_worker_output(
                engine_id,
                fixture,
                witness,
                julia_project=broker.julia_project,
            )
            expect(
                row.get("controller_evaluation"),
                evaluation,
                path + ".controller_evaluation",
            )
            expect(row.get("controls"), evaluation["controls"], path + ".controls")
            controls = row.get("controls")
            if (
                not isinstance(controls, dict)
                or not controls
                or not all(value is True for value in controls.values())
                or evaluation["errors"]
            ):
                error(path + ".controls", "not_all_true")

    by_engine = {
        row.get("engine_id"): row
        for row in rows
        if isinstance(row.get("engine_id"), str)
    }
    integration_keys = {
        "schema",
        "integration_id",
        "external_system",
        "kernel_membership",
        "producer_engine_id",
        "consumer_engine_id",
        "exact_api",
        "fixture_sha256",
        "controller_sha256",
        "promotion_allowed",
        "engine_readiness_claim",
        "cr_truth_claim",
        "claim_ceiling",
        "runtime_pin",
        "artifact",
        "artifact_sha256",
        "handoff_rejection_evidence",
        "input_sha256",
        "command",
        "worker_source_sha256",
        "worker_source_sha256_expected",
        "executable_path",
        "executable_resolved_path",
        "executable_sha256",
        "executable_sha256_is_policy_input",
        "runtime_version",
        "runtime_implementation",
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
    }
    integration = exact_keys(
        receipt.get("integration"), "$.integration", integration_keys
    )
    producer = by_engine.get("pysindy_identification")
    if integration is not None:
        path = "$.integration"
        fixed_values = {
            "schema": INTEGRATION_SCHEMA,
            "integration_id": INTEGRATION_ID,
            "external_system": True,
            "kernel_membership": "EXTERNAL_NOT_CB_KERNEL",
            "producer_engine_id": "pysindy_identification",
            "consumer_engine_id": "julia_diffeq",
            "exact_api": {
                "producer": EXACT_APIS["pysindy_identification"],
                "consumer": INTEGRATION_APIS,
            },
            "fixture_sha256": fixture_digest,
            "controller_sha256": controller_digest,
            "promotion_allowed": False,
            "engine_readiness_claim": False,
            "cr_truth_claim": False,
            "claim_ceiling": EXTERNAL_BOUNDARY,
            "status": "PASS",
            "reason": "pysindy_artifact_consumed_by_julia",
        }
        for name, expected in fixed_values.items():
            expect(integration.get(name), expected, path + "." + name)
        validate_runtime(integration, path, "julia")
        expect(
            integration.get("command"),
            broker._command("julia_diffeq")[0],
            path + ".command",
        )
        expect(
            integration.get("worker_source_sha256"),
            WORKER_SHA256["julia"],
            path + ".worker_source_sha256",
        )
        expect(
            integration.get("worker_source_sha256_expected"),
            WORKER_SHA256["julia"],
            path + ".worker_source_sha256_expected",
        )
        validate_elapsed(
            integration.get("elapsed_seconds"), path + ".elapsed_seconds"
        )
        expect(integration.get("returncode"), 0, path + ".returncode")
        for name in ("stdout_sha256", "stderr_sha256", "output_sha256"):
            validate_digest(integration.get(name), path + "." + name)
        worker_pid = integration.get("worker_pid")
        if (
            isinstance(worker_pid, bool)
            or not isinstance(worker_pid, int)
            or worker_pid <= 0
        ):
            error(path + ".worker_pid", "invalid")
        artifact = integration.get("artifact")
        artifact_bytes: bytes | None = None
        if not isinstance(artifact, dict):
            error(path + ".artifact", "not_object")
        elif producer is None:
            error(path + ".artifact", "producer_row_missing")
        else:
            try:
                expected_artifact_bytes = build_identified_rate_artifact(producer)
                artifact_bytes = canonical_json(artifact)
                if artifact_bytes != expected_artifact_bytes:
                    error(path + ".artifact", "producer_binding_mismatch")
            except (ExternalPacketError, ValueError, TypeError) as exc:
                error(path + ".artifact", f"invalid={exc}")
        if artifact_bytes is not None and producer is not None:
            artifact_sha256 = _sha256_bytes(artifact_bytes)
            expect(
                integration.get("artifact_sha256"),
                artifact_sha256,
                path + ".artifact_sha256",
            )
            accepted = validate_handoff_artifact(
                artifact_bytes,
                expected_sha256=artifact_sha256,
                expected_producer_output_sha256=producer["output_sha256"],
            )
            removal = validate_handoff_artifact(
                None,
                expected_sha256=artifact_sha256,
                expected_producer_output_sha256=producer["output_sha256"],
            )
            digest_mutation = validate_handoff_artifact(
                artifact_bytes + b" ",
                expected_sha256=artifact_sha256,
                expected_producer_output_sha256=producer["output_sha256"],
            )
            substituted_artifact = dict(artifact)
            try:
                identified_rate = _number(
                    artifact.get("identified_rate"),
                    "$.integration.artifact.identified_rate",
                )
            except ExternalPacketError:
                identified_rate = 0.0
                error(path + ".artifact.identified_rate", "invalid")
            substituted_artifact["identified_rate"] = (
                -identified_rate if abs(identified_rate) > 1e-15 else 1.0
            )
            wrong_rate = validate_handoff_artifact(
                canonical_json(substituted_artifact),
                expected_sha256=artifact_sha256,
                expected_producer_output_sha256=producer["output_sha256"],
            )
            rejection_evidence = {
                "removal": removal,
                "digest_mutation": digest_mutation,
                "wrong_rate_substitution": wrong_rate,
            }
            expect(
                integration.get("handoff_rejection_evidence"),
                rejection_evidence,
                path + ".handoff_rejection_evidence",
            )
            preflight_controls = {
                "producer_passed": producer.get("status") == "PASS",
                "artifact_canonical": bool(accepted["accepted"]),
                "removal_rejected": (
                    not removal["accepted"]
                    and removal["reason"] == "artifact_missing"
                ),
                "digest_mutation_rejected": (
                    not digest_mutation["accepted"]
                    and digest_mutation["reason"] == "artifact_digest_mismatch"
                ),
                "wrong_rate_substitution_rejected": (
                    not wrong_rate["accepted"]
                    and wrong_rate["reason"] == "artifact_digest_mismatch"
                ),
            }
            transport = {
                "schema": "constraintbox.external-engine-handoff-input.v1",
                "engine_id": INTEGRATION_ID,
                "artifact_json": artifact_bytes.decode("utf-8"),
                "artifact_sha256": artifact_sha256,
                "case": {
                    "initial": fixture["julia"]["initial"],
                    "duration": fixture["julia"]["duration"],
                },
            }
            expect(
                integration.get("input_sha256"),
                _sha256_bytes(canonical_json(transport)),
                path + ".input_sha256",
            )
            observed = exact_keys(
                integration.get("observed"),
                path + ".observed",
                {"terminal", "consumed_rate", "artifact_sha256"},
            )
            runtime = exact_keys(
                integration.get("runtime"),
                path + ".runtime",
                runtime_keys["julia_diffeq"],
            )
            if observed is not None and runtime is not None:
                integration_witness = {
                    "schema": (
                        "constraintbox.external-engine-integration-witness.v1"
                    ),
                    "integration_id": INTEGRATION_ID,
                    "exact_api": INTEGRATION_APIS,
                    "observed": observed,
                    "runtime": runtime,
                    "pid": worker_pid,
                }
                expect(
                    integration.get("output_sha256"),
                    _sha256_bytes(canonical_json(integration_witness)),
                    path + ".output_sha256_binding",
                )
                initial = float(fixture["julia"]["initial"])
                duration = float(fixture["julia"]["duration"])
                expected_terminal = initial * math.exp(
                    identified_rate * duration
                )
                terminal_check = _comparison(
                    observed.get("terminal"), expected_terminal, 5e-8
                )
                rate_check = _comparison(
                    observed.get("consumed_rate"), identified_rate, 1e-12
                )
                artifact_check = (
                    observed.get("artifact_sha256") == artifact_sha256
                )
                expected_project = (
                    broker.julia_project / "Project.toml"
                ).resolve()
                try:
                    active_project = Path(
                        runtime.get("active_project", "")
                    ).resolve()
                except (OSError, TypeError):
                    active_project = Path("")
                strict_carrier = (
                    active_project == expected_project
                    and runtime.get("load_path") == ["@", "@stdlib"]
                )
                expected_controls = preflight_controls | {
                    "artifact_digest_bound": artifact_check,
                    "consumer_used_identified_rate": bool(rate_check["pass"]),
                    "positive": bool(terminal_check["pass"]),
                    "strict_carrier": strict_carrier,
                    "separate_process": (
                        isinstance(worker_pid, int)
                        and not isinstance(worker_pid, bool)
                        and worker_pid > 0
                    ),
                }
                expected_evaluation = {
                    "expected": {
                        "identified_rate": identified_rate,
                        "terminal": expected_terminal,
                    },
                    "comparisons": {
                        "consumed_rate": rate_check,
                        "terminal": terminal_check,
                        "artifact_sha256_match": artifact_check,
                    },
                    "strict_carrier": {
                        "pass": strict_carrier,
                        "expected_project": str(expected_project),
                        "observed_project": runtime.get("active_project"),
                        "observed_load_path": runtime.get("load_path"),
                    },
                    "errors": [],
                }
                expect(
                    integration.get("controls"),
                    expected_controls,
                    path + ".controls",
                )
                expect(
                    integration.get("controller_evaluation"),
                    expected_evaluation,
                    path + ".controller_evaluation",
                )
                if not all(value is True for value in expected_controls.values()):
                    error(path + ".controls", "not_all_true")

    return tuple(dict.fromkeys(errors))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run the controller-selected external basic engine packet."
    )
    parser.add_argument("--timeout", type=float, default=180.0)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    broker = ExternalEnginePacketBroker(
        timeout_seconds=args.timeout,
    )
    receipt = broker.run()
    encoded = canonical_json(receipt) + b"\n"
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_bytes(encoded)
    else:
        sys.stdout.buffer.write(encoded)
    return {"PASS": 0, "FAIL": 1, "PARKED": 4}[receipt["status"]]


if __name__ == "__main__":
    raise SystemExit(main())
