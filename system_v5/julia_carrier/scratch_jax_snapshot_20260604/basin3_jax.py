#!/usr/bin/env python3
"""
basin3_jax.py — JAX audit lane for basin3 Hopfield quaternion network.

Reimplements the same four-model Hopfield with jax.numpy (jnp) as the compute
engine. Plain numpy is allowed only for non-compute I/O (json dump). All
random draws use jax.random with explicit key splitting; all linear algebra
and finite-map computation uses jnp.

Same Hamilton product quaternion convention as Julia carrier.
Writes /tmp/basin3_jax_results.json.

CLAIM CEILING: audit_lane — does not assert layer-completion or manifold admission.
"""

import jax
jax.config.update("jax_enable_x64", True)

import json
import math
import time
from pathlib import Path

import jax.numpy as jnp
import numpy as np           # I/O only: json.dump needs plain Python types

JULIA_RESULT_PATH = Path("/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v5/julia_carrier/basin3_julia_results.json")
JAX_RESULT_PATH   = Path("/tmp/basin3_jax_results.json")

SEED          = 20260603
N_NEURONS     = 12
M_VALUES      = [2, 3, 4, 8]
N_SEEDS       = 80
WARM_TRIALS   = 8
MAX_ITER      = 200
TOL           = 1e-9
CORRUPT_FRAC  = 0.30

print("=" * 78)
print("basin3_jax.py — real-JAX compute lane for basin3_hopfield_chiral_quaternion_network")
print(f"x64_enabled = {jax.config.x64_enabled}")
print("=" * 78)

# =============================================================================
# N01 CHECK via JAX (Hamilton product is noncommutative)
# =============================================================================

def jax_qmul(q, p):
    """Hamilton product via JAX. q, p shape (4,)."""
    w1, x1, y1, z1 = q[0], q[1], q[2], q[3]
    w2, x2, y2, z2 = p[0], p[1], p[2], p[3]
    return jnp.array([
        w1*w2 - x1*x2 - y1*y2 - z1*z2,
        w1*x2 + x1*w2 + y1*z2 - z1*y2,
        w1*y2 - x1*z2 + y1*w2 + z1*x2,
        w1*z2 + x1*y2 - y1*x2 + z1*w2,
    ])

qi = jnp.array([0., 1., 0., 0.])
qj = jnp.array([0., 0., 1., 0.])
ij = jax_qmul(qi, qj)
ji = jax_qmul(qj, qi)
comm_norm = float(jnp.sqrt(jnp.sum((ij - ji)**2)))
assert comm_norm > 1.0, f"N01 check FAILED: Hamilton product commutes (norm={comm_norm})"
print(f"N01 check PASSED: ||i*j - j*i||_quat = {comm_norm:.6f} > 1.0  (JAX verified)")

# =============================================================================
# JAX QUATERNION ALGEBRA (all compute via jnp)
# All pattern/state arrays shape (N, 4); W shape (N, N, 4)
# =============================================================================

def jnp_qmul_W_state(W, state):
    """
    W: (N, N, 4), state: (N, 4).
    Returns h of shape (N, 4) where h[i] = sum_j Hamilton(W[i,j], state[j]).
    Vectorized entirely in jnp.
    """
    # Broadcast: W shape (N,N,4), state shape (N,4) -> state reshaped (1,N,4)
    w1 = W[:, :, 0]; x1 = W[:, :, 1]; y1 = W[:, :, 2]; z1 = W[:, :, 3]
    w2 = state[:, 0]; x2 = state[:, 1]; y2 = state[:, 2]; z2 = state[:, 3]
    # Broadcast state over i dimension
    rw = w1 * w2[jnp.newaxis, :] - x1 * x2[jnp.newaxis, :] - y1 * y2[jnp.newaxis, :] - z1 * z2[jnp.newaxis, :]
    rx = w1 * x2[jnp.newaxis, :] + x1 * w2[jnp.newaxis, :] + y1 * z2[jnp.newaxis, :] - z1 * y2[jnp.newaxis, :]
    ry = w1 * y2[jnp.newaxis, :] - x1 * z2[jnp.newaxis, :] + y1 * w2[jnp.newaxis, :] + z1 * x2[jnp.newaxis, :]
    rz = w1 * z2[jnp.newaxis, :] + x1 * y2[jnp.newaxis, :] - y1 * x2[jnp.newaxis, :] + z1 * w2[jnp.newaxis, :]
    # Sum over j axis
    hw = rw.sum(axis=1); hx = rx.sum(axis=1); hy = ry.sum(axis=1); hz = rz.sum(axis=1)
    return jnp.stack([hw, hx, hy, hz], axis=-1)  # (N, 4)


def jnp_qconj(Q):
    """Quaternion conjugate. Q shape (..., 4)."""
    return Q.at[..., 1:].mul(-1)


def jnp_qnorm(Q):
    """Norm. Q shape (..., 4). Returns (...,)."""
    return jnp.sqrt((Q ** 2).sum(axis=-1))


def jnp_qnormalize(Q):
    """Normalize. Q shape (..., 4). Returns (..., 4)."""
    n = jnp_qnorm(Q)[..., jnp.newaxis]
    ones_q = jnp.zeros_like(Q).at[..., 0].set(1.0)
    return jnp.where(n > 1e-300, Q / n, ones_q)


def jnp_quat_geodesic_vec(Q1, Q2):
    """Geodesic distance row-wise on S^3 (sign-folded). Q1, Q2 shape (N, 4). Returns (N,)."""
    d = jnp.abs((Q1 * Q2).sum(axis=-1))
    d = jnp.clip(d, 0.0, 1.0)
    return jnp.arccos(d)


def rand_unit_quat_jax(key, shape):
    """Random unit quaternions using JAX. Returns shape (*shape, 4)."""
    Q = jax.random.normal(key, shape=(*shape, 4))
    n = jnp.sqrt((Q ** 2).sum(axis=-1, keepdims=True))
    return Q / jnp.where(n > 1e-300, n, 1.0)


# =============================================================================
# JAX WEIGHT ASSEMBLY
# =============================================================================

def _build_W_one_pass_jax(pats_L, pats_R, N, sign_R):
    """
    Build chiral Hebbian weight matrix entirely in JAX.
    pats_L, pats_R: lists of M arrays each shape (N, 4) (JAX arrays).
    sign_R: +1.0 nonchiral, -1.0 chiral.
    Returns W (N, N, 4) as JAX array.
    """
    W = jnp.zeros((N, N, 4))
    for mu in range(len(pats_L)):
        qL = pats_L[mu]   # (N, 4)
        qR = pats_R[mu]
        cqLj = jnp_qconj(qL)   # (N, 4)
        cqRj = jnp_qconj(qR)

        # For each i: W[i,j] += qmul(qL[i], cqLj[j]) + sign_R * qmul(qR[i], cqRj[j])
        # Vectorize over i via broadcasting: qL shape (N,4), cqLj shape (N,4)
        # Result W_contrib shape (N, N, 4) where [i,j] = qmul(qL[i], cqLj[j])

        # LEFT factors (i dimension): shape (N,1,4)
        qL_i = qL[:, jnp.newaxis, :]   # (N, 1, 4)
        qR_i = qR[:, jnp.newaxis, :]

        # RIGHT factors (j dimension): shape (1,N,4)
        cqLj_j = cqLj[jnp.newaxis, :, :]  # (1, N, 4)
        cqRj_j = cqRj[jnp.newaxis, :, :]

        # Extract components
        w1L = qL_i[:, :, 0]; x1L = qL_i[:, :, 1]; y1L = qL_i[:, :, 2]; z1L = qL_i[:, :, 3]
        w2L = cqLj_j[:, :, 0]; x2L = cqLj_j[:, :, 1]; y2L = cqLj_j[:, :, 2]; z2L = cqLj_j[:, :, 3]

        cL = jnp.stack([
            w1L*w2L - x1L*x2L - y1L*y2L - z1L*z2L,
            w1L*x2L + x1L*w2L + y1L*z2L - z1L*y2L,
            w1L*y2L - x1L*z2L + y1L*w2L + z1L*x2L,
            w1L*z2L + x1L*y2L - y1L*x2L + z1L*w2L,
        ], axis=-1)  # (N, N, 4)

        w1R = qR_i[:, :, 0]; x1R = qR_i[:, :, 1]; y1R = qR_i[:, :, 2]; z1R = qR_i[:, :, 3]
        w2R = cqRj_j[:, :, 0]; x2R = cqRj_j[:, :, 1]; y2R = cqRj_j[:, :, 2]; z2R = cqRj_j[:, :, 3]

        cR = jnp.stack([
            w1R*w2R - x1R*x2R - y1R*y2R - z1R*z2R,
            w1R*x2R + x1R*w2R + y1R*z2R - z1R*y2R,
            w1R*y2R - x1R*z2R + y1R*w2R + z1R*x2R,
            w1R*z2R + x1R*y2R - y1R*x2R + z1R*w2R,
        ], axis=-1)  # (N, N, 4)

        W = W + cL + sign_R * cR

    # Zero diagonal
    diag_mask = jnp.eye(N, dtype=bool)
    W = W.at[diag_mask].set(0.0)
    return W


def realvec_hebbian_jax(patterns, N):
    """Quaternion Hebbian on patterns (N,4) each, using JAX."""
    W = jnp.zeros((N, N, 4))
    for mu in range(len(patterns)):
        xi = patterns[mu]   # (N, 4)
        cxj = jnp_qconj(xi)   # (N, 4)

        xi_i = xi[:, jnp.newaxis, :]       # (N, 1, 4)
        cxj_j = cxj[jnp.newaxis, :, :]    # (1, N, 4)

        w1 = xi_i[:, :, 0]; x1 = xi_i[:, :, 1]; y1 = xi_i[:, :, 2]; z1 = xi_i[:, :, 3]
        w2 = cxj_j[:, :, 0]; x2 = cxj_j[:, :, 1]; y2 = cxj_j[:, :, 2]; z2 = cxj_j[:, :, 3]

        contrib = jnp.stack([
            w1*w2 - x1*x2 - y1*y2 - z1*z2,
            w1*x2 + x1*w2 + y1*z2 - z1*y2,
            w1*y2 - x1*z2 + y1*w2 + z1*x2,
            w1*z2 + x1*y2 - y1*x2 + z1*w2,
        ], axis=-1)  # (N, N, 4)
        W = W + contrib

    diag_mask = jnp.eye(N, dtype=bool)
    W = W.at[diag_mask].set(0.0)
    return W


def classical_hebbian_jax(patterns, N):
    """Scalar Hebbian. patterns: list of (N,4) with only w component."""
    W = jnp.zeros((N, N))
    for mu in range(len(patterns)):
        s = patterns[mu][:, 0]   # (N,) scalar — jnp array
        W = W + jnp.outer(s, s)
    diag_mask = jnp.eye(N, dtype=bool)
    W = W.at[diag_mask].set(0.0)
    return W


# =============================================================================
# JAX RECALL DYNAMICS
# =============================================================================

def chiral_recall_step_jax(state_L, state_R, W, use_chirality):
    """One recall step. state_L, state_R: (N,4). W: (N,N,4)."""
    hL = jnp_qmul_W_state(W, state_L)
    if use_chirality:
        hR = jnp_qmul_W_state(-W, state_R)
    else:
        hR = jnp_qmul_W_state(W, state_R)
    return jnp_qnormalize(hL), jnp_qnormalize(hR)


def run_chiral_recall_jax(state_L0, state_R0, W, use_chirality,
                           max_iter=MAX_ITER, tol=TOL):
    sL = state_L0; sR = state_R0
    for _ in range(max_iter):
        pL, pR = sL, sR
        sL, sR = chiral_recall_step_jax(sL, sR, W, use_chirality)
        dL = jnp_quat_geodesic_vec(pL, sL).max()
        dR = jnp_quat_geodesic_vec(pR, sR).max()
        if float((dL + dR) / 2) < tol:
            break
    return sL, sR


def realvec_recall_step_jax(state, W):
    h = jnp_qmul_W_state(W, state)   # (N, 4)
    # Project to real-vector: zero y, z components
    h = h.at[:, 2].set(0.0).at[:, 3].set(0.0)
    return jnp_qnormalize(h)


def run_realvec_recall_jax(state0, W, max_iter=MAX_ITER, tol=TOL):
    state = state0
    for _ in range(max_iter):
        prev = state
        state = realvec_recall_step_jax(state, W)
        d = jnp_quat_geodesic_vec(prev, state).max()
        if float(d) < tol:
            break
    return state


def run_classical_recall_jax(state0, W, max_iter=MAX_ITER, tol=TOL):
    """W: (N,N) scalar jnp array. state: (N,4) with only w component."""
    state = state0
    for _ in range(max_iter):
        prev_w = state[:, 0]
        h = W @ state[:, 0]   # (N,) — jnp matmul
        s = jnp.where(h >= 0.0, 1.0, -1.0)
        state = state.at[:, 0].set(s)
        if float(jnp.abs(prev_w - s).max()) < tol:
            break
    return state


# =============================================================================
# OVERLAP AND BASIN LABEL (JAX)
# =============================================================================

def chiral_overlap_jax(sL, sR, pL, pR):
    dL = jnp.cos(jnp_quat_geodesic_vec(sL, pL)).mean()
    dR = jnp.cos(jnp_quat_geodesic_vec(sR, pR)).mean()
    return float((dL + dR) / 2)


def quat_overlap_jax(state, pattern):
    return float(jnp.cos(jnp_quat_geodesic_vec(state, pattern)).mean())


def chiral_basin_label_jax(sL, sR, pats_L, pats_R):
    ovs = [chiral_overlap_jax(sL, sR, pats_L[m], pats_R[m]) for m in range(len(pats_L))]
    best = int(jnp.argmax(jnp.array(ovs)))
    return best, ovs[best]


def quat_basin_label_jax(state, patterns):
    ovs = [quat_overlap_jax(state, patterns[m]) for m in range(len(patterns))]
    best = int(jnp.argmax(jnp.array(ovs)))
    return best, ovs[best]


# =============================================================================
# CORRUPTION (JAX random)
# =============================================================================

def corrupt_chiral_jax(pL, pR, frac, key, N):
    k = max(1, round(frac * N))
    key, subkey = jax.random.split(key)
    idx = jax.random.choice(subkey, N, shape=(k,), replace=False)
    key, subkeyL, subkeyR = jax.random.split(key, 3)
    noise_L = rand_unit_quat_jax(subkeyL, (k,))
    noise_R = rand_unit_quat_jax(subkeyR, (k,))
    sL = pL.at[idx].set(noise_L)
    sR = pR.at[idx].set(noise_R)
    return sL, sR, key


def corrupt_quat_jax(pattern, frac, key, N, model):
    k = max(1, round(frac * N))
    key, subkey = jax.random.split(key)
    idx = jax.random.choice(subkey, N, shape=(k,), replace=False)
    state = pattern
    if model == 'realvec':
        key, subkey2 = jax.random.split(key)
        noise = rand_unit_quat_jax(subkey2, (k,))
        noise = noise.at[:, 2].set(0.0).at[:, 3].set(0.0)
        n = jnp.sqrt((noise ** 2).sum(axis=-1, keepdims=True))
        noise = noise / jnp.where(n > 1e-12, n, 1.0)
        state = state.at[idx].set(noise)
    elif model == 'classical':
        key, subkey2 = jax.random.split(key)
        raw = jax.random.normal(subkey2, shape=(k,))
        s = jnp.where(raw >= 0.0, 1.0, -1.0)
        state = state.at[idx, 0].set(s)
    else:
        key, subkey2 = jax.random.split(key)
        noise = rand_unit_quat_jax(subkey2, (k,))
        state = state.at[idx].set(noise)
    return state, key


# =============================================================================
# CAPACITY TRIALS (JAX compute throughout)
# =============================================================================

def trial_chiral_jax(M, N, base_key, use_chirality, trials=WARM_TRIALS, corrupt_frac=CORRUPT_FRAC):
    key = base_key
    # Generate patterns
    pats_L = []
    pats_R = []
    for _ in range(M):
        key, k1, k2 = jax.random.split(key, 3)
        pats_L.append(rand_unit_quat_jax(k1, (N,)))
        pats_R.append(rand_unit_quat_jax(k2, (N,)))

    sign_R = -1.0 if use_chirality else 1.0
    W = _build_W_one_pass_jax(pats_L, pats_R, N, sign_R)

    basin_hits = 0; total = 0; overlaps = []
    basins_seen = set()
    for mu in range(M):
        for _ in range(trials):
            cL, cR, key = corrupt_chiral_jax(pats_L[mu], pats_R[mu], corrupt_frac, key, N)
            recL, recR = run_chiral_recall_jax(cL, cR, W, use_chirality)
            lbl, ov = chiral_basin_label_jax(recL, recR, pats_L, pats_R)
            overlaps.append(float(ov))
            basins_seen.add(lbl)
            if lbl == mu:
                basin_hits += 1
            total += 1
    return basin_hits / total, float(sum(overlaps) / len(overlaps)), len(basins_seen)


def trial_quat_jax(M, N, base_key, model, trials=WARM_TRIALS, corrupt_frac=CORRUPT_FRAC):
    key = base_key

    if model == 'realvec':
        patterns = []
        for _ in range(M):
            key, subkey = jax.random.split(key)
            q = rand_unit_quat_jax(subkey, (N,))
            q = q.at[:, 2].set(0.0).at[:, 3].set(0.0)
            n = jnp.sqrt((q ** 2).sum(axis=-1, keepdims=True))
            q = q / jnp.where(n > 1e-12, n, 1.0)
            patterns.append(q)
        W = realvec_hebbian_jax(patterns, N)

    elif model == 'classical':
        patterns = []
        for _ in range(M):
            key, subkey = jax.random.split(key)
            raw = jax.random.normal(subkey, shape=(N,))
            s = jnp.where(raw >= 0.0, 1.0, -1.0)
            p = jnp.zeros((N, 4))
            p = p.at[:, 0].set(s)
            patterns.append(p)
        W = classical_hebbian_jax(patterns, N)

    else:
        patterns = []
        for _ in range(M):
            key, subkey = jax.random.split(key)
            patterns.append(rand_unit_quat_jax(subkey, (N,)))
        W = realvec_hebbian_jax(patterns, N)

    basin_hits = 0; total = 0; overlaps = []
    basins_seen = set()
    for mu in range(M):
        for _ in range(trials):
            probe, key = corrupt_quat_jax(patterns[mu], corrupt_frac, key, N, model)
            if model == 'classical':
                rec = run_classical_recall_jax(probe, W)
            elif model == 'realvec':
                rec = run_realvec_recall_jax(probe, realvec_hebbian_jax(patterns, N))
            else:
                rec = run_realvec_recall_jax(probe, W)
            lbl, ov = quat_basin_label_jax(rec, patterns)
            overlaps.append(float(ov))
            basins_seen.add(lbl)
            if lbl == mu:
                basin_hits += 1
            total += 1
    return basin_hits / total, float(sum(overlaps) / len(overlaps)), len(basins_seen)


# =============================================================================
# MAIN EXPERIMENT
# =============================================================================

print(f"\n--- JAX four-model Hopfield experiment ---")
print(f"N={N_NEURONS}, M in {M_VALUES}, N_SEEDS={N_SEEDS}, WARM_TRIALS={WARM_TRIALS}\n")

# JAX PRNG root key — derived from SEED
root_key = jax.random.PRNGKey(SEED)

per_M_results = []
best_recall = {"chiral": 0., "nonchiral": 0., "realvec": 0., "classical": 0.}
any_genuine_multistable = False
any_candidate_distinct = False

t0 = time.time()

for M in M_VALUES:
    print(f"  M = {M} patterns:")
    n_reps = max(1, N_SEEDS // (WARM_TRIALS * M))

    accs = {"chiral": [], "nonchiral": [], "realvec": [], "classical": []}
    ovs  = {"chiral": [], "nonchiral": [], "realvec": [], "classical": []}
    nbs  = {"chiral": [], "nonchiral": [], "realvec": [], "classical": []}

    for rep in range(n_reps):
        # Derive a key for this (M, rep) cell — deterministic from SEED
        cell_key = jax.random.fold_in(root_key, M * 10000 + rep)
        k_ch, k_nc, k_rv, k_cl = jax.random.split(cell_key, 4)

        ra, mo, nb = trial_chiral_jax(M, N_NEURONS, k_ch, use_chirality=True)
        accs["chiral"].append(ra); ovs["chiral"].append(mo); nbs["chiral"].append(nb)

        ra, mo, nb = trial_chiral_jax(M, N_NEURONS, k_nc, use_chirality=False)
        accs["nonchiral"].append(ra); ovs["nonchiral"].append(mo); nbs["nonchiral"].append(nb)

        ra, mo, nb = trial_quat_jax(M, N_NEURONS, k_rv, model='realvec')
        accs["realvec"].append(ra); ovs["realvec"].append(mo); nbs["realvec"].append(nb)

        ra, mo, nb = trial_quat_jax(M, N_NEURONS, k_cl, model='classical')
        accs["classical"].append(ra); ovs["classical"].append(mo); nbs["classical"].append(nb)

    mean_acc = {k: float(sum(v) / len(v)) for k, v in accs.items()}
    mean_ov  = {k: float(sum(v) / len(v)) for k, v in ovs.items()}
    mean_nb  = {k: float(sum(v) / len(v)) for k, v in nbs.items()}
    chance   = 1.0 / M

    for k in ["chiral", "nonchiral", "realvec", "classical"]:
        print(f"    {k:<12}: recall={mean_acc[k]:.3f}, overlap={mean_ov[k]:.3f}, basins={mean_nb[k]:.1f}")
    print(f"    chance=1/M={chance:.3f}")

    for k in best_recall:
        best_recall[k] = max(best_recall[k], mean_acc[k])

    multistable_M = mean_acc["chiral"] > 2 * chance and mean_nb["chiral"] > 1
    any_genuine_multistable = any_genuine_multistable or multistable_M

    neg_max_matched = max(mean_acc["nonchiral"], mean_acc["realvec"])
    cand_distinct_M = mean_acc["chiral"] > neg_max_matched
    any_candidate_distinct = any_candidate_distinct or cand_distinct_M

    per_M_results.append({
        "M": M,
        "chance": float(chance),
        "chiral":    {"recall_accuracy": mean_acc["chiral"],    "mean_recall_overlap": mean_ov["chiral"],    "n_basins_found": mean_nb["chiral"]},
        "nonchiral": {"recall_accuracy": mean_acc["nonchiral"], "mean_recall_overlap": mean_ov["nonchiral"], "n_basins_found": mean_nb["nonchiral"]},
        "realvec":   {"recall_accuracy": mean_acc["realvec"],   "mean_recall_overlap": mean_ov["realvec"],   "n_basins_found": mean_nb["realvec"]},
        "classical": {"recall_accuracy": mean_acc["classical"],  "mean_recall_overlap": mean_ov["classical"],  "n_basins_found": mean_nb["classical"]},
        "candidate_distinct_at_matched_dim": bool(cand_distinct_M),
        "genuine_multistable_at_M": bool(multistable_M),
    })

elapsed = time.time() - t0
print(f"\nElapsed: {elapsed:.1f}s")

print(f"\n--- JAX aggregate verdict ---")
print(f"  genuine_multistability: {any_genuine_multistable}")
print(f"  candidate_distinct_matched: {any_candidate_distinct}")
print(f"  best recalls: {best_recall}")

# =============================================================================
# PARITY CHECK vs Julia reference
# =============================================================================

parity_holds = False
parity_note = "Julia reference not found"
parity_details = {}

if JULIA_RESULT_PATH.exists():
    with open(JULIA_RESULT_PATH) as f:
        julia_ref = json.load(f)

    jref_chiral  = julia_ref.get("per_model_summary", {}).get("chiral", None)
    jref_recall  = julia_ref.get("recall_accuracy", None)
    jref_ms      = julia_ref.get("genuine_multistability", None)
    jref_cand    = julia_ref.get("candidate_distinct_matched", None)

    jax_chiral   = best_recall["chiral"]
    jax_ms       = any_genuine_multistable
    jax_cand     = any_candidate_distinct

    # Parity: statistical (not bit-identical) — same qualitative outcomes expected
    # RNG differs (JAX PRNGKey vs numpy default_rng) so numerical values will differ;
    # parity holds if: multistability flag matches AND candidate_distinct matches
    # AND chiral recall is in a plausible range relative to Julia (within 0.30 abs).
    flag_match = (jax_ms == jref_ms) and (jax_cand == jref_cand)
    if jref_chiral is not None:
        recall_delta = abs(jax_chiral - jref_chiral)
    else:
        recall_delta = None

    parity_holds = flag_match and (recall_delta is None or recall_delta < 0.30)

    parity_details = {
        "julia_chiral_recall": jref_chiral,
        "jax_chiral_recall": jax_chiral,
        "recall_delta": recall_delta,
        "julia_genuine_multistable": jref_ms,
        "jax_genuine_multistable": jax_ms,
        "julia_candidate_distinct": jref_cand,
        "jax_candidate_distinct": jax_cand,
        "flag_match": flag_match,
        "parity_criterion": "flag_match AND |recall_delta| < 0.30 (statistical, not bit-identical; RNG differs)",
    }
    parity_note = "HOLDS (qualitative parity)" if parity_holds else "BREAKS — disagreement is a real signal"
    print(f"\n--- Parity vs Julia ---")
    print(f"  Julia chiral recall: {jref_chiral}")
    print(f"  JAX   chiral recall: {jax_chiral:.4f}  delta={recall_delta:.4f}")
    print(f"  Flags: multistable={jax_ms}=={jref_ms}, cand_distinct={jax_cand}=={jref_cand}")
    print(f"  Parity: {parity_note}")
else:
    print(f"\nWARN: Julia reference not found at {JULIA_RESULT_PATH}")

# =============================================================================
# np_compute_remaining check (honest count of np.* in compute paths)
# The only np.* calls remaining are in the I/O section (json.load/dump) — not compute.
# =============================================================================
NP_COMPUTE_REMAINING = 0  # all compute is jnp; np used only in json I/O above

# =============================================================================
# WRITE JAX RESULTS
# =============================================================================

result = {
    "object_id": "basin3_hopfield_chiral_quaternion_network_jax",
    "engine": "real_jax",
    "version": "4.0",
    "x64_enabled": bool(jax.config.x64_enabled),
    "classification": "audit_lane",
    "promotion_allowed": False,
    "seed": SEED,
    "n_neurons": N_NEURONS,
    "m_values": M_VALUES,
    "per_M_results": per_M_results,
    "genuine_multistability": bool(any_genuine_multistable),
    "candidate_distinct_matched": bool(any_candidate_distinct),
    "recall_accuracy": float(best_recall["chiral"]),
    "per_model_summary": {k: float(v) for k, v in best_recall.items()},
    "n01_check": {
        "passed": True,
        "commutator_norm": float(comm_norm),
        "note": "verified via JAX: Hamilton product i*j != j*i",
    },
    "parity_vs_julia": {
        "holds": bool(parity_holds),
        "note": parity_note,
        **parity_details,
    },
    "np_compute_remaining": NP_COMPUTE_REMAINING,
    "blocked_consumers": [
        "layer-completion / manifold admission",
        "coupling / coexistence / nesting promotion",
        "bridge / rho_AB / Xi / Phi0 / Axis0",
        "flux / FEP / physics",
    ],
}

with open(JAX_RESULT_PATH, "w") as f:
    json.dump(result, f, indent=2)
print(f"\nJAX result written to: {JAX_RESULT_PATH}")
print("=" * 78)
print("basin3_jax.py DONE")
print("=" * 78)
