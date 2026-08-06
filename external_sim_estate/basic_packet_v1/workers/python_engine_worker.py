from __future__ import annotations

import importlib.metadata
import json
import os
import re
import sys
from typing import Any, Callable


class ExactFunctionUnavailable(RuntimeError):
    pass


_SAFE_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}")
_LOWER_SHA256 = re.compile(r"[0-9a-f]{64}")
_EXECUTION_BINDING_KEYS = {
    "schema",
    "capability_id",
    "run_id",
    "flow_policy_sha256",
    "request_sha256",
    "step_id",
    "challenge_seed_hex",
}


def _validate_execution_binding(value: object) -> dict[str, str]:
    if not isinstance(value, dict) or set(value) != _EXECUTION_BINDING_KEYS:
        raise ValueError("execution binding keys mismatch")
    if value.get("schema") != "constraintbox.external-capability-binding.v1":
        raise ValueError("execution binding schema mismatch")
    for key in ("capability_id", "run_id", "step_id"):
        item = value.get(key)
        if not isinstance(item, str) or _SAFE_ID.fullmatch(item) is None:
            raise ValueError(f"execution binding {key} is invalid")
    for key in (
        "flow_policy_sha256",
        "request_sha256",
        "challenge_seed_hex",
    ):
        item = value.get(key)
        if not isinstance(item, str) or _LOWER_SHA256.fullmatch(item) is None:
            raise ValueError(f"execution binding {key} is invalid")
    return {key: value[key] for key in sorted(_EXECUTION_BINDING_KEYS)}


def _canonical_emit(value: dict[str, Any]) -> None:
    print(
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        )
    )


def _require_attr(owner: object, name: str, qualified_name: str) -> Any:
    value = getattr(owner, name, None)
    if value is None:
        raise ExactFunctionUnavailable(f"{qualified_name} is unavailable")
    return value


def _jax(case: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    try:
        import jax
    except (ImportError, ModuleNotFoundError) as exc:
        raise ExactFunctionUnavailable(f"jax import failed: {exc}") from exc

    jax.config.update("jax_enable_x64", True)
    import jax.numpy as jnp

    jit: Callable[..., Any] = _require_attr(jax, "jit", "jax.jit")
    grad: Callable[..., Any] = _require_attr(jax, "grad", "jax.grad")
    vmap: Callable[..., Any] = _require_attr(jax, "vmap", "jax.vmap")
    cubic = float(case["cubic"])
    linear = float(case["linear"])

    def scalar_function(x: Any) -> Any:
        return cubic * x**3 + linear * x

    differentiated = grad(scalar_function)
    batched = vmap(differentiated)
    compiled = jit(batched)
    points = jnp.asarray(case["points"], dtype=jnp.float64)
    boundary = jnp.asarray([case["boundary_point"]], dtype=jnp.float64)
    derivatives = compiled(points)
    boundary_derivative = compiled(boundary)
    observed = {
        "derivatives": [float(value) for value in derivatives.tolist()],
        "boundary_derivative": float(boundary_derivative[0]),
    }
    runtime = {
        "package_version": importlib.metadata.version("jax"),
        "x64": bool(jax.config.jax_enable_x64),
        "device": str(points.device),
        "platform": getattr(points.device, "platform", None),
    }
    return observed, runtime


def _pytorch(case: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    try:
        import torch
    except (ImportError, ModuleNotFoundError) as exc:
        raise ExactFunctionUnavailable(f"torch import failed: {exc}") from exc

    func = _require_attr(torch, "func", "torch.func")
    jacrev: Callable[..., Any] = _require_attr(
        func, "jacrev", "torch.func.jacrev"
    )
    torch.set_default_dtype(torch.float64)
    alpha = float(case["alpha"])
    beta = float(case["beta"])

    def vector_function(x: Any) -> Any:
        return torch.stack(
            (
                alpha * x[0] ** 2 + beta * x[1],
                x[0] * x[1],
            )
        )

    differentiated = jacrev(vector_function)
    point = torch.tensor(case["point"], dtype=torch.float64, device="cpu")
    boundary = torch.tensor(
        case["boundary_point"], dtype=torch.float64, device="cpu"
    )
    jacobian = differentiated(point)
    boundary_jacobian = differentiated(boundary)
    observed = {
        "jacobian": [
            [float(value) for value in row]
            for row in jacobian.detach().cpu().tolist()
        ],
        "boundary_jacobian": [
            [float(value) for value in row]
            for row in boundary_jacobian.detach().cpu().tolist()
        ],
    }
    runtime = {
        "package_version": importlib.metadata.version("torch"),
        "dtype": str(point.dtype),
        "device": str(point.device),
    }
    return observed, runtime


def _pysindy(case: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    try:
        import numpy as np
        import pysindy as ps
    except (ImportError, ModuleNotFoundError) as exc:
        raise ExactFunctionUnavailable(f"pysindy import failed: {exc}") from exc

    polynomial_library = _require_attr(
        ps, "PolynomialLibrary", "pysindy.PolynomialLibrary"
    )
    stlsq = _require_attr(ps, "STLSQ", "pysindy.STLSQ")
    sindy = _require_attr(ps, "SINDy", "pysindy.SINDy")
    _require_attr(sindy, "fit", "pysindy.SINDy.fit")
    _require_attr(sindy, "predict", "pysindy.SINDy.predict")

    rate = float(case["rate"])
    states = np.asarray(case["train_states"], dtype=np.float64).reshape(-1, 1)
    derivatives = rate * states
    library = polynomial_library(degree=1, include_bias=False)
    optimizer = stlsq(threshold=0.0, alpha=1e-12)
    model = sindy(feature_library=library, optimizer=optimizer)
    model.fit(states, t=1.0, x_dot=derivatives)

    heldout = np.asarray(case["heldout_states"], dtype=np.float64).reshape(-1, 1)
    prediction = np.asarray(model.predict(heldout), dtype=np.float64).reshape(-1)
    coefficient = float(np.asarray(model.coefficients())[0, 0])
    boundary = np.asarray([[case["boundary_state"]]], dtype=np.float64)
    boundary_prediction = float(
        np.asarray(model.predict(boundary), dtype=np.float64).reshape(-1)[0]
    )
    observed = {
        "coefficient": coefficient,
        "heldout_derivatives": [float(value) for value in prediction],
        "boundary_derivative": boundary_prediction,
    }
    runtime = {
        "package_version": importlib.metadata.version("pysindy"),
        "numpy_version": importlib.metadata.version("numpy"),
        "feature_library": "PolynomialLibrary(degree=1,include_bias=False)",
        "optimizer": "STLSQ(threshold=0.0,alpha=1e-12)",
    }
    return observed, runtime


EXACT_APIS = {
    "jax_autodiff": ["jax.grad", "jax.vmap", "jax.jit"],
    "pytorch_jacobian": ["torch.func.jacrev"],
    "pysindy_identification": ["pysindy.SINDy.fit", "pysindy.SINDy.predict"],
}


def main() -> int:
    if len(sys.argv) != 2 or sys.argv[1] not in EXACT_APIS:
        raise SystemExit(
            "usage: python_engine_worker.py "
            "{jax_autodiff|pytorch_jacobian|pysindy_identification}"
        )
    engine_id = sys.argv[1]
    raw = sys.stdin.buffer.read()
    request = json.loads(raw.decode("utf-8"))
    if request.get("schema") != "constraintbox.external-engine-input.v1":
        raise ValueError("unsupported worker input schema")
    if request.get("engine_id") != engine_id:
        raise ValueError("worker input engine_id mismatch")
    expected_request_keys = {"schema", "engine_id", "case"}
    execution_binding = None
    if "execution_binding" in request:
        expected_request_keys.add("execution_binding")
        execution_binding = _validate_execution_binding(
            request["execution_binding"]
        )
    if set(request) != expected_request_keys:
        raise ValueError("worker input keys mismatch")

    operation = {
        "jax_autodiff": _jax,
        "pytorch_jacobian": _pytorch,
        "pysindy_identification": _pysindy,
    }[engine_id]
    try:
        observed, runtime = operation(request["case"])
    except ExactFunctionUnavailable as exc:
        unavailable = {
            "schema": "constraintbox.external-engine-unavailable.v1",
            "engine_id": engine_id,
            "exact_api": EXACT_APIS[engine_id],
            "reason": str(exc),
            "pid": os.getpid(),
        }
        if execution_binding is not None:
            unavailable["execution_binding"] = execution_binding
        _canonical_emit(unavailable)
        return 3

    witness = {
        "schema": "constraintbox.external-engine-witness.v1",
        "engine_id": engine_id,
        "exact_api": EXACT_APIS[engine_id],
        "observed": observed,
        "runtime": runtime,
        "pid": os.getpid(),
    }
    if execution_binding is not None:
        witness["execution_binding"] = execution_binding
    _canonical_emit(witness)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
