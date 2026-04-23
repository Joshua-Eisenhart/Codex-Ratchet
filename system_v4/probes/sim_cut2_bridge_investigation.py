#!/usr/bin/env python3
"""
sim_cut2_bridge_investigation.py
================================

Investigation: Why does Fi (X x I x Z) fail to bridge cut2 (q1q2 vs q3)?
And what operator WOULD genuinely entangle q3 with the q1q2 subsystem?

Key finding expected: Fi acts as a LOCAL rotation on q1 when q3=|0>,
because Z|0> = +|0>.  The Z on q3 contributes only a state-dependent
phase, not entanglement.  We need an operator that flips q3 conditionally.
"""

import json
import os
import sys
from datetime import datetime, UTC

import numpy as np
classification = "classical_baseline"  # auto-backfill
divergence_log = "Classical baseline: cut-2 bridge behavior is investigated here by explicit 3-qubit operator numerics, not a canonical nonclassical witness."
TOOL_MANIFEST = {
    "numpy": {"tried": True, "used": True, "reason": "3-qubit operator construction, evolution, and cut-information numerics"},
}
TOOL_INTEGRATION_DEPTH = {
    "numpy": "supportive",
}

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sim_3qubit_bridge_prototype import (
    I2, SIGMA_X, SIGMA_Y, SIGMA_Z,
    partial_trace_keep, von_neumann_entropy, ensure_valid_density,
    BIPARTITIONS, compute_info_measures,
    build_3q_Ti, build_3q_Fe, build_3q_Te,
)


# ===================================================================
# PART 1: WHY DOES Fi FAIL?
# ===================================================================

def analyse_fi_failure():
    """
    H_Fi = X x I x Z.
    On |000>:  H_Fi|000> = (X|0>) x (I|0>) x (Z|0>) = |1> x |0> x |0> = |100>.
    So U_Fi(t)|000> = cos(t)|000> - i sin(t)|100>.
    This is a superposition within the q1 subspace only -- q2 and q3 are
    ALWAYS |0>, meaning no entanglement is created across ANY cut involving q3.

    The root cause: Z|0> = +1|0>, so Z acts as identity on the |0> state of q3.
    """
    print("=" * 72)
    print("  PART 1: Fi FAILURE ANALYSIS")
    print("=" * 72)

    H_Fi = np.kron(np.kron(SIGMA_X, I2), SIGMA_Z)  # 8x8

    # Initial state |000>
    psi_000 = np.zeros(8, dtype=complex)
    psi_000[0] = 1.0
    rho_000 = np.outer(psi_000, psi_000.conj())

    # Commutator [H_Fi, rho_000]
    commutator = H_Fi @ rho_000 - rho_000 @ H_Fi
    comm_norm = np.linalg.norm(commutator, 'fro')
    print(f"  ||[H_Fi, rho_000]||_F = {comm_norm:.10f}")

    # H_Fi |000>
    result_vec = H_Fi @ psi_000
    print(f"  H_Fi|000> = {result_vec}")
    # Expected: |100> = index 4
    expected = np.zeros(8, dtype=complex)
    expected[4] = 1.0
    is_100 = np.allclose(result_vec, expected)
    print(f"  H_Fi|000> == |100>?  {is_100}")

    # Evolve and check entanglement
    theta = 0.4
    U_Fi = np.cos(theta / 2) * np.eye(8, dtype=complex) - 1j * np.sin(theta / 2) * H_Fi
    psi_evolved = U_Fi @ psi_000
    rho_evolved = np.outer(psi_evolved, psi_evolved.conj())

    # Check all cuts
    info_evolved = compute_info_measures(rho_evolved)
    print("\n  After Fi on |000> (theta=0.4):")
    for cut_name, data in info_evolved.items():
        print(f"    {data['label']:20s}  I_c = {data['I_c']:+.8f}  "
              f"I(A:B) = {data['I_AB']:+.8f}")

    # Verify: the evolved state is cos(t/2)|000> - i sin(t/2)|100>
    # This is separable as (cos|0> - i sin|1>) x |0> x |0>
    # because |000> and |100> differ ONLY in q1.
    c0 = np.cos(theta / 2)
    c1 = -1j * np.sin(theta / 2)
    psi_q1 = np.array([c0, c1])
    psi_expected = np.kron(np.kron(psi_q1, np.array([1, 0])), np.array([1, 0]))
    is_product = np.allclose(psi_evolved, psi_expected)
    print(f"\n  Evolved state is product state (q1 x |0> x |0>)?  {is_product}")

    # The Z on q3 explanation
    z_on_zero = SIGMA_Z @ np.array([1, 0], dtype=complex)
    z_eigenvalue = z_on_zero[0]  # should be +1
    print(f"  Z|0> eigenvalue: {z_eigenvalue.real:+.1f}")
    print(f"  --> Z acts as +1*identity on |0>, so X x I x Z = X x I x I on |000>")
    print(f"  --> Fi is a LOCAL q1 rotation, not a q1-q3 entangling gate")

    analysis = {
        "commutator_frobenius_norm": float(comm_norm),
        "commutator_is_zero": bool(comm_norm < 1e-10),
        "H_Fi_on_000_equals_100": bool(is_100),
        "evolved_state_is_product": bool(is_product),
        "z_eigenvalue_on_ket0": float(z_eigenvalue.real),
        "reason": (
            "Z|0> = +|0>, so X x I x Z acting on |000> reduces to "
            "X x I x I -- a local q1 rotation. The Z on q3 contributes "
            "only a state-dependent phase (+1 for |0>, -1 for |1>), but "
            "since q3 starts in |0> and no operator ever flips q3, the "
            "phase is always +1. No entanglement across cut2 is generated."
        ),
    }
    return analysis


# ===================================================================
# PART 2: CANDIDATE OPERATORS TO BRIDGE CUT2
# ===================================================================

def build_cnot_13():
    """CNOT controlled on q1, target q3: |0><0| x I x I + |1><1| x I x X"""
    proj0 = np.array([[1, 0], [0, 0]], dtype=complex)  # |0><0|
    proj1 = np.array([[0, 0], [0, 1]], dtype=complex)  # |1><1|
    cnot = np.kron(np.kron(proj0, I2), I2) + np.kron(np.kron(proj1, I2), SIGMA_X)
    return cnot


def build_swap_23():
    """SWAP on qubits 2 and 3: I x SWAP"""
    swap_2q = np.array([
        [1, 0, 0, 0],
        [0, 0, 1, 0],
        [0, 1, 0, 0],
        [0, 0, 0, 1],
    ], dtype=complex)
    return np.kron(I2, swap_2q)


def build_iswap_23():
    """iSWAP-like on q2,q3: exp(-i pi/4 (XX+YY)/2) acting on q2,q3.
    H = (XX + YY)/2 on q2,q3, tensored with I on q1.
    This is the XY interaction Hamiltonian."""
    XX_23 = np.kron(SIGMA_X, SIGMA_X)
    YY_23 = np.kron(SIGMA_Y, SIGMA_Y)
    H_xy = (XX_23 + YY_23) / 2  # 4x4
    H_full = np.kron(I2, H_xy)  # 8x8
    # Use angle pi/4 for partial swap
    angle = np.pi / 4
    U = np.cos(angle / 2) * np.eye(8, dtype=complex) - 1j * np.sin(angle / 2) * H_full
    return U


def build_cz_13():
    """CZ between q1 and q3: diag(1,1,1,-1) on q1,q3 space.
    CZ = |0><0| x I x I + |1><1| x I x Z"""
    proj0 = np.array([[1, 0], [0, 0]], dtype=complex)
    proj1 = np.array([[0, 0], [0, 1]], dtype=complex)
    cz = np.kron(np.kron(proj0, I2), I2) + np.kron(np.kron(proj1, I2), SIGMA_Z)
    return cz


def build_xx_23():
    """XX interaction on q2,q3: I x X x X, as a unitary rotation."""
    H = np.kron(I2, np.kron(SIGMA_X, SIGMA_X))  # 8x8
    angle = 0.4  # same strength as Fe
    U = np.cos(angle / 2) * np.eye(8, dtype=complex) - 1j * np.sin(angle / 2) * H
    return U


CANDIDATES = {
    "CNOT_13": {"builder": build_cnot_13, "is_unitary_gate": True},
    "SWAP_23": {"builder": build_swap_23, "is_unitary_gate": True},
    "iSWAP_23": {"builder": build_iswap_23, "is_unitary_gate": True},
    "CZ_13": {"builder": build_cz_13, "is_unitary_gate": True},
    "XX_23": {"builder": build_xx_23, "is_unitary_gate": True},
}


def run_candidate_cycle(candidate_U, n_cycles=20, dephasing=0.05):
    """
    Run cycle: Ti -> Fe -> CANDIDATE -> Te -> Fi
    from |000>, with given dephasing strength.
    Fi is kept as X x I x Z (the original, which we now know is local).
    """
    Ti = build_3q_Ti(strength=dephasing)
    Fe = build_3q_Fe(strength=1.0, phi=0.4)
    Te = build_3q_Te(strength=dephasing, q=0.7)

    # Fi as Hamiltonian rotation (original)
    H_Fi = np.kron(np.kron(SIGMA_X, I2), SIGMA_Z)
    theta_fi = 0.4

    # Initial state |000>
    rho = np.zeros((8, 8), dtype=complex)
    rho[0, 0] = 1.0

    history = {"cut1": [], "cut2": [], "cut3": []}
    max_ic = {"cut1_1vs23": -999.0, "cut2_12vs3": -999.0, "cut3_13vs2": -999.0}

    for cycle in range(1, n_cycles + 1):
        # Ti
        rho = Ti(rho)
        # Fe
        rho = Fe(rho)
        # CANDIDATE
        rho = candidate_U @ rho @ candidate_U.conj().T
        rho = ensure_valid_density(rho)
        # Te
        rho = Te(rho)
        # Fi (original)
        angle = theta_fi
        U_fi = np.cos(angle / 2) * np.eye(8, dtype=complex) - 1j * np.sin(angle / 2) * H_Fi
        rho = U_fi @ rho @ U_fi.conj().T
        rho = ensure_valid_density(rho)

        info = compute_info_measures(rho)
        for cut_name in max_ic:
            ic_val = info[cut_name]["I_c"]
            if ic_val > max_ic[cut_name]:
                max_ic[cut_name] = ic_val

        history["cut1"].append(float(info["cut1_1vs23"]["I_c"]))
        history["cut2"].append(float(info["cut2_12vs3"]["I_c"]))
        history["cut3"].append(float(info["cut3_13vs2"]["I_c"]))

    return {
        "cut1_max_ic": round(float(max_ic["cut1_1vs23"]), 8),
        "cut2_max_ic": round(float(max_ic["cut2_12vs3"]), 8),
        "cut3_max_ic": round(float(max_ic["cut3_13vs2"]), 8),
        "cut1_trajectory": [round(v, 8) for v in history["cut1"]],
        "cut2_trajectory": [round(v, 8) for v in history["cut2"]],
        "cut3_trajectory": [round(v, 8) for v in history["cut3"]],
    }


def test_candidates():
    """Test all candidate operators for cut2 bridging."""
    print("\n" + "=" * 72)
    print("  PART 2: CANDIDATE CUT2 BRIDGE OPERATORS")
    print("=" * 72)

    results = {}
    for name, spec in CANDIDATES.items():
        U = spec["builder"]()

        # Verify unitarity
        is_unitary = np.allclose(U @ U.conj().T, np.eye(8), atol=1e-12)
        print(f"\n  {name}:")
        print(f"    Unitary: {is_unitary}")

        cycle_result = run_candidate_cycle(U, n_cycles=20, dephasing=0.05)
        results[name] = cycle_result
        results[name]["is_unitary"] = bool(is_unitary)

        print(f"    cut1 max I_c = {cycle_result['cut1_max_ic']:+.8f}")
        print(f"    cut2 max I_c = {cycle_result['cut2_max_ic']:+.8f}")
        print(f"    cut3 max I_c = {cycle_result['cut3_max_ic']:+.8f}")

    return results


# ===================================================================
# PART 3: ALL THREE CUTS POSITIVE SIMULTANEOUSLY?
# ===================================================================

def check_all_cuts_positive(candidate_results):
    """Find the best cut2 bridge and check if all 3 cuts are positive."""
    print("\n" + "=" * 72)
    print("  PART 3: ALL THREE CUTS POSITIVE?")
    print("=" * 72)

    # Rank by cut2 I_c
    ranked = sorted(candidate_results.items(),
                    key=lambda kv: kv[1]["cut2_max_ic"], reverse=True)

    best_name, best_data = ranked[0]
    print(f"\n  Best cut2 bridge: {best_name}")
    print(f"    cut1 max I_c = {best_data['cut1_max_ic']:+.8f}")
    print(f"    cut2 max I_c = {best_data['cut2_max_ic']:+.8f}")
    print(f"    cut3 max I_c = {best_data['cut3_max_ic']:+.8f}")

    all_positive = (
        best_data["cut1_max_ic"] > 1e-10
        and best_data["cut2_max_ic"] > 1e-10
        and best_data["cut3_max_ic"] > 1e-10
    )
    print(f"    All three cuts I_c > 0?  {all_positive}")

    # Check if ANY candidate achieves all three
    any_all_positive = False
    any_all_name = None
    for name, data in ranked:
        if (data["cut1_max_ic"] > 1e-10
                and data["cut2_max_ic"] > 1e-10
                and data["cut3_max_ic"] > 1e-10):
            any_all_positive = True
            any_all_name = name
            break

    if any_all_positive:
        print(f"\n  First candidate with ALL cuts positive: {any_all_name}")
    else:
        print("\n  No candidate achieves all three cuts positive simultaneously.")
        # Check which cuts are missing for each
        for name, data in ranked[:3]:
            missing = []
            if data["cut1_max_ic"] <= 1e-10:
                missing.append("cut1")
            if data["cut2_max_ic"] <= 1e-10:
                missing.append("cut2")
            if data["cut3_max_ic"] <= 1e-10:
                missing.append("cut3")
            print(f"    {name}: missing {missing}")

    return best_name, all_positive, any_all_positive, any_all_name


# ===================================================================
# MAIN
# ===================================================================

def sanitize(obj):
    """Recursively convert numpy types to native Python for JSON."""
    if isinstance(obj, dict):
        return {k: sanitize(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [sanitize(v) for v in obj]
    elif isinstance(obj, (np.integer,)):
        return int(obj)
    elif isinstance(obj, (np.floating,)):
        return float(obj)
    elif isinstance(obj, (np.bool_,)):
        return bool(obj)
    elif isinstance(obj, np.ndarray):
        return sanitize(obj.tolist())
    return obj


def main():
    print("=" * 72)
    print("  CUT2 BRIDGE INVESTIGATION")
    print("  Why does Fi (X x I x Z) fail to entangle q3?")
    print("=" * 72)

    # Part 1
    fi_analysis = analyse_fi_failure()

    # Part 2
    candidate_results = test_candidates()

    # Part 3
    best_name, all_pos, any_all_pos, any_all_name = check_all_cuts_positive(
        candidate_results
    )

    # Build output
    output = {
        "name": "cut2_bridge_investigation",
        "fi_failure_analysis": fi_analysis,
        "candidate_operators": {
            name: {
                "cut1_max_ic": data["cut1_max_ic"],
                "cut2_max_ic": data["cut2_max_ic"],
                "cut3_max_ic": data["cut3_max_ic"],
                "is_unitary": data["is_unitary"],
            }
            for name, data in candidate_results.items()
        },
        "candidate_trajectories": {
            name: {
                "cut1": data["cut1_trajectory"],
                "cut2": data["cut2_trajectory"],
                "cut3": data["cut3_trajectory"],
            }
            for name, data in candidate_results.items()
        },
        "best_cut2_bridge": best_name,
        "best_cut2_bridge_all_cuts": {
            "cut1_max_ic": candidate_results[best_name]["cut1_max_ic"],
            "cut2_max_ic": candidate_results[best_name]["cut2_max_ic"],
            "cut3_max_ic": candidate_results[best_name]["cut3_max_ic"],
        },
        "all_three_cuts_positive": bool(all_pos),
        "any_candidate_all_three_positive": bool(any_all_pos),
        "any_candidate_all_three_name": any_all_name,
        "timestamp": datetime.now(UTC).strftime("%Y-%m-%d"),
    }

    output = sanitize(output)

    out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "cut2_bridge_investigation_results.json")
    with open(out_path, "w") as f:
        json.dump(output, f, indent=2)
    print(f"\nResults written to {out_path}")

    # Quick summary
    print("\n" + "=" * 72)
    print("  SUMMARY")
    print("=" * 72)
    print(f"  Fi failure reason: {fi_analysis['reason'][:80]}...")
    print(f"  Best cut2 bridge:  {best_name}")
    print(f"  All 3 cuts > 0:    {all_pos}")
    if any_all_pos and any_all_name != best_name:
        print(f"  Alt all-3-positive: {any_all_name}")
    print("=" * 72)

    return output


if __name__ == "__main__":
    main()
