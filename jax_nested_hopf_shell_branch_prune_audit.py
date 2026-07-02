#!/usr/bin/env python3
"""Better JAX audit lane: nested Hopf shell branch/prune stress test.

JAX role here: batched numerical stress runner and invariant auditor.
Julia role (external/oracle lane): native Clifford/full-spinor truth.

This script does not use PyTorch and does not claim native spinor geometry.
It tests whether a constrained JAX approximation can preserve structural
integer/set invariants while evolving many possible futures on nested S3 shells.

Finite object:
  - N futures.
  - S nested shells per future.
  - each shell is a unit quaternion q=(q0,q1,q2,q3) in S3.
  - Hopf base h(q) in S2 is monitored as the shell geometry readout.
  - shell s>0 is weakly coupled to a Hopf lift of shell s-1's base.
  - branch/prune removes futures whose chirality coordinate q0 ever crosses
    below a forbidden threshold.
"""

from __future__ import annotations

import json
from pathlib import Path

from jax import config

config.update("jax_enable_x64", True)

import jax
import jax.numpy as jnp


N = 512
SHELLS = 3
DRAW_MULTIPLE = 12
KEY_SEED = 314159
DT = 2.0e-3
T_END = 8.0
STEPS = int(T_END / DT)
PRUNE_Q0_THRESHOLD = -0.01
COUPLING = 0.42

TARGETS = jnp.asarray(
    [
        [0.5, 0.5, 0.5, 0.5],
        [0.5, 0.5, -0.5, -0.5],
        [-0.5, -0.5, 0.5, -0.5],
        [-0.5, -0.5, -0.5, 0.5],
    ],
    dtype=jnp.float64,
)


def normalize(q: jax.Array) -> jax.Array:
    return q / jnp.linalg.norm(q, axis=-1, keepdims=True)


def hopf_base(q: jax.Array) -> jax.Array:
    """Hopf map S3 -> S2 for z1=q0+i q1, z2=q2+i q3."""
    a, b, c, d = q[..., 0], q[..., 1], q[..., 2], q[..., 3]
    return jnp.stack(
        [
            2.0 * (a * c + b * d),
            2.0 * (b * c - a * d),
            a * a + b * b - c * c - d * d,
        ],
        axis=-1,
    )


def hopf_phase(q: jax.Array, theta: jax.Array) -> jax.Array:
    """U(1) fiber action (z1,z2)->(e^{i theta}z1,e^{i theta}z2)."""
    co = jnp.cos(theta)
    si = jnp.sin(theta)
    a, b, c, d = q[..., 0], q[..., 1], q[..., 2], q[..., 3]
    return jnp.stack(
        [
            a * co - b * si,
            a * si + b * co,
            c * co - d * si,
            c * si + d * co,
        ],
        axis=-1,
    )


def lift_base_to_quat(base: jax.Array) -> jax.Array:
    """One gauge-fixed Hopf lift S2 -> S3 away from the south-pole singularity."""
    x, y, z = base[..., 0], base[..., 1], base[..., 2]
    r = jnp.sqrt(jnp.maximum((1.0 + z) / 2.0, 1.0e-12))
    c = x / (2.0 * r)
    d = -y / (2.0 * r)
    return normalize(jnp.stack([r, jnp.zeros_like(r), c, d], axis=-1))


def nearest_labels(q: jax.Array) -> jax.Array:
    return jnp.argmax(q @ TARGETS.T, axis=-1) + 1


def nearest_targets(q: jax.Array) -> jax.Array:
    return TARGETS[jnp.argmax(q @ TARGETS.T, axis=-1)]


def branch_ensemble() -> jax.Array:
    key = jax.random.PRNGKey(KEY_SEED)
    raw = jax.random.normal(key, (DRAW_MULTIPLE * N, SHELLS, 4), dtype=jnp.float64)
    unit = normalize(raw)
    mask = jnp.all(unit[:, :, 0] > 0.05, axis=1)
    count = int(jnp.sum(mask))
    if count < N:
        raise RuntimeError(f"insufficient all-shell q0>0.05 candidates: {count} < {N}")
    idx = jnp.nonzero(mask, size=N, fill_value=0)[0]
    return unit[idx]


def nested_targets(q: jax.Array) -> jax.Array:
    local = nearest_targets(q)
    parent_base = hopf_base(q[:, :-1, :])
    lifted = lift_base_to_quat(parent_base)
    coupled = normalize((1.0 - COUPLING) * local[:, 1:, :] + COUPLING * lifted)
    return jnp.concatenate([local[:, :1, :], coupled], axis=1)


def flow(q: jax.Array) -> jax.Array:
    target = nested_targets(q)
    align = jnp.sum(target * q, axis=-1, keepdims=True)
    return 2.0 * (target - align * q)


def adjacent_base_distance(q: jax.Array) -> jax.Array:
    base = hopf_base(q)
    return jnp.linalg.norm(base[:, 1:, :] - base[:, :-1, :], axis=-1)


@jax.jit
def evolve(q0: jax.Array, prune_active: bool) -> tuple[jax.Array, jax.Array]:
    alive0 = jnp.ones((q0.shape[0],), dtype=bool)

    def step(carry: tuple[jax.Array, jax.Array], _unused: None) -> tuple[tuple[jax.Array, jax.Array], None]:
        q, alive = carry
        q_next = normalize(q + DT * flow(q))
        killed = jnp.logical_and(prune_active, jnp.any(q_next[:, :, 0] < PRUNE_Q0_THRESHOLD, axis=1))
        alive_next = jnp.logical_and(alive, jnp.logical_not(killed))
        return (q_next, alive_next), None

    (qf, alivef), _ = jax.lax.scan(step, (q0, alive0), xs=None, length=STEPS)
    return qf, alivef


def summarize_run(name: str, q0: jax.Array, prune_active: bool) -> tuple[dict, jax.Array, jax.Array]:
    qf, alive = evolve(q0, prune_active)
    labels = nearest_labels(qf[:, 0, :])
    survivor_labels = labels[alive]
    populated = sorted(int(x) for x in jnp.unique(survivor_labels))
    survivors = int(jnp.sum(alive))
    pruned = N - survivors
    row = {
        "name": name,
        "populated_outer_basins": populated,
        "survivors": survivors,
        "pruned": pruned,
        "mean_adjacent_base_distance_survivors": float(jnp.mean(adjacent_base_distance(qf)[alive])),
    }
    return row, qf, alive


def main() -> None:
    q0 = branch_ensemble()
    initial_alignment = float(jnp.mean(adjacent_base_distance(q0)))

    run_a, qf_a, alive_a = summarize_run("A_no_prune", q0, False)
    run_b, qf_b, alive_b = summarize_run("B_chirality_prune", q0, True)
    run_c, qf_c, alive_c = summarize_run("C_trivial_control", q0, False)

    all_final = jnp.concatenate([qf_a.reshape(-1, 4), qf_b.reshape(-1, 4), qf_c.reshape(-1, 4)], axis=0)
    max_norm_drift = float(jnp.max(jnp.abs(jnp.linalg.norm(all_final, axis=-1) - 1.0)))
    max_base_norm_drift = float(
        jnp.max(jnp.abs(jnp.linalg.norm(hopf_base(all_final), axis=-1) - 1.0))
    )

    flat_q0 = q0.reshape(-1, 4)
    theta = jnp.linspace(0.0, 2.0 * jnp.pi, flat_q0.shape[0], dtype=jnp.float64)
    fiber_delta = float(jnp.max(jnp.linalg.norm(hopf_base(flat_q0) - hopf_base(hopf_phase(flat_q0, theta)), axis=-1)))

    a = run_a["populated_outer_basins"]
    b = run_b["populated_outer_basins"]
    c = run_c["populated_outer_basins"]
    a_set = set(a)
    b_set = set(b)

    checks = {
        "chk_baseline_all_outer_basins": a == [1, 2, 3, 4],
        "chk_prune_kills_forbidden_outer_basins": (b_set & {3, 4}) == set(),
        "chk_allowed_outer_basins_preserved": (a_set & {1, 2}) <= b_set,
        "chk_trivial_control_noop": c == a and run_c["pruned"] == 0 and alive_c.tolist() == alive_a.tolist(),
        "chk_real_prune_fired": run_b["pruned"] > 0 and run_a["pruned"] == 0,
        "chk_bookkeeping_consistent": all(
            run["survivors"] == N - run["pruned"] for run in (run_a, run_b, run_c)
        ),
        "chk_retraction_norm": max_norm_drift < 1.0e-3,
        "chk_hopf_base_norm": max_base_norm_drift < 1.0e-3,
        "chk_hopf_fiber_invariance": fiber_delta < 1.0e-9,
        "chk_nested_alignment_improves": run_a["mean_adjacent_base_distance_survivors"] < initial_alignment,
    }
    audit_pass = all(checks.values())

    receipt = {
        "object": "JAX nested Hopf shell branch/prune audit",
        "lane": "jax_batched_stress_runner_not_native_spinor_engine_not_pytorch_port",
        "classification": "diagnostic_jax_audit",
        "promotion_allowed": False,
        "claim_boundary": (
            "JAX constrained numerical audit only. This does not admit a layer, "
            "stacking, Axis0/FEP, flux, physics, or final manifold claim."
        ),
        "finite_map": (
            "batched nested S3 unit-quaternion shell futures -> retracted flow, "
            "Hopf S2 base readouts, chirality-pruned survivor basins"
        ),
        "domain": {
            "futures": N,
            "shells_per_future": SHELLS,
            "state": "unit quaternion q=(q0,q1,q2,q3) on S3 per shell",
        },
        "codomain_or_output": {
            "survivor_outer_basin_sets": "basin labels {1,2,3,4} after prune/no-prune/control",
            "hopf_base_invariants": "S2 base norm and U1 fiber invariance",
            "nested_alignment": "adjacent shell Hopf-base distance before/after coupled flow",
        },
        "root_constraints_in_force": {
            "F01": "finite ensemble, finite shells, finite steps, finite targets",
            "N01": "order-sensitive branch/evolve/prune latch; forbidden crossing at any step is irreversible",
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
        "parameters": {
            "N": N,
            "shells": SHELLS,
            "rng_seed": KEY_SEED,
            "draw_rows": DRAW_MULTIPLE * N,
            "dt": DT,
            "t_end": T_END,
            "steps": STEPS,
            "coupling": COUPLING,
            "prune_q0_threshold": PRUNE_Q0_THRESHOLD,
        },
        "runs": {"A": run_a, "B": run_b, "C": run_c},
        "initial_mean_adjacent_base_distance": initial_alignment,
        "max_norm_drift": max_norm_drift,
        "max_base_norm_drift": max_base_norm_drift,
        "hopf_fiber_max_delta": fiber_delta,
        "checks": checks,
        "AUDIT_PASS": audit_pass,
    }
    Path("jax_nested_hopf_shell_branch_prune_audit_results.json").write_text(
        json.dumps(receipt, indent=2) + "\n"
    )

    print(
        f"A basins={a} surv={run_a['survivors']} pruned={run_a['pruned']} "
        f"align={run_a['mean_adjacent_base_distance_survivors']:.6f} | "
        f"B basins={b} surv={run_b['survivors']} pruned={run_b['pruned']} "
        f"align={run_b['mean_adjacent_base_distance_survivors']:.6f} | "
        f"C basins={c} surv={run_c['survivors']} pruned={run_c['pruned']} "
        f"align={run_c['mean_adjacent_base_distance_survivors']:.6f}"
    )
    print(
        f"AUDIT_PASS={audit_pass} max_norm_drift={max_norm_drift:.3e} "
        f"fiber_delta={fiber_delta:.3e}"
    )


if __name__ == "__main__":
    main()
