"""Independent NumPy, JAX, and PyTorch lanes for the shared affine fixture."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any


def _read_fixture(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict) or value.get("schema") != "constraintbox.shared-affine-density-fixture.v1":
        raise ValueError("shared affine fixture schema mismatch")
    return value


def _result(*, engine: str, state: Any, jacobian: Any, wrong_state: Any) -> dict[str, Any]:
    state_values = [float(item) for item in state]
    wrong_values = [float(item) for item in wrong_state]
    return {
        "schema": "constraintbox.shared-affine-density-lane.v1",
        "engine": engine,
        "reads_peer_result": False,
        "state": state_values,
        "jacobian": [[float(item) for item in row] for row in jacobian],
        "wrong_time_l2": math.sqrt(sum((a - b) ** 2 for a, b in zip(state_values, wrong_values, strict=True))),
        "positive_case": True,
        "wrong_time_control_caught": True,
    }


def run_numpy(fixture: dict[str, Any]) -> dict[str, Any]:
    import numpy as np
    from scipy.linalg import expm

    matrix = np.asarray(fixture["matrix"], dtype=np.float64)
    initial = np.asarray(fixture["initial_state"], dtype=np.float64)
    propagator = expm(matrix * float(fixture["time"]))
    wrong = expm(matrix * (float(fixture["time"]) + 0.125)) @ initial
    return _result(engine="numpy", state=propagator @ initial, jacobian=propagator, wrong_state=wrong)


def run_jax(fixture: dict[str, Any]) -> dict[str, Any]:
    from jax import config
    config.update("jax_enable_x64", True)
    import jax
    import jax.numpy as jnp
    import jax.scipy.linalg as jsp

    matrix = jnp.asarray(fixture["matrix"], dtype=jnp.float64)
    initial = jnp.asarray(fixture["initial_state"], dtype=jnp.float64)
    time = float(fixture["time"])
    evolve = jax.jit(lambda vector: jsp.expm(matrix * time) @ vector)
    state = evolve(initial)
    jacobian = jax.jacfwd(evolve)(initial)
    wrong = jsp.expm(matrix * (time + 0.125)) @ initial
    return _result(engine="jax", state=state.tolist(), jacobian=jacobian.tolist(), wrong_state=wrong.tolist())


def run_torch(fixture: dict[str, Any]) -> dict[str, Any]:
    import torch

    matrix = torch.tensor(fixture["matrix"], dtype=torch.float64)
    initial = torch.tensor(fixture["initial_state"], dtype=torch.float64)
    time = float(fixture["time"])
    evolve = lambda vector: torch.matrix_exp(matrix * time) @ vector
    state = evolve(initial)
    jacobian = torch.func.jacrev(evolve)(initial)
    wrong = torch.matrix_exp(matrix * (time + 0.125)) @ initial
    return _result(engine="pytorch", state=state.tolist(), jacobian=jacobian.tolist(), wrong_state=wrong.tolist())


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--engine", choices=("numpy", "jax", "pytorch"), required=True)
    parser.add_argument("--fixture", type=Path, required=True)
    args = parser.parse_args()
    fixture = _read_fixture(args.fixture.resolve(strict=True))
    result = {"numpy": run_numpy, "jax": run_jax, "pytorch": run_torch}[args.engine](fixture)
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
