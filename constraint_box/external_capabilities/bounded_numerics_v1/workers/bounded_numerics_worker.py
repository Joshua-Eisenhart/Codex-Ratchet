"""Isolated workers for two fixed, controller-owned numeric capabilities.

This file is deliberately outside ``constraintbox``. It accepts only a typed,
controller-derived case, performs exactly the named library operation, and
emits a canonical witness. It does not decide eligibility, retry, release, or
promotion.
"""

from __future__ import annotations

import importlib.metadata
import json
import math
import os
import sys
from pathlib import Path
from typing import Any


INPUT_SCHEMA = "constraintbox.bounded-numerics-input.v1"
WITNESS_SCHEMA = "constraintbox.bounded-numerics-witness.v1"
BINDING_SCHEMA = "constraintbox.external-capability-binding.v1"
SEVERED_EXIT_CODE = 86
SEVERED_PREFIX = "constraintbox.bounded-numerics.operation-severed.v1:"
_SHA256_HEX = set("0123456789abcdef")
_SAFE_ID = set("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789._-")

EXACT_APIS = {
    "scipy_expm_rotation": ["scipy.linalg.expm"],
    "diffrax_tsit5_affine": [
        "diffrax.ODETerm",
        "diffrax.Tsit5",
        "diffrax.PIDController",
        "diffrax.diffeqsolve",
    ],
}


def _canonical_emit(value: dict[str, Any]) -> None:
    sys.stdout.write(
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        )
        + "\n"
    )
    sys.stdout.flush()


def _finite_number(value: object, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be a finite number")
    converted = float(value)
    if not math.isfinite(converted):
        raise ValueError(f"{name} must be a finite number")
    return converted


def _exact_object(
    value: object, name: str, expected: set[str]
) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != expected:
        raise ValueError(f"{name} keys mismatch")
    return value


def _validate_binding(value: object, profile_id: str) -> dict[str, str]:
    binding = _exact_object(
        value,
        "binding",
        {
            "schema",
            "capability_id",
            "run_id",
            "flow_policy_sha256",
            "request_sha256",
            "step_id",
            "challenge_seed_hex",
        },
    )
    if binding["schema"] != BINDING_SCHEMA:
        raise ValueError("binding schema mismatch")
    if binding["capability_id"] != profile_id:
        raise ValueError("binding capability_id mismatch")
    for name in ("capability_id", "run_id", "step_id"):
        item = binding[name]
        if (
            not isinstance(item, str)
            or not item
            or len(item) > 128
            or any(character not in _SAFE_ID for character in item)
        ):
            raise ValueError(f"binding {name} is invalid")
    for name in ("flow_policy_sha256", "request_sha256", "challenge_seed_hex"):
        item = binding[name]
        if (
            not isinstance(item, str)
            or len(item) != 64
            or any(character not in _SHA256_HEX for character in item)
        ):
            raise ValueError(f"binding {name} is invalid")
    return {name: binding[name] for name in sorted(binding)}


def _operation_poison_wrapper(exact_api: str):
    """Return a replacement that exits only if the named operation is called."""

    def poisoned(*_args: object, **_kwargs: object) -> object:
        sys.stderr.write(SEVERED_PREFIX + exact_api + "\n")
        sys.stderr.flush()
        raise SystemExit(SEVERED_EXIT_CODE)

    return poisoned


def _scipy_expm_rotation(
    case: dict[str, Any]
) -> tuple[dict[str, Any], dict[str, Any]]:
    case = _exact_object(
        case,
        "case",
        {
            "angular_rate",
            "duration",
            "wrong_angular_rate",
            "boundary_duration",
        },
    )
    angular_rate = _finite_number(case["angular_rate"], "angular_rate")
    duration = _finite_number(case["duration"], "duration")
    _finite_number(case["wrong_angular_rate"], "wrong_angular_rate")
    boundary_duration = _finite_number(
        case["boundary_duration"], "boundary_duration"
    )
    if angular_rate == 0.0 or duration == 0.0 or boundary_duration != 0.0:
        raise ValueError("scipy case is not the fixed non-degenerate shape")

    import scipy
    import scipy.linalg

    if os.environ.get("CONSTRAINTBOX_SEVER_OPERATION") == "scipy.linalg.expm":
        scipy.linalg.expm = _operation_poison_wrapper("scipy.linalg.expm")
    expm = scipy.linalg.expm
    if not callable(expm):
        raise RuntimeError("scipy.linalg.expm is unavailable")

    generator = [[0.0, -angular_rate], [angular_rate, 0.0]]
    normal = expm([[duration * value for value in row] for row in generator])
    boundary = expm(
        [[boundary_duration * value for value in row] for row in generator]
    )
    return (
        {
            "matrix": [[float(value) for value in row] for row in normal.tolist()],
            "boundary_matrix": [
                [float(value) for value in row] for row in boundary.tolist()
            ],
        },
        {
            "python_executable_resolved_path": str(Path(sys.executable).resolve()),
            "package_versions": {"scipy": importlib.metadata.version("scipy")},
        },
    )


def _diffrax_tsit5_affine(
    case: dict[str, Any]
) -> tuple[dict[str, Any], dict[str, Any]]:
    case = _exact_object(
        case,
        "case",
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
    rate = _finite_number(case["rate"], "rate")
    initial = _finite_number(case["initial"], "initial")
    duration = _finite_number(case["duration"], "duration")
    _finite_number(case["wrong_rate"], "wrong_rate")
    boundary_rate = _finite_number(case["boundary_rate"], "boundary_rate")
    boundary_initial = _finite_number(
        case["boundary_initial"], "boundary_initial"
    )
    boundary_duration = _finite_number(
        case["boundary_duration"], "boundary_duration"
    )
    if (
        rate == 0.0
        or initial == 0.0
        or duration <= 0.0
        or boundary_rate != 0.0
        or boundary_initial == 0.0
        or boundary_duration <= 0.0
    ):
        raise ValueError("diffrax case is not the fixed non-degenerate shape")

    import jax

    jax.config.update("jax_enable_x64", True)
    import diffrax
    import jax.numpy as jnp

    ode_term = diffrax.ODETerm
    tsit5 = diffrax.Tsit5
    pid_controller = diffrax.PIDController
    if os.environ.get("CONSTRAINTBOX_SEVER_OPERATION") == "diffrax.diffeqsolve":
        diffrax.diffeqsolve = _operation_poison_wrapper("diffrax.diffeqsolve")
    diffeqsolve = diffrax.diffeqsolve
    if not all(
        callable(value) for value in (ode_term, tsit5, pid_controller, diffeqsolve)
    ):
        raise RuntimeError("one required Diffrax API is unavailable")

    def vector_field(_time: object, state: object, args: object) -> object:
        return args * state

    def solve(one_rate: float, one_initial: float, one_duration: float) -> float:
        solution = diffeqsolve(
            ode_term(vector_field),
            tsit5(),
            t0=0.0,
            t1=one_duration,
            dt0=0.02,
            y0=jnp.asarray(one_initial, dtype=jnp.float64),
            args=jnp.asarray(one_rate, dtype=jnp.float64),
            saveat=diffrax.SaveAt(t1=True),
            stepsize_controller=pid_controller(rtol=1e-10, atol=1e-12),
        )
        return float(solution.ys[-1])

    return (
        {
            "terminal": solve(rate, initial, duration),
            "boundary_terminal": solve(
                boundary_rate, boundary_initial, boundary_duration
            ),
        },
        {
            "python_executable_resolved_path": str(Path(sys.executable).resolve()),
            "package_versions": {
                "diffrax": importlib.metadata.version("diffrax"),
                "jax": importlib.metadata.version("jax"),
                "jaxlib": importlib.metadata.version("jaxlib"),
            },
            "x64": bool(jax.config.jax_enable_x64),
            "platform": jax.default_backend(),
        },
    )


def _read_request(profile_id: str) -> tuple[dict[str, Any], dict[str, str]]:
    raw = sys.stdin.buffer.read()
    request = json.loads(raw.decode("utf-8"))
    request = _exact_object(
        request,
        "request",
        {"schema", "profile_id", "case", "binding"},
    )
    if request["schema"] != INPUT_SCHEMA or request["profile_id"] != profile_id:
        raise ValueError("request schema or profile mismatch")
    binding = _validate_binding(request["binding"], profile_id)
    if not isinstance(request["case"], dict):
        raise ValueError("request case is not an object")
    return request["case"], binding


def main() -> int:
    if len(sys.argv) != 2 or sys.argv[1] not in EXACT_APIS:
        raise SystemExit(
            "usage: bounded_numerics_worker.py "
            "{scipy_expm_rotation|diffrax_tsit5_affine}"
        )
    selector = sys.argv[1]
    profile_id = {
        "scipy_expm_rotation": "scipy-expm-rotation-v1",
        "diffrax_tsit5_affine": "diffrax-tsit5-affine-flow-v1",
    }[selector]
    case, binding = _read_request(profile_id)
    operation = {
        "scipy_expm_rotation": _scipy_expm_rotation,
        "diffrax_tsit5_affine": _diffrax_tsit5_affine,
    }[selector]
    observed, runtime = operation(case)
    _canonical_emit(
        {
            "schema": WITNESS_SCHEMA,
            "profile_id": profile_id,
            "exact_api": EXACT_APIS[selector],
            "observed": observed,
            "runtime": runtime,
            "pid": os.getpid(),
            "binding": binding,
        }
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
