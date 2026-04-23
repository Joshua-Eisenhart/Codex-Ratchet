"""
EXTENDED GRAVEYARD: Additional Compound & Triplet Negative SIMs
================================================================
Extends the Deep Graveyard with:
- CMP-3: C3 ∧ C5 → Entropy Ordering (CPTP + Monotonicity)
- CMP-4: F01 ∧ N01 ∧ C3 → Triple Lock (Finitude + Non-Commutation + CPTP)
- CMP-5: C6 ∧ X2 → Dual-Loop + Chirality (both loops + correct handedness)
- NEG-SCRAMBLE: Random stage ordering (proves the 8-stage sequence matters)
- NEG-SYMMETRIC: Force all operators self-adjoint (removes dissipation asymmetry)
- NEG-DECOHERE: Maximal decoherence every stage (proves partial coherence needed)
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


def make_fourier(d):
    F = np.zeros((d, d), dtype=complex)
    for j in range(d):
        for k in range(d):
            F[j, k] = np.exp(2j * np.pi * j * k / d) / np.sqrt(d)
    return F


def enforce_psd(rho, d):
    """Enforce positive semi-definiteness and unit trace."""
    rho = (rho + rho.conj().T) / 2
    evals, evecs = np.linalg.eigh(rho)
    evals = np.maximum(evals, 0)
    rho = evecs @ np.diag(evals) @ evecs.conj().T
    tr = np.real(np.trace(rho))
    if tr > 1e-12:
        rho /= tr
    else:
        rho = np.eye(d, dtype=complex) / d
    return rho


def standard_8stage_cycle(rho, d, H, L, F, dt=0.05,
                          scramble_order=False,
                          force_symmetric=False,
                          max_decohere=False,
                          commutative_only=False,
                          no_dissipation=False,
                          no_coherence_transfer=False):
    """Full 8-stage cycle with configurable violations."""
    if commutative_only:
        H = np.diag(np.diagonal(H))
        L = np.diag(np.diagonal(L))

    if force_symmetric:
        L = (L + L.conj().T) / 2
        H = np.diag(np.real(np.diagonal(H)))

    stages = list(range(8))
    if scramble_order:
        np.random.shuffle(stages)

    for stage in stages:
        stage_type = stage % 4

        if stage_type == 0:  # Ti: Lüders measurement
            probs = np.abs(np.diagonal(rho))
            probs /= max(np.sum(probs), 1e-12)
            rho_meas = np.diag(probs.astype(complex))
            rho = 0.7 * rho + 0.3 * rho_meas

        elif stage_type == 1:  # Fe: Lindbladian dissipation
            if not no_dissipation:
                LdL = L.conj().T @ L
                drho = L @ rho @ L.conj().T - 0.5 * (LdL @ rho + rho @ LdL)
                rho = rho + drho * dt

        elif stage_type == 2:  # Te: Hamiltonian unitary
            U = np.eye(d, dtype=complex) - 1j * H * dt
            u, _, vh = np.linalg.svd(U)
            U = u @ vh
            rho = U @ rho @ U.conj().T

        elif stage_type == 3:  # Fi: Fourier spectral
            if not no_coherence_transfer:
                rho_f = F @ rho @ F.conj().T
                rho = 0.8 * rho + 0.2 * rho_f

        # Optional maximal decoherence after every stage
        if max_decohere:
            rho = np.diag(np.diagonal(rho)).astype(complex)

        rho = enforce_psd(rho, d)

    return rho


def run_test(name, d, n_cycles, cycle_kwargs):
    """Run a single negative test: 5 trials, report avg ΔΦ."""
    results = []
    np.random.seed(42)
    H_raw = np.random.randn(d, d) + 1j * np.random.randn(d, d)
    H = (H_raw + H_raw.conj().T) / 2 * 3.0
    L_raw = np.random.randn(d, d) + 1j * np.random.randn(d, d)
    L = L_raw / np.linalg.norm(L_raw) * 2.0
    F = make_fourier(d)

    for trial in range(5):
        np.random.seed(42 + trial)
        rho = make_random_density_matrix(d)
        phi_start = negentropy(rho, d)
        for _ in range(n_cycles):
            rho = standard_8stage_cycle(rho, d, H, L, F, **cycle_kwargs)
        phi_end = negentropy(rho, d)
        results.append(phi_end - phi_start)

    avg = float(np.mean(results))
    killed = avg < -0.01 or all(r < 0.01 for r in results)
    return name, avg, killed


def run_extended_graveyard(d=4, n_cycles=50):
    """Execute the extended graveyard battery."""
    print("=" * 72)
    print("EXTENDED GRAVEYARD: Additional Compound & Triplet Negative SIMs")
    print(f"  d={d}, cycles={n_cycles}, 5 trials each")
    print("=" * 72)

    tests = [
        ("CMP-3: C3∧C5 Entropy Order",
         dict(force_symmetric=True, no_dissipation=True)),
        ("CMP-4: F01∧N01∧C3 TripleLock",
         dict(commutative_only=True, force_symmetric=True)),
        ("CMP-5: C6∧X2 DualLoop+Chiral",
         dict(no_dissipation=True, no_coherence_transfer=True)),
        ("NEG-SCRAMBLE: Random Order",
         dict(scramble_order=True)),
        ("NEG-SYMMETRIC: Self-Adjoint",
         dict(force_symmetric=True)),
        ("NEG-DECOHERE: Max Decoherence",
         dict(max_decohere=True)),
    ]

    results = []
    evidence = []

    for test_name, kwargs in tests:
        name, avg_dphi, killed = run_test(test_name, d, n_cycles, kwargs)
        status = "KILL" if killed else "UNEXPECTED_PASS"
        icon = "✗" if killed else "⚠"
        print(f"  {icon} {name:40s}: avg ΔΦ={avg_dphi:+.4f} [{status}]")

        results.append({
            "test": name, "avg_dphi": avg_dphi,
            "status": status, "killed": killed
        })

        sim_id = name.split(":")[0].strip().replace("-", "_").replace("∧", "_AND_")
        evidence.append(EvidenceToken(
            token_id="" if killed else f"E_{sim_id}_UNEXPECTED_PASS",
            sim_spec_id=f"S_{sim_id}",
            status="KILL" if killed else "PASS",
            measured_value=avg_dphi,
            kill_reason=name.split(":")[1].strip() if killed else None,
        ))

    total = len(results)
    killed_count = sum(1 for r in results if r["killed"])

    print(f"\n{'='*72}")
    print(f"EXTENDED GRAVEYARD VERDICT: {killed_count}/{total} KILLED")
    print(f"{'='*72}")

    if killed_count == total:
        print("  ALL extended constraints proven NECESSARY.")
    else:
        survivors = [r["test"] for r in results if not r["killed"]]
        print(f"  WARNING: {len(survivors)} tests survived:")
        for s in survivors:
            print(f"    ⚠ {s}")

    base = os.path.dirname(os.path.abspath(__file__))
    results_dir = os.path.join(base, "a2_state", "sim_results")
    os.makedirs(results_dir, exist_ok=True)
    outpath = os.path.join(results_dir, "extended_graveyard_results.json")

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
    run_extended_graveyard(d=4, n_cycles=50)
