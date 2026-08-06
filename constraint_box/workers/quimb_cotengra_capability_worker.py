"""Fixed external worker for bounded Quimb and Cotengra capability probes.

This file is deliberately executed as an isolated child process.  It never
decides whether a result is eligible and accepts only controller-created JSON
on stdin.  The parent controller pins this source, the selected interpreter,
the package artifacts, and the environment policy before it treats a witness
as evidence.
"""

from __future__ import annotations

import importlib.metadata
import json
import math
import os
import sys
from typing import Any


REQUEST_SCHEMA = "constraintbox.external-quimb-cotengra-worker-request.v1"
WITNESS_SCHEMA = "constraintbox.external-quimb-cotengra-worker-witness.v1"
POISON_SCHEMA = "constraintbox.external-quimb-cotengra-operation-poison.v1"
QUIMB_PROFILE = "quimb-density-v1"
COTENGRA_PROFILE = "cotengra-triangle-path-v1"
COTENGRA_OPTIMIZER_CONFIG = {
    "max_repeats": 4,
    "progbar": False,
    "parallel": False,
    "minimize": "flops",
    "optlib_opts": {"sampler": "TPESampler", "sampler_opts": {"seed": 0}},
}


class _OperationPoisoned(RuntimeError):
    """Raised only by a controller-selected operation-severance probe."""


def _canonical_json(value: dict[str, Any]) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def _emit(value: dict[str, Any]) -> None:
    sys.stdout.buffer.write(_canonical_json(value) + b"\n")


def _finite(value: object, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{label} must be finite numeric data")
    converted = float(value)
    if not math.isfinite(converted):
        raise ValueError(f"{label} must be finite numeric data")
    return converted


def _matrix(value: object, label: str) -> list[list[float]]:
    if not isinstance(value, list) or len(value) != 2:
        raise ValueError(f"{label} must be a 2 by 2 array")
    rows: list[list[float]] = []
    for row_index, row in enumerate(value):
        if not isinstance(row, list) or len(row) != 2:
            raise ValueError(f"{label}[{row_index}] must have two entries")
        rows.append(
            [_finite(item, f"{label}[{row_index}][{column_index}]") for column_index, item in enumerate(row)]
        )
    return rows


def _request() -> dict[str, Any]:
    raw = sys.stdin.buffer.read()
    try:
        value = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("worker request is not JSON") from exc
    if _canonical_json(value) != raw:
        raise ValueError("worker request is not canonical JSON")
    if not isinstance(value, dict) or set(value) != {
        "schema",
        "profile_id",
        "case",
        "execution_binding",
        "environment_policy_sha256",
    }:
        raise ValueError("worker request fields differ")
    if value["schema"] != REQUEST_SCHEMA:
        raise ValueError("worker request schema mismatch")
    if value["profile_id"] not in {QUIMB_PROFILE, COTENGRA_PROFILE}:
        raise ValueError("worker request profile is not fixed")
    if not isinstance(value["case"], dict):
        raise ValueError("worker request case is not an object")
    if not isinstance(value["execution_binding"], dict):
        raise ValueError("worker request binding is not an object")
    policy_digest = value["environment_policy_sha256"]
    if not isinstance(policy_digest, str) or len(policy_digest) != 64:
        raise ValueError("worker environment policy digest is invalid")
    return value


def _environment() -> dict[str, str | None]:
    return {
        "PATH": os.environ.get("PATH"),
        "HOME": os.environ.get("HOME"),
        "NUMBA_CACHE_DIR": os.environ.get("NUMBA_CACHE_DIR"),
        "MPLCONFIGDIR": os.environ.get("MPLCONFIGDIR"),
        "PYTHONHASHSEED": os.environ.get("PYTHONHASHSEED"),
        "PYTHONPATH": os.environ.get("PYTHONPATH"),
        "PYTHONHOME": os.environ.get("PYTHONHOME"),
    }


def _quimb_observed(case: dict[str, Any]) -> tuple[dict[str, Any], tuple[str, ...]]:
    if set(case) != {"rho", "boundary_rho"}:
        raise ValueError("Quimb case fields differ")
    rho_values = _matrix(case["rho"], "$.rho")
    boundary_values = _matrix(case["boundary_rho"], "$.boundary_rho")
    import quimb as qu

    rho = qu.qarray(rho_values)
    boundary_rho = qu.qarray(boundary_values)
    observed = {
        "eigenvalues": sorted(float(item) for item in qu.eigvalsh(rho)),
        "trace": float(qu.trace(rho)),
        "boundary_eigenvalues": sorted(
            float(item) for item in qu.eigvalsh(boundary_rho)
        ),
        "boundary_trace": float(qu.trace(boundary_rho)),
    }
    return observed, ("quimb.qarray", "quimb.eigvalsh", "quimb.trace")


def _cotengra_tree(inputs: list[tuple[int, ...]], sizes: dict[int, int]):
    import cotengra as ctg

    optimizer = ctg.HyperOptimizer(**COTENGRA_OPTIMIZER_CONFIG)
    return optimizer.search(inputs, (), sizes)


def _cotengra_observed(case: dict[str, Any]) -> tuple[dict[str, Any], tuple[str, ...]]:
    if set(case) != {"inputs", "sizes", "boundary_sizes"}:
        raise ValueError("Cotengra case fields differ")
    raw_inputs = case["inputs"]
    if raw_inputs != [[0, 1], [1, 2], [2, 0]]:
        raise ValueError("Cotengra case inputs differ from the fixed triangle")
    inputs = [tuple(item) for item in raw_inputs]

    def sizes_from(value: object, label: str) -> dict[int, int]:
        if not isinstance(value, dict) or set(value) != {"0", "1", "2"}:
            raise ValueError(f"{label} fields differ")
        parsed: dict[int, int] = {}
        for key in ("0", "1", "2"):
            item = value[key]
            if isinstance(item, bool) or not isinstance(item, int) or item < 1 or item > 2:
                raise ValueError(f"{label}.{key} must be one of the fixed dimensions")
            parsed[int(key)] = item
        return parsed

    sizes = sizes_from(case["sizes"], "$.sizes")
    boundary_sizes = sizes_from(case["boundary_sizes"], "$.boundary_sizes")
    tree = _cotengra_tree(inputs, sizes)
    boundary_tree = _cotengra_tree(inputs, boundary_sizes)
    observed = {
        "contraction_cost": int(tree.contraction_cost()),
        "max_size": int(tree.max_size()),
        "boundary_contraction_cost": int(boundary_tree.contraction_cost()),
        "boundary_max_size": int(boundary_tree.max_size()),
    }
    return observed, ("cotengra.HyperOptimizer", "cotengra.HyperOptimizer.search")


def _poisoned_witness(
    *,
    request: dict[str, Any],
    exact_api: tuple[str, ...],
    poisoned_api: str,
) -> None:
    _emit(
        {
            "schema": POISON_SCHEMA,
            "profile_id": request["profile_id"],
            "exact_api": list(exact_api),
            "poisoned_api": poisoned_api,
            "pid": os.getpid(),
            "execution_binding": request["execution_binding"],
            "environment_policy_sha256": request["environment_policy_sha256"],
            "environment": _environment(),
        }
    )


def _run_quimb(request: dict[str, Any]) -> None:
    poison = os.environ.get("CONSTRAINTBOX_OPERATION_POISON")
    if poison is not None and poison not in {"quimb.eigvalsh", "quimb.trace"}:
        raise ValueError("unexpected Quimb poison selector")
    if poison is not None:
        import quimb as qu

        if poison == "quimb.eigvalsh":
            qu.eigvalsh = lambda *_args, **_kwargs: (_ for _ in ()).throw(_OperationPoisoned())
        else:
            qu.trace = lambda *_args, **_kwargs: (_ for _ in ()).throw(_OperationPoisoned())
        try:
            _quimb_observed(request["case"])
        except _OperationPoisoned:
            _poisoned_witness(
                request=request,
                exact_api=("quimb.qarray", "quimb.eigvalsh", "quimb.trace"),
                poisoned_api=poison,
            )
            return
        raise RuntimeError("poisoned Quimb API was not exercised")
    observed, exact_api = _quimb_observed(request["case"])
    _emit(
        {
            "schema": WITNESS_SCHEMA,
            "profile_id": QUIMB_PROFILE,
            "exact_api": list(exact_api),
            "observed": observed,
            "runtime": {"package_version": importlib.metadata.version("quimb")},
            "pid": os.getpid(),
            "execution_binding": request["execution_binding"],
            "environment_policy_sha256": request["environment_policy_sha256"],
            "environment": _environment(),
        }
    )


def _run_cotengra(request: dict[str, Any]) -> None:
    poison = os.environ.get("CONSTRAINTBOX_OPERATION_POISON")
    if poison is not None and poison != "cotengra.HyperOptimizer.search":
        raise ValueError("unexpected Cotengra poison selector")
    if poison is not None:
        import cotengra as ctg

        ctg.HyperOptimizer.search = lambda *_args, **_kwargs: (_ for _ in ()).throw(_OperationPoisoned())
        try:
            _cotengra_observed(request["case"])
        except _OperationPoisoned:
            _poisoned_witness(
                request=request,
                exact_api=("cotengra.HyperOptimizer", "cotengra.HyperOptimizer.search"),
                poisoned_api=poison,
            )
            return
        raise RuntimeError("poisoned Cotengra API was not exercised")
    observed, exact_api = _cotengra_observed(request["case"])
    _emit(
        {
            "schema": WITNESS_SCHEMA,
            "profile_id": COTENGRA_PROFILE,
            "exact_api": list(exact_api),
            "observed": observed,
            "runtime": {
                "package_version": importlib.metadata.version("cotengra"),
                "optimizer_config": COTENGRA_OPTIMIZER_CONFIG,
            },
            "pid": os.getpid(),
            "execution_binding": request["execution_binding"],
            "environment_policy_sha256": request["environment_policy_sha256"],
            "environment": _environment(),
        }
    )


def main() -> None:
    request = _request()
    if request["profile_id"] == QUIMB_PROFILE:
        _run_quimb(request)
    else:
        _run_cotengra(request)


if __name__ == "__main__":
    main()
