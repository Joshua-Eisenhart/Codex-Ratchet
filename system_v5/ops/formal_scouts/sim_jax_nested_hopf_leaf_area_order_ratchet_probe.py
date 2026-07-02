#!/usr/bin/env python3
"""JAX-only nested Hopf leaf-area order ratchet scout.

Julia is read-only reference for this lane. This script does not import or run
Julia, PyTorch, or Torch. It uses finite S3 spinor coordinates on nested Hopf
tori and asks one bounded question:

    does a finite leaf-area ratchet fail to commute with finite Weyl/terrain
    channel motion, and does the resulting branch/prune ensemble expose basin,
    subbasin, and subsubbasin structure?

Claim ceiling: formal scout only. No layer completion, stacking, flux, Axis0,
FEP, physics, or final manifold admission.
"""

from __future__ import annotations

import json
import math
import time
from pathlib import Path
from typing import Any

from jax import config

config.update("jax_enable_x64", True)

import jax
import jax.numpy as jnp


RESULT = Path("system_v5/ops/formal_scouts/results/jax_nested_hopf_leaf_area_order_ratchet_probe_results.json")
RTYPE = jnp.float64
N_PLACEMENTS = 16
N_LEAVES = 16
N_SEEDS = 16
N_STEPS = 160
DT = 0.045
EPS = 1.0e-9

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
        "reason": "JAX x64 computes the finite nested-Hopf branch/prune dynamics and noncommuting order gap.",
    },
    "jax.numpy": {
        "used": True,
        "role": "load_bearing",
        "reason": "Finite S3 spinor coordinates, leaf-area ratchet, controls, and basin labels.",
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


def placements() -> tuple[jax.Array, jax.Array, jax.Array]:
    p = jnp.arange(N_PLACEMENTS, dtype=jnp.int32)
    topo = p % 4
    sheet = (p // 4) % 2
    path = (p // 8) % 2
    return topo, sheet, path


def signs(topo: jax.Array, sheet: jax.Array, path: jax.Array) -> tuple[jax.Array, jax.Array, jax.Array]:
    topo_s = jnp.asarray([-1.0, -0.33, 0.33, 1.0], dtype=RTYPE)[topo]
    sheet_s = jnp.where(sheet == 0, 1.0, -1.0)
    path_s = jnp.where(path == 0, 1.0, -1.0)
    return topo_s, sheet_s, path_s


def initial_angles() -> jax.Array:
    topo, sheet, path = placements()
    leaves = jnp.arange(N_LEAVES, dtype=RTYPE)
    seeds = jnp.arange(N_SEEDS, dtype=RTYPE)
    theta0 = (leaves + 1.0) * (0.5 * jnp.pi) / (N_LEAVES + 1.0)
    theta = theta0[None, :, None] + 0.012 * jnp.sin((seeds[None, None, :] + 1.0) * 1.7)
    phi = (
        2.0 * jnp.pi * seeds[None, None, :] / N_SEEDS
        + 0.19 * topo[:, None, None]
        + 0.07 * path[:, None, None]
    )
    chi = (
        2.0 * jnp.pi * jnp.mod(3.0 * seeds, N_SEEDS)[None, None, :] / N_SEEDS
        + 0.13 * sheet[:, None, None]
        - 0.11 * topo[:, None, None]
    )
    theta = jnp.broadcast_to(theta, (N_PLACEMENTS, N_LEAVES, N_SEEDS))
    phi = jnp.broadcast_to(phi, (N_PLACEMENTS, N_LEAVES, N_SEEDS))
    chi = jnp.broadcast_to(chi, (N_PLACEMENTS, N_LEAVES, N_SEEDS))
    return jnp.stack([theta, phi, chi], axis=-1).reshape(-1, 3)


def placement_arrays() -> tuple[jax.Array, jax.Array, jax.Array]:
    topo, sheet, path = placements()
    topo = jnp.broadcast_to(topo[:, None, None], (N_PLACEMENTS, N_LEAVES, N_SEEDS)).reshape(-1)
    sheet = jnp.broadcast_to(sheet[:, None, None], (N_PLACEMENTS, N_LEAVES, N_SEEDS)).reshape(-1)
    path = jnp.broadcast_to(path[:, None, None], (N_PLACEMENTS, N_LEAVES, N_SEEDS)).reshape(-1)
    return topo, sheet, path


def retract_angles(x: jax.Array) -> jax.Array:
    theta = jnp.clip(x[:, 0], 0.02, 0.5 * jnp.pi - 0.02)
    phi = jnp.mod(x[:, 1], 2.0 * jnp.pi)
    chi = jnp.mod(x[:, 2], 2.0 * jnp.pi)
    return jnp.stack([theta, phi, chi], axis=1)


def spinor_q(x: jax.Array) -> jax.Array:
    theta, phi, chi = x[:, 0], x[:, 1], x[:, 2]
    q = jnp.stack(
        [
            jnp.cos(theta) * jnp.cos(phi),
            jnp.cos(theta) * jnp.sin(phi),
            jnp.sin(theta) * jnp.cos(chi),
            jnp.sin(theta) * jnp.sin(chi),
        ],
        axis=1,
    )
    return q / jnp.linalg.norm(q, axis=1, keepdims=True)


def leaf_area(theta: jax.Array) -> jax.Array:
    # Clifford torus leaf area in S3 is proportional to cos(theta) sin(theta).
    return jnp.clip(jnp.sin(2.0 * theta), EPS, None)


def ratchet_step(x: jax.Array, topo: jax.Array, sheet: jax.Array, path: jax.Array, *, flat: bool = False) -> jax.Array:
    theta, phi, chi = x[:, 0], x[:, 1], x[:, 2]
    topo_s, sheet_s, path_s = signs(topo, sheet, path)
    area = jnp.ones_like(theta) if flat else leaf_area(theta)
    area_grad = 2.0 / jnp.tan(jnp.clip(2.0 * theta, 0.04, jnp.pi - 0.04))
    theta_n = theta + DT * (0.18 * jnp.tanh(area_grad) + 0.018 * topo_s * sheet_s - 0.012 * path_s)
    phi_n = phi + DT * (0.09 * topo_s * area + 0.03 * sheet_s * jnp.sin(chi))
    chi_n = chi - DT * (0.07 * path_s * area + 0.02 * topo_s * jnp.cos(phi))
    return retract_angles(jnp.stack([theta_n, phi_n, chi_n], axis=1))


def channel_step(x: jax.Array, topo: jax.Array, sheet: jax.Array, path: jax.Array, *, commuting: bool = False) -> jax.Array:
    theta, phi, chi = x[:, 0], x[:, 1], x[:, 2]
    topo_s, sheet_s, path_s = signs(topo, sheet, path)
    if commuting:
        phi_n = phi + DT * 0.05
        chi_n = chi + DT * 0.05
        theta_n = theta
    else:
        phi_n = phi + DT * (0.31 * topo_s + 0.23 * sheet_s * jnp.cos(chi) + 0.11 * path_s * jnp.sin(theta))
        chi_n = chi + DT * (0.29 * path_s * jnp.sin(phi) - 0.17 * topo_s * jnp.cos(theta))
        theta_n = theta + DT * (0.035 * sheet_s * jnp.sin(phi - chi) + 0.012 * topo_s * path_s)
    return retract_angles(jnp.stack([theta_n, phi_n, chi_n], axis=1))


def scan_order(x0: jax.Array, topo: jax.Array, sheet: jax.Array, path: jax.Array, order: int, *, flat: bool = False, commuting: bool = False) -> tuple[jax.Array, jax.Array]:
    def body(carry, _):
        x, alive = carry
        if order == 0:
            x_next = channel_step(ratchet_step(x, topo, sheet, path, flat=flat), topo, sheet, path, commuting=commuting)
        else:
            x_next = ratchet_step(channel_step(x, topo, sheet, path, commuting=commuting), topo, sheet, path, flat=flat)
        q = spinor_q(x_next)
        alive_next = alive & ~(q[:, 0] < -0.01)
        return (x_next, alive_next), None

    alive0 = jnp.ones((x0.shape[0],), dtype=bool)
    (xf, alivef), _ = jax.lax.scan(body, (x0, alive0), xs=None, length=N_STEPS)
    return xf, alivef


@jax.jit
def run_core() -> dict[str, jax.Array]:
    x0 = initial_angles()
    topo, sheet, path = placement_arrays()
    rt, alive_rt = scan_order(x0, topo, sheet, path, 0)
    tr, alive_tr = scan_order(x0, topo, sheet, path, 1)
    commuting, alive_commuting = scan_order(x0, topo, sheet, path, 0, commuting=True)
    commuting_rev, alive_commuting_rev = scan_order(x0, topo, sheet, path, 1, commuting=True)
    flat, alive_flat = scan_order(x0, topo, sheet, path, 0, flat=True)
    erased_topo = jnp.zeros_like(topo)
    erased_sheet = jnp.zeros_like(sheet)
    erased_path = jnp.zeros_like(path)
    erased, alive_erased = scan_order(x0, erased_topo, erased_sheet, erased_path, 0, flat=True, commuting=True)
    q_rt = spinor_q(rt)
    q_tr = spinor_q(tr)
    q_commuting = spinor_q(commuting)
    q_flat = spinor_q(flat)
    q_erased = spinor_q(erased)
    return {
        "q_rt": q_rt,
        "q_tr": q_tr,
        "q_commuting": q_commuting,
        "q_commuting_rev": spinor_q(commuting_rev),
        "q_flat": q_flat,
        "q_erased": q_erased,
        "x_rt": rt,
        "x_erased": erased,
        "alive_rt": alive_rt,
        "alive_tr": alive_tr,
        "alive_commuting": alive_commuting,
        "alive_commuting_rev": alive_commuting_rev,
        "alive_flat": alive_flat,
        "alive_erased": alive_erased,
    }


def populated_count(labels: jax.Array, alive: jax.Array, size: int) -> int:
    hist = jnp.bincount(jnp.where(alive, labels, size), length=size + 1)[:size]
    return int(jnp.sum(hist > 0))


def basin_labels(q: jax.Array, x: jax.Array) -> tuple[jax.Array, jax.Array, jax.Array]:
    targets = jnp.asarray(
        [
            [0.5, 0.5, 0.5, 0.5],
            [0.5, 0.5, -0.5, -0.5],
            [-0.5, -0.5, 0.5, -0.5],
            [-0.5, -0.5, -0.5, 0.5],
        ],
        dtype=RTYPE,
    )
    basin = jnp.argmax(q @ targets.T, axis=1)
    theta_bin = jnp.clip(jnp.floor(4.0 * x[:, 0] / (0.5 * jnp.pi)).astype(jnp.int32), 0, 3)
    phase_bin = jnp.clip(jnp.floor(4.0 * x[:, 1] / (2.0 * jnp.pi)).astype(jnp.int32), 0, 3)
    sub = basin * 4 + theta_bin
    subsub = basin * 16 + theta_bin * 4 + phase_bin
    return basin, sub, subsub


def main() -> int:
    started = time.time()
    core = run_core()
    q_rt = core["q_rt"]
    q_tr = core["q_tr"]
    q_commuting = core["q_commuting"]
    q_commuting_rev = core["q_commuting_rev"]
    q_flat = core["q_flat"]
    q_erased = core["q_erased"]
    alive = core["alive_rt"]
    basin, sub, subsub = basin_labels(q_rt, core["x_rt"])
    basin_e, sub_e, subsub_e = basin_labels(q_erased, core["x_erased"])
    total = int(q_rt.shape[0])
    order_gap = float(jnp.mean(jnp.linalg.norm(q_rt - q_tr, axis=1)))
    commuting_gap = float(jnp.mean(jnp.linalg.norm(q_commuting - q_commuting_rev, axis=1)))
    flat_gap = float(jnp.mean(jnp.linalg.norm(q_flat - q_rt, axis=1)))
    erased_gap = float(jnp.mean(jnp.linalg.norm(q_erased - q_rt, axis=1)))
    max_norm_drift = float(jnp.max(jnp.abs(jnp.linalg.norm(q_rt, axis=1) - 1.0)))
    survivors = int(jnp.sum(alive))
    pruned = total - survivors
    basin_count = populated_count(basin, alive, 4)
    sub_count = populated_count(sub, alive, 16)
    subsub_count = populated_count(subsub, alive, 64)
    erased_basin_count = populated_count(basin_e, core["alive_erased"], 4)
    erased_sub_count = populated_count(sub_e, core["alive_erased"], 16)
    erased_subsub_count = populated_count(subsub_e, core["alive_erased"], 64)
    area_values = leaf_area((jnp.arange(N_LEAVES, dtype=RTYPE) + 1.0) * (0.5 * jnp.pi) / (N_LEAVES + 1.0))
    checks = {
        "finite_domain": total == N_PLACEMENTS * N_LEAVES * N_SEEDS,
        "s3_retraction_holds": max_norm_drift < 1.0e-10,
        "leaf_area_nonuniform": float(jnp.max(area_values) - jnp.min(area_values)) > 0.1,
        "noncommuting_order_gap": order_gap > 1.0e-3,
        "commuting_control_smaller": commuting_gap < order_gap,
        "flat_area_control_changes_result": flat_gap > 1.0e-3,
        "label_erased_control_changes_result": erased_gap > order_gap,
        "branch_prune_fired": pruned > 0,
        "basin_hierarchy_nonvacuous": basin_count >= 3 and sub_count >= 8 and subsub_count >= 16,
        "erased_hierarchy_not_stronger": erased_subsub_count <= subsub_count,
    }
    all_pass = all(checks.values())
    result = {
        "sim_id": "jax_nested_hopf_leaf_area_order_ratchet_probe",
        "name": "JAX nested Hopf leaf-area order ratchet formal scout",
        "classification": "formal_scout",
        "sim_class": "nested_hopf_leaf_area_order_ratchet_probe",
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "ran_julia": False,
        "ran_pytorch": False,
        "julia_reference_mode": "read_only_not_executed",
        "julia_reference_paths_read_only": [
            "system_v5/julia_carrier/layers/nested_leaf_area_ratchet_results.json",
            "system_v5/julia_carrier/layers/multishell_ratchet_cascade_results.json",
            "system_v5/julia_carrier/layers/ratchet_order_test_results.json",
        ],
        "claim_boundary": "JAX-only formal scout for finite leaf-area/order ratchet behavior; no layer completion, stacking, flux, Axis0, FEP, physics, or final manifold admission.",
        "root_constraints_exercised": {
            "F01": "finite 16 placements x 16 Hopf leaves x 16 branch seeds",
            "N01": "leaf-area ratchet and Weyl/terrain channel order do not commute under finite controls",
        },
        "finite_map": "(placement, Hopf leaf theta, branch seed) -> S3 spinor trajectory under ratchet/channel order and monotone prune latch",
        "domain": {
            "placements": N_PLACEMENTS,
            "leaves": N_LEAVES,
            "seeds_per_placement_leaf": N_SEEDS,
            "total_branches": total,
            "topology_laws": 4,
            "weyl_sheets": 2,
            "path_placements": 2,
        },
        "codomain_or_output": {
            "objects": [
                "S3 unit-quaternion spinor final states",
                "monotone alive/pruned mask",
                "ratchet/channel order gap",
                "basin, subbasin, and subsubbasin finite labels",
            ]
        },
        "metrics": {
            "total": total,
            "survivors": survivors,
            "pruned": pruned,
            "order_gap": order_gap,
            "commuting_gap": commuting_gap,
            "flat_area_gap": flat_gap,
            "label_erased_gap": erased_gap,
            "max_norm_drift": max_norm_drift,
            "basins": basin_count,
            "subbasins": sub_count,
            "subsubbasins": subsub_count,
            "erased_basins": erased_basin_count,
            "erased_subbasins": erased_sub_count,
            "erased_subsubbasins": erased_subsub_count,
            "leaf_area_values": [float(x) for x in area_values],
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
        "jax_nested_hopf_leaf_area_order_ratchet "
        f"AUDIT_PASS={all_pass} order_gap={order_gap:.6f} "
        f"survivors={survivors} pruned={pruned} hierarchy={basin_count}/{sub_count}/{subsub_count}"
    )
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
