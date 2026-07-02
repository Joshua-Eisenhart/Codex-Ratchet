#!/usr/bin/env python3
"""JAX-only radial Dirac inter-leaf coupling scout on 16 Hopf leaves.

Julia is a read-only reference for the object shape. This script does not
import or run Julia, PyTorch, or Torch. It mirrors the finite radial Dirac
inter-leaf coupling test from the Julia carrier:

* 16 interior Hopf leaves theta in (0, pi/2).
* two-component spinor per leaf.
* gamma^theta = sigma_x.
* coupled operator links adjacent leaves only.
* decoupled operator is block diagonal.
* coupled eigenmodes delocalize across leaves; decoupled modes localize.

Claim ceiling: formal scout only. No layer completion, stacking, flux, Axis0,
FEP, physics, or final manifold admission.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from jax import config

config.update("jax_enable_x64", True)

import jax
import jax.numpy as jnp


NLEAF = 16
ONLEAF = 0.3
RESULT = Path("system_v5/ops/formal_scouts/results/jax_radial_dirac_interleaf_coupling_probe_results.json")
RTYPE = jnp.float64

BLOCKED_CONSUMERS = [
    "full_layer_completion",
    "official_g_structure_selection",
    "layer_stacking",
    "layer_stacking_readiness",
    "flux",
    "Xi/Phi0",
    "Axis0",
    "FEP",
    "physics_gravity",
    "final_manifold_admission",
]

TOOL_MANIFEST = {
    "jax": {
        "used": True,
        "role": "load_bearing",
        "reason": "JAX x64 builds the finite radial Dirac operator and computes eigenmode leaf participation.",
    },
    "jax.numpy": {
        "used": True,
        "role": "load_bearing",
        "reason": "Finite matrices, eigensolve, adjacent-coupling and block-diagonal controls.",
    },
}
TOOL_INTEGRATION_DEPTH = {"jax": "load_bearing", "jax.numpy": "load_bearing"}


def jsonable(x: Any) -> Any:
    if hasattr(x, "item"):
        return x.item()
    if isinstance(x, dict):
        return {str(k): jsonable(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [jsonable(v) for v in x]
    return x


def leaf_grid() -> tuple[jax.Array, jax.Array]:
    theta = jnp.linspace(0.0, 0.5 * jnp.pi, NLEAF + 2, dtype=RTYPE)[1:-1]
    return theta, theta[1] - theta[0]


def radial_dirac(couple: bool = True) -> tuple[jax.Array, jax.Array, jax.Array]:
    theta, dtheta = leaf_grid()
    dim = 2 * NLEAF
    sigma_x = jnp.asarray([[0.0, 1.0], [1.0, 0.0]], dtype=RTYPE)
    eye2 = jnp.eye(2, dtype=RTYPE)
    d = jnp.zeros((dim, dim), dtype=RTYPE)
    for k in range(NLEAF):
        sl = slice(2 * k, 2 * k + 2)
        d = d.at[sl, sl].add(ONLEAF * eye2)
    if couple:
        h = 1.0 / dtheta
        for k in range(NLEAF - 1):
            a = slice(2 * k, 2 * k + 2)
            b = slice(2 * (k + 1), 2 * (k + 1) + 2)
            d = d.at[a, b].add(h * sigma_x)
            d = d.at[b, a].add(h * sigma_x)
    return d, theta, dtheta


def offdiag_weight(d: jax.Array) -> jax.Array:
    w = 0.0
    for k in range(NLEAF):
        for l in range(NLEAF):
            if k == l:
                continue
            w = w + jnp.linalg.norm(d[2 * k : 2 * k + 2, 2 * l : 2 * l + 2])
    return w


def nonadjacent_weight(d: jax.Array) -> jax.Array:
    w = 0.0
    for k in range(NLEAF):
        for l in range(NLEAF):
            if abs(k - l) <= 1:
                continue
            w = w + jnp.linalg.norm(d[2 * k : 2 * k + 2, 2 * l : 2 * l + 2])
    return w


def leaf_participation(d: jax.Array) -> jax.Array:
    _, vecs = jnp.linalg.eigh(0.5 * (d + d.T))
    v = vecs.reshape((NLEAF, 2, 2 * NLEAF))
    p = jnp.sum(v * v, axis=1)
    p = p / jnp.sum(p, axis=0, keepdims=True)
    lpr = 1.0 / jnp.sum(p * p, axis=0)
    return jnp.mean(lpr)


@jax.jit
def run_core() -> dict[str, jax.Array]:
    dc, theta, dtheta = radial_dirac(True)
    dd, _, _ = radial_dirac(False)
    area = jnp.sin(2.0 * theta)
    max_area = jnp.max(area)
    peak = jnp.argmax(area)
    clifford_distance = jnp.min(jnp.abs(theta - 0.25 * jnp.pi))
    return {
        "dc": dc,
        "dd": dd,
        "theta": theta,
        "dtheta": dtheta,
        "off_c": offdiag_weight(dc),
        "off_d": offdiag_weight(dd),
        "nonadj_c": nonadjacent_weight(dc),
        "loc_c": leaf_participation(dc),
        "loc_d": leaf_participation(dd),
        "hermitian_c": jnp.max(jnp.abs(dc - dc.T)),
        "hermitian_d": jnp.max(jnp.abs(dd - dd.T)),
        "area": area,
        "max_area": max_area,
        "peak_leaf_zero_indexed": peak,
        "clifford_distance": clifford_distance,
    }


def main() -> int:
    started = time.time()
    core = run_core()
    off_c = float(core["off_c"])
    off_d = float(core["off_d"])
    nonadj_c = float(core["nonadj_c"])
    loc_c = float(core["loc_c"])
    loc_d = float(core["loc_d"])
    herm_c = float(core["hermitian_c"])
    herm_d = float(core["hermitian_d"])
    checks = {
        "finite_16_leaf_domain": NLEAF == 16,
        "coupled_links_leaves": off_c > 1.0e-9,
        "decoupled_block_diagonal": off_d < 1.0e-12,
        "nearest_neighbour_only": nonadj_c < 1.0e-12,
        "operators_hermitian": herm_c < 1.0e-12 and herm_d < 1.0e-12,
        "coupled_delocalizes": loc_c > 2.0 and loc_c > 3.0 * loc_d,
        "decoupled_localizes": loc_d < 1.0 + 1.0e-6,
        "area_peak_near_clifford": float(core["clifford_distance"]) < float(core["dtheta"]),
    }
    all_pass = all(checks.values())
    result = {
        "sim_id": "jax_radial_dirac_interleaf_coupling_probe",
        "name": "JAX radial Dirac inter-leaf coupling formal scout",
        "classification": "formal_scout",
        "sim_class": "radial_dirac_interleaf_coupling_probe",
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "ran_julia": False,
        "ran_pytorch": False,
        "julia_reference_mode": "read_only_not_executed",
        "julia_reference_paths_read_only": [
            "system_v5/julia_carrier/layers/nested_leaf_area_ratchet.jl",
            "system_v5/julia_carrier/layers/nested_leaf_area_ratchet_results.json",
        ],
        "claim_boundary": "JAX-only formal scout for finite radial Dirac inter-leaf coupling; no layer completion, stacking, flux, Axis0, FEP, physics, or final manifold admission.",
        "root_constraints_exercised": {
            "F01": "finite 16 Hopf leaves with two-component spinor block per leaf",
            "N01": "radial gamma-theta adjacent hopping is removed by the decoupling negative",
        },
        "finite_map": "finite block-tridiagonal radial Dirac operator D(theta) -> off-diagonal coupling, nonadjacent-coupling, and eigenmode leaf-participation readouts",
        "domain": {
            "Nleaf": NLEAF,
            "state_dimension": 2 * NLEAF,
            "theta_grid": [float(x) for x in core["theta"]],
        },
        "codomain_or_output": {
            "objects": [
                "coupled and decoupled finite radial Dirac matrices",
                "off-diagonal and nonadjacent block weights",
                "mean leaf participation ratios",
                "leaf-area peak readout",
            ]
        },
        "metrics": {
            "dtheta": float(core["dtheta"]),
            "offdiag_weight_coupled": off_c,
            "offdiag_weight_decoupled": off_d,
            "nonadjacent_weight_coupled": nonadj_c,
            "mean_leaf_participation_coupled": loc_c,
            "mean_leaf_participation_decoupled": loc_d,
            "hermitian_residual_coupled": herm_c,
            "hermitian_residual_decoupled": herm_d,
            "max_area": float(core["max_area"]),
            "peak_leaf_zero_indexed": int(core["peak_leaf_zero_indexed"]),
            "clifford_distance": float(core["clifford_distance"]),
            "elapsed_seconds": round(time.time() - started, 6),
        },
        "checks": {k: bool(v) for k, v in checks.items()},
        "all_pass": bool(all_pass),
        "AUDIT_PASS": bool(all_pass),
        "blocked_consumers": BLOCKED_CONSUMERS,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
    }
    RESULT.parent.mkdir(parents=True, exist_ok=True)
    RESULT.write_text(json.dumps(jsonable(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        "jax_radial_dirac_interleaf "
        f"AUDIT_PASS={all_pass} off_c={off_c:.4f} off_d={off_d:.2e} "
        f"loc={loc_c:.3f}/{loc_d:.3f}"
    )
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
