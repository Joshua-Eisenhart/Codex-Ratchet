#!/usr/bin/env python3
"""JAX audit of a Julia Dirac-spinor chirality branch/prune result."""

import json
from pathlib import Path

import jax

jax.config.update("jax_enable_x64", True)

import jax.numpy as jnp


N = 600
SEED = 42
DT = 1.0e-3
T_FINAL = 12.0
STEPS = int(round(T_FINAL / DT))
RECEIPT_PATH = Path("jax_dirac_gamma5_audit_results.json")


def normalize_rows(z):
    return z / jnp.linalg.norm(z, axis=1, keepdims=True)


def normalize_vec(z):
    return z / jnp.linalg.norm(z)


def build_gamma_matrices():
    ctype = jnp.complex128
    zero = jnp.zeros((2, 2), dtype=ctype)
    i2 = jnp.eye(2, dtype=ctype)
    sx = jnp.array([[0, 1], [1, 0]], dtype=ctype)
    sy = jnp.array([[0, -1j], [1j, 0]], dtype=ctype)
    sz = jnp.array([[1, 0], [0, -1]], dtype=ctype)

    g0 = jnp.block([[zero, i2], [i2, zero]])
    g1 = jnp.block([[zero, sx], [-sx, zero]])
    g2 = jnp.block([[zero, sy], [-sy, zero]])
    g3 = jnp.block([[zero, sz], [-sz, zero]])
    gamma5 = 1j * g0 @ g1 @ g2 @ g3
    return (g0, g1, g2, g3), gamma5


GAMMAS, GAMMA5 = build_gamma_matrices()
IDENT4 = jnp.eye(4, dtype=jnp.complex128)
EXPECTED_GAMMA5 = jnp.diag(jnp.array([-1, -1, 1, 1], dtype=jnp.complex128))

gamma5_square_identity = bool(jnp.allclose(GAMMA5 @ GAMMA5, IDENT4, atol=1e-12, rtol=1e-12))
gamma5_expected_diag = bool(jnp.allclose(GAMMA5, EXPECTED_GAMMA5, atol=1e-12, rtol=1e-12))
gamma5_anticommutes = [
    bool(jnp.allclose(GAMMA5 @ g + g @ GAMMA5, jnp.zeros((4, 4), dtype=jnp.complex128), atol=1e-12, rtol=1e-12))
    for g in GAMMAS
]
gamma5_anticommutes_all = all(gamma5_anticommutes)

assert gamma5_square_identity
assert gamma5_expected_diag
assert gamma5_anticommutes_all

TARGETS = jnp.stack(
    [
        normalize_vec(jnp.array([0, 0, 1, 0.3], dtype=jnp.complex128)),
        normalize_vec(jnp.array([0, 0, 0.3, 1], dtype=jnp.complex128)),
        normalize_vec(jnp.array([1, 0.3, 0, 0], dtype=jnp.complex128)),
        normalize_vec(jnp.array([0.3, 1, 0, 0], dtype=jnp.complex128)),
    ]
)


def chiral_charge(psi):
    return jnp.real(jnp.einsum("...i,ij,...j->...", jnp.conjugate(psi), GAMMA5, psi))


def basin_labels(psi):
    overlaps = psi @ jnp.conjugate(TARGETS).T
    return jnp.argmax(jnp.abs(overlaps) ** 2, axis=1) + 1


def populated_basins(labels, mask):
    selected = labels[mask]
    return [int(x) for x in sorted(set(map(int, jax.device_get(selected))))]


def make_initial_ensemble():
    key = jax.random.PRNGKey(SEED)
    key_re, key_im, key_random = jax.random.split(key, 3)
    candidates = 8192
    real = jax.random.normal(key_re, (candidates, 4), dtype=jnp.float64)
    imag = jax.random.normal(key_im, (candidates, 4), dtype=jnp.float64)
    psi = normalize_rows(real + 1j * imag)
    kept = psi[chiral_charge(psi) > 0.1]
    if kept.shape[0] < N:
        raise RuntimeError(f"needed {N} right-chiral starts, got {kept.shape[0]}")
    return kept[:N], key_random


@jax.jit
def evolve(psi0):
    q0 = chiral_charge(psi0)
    neg_latch0 = q0 < -0.01
    pos_latch0 = q0 > 0.99
    drift0 = jnp.max(jnp.abs(jnp.linalg.norm(psi0, axis=1) - 1.0))

    def step(carry, _):
        psi, neg_latch, pos_latch, max_drift = carry
        overlaps = psi @ jnp.conjugate(TARGETS).T
        nearest_idx = jnp.argmax(jnp.abs(overlaps) ** 2, axis=1)
        nearest = TARGETS[nearest_idx]
        inner = jnp.einsum("ni,ni->n", jnp.conjugate(psi), nearest)
        psi_next = psi + DT * 2.0 * (nearest - inner[:, None] * psi)
        psi_next = normalize_rows(psi_next)
        q = chiral_charge(psi_next)
        neg_latch = jnp.logical_or(neg_latch, q < -0.01)
        pos_latch = jnp.logical_or(pos_latch, q > 0.99)
        drift = jnp.max(jnp.abs(jnp.linalg.norm(psi_next, axis=1) - 1.0))
        max_drift = jnp.maximum(max_drift, drift)
        return (psi_next, neg_latch, pos_latch, max_drift), None

    (psi_final, neg_latch, pos_latch, max_drift), _ = jax.lax.scan(
        step,
        (psi0, neg_latch0, pos_latch0, drift0),
        None,
        length=STEPS,
    )
    return psi_final, neg_latch, pos_latch, max_drift


def run_record(labels, survivor_mask):
    survivors = int(jnp.sum(survivor_mask))
    return {
        "populated_basins": populated_basins(labels, survivor_mask),
        "survivors": survivors,
        "pruned": int(N - survivors),
    }


def main():
    psi0, key_random = make_initial_ensemble()
    psi_final, neg_latch, pos_latch, max_norm_drift = evolve(psi0)
    labels = basin_labels(psi_final)

    all_mask = jnp.ones((N,), dtype=bool)
    b_survivor_mask = jnp.logical_not(neg_latch)
    c_survivor_mask = all_mask

    run_a = run_record(labels, all_mask)
    run_b = run_record(labels, b_survivor_mask)
    run_c = run_record(labels, c_survivor_mask)

    k_pruned_b = run_b["pruned"]
    permutation = jax.random.permutation(key_random, N)
    random_prune_mask = jnp.zeros((N,), dtype=bool).at[permutation[:k_pruned_b]].set(True)
    random_survivor_mask = jnp.logical_not(random_prune_mask)
    rate_matched_random = run_record(labels, random_survivor_mask)
    rate_matched_random["keeps_forbidden"] = bool(set(rate_matched_random["populated_basins"]) & {3, 4})

    inverted_survivor_mask = jnp.logical_not(pos_latch)
    inverted_sign = run_record(labels, inverted_survivor_mask)
    inverted_sign["survivors_within_forbidden"] = bool(
        inverted_sign["survivors"] > 0 and set(inverted_sign["populated_basins"]).issubset({3, 4})
    )

    max_norm_drift_float = float(max_norm_drift)
    audit_pass = bool(
        run_a["populated_basins"] == [1, 2, 3, 4]
        and not (set(run_b["populated_basins"]) & {3, 4})
        and {1, 2}.issubset(set(run_b["populated_basins"]))
        and run_c["populated_basins"] == run_a["populated_basins"]
        and run_c["pruned"] == 0
        and run_b["pruned"] > 0
        and run_a["pruned"] == 0
        and rate_matched_random["keeps_forbidden"]
        and inverted_sign["survivors_within_forbidden"]
        and max_norm_drift_float < 1.0e-3
    )

    receipt = {
        "audit_pass": audit_pass,
        "n": N,
        "seed": SEED,
        "dt": DT,
        "steps": STEPS,
        "gamma5_verification": {
            "square_identity": gamma5_square_identity,
            "expected_diag": gamma5_expected_diag,
            "anticommutes": gamma5_anticommutes,
            "anticommutes_all": gamma5_anticommutes_all,
        },
        "runs": {
            "A": run_a,
            "B": run_b,
            "C": run_c,
        },
        "selector_controls": {
            "rate_matched_random": rate_matched_random,
            "inverted_sign": inverted_sign,
        },
        "max_norm_drift": max_norm_drift_float,
    }
    RECEIPT_PATH.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")

    print(
        f"A basins={run_a['populated_basins']} surv={run_a['survivors']} pruned={run_a['pruned']} | "
        f"B basins={run_b['populated_basins']} surv={run_b['survivors']} pruned={run_b['pruned']} | "
        f"C basins={run_c['populated_basins']} surv={run_c['survivors']} pruned={run_c['pruned']}"
    )
    print(f"AUDIT_PASS={audit_pass}")


if __name__ == "__main__":
    main()
