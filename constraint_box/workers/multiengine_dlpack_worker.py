"""Fixed canonical-Python child for the external multi-engine diagnostic."""

from __future__ import annotations

import json
import os
import sys


def _reject_constant(value: str):
    raise ValueError(f"non-finite JSON constant: {value}")


def _no_duplicate_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _read_input() -> dict:
    value = json.loads(
        sys.stdin.buffer.read().decode("utf-8"),
        parse_constant=_reject_constant,
        object_pairs_hook=_no_duplicate_object,
    )
    if not isinstance(value, dict) or set(value) != {
        "schema",
        "lane",
        "binding",
        "challenge",
        "input_origin",
    }:
        raise ValueError("worker input keys mismatch")
    if value["schema"] != "constraintbox.multiengine-worker-input.v1":
        raise ValueError("worker input schema mismatch")
    if value["lane"] != "python_dlpack_jax":
        raise ValueError("worker lane mismatch")
    if value["input_origin"] != "controller-derived":
        raise ValueError("worker input origin mismatch")
    if not isinstance(value["binding"], dict) or not isinstance(value["challenge"], dict):
        raise ValueError("worker input requires object binding and challenge")
    return value


class _DLPackCapsuleSource:
    """Expose one real torch.utils.dlpack capsule to current JAX."""

    def __init__(self, capsule, device):
        self._capsule = capsule
        self._device = device

    def __dlpack__(self, stream=None, max_version=None):
        return self._capsule

    def __dlpack_device__(self):
        return self._device


def _as_list(values) -> list[float]:
    return [float(value) for value in values]


def _main() -> None:
    source = _read_input()
    challenge = source["challenge"]
    required = {
        "alpha",
        "beta",
        "gamma",
        "point",
        "boundary_point",
        "wrong_jacobian",
        "severance_shift",
    }
    if set(challenge) != required:
        raise ValueError("Python challenge keys mismatch")
    from jax import config

    config.update("jax_enable_x64", True)
    import jax
    import jax.dlpack as jax_dlpack
    import jax.numpy as jnp
    import jaxlib
    import torch
    from torch.utils import dlpack as torch_dlpack

    alpha = float(challenge["alpha"])
    beta = float(challenge["beta"])
    gamma = float(challenge["gamma"])
    point = torch.tensor(challenge["point"], dtype=torch.float64, device="cpu")
    boundary = torch.tensor(
        challenge["boundary_point"], dtype=torch.float64, device="cpu"
    )

    def torch_function(vector):
        return torch.stack(
            (
                alpha * vector[0] * vector[0] + beta * vector[1],
                vector[0] * vector[1] + gamma,
            )
        )

    jacobian = torch.func.jacrev(torch_function)(point)
    values = torch_function(point)
    boundary_jacobian = torch.func.jacrev(torch_function)(boundary)
    boundary_values = torch_function(boundary)

    def dlpack_to_jax(tensor):
        capsule = torch_dlpack.to_dlpack(tensor)
        source_capsule = _DLPackCapsuleSource(
            capsule, tensor.__dlpack_device__()
        )
        return jax_dlpack.from_dlpack(source_capsule)

    jax_values = dlpack_to_jax(values)
    jax_boundary_values = dlpack_to_jax(boundary_values)

    @jax.jit
    def jitted_vmap(vector):
        return jax.vmap(lambda value: value * value + 0.5 * gamma)(vector)

    jax_output = jitted_vmap(jax_values)
    boundary_jax_output = jitted_vmap(jax_boundary_values)
    severed_jax_output = jitted_vmap(
        jax_values + float(challenge["severance_shift"])
    )
    witness = {
        "schema": "constraintbox.multiengine-python-witness.v1",
        "lane": "python_dlpack_jax",
        "exact_apis": [
            "torch.func.jacrev",
            "torch.utils.dlpack.to_dlpack",
            "jax.dlpack.from_dlpack",
            "jax.jit",
            "jax.vmap",
        ],
        "binding": source["binding"],
        "input_origin": "controller-derived",
        "reads_peer_output": False,
        "pid": os.getpid(),
        "runtime": {
            "python_executable": str(__import__("pathlib").Path(sys.executable).resolve()),
            "torch_version": torch.__version__,
            "jax_version": jax.__version__,
            "jaxlib_version": jaxlib.__version__,
            "torch_dtype": str(values.dtype),
            "jax_dtype": str(jax_values.dtype),
            "device": str(values.device),
        },
        "observed": {
            "torch_values": _as_list(values),
            "jacobian": [_as_list(row) for row in jacobian],
            "jax_values": _as_list(jax_values),
            "jax_output": _as_list(jax_output),
            "boundary_jacobian": [_as_list(row) for row in boundary_jacobian],
            "boundary_jax_output": _as_list(boundary_jax_output),
            "wrong_jacobian": challenge["wrong_jacobian"],
            "severed_jax_output": _as_list(severed_jax_output),
        },
    }
    sys.stdout.write(
        json.dumps(witness, sort_keys=True, separators=(",", ":"), allow_nan=False)
    )
    sys.stdout.write("\n")


if __name__ == "__main__":
    _main()
