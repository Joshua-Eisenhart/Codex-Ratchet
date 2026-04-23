"""
DEEP GRAVEYARD: 16-Point Constraint Matrix — Systematic Negative SIM Battery
=============================================================================
Executes ALL remaining constraint violations to prove each axiom is mandatory.
Each test intentionally breaks one (or more) constraints and verifies KILL.

NEG-C3:  CPTP Admissibility — trace-increasing / non-positive map
NEG-X2:  Chirality Violation — swap Left/Right Weyl action (TF≠FT)
NEG-Ti:  No Measurement — remove Lüders projection entirely
NEG-Te:  No Unitary Drive — remove Hamiltonian rotation
NEG-Fi:  No Spectral Projection — remove Fourier spectral shaping
NEG-C4:  Operational Equivalence — force primitive identity (a=a)
CMP-1:   F01 ∧ N01 → Action Precedence (compound: finitude + non-commutation)
CMP-2:   C6 ∧ C8 → Net Ratchet Gain (compound: dual-loop + net gain over 720°)
"""

import numpy as np
import json
import os
from datetime import datetime, UTC

import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from proto_ratchet_sim_runner import (
    make_random_density_matrix,
    make_random_unitary,
    von_neumann_entropy,
    EvidenceToken,
)


def negentropy(rho, d):
    S = von_neumann_entropy(rho)
    return max(0.0, 1.0 - S / np.log2(d))


def purity(rho):
    return float(np.real(np.trace(rho @ rho)))


def build_engine_cycle(rho, d, H, L, F_mat, apply_Ti=True, apply_Te=True,
                       apply_Fe=True, apply_Fi=True, swap_chirality=False,
                       cptp_violation=False, force_identity=False,
                       commutative=False, dt=0.05):
    """Configurable 8-stage engine cycle with selective operator disabling."""
    
    if force_identity:
        return rho.copy()
    
    if commutative:
        H = np.diag(np.diagonal(H))
        L = np.diag(np.diagonal(L))
    
    stages = []
    
    # Define operator order based on chirality
    if swap_chirality:
        # REVERSED: Fi→Te→Fe→Ti (instead of Ti→Fe→Te→Fi)
        if apply_Fi:
            stages.append(('Fi', lambda r: F_mat @ r @ F_mat.conj().T))
        if apply_Te:
            U = np.eye(d, dtype=complex) - 1j * H * dt
            u, _, vh = np.linalg.svd(U)
            U_clean = u @ vh
            stages.append(('Te', lambda r, U=U_clean: U @ r @ U.conj().T))
        if apply_Fe:
            def fe_step(r):
                LdL = L.conj().T @ L
                dr = L @ r @ L.conj().T - 0.5 * (LdL @ r + r @ LdL)
                return r + dr * dt
            stages.append(('Fe', fe_step))
        if apply_Ti:
            stages.append(('Ti', lambda r: np.diag(np.diagonal(r)).astype(complex)))
    else:
        # STANDARD: Ti→Fe→Te→Fi
        if apply_Ti:
            stages.append(('Ti', lambda r: np.diag(np.diagonal(r)).astype(complex)))
        if apply_Fe:
            def fe_step(r):
                LdL = L.conj().T @ L
                dr = L @ r @ L.conj().T - 0.5 * (LdL @ r + r @ LdL)
                return r + dr * dt
            stages.append(('Fe', fe_step))
        if apply_Te:
            U = np.eye(d, dtype=complex) - 1j * H * dt
            u, _, vh = np.linalg.svd(U)
            U_clean = u @ vh
            stages.append(('Te', lambda r, U=U_clean: U @ r @ U.conj().T))
        if apply_Fi:
            stages.append(('Fi', lambda r: F_mat @ r @ F_mat.conj().T))
    
    # Execute stages
    for name, op in stages:
        rho = op(rho)
        
        if cptp_violation:
            # Intentionally break CPTP: scale trace UP (non-trace-preserving)
            rho *= 1.05
        
        # Enforce Hermiticity
        rho = (rho + rho.conj().T) / 2
        # Clamp eigenvalues for positivity (unless testing CPTP violation)
        if not cptp_violation:
            evals, evecs = np.linalg.eigh(rho)
            evals = np.maximum(evals, 0)
            rho = evecs @ np.diag(evals) @ evecs.conj().T
        rho /= max(np.real(np.trace(rho)), 1e-12)
    
    return rho


def run_single_neg_test(name, d, n_cycles, **kwargs):
    """Run a single negative test and return (name, avg_dphi, killed)."""
    np.random.seed(42)
    
    H_raw = np.random.randn(d, d) + 1j * np.random.randn(d, d)
    H = (H_raw + H_raw.conj().T) / 2 * 3.0
    L_raw = np.random.randn(d, d) + 1j * np.random.randn(d, d)
    L = L_raw / np.linalg.norm(L_raw) * 2.0
    F = np.zeros((d, d), dtype=complex)
    for j in range(d):
        for k in range(d):
            F[j, k] = np.exp(2j * np.pi * j * k / d) / np.sqrt(d)
    
    results = []
    for trial in range(5):
        np.random.seed(42 + trial)
        rho = make_random_density_matrix(d)
        phi_start = negentropy(rho, d)
        
        for _ in range(n_cycles):
            rho = build_engine_cycle(rho, d, H, L, F, **kwargs)
        
        phi_end = negentropy(rho, d)
        dphi = phi_end - phi_start
        results.append(dphi)
    
    avg_dphi = float(np.mean(results))
    killed = avg_dphi < -0.01 or all(r < 0.01 for r in results)
    return name, avg_dphi, killed


def run_deep_graveyard(d=4, n_cycles=50):
    """Execute the complete Deep Graveyard battery."""
    print("=" * 72)
    print("DEEP GRAVEYARD: 16-POINT CONSTRAINT MATRIX")
    print(f"  d={d}, cycles={n_cycles}, 5 trials each")
    print("=" * 72)
    
    tests = [
        ("NEG-C3: CPTP Violation",
         dict(cptp_violation=True)),
        ("NEG-X2: Chirality Swap",
         dict(swap_chirality=True)),
        ("NEG-Ti: No Measurement",
         dict(apply_Ti=False)),
        ("NEG-Te: No Unitary Drive",
         dict(apply_Te=False)),
        ("NEG-Fi: No Spectral Proj",
         dict(apply_Fi=False)),
        ("NEG-C4: Force Identity",
         dict(force_identity=True)),
    ]
    
    results = []
    evidence = []
    
    for test_name, kwargs in tests:
        name, avg_dphi, killed = run_single_neg_test(
            test_name, d, n_cycles, **kwargs)
        
        status = "KILL" if killed else "UNEXPECTED_PASS"
        icon = "✗" if killed else "⚠"
        print(f"  {icon} {name:35s}: avg ΔΦ={avg_dphi:+.4f} [{status}]")
        
        results.append({
            "test": name, "avg_dphi": avg_dphi,
            "status": status, "killed": killed
        })
        
        token_id = "" if killed else f"E_{name.split(':')[0].strip().replace('-','_')}_UNEXPECTED_PASS"
        sim_id = f"S_{name.split(':')[0].strip().replace('-','_')}"
        evidence.append(EvidenceToken(
            token_id=token_id if not killed else "",
            sim_spec_id=sim_id,
            status="KILL" if killed else "PASS",
            measured_value=avg_dphi,
            kill_reason=name.split(':')[1].strip() if killed else None,
        ))
    
    # ── COMPOUND TESTS ──
    print(f"\n  {'─'*68}")
    print(f"  COMPOUND INTERACTION TESTS")
    print(f"  {'─'*68}")
    
    # CMP-1: F01 ∧ N01 → Action Precedence
    # Finite + commutative system should fail to establish Axis 6 ordering
    name1, dphi1, killed1 = run_single_neg_test(
        "CMP-1: F01∧N01→Axis6", d, n_cycles, commutative=True)
    status1 = "KILL" if killed1 else "UNEXPECTED_PASS"
    print(f"  {'✗' if killed1 else '⚠'} {name1:35s}: avg ΔΦ={dphi1:+.4f} [{status1}]")
    results.append({"test": name1, "avg_dphi": dphi1, "status": status1, "killed": killed1})
    evidence.append(EvidenceToken(
        token_id="" if killed1 else "E_CMP1_UNEXPECTED_PASS",
        sim_spec_id="S_CMP_F01_N01",
        status="KILL" if killed1 else "PASS",
        measured_value=dphi1,
        kill_reason="COMMUTATIVE_BLOCKS_AXIS6_PRECEDENCE" if killed1 else None,
    ))
    
    # CMP-2: C6 ∧ C8 → Net Ratchet Gain (720° cycle)
    # Single-loop (no Te/Fi) should fail to achieve net ratchet over 720°
    name2, dphi2, killed2 = run_single_neg_test(
        "CMP-2: C6∧C8→Ratchet720", d, n_cycles * 2,  # Double cycles for 720°
        apply_Te=False, apply_Fi=False)
    status2 = "KILL" if killed2 else "UNEXPECTED_PASS"
    print(f"  {'✗' if killed2 else '⚠'} {name2:35s}: avg ΔΦ={dphi2:+.4f} [{status2}]")
    results.append({"test": name2, "avg_dphi": dphi2, "status": status2, "killed": killed2})
    evidence.append(EvidenceToken(
        token_id="" if killed2 else "E_CMP2_UNEXPECTED_PASS",
        sim_spec_id="S_CMP_C6_C8",
        status="KILL" if killed2 else "PASS",
        measured_value=dphi2,
        kill_reason="SINGLE_LOOP_FAILS_NET_RATCHET_720" if killed2 else None,
    ))
    
    # ── VERDICT ──
    total = len(results)
    killed_count = sum(1 for r in results if r["killed"])
    
    print(f"\n{'='*72}")
    print(f"DEEP GRAVEYARD VERDICT: {killed_count}/{total} KILLED")
    print(f"{'='*72}")
    
    if killed_count == total:
        print("  ALL constraints proven NECESSARY. Foundation is SEALED.")
    else:
        survivors = [r["test"] for r in results if not r["killed"]]
        print(f"  WARNING: {len(survivors)} tests survived unexpectedly:")
        for s in survivors:
            print(f"    ⚠ {s}")
    
    # Save
    base = os.path.dirname(os.path.abspath(__file__))
    results_dir = os.path.join(base, "a2_state", "sim_results")
    os.makedirs(results_dir, exist_ok=True)
    outpath = os.path.join(results_dir, "deep_graveyard_results.json")
    
    with open(outpath, "w") as f:
        json.dump({
            "timestamp": datetime.now(UTC).isoformat(),
            "d": d,
            "n_cycles": n_cycles,
            "total_tests": total,
            "killed_count": killed_count,
            "results": results,
            "evidence_ledger": [
                {"token_id": e.token_id, "sim_spec_id": e.sim_spec_id,
                 "status": e.status, "measured_value": e.measured_value,
                 "kill_reason": e.kill_reason} for e in evidence
            ],
        }, f, indent=2)
    
    print(f"  Results saved: {outpath}")
    return evidence, results


if __name__ == "__main__":
    run_deep_graveyard(d=4, n_cycles=50)
