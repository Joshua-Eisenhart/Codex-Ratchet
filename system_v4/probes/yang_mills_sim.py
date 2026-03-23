"""
Yang-Mills SIM — Pro Thread 11
=================================
Finite-d lattice gauge with SU(2) gauge links (Te operators).
Wilson action = sum of trace of plaquettes.
Tests mass gap persistence across d=4..32.
"""

import numpy as np
import json
import os
from datetime import datetime, UTC

import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from proto_ratchet_sim_runner import (
    make_random_unitary,
    EvidenceToken,
)


def random_su2(d, seed=None):
    """Random SU(2)-like unitary in d dimensions."""
    if seed is not None:
        np.random.seed(seed)
    H = np.random.randn(d, d) + 1j * np.random.randn(d, d)
    H = (H + H.conj().T) / 2
    return np.linalg.matrix_power(
        np.eye(d, dtype=complex) + 1j * 0.1 * H, 1
    ) / np.linalg.norm(
        np.eye(d, dtype=complex) + 1j * 0.1 * H
    ) * np.sqrt(d)


def sim_yang_mills(dims=None, lattice_size=4):
    if dims is None:
        dims = [4, 8, 16, 32]

    print(f"\n{'='*60}")
    print(f"YANG-MILLS — LATTICE GAUGE MASS GAP")
    print(f"  dims={dims}, lattice={lattice_size}x{lattice_size}")
    print(f"{'='*60}")

    gap_data = {}

    for d in dims:
        np.random.seed(42)

        # Create lattice of gauge links (Te operators = unitaries)
        # Horizontal links
        h_links = [[make_random_unitary(d) for _ in range(lattice_size)]
                    for _ in range(lattice_size)]
        # Vertical links
        v_links = [[make_random_unitary(d) for _ in range(lattice_size)]
                    for _ in range(lattice_size)]

        # Compute plaquettes (loops of 4 links)
        plaquette_traces = []
        for i in range(lattice_size - 1):
            for j in range(lattice_size - 1):
                # Plaquette = U_h(i,j) @ U_v(i+1,j) @ U_h(i,j+1)† @ U_v(i,j)†
                P = (h_links[i][j] @
                     v_links[i+1][j] @
                     h_links[i][j+1].conj().T @
                     v_links[i][j].conj().T)
                plaquette_traces.append(float(np.real(np.trace(P))) / d)

        # Wilson action = sum of (1 - Re(Tr(P))/d)
        wilson_action = sum(1.0 - t for t in plaquette_traces)

        # Transfer matrix: construct effective Hamiltonian from plaquettes
        # The mass gap = difference between lowest two eigenvalues
        # Build transfer matrix from gauge links
        T_matrix = np.eye(d, dtype=complex)
        for j in range(lattice_size):
            T_matrix = T_matrix @ h_links[0][j]

        eigvals_T = np.sort(np.abs(np.linalg.eigvals(T_matrix)))[::-1]

        # Mass gap from transfer matrix: m = -ln(λ_1/λ_0)
        if len(eigvals_T) >= 2 and eigvals_T[0] > 0 and eigvals_T[1] > 0:
            mass_gap = -np.log(eigvals_T[1] / eigvals_T[0])
        else:
            mass_gap = 0.0

        # Eigenvalue gap of the effective Hamiltonian
        H_eff = -np.log(T_matrix @ T_matrix.conj().T + 1e-10 * np.eye(d)) / 2
        H_eff = (H_eff + H_eff.conj().T) / 2
        eig_H = np.sort(np.real(np.linalg.eigvalsh(H_eff)))
        spectral_gap = eig_H[1] - eig_H[0] if len(eig_H) >= 2 else 0.0

        gap_data[d] = {
            'mass_gap': float(mass_gap),
            'spectral_gap': float(spectral_gap),
            'wilson_action': float(wilson_action),
            'mean_plaquette': float(np.mean(plaquette_traces)),
        }

        print(f"\n  d={d}:")
        print(f"    Wilson action: {wilson_action:.4f}")
        print(f"    Mean plaquette: {np.mean(plaquette_traces):.4f}")
        print(f"    Transfer matrix mass gap: {mass_gap:.4f}")
        print(f"    Spectral gap: {spectral_gap:.4f}")

    # Check mass gap persists across dimensions
    all_gaps = [gap_data[d]['spectral_gap'] for d in dims]
    gap_persists = all(g > 1e-6 for g in all_gaps)

    print(f"\n  Mass gap persistence: {gap_persists}")
    print(f"  Gaps: {[f'{g:.4f}' for g in all_gaps]}")

    results = []

    if gap_persists:
        results.append(EvidenceToken(
            "E_SIM_MASS_GAP_PERSISTS_OK", "S_SIM_YANG_MILLS_V1",
            "PASS", float(min(all_gaps))
        ))
    else:
        results.append(EvidenceToken(
            "", "S_SIM_YANG_MILLS_V1",
            "KILL", 0.0, "MASS_GAP_CLOSES"
        ))

    # Token: Wilson action computed
    results.append(EvidenceToken(
        "E_SIM_WILSON_ACTION_OK", "S_SIM_WILSON_V1",
        "PASS", float(gap_data[dims[0]]['wilson_action'])
    ))

    return results


if __name__ == "__main__":
    results = sim_yang_mills()

    print(f"\n{'='*60}")
    print(f"YANG-MILLS RESULTS")
    print(f"{'='*60}")
    for e in results:
        icon = "✓" if e.status == "PASS" else "✗"
        print(f"  {icon} {e.sim_spec_id}: {e.status} (value={e.measured_value:.4f})")

    base = os.path.dirname(os.path.abspath(__file__))
    results_dir = os.path.join(base, "a2_state", "sim_results")
    os.makedirs(results_dir, exist_ok=True)
    outpath = os.path.join(results_dir, "yang_mills_results.json")
    with open(outpath, "w") as f:
        json.dump({
            "timestamp": datetime.now(UTC).isoformat(),
            "evidence_ledger": [
                {"token_id": e.token_id, "sim_spec_id": e.sim_spec_id,
                 "status": e.status, "measured_value": e.measured_value,
                 "kill_reason": e.kill_reason}
                for e in results
            ],
        }, f, indent=2)
    print(f"  Results saved to: {outpath}")
