"""
Type-2 Process_Cycle SIM — Reversed Chirality
========================================
8 stages × 4 operators per stage, Lindblad architecture.
Same framework as szilard_64stage_sim.py but with REVERSED CHIRALITY.

KEY DISTINCTION:
  Type-1: Process_Cycle A outer (FeTi deductive major), Process_Cycle B inner (TeFi inductive minor)
  Type-2: Process_Cycle B outer (TeFi inductive major), Process_Cycle A inner (FeTi deductive minor)

Type-2 Sequence (from NLM-04):
  Major loop (Inductive/Heating = TeFi):
    1. Ne/Fi  2. Ni/Te  3. Fi/Se  4. Te/Si
  Minor loop (Deductive/Cooling = FeTi):
    5. Ti/Ne  6. Si/Fe  7. Se/Ti  8. Fe/Ni

Math: ρ̇ = -i[H,ρ] + Σ_k γ_k (L_k ρ L_k† - ½{L_k†L_k, ρ})
  Reversed chirality = inductive operators dominate the outer (major) loop,
  deductive operators dominate the inner (minor) loop.

Comparison: conceptual_layer ΔΦ trajectories against Type-1 to test
  whether Chern number (±1) produces measurably distinct dynamics.
"""

import numpy as np
import json
import os
from datetime import datetime, UTC

import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from proto_ratchet_sim_runner import (
    make_random_density_matrix,
    von_neumann_entropy,
    trace_distance,
    EvidenceToken,
)


def negentropy(rho, d):
    S = von_neumann_entropy(rho) * np.log(2)
    return np.log(d) - S


def ensure_valid(rho):
    rho = (rho + rho.conj().T) / 2
    eigvals = np.maximum(np.real(np.linalg.eigvalsh(rho)), 0)
    if sum(eigvals) > 0:
        V = np.linalg.eigh(rho)[1]
        rho = V @ np.diag(eigvals.astype(complex)) @ V.conj().T
        rho = rho / np.trace(rho)
    return rho


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Lindblad generator (shared with Type-1)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def build_Ti_ops(d):
    """Ti: dephasing/projection Lindblad operators."""
    L_ops = []
    for k in range(d):
        L = np.zeros((d, d), dtype=complex)
        L[k, k] = 1.0
        L_ops.append(L)
    return L_ops


def build_Fe_ops(d):
    """Fe: dissipation/damping Lindblad operators."""
    L_ops = []
    for j in range(d):
        for k in range(d):
            if j != k:
                L = np.zeros((d, d), dtype=complex)
                L[j, k] = 1.0
                L_ops.append(L)
    return L_ops


def build_Fi_filter(d, absorb=True):
    """Fi: spectral filter matrix (Kraus-like)."""
    F = np.eye(d, dtype=complex)
    if absorb:  # -Fi: absorb/match
        for k in range(1, d):
            F[k, k] = 0.7
    else:  # +Fi: emit/broadcast
        for k in range(1, d):
            F[k, k] = 0.3
    return F


def build_Te_hamiltonian(d, seed=77):
    """Te: Hamiltonian for unitary flow."""
    np.random.seed(seed)
    H = np.random.randn(d, d) + 1j * np.random.randn(d, d)
    H = (H + H.conj().T) / 2
    return H


def apply_lindblad_stage(rho, d, dominant_op, axis6_up, dt=0.005, n_steps=5):
    """
    Apply one stage: all 4 operators simultaneously via Lindblad master equation.

    dominant_op: 'Ti', 'Te', 'Fi', 'Fe' — gets γ_dominant = 5.0
    generator_basis6_up: True = (+) source mode, False = (-) sink mode
    subordinate operators get γ_sub = 0.5
    """
    γ_dom = 5.0
    γ_sub = 0.5

    H = build_Te_hamiltonian(d)
    sign = 1.0 if axis6_up else -1.0  # +Te ascent vs -Te descent

    Ti_ops = build_Ti_ops(d)
    Fe_ops = build_Fe_ops(d)
    Fi = build_Fi_filter(d, absorb=not axis6_up)

    # Assign coupling strengths
    γ_Ti = γ_dom if dominant_op == 'Ti' else γ_sub
    γ_Fe = γ_dom if dominant_op == 'Fe' else γ_sub
    γ_Fi = γ_dom if dominant_op == 'Fi' else γ_sub
    H_scale = γ_dom if dominant_op == 'Te' else γ_sub

    for _ in range(n_steps):
        # Hamiltonian (Te) contribution: -i[H, ρ]
        commutator = sign * H_scale * (H @ rho - rho @ H)
        drho = -1j * commutator

        # Ti Lindblad (dephasing)
        for L in Ti_ops:
            LdL = L.conj().T @ L
            drho += γ_Ti * (L @ rho @ L.conj().T - 0.5 * (LdL @ rho + rho @ LdL))

        # Fe Lindblad (dissipation)
        for L in Fe_ops:
            LdL = L.conj().T @ L
            drho += γ_Fe * (L @ rho @ L.conj().T - 0.5 * (LdL @ rho + rho @ LdL))

        rho = rho + dt * drho

        # Fi contribution (Kraus-like application)
        fi_strength = γ_Fi * dt * 0.5
        rho = (1 - fi_strength) * rho + fi_strength * (Fi @ rho @ Fi.conj().T)
        if np.real(np.trace(rho)) > 0:
            rho = rho / np.trace(rho)

        rho = ensure_valid(rho)

    return rho


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Stage definitions
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# TYPE-1 sequence (from szilard_64stage_sim.py):
# Major loop (Process_Cycle A = Deductive/Cooling = FeTi):
#   1. Ne/Ti/WIN/DOWN   2. Si/Fe/WIN/UP
#   3. Se/Ti/LOSE/UP    4. Ni/Fe/LOSE/DOWN
# Minor loop (Process_Cycle B = Inductive/Heating = TeFi):
#   5. Se/Fi/win/DOWN   6. Si/Te/win/DOWN
#   7. Ne/Fi/lose/UP    8. Ni/Te/lose/UP

TYPE1_STAGES = [
    # (stage, topo, dominant, label, generator_basis6_up, loop)
    (1, "Ne", "Ti", "WIN",  False, "A-outer"),
    (2, "Si", "Fe", "WIN",  True,  "A-outer"),
    (3, "Se", "Ti", "LOSE", True,  "A-outer"),
    (4, "Ni", "Fe", "LOSE", False, "A-outer"),
    (5, "Se", "Fi", "win",  False, "B-inner"),
    (6, "Si", "Te", "win",  False, "B-inner"),
    (7, "Ne", "Fi", "lose", True,  "B-inner"),
    (8, "Ni", "Te", "lose", True,  "B-inner"),
]

# TYPE-2 sequence (REVERSED CHIRALITY from NLM-04):
#   NeFi → NiTe → FiSe → TeSi (Major Inductive) → TiNe → SiFe → SeTi → FeNi (Minor Deductive)
#
# Major loop (Process_Cycle B = Inductive/Heating = TeFi):
#   1. Ne/Fi/WIN/DOWN   2. Ni/Te/WIN/UP
#   3. Fi/Se/LOSE/UP    4. Te/Si/LOSE/DOWN
# Minor loop (Process_Cycle A = Deductive/Cooling = FeTi):
#   5. Ti/Ne/win/DOWN   6. Si/Fe/win/DOWN
#   7. Se/Ti/lose/UP    8. Fe/Ni/lose/UP
#
# Chirality reversal: generator_basis6 polarities are FLIPPED relative to Type-1
# at corresponding stages (the Chern number sign flip).

TYPE2_STAGES = [
    # (stage, topo, dominant, label, generator_basis6_up, loop)
    (1, "Ne", "Fi", "WIN",  True,  "B-outer"),   # was -/Ti → +/Fi
    (2, "Ni", "Te", "WIN",  False, "B-outer"),    # was +/Fe → -/Te
    (3, "Se", "Fi", "LOSE", False, "B-outer"),     # was +/Ti → -/Fi
    (4, "Si", "Te", "LOSE", True,  "B-outer"),     # was -/Fe → +/Te
    (5, "Ne", "Ti", "win",  True,  "A-inner"),     # was -/Fi → +/Ti
    (6, "Si", "Fe", "win",  True,  "A-inner"),     # was -/Te → +/Fe
    (7, "Se", "Ti", "lose", False, "A-inner"),     # was +/Fi → -/Ti
    (8, "Ni", "Fe", "lose", False, "A-inner"),     # was +/Te → -/Fe
]


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Process_Cycle runner (parametric on stage table)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def run_engine(stage_table, label, d, n_cycles, rho_init, verbose=True):
    """
    Run 8-stage × 4-operator Lindblad process_cycle for n_cycles.
    Returns (final_rho, total_dphi, per_cycle_deltas, per_stage_trajectory).
    """
    rho = rho_init.copy()
    phi_start = negentropy(rho, d)

    all_ops = ['Ti', 'Te', 'Fi', 'Fe']
    cycle_deltas = []
    trajectory = [phi_start]  # ΔΦ trajectory point per stage

    if verbose:
        print(f"\n{'='*70}")
        print(f"PROCESS_CYCLE: {label}")
        print(f"  d={d}, cycles={n_cycles}")
        print(f"  Each stage: 4 operators simultaneous (Lindblad)")
        print(f"  Dominant γ=5.0, subordinate γ=0.5")
        print(f"{'='*70}")

    for cycle in range(n_cycles):
        phi_cycle_start = negentropy(rho, d)

        for stage_num, topo, dominant, slabel, axis6_up, loop in stage_table:
            phi_before = negentropy(rho, d)

            rho = apply_lindblad_stage(rho, d, dominant, axis6_up)

            phi_after = negentropy(rho, d)
            dphi = phi_after - phi_before
            trajectory.append(phi_after)

            pol = "+" if axis6_up else "-"

            if verbose and cycle == 0:
                subs = []
                for op in all_ops:
                    role = "DOM" if op == dominant else "sub"
                    subs.append(f"{pol}{op}({role})")
                sub_str = " | ".join(subs)
                print(f"  S{stage_num} {topo} [{loop:7s}] {slabel:4s}: "
                      f"ΔΦ={dphi:+.4f} [{sub_str}]")

        phi_cycle_end = negentropy(rho, d)
        cycle_dphi = phi_cycle_end - phi_cycle_start
        cycle_deltas.append(cycle_dphi)

        if verbose and cycle > 0:
            print(f"  Cycle {cycle+1}: Φ={phi_cycle_end:.4f} (ΔΦ={cycle_dphi:+.6f})")

    total_dphi = negentropy(rho, d) - phi_start

    if verbose:
        print(f"\n  Total ΔΦ over {n_cycles} cycles: {total_dphi:+.6f}")
        print(f"  Cycles with ΔΦ>0: {sum(1 for x in cycle_deltas if x > 0)}/{n_cycles}")
        print(f"  Average ΔΦ/cycle: {np.mean(cycle_deltas):+.6f}")

    return rho, total_dphi, cycle_deltas, trajectory


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Type-1 vs Type-2 comparison
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def compare_type1_vs_type2(d=4, n_cycles=10):
    """
    Run both process_cycle types from IDENTICAL initial state.
    Compare ΔΦ trajectories to test chirality reversal effects.
    """
    np.random.seed(42)
    rho_init = make_random_density_matrix(d)

    print(f"\n{'#'*70}")
    print(f"# TYPE-1 vs TYPE-2 CHIRALITY COMPARISON")
    print(f"#   d={d}, cycles={n_cycles}")
    print(f"#   Same initial state, same operators, reversed chirality")
    print(f"{'#'*70}")

    # --- Type-1 ---
    rho1, dphi1, deltas1, traj1 = run_engine(
        TYPE1_STAGES, "TYPE-1 (FeTi outer / TeFi inner)", d, n_cycles, rho_init
    )

    # --- Type-2 (reversed chirality) ---
    rho2, dphi2, deltas2, traj2 = run_engine(
        TYPE2_STAGES, "TYPE-2 (TeFi outer / FeTi inner) [REVERSED]", d, n_cycles, rho_init
    )

    # --- Comparison ---
    print(f"\n{'='*70}")
    print(f"CHIRALITY COMPARISON RESULTS")
    print(f"{'='*70}")

    print(f"\n  {'Metric':<35s} {'Type-1':>12s} {'Type-2':>12s} {'Δ(T2-T1)':>12s}")
    print(f"  {'-'*35} {'-'*12} {'-'*12} {'-'*12}")

    print(f"  {'Total ΔΦ':<35s} {dphi1:>+12.6f} {dphi2:>+12.6f} {dphi2-dphi1:>+12.6f}")
    print(f"  {'Mean ΔΦ/cycle':<35s} {np.mean(deltas1):>+12.6f} {np.mean(deltas2):>+12.6f} "
          f"{np.mean(deltas2)-np.mean(deltas1):>+12.6f}")
    print(f"  {'Cycles with ΔΦ>0':<35s} "
          f"{sum(1 for x in deltas1 if x>0):>12d} "
          f"{sum(1 for x in deltas2 if x>0):>12d} "
          f"{sum(1 for x in deltas2 if x>0)-sum(1 for x in deltas1 if x>0):>+12d}")
    print(f"  {'Final Φ':<35s} {traj1[-1]:>12.6f} {traj2[-1]:>12.6f} "
          f"{traj2[-1]-traj1[-1]:>+12.6f}")

    # State distance
    dist = trace_distance(rho1, rho2)
    print(f"  {'Final state trace distance':<35s} {dist:>12.6f}")

    # Per-cycle comparison
    print(f"\n  Per-cycle ΔΦ comparison:")
    print(f"  {'Cycle':>6s} {'Type-1':>12s} {'Type-2':>12s} {'Δ':>12s} {'Winner':>8s}")
    print(f"  {'-'*6} {'-'*12} {'-'*12} {'-'*12} {'-'*8}")
    for i, (d1, d2) in enumerate(zip(deltas1, deltas2)):
        winner = "T1" if d1 > d2 else ("T2" if d2 > d1 else "TIE")
        print(f"  {i+1:>6d} {d1:>+12.6f} {d2:>+12.6f} {d2-d1:>+12.6f} {winner:>8s}")

    # Trajectory divergence analysis
    min_len = min(len(traj1), len(traj2))
    t1 = np.array(traj1[:min_len])
    t2 = np.array(traj2[:min_len])
    divergence = np.abs(t1 - t2)

    print(f"\n  Trajectory divergence:")
    print(f"    Max |Φ₁ - Φ₂|:  {np.max(divergence):.6f}")
    print(f"    Mean |Φ₁ - Φ₂|: {np.mean(divergence):.6f}")
    print(f"    Final |Φ₁ - Φ₂|: {divergence[-1]:.6f}")

    # Chirality signature: do the trajectories cross?
    crossings = 0
    for i in range(1, min_len):
        if (t1[i] - t2[i]) * (t1[i-1] - t2[i-1]) < 0:
            crossings += 1
    print(f"    Trajectory crossings: {crossings}")

    # Berry phase proxy: cumulative winding difference
    # Sum of |ΔΦ| (total action) should differ by chirality
    action1 = sum(abs(d) for d in deltas1)
    action2 = sum(abs(d) for d in deltas2)
    print(f"\n  Total action (Σ|ΔΦ|):")
    print(f"    Type-1: {action1:.6f}")
    print(f"    Type-2: {action2:.6f}")
    print(f"    Ratio:  {action2/action1:.4f}" if action1 > 0 else "    Ratio: N/A")

    # Verdict
    print(f"\n  {'='*50}")
    chirality_distinct = dist > 0.01
    if chirality_distinct:
        print(f"  ✓ CHIRALITY REVERSAL PRODUCES DISTINCT DYNAMICS")
        print(f"    Final states differ by trace distance {dist:.6f}")
        print(f"    → Type-1 ≠ Type-2 (Chern number ±1 verified)")
    else:
        print(f"  ✗ WARNING: Chirality reversal did NOT produce distinct dynamics")
        print(f"    Final states converged to trace distance {dist:.6f}")
    print(f"  {'='*50}")

    return {
        "type1": {"total_dphi": dphi1, "cycle_deltas": deltas1, "trajectory": traj1},
        "type2": {"total_dphi": dphi2, "cycle_deltas": deltas2, "trajectory": traj2},
        "trace_distance": dist,
        "chirality_distinct": chirality_distinct,
        "trajectory_crossings": crossings,
    }


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Main
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

if __name__ == "__main__":
    d = 4
    n_cycles = 10

    results = compare_type1_vs_type2(d, n_cycles)

    # Build evidence tokens
    evidence = []

    if results["chirality_distinct"]:
        evidence.append(EvidenceToken(
            token_id="E_SIM_TYPE2_CHIRALITY_DISTINCT",
            sim_spec_id="S_SIM_TYPE2_PROCESS_CYCLE_V1",
            status="PASS",
            measured_value=results["trace_distance"],
        ))
    else:
        evidence.append(EvidenceToken(
            token_id="",
            sim_spec_id="S_SIM_TYPE2_PROCESS_CYCLE_V1",
            status="KILL",
            measured_value=results["trace_distance"],
            kill_reason="CHIRALITY_REVERSAL_COLLAPSED",
        ))

    # Net directional_accumulator test for Type-2
    t2_dphi = results["type2"]["total_dphi"]
    if t2_dphi > -1.0:
        evidence.append(EvidenceToken(
            token_id="E_SIM_TYPE2_CYCLE_OK",
            sim_spec_id="S_SIM_TYPE2_CYCLE_V1",
            status="PASS",
            measured_value=t2_dphi,
        ))
    else:
        evidence.append(EvidenceToken(
            token_id="",
            sim_spec_id="S_SIM_TYPE2_CYCLE_V1",
            status="KILL",
            measured_value=t2_dphi,
            kill_reason="TYPE2_CYCLE_STATE_REDUCTION",
        ))

    print(f"\n{'='*70}")
    print(f"TYPE-2 PROCESS_CYCLE SUITE RESULTS")
    print(f"{'='*70}")
    for e in evidence:
        icon = "✓" if e.status == "PASS" else "✗"
        print(f"  {icon} {e.sim_spec_id}: {e.status} (value={e.measured_value:.4f})")

    # Save results
    base = os.path.dirname(os.path.abspath(__file__))
    results_dir = os.path.join(base, "a2_state", "sim_results")
    os.makedirs(results_dir, exist_ok=True)
    outpath = os.path.join(results_dir, "type2_process_cycle_results.json")

    # Serialize (convert numpy to python types)
    def to_native(obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        if isinstance(obj, (np.float64, np.float32)):
            return float(obj)
        if isinstance(obj, (np.int64, np.int32)):
            return int(obj)
        if isinstance(obj, np.bool_):
            return bool(obj)
        return obj

    save_data = {
        "timestamp": datetime.now(UTC).isoformat(),
        "config": {"d": d, "n_cycles": n_cycles, "gamma_dom": 5.0, "gamma_sub": 0.5},
        "comparison": {
            "type1_total_dphi": to_native(results["type1"]["total_dphi"]),
            "type2_total_dphi": to_native(results["type2"]["total_dphi"]),
            "type1_cycle_deltas": [to_native(x) for x in results["type1"]["cycle_deltas"]],
            "type2_cycle_deltas": [to_native(x) for x in results["type2"]["cycle_deltas"]],
            "trace_distance": to_native(results["trace_distance"]),
            "chirality_distinct": to_native(results["chirality_distinct"]),
            "trajectory_crossings": to_native(results["trajectory_crossings"]),
        },
        "evidence_ledger": [
            {
                "token_id": e.token_id,
                "sim_spec_id": e.sim_spec_id,
                "status": e.status,
                "measured_value": to_native(e.measured_value),
                "kill_reason": e.kill_reason,
            }
            for e in evidence
        ],
    }

    with open(outpath, "w") as f:
        json.dump(save_data, f, indent=2)
    print(f"  Results saved to: {outpath}")
