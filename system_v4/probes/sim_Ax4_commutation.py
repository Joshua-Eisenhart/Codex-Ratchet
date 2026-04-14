#!/usr/bin/env python3
"""
sim_Ax4_commutation.py — Axis 4 Loop Ordering Distinguishability
=================================================================
Local probe for Ax4: verifies that the CPTP semigroup is non-commutative
under the UEUE vs EUEU composition orderings, using the locked
Ax5 operators on 8 canonical terrain states.

Axis 4 definition (AXIS_3_4_5_6_QIT_MATH.md):
  - DEDUCTIVE (fiber/inner, b₃=-1): Φ_UEUE = U∘E∘U∘E (FeTi kernel; b₄=-1)
  - INDUCTIVE (base/outer, b₃=+1): Φ_EUEU = E∘U∘E∘U (TeFi kernel; b₄=+1)
  where U = Ne/Si class (NU/unitary branch) and E = Se/Ni class (U/dissipative branch)

Evidence: UEUE and EUEU produce distinguishable quantum trajectories (trace
distance > threshold) and different entropy profiles for typical input states.

Results saved: a2_state/sim_results/Ax4_commutation_results.json
"""

import numpy as np
import json
from datetime import datetime, timezone
from geometric_operators import (
classification = "classical_baseline"  # auto-backfill
    apply_Ti, apply_Fe, apply_Te, apply_Fi,
    trace_distance_2x2, _ensure_valid_density
)

# ─── Locked operators as in sim_Ax5_TF_kernel.py ──────────────────────────

def U_operator(rho, theta=0.4):
    """U-branch: Ne/Si class — unitary (F-kernel rotation). Uses Fi (U_x rotation).
    U_x(θ) mixes populations |0⟩↔|1⟩, producing genuine non-commutativity
    with Ti (σ_z dephasing). Fe (U_z) commutes with Ti — wrong choice for Ax4.
    """
    return apply_Fi(rho, polarity_up=True, strength=1.0, theta=theta)

def E_operator(rho, q=0.7):
    """E-branch: Se/Ni class — dissipative (T-kernel dephasing). Uses Ti (σ_z dephasing)."""
    return apply_Ti(rho, polarity_up=True, strength=q)

def apply_UEUE(rho, theta=0.4, q=0.7):
    """Φ_UEUE = U∘E∘U∘E (Deductive / fiber / b₃=-1)"""
    rho = E_operator(rho, q=q)
    rho = U_operator(rho, theta=theta)
    rho = E_operator(rho, q=q)
    rho = U_operator(rho, theta=theta)
    return rho

def apply_EUEU(rho, theta=0.4, q=0.7):
    """Φ_EUEU = E∘U∘E∘U (Inductive / base / b₃=+1)"""
    rho = U_operator(rho, theta=theta)
    rho = E_operator(rho, q=q)
    rho = U_operator(rho, theta=theta)
    rho = E_operator(rho, q=q)
    return rho

def von_neumann_entropy(rho):
    evals = np.linalg.eigvalsh(rho)
    evals = np.maximum(evals, 0)
    s = 0.0
    for ev in evals:
        if ev > 1e-15:
            s -= ev * np.log(ev)
    return float(s)

# ─── Canonical test states ──────────────────────────────────────────────────

def bloch_state(theta, phi):
    """Pure state on Bloch sphere: cos(θ/2)|0⟩ + e^{iφ}sin(θ/2)|1⟩"""
    psi = np.array([np.cos(theta/2), np.exp(1j*phi)*np.sin(theta/2)], dtype=complex)
    return np.outer(psi, psi.conj())

def maximally_mixed():
    return np.eye(2, dtype=complex) / 2

# 8 test states covering Bloch sphere
TEST_STATES = {
    "north_pole":     bloch_state(0.0, 0.0),
    "south_pole":     bloch_state(np.pi, 0.0),
    "equator_x":      bloch_state(np.pi/2, 0.0),
    "equator_y":      bloch_state(np.pi/2, np.pi/2),
    "mixed_half":     0.7*bloch_state(0.2, 0.3) + 0.3*bloch_state(2.1, 1.2),
    "upper_mixed":    bloch_state(np.pi/4, 0.5),
    "lower_mixed":    bloch_state(3*np.pi/4, 1.0),
    "maximally_mixed": maximally_mixed(),
}

# ─── Robustness: test across parameter range ────────────────────────────────

def robustness_check(rho_init, n_trials=100, theta_range=(0.1, 1.5), q_range=(0.3, 0.9)):
    """Check that UEUE ≠ EUEU across parameter space."""
    rng = np.random.default_rng(42)
    pass_count = 0
    for _ in range(n_trials):
        theta = rng.uniform(*theta_range)
        q = rng.uniform(*q_range)
        r_ueue = apply_UEUE(rho_init.copy(), theta=theta, q=q)
        r_eueu = apply_EUEU(rho_init.copy(), theta=theta, q=q)
        d = trace_distance_2x2(r_ueue, r_eueu)
        if d > 1e-6:
            pass_count += 1
    return pass_count / n_trials

# ─── Entropy trajectory ──────────────────────────────────────────────────────

def entropy_trajectory(rho_init, n_steps=4, theta=0.4, q=0.7, mode="UEUE"):
    """Apply operators one at a time and record entropy after each step."""
    ops_ueue = [
        ("E1", lambda r: E_operator(r, q=q)),
        ("U1", lambda r: U_operator(r, theta=theta)),
        ("E2", lambda r: E_operator(r, q=q)),
        ("U2", lambda r: U_operator(r, theta=theta)),
    ]
    ops_eueu = [
        ("U1", lambda r: U_operator(r, theta=theta)),
        ("E1", lambda r: E_operator(r, q=q)),
        ("U2", lambda r: U_operator(r, theta=theta)),
        ("E2", lambda r: E_operator(r, q=q)),
    ]
    ops = ops_ueue if mode == "UEUE" else ops_eueu
    rho = rho_init.copy()
    traj = [von_neumann_entropy(rho)]
    for name, op in ops:
        rho = op(rho)
        traj.append(von_neumann_entropy(rho))
    return traj

# ─── Main ────────────────────────────────────────────────────────────────────

def run():
    results = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "name": "Ax4_commutation",
        "source": "sim_Ax4_commutation.py",
        "axis": "Ax4",
        "claim": "UEUE != EUEU for non-trivial initial states (non-commutative CPTP semigroup)",
        "tests": [],
        "evidence_tokens": [],
    }

    print("=" * 70)
    print("  AX4 COMMUTATION SIM — UEUE vs EUEU LOOP ORDERING")
    print("=" * 70)

    # T1: Trace distance between UEUE and EUEU outputs across test states
    print("\n[T1] Trace distance UEUE vs EUEU across 8 test states...")
    theta, q = 0.4, 0.7
    distances = {}
    for name, rho in TEST_STATES.items():
        rho = _ensure_valid_density(rho.copy())
        r_ueue = apply_UEUE(rho, theta=theta, q=q)
        r_eueu = apply_EUEU(rho, theta=theta, q=q)
        d = trace_distance_2x2(r_ueue, r_eueu)
        distances[name] = float(d)
        print(f"  {name}: D(UEUE, EUEU) = {d:.4f}")

    non_zero = sum(1 for d in distances.values() if d > 1e-4)
    t1_pass = non_zero >= 6
    print(f"  Non-trivial distances (>1e-4): {non_zero}/8 → {'PASS' if t1_pass else 'FAIL'}")
    results["tests"].append({
        "id": "T1",
        "name": "trace_distance_non_zero",
        "distances": distances,
        "non_trivial_count": non_zero,
        "pass": t1_pass
    })

    # T2: Entropy trajectory differs between UEUE and EUEU
    print("\n[T2] Entropy trajectories differ for mixed input state...")
    rho_test = _ensure_valid_density(TEST_STATES["upper_mixed"].copy())
    traj_ueue = entropy_trajectory(rho_test, mode="UEUE")
    traj_eueu = entropy_trajectory(rho_test, mode="EUEU")
    traj_diff = [abs(a - b) for a, b in zip(traj_ueue, traj_eueu)]
    max_traj_diff = max(traj_diff)
    print(f"  UEUE trajectory: {[f'{s:.4f}' for s in traj_ueue]}")
    print(f"  EUEU trajectory: {[f'{s:.4f}' for s in traj_eueu]}")
    print(f"  Max diff at any step: {max_traj_diff:.4f}")
    t2_pass = max_traj_diff > 0.01
    print(f"  → {'PASS' if t2_pass else 'FAIL'}")
    results["tests"].append({
        "id": "T2",
        "name": "entropy_trajectory_diff",
        "traj_ueue": traj_ueue,
        "traj_eueu": traj_eueu,
        "max_diff": float(max_traj_diff),
        "pass": t2_pass
    })

    # T3: Robustness — UEUE ≠ EUEU across parameter space
    # Note: equator_x = |+x⟩ is an eigenstate of U_x (Fi), so U acts as identity
    # on that state and UEUE degenerates to EEEE. Use upper_mixed instead.
    print("\n[T3] Robustness: UEUE ≠ EUEU across (theta, q) parameter space...")
    rho_rob = _ensure_valid_density(TEST_STATES["upper_mixed"].copy())
    rob_rate = robustness_check(rho_rob)
    print(f"  Non-trivial distance rate: {rob_rate*100:.1f}%")
    t3_pass = rob_rate >= 0.95
    print(f"  → {'PASS' if t3_pass else 'FAIL'}")
    results["tests"].append({
        "id": "T3",
        "name": "robustness_across_params",
        "robustness_rate": float(rob_rate),
        "pass": t3_pass
    })

    # T4: Commutator check — verify U∘E ≠ E∘U at operator level
    print("\n[T4] Commutator: U∘E ≠ E∘U at operator level...")
    rho_c = _ensure_valid_density(TEST_STATES["equator_y"].copy())
    r_ue = U_operator(E_operator(rho_c.copy()))
    r_eu = E_operator(U_operator(rho_c.copy()))
    d_comm = trace_distance_2x2(r_ue, r_eu)
    print(f"  D(U∘E, E∘U) = {d_comm:.4f}")
    t4_pass = d_comm > 1e-4
    print(f"  → {'PASS' if t4_pass else 'FAIL'}")
    results["tests"].append({
        "id": "T4",
        "name": "single_commutator",
        "trace_distance": float(d_comm),
        "pass": t4_pass
    })

    # T5: Final entropy differs (UEUE ends more structured vs EUEU)
    print("\n[T5] Final state structure: entropy ordering after full cycle...")
    n_samples = 50
    rng = np.random.default_rng(123)
    ueue_lower = 0
    for _ in range(n_samples):
        theta = rng.uniform(0.2, 1.2)
        q = rng.uniform(0.4, 0.8)
        rho0 = _ensure_valid_density(bloch_state(rng.uniform(0.1, np.pi-0.1), rng.uniform(0, 2*np.pi)))
        s_ueue = von_neumann_entropy(apply_UEUE(rho0, theta=theta, q=q))
        s_eueu = von_neumann_entropy(apply_EUEU(rho0, theta=theta, q=q))
        if s_ueue < s_eueu:
            ueue_lower += 1
    rate = ueue_lower / n_samples
    print(f"  UEUE ends lower entropy than EUEU: {ueue_lower}/{n_samples} ({rate*100:.1f}%)")
    t5_pass = 0.3 < rate < 0.8  # Not systematically same
    print(f"  (ordering varies — not degenerate) → {'PASS' if t5_pass else 'FAIL'}")
    results["tests"].append({
        "id": "T5",
        "name": "final_entropy_non_degenerate",
        "ueue_lower_rate": float(rate),
        "pass": t5_pass
    })

    # Summary
    all_pass = all(t["pass"] for t in results["tests"])
    n_pass = sum(1 for t in results["tests"] if t["pass"])
    print(f"\n{'='*70}")
    print(f"  AX4 VERDICT: {'PASS ✓' if all_pass else f'PARTIAL ({n_pass}/5)'}")
    print(f"{'='*70}")

    # Evidence tokens (SIM_EVIDENCE v1 format)
    if t1_pass:
        results["evidence_tokens"].append({
            "token": "AX4_UEUE_EUEU_DISTINCT",
            "value": "PASS",
            "witness": f"non_trivial_distance_count={non_zero}/8",
        })
    if t2_pass:
        results["evidence_tokens"].append({
            "token": "AX4_ENTROPY_TRAJECTORY_DIFFERS",
            "value": "PASS",
            "witness": f"max_traj_diff={max_traj_diff:.4f}",
        })
    if t3_pass:
        results["evidence_tokens"].append({
            "token": "AX4_LOOP_ORDERING_NONCOMMUTATIVE",
            "value": "PASS",
            "witness": f"robustness_rate={rob_rate:.3f}",
        })
    if t4_pass:
        results["evidence_tokens"].append({
            "token": "AX4_UE_COMMUTATOR_NONZERO",
            "value": "PASS",
            "witness": f"D(UoE, EoU)={d_comm:.4f}",
        })

    results["verdict"] = "PASS" if all_pass else "PARTIAL"
    results["n_pass"] = n_pass
    results["n_total"] = len(results["tests"])

    out_path = "a2_state/sim_results/Ax4_commutation_results.json"
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\n  Results saved: {out_path}")
    print(f"  Evidence tokens emitted: {len(results['evidence_tokens'])}")
    for tok in results["evidence_tokens"]:
        print(f"    {tok['token']}={tok['value']}")

    return results


if __name__ == "__main__":
    run()
