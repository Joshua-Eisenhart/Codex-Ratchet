#!/usr/bin/env python3
"""JAX branch/prune audit lane for a Julia unit-quaternion spinor oracle.

This is intentionally a numerical stress/audit script, not a native spinor
engine and not a PyTorch port. It implements the finite spec directly:
batched unit-quaternion futures on S^3, tangent flow toward nearest fixed
attractor, monotone chirality pruning, retraction after every Euler step, and
structural invariant checks against the Julia oracle's basin-set behavior.
"""

from __future__ import annotations

import json
from pathlib import Path

from jax import config

config.update("jax_enable_x64", True)

import jax
import jax.numpy as jnp


N = 400
DRAW_MULTIPLE = 4
KEY_SEED = 42
T_END = 12.0
DT = 1.0e-3
STEPS = int(T_END / DT)
PRUNE_Q0_THRESHOLD = -0.01

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


def branch_ensemble() -> jax.Array:
    key = jax.random.PRNGKey(KEY_SEED)
    raw = jax.random.normal(key, (DRAW_MULTIPLE * N, 4), dtype=jnp.float64)
    unit = normalize(raw)
    mask = unit[:, 0] > 0.05
    candidate_count = int(jnp.sum(mask))
    if candidate_count < N:
        raise RuntimeError(f"insufficient q0>0.05 candidates: {candidate_count} < {N}")
    idx = jnp.nonzero(mask, size=N, fill_value=0)[0]
    return unit[idx]


def nearest_labels(q: jax.Array) -> jax.Array:
    return jnp.argmax(q @ TARGETS.T, axis=-1) + 1


def flow(q: jax.Array) -> jax.Array:
    dots = q @ TARGETS.T
    target = TARGETS[jnp.argmax(dots, axis=-1)]
    align = jnp.sum(target * q, axis=-1, keepdims=True)
    return 2.0 * (target - align * q)


@jax.jit
def evolve(q0: jax.Array, prune_active: bool) -> tuple[jax.Array, jax.Array]:
    alive0 = jnp.ones((q0.shape[0],), dtype=bool)

    def step(carry: tuple[jax.Array, jax.Array], _unused: None) -> tuple[tuple[jax.Array, jax.Array], None]:
        q, alive = carry
        q_next = normalize(q + DT * flow(q))
        killed = jnp.logical_and(prune_active, q_next[:, 0] < PRUNE_Q0_THRESHOLD)
        alive_next = jnp.logical_and(alive, jnp.logical_not(killed))
        return (q_next, alive_next), None

    (qf, alivef), _ = jax.lax.scan(step, (q0, alive0), xs=None, length=STEPS)
    return qf, alivef


def summarize_run(name: str, q0: jax.Array, prune_active: bool) -> tuple[dict, jax.Array]:
    qf, alive = evolve(q0, prune_active)
    labels = nearest_labels(qf)
    survivor_labels = labels[alive]
    populated = sorted(int(x) for x in jnp.unique(survivor_labels))
    pruned = int(N - jnp.sum(alive))
    row = {
        "name": name,
        "populated_basins": populated,
        "survivors": int(jnp.sum(alive)),
        "pruned": pruned,
    }
    return row, qf


def main() -> None:
    q0 = branch_ensemble()
    run_a, qf_a = summarize_run("A_no_prune", q0, False)
    run_b, qf_b = summarize_run("B_chirality_prune", q0, True)
    run_c, qf_c = summarize_run("C_trivial_control", q0, False)

    final_states = jnp.concatenate([qf_a, qf_b, qf_c], axis=0)
    max_norm_drift = float(jnp.max(jnp.abs(jnp.linalg.norm(final_states, axis=-1) - 1.0)))

    a = run_a["populated_basins"]
    b = run_b["populated_basins"]
    c = run_c["populated_basins"]
    a_set = set(a)
    b_set = set(b)

    checks = {
        "chk1_baseline_all_basins": a == [1, 2, 3, 4],
        "chk2_prune_kills_forbidden": (b_set & {3, 4}) == set(),
        "chk3_allowed_basins_preserved": (a_set & {1, 2}) <= b_set,
        "chk4_trivial_control_noop": c == a and run_c["pruned"] == 0,
        "chk5_real_prune_fired": run_b["pruned"] > 0 and run_a["pruned"] == 0,
        "chk6_bookkeeping_consistent": all(
            run["survivors"] == N - run["pruned"] for run in (run_a, run_b, run_c)
        ),
        "chk7_retraction_norm": max_norm_drift < 1.0e-3,
    }
    audit_pass = all(checks.values())

    receipt = {
        "object": "JAX branch/prune audit of Julia unit-quaternion spinor branch/prune oracle",
        "lane": "jax_audit_stress_tester_not_native_spinor_engine_not_pytorch_port",
        "N": N,
        "rng": {"jax_prng_key": KEY_SEED, "draw_rows": DRAW_MULTIPLE * N},
        "integrator": {
            "kind": "fixed_step_euler",
            "dt": DT,
            "t_end": T_END,
            "steps": STEPS,
            "retraction": "renormalize_to_unit_S3_after_every_step",
        },
        "prune_predicate": {
            "kind": "monotone_latch",
            "active_run": "B_chirality_prune",
            "condition": f"q0 < {PRUNE_Q0_THRESHOLD}",
        },
        "runs": {
            "A": run_a,
            "B": run_b,
            "C": run_c,
        },
        "max_norm_drift": max_norm_drift,
        "checks": checks,
        "AUDIT_PASS": audit_pass,
        "julia_reference_info_only": {
            "A": {"populated_basins": [1, 2, 3, 4], "survivors": 400, "pruned": 0},
            "B": {"populated_basins": [1, 2], "survivors": 293, "pruned": 107},
            "C": "same as A",
        },
    }
    Path("jax_branch_prune_audit_results.json").write_text(json.dumps(receipt, indent=2) + "\n")

    print(
        f"A basins={a} surv={run_a['survivors']} pruned={run_a['pruned']} | "
        f"B basins={b} surv={run_b['survivors']} pruned={run_b['pruned']} | "
        f"C basins={c} surv={run_c['survivors']} pruned={run_c['pruned']}"
    )
    print(f"AUDIT_PASS={audit_pass}")


if __name__ == "__main__":
    main()
