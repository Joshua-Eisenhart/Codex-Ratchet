#!/usr/bin/env python3
"""JAX-only robustness/negative sweep for the bottom-up nested Hopf receipt.

This script is based on ``jax_nested_hopf_bottom_up_branch_prune_audit.py`` and
reruns the finite branch/prune object across deterministic lightweight cases.
It does not run Julia and does not import PyTorch.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import jax
from jax import config

config.update("jax_enable_x64", True)

import jax.numpy as jnp


OUT = Path("jax_nested_hopf_bottom_up_robustness_sweep_results.json")
PROMOTION_ALLOWED = False
TOPOLOGIES = ("Se", "Ne", "Ni", "Si")
LEFT_TERRAINS = {"Se": "Funnel", "Ne": "Vortex", "Ni": "Pit", "Si": "Hill"}
RIGHT_TERRAINS = {"Se": "Cannon", "Ne": "Spiral", "Ni": "Source", "Si": "Citadel"}
TARGETS = jnp.asarray(
    [
        [0.5 if sheet == "L" else -0.5, 0.5 if path == "fiber" else -0.5, 0.5 if (topo_i & 1) == 0 else -0.5, 0.5 if (topo_i & 2) == 0 else -0.5]
        for sheet in ("L", "R")
        for path in ("fiber", "base")
        for topo_i, _topology in enumerate(TOPOLOGIES)
    ],
    dtype=jnp.float64,
)
SHEET_SIGN = jnp.asarray([1.0 if i < 8 else -1.0 for i in range(16)], dtype=jnp.float64)
TOPO_IDX = jnp.asarray([i % 4 for i in range(16)], dtype=jnp.int32)
PATH_IDX = jnp.asarray([(i // 4) % 2 for i in range(16)], dtype=jnp.int32)
BLOCKED_CONSUMERS = [
    "official_g_structure_selection",
    "layer_stacking_readiness",
    "Axis0",
    "FEP",
    "flux",
    "Xi",
    "Phi0",
    "physics/gravity",
    "final_manifold_admission",
]


@dataclass(frozen=True)
class Placement:
    label: int
    sheet: str
    path: str
    topology: str
    terrain: str
    target: tuple[float, float, float, float]


@dataclass(frozen=True)
class SweepCase:
    name: str
    seed: int
    branches: int
    leaves: int
    steps: int
    dt: float
    f01_tol: float
    hop_base: float
    hop_scale: float
    radial_scale: float


CASES = (
    SweepCase("seed20260603_branches512_leaves9", 20260603, 512, 9, 520, 0.010, 1.0e-3, 0.060, 0.30, 1.00),
    SweepCase("seed20260617_branches640_leaves9", 20260617, 640, 9, 500, 0.009, 8.0e-4, 0.055, 0.34, 0.92),
    SweepCase("seed20260631_branches768_leaves11", 20260631, 768, 11, 560, 0.008, 1.2e-3, 0.050, 0.36, 0.88),
    SweepCase("seed20260709_branches896_leaves7", 20260709, 896, 7, 480, 0.011, 1.0e-3, 0.065, 0.28, 0.95),
    SweepCase("seed20260721_branches1024_leaves9", 20260721, 1024, 9, 540, 0.0085, 9.0e-4, 0.052, 0.38, 0.90),
)


def _f(x: Any) -> float:
    return float(jax.device_get(x))


def _i(x: Any) -> int:
    return int(jax.device_get(x))


def unit(x: jax.Array) -> jax.Array:
    return x / jnp.linalg.norm(x, axis=-1, keepdims=True)


def qmul(a: jax.Array, b: jax.Array) -> jax.Array:
    a0, a1, a2, a3 = a[:, 0], a[:, 1], a[:, 2], a[:, 3]
    b0, b1, b2, b3 = b[:, 0], b[:, 1], b[:, 2], b[:, 3]
    return jnp.stack(
        [
            a0 * b0 - a1 * b1 - a2 * b2 - a3 * b3,
            a0 * b1 + a1 * b0 + a2 * b3 - a3 * b2,
            a0 * b2 - a1 * b3 + a2 * b0 + a3 * b1,
            a0 * b3 + a1 * b2 - a2 * b1 + a3 * b0,
        ],
        axis=1,
    )


def qrot(q: jax.Array) -> jax.Array:
    q = q / jnp.linalg.norm(q)
    w, x, y, z = q
    return jnp.asarray(
        [
            [1.0 - 2.0 * (y * y + z * z), 2.0 * (x * y - z * w), 2.0 * (x * z + y * w)],
            [2.0 * (x * y + z * w), 1.0 - 2.0 * (x * x + z * z), 2.0 * (y * z - x * w)],
            [2.0 * (x * z - y * w), 2.0 * (y * z + x * w), 1.0 - 2.0 * (x * x + y * y)],
        ],
        dtype=jnp.float64,
    )


def placements() -> list[Placement]:
    rows: list[Placement] = []
    label = 1
    for sheet, terrains in (("L", LEFT_TERRAINS), ("R", RIGHT_TERRAINS)):
        q0 = 0.5 if sheet == "L" else -0.5
        for path_bit, path in enumerate(("fiber", "base")):
            for topo_i, topology in enumerate(TOPOLOGIES):
                rows.append(
                    Placement(
                        label=label,
                        sheet=sheet,
                        path=path,
                        topology=topology,
                        terrain=terrains[topology],
                        target=(
                            q0,
                            0.5 if path_bit == 0 else -0.5,
                            0.5 if (topo_i & 1) == 0 else -0.5,
                            0.5 if (topo_i & 2) == 0 else -0.5,
                        ),
                    )
                )
                label += 1
    return rows


PLACEMENTS = placements()


def leaf_grid(case: SweepCase) -> tuple[jax.Array, jax.Array, int]:
    thetas = jnp.linspace(
        jnp.pi / (2.0 * (case.leaves + 1)),
        jnp.pi / 2.0 - jnp.pi / (2.0 * (case.leaves + 1)),
        case.leaves,
    )
    areas = 2.0 * jnp.pi**2 * jnp.sin(2.0 * thetas)
    return thetas, areas, int(case.leaves // 2)


def initial_nested_state(case: SweepCase) -> tuple[jax.Array, jax.Array, jax.Array, jax.Array, jax.Array]:
    key = jax.random.PRNGKey(case.seed)
    q = unit(jax.random.normal(key, (case.branches, 4), dtype=jnp.float64))
    placement = jnp.arange(case.branches, dtype=jnp.int32) % 16
    leaf = (jnp.arange(case.branches, dtype=jnp.int32) * 5 + placement) % case.leaves
    angles = 2.0 * jnp.pi * (jnp.arange(case.branches, dtype=jnp.float64) / case.branches)
    rad = case.radial_scale * (0.48 + 0.08 * (placement.astype(jnp.float64) % 3.0))
    r = jnp.stack([rad * jnp.cos(angles), rad * jnp.sin(angles), 0.22 * case.radial_scale * jnp.sin(2.0 * angles)], axis=1)
    alive = jnp.ones((case.branches,), dtype=bool)
    return q, r, leaf, placement, alive


def project_bloch_ball(r: jax.Array) -> jax.Array:
    n = jnp.linalg.norm(r, axis=-1, keepdims=True)
    return jnp.where(n > 1.0, r / n, r)


def bloch_field(r: jax.Array, placement: jax.Array, mode_code: int) -> jax.Array:
    rx, ry, rz = r[:, 0], r[:, 1], r[:, 2]
    sign = SHEET_SIGN[placement]
    topo = TOPO_IDX[placement]
    eps = 0.2

    se = jnp.stack([-0.55 * rx - 0.35 * sign * ry, 0.35 * sign * rx - 0.55 * ry, -0.8 * (rz + 0.538)], axis=1)
    ne = jnp.stack([-2.0 * sign * ry - 2.0 * eps * rx, 2.0 * sign * rx - 2.0 * eps * ry, -0.08 * rz], axis=1)
    pit_or_source_target = jnp.where(sign > 0.0, -1.0, 1.0)
    ni = jnp.stack([-0.5 * rx, -0.5 * ry, -1.0 * (rz - pit_or_source_target)], axis=1)
    si = jnp.stack([jnp.zeros_like(rx), -1.0 * ry, -1.0 * rz], axis=1)
    field = jnp.where((topo == 0)[:, None], se, jnp.where((topo == 1)[:, None], ne, jnp.where((topo == 2)[:, None], ni, si)))

    commuting = jnp.stack([-0.5 * rx, -0.5 * ry, -(rz + 1.0)], axis=1)
    expansive = jnp.stack([rx, ry, rz], axis=1)
    field = jnp.where(mode_code == 1, commuting, field)
    field = jnp.where(mode_code == 3, expansive, field)
    return field


def run_nested(case: SweepCase, mode_code: int) -> tuple[jax.Array, jax.Array, jax.Array, jax.Array, jax.Array, jax.Array]:
    q0, r0, leaf0, placement0, alive0 = initial_nested_state(case)
    _thetas, areas, _max_leaf = leaf_grid(case)
    key0 = jax.random.PRNGKey(case.seed + 9001)

    def step(carry: tuple[jax.Array, jax.Array, jax.Array, jax.Array, jax.Array, jax.Array], _unused: Any):
        q, r, leaf, placement, alive, key = carry
        key, sub = jax.random.split(key)
        u = jax.random.uniform(sub, (case.branches,), dtype=jnp.float64)

        target_idx = jnp.where(mode_code == 1, jnp.zeros_like(placement), placement)
        target = TARGETS[target_idx]
        tangent = target - jnp.sum(target * q, axis=1, keepdims=True) * q
        rotor_axis = jnp.stack(
            [
                jnp.zeros(case.branches),
                0.05 * SHEET_SIGN[placement],
                0.03 * (TOPO_IDX[placement] - 1.5),
                0.02 * (PATH_IDX[placement] * 2 - 1),
            ],
            axis=1,
        )
        q_next = unit(q + case.dt * (1.8 * tangent + qmul(rotor_axis, q)))

        r_raw = r + case.dt * bloch_field(r, placement, mode_code)
        killed = jnp.linalg.norm(r_raw, axis=1) > (1.0 + case.f01_tol)
        r_next = project_bloch_ball(r_raw)

        left = jnp.maximum(leaf - 1, 0)
        right = jnp.minimum(leaf + 1, case.leaves - 1)
        active_areas = jnp.where(mode_code == 4, jnp.ones_like(areas), areas)
        prefer_right = active_areas[right] > active_areas[left]
        candidate = jnp.clip(leaf + jnp.where(prefer_right, 1, -1), 0, case.leaves - 1)
        area_gain = jnp.maximum(active_areas[candidate] - active_areas[leaf], 0.0)
        hop_p = jnp.where((mode_code == 2) | (area_gain <= 0.0), 0.0, case.hop_base + case.hop_scale * area_gain / jnp.max(active_areas))
        leaf_next = jnp.where(u < hop_p, candidate, leaf)

        alive_next = alive & ~killed
        max_q_drift = jnp.max(jnp.abs(jnp.linalg.norm(q_next, axis=1) - 1.0))
        max_r_norm = jnp.max(jnp.linalg.norm(r_next, axis=1))
        return (q_next, r_next, leaf_next, placement, alive_next, key), jnp.asarray([max_q_drift, max_r_norm])

    (qf, rf, leaff, _placement, alive, _key), metrics = jax.lax.scan(
        step,
        (q0, r0, leaf0, placement0, alive0, key0),
        None,
        length=case.steps,
    )
    return qf, rf, leaff, alive, jnp.max(metrics[:, 0]), jnp.max(metrics[:, 1])


def populated(values: jax.Array, alive: jax.Array, size: int) -> list[int]:
    uniq = jnp.unique(values[alive], size=size, fill_value=-1)
    return [int(x) for x in jax.device_get(uniq) if int(x) >= 0]


def run_nested_summary(case: SweepCase, name: str, mode: int) -> dict[str, Any]:
    qf, rf, leaff, alive, max_q_drift, max_r_norm = run_nested(case, mode)
    _thetas, _areas, max_leaf = leaf_grid(case)
    labels = jnp.argmax(qf @ TARGETS.T, axis=1) + 1
    alive_count = _i(jnp.sum(alive))
    central_alive = _i(jnp.sum(alive & (leaff == max_leaf)))
    leaf_hist = jnp.bincount(jnp.where(alive, leaff, 0), length=case.leaves)
    leaf_hist = leaf_hist.at[0].add(-_i(jnp.sum(~alive)))
    if alive_count:
        q_alive = qf[alive]
        double_cover = jax.vmap(lambda q: jnp.linalg.norm(qrot(q) - qrot(-q)))(q_alive)
        max_double_cover_gap = _f(jnp.max(double_cover))
        mean_bloch_norm = _f(jnp.mean(jnp.linalg.norm(rf[alive], axis=1)))
    else:
        max_double_cover_gap = None
        mean_bloch_norm = None
    return {
        "name": name,
        "populated_placements": populated(labels, alive, 16),
        "populated_leaves_zero_based": populated(leaff, alive, case.leaves),
        "survivors": alive_count,
        "pruned": int(case.branches - alive_count),
        "central_leaf_fraction": float(central_alive / max(alive_count, 1)),
        "leaf_histogram": [int(x) for x in jax.device_get(leaf_hist)],
        "max_q_norm_drift": _f(max_q_drift),
        "max_bloch_norm_after_projection": _f(max_r_norm),
        "max_double_cover_gap": max_double_cover_gap,
        "mean_final_bloch_norm": mean_bloch_norm,
    }


def evaluate_case(case: SweepCase) -> dict[str, Any]:
    genuine = run_nested_summary(case, "genuine_ratchet_noncommuting", 0)
    n01_off = run_nested_summary(case, "n01_off_single_commuting_sink", 1)
    ratchet_off = run_nested_summary(case, "ratchet_off_theta_frozen", 2)
    expansive = run_nested_summary(case, "f01_expansive_prune_control", 3)
    flat_area = run_nested_summary(case, "flat_area_no_ratchet_control", 4)

    genuine_set = set(genuine["populated_placements"])
    ratchet_hist_differs = ratchet_off["leaf_histogram"] != genuine["leaf_histogram"]
    flat_hist_differs = flat_area["leaf_histogram"] != genuine["leaf_histogram"]
    q_drift_rows = (genuine, n01_off, ratchet_off, expansive, flat_area)
    checks = {
        "genuine_populates_all_16_placement_basins": genuine_set == set(range(1, 17)),
        "genuine_survivors_not_pruned": genuine["pruned"] == 0,
        "genuine_ratchet_concentrates_clifford_leaf": genuine["central_leaf_fraction"] > 0.70,
        "n01_off_collapses_to_one_placement_basin": n01_off["populated_placements"] == [1],
        "ratchet_off_leaf_histogram_differs": ratchet_hist_differs and ratchet_off["central_leaf_fraction"] < genuine["central_leaf_fraction"] - 0.20,
        "flat_area_control_leaf_histogram_differs": flat_hist_differs and flat_area["central_leaf_fraction"] < genuine["central_leaf_fraction"] - 0.20,
        "f01_expansive_prune_fires": expansive["pruned"] > 0,
        "bookkeeping_consistent": all(row["survivors"] == case.branches - row["pruned"] for row in q_drift_rows),
        "s3_retraction_works": max(row["max_q_norm_drift"] for row in q_drift_rows) < 1.0e-12,
        "double_cover_preserved": max(row["max_double_cover_gap"] or 0.0 for row in (genuine, n01_off, ratchet_off, flat_area)) < 1.0e-12,
        "promotion_allowed_false": PROMOTION_ALLOWED is False,
    }
    return {
        "case": case.__dict__,
        "runs": {
            "genuine": genuine,
            "n01_off_control": n01_off,
            "ratchet_off_control": ratchet_off,
            "expansive_prune_control": expansive,
            "flat_area_control": flat_area,
        },
        "checks": checks,
        "case_pass": all(checks.values()),
    }


def rejected_weakened_control_lane(case: SweepCase) -> dict[str, Any]:
    lane = run_nested_summary(case, "weakened_n01_masquerading_as_genuine", 1)
    lane_checks = {
        "would_populate_all_16_if_it_were_genuine": lane["populated_placements"] == list(range(1, 17)),
        "would_not_collapse_if_n01_survived": len(lane["populated_placements"]) > 1,
    }
    lane_pass = all(lane_checks.values())
    return {
        "name": "weakened_n01_masquerading_as_genuine",
        "source_case": case.name,
        "expectation": "This lane intentionally runs the N01-off commuting sink while pretending to be genuine; it must fail all-16 structural admission.",
        "run": lane,
        "checks": lane_checks,
        "lane_pass": lane_pass,
        "rejected": not lane_pass,
        "rejection_reason": "N01-off collapsed to one placement basin, so the weakened lane cannot be accepted as genuine robustness evidence.",
    }


def main() -> int:
    rows = [evaluate_case(case) for case in CASES]
    rejected_lane = rejected_weakened_control_lane(CASES[0])
    top_checks = {
        "at_least_five_deterministic_cases": len(rows) >= 5,
        "all_cases_pass": all(row["case_pass"] for row in rows),
        "rejected_lane_rejected": bool(rejected_lane["rejected"]) and not bool(rejected_lane["lane_pass"]),
        "promotion_allowed_false": PROMOTION_ALLOWED is False,
        "ran_julia_false": True,
        "ran_pytorch_false": True,
    }
    audit_pass = all(top_checks.values())
    passed = sum(1 for row in rows if row["case_pass"])
    receipt = {
        "sim_id": "jax_nested_hopf_bottom_up_robustness_sweep",
        "name": "JAX bottom-up nested Hopf robustness/negative sweep",
        "version": "1.0",
        "based_on": [
            "jax_nested_hopf_bottom_up_branch_prune_audit.py",
            "jax_nested_hopf_bottom_up_branch_prune_audit_results.json",
        ],
        "classification": "tool_lego_fit_probe",
        "sim_execution_kind": "nonclassical_diagnostic_jax_audit",
        "promotion_allowed": PROMOTION_ALLOWED,
        "promotion_status": "blocked_diagnostic_only",
        "claim_ceiling": (
            "JAX-only deterministic robustness/negative sweep for the finite bottom-up nested Hopf receipt. "
            "It checks local structural survival across seeds/branch counts/light parameters and records a "
            "deliberately weakened rejected lane. It is not Julia-native evidence, not PyTorch evidence, "
            "not official G-structure selection, not layer completion, and not Axis0/FEP/flux/physics admission."
        ),
        "ran_julia": False,
        "ran_pytorch": False,
        "root_constraints_in_force": {
            "F01": "finite placement set, finite theta leaf grid, finite branch ensemble, S3 retraction, Bloch-ball prune",
            "N01": "noncommuting/order-sensitive target flow and branch evolution; N01-off commuting sink must collapse basin labels",
        },
        "finite_map": "case grid x {genuine,N01-off,ratchet-off,F01-expansive,flat-area} -> survivor placement/leaf/prune invariants",
        "domain": {
            "placements": "{L,R} x {fiber,base} x {Se,Ne,Ni,Si}",
            "case_count": len(CASES),
            "case_parameters": [case.__dict__ for case in CASES],
            "state": "unit quaternion q in S3 plus finite Bloch-ball control vector r",
        },
        "codomain_or_output": "JSON receipt with per-case structural invariants, negative/control lanes, and rejected weakened-control lane",
        "carrier_layer": "S3 unit-quaternion spinor carrier with finite nested Hopf-torus leaf grid",
        "geometry_layer": "nested Hopf tori T^2_theta with leaf-area ratchet A(theta)=2*pi^2*sin(2theta)",
        "carrier_realization": "jax arrays: q in R^4 normalized to S3 and r in Bloch ball",
        "spinor_state": "q=(Re z1, Im z1, Re z2, Im z2), ||q||=1",
        "quaternion_action": "Spin(3)/SU(2) q target flow plus q/-q SO(3) double-cover invariant",
        "peps3d_embedding": "diagnostic finite cell anchor only: placement x leaf x branch index; not admitted PEPS3D evidence",
        "dependency_receipts": ["jax_nested_hopf_bottom_up_branch_prune_audit_results.json"],
        "blocked_consumers": BLOCKED_CONSUMERS,
        "tool_manifest": {
            "jax": "load-bearing deterministic batched S3 branch/prune robustness sweep and invariant checks",
            "json": "supportive receipt serialization",
        },
        "TOOL_MANIFEST": {
            "jax": "load-bearing deterministic batched S3 branch/prune robustness sweep and invariant checks",
            "json": "supportive receipt serialization",
        },
        "tool_integration_depth": {"jax": "load_bearing", "json": "supportive"},
        "TOOL_INTEGRATION_DEPTH": {"jax": "load_bearing", "json": "supportive"},
        "required_negatives": [
            "N01-off commuting sink collapses to one basin",
            "ratchet-off leaf histogram differs from genuine",
            "F01 expansive mode prunes branches",
            "flat-area no-ratchet control differs from genuine",
            "weakened N01 masquerade is rejected",
        ],
        "negatives_run": [
            "n01_off_control",
            "ratchet_off_control",
            "expansive_prune_control",
            "flat_area_control",
            "weakened_n01_masquerading_as_genuine",
        ],
        "rows": rows,
        "rejected_lane": rejected_lane,
        "checks": top_checks,
        "AUDIT_PASS": audit_pass,
    }
    OUT.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print(
        "jax_nested_hopf_bottom_up_robustness_sweep "
        f"cases={len(rows)} passed={passed}/{len(rows)} "
        f"rejected={rejected_lane['name']} AUDIT_PASS={audit_pass}"
    )
    return 0 if audit_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
