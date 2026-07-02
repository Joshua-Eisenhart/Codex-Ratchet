#!/usr/bin/env python3
"""JAX nested Hopf shell robustness sweep.

Role boundary:
  - JAX is the batched numerical stress/audit lane.
  - Julia is the native Clifford/full-spinor truth lane.
  - This is not PyTorch, not a PyTorch port, and not a native spinor engine.

The sweep reuses the finite branch/prune object from the single-point audit:
many possible futures, three nested unit-quaternion S3 shells per future,
Hopf base readouts S3 -> S2, retraction after every step, and a monotone
chirality-prune latch. It varies only the shell-to-shell coupling strength.

The point is not promotion. The point is to find whether the JAX approximation
keeps the structural invariants under parameter variation:
  - baseline reaches all four outer basins;
  - chirality prune removes forbidden outer basins 3 and 4;
  - no-op control equals baseline;
  - norm/base/fiber invariants stay tight;
  - positive shell coupling can improve nested Hopf-base alignment.
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
KEY_SEED = 271828
DT = 2.0e-3
T_END = 8.0
STEPS = int(T_END / DT)
PRUNE_Q0_THRESHOLD = -0.01
COUPLINGS = (0.0, 0.21, 0.42, 0.63)

TARGETS = jnp.asarray(
    [
        [0.5, 0.5, 0.5, 0.5],
        [0.5, 0.5, -0.5, -0.5],
        [-0.5, -0.5, 0.5, -0.5],
        [-0.5, -0.5, -0.5, 0.5],
    ],
    dtype=jnp.float64,
)

BLOCKED_CONSUMERS = [
    "layer_stacking",
    "flux",
    "xi_phi0",
    "axis0",
    "fep_holodeck",
    "physics_gravity",
    "final_manifold_admission",
]


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
    """U(1) fiber action, preserving the Hopf base."""
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
    """Gauge-fixed local Hopf lift S2 -> S3 away from the south pole."""
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


def nested_targets(q: jax.Array, coupling: jax.Array) -> jax.Array:
    local = nearest_targets(q)
    parent_base = hopf_base(q[:, :-1, :])
    lifted = lift_base_to_quat(parent_base)
    coupled = normalize((1.0 - coupling) * local[:, 1:, :] + coupling * lifted)
    return jnp.concatenate([local[:, :1, :], coupled], axis=1)


def flow(q: jax.Array, coupling: jax.Array) -> jax.Array:
    target = nested_targets(q, coupling)
    align = jnp.sum(target * q, axis=-1, keepdims=True)
    return 2.0 * (target - align * q)


def adjacent_base_distance(q: jax.Array) -> jax.Array:
    base = hopf_base(q)
    return jnp.linalg.norm(base[:, 1:, :] - base[:, :-1, :], axis=-1)


@jax.jit
def evolve(q0: jax.Array, coupling: jax.Array, prune_active: bool) -> tuple[jax.Array, jax.Array]:
    alive0 = jnp.ones((q0.shape[0],), dtype=bool)

    def step(carry: tuple[jax.Array, jax.Array], _unused: None) -> tuple[tuple[jax.Array, jax.Array], None]:
        q, alive = carry
        q_next = normalize(q + DT * flow(q, coupling))
        killed = jnp.logical_and(prune_active, jnp.any(q_next[:, :, 0] < PRUNE_Q0_THRESHOLD, axis=1))
        alive_next = jnp.logical_and(alive, jnp.logical_not(killed))
        return (q_next, alive_next), None

    (qf, alivef), _ = jax.lax.scan(step, (q0, alive0), xs=None, length=STEPS)
    return qf, alivef


def summarize_run(name: str, q0: jax.Array, coupling: float, prune_active: bool) -> tuple[dict, jax.Array, jax.Array]:
    qf, alive = evolve(q0, jnp.asarray(coupling, dtype=jnp.float64), prune_active)
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


def fiber_delta_for_initial(q0: jax.Array) -> float:
    flat = q0.reshape(-1, 4)
    theta = jnp.linspace(0.0, 2.0 * jnp.pi, flat.shape[0], dtype=jnp.float64)
    shifted = hopf_phase(flat, theta)
    return float(jnp.max(jnp.linalg.norm(hopf_base(flat) - hopf_base(shifted), axis=-1)))


def sweep_row(q0: jax.Array, coupling: float) -> dict:
    initial_alignment = float(jnp.mean(adjacent_base_distance(q0)))
    run_a, qf_a, alive_a = summarize_run("A_no_prune", q0, coupling, False)
    run_b, qf_b, _alive_b = summarize_run("B_chirality_prune", q0, coupling, True)
    run_c, qf_c, alive_c = summarize_run("C_trivial_control", q0, coupling, False)

    all_final = jnp.concatenate([qf_a.reshape(-1, 4), qf_b.reshape(-1, 4), qf_c.reshape(-1, 4)], axis=0)
    max_norm_drift = float(jnp.max(jnp.abs(jnp.linalg.norm(all_final, axis=-1) - 1.0)))
    max_base_norm_drift = float(
        jnp.max(jnp.abs(jnp.linalg.norm(hopf_base(all_final), axis=-1) - 1.0))
    )
    fiber_delta = fiber_delta_for_initial(q0)

    a = run_a["populated_outer_basins"]
    b = run_b["populated_outer_basins"]
    c = run_c["populated_outer_basins"]
    a_set = set(a)
    b_set = set(b)
    final_alignment = run_a["mean_adjacent_base_distance_survivors"]
    alignment_delta = initial_alignment - final_alignment
    alignment_improved = bool(alignment_delta > 1.0e-6)

    checks = {
        "baseline_all_outer_basins": a == [1, 2, 3, 4],
        "prune_kills_forbidden_outer_basins": (b_set & {3, 4}) == set(),
        "allowed_outer_basins_preserved": (a_set & {1, 2}) <= b_set,
        "trivial_control_noop": c == a and run_c["pruned"] == 0 and alive_c.tolist() == alive_a.tolist(),
        "real_prune_fired": run_b["pruned"] > 0 and run_a["pruned"] == 0,
        "bookkeeping_consistent": all(
            run["survivors"] == N - run["pruned"] for run in (run_a, run_b, run_c)
        ),
        "retraction_norm": max_norm_drift < 1.0e-3,
        "hopf_base_norm": max_base_norm_drift < 1.0e-3,
        "hopf_fiber_invariance": fiber_delta < 1.0e-9,
    }
    if coupling > 0.0:
        checks["positive_coupling_alignment_improves"] = alignment_improved

    return {
        "coupling": coupling,
        "initial_mean_adjacent_base_distance": initial_alignment,
        "final_A_mean_adjacent_base_distance": final_alignment,
        "alignment_delta": alignment_delta,
        "alignment_improved": alignment_improved,
        "max_norm_drift": max_norm_drift,
        "max_base_norm_drift": max_base_norm_drift,
        "hopf_fiber_max_delta": fiber_delta,
        "runs": {"A": run_a, "B": run_b, "C": run_c},
        "checks": checks,
        "row_pass": all(checks.values()),
    }


def main() -> None:
    q0 = branch_ensemble()
    rows = [sweep_row(q0, coupling) for coupling in COUPLINGS]
    positive_rows = [row for row in rows if row["coupling"] > 0.0]
    zero_rows = [row for row in rows if row["coupling"] == 0.0]
    zero_delta = zero_rows[0]["alignment_delta"] if zero_rows else float("nan")
    best_positive_delta = max((row["alignment_delta"] for row in positive_rows), default=float("-inf"))
    checks = {
        "all_rows_pass": all(row["row_pass"] for row in rows),
        "at_least_four_rows": len(rows) >= 4,
        "some_positive_coupling_alignment_improves": any(row["alignment_improved"] for row in positive_rows),
        "zero_coupling_present": len(zero_rows) == 1,
        "positive_coupling_beats_zero_control": best_positive_delta > zero_delta + 1.0e-6,
        "promotion_blocked": True,
    }
    audit_pass = all(checks.values())

    receipt = {
        "object": "JAX nested Hopf shell robustness sweep",
        "lane": "jax_batched_stress_runner_not_native_spinor_engine_not_pytorch_port",
        "classification": "diagnostic_jax_audit",
        "promotion_allowed": False,
        "claim_boundary": (
            "Parameter robustness audit only. This does not admit a layer, stacking, "
            "Axis0/FEP, flux, physics, or final manifold claim."
        ),
        "finite_map": (
            "finite nested S3 unit-quaternion futures -> retracted JAX flow under "
            "coupling sweep -> Hopf S2 base readouts and chirality-pruned basin sets"
        ),
        "domain": {
            "futures": N,
            "shells_per_future": SHELLS,
            "state": "unit quaternion q=(q0,q1,q2,q3) on S3 per shell",
            "couplings": list(COUPLINGS),
        },
        "codomain_or_output": {
            "per_coupling_survivor_outer_basin_sets": "basin labels {1,2,3,4}",
            "hopf_base_invariants": "S2 base norm and U1 fiber invariance",
            "nested_alignment": "adjacent shell Hopf-base distance before/after flow",
        },
        "root_constraints_in_force": {
            "F01": "finite ensemble, finite shells, finite coupling grid, finite steps, finite targets",
            "N01": "order-sensitive branch/evolve/prune latch; forbidden crossing at any step is irreversible",
        },
        "tool_manifest": {
            "jax": "load_bearing batched S3 evolution, retraction, latch, and invariant checks",
            "json": "supportive receipt serialization",
        },
        "tool_integration_depth": {
            "jax": "load_bearing",
            "json": "supportive",
        },
        "blocked_consumers": BLOCKED_CONSUMERS,
        "sweep_parameters": {
            "N": N,
            "shells": SHELLS,
            "rng_seed": KEY_SEED,
            "draw_rows": DRAW_MULTIPLE * N,
            "dt": DT,
            "t_end": T_END,
            "steps": STEPS,
            "prune_q0_threshold": PRUNE_Q0_THRESHOLD,
            "couplings": list(COUPLINGS),
        },
        "rows": rows,
        "checks": checks,
        "AUDIT_PASS": audit_pass,
    }
    Path("jax_nested_hopf_shell_robustness_sweep_results.json").write_text(
        json.dumps(receipt, indent=2) + "\n"
    )

    passed = sum(1 for row in rows if row["row_pass"])
    print(
        f"rows={len(rows)} row_pass={passed}/{len(rows)} "
        f"zero_delta={zero_delta:.6f} best_positive_delta={best_positive_delta:.6f}"
    )
    print(f"AUDIT_PASS={audit_pass}")


if __name__ == "__main__":
    main()
