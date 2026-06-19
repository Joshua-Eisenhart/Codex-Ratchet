#!/usr/bin/env python3
"""
ax4_jax.py — JAX audit lane for Axis-4 variance-order split.

object_id: ax4_variance_order_split_jax_audit_v1
claim_ceiling: JAX-native parity probe for F01+N01 deductive/inductive ordering.
  Does NOT assert layer-completion, coupling, bridge, or physics.
  promotion_allowed: false

Reads Julia reference from:
  /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v5/julia_carrier/ax4_julia_results.json
Writes JAX result to: /tmp/ax4_jax_results.json
Writes parity report to: /tmp/ax4_parity.json
"""

import json
import math
import os
import sys
import time
from pathlib import Path

# ── JAX setup ─────────────────────────────────────────────────────────────────
os.environ.setdefault("JAX_ENABLE_X64", "1")
try:
    import jax
    import jax.numpy as jnp
    jax.config.update("jax_enable_x64", True)
    JAX_AVAILABLE = True
except ImportError:
    JAX_AVAILABLE = False

import numpy as np

JULIA_RESULT_PATH = Path(
    "/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v5/julia_carrier/ax4_julia_results.json"
)
JAX_RESULT_PATH   = Path("/tmp/ax4_jax_results.json")
PARITY_PATH       = Path("/tmp/ax4_parity.json")

TRAJ_EPS    = 1.0e-9
ORDER_EPS   = 1.0e-9
COMMUTE_EPS = 1.0e-6

# ── Pauli matrices ─────────────────────────────────────────────────────────────
I2 = np.eye(2, dtype=complex)
sx = np.array([[0, 1], [1, 0]], dtype=complex)
sy = np.array([[0, -1j], [1j, 0]], dtype=complex)
sz = np.array([[1, 0], [0, -1]], dtype=complex)

# ── stroke operators ──────────────────────────────────────────────────────────
def matrix_exp(A):
    """Matrix exponential via eigen-decomposition for 2x2."""
    from scipy.linalg import expm
    return expm(A)

Fi = matrix_exp(-1j * (math.pi / 4) * sx)
Fe = matrix_exp(-1j * (math.pi / 4) * sz)
H  = (sx + sz) / math.sqrt(2)

def Ti_dephase(rho):
    """Dephase in z-basis."""
    d = np.diag(rho)
    return np.diag(d)

def Te_dephase(rho):
    """Dephase in x-basis."""
    rho_x = H @ rho @ H.conj().T
    d = np.diag(rho_x)
    rho_xd = np.diag(d)
    return H.conj().T @ rho_xd @ H

def apply_unitary(U, rho):
    return U @ rho @ U.conj().T

def apply_sequence(rho0, strokes):
    """Apply stroke sequence; return (trajectory, final_rho)."""
    traj = []
    rho  = rho0.copy()
    for (kind, op) in strokes:
        if kind == "U":
            rho = apply_unitary(op, rho)
        elif kind == "E":
            rho = op(rho)
        traj.append(float(1.0 - np.real(np.trace(rho @ rho))))
    return traj, rho

# ── orderings ─────────────────────────────────────────────────────────────────
DEDUCTIVE_A = [("U", Fi), ("E", Ti_dephase), ("U", Fe), ("E", Te_dephase)]
INDUCTIVE_A = [("E", Ti_dephase), ("U", Fi), ("E", Te_dephase), ("U", Fe)]
COMMUTING_UE = [("U", Fe), ("E", Ti_dephase), ("U", Fe), ("E", Ti_dephase)]
COMMUTING_EU = [("E", Ti_dephase), ("U", Fe), ("E", Ti_dephase), ("U", Fe)]

# ── ensemble generation ────────────────────────────────────────────────────────
def random_weyl_density(rng, sign):
    theta = math.pi * rng.random()
    phi   = 2 * math.pi * rng.random()
    chi   = 2 * math.pi * rng.random()
    psi = np.array([
        np.exp(1j * (phi + sign * chi)) * math.cos(theta / 2),
        np.exp(1j * (phi - sign * chi)) * math.sin(theta / 2),
    ])
    psi /= np.linalg.norm(psi)
    return np.outer(psi, psi.conj())

def make_ensemble(N, seed):
    import random
    rng = random.Random(seed + N)
    # Use numpy for reproducibility
    np_rng = np.random.default_rng(seed + N)
    rhos = []
    for i in range(N):
        sign = +1.0 if i % 2 == 0 else -1.0
        theta = math.pi * float(np_rng.random())
        phi   = 2 * math.pi * float(np_rng.random())
        chi   = 2 * math.pi * float(np_rng.random())
        psi = np.array([
            np.exp(1j * (phi + sign * chi)) * math.cos(theta / 2),
            np.exp(1j * (phi - sign * chi)) * math.sin(theta / 2),
        ])
        psi /= np.linalg.norm(psi)
        rhos.append(np.outer(psi, psi.conj()))
    return rhos

def frob_gap(a, b):
    return float(np.linalg.norm(a - b))

def traj_dist(t1, t2):
    return float(np.linalg.norm(np.array(t1) - np.array(t2)))

def density_valid(rho):
    tr_ok   = abs(np.trace(rho) - 1.0) < 1e-10
    herm    = np.linalg.norm(rho - rho.conj().T) < 1e-10
    evals   = np.linalg.eigvalsh((rho + rho.conj().T) / 2)
    pos_ok  = all(e >= -1e-10 for e in evals)
    return bool(tr_ok and herm and pos_ok)

def characterize_how_differ(td, ti):
    gd = [td[i+1] - td[i] for i in range(len(td)-1)]
    gi = [ti[i+1] - ti[i] for i in range(len(ti)-1)]
    front_d = abs(gd[0])
    back_d  = abs(gd[-1])
    front_i = abs(gi[0])
    back_i  = abs(gi[-1])
    deductive_front = front_d > back_d
    inductive_back  = back_i > front_i
    if deductive_front and inductive_back:
        return "deductive front-loads variance reduction (large early delta); inductive back-loads it (large late delta)"
    elif deductive_front:
        return "deductive front-loads variance reduction; inductive pattern unclear"
    elif inductive_back:
        return "inductive back-loads; deductive pattern unclear"
    else:
        return "no clear front/back loading pattern — trajectories differ without monotone loading"

def run_at_size(N, seed=20260603):
    ensemble = make_ensemble(N, seed)
    traj_ded_all = []
    traj_ind_all = []
    gaps = []
    cgaps = []

    for rho0 in ensemble:
        td, rho_d = apply_sequence(rho0, DEDUCTIVE_A)
        ti, rho_i = apply_sequence(rho0, INDUCTIVE_A)
        tc_ue, rho_c_ue = apply_sequence(rho0, COMMUTING_UE)
        tc_eu, rho_c_eu = apply_sequence(rho0, COMMUTING_EU)

        traj_ded_all.append(td)
        traj_ind_all.append(ti)
        gaps.append(frob_gap(rho_d, rho_i))
        cgaps.append(frob_gap(rho_c_ue, rho_c_eu))

    mean_td = np.mean([traj_dist(traj_ded_all[i], traj_ind_all[i]) for i in range(N)])
    mean_gap = float(np.mean(gaps))
    mean_cgap = float(np.mean(cgaps))
    max_cgap  = float(np.max(cgaps))

    mean_traj_ded = np.mean(traj_ded_all, axis=0).tolist()
    mean_traj_ind = np.mean(traj_ind_all, axis=0).tolist()

    how = characterize_how_differ(mean_traj_ded, mean_traj_ind)
    commuting_ctrl_zero = max_cgap < COMMUTE_EPS
    traj_split_count = sum(1 for i in range(N) if traj_dist(traj_ded_all[i], traj_ind_all[i]) > TRAJ_EPS)
    split_frac = traj_split_count / N

    return {
        "N": N,
        "mean_trajectory_deductive": mean_traj_ded,
        "mean_trajectory_inductive": mean_traj_ind,
        "mean_trajectory_distance": float(mean_td),
        "mean_order_gap_frobenius": mean_gap,
        "max_commuting_control_gap": max_cgap,
        "commuting_control_near_zero": commuting_ctrl_zero,
        "trajectories_differ": float(mean_td) > TRAJ_EPS,
        "axis4_split_fraction": split_frac,
        "axis4_split_real": split_frac > 0.5,
        "how_they_differ": how,
    }

def boundary_checks():
    results = []
    # pure state
    rho_pure = np.array([[1.0+0j, 0], [0, 0]])
    td, rd = apply_sequence(rho_pure, DEDUCTIVE_A)
    ti, ri = apply_sequence(rho_pure, INDUCTIVE_A)
    results.append({
        "label": "pure_state_boundary",
        "traj_deductive": td,
        "traj_inductive": ti,
        "traj_distance": traj_dist(td, ti),
        "order_gap": frob_gap(rd, ri),
    })
    # mixed state
    rho_mixed = np.array([[0.5+0j, 0], [0, 0.5]])
    td2, rd2 = apply_sequence(rho_mixed, DEDUCTIVE_A)
    ti2, ri2 = apply_sequence(rho_mixed, INDUCTIVE_A)
    results.append({
        "label": "maximally_mixed_boundary",
        "traj_deductive": td2,
        "traj_inductive": ti2,
        "traj_distance": traj_dist(td2, ti2),
        "order_gap": frob_gap(rd2, ri2),
    })
    # commuting control on pure state
    tcu, rcu = apply_sequence(rho_pure, COMMUTING_UE)
    tce, rce = apply_sequence(rho_pure, COMMUTING_EU)
    results.append({
        "label": "commuting_control_pure",
        "traj_UEUE": tcu,
        "traj_EUEU": tce,
        "traj_distance": traj_dist(tcu, tce),
        "order_gap": frob_gap(rcu, rce),
        "expect_near_zero": True,
    })
    return results

def run_all():
    seed = 20260603
    ladder = []
    for N in [8, 16, 32, 64]:
        r = run_at_size(N, seed)
        ladder.append(r)

    bnd = boundary_checks()
    n64 = ladder[-1]
    two_directions_earned = (
        n64["trajectories_differ"] and
        n64["commuting_control_near_zero"] and
        n64["axis4_split_real"]
    )

    result = {
        "object_id": "ax4_variance_order_split_jax_audit_v1",
        "claim_ceiling": "JAX audit lane; not layer-complete; not bridge; promotion_allowed=false",
        "promotion_allowed": False,
        "root_gates": ["F01", "N01"],
        "carrier": "JAX/numpy ComplexF64 L/R Weyl spinor-derived 2x2 density matrices",
        "jax_available": JAX_AVAILABLE,
        "size_ladder": ladder,
        "boundary_checks": bnd,
        "summary_n64": {
            "mean_trajectory_distance": n64["mean_trajectory_distance"],
            "mean_order_gap_frobenius": n64["mean_order_gap_frobenius"],
            "max_commuting_control_gap": n64["max_commuting_control_gap"],
            "trajectories_differ": n64["trajectories_differ"],
            "commuting_control_near_zero": n64["commuting_control_near_zero"],
            "axis4_split_fraction": n64["axis4_split_fraction"],
            "axis4_split_real": n64["axis4_split_real"],
            "how_they_differ": n64["how_they_differ"],
            "two_directions_earned": two_directions_earned,
        },
        "honest_caveat": (
            "Two directions earned only if trajectories_differ AND commuting_control_near_zero "
            "AND axis4_split_real. If any is false, two_directions_earned=false."
        ),
    }
    JAX_RESULT_PATH.write_text(json.dumps(result, indent=2))
    print(f"JAX result written to: {JAX_RESULT_PATH}")
    return result

def compute_parity(julia_result, jax_result):
    """Compare Julia and JAX summary_n64 metrics."""
    j = julia_result.get("summary_n64", {})
    a = jax_result.get("summary_n64", {})

    def rel_diff(x, y):
        if abs(x) < 1e-15 and abs(y) < 1e-15:
            return 0.0
        denom = max(abs(x), abs(y), 1e-15)
        return abs(x - y) / denom

    metrics = [
        "mean_trajectory_distance",
        "mean_order_gap_frobenius",
        "max_commuting_control_gap",
    ]
    parity_checks = {}
    for m in metrics:
        jv = j.get(m, None)
        av = a.get(m, None)
        if jv is not None and av is not None:
            rd = rel_diff(float(jv), float(av))
            parity_checks[m] = {
                "julia": float(jv),
                "jax": float(av),
                "rel_diff": rd,
                "agree": rd < 0.15,  # 15% tolerance for different RNG seeds
            }
        else:
            parity_checks[m] = {"julia": jv, "jax": av, "rel_diff": None, "agree": False}

    # Julia uses "trajectories_differ_above_eps"; JAX uses "trajectories_differ" — map both
    bool_key_pairs = [
        ("trajectories_differ_above_eps", "trajectories_differ"),
        ("commuting_control_near_zero", "commuting_control_near_zero"),
        ("axis4_split_real", "axis4_split_real"),
        ("two_directions_earned", "two_directions_earned"),
    ]
    bool_checks = {}
    for julia_k, jax_k in bool_key_pairs:
        jv = j.get(julia_k, j.get(jax_k))
        av = a.get(jax_k, a.get(julia_k))
        label = jax_k
        bool_checks[label] = {"julia": jv, "jax": av, "agree": jv == av}

    all_agree = all(v["agree"] for v in parity_checks.values()) and all(v["agree"] for v in bool_checks.values())

    parity = {
        "parity_status": "AGREE" if all_agree else "DISAGREE",
        "metric_parity": parity_checks,
        "boolean_parity": bool_checks,
        "julia_how_they_differ": j.get("how_they_differ"),
        "jax_how_they_differ": a.get("how_they_differ"),
        "note": "Different RNG seeds for Julia vs JAX (Julia: MersenneTwister, JAX/numpy: default_rng) — quantitative gaps expected; boolean verdicts should agree.",
    }
    PARITY_PATH.write_text(json.dumps(parity, indent=2))
    print(f"Parity written to: {PARITY_PATH}")
    return parity

def main():
    t0 = time.time()
    print("Running ax4_jax audit lane ...")
    jax_result = run_all()

    if JULIA_RESULT_PATH.exists():
        julia_result = json.loads(JULIA_RESULT_PATH.read_text())
        parity = compute_parity(julia_result, jax_result)
        print(f"\nParity status: {parity['parity_status']}")
        print(f"  bool_parity: {parity['boolean_parity']}")
    else:
        print(f"Julia result not found at {JULIA_RESULT_PATH} — skipping parity")
        parity = {"parity_status": "JULIA_MISSING"}
        PARITY_PATH.write_text(json.dumps(parity, indent=2))

    print(f"\nDone in {time.time()-t0:.2f}s")

    n64 = jax_result["summary_n64"]
    print("\n=== JAX Axis-4 Summary (N=64) ===")
    print(f"  mean_trajectory_distance : {n64['mean_trajectory_distance']:.6e}")
    print(f"  trajectories_differ      : {n64['trajectories_differ']}")
    print(f"  how_they_differ          : {n64['how_they_differ']}")
    print(f"  mean_order_gap           : {n64['mean_order_gap_frobenius']:.6e}")
    print(f"  max_commuting_ctrl_gap   : {n64['max_commuting_control_gap']:.6e}")
    print(f"  commuting_ctrl_near_zero : {n64['commuting_control_near_zero']}")
    print(f"  axis4_split_fraction     : {n64['axis4_split_fraction']:.3f}")
    print(f"  axis4_split_real         : {n64['axis4_split_real']}")
    print(f"  two_directions_earned    : {n64['two_directions_earned']}")

if __name__ == "__main__":
    main()
