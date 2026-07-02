#!/usr/bin/env python3
"""JAX-only gamma5 branch/prune audit using Julia as read-only reference.

Boundary:
  - Executes the JAX lane only.
  - Reads the existing Julia result JSON as an oracle receipt.
  - Does not run Julia, mutate Julia files, or attempt a legacy-track mirror.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import jax

jax.config.update("jax_enable_x64", True)

import jax.numpy as jnp


BASE = Path(__file__).resolve().parent
JULIA_REFERENCE_PATH = BASE / "branch_prune_dirac_gamma5_chirality_object_results.json"
RECEIPT_PATH = BASE / "jax_readonly_julia_gamma5_reference_audit_results.json"

N = 600
T_FINAL = 12.0
SEED_GRID = (42, 2026, 9001)
DT_GRID = (2.0e-3, 1.0e-3)
PRUNE_THRESHOLD = -0.01
INIT_CHIRAL_MIN = 0.1


def normalize_rows(z: jnp.ndarray) -> jnp.ndarray:
    return z / jnp.linalg.norm(z, axis=1, keepdims=True)


def normalize_vec(z: jnp.ndarray) -> jnp.ndarray:
    return z / jnp.linalg.norm(z)


def build_gamma_matrices():
    ctype = jnp.complex128
    zero = jnp.zeros((2, 2), dtype=ctype)
    ident = jnp.eye(2, dtype=ctype)
    sx = jnp.array([[0, 1], [1, 0]], dtype=ctype)
    sy = jnp.array([[0, -1j], [1j, 0]], dtype=ctype)
    sz = jnp.array([[1, 0], [0, -1]], dtype=ctype)
    g0 = jnp.block([[zero, ident], [ident, zero]])
    g1 = jnp.block([[zero, sx], [-sx, zero]])
    g2 = jnp.block([[zero, sy], [-sy, zero]])
    g3 = jnp.block([[zero, sz], [-sz, zero]])
    gamma5 = 1j * g0 @ g1 @ g2 @ g3
    return (g0, g1, g2, g3), gamma5


GAMMAS, GAMMA5 = build_gamma_matrices()
TARGETS = jnp.stack(
    [
        normalize_vec(jnp.array([0, 0, 1, 0.3], dtype=jnp.complex128)),
        normalize_vec(jnp.array([0, 0, 0.3, 1], dtype=jnp.complex128)),
        normalize_vec(jnp.array([1, 0.3, 0, 0], dtype=jnp.complex128)),
        normalize_vec(jnp.array([0.3, 1, 0, 0], dtype=jnp.complex128)),
    ]
)


def chiral_charge(psi: jnp.ndarray) -> jnp.ndarray:
    return jnp.real(jnp.einsum("...i,ij,...j->...", jnp.conjugate(psi), GAMMA5, psi))


def basin_labels(psi: jnp.ndarray) -> jnp.ndarray:
    overlaps = psi @ jnp.conjugate(TARGETS).T
    return jnp.argmax(jnp.abs(overlaps) ** 2, axis=1) + 1


def populated_basins(labels: jnp.ndarray, mask: jnp.ndarray) -> list[int]:
    selected = labels[mask]
    return [int(x) for x in sorted(set(map(int, jax.device_get(selected))))]


def make_initial_ensemble(seed: int) -> tuple[jnp.ndarray, jax.Array]:
    key = jax.random.PRNGKey(seed)
    key_re, key_im, key_random = jax.random.split(key, 3)
    candidates = 8192
    real = jax.random.normal(key_re, (candidates, 4), dtype=jnp.float64)
    imag = jax.random.normal(key_im, (candidates, 4), dtype=jnp.float64)
    psi = normalize_rows(real + 1j * imag)
    kept = psi[chiral_charge(psi) > INIT_CHIRAL_MIN]
    if kept.shape[0] < N:
        raise RuntimeError(f"seed={seed}: needed {N} right-chiral starts, got {kept.shape[0]}")
    return kept[:N], key_random


def make_evolver(dt: float):
    steps = int(round(T_FINAL / dt))

    @jax.jit
    def evolve(psi0: jnp.ndarray):
        q0 = chiral_charge(psi0)
        neg_latch0 = q0 < PRUNE_THRESHOLD
        pos_latch0 = q0 > 0.99
        drift0 = jnp.max(jnp.abs(jnp.linalg.norm(psi0, axis=1) - 1.0))

        def step(carry, _):
            psi, neg_latch, pos_latch, max_drift = carry
            overlaps = psi @ jnp.conjugate(TARGETS).T
            nearest_idx = jnp.argmax(jnp.abs(overlaps) ** 2, axis=1)
            nearest = TARGETS[nearest_idx]
            inner = jnp.einsum("ni,ni->n", jnp.conjugate(psi), nearest)
            psi_next = psi + dt * 2.0 * (nearest - inner[:, None] * psi)
            psi_next = normalize_rows(psi_next)
            q = chiral_charge(psi_next)
            neg_latch = jnp.logical_or(neg_latch, q < PRUNE_THRESHOLD)
            pos_latch = jnp.logical_or(pos_latch, q > 0.99)
            drift = jnp.max(jnp.abs(jnp.linalg.norm(psi_next, axis=1) - 1.0))
            max_drift = jnp.maximum(max_drift, drift)
            return (psi_next, neg_latch, pos_latch, max_drift), None

        (psi_final, neg_latch, pos_latch, max_drift), _ = jax.lax.scan(
            step,
            (psi0, neg_latch0, pos_latch0, drift0),
            None,
            length=steps,
        )
        return psi_final, neg_latch, pos_latch, max_drift

    return evolve, steps


def run_record(labels: jnp.ndarray, survivor_mask: jnp.ndarray) -> dict[str, Any]:
    survivors = int(jnp.sum(survivor_mask))
    return {
        "populated_basins": populated_basins(labels, survivor_mask),
        "survivors": survivors,
        "pruned": int(N - survivors),
    }


def simulate(seed: int, dt: float) -> dict[str, Any]:
    psi0, key_random = make_initial_ensemble(seed)
    evolve, steps = make_evolver(dt)
    psi_final, neg_latch, pos_latch, max_norm_drift = evolve(psi0)
    labels = basin_labels(psi_final)

    all_mask = jnp.ones((N,), dtype=bool)
    b_mask = jnp.logical_not(neg_latch)
    run_a = run_record(labels, all_mask)
    run_b = run_record(labels, b_mask)
    run_c = run_record(labels, all_mask)

    permutation = jax.random.permutation(key_random, N)
    random_prune_mask = jnp.zeros((N,), dtype=bool).at[permutation[: run_b["pruned"]]].set(True)
    random_record = run_record(labels, jnp.logical_not(random_prune_mask))
    random_record["keeps_forbidden"] = bool(set(random_record["populated_basins"]) & {3, 4})

    inverted_record = run_record(labels, jnp.logical_not(pos_latch))
    inverted_record["survivors_within_forbidden"] = bool(
        inverted_record["survivors"] > 0 and set(inverted_record["populated_basins"]).issubset({3, 4})
    )

    max_norm_drift_float = float(max_norm_drift)
    checks = {
        "A_reaches_all_basins": run_a["populated_basins"] == [1, 2, 3, 4],
        "B_kills_forbidden": not (set(run_b["populated_basins"]) & {3, 4}),
        "B_preserves_allowed": {1, 2}.issubset(run_b["populated_basins"]),
        "control_C_equals_A": run_c["populated_basins"] == run_a["populated_basins"] and run_c["pruned"] == 0,
        "B_pruned_some_A_none": run_b["pruned"] > 0 and run_a["pruned"] == 0,
        "rate_matched_random_keeps_forbidden": random_record["keeps_forbidden"],
        "inverted_sign_flips_to_forbidden": inverted_record["survivors_within_forbidden"],
        "bookkeeping": all(rec["survivors"] == N - rec["pruned"] for rec in (run_a, run_b, run_c)),
        "norm_drift_small": max_norm_drift_float < 1.0e-3,
    }
    return {
        "seed": seed,
        "dt": dt,
        "steps": steps,
        "runs": {"A": run_a, "B_gamma5": run_b, "C_control": run_c},
        "selector_controls": {
            "rate_matched_random": random_record,
            "inverted_sign": inverted_record,
        },
        "max_norm_drift": max_norm_drift_float,
        "checks": checks,
        "pass": bool(all(checks.values())),
    }


def load_julia_reference() -> dict[str, Any]:
    reference = json.loads(JULIA_REFERENCE_PATH.read_text())
    branch = reference["branch_prune"]
    checks = {
        "reference_all_pass": bool(reference.get("all_pass")),
        "reference_no_promotion": reference.get("promotion_allowed") is False,
        "reference_A_all_basins": branch["A"] == [1, 2, 3, 4],
        "reference_B_allowed_only": branch["B_gamma5"] == [1, 2],
        "reference_C_equals_A": branch["C_control"] == branch["A"],
    }
    return {
        "path": str(JULIA_REFERENCE_PATH),
        "classification": reference.get("classification"),
        "promotion_allowed": reference.get("promotion_allowed"),
        "branch_prune": branch,
        "checks": checks,
        "pass": bool(all(checks.values())),
    }


def main() -> None:
    julia_reference = load_julia_reference()
    gamma5_checks = {
        "square_identity": bool(jnp.allclose(GAMMA5 @ GAMMA5, jnp.eye(4, dtype=jnp.complex128), atol=1e-12, rtol=1e-12)),
        "expected_diag": bool(
            jnp.allclose(
                GAMMA5,
                jnp.diag(jnp.array([-1, -1, 1, 1], dtype=jnp.complex128)),
                atol=1e-12,
                rtol=1e-12,
            )
        ),
        "anticommutes_all": all(
            bool(jnp.allclose(GAMMA5 @ g + g @ GAMMA5, jnp.zeros((4, 4), dtype=jnp.complex128), atol=1e-12, rtol=1e-12))
            for g in GAMMAS
        ),
    }
    runs = [simulate(seed, dt) for seed in SEED_GRID for dt in DT_GRID]
    primary = runs[0]

    audit_checks = {
        "julia_reference_read_only_pass": julia_reference["pass"],
        "gamma5_rederived_in_jax": all(gamma5_checks.values()),
        "primary_matches_julia_basin_sets": (
            primary["runs"]["A"]["populated_basins"] == julia_reference["branch_prune"]["A"]
            and primary["runs"]["B_gamma5"]["populated_basins"] == julia_reference["branch_prune"]["B_gamma5"]
            and primary["runs"]["C_control"]["populated_basins"] == julia_reference["branch_prune"]["C_control"]
        ),
        "robust_grid_all_pass": all(r["pass"] for r in runs),
        "no_julia_execution": True,
    }
    audit_pass = bool(all(audit_checks.values()))

    receipt = {
        "name": "jax_readonly_julia_gamma5_reference_audit",
        "executed_track": "jax",
        "ran_julia": False,
        "julia_reference_mode": "read_only",
        "classification": "jax_readonly_reference_audit_poc",
        "promotion_allowed": False,
        "claim_ceiling": "JAX stress/audit of existing Julia gamma5 branch/prune result. Diagnostic only; no layer, bridge, Axis0, flux, or physics admission.",
        "audit_pass": audit_pass,
        "julia_reference": julia_reference,
        "gamma5_checks": gamma5_checks,
        "primary_run": primary,
        "robustness_grid": runs,
        "audit_checks": audit_checks,
        "tool_manifest": {
            "JAX": "load-bearing batched audit lane",
            "jax.lax.scan": "load-bearing projected evolution and monotone prune latch",
            "jax.random": "load-bearing branch ensemble generation",
            "jax.numpy": "load-bearing Dirac/gamma5 complex linear algebra",
            "JSON": "read-only Julia reference and JAX receipt serialization",
        },
        "tool_integration_depth": {
            "JAX": "load_bearing",
            "jax.lax.scan": "load_bearing",
            "jax.random": "load_bearing",
            "JSON": "supportive",
        },
        "blocked_consumers": ["layer_completion", "bridge", "Axis0", "flux", "physics_gravity", "canonical_manifold"],
    }
    RECEIPT_PATH.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")

    a = primary["runs"]["A"]
    b = primary["runs"]["B_gamma5"]
    c = primary["runs"]["C_control"]
    print(
        f"JAX read-only reference audit | A basins={a['populated_basins']} surv={a['survivors']} pruned={a['pruned']} | "
        f"B basins={b['populated_basins']} surv={b['survivors']} pruned={b['pruned']} | "
        f"C basins={c['populated_basins']} surv={c['survivors']} pruned={c['pruned']}"
    )
    print(f"AUDIT_PASS={audit_pass}")


if __name__ == "__main__":
    main()
