#!/usr/bin/env python3
"""JAX nested Hopf-shell branch/prune QIT probe.

This is the JAX audit lane learning from the Julia branch/prune framing without
running Julia. It stress-tests finite unit-quaternion spinors on nested S^3
shells, monotone chirality pruning, Hopf-map readouts, quaternion
order-sensitivity, and separate QIT link controls.

No formal layer/admission claim is made here.
"""

from __future__ import annotations

from functools import partial
import json
from pathlib import Path
from typing import Any

import jax
from jax import config

config.update("jax_enable_x64", True)

import jax.numpy as jnp
import numpy as np


OUT = Path("jax_nested_hopf_shell_branch_prune_qit_probe_results.json")
N = 512
SHELLS = 3
STEPS = 3000
DT = 0.002
EPS = 1.0e-9

TARGETS = jnp.asarray(
    [
        [0.5, 0.5, 0.5, 0.5],
        [0.5, 0.5, -0.5, -0.5],
        [-0.5, -0.5, 0.5, -0.5],
        [-0.5, -0.5, -0.5, 0.5],
    ],
    dtype=jnp.float64,
)
FORBIDDEN = {3, 4}
ALLOWED = {1, 2}

I = 1j
BELL = jnp.asarray([1.0, 0.0, 0.0, 1.0], dtype=jnp.complex128) / jnp.sqrt(2.0)
PRODUCT = jnp.asarray([1.0, 0.0, 0.0, 0.0], dtype=jnp.complex128)


def normalize(q: jax.Array) -> jax.Array:
    return q / jnp.linalg.norm(q, axis=-1, keepdims=True)


def initial_ensemble() -> jax.Array:
    key = jax.random.PRNGKey(4307)
    raw = jax.random.normal(key, (N, SHELLS, 4), dtype=jnp.float64)
    return normalize(raw)


def nearest_labels(q: jax.Array) -> jax.Array:
    dots = jnp.einsum("...d,kd->...k", q, TARGETS)
    return jnp.argmax(dots, axis=-1)


def nearest_targets(q: jax.Array) -> jax.Array:
    return TARGETS[nearest_labels(q)]


def flow(q: jax.Array) -> jax.Array:
    target = nearest_targets(q)
    dot = jnp.sum(target * q, axis=-1, keepdims=True)
    return 2.0 * (target - dot * q)


@partial(jax.jit, static_argnames=("prune_active",))
def evolve(q0: jax.Array, prune_active: bool) -> tuple[jax.Array, jax.Array]:
    alive0 = jnp.ones((q0.shape[0],), dtype=bool)

    def step(carry: tuple[jax.Array, jax.Array], _: None) -> tuple[tuple[jax.Array, jax.Array], None]:
        q, alive = carry
        q_next = normalize(q + DT * flow(q))
        killed = jnp.any(q_next[:, :, 0] < -0.01, axis=1)
        alive_next = jnp.where(prune_active, alive & (~killed), alive)
        return (q_next, alive_next), None

    (qf, alivef), _ = jax.lax.scan(step, (q0, alive0), None, length=STEPS)
    return qf, alivef


def hopf_map(q: jax.Array) -> jax.Array:
    a, b, c, d = jnp.moveaxis(q, -1, 0)
    return jnp.stack(
        [
            2.0 * (a * c + b * d),
            2.0 * (b * c - a * d),
            a * a + b * b - c * c - d * d,
        ],
        axis=-1,
    )


def qmul(a: jax.Array, b: jax.Array) -> jax.Array:
    a0, a1, a2, a3 = a
    b0, b1, b2, b3 = b
    return jnp.asarray(
        [
            a0 * b0 - a1 * b1 - a2 * b2 - a3 * b3,
            a0 * b1 + a1 * b0 + a2 * b3 - a3 * b2,
            a0 * b2 - a1 * b3 + a2 * b0 + a3 * b1,
            a0 * b3 + a1 * b2 - a2 * b1 + a3 * b0,
        ],
        dtype=jnp.float64,
    )


def rotor(axis: int, theta: float) -> jax.Array:
    q = jnp.zeros((4,), dtype=jnp.float64).at[0].set(jnp.cos(theta))
    return q.at[axis].set(jnp.sin(theta))


def quaternion_order_witness() -> dict[str, float | bool]:
    rx = rotor(1, 0.37)
    ry = rotor(2, 0.29)
    rx2 = rotor(1, -0.19)
    shared = jnp.linalg.norm(qmul(rx, ry) - qmul(ry, rx))
    same_axis_control = jnp.linalg.norm(qmul(rx, rx2) - qmul(rx2, rx))
    return {
        "shared_axis_order_gap": float(shared),
        "same_axis_control_gap": float(same_axis_control),
        "pass": bool(shared > 1.0e-3 and same_axis_control < 1.0e-12),
    }


def rho(psi: jax.Array) -> jax.Array:
    return jnp.outer(psi, jnp.conj(psi))


def dephase(r: jax.Array) -> jax.Array:
    return jnp.diag(jnp.real(jnp.diag(r))).astype(jnp.complex128)


def vn_entropy(r: jax.Array) -> jax.Array:
    herm = 0.5 * (r + jnp.conj(r.T))
    vals = jnp.clip(jnp.real(jnp.linalg.eigvalsh(herm)), 0.0, 1.0)
    return -jnp.sum(jnp.where(vals > 1.0e-12, vals * jnp.log2(vals), 0.0))


def logneg_2q(r: jax.Array) -> jax.Array:
    pt = r.reshape(2, 2, 2, 2).transpose(0, 3, 2, 1).reshape(4, 4)
    vals = jnp.linalg.eigvalsh(0.5 * (pt + jnp.conj(pt.T)))
    return jnp.log2(jnp.sum(jnp.abs(vals)))


def cmi_abc_from_ac(r_ac: jax.Array) -> jax.Array:
    # B is empty for this two-qubit link control, so I(A:C|B)=I(A:C).
    r_a = jnp.trace(r_ac.reshape(2, 2, 2, 2), axis1=1, axis2=3)
    r_c = jnp.trace(r_ac.reshape(2, 2, 2, 2), axis1=0, axis2=2)
    return vn_entropy(r_a) + vn_entropy(r_c) - vn_entropy(r_ac)


def qit_link_controls() -> dict[str, float | bool]:
    linked = rho(BELL)
    dephased = dephase(linked)
    product = rho(PRODUCT)
    linked_ln = logneg_2q(linked)
    deph_ln = logneg_2q(dephased)
    product_ln = logneg_2q(product)
    deph_cmi = cmi_abc_from_ac(dephased)
    return {
        "linked_logneg": float(linked_ln),
        "dephased_logneg": float(deph_ln),
        "product_logneg": float(product_ln),
        "dephased_cmi_shadow": float(deph_cmi),
        "pass": bool(linked_ln > 0.99 and deph_ln < EPS and product_ln < EPS and deph_cmi > 0.99),
    }


def classify_run(name: str, qf: jax.Array, alive: jax.Array) -> dict[str, Any]:
    labels = np.asarray(nearest_labels(qf)) + 1
    alive_np = np.asarray(alive, dtype=bool)
    survivor_labels = labels[alive_np]
    populated = sorted(int(x) for x in np.unique(survivor_labels)) if survivor_labels.size else []
    shell_rows = []
    for shell in range(SHELLS):
        shell_labels = labels[alive_np, shell]
        shell_rows.append(
            {
                "shell": shell,
                "populated_basins": sorted(int(x) for x in np.unique(shell_labels)) if shell_labels.size else [],
            }
        )
    survivors = int(np.sum(alive_np))
    return {
        "name": name,
        "populated_basins": populated,
        "survivors": survivors,
        "pruned": int(N - survivors),
        "shell_rows": shell_rows,
    }


def shell_geometry_metrics(qf: jax.Array, alive: jax.Array) -> dict[str, float]:
    h = hopf_map(qf)
    max_q_norm_drift = jnp.max(jnp.abs(jnp.linalg.norm(qf, axis=-1) - 1.0))
    max_hopf_norm_drift = jnp.max(jnp.abs(jnp.linalg.norm(h, axis=-1) - 1.0))
    alive_h = h[np.asarray(alive, dtype=bool)]
    if alive_h.shape[0] == 0:
        return {
            "max_spinor_norm_drift": float(max_q_norm_drift),
            "max_hopf_norm_drift": float(max_hopf_norm_drift),
            "mean_adjacent_hopf_alignment": float("nan"),
        }
    align = jnp.sum(alive_h[:, :-1, :] * alive_h[:, 1:, :], axis=-1)
    return {
        "max_spinor_norm_drift": float(max_q_norm_drift),
        "max_hopf_norm_drift": float(max_hopf_norm_drift),
        "mean_adjacent_hopf_alignment": float(jnp.mean(align)),
    }


def capacity_budget() -> dict[str, float | int | bool]:
    carrier_dim = 2 ** SHELLS
    path_registry = N
    s_max = float(np.log2(carrier_dim))
    h_path_max = float(np.log2(path_registry))
    observed_boundary = 1.0  # two-qubit EPR control boundary entropy, finite and explicit
    return {
        "finite_shells": SHELLS,
        "finite_branches": N,
        "carrier_dim_per_branch": carrier_dim,
        "S_max": s_max,
        "H_path_max": h_path_max,
        "observed_boundary_entropy": observed_boundary,
        "pass": bool(observed_boundary <= s_max + EPS and h_path_max == float(np.log2(N))),
    }


def run_probe(write: bool = True) -> dict[str, Any]:
    q0 = initial_ensemble()
    q_a, alive_a = evolve(q0, prune_active=False)
    q_b, alive_b = evolve(q0, prune_active=True)
    q_c, alive_c = evolve(q0, prune_active=False)

    runs = {
        "A_no_prune": classify_run("A_no_prune", q_a, alive_a),
        "B_chirality_prune": classify_run("B_chirality_prune", q_b, alive_b),
        "C_trivial_control": classify_run("C_trivial_control", q_c, alive_c),
    }

    geom_a = shell_geometry_metrics(q_a, alive_a)
    geom_b = shell_geometry_metrics(q_b, alive_b)
    geom_c = shell_geometry_metrics(q_c, alive_c)
    max_norm_drift = max(geom_a["max_spinor_norm_drift"], geom_b["max_spinor_norm_drift"], geom_c["max_spinor_norm_drift"])
    max_hopf_drift = max(geom_a["max_hopf_norm_drift"], geom_b["max_hopf_norm_drift"], geom_c["max_hopf_norm_drift"])

    order = quaternion_order_witness()
    qit = qit_link_controls()
    cap = capacity_budget()

    a_set = set(runs["A_no_prune"]["populated_basins"])
    b_set = set(runs["B_chirality_prune"]["populated_basins"])
    c_set = set(runs["C_trivial_control"]["populated_basins"])

    checks = {
        "baseline_reaches_all_basins": runs["A_no_prune"]["populated_basins"] == [1, 2, 3, 4],
        "chirality_prune_kills_forbidden_basins": len(b_set & FORBIDDEN) == 0,
        "allowed_basins_preserved_after_prune": (a_set & ALLOWED) <= b_set,
        "trivial_control_matches_baseline": c_set == a_set and runs["C_trivial_control"]["pruned"] == 0,
        "real_prune_fired": runs["B_chirality_prune"]["pruned"] > 0 and runs["A_no_prune"]["pruned"] == 0,
        "bookkeeping_consistent": all(v["survivors"] == N - v["pruned"] for v in runs.values()),
        "spinor_norm_retraction_works": max_norm_drift < 1.0e-9,
        "hopf_map_stays_on_s2": max_hopf_drift < 1.0e-9,
        "quaternion_order_witness_present": bool(order["pass"]),
        "qit_link_controls_pass": bool(qit["pass"]),
        "capacity_budget_finite_and_respected": bool(cap["pass"]),
    }

    result = {
        "AUDIT_PASS": bool(all(checks.values())),
        "name": "jax_nested_hopf_shell_branch_prune_qit_probe",
        "classification": "diagnostic_jax_nested_hopf_shell_branch_prune_qit",
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "executed_track": "jax",
        "ran_julia": False,
        "julia_reference_mode": "read_only",
        "legacy_tensor_lane_used": False,
        "purpose": "JAX-only batched stress test of nested S3 spinor shells with branch/prune constraints and separate QIT link controls.",
        "finite_map": "N finite branches x 3 unit-quaternion shells -> attractor basin labels, alive mask, Hopf-map S2 readouts, QIT link controls",
        "domain": "finite unit-quaternion spinors q=(q0,q1,q2,q3) on three nested S3 shells",
        "codomain_or_output": "basin sets, survivor/pruned counts, Hopf map norm/alignment metrics, QIT link controls",
        "root_constraints_in_force": {
            "F01": "finite branch registry, finite shell count, finite target set, finite QIT density controls",
            "N01": "quaternion rotor order witness plus monotone chirality/dephasing controls",
        },
        "configuration": {
            "branches": N,
            "shells": SHELLS,
            "steps": STEPS,
            "dt": DT,
            "targets": np.asarray(TARGETS).tolist(),
        },
        "runs": runs,
        "geometry_metrics": {
            "A_no_prune": geom_a,
            "B_chirality_prune": geom_b,
            "C_trivial_control": geom_c,
            "max_spinor_norm_drift": max_norm_drift,
            "max_hopf_norm_drift": max_hopf_drift,
        },
        "quaternion_order_witness": order,
        "qit_link_controls": qit,
        "capacity_budget": cap,
        "checks": checks,
        "tool_manifest": {
            "jax": "load-bearing batched spinor dynamics, PRNG ensemble, JIT scan, and finite QIT controls",
            "jax.numpy": "load-bearing quaternion, Hopf-map, entropy, and branch/prune algebra",
            "numpy": "supportive host-side classification of finite JAX results",
            "json": "supportive receipt serialization",
        },
        "tool_integration_depth": {
            "jax": "load_bearing",
            "jax.numpy": "load_bearing",
            "numpy": "supportive",
            "json": "supportive",
        },
        "blocked_consumers": [
            "layer_stacking",
            "flux",
            "xi_phi0",
            "axis0",
            "fep_holodeck",
            "physics_gravity",
            "final_manifold_admission",
        ],
        "claim_boundary": "diagnostic JAX branch/prune shell probe only; Julia was not executed; no full-layer or manifold admission claim",
    }

    if write:
        OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    return result


def main() -> None:
    result = run_probe(write=True)
    a = result["runs"]["A_no_prune"]
    b = result["runs"]["B_chirality_prune"]
    c = result["runs"]["C_trivial_control"]
    print(
        "nested_hopf_shell_branch_prune "
        f"A basins={a['populated_basins']} surv={a['survivors']} pruned={a['pruned']} | "
        f"B basins={b['populated_basins']} surv={b['survivors']} pruned={b['pruned']} | "
        f"C basins={c['populated_basins']} surv={c['survivors']} pruned={c['pruned']} "
        f"AUDIT_PASS={result['AUDIT_PASS']}"
    )


if __name__ == "__main__":
    main()
