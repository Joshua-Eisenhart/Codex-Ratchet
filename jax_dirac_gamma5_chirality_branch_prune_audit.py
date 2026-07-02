#!/usr/bin/env python3
"""JAX audit of the Julia Dirac gamma5 branch/prune chirality object.

Role boundary:
  - JAX is the batched numerical stress/audit lane.
  - Julia is the native Clifford/full-spinor truth lane.
  - This is not PyTorch, not a PyTorch port, and not a native spinor engine.

Object under audit:
  - finite ensemble of normalized Dirac 4-spinors psi in C^4;
  - gamma5 is derived from Weyl-basis Dirac gamma matrices;
  - chiral charge q(psi)=Re(psi^dagger gamma5 psi);
  - branch/prune removes futures whose q ever crosses below -0.01;
  - selector proof requires gamma5 prune to kill forbidden basins, a
    rate-matched random prune to keep forbidden basins, and an inverted-sign
    prune to flip survivors into forbidden basins.

This receipt is diagnostic only. It supports the cross-audit harness, not layer
admission, bridge claims, Axis0/FEP, flux, physics, or final manifold claims.
"""

from __future__ import annotations

import json
from pathlib import Path

from jax import config

config.update("jax_enable_x64", True)

import jax
import jax.numpy as jnp


N = 600
DRAW_MULTIPLE = 10
KEY_SEED = 20260305
RANDOM_PRUNE_SEED = 11
T_END = 12.0
DT = 1.0e-2
STEPS = int(T_END / DT)
GAMMA5_PRUNE_THRESHOLD = -0.01
INVERTED_SIGN_THRESHOLD = 0.99
ALLOWED = {1, 2}
FORBIDDEN = {3, 4}

I = 1j
C4 = jnp.eye(4, dtype=jnp.complex128)
I2 = jnp.eye(2, dtype=jnp.complex128)
Z2 = jnp.zeros((2, 2), dtype=jnp.complex128)
SX = jnp.asarray([[0, 1], [1, 0]], dtype=jnp.complex128)
SY = jnp.asarray([[0, -I], [I, 0]], dtype=jnp.complex128)
SZ = jnp.asarray([[1, 0], [0, -1]], dtype=jnp.complex128)
ETA = jnp.diag(jnp.asarray([1, -1, -1, -1], dtype=jnp.complex128))


def blk(a: jax.Array, b: jax.Array, c: jax.Array, d: jax.Array) -> jax.Array:
    return jnp.block([[a, b], [c, d]])


G0 = blk(Z2, I2, I2, Z2)
G1 = blk(Z2, SX, -SX, Z2)
G2 = blk(Z2, SY, -SY, Z2)
G3 = blk(Z2, SZ, -SZ, Z2)
GAMMAS = jnp.stack([G0, G1, G2, G3], axis=0)
G5 = I * G0 @ G1 @ G2 @ G3

SROT = G1 @ G2 / 2.0
SBOOST = G0 @ G1 / 2.0


def rot_u(a: float) -> jax.Array:
    return jnp.cos(a / 2.0) * C4 + 2.0 * jnp.sin(a / 2.0) * SROT


def boost_u(a: float) -> jax.Array:
    return jnp.cosh(a / 2.0) * C4 + 2.0 * jnp.sinh(a / 2.0) * SBOOST


def normalize(psi: jax.Array) -> jax.Array:
    return psi / jnp.linalg.norm(psi, axis=-1, keepdims=True)


TARGETS = normalize(
    jnp.asarray(
        [
            [0, 0, 1, 0.3],
            [0, 0, 0.3, 1],
            [1, 0.3, 0, 0],
            [0.3, 1, 0, 0],
        ],
        dtype=jnp.complex128,
    )
)


def dagger_dot(a: jax.Array, b: jax.Array) -> jax.Array:
    return jnp.sum(jnp.conj(a) * b, axis=-1)


def chiral_charge(psi: jax.Array) -> jax.Array:
    return jnp.real(jnp.einsum("...i,ij,...j->...", jnp.conj(psi), G5, psi))


def nearest_labels(psi: jax.Array, targets: jax.Array) -> jax.Array:
    overlaps = jnp.abs(jnp.conj(psi) @ targets.T) ** 2
    return jnp.argmax(overlaps, axis=-1) + 1


def nearest_targets(psi: jax.Array, targets: jax.Array) -> jax.Array:
    overlaps = jnp.abs(jnp.conj(psi) @ targets.T) ** 2
    return targets[jnp.argmax(overlaps, axis=-1)]


def flow(psi: jax.Array, targets: jax.Array) -> jax.Array:
    target = nearest_targets(psi, targets)
    align = dagger_dot(psi, target)[..., None]
    return 2.0 * (target - align * psi)


def gamma5_verification() -> dict:
    g5sq = float(jnp.max(jnp.abs(G5 @ G5 - C4)))
    anti = float(jnp.max(jnp.asarray([jnp.max(jnp.abs(G5 @ g + g @ G5)) for g in GAMMAS])))
    cliff = float(
        jnp.max(
            jnp.asarray(
                [
                    jnp.max(jnp.abs(GAMMAS[m] @ GAMMAS[n] + GAMMAS[n] @ GAMMAS[m] - 2 * ETA[m, n] * C4))
                    for m in range(4)
                    for n in range(4)
                ]
            )
        )
    )
    u_rot = rot_u(0.7)
    u_boost = boost_u(0.7)
    rot_commute = float(jnp.max(jnp.abs(G5 @ SROT - SROT @ G5)))
    rot_unitary = float(jnp.max(jnp.abs(jnp.conj(u_rot.T) @ u_rot - C4)))
    boost_nonunitary_size = float(jnp.max(jnp.abs(jnp.conj(u_boost.T) @ u_boost - C4)))
    return {
        "g5_sq_eq_I": g5sq < 1.0e-12,
        "anticommutes": anti < 1.0e-12,
        "clifford_relations": cliff < 1.0e-12,
        "rotation_commute": rot_commute < 1.0e-12,
        "rot_unitary": rot_unitary < 1.0e-10,
        "boost_nonunitary": boost_nonunitary_size > 1.0e-3,
        "max_g5sq_error": g5sq,
        "max_anticomm_error": anti,
        "max_clifford_error": cliff,
        "boost_nonunitary_size": boost_nonunitary_size,
    }


def branch_ensemble() -> jax.Array:
    key = jax.random.PRNGKey(KEY_SEED)
    raw = jax.random.normal(key, (DRAW_MULTIPLE * N, 4, 2), dtype=jnp.float64)
    complex_raw = raw[..., 0] + 1j * raw[..., 1]
    unit = normalize(complex_raw)
    mask = chiral_charge(unit) > 0.1
    count = int(jnp.sum(mask))
    if count < N:
        raise RuntimeError(f"insufficient q_gamma5>0.1 candidates: {count} < {N}")
    idx = jnp.nonzero(mask, size=N, fill_value=0)[0]
    return unit[idx]


@jax.jit
def evolve(psi0: jax.Array, targets: jax.Array, prune_code: jax.Array) -> tuple[jax.Array, jax.Array]:
    alive0 = jnp.ones((psi0.shape[0],), dtype=bool)

    def step(carry: tuple[jax.Array, jax.Array], _unused: None) -> tuple[tuple[jax.Array, jax.Array], None]:
        psi, alive = carry
        k1 = flow(psi, targets)
        k2 = flow(normalize(psi + 0.5 * DT * k1), targets)
        k3 = flow(normalize(psi + 0.5 * DT * k2), targets)
        k4 = flow(normalize(psi + DT * k3), targets)
        psi_next = normalize(psi + (DT / 6.0) * (k1 + 2.0 * k2 + 2.0 * k3 + k4))
        q = chiral_charge(psi_next)
        killed_gamma5 = q < GAMMA5_PRUNE_THRESHOLD
        killed_inverted = q > INVERTED_SIGN_THRESHOLD
        killed = jnp.where(prune_code == 1, killed_gamma5, jnp.where(prune_code == 3, killed_inverted, False))
        alive_next = jnp.logical_and(alive, jnp.logical_not(killed))
        return (psi_next, alive_next), None

    (psif, alivef), _ = jax.lax.scan(step, (psi0, alive0), xs=None, length=STEPS)
    return psif, alivef


def classify(name: str, psi0: jax.Array, targets: jax.Array, prune_code: int) -> tuple[dict, jax.Array, jax.Array]:
    psif, alive = evolve(psi0, targets, jnp.asarray(prune_code))
    labels = nearest_labels(psif, targets)
    survivor_labels = labels[alive]
    populated = sorted(int(x) for x in jnp.unique(survivor_labels))
    survivors = int(jnp.sum(alive))
    pruned = N - survivors
    return {
        "name": name,
        "populated": populated,
        "survivors": survivors,
        "pruned": pruned,
        "max_norm_drift": float(jnp.max(jnp.abs(jnp.linalg.norm(psif, axis=-1) - 1.0))),
    }, psif, alive


def transformed(states: jax.Array, u: jax.Array) -> jax.Array:
    return normalize(states @ u.T)


def rate_matched_random_populated(labels_a: jax.Array, k: int) -> list[int]:
    key = jax.random.PRNGKey(RANDOM_PRUNE_SEED)
    perm = jax.random.permutation(key, N)
    doomed = jnp.zeros((N,), dtype=bool).at[perm[:k]].set(True)
    survivors = labels_a[jnp.logical_not(doomed)]
    return sorted(int(x) for x in jnp.unique(survivors))


def main() -> None:
    gamma = gamma5_verification()
    base = branch_ensemble()

    run_a, psif_a, alive_a = classify("A_no_prune", base, TARGETS, 0)
    run_b, psif_b, alive_b = classify("B_gamma5_prune", base, TARGETS, 1)
    run_c, _psif_c, alive_c = classify("C_trivial_control", base, TARGETS, 2)
    run_inv, _psif_inv, _alive_inv = classify("D_inverted_sign_prune", base, TARGETS, 3)

    labels_a = nearest_labels(psif_a, TARGETS)
    random_pop = rate_matched_random_populated(labels_a, run_b["pruned"])

    u_rot = rot_u(0.7)
    u_boost = boost_u(0.7)
    base_rot = transformed(base, u_rot)
    targets_rot = transformed(TARGETS, u_rot)
    base_boost = transformed(base, u_boost)
    targets_boost = transformed(TARGETS, u_boost)
    run_rot, _psif_rot, alive_rot = classify("reported_rotation_gamma5_prune", base_rot, targets_rot, 1)
    run_boost, _psif_boost, alive_boost = classify("reported_boost_gamma5_prune", base_boost, targets_boost, 1)

    a = set(run_a["populated"])
    b = set(run_b["populated"])
    inv = set(run_inv["populated"])
    random_set = set(random_pop)
    max_norm_drift = max(run["max_norm_drift"] for run in (run_a, run_b, run_c, run_inv, run_rot, run_boost))

    checks = {
        "gamma5_genuine": bool(
            gamma["g5_sq_eq_I"]
            and gamma["anticommutes"]
            and gamma["clifford_relations"]
            and gamma["rotation_commute"]
            and gamma["rot_unitary"]
        ),
        "A_reaches_forbidden": bool(a & FORBIDDEN),
        "B_kills_all_forbidden": bool((b & FORBIDDEN) == set()),
        "B_preserves_allowed": bool((a & ALLOWED) <= b),
        "control_C_equals_A": bool(run_c["populated"] == run_a["populated"] and run_c["pruned"] == 0 and alive_c.tolist() == alive_a.tolist()),
        "B_pruned_some_A_none": bool(run_b["pruned"] > 0 and run_a["pruned"] == 0),
        "rate_matched_random_KEEPS_forbidden": bool(random_set & FORBIDDEN),
        "inverted_sign_flips_to_forbidden": bool((inv & ALLOWED) == set() and bool(inv & FORBIDDEN)),
        "norm_drift_small": bool(max_norm_drift < 1.0e-3),
    }
    audit_pass = all(checks.values())

    receipt = {
        "name": "jax_dirac_gamma5_chirality_branch_prune_audit",
        "object": "JAX cross-audit of Julia branch_prune_dirac_gamma5_chirality_object",
        "lane": "jax_batched_stress_runner_not_native_spinor_engine_not_pytorch_port",
        "classification": "diagnostic_jax_audit",
        "promotion_allowed": False,
        "ran_julia": False,
        "ran_pytorch": False,
        "claim_boundary": (
            "Cross-audit harness evidence only. This does not admit a layer, bridge, "
            "Axis0/FEP, flux, physics, or final manifold claim."
        ),
        "finite_map": (
            "finite C4 Dirac spinor ensemble -> RK4 retracted flow toward nearest target -> "
            "gamma5 monotone chirality prune -> survivor basin sets"
        ),
        "domain": {
            "futures": N,
            "state": "normalized Dirac 4-spinor psi in C^4",
            "initial_filter": "q_gamma5(psi)>0.1",
        },
        "codomain_or_output": {
            "survivor_basin_sets": "labels {1,2,3,4}",
            "gamma5_selector_controls": "rate-matched random prune and inverted-sign prune",
            "reported_limits": "rotation covariance and boost variance reported, not used as selector proof",
        },
        "root_constraints_in_force": {
            "F01": "finite ensemble, finite C4 spinors, finite targets, finite RK4 steps",
            "N01": "Dirac gamma matrices anticommute; monotone order-sensitive prune latch",
        },
        "tool_manifest": {
            "jax": "load_bearing batched complex spinor flow, gamma5 charge, latch, and controls",
            "json": "supportive receipt serialization",
        },
        "tool_integration_depth": {"jax": "load_bearing", "json": "supportive"},
        "blocked_consumers": [
            "layer_stacking",
            "flux",
            "xi_phi0",
            "axis0",
            "fep_holodeck",
            "physics_gravity",
            "final_manifold_admission",
        ],
        "parameters": {
            "N": N,
            "rng_seed": KEY_SEED,
            "draw_rows": DRAW_MULTIPLE * N,
            "dt": DT,
            "t_end": T_END,
            "steps": STEPS,
            "gamma5_prune_threshold": GAMMA5_PRUNE_THRESHOLD,
            "inverted_sign_threshold": INVERTED_SIGN_THRESHOLD,
            "rate_matched_random_seed": RANDOM_PRUNE_SEED,
        },
        "gamma5_verification": gamma,
        "runs": {
            "A": run_a,
            "B_gamma5": run_b,
            "C_control": run_c,
            "D_inverted_sign": run_inv,
            "rate_matched_random_populated": random_pop,
        },
        "reported_limits": {
            "gamma5_prune_rotation_covariant": bool(alive_rot.tolist() == alive_b.tolist() and run_rot["populated"] == run_b["populated"]),
            "gamma5_prune_boost_changes": bool(alive_boost.tolist() != alive_b.tolist() or run_boost["populated"] != run_b["populated"]),
            "rotation_B": run_rot,
            "boost_B": run_boost,
        },
        "max_norm_drift": max_norm_drift,
        "checks": checks,
        "AUDIT_PASS": audit_pass,
        "julia_reference_info_only": {
            "A": [1, 2, 3, 4],
            "B_gamma5": [1, 2],
            "C_control": [1, 2, 3, 4],
            "inverted_survivors": [3, 4],
            "random_prune_survivors": [1, 2, 3, 4],
            "B_pruned": 130,
        },
    }
    Path("jax_dirac_gamma5_chirality_branch_prune_audit_results.json").write_text(
        json.dumps(receipt, indent=2) + "\n"
    )

    print(
        f"A basins={run_a['populated']} surv={run_a['survivors']} pruned={run_a['pruned']} | "
        f"B basins={run_b['populated']} surv={run_b['survivors']} pruned={run_b['pruned']} | "
        f"C basins={run_c['populated']} surv={run_c['survivors']} pruned={run_c['pruned']} | "
        f"random={random_pop} inverted={run_inv['populated']}"
    )
    print(f"AUDIT_PASS={audit_pass}")


if __name__ == "__main__":
    main()
