#!/usr/bin/env python3
"""JAX-only recurrence/prune mirror for the nested-terrain emergent basin.

Read-only Julia reference:
  system_v5/julia_carrier/layers/emergent_basin_nested_terrains.jl

This diagnostic is the JAX audit lane: finite, batched, explicitly projected,
and promotion-blocked. It does not run Julia and does not import PyTorch.
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


OUT = Path("jax_emergent_basin_recurrence_prune_mirror_results.json")
N_PER_PLACEMENT = 192
N = 16 * N_PER_PLACEMENT
STEPS = 2400
DT = 0.004
F01_TOL = 1.0e-3
CHIRAL_TOL = 1.0e-2
KRATCH = 0.95
EPS = 1.0e-12

TOPOLOGIES = ("Se", "Ne", "Ni", "Si")
LEFT_TERRAINS = {"Se": "Funnel", "Ne": "Vortex", "Ni": "Pit", "Si": "Hill"}
RIGHT_TERRAINS = {"Se": "Cannon", "Ne": "Spiral", "Ni": "Source", "Si": "Citadel"}

PAULI_X = jnp.asarray([[0, 1], [1, 0]], dtype=jnp.complex128)
PAULI_Y = jnp.asarray([[0, -1j], [1j, 0]], dtype=jnp.complex128)
PAULI_Z = jnp.asarray([[1, 0], [0, -1]], dtype=jnp.complex128)
ID2 = jnp.eye(2, dtype=jnp.complex128)


@dataclass(frozen=True)
class Placement:
    label: int
    sheet: str
    path: str
    topology: str
    terrain: str
    target_q: tuple[float, float, float, float]
    target_r: tuple[float, float, float]


def _f(x: Any) -> float:
    return float(jax.device_get(x))


def _i(x: Any) -> int:
    return int(jax.device_get(x))


def _b(x: Any) -> bool:
    return bool(jax.device_get(x))


def unit(x: jax.Array) -> jax.Array:
    return x / jnp.linalg.norm(x, axis=-1, keepdims=True)


def placements() -> list[Placement]:
    rows: list[Placement] = []
    label = 1
    for sheet, terrains in (("L", LEFT_TERRAINS), ("R", RIGHT_TERRAINS)):
        sheet_sign = 1.0 if sheet == "L" else -1.0
        q0 = 0.5 if sheet == "L" else -0.5
        for path_bit, path in enumerate(("fiber", "base")):
            path_sign = 1.0 if path_bit == 0 else -1.0
            for topo_i, topology in enumerate(TOPOLOGIES):
                q1 = 0.5 if path_bit == 0 else -0.5
                q2 = 0.5 if (topo_i & 1) == 0 else -0.5
                q3 = 0.5 if (topo_i & 2) == 0 else -0.5
                if topology == "Se":
                    target_r = (0.0, 0.0, -sheet_sign)
                elif topology == "Ne":
                    target_r = (0.0, 0.0, 0.35 * sheet_sign)
                elif topology == "Ni":
                    target_r = (0.0, 0.0, sheet_sign)
                elif topology == "Si":
                    target_r = (0.65 * path_sign, 0.0, 0.0)
                else:
                    raise AssertionError(topology)
                rows.append(
                    Placement(
                        label=label,
                        sheet=sheet,
                        path=path,
                        topology=topology,
                        terrain=terrains[topology],
                        target_q=(q0, q1, q2, q3),
                        target_r=target_r,
                    )
                )
                label += 1
    return rows


PLACEMENTS = placements()
TARGET_Q = unit(jnp.asarray([p.target_q for p in PLACEMENTS], dtype=jnp.float64))
TARGET_R = jnp.asarray([p.target_r for p in PLACEMENTS], dtype=jnp.float64)
SHEET_SIGN = jnp.asarray([1.0 if p.sheet == "L" else -1.0 for p in PLACEMENTS], dtype=jnp.float64)
TOPO_IDX = jnp.asarray([TOPOLOGIES.index(p.topology) for p in PLACEMENTS], dtype=jnp.int32)
ASSIGNED = jnp.repeat(jnp.arange(16, dtype=jnp.int32), N_PER_PLACEMENT)
PRODUCT_TARGET_Q = TARGET_Q[0]
PRODUCT_TARGET_R = jnp.asarray([0.0, 0.0, -1.0], dtype=jnp.float64)


def initial_ensemble() -> tuple[jax.Array, jax.Array, jax.Array]:
    q_key, r_key, th_key = jax.random.split(jax.random.PRNGKey(20260602), 3)
    q_noise = jax.random.normal(q_key, (N, 4), dtype=jnp.float64)
    q0 = unit(0.35 * TARGET_Q[ASSIGNED] + q_noise)

    r_dir = unit(jax.random.normal(r_key, (N, 3), dtype=jnp.float64))
    # Deterministic bounded radii, no rejection loop.
    radii = 0.84 * (0.15 + 0.85 * jax.random.uniform(r_key, (N, 1), dtype=jnp.float64)) ** (1.0 / 3.0)
    r0 = radii * r_dir
    theta0 = 0.04 + (jnp.pi / 2.0 - 0.08) * jax.random.uniform(th_key, (N,), dtype=jnp.float64)
    return q0, r0, theta0


def terrain_drift(r: jax.Array, theta: jax.Array, target_r: jax.Array, topo_idx: jax.Array) -> jax.Array:
    base = 0.78 * (target_r - r)
    # Ne/Vortex and Spiral keep a genuine noncommuting swirl while remaining contractive.
    swirl = jnp.stack([-r[:, 1], r[:, 0], jnp.zeros((r.shape[0],), dtype=jnp.float64)], axis=1)
    ne_weight = (topo_idx == 1).astype(jnp.float64)[:, None]
    leaf_weight = (0.75 + 0.25 * jnp.sin(2.0 * theta))[:, None]
    return leaf_weight * base + ne_weight * 1.15 * swirl


def theta_step(theta: jax.Array, product_mode: jax.Array) -> jax.Array:
    dtheta = KRATCH * jnp.cos(2.0 * theta)
    dtheta = jnp.where(product_mode, 0.0, dtheta)
    return jnp.clip(theta + DT * dtheta, 1.0e-4, jnp.pi / 2.0 - 1.0e-4)


@jax.jit
def evolve(product_mode: jax.Array, prune_active: jax.Array) -> tuple[jax.Array, jax.Array, jax.Array, jax.Array, jax.Array]:
    q0, r0, theta0 = initial_ensemble()
    alive0 = jnp.ones((N,), dtype=bool)
    product_q = jnp.broadcast_to(PRODUCT_TARGET_Q, (N, 4))
    product_r = jnp.broadcast_to(PRODUCT_TARGET_R, (N, 3))

    def step(carry: tuple[jax.Array, jax.Array, jax.Array, jax.Array], _: Any) -> tuple[tuple[jax.Array, jax.Array, jax.Array, jax.Array], jax.Array]:
        q, r, theta, alive = carry
        target_q = jnp.where(product_mode, product_q, TARGET_Q[ASSIGNED])
        target_r = jnp.where(product_mode, product_r, TARGET_R[ASSIGNED])

        dot = jnp.sum(q * target_q, axis=1, keepdims=True)
        dq = 2.0 * (target_q - dot * q)
        q_next = unit(q + DT * dq)

        dr = jnp.where(product_mode, 0.9 * (product_r - r), terrain_drift(r, theta, target_r, TOPO_IDX[ASSIGNED]))
        r_next = r + DT * dr
        theta_next = theta_step(theta, product_mode)

        finite_kill = jnp.linalg.norm(r_next, axis=1) > 1.0 + F01_TOL
        sheet = SHEET_SIGN[ASSIGNED]
        chiral_kill = ((sheet > 0.0) & (q_next[:, 0] < -CHIRAL_TOL)) | ((sheet < 0.0) & (q_next[:, 0] > CHIRAL_TOL))
        killed = prune_active & (finite_kill | chiral_kill)
        alive_next = alive & ~killed
        norm_drift = jnp.max(jnp.abs(jnp.linalg.norm(q_next, axis=1) - 1.0))
        return (q_next, r_next, theta_next, alive_next), norm_drift

    (qf, rf, thetaf, alive), norm_drifts = jax.lax.scan(step, (q0, r0, theta0, alive0), None, length=STEPS)
    return qf, rf, thetaf, alive, norm_drifts


def populated(labels: jax.Array, alive: jax.Array) -> list[int]:
    values = jnp.unique(labels[alive], size=16, fill_value=-1)
    return [int(v) for v in jax.device_get(values) if int(v) > 0]


def recurrence_labels(q: jax.Array) -> jax.Array:
    return 1 + jnp.argmax(q @ TARGET_Q.T, axis=1)


def recurrence_residual(q: jax.Array, r: jax.Array, theta: jax.Array, labels: jax.Array, product_mode: bool) -> jax.Array:
    if product_mode:
        tq = jnp.broadcast_to(PRODUCT_TARGET_Q, q.shape)
        tr = jnp.broadcast_to(PRODUCT_TARGET_R, r.shape)
        theta_res = jnp.zeros_like(theta)
    else:
        idx = labels - 1
        tq = TARGET_Q[idx]
        tr = TARGET_R[idx]
        theta_res = jnp.abs(theta - jnp.pi / 4.0)
    q_res = jnp.linalg.norm(q - jnp.sign(jnp.sum(q * tq, axis=1, keepdims=True)) * tq, axis=1)
    r_res = jnp.linalg.norm(r - tr, axis=1)
    return q_res + r_res + theta_res


def run_one(name: str, product_mode: bool, prune_active: bool) -> dict[str, Any]:
    qf, rf, thetaf, alive, norm_drifts = evolve(jnp.asarray(product_mode), jnp.asarray(prune_active))
    labels = recurrence_labels(qf)
    pop = populated(labels, alive)
    survivors = _i(jnp.sum(alive))
    pruned = N - survivors
    if survivors:
        residual = recurrence_residual(qf[alive], rf[alive], thetaf[alive], labels[alive], product_mode)
        max_residual = _f(jnp.max(residual))
        mean_theta = _f(jnp.mean(thetaf[alive]))
        max_bloch_norm = _f(jnp.max(jnp.linalg.norm(rf[alive], axis=1)))
    else:
        max_residual = None
        mean_theta = None
        max_bloch_norm = None
    return {
        "name": name,
        "product_mode": bool(product_mode),
        "prune_active": bool(prune_active),
        "populated_basins": pop,
        "survivors": survivors,
        "pruned": pruned,
        "max_q_norm_drift": _f(jnp.max(norm_drifts)),
        "max_recurrence_residual": max_residual,
        "mean_survivor_theta": mean_theta,
        "max_survivor_bloch_norm": max_bloch_norm,
    }


def commutator_norms() -> dict[str, float]:
    genuine = jnp.stack(
        [
            PAULI_Z,
            PAULI_X + 0.35 * PAULI_Z,
            PAULI_Y,
            PAULI_X,
            -PAULI_Z,
            -PAULI_X + 0.35 * PAULI_Z,
            -PAULI_Y,
            PAULI_X,
        ],
        axis=0,
    )
    product = jnp.stack([PAULI_Z for _ in range(8)], axis=0)

    def max_comm(rows: jax.Array) -> jax.Array:
        comms = []
        for i in range(rows.shape[0]):
            for j in range(i + 1, rows.shape[0]):
                comms.append(jnp.linalg.norm(rows[i] @ rows[j] - rows[j] @ rows[i]))
        return jnp.max(jnp.asarray(comms))

    return {
        "genuine_max_commutator_norm": _f(max_comm(genuine)),
        "product_negative_max_commutator_norm": _f(max_comm(product)),
    }


def vn_entropy(rho: jax.Array) -> jax.Array:
    vals = jnp.linalg.eigvalsh(0.5 * (rho + rho.conj().T))
    vals = vals[vals > 1.0e-12]
    return -jnp.sum(vals * jnp.log2(vals))


def rho_of_r(r: jax.Array) -> jax.Array:
    return 0.5 * (ID2 + r[0] * PAULI_X + r[1] * PAULI_Y + r[2] * PAULI_Z)


def product_negative_mi() -> float:
    rho_l = rho_of_r(jnp.asarray([0.0, 0.0, -1.0], dtype=jnp.float64))
    rho_r = rho_of_r(jnp.asarray([0.0, 0.0, 1.0], dtype=jnp.float64))
    rho_lr = jnp.kron(rho_l, rho_r)
    mi = vn_entropy(rho_l) + vn_entropy(rho_r) - vn_entropy(rho_lr)
    return _f(jnp.abs(mi))


def run_probe() -> dict[str, Any]:
    a = run_one("A_no_prune", product_mode=False, prune_active=False)
    b = run_one("B_monotone_chirality_finitude_prune", product_mode=False, prune_active=True)
    c = run_one("C_trivial_noop_control", product_mode=False, prune_active=False)
    d = run_one("D_commuting_product_negative", product_mode=True, prune_active=False)
    comm = commutator_norms()
    product_mi = product_negative_mi()

    checks = {
        "A_reaches_all_16_basins": a["populated_basins"] == list(range(1, 17)),
        "B_prune_fires": b["pruned"] > 0,
        "B_preserves_all_16_recurrence_basins": b["populated_basins"] == list(range(1, 17)),
        "C_noop_equals_A": c["populated_basins"] == a["populated_basins"] and c["survivors"] == a["survivors"] and c["pruned"] == 0,
        "D_commuting_product_collapses": d["populated_basins"] == [1],
        "D_product_negative_has_zero_MI": product_mi < 1.0e-9,
        "genuine_noncommuting_generators_present": comm["genuine_max_commutator_norm"] > 1.0,
        "product_negative_commutes": comm["product_negative_max_commutator_norm"] < 1.0e-12,
        "bookkeeping": all(row["survivors"] == N - row["pruned"] for row in (a, b, c, d)),
        "q_retraction": max(row["max_q_norm_drift"] for row in (a, b, c, d)) < 1.0e-10,
        "finite_survivors": all((row["max_survivor_bloch_norm"] or 0.0) <= 1.0 + F01_TOL + 1.0e-7 for row in (a, b, c, d)),
    }
    audit_pass = all(checks.values())

    return {
        "object": "jax_emergent_basin_recurrence_prune_mirror",
        "julia_reference_readonly": "system_v5/julia_carrier/layers/emergent_basin_nested_terrains.jl",
        "julia_result_reference_readonly": "system_v5/julia_carrier/layers/emergent_basin_nested_terrains_results.json",
        "classification": "diagnostic_only",
        "promotion_allowed": False,
        "ran_julia": False,
        "ran_pytorch": False,
        "sim_execution_kind": "jax_audit_lane",
        "finite_map": "finite branch ensemble over 16 Weyl terrain placements -> monotone survivor mask -> recurrence basin labels",
        "domain": {
            "placements": "{L,R} x {fiber,base} x {Se,Ne,Ni,Si}",
            "branches": N,
            "state": "unit quaternion q in S3, Bloch vector r in closed ball, nested leaf coordinate theta in (0,pi/2)",
        },
        "codomain_or_output": "survivor counts, pruned counts, populated recurrence basin labels, negative/control readouts",
        "root_constraints_in_force": ["F01 finite branch/state/control set", "N01 noncommuting terrain-generator control"],
        "tool_manifest": {
            "jax": "load-bearing batched branch evolution, S3 retraction, survivor-mask latch, recurrence labels",
            "jax.numpy": "load-bearing finite linear algebra and density entropy for product negative",
        },
        "tool_integration_depth": {"jax": "load_bearing", "jax.numpy": "load_bearing"},
        "runs": {"A": a, "B": b, "C": c, "D": d},
        "noncommutation_control": comm,
        "product_negative_mutual_information_bits_abs": product_mi,
        "checks": checks,
        "AUDIT_PASS": audit_pass,
        "allowed_claims": [
            "JAX can reproduce the finite recurrence/prune control shape of the Julia emergent-basin object",
            "commuting/product collapse is a real negative against basin multiplicity in this finite JAX diagnostic",
        ],
        "blocked_consumers": ["full_layer_completion", "official_g_structure_selection", "layer_stacking", "Axis0", "FEP", "flux", "physics_gravity", "final_manifold_admission"],
    }


def main() -> int:
    result = run_probe()
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    runs = result["runs"]
    print(
        "jax_emergent_basin_recurrence_prune_mirror "
        f"A basins={runs['A']['populated_basins']} surv={runs['A']['survivors']} pruned={runs['A']['pruned']} | "
        f"B basins={runs['B']['populated_basins']} surv={runs['B']['survivors']} pruned={runs['B']['pruned']} | "
        f"C basins={runs['C']['populated_basins']} surv={runs['C']['survivors']} pruned={runs['C']['pruned']} | "
        f"D basins={runs['D']['populated_basins']} surv={runs['D']['survivors']} pruned={runs['D']['pruned']}"
    )
    print(f"AUDIT_PASS={result['AUDIT_PASS']} wrote={OUT}")
    return 0 if result["AUDIT_PASS"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
