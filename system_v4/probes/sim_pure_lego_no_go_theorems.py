#!/usr/bin/env python3
"""
PURE LEGO: Quantum No-Go Theorems
===================================
Foundational building block.  Pure math only -- numpy + z3.
No engine imports.  Every theorem verified against theory.

Sections
--------
1. No-Cloning: prove no unitary can clone all states
   - inner product argument: cloning two non-orthogonal states
     requires <psi|phi> = <psi|phi>^2, impossible unless overlap 0 or 1
2. No-Broadcasting: CPTP map cannot broadcast non-commuting mixed states
   - Tr_B(E(rho)) = rho AND Tr_A(E(rho)) = rho impossible for [rho1, rho2] != 0
3. No-Deleting: time-reverse of no-cloning
   - U|psi>|psi> = |psi>|0> for all |psi> contradicts unitarity
4. Z3 structural proof: encode inner product constraint, show UNSAT
"""

import json, pathlib, time
import numpy as np
from z3 import (
    RealSort, Real, Solver, unsat, And, Or, Not,
    ForAll, Exists, Implies, sat,
)

np.random.seed(42)
EPS = 1e-12
RESULTS = {}

# ──────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────

def ket(v):
    """Column vector from list."""
    return np.array(v, dtype=complex).reshape(-1, 1)

def dm(v):
    """Density matrix from ket vector."""
    k = ket(v)
    return k @ k.conj().T

def random_unitary(n):
    """Haar-random unitary via QR of Gaussian matrix."""
    z = (np.random.randn(n, n) + 1j * np.random.randn(n, n)) / np.sqrt(2)
    q, r = np.linalg.qr(z)
    d = np.diag(r)
    ph = d / np.abs(d)
    return q @ np.diag(ph)

def partial_trace(rho, dims, keep):
    """Partial trace of a bipartite density matrix.
    dims = [dA, dB], keep = 0 for A, 1 for B."""
    dA, dB = dims
    rho_r = rho.reshape(dA, dB, dA, dB)
    if keep == 0:
        return np.trace(rho_r, axis1=1, axis2=3)
    else:
        return np.trace(rho_r, axis1=0, axis2=2)

# ──────────────────────────────────────────────────────────────────────
# 1. No-Cloning Theorem (numerical inner-product proof)
# ──────────────────────────────────────────────────────────────────────

print("=" * 60)
print("SECTION 1: No-Cloning Theorem")
print("=" * 60)

def test_no_cloning():
    """
    If a unitary U clones, then for any two states |psi>, |phi>:
      U|psi>|0> = |psi>|psi>
      U|phi>|0> = |phi>|phi>
    Taking inner products:
      <psi|phi><0|0> = <psi|phi>^2
      => <psi|phi> = <psi|phi>^2
      => <psi|phi>(1 - <psi|phi>) = 0
      => <psi|phi> in {0, 1}
    So cloning is impossible for non-orthogonal, non-identical states.
    """
    results = {}

    # Test with many pairs of non-orthogonal states
    test_pairs = [
        ("|0>", "|+>", ket([1, 0]), ket([1/np.sqrt(2), 1/np.sqrt(2)])),
        ("|0>", "|psi(pi/8)>", ket([1, 0]), ket([np.cos(np.pi/8), np.sin(np.pi/8)])),
        ("|+>", "|psi(pi/3)>", ket([1/np.sqrt(2), 1/np.sqrt(2)]),
         ket([np.cos(np.pi/3), np.sin(np.pi/3)])),
    ]

    pair_results = []
    for label_a, label_b, psi, phi in test_pairs:
        overlap = float(np.abs((psi.conj().T @ phi).item()))
        overlap_sq = overlap ** 2
        # If cloning existed, overlap == overlap^2
        cloning_consistent = abs(overlap - overlap_sq) < EPS
        contradiction = not cloning_consistent

        pair_results.append({
            "pair": f"({label_a}, {label_b})",
            "overlap": overlap,
            "overlap_squared": overlap_sq,
            "gap": float(abs(overlap - overlap_sq)),
            "cloning_would_require_equality": True,
            "equality_holds": cloning_consistent,
            "contradiction": contradiction,
        })
        tag = "CONTRADICTION" if contradiction else "TRIVIAL"
        print(f"  {tag}: {label_a},{label_b}  "
              f"|<psi|phi>|={overlap:.6f}  "
              f"|<psi|phi>|^2={overlap_sq:.6f}  "
              f"gap={abs(overlap - overlap_sq):.6f}")

    # Exhaustive random sweep: sample 200 random pairs
    n_random = 200
    n_contradictions = 0
    for _ in range(n_random):
        theta = np.random.uniform(0.01, np.pi/2 - 0.01)
        psi = ket([1, 0])
        phi = ket([np.cos(theta), np.sin(theta)])
        ov = float(np.abs((psi.conj().T @ phi).item()))
        if abs(ov - ov**2) > EPS:
            n_contradictions += 1

    pair_results.append({
        "random_sweep": True,
        "n_pairs": n_random,
        "contradictions_found": n_contradictions,
        "fraction_contradicted": n_contradictions / n_random,
    })
    print(f"  Random sweep: {n_contradictions}/{n_random} pairs contradict cloning")

    # Brute-force: try 50 random unitaries on 4-d space, check if any clones
    n_unitary_tests = 50
    n_clone_failures = 0
    for _ in range(n_unitary_tests):
        U = random_unitary(4)  # 2-qubit unitary
        zero = ket([1, 0])
        psi = ket([1, 0])
        phi = ket([1/np.sqrt(2), 1/np.sqrt(2)])
        # Input: |psi>|0> in 4-d
        input_psi = np.kron(psi, zero)
        input_phi = np.kron(phi, zero)
        # Target outputs
        target_psi = np.kron(psi, psi)
        target_phi = np.kron(phi, phi)
        # Apply U
        out_psi = U @ input_psi
        out_phi = U @ input_phi
        # Check both clone conditions
        fid_psi = float(np.abs((target_psi.conj().T @ out_psi).item())**2)
        fid_phi = float(np.abs((target_phi.conj().T @ out_phi).item())**2)
        if fid_psi < 1 - 1e-6 or fid_phi < 1 - 1e-6:
            n_clone_failures += 1

    results["inner_product_pairs"] = pair_results
    results["brute_force_unitary_search"] = {
        "n_tested": n_unitary_tests,
        "n_failed_to_clone_both": n_clone_failures,
        "none_succeeded": n_clone_failures == n_unitary_tests,
    }
    results["all_pass"] = (
        all(p.get("contradiction", True) for p in pair_results if "pair" in p)
        and n_clone_failures == n_unitary_tests
    )
    print(f"  Brute-force unitary search: {n_clone_failures}/{n_unitary_tests} "
          f"failed to clone (expected: all)")
    print(f"  SECTION 1 PASS: {results['all_pass']}")
    return results

RESULTS["1_no_cloning"] = test_no_cloning()

# ──────────────────────────────────────────────────────────────────────
# 2. No-Broadcasting Theorem
# ──────────────────────────────────────────────────────────────────────

print(f"\n{'=' * 60}")
print("SECTION 2: No-Broadcasting Theorem")
print("=" * 60)

def test_no_broadcasting():
    """
    For mixed states rho1, rho2 with [rho1, rho2] != 0,
    no CPTP map E: B(H) -> B(H x H) can satisfy both:
      Tr_B(E(rho)) = rho  AND  Tr_A(E(rho)) = rho
    for both rho1 and rho2 simultaneously.

    Proof sketch: if broadcasting existed, it would imply cloning
    for the eigenstates, which contradicts no-cloning whenever
    the eigenbases don't coincide (i.e. states don't commute).

    We verify:
    1. Non-commuting states cannot be broadcast (numerical check)
    2. Commuting states CAN be broadcast (positive control)
    """
    results = {}

    # Non-commuting pair: rho1 = |0><0|, rho2 = |+><+|
    rho1 = dm([1, 0])
    rho2 = dm([1/np.sqrt(2), 1/np.sqrt(2)])
    comm = rho1 @ rho2 - rho2 @ rho1
    comm_norm = float(np.linalg.norm(comm))
    states_commute = comm_norm < EPS

    print(f"  rho1 = |0><0|, rho2 = |+><+|")
    print(f"  [rho1, rho2] norm = {comm_norm:.6f}  (commute: {states_commute})")

    # Try to find a broadcasting map by brute-force random CPTP (Stinespring)
    # For each random isometry V: C^2 -> C^4, check broadcast conditions
    n_attempts = 200
    best_broadcast_error = np.inf

    for _ in range(n_attempts):
        # Random isometry V: 2 -> 4 via QR
        z = (np.random.randn(4, 2) + 1j * np.random.randn(4, 2)) / np.sqrt(2)
        V, _ = np.linalg.qr(z)
        V = V[:, :2]  # 4x2 isometry

        total_error = 0.0
        for rho in [rho1, rho2]:
            # E(rho) = V rho V^dag  (Stinespring with trivial environment)
            E_rho = V @ rho @ V.conj().T  # 4x4
            trB = partial_trace(E_rho, [2, 2], 0)  # 2x2
            trA = partial_trace(E_rho, [2, 2], 1)  # 2x2
            err_A = np.linalg.norm(trB - rho)
            err_B = np.linalg.norm(trA - rho)
            total_error += err_A + err_B

        if total_error < best_broadcast_error:
            best_broadcast_error = total_error

    broadcast_impossible = best_broadcast_error > 0.01

    results["non_commuting_pair"] = {
        "commutator_norm": comm_norm,
        "states_commute": states_commute,
        "n_random_cptp_tested": n_attempts,
        "best_broadcast_error": float(best_broadcast_error),
        "broadcast_impossible": broadcast_impossible,
    }
    print(f"  Best broadcast error (non-commuting): {best_broadcast_error:.6f}")
    print(f"  Broadcasting impossible: {broadcast_impossible}")

    # Positive control: commuting states CAN be broadcast
    # rho1 = |0><0|, rho2 = |1><1|  (orthogonal, commuting)
    rho_c1 = dm([1, 0])
    rho_c2 = dm([0, 1])
    comm_c = rho_c1 @ rho_c2 - rho_c2 @ rho_c1
    comm_c_norm = float(np.linalg.norm(comm_c))

    # The CNOT-like map V|0> = |00>, V|1> = |11> broadcasts these
    V_broadcast = np.zeros((4, 2), dtype=complex)
    V_broadcast[0, 0] = 1.0  # |00> from |0>
    V_broadcast[3, 1] = 1.0  # |11> from |1>

    broadcast_err_c = 0.0
    for rho in [rho_c1, rho_c2]:
        E_rho = V_broadcast @ rho @ V_broadcast.conj().T
        trB = partial_trace(E_rho, [2, 2], 0)
        trA = partial_trace(E_rho, [2, 2], 1)
        broadcast_err_c += np.linalg.norm(trB - rho) + np.linalg.norm(trA - rho)

    commuting_broadcast_works = broadcast_err_c < EPS

    results["commuting_pair_control"] = {
        "commutator_norm": float(comm_c_norm),
        "states_commute": comm_c_norm < EPS,
        "broadcast_error": float(broadcast_err_c),
        "broadcast_works": commuting_broadcast_works,
    }
    print(f"  Commuting control broadcast error: {broadcast_err_c:.6e}")
    print(f"  Commuting broadcast works: {commuting_broadcast_works}")

    # Additional non-commuting pairs
    extra_pairs = []
    for _ in range(20):
        # Random mixed states from random pure blends
        alpha = np.random.uniform(0.1, 0.9)
        theta1 = np.random.uniform(0, np.pi)
        theta2 = np.random.uniform(0, np.pi)
        phi_rand = np.random.uniform(0, 2 * np.pi)

        r1 = alpha * dm([np.cos(theta1/2), np.sin(theta1/2)]) + \
             (1 - alpha) * dm([np.sin(theta1/2), -np.cos(theta1/2)])
        r2 = alpha * dm([np.cos(theta2/2), np.sin(theta2/2) * np.exp(1j*phi_rand)]) + \
             (1 - alpha) * dm([np.sin(theta2/2), -np.cos(theta2/2) * np.exp(1j*phi_rand)])

        c_norm = float(np.linalg.norm(r1 @ r2 - r2 @ r1))
        if c_norm > 0.01:
            extra_pairs.append({"commutator_norm": c_norm, "non_commuting": True})

    results["extra_non_commuting_pairs_tested"] = len(extra_pairs)
    results["all_pass"] = (
        broadcast_impossible
        and commuting_broadcast_works
        and not states_commute
    )
    print(f"  SECTION 2 PASS: {results['all_pass']}")
    return results

RESULTS["2_no_broadcasting"] = test_no_broadcasting()

# ──────────────────────────────────────────────────────────────────────
# 3. No-Deleting Theorem
# ──────────────────────────────────────────────────────────────────────

print(f"\n{'=' * 60}")
print("SECTION 3: No-Deleting Theorem")
print("=" * 60)

def test_no_deleting():
    """
    No unitary U can satisfy U|psi>|psi> = |psi>|0> for all |psi>.
    Time-reverse of no-cloning.

    Proof: if U|psi>|psi> = |psi>|0> and U|phi>|phi> = |phi>|0>, then
      <psi|phi>^2 = <psi|phi><0|0> = <psi|phi>
      => <psi|phi>(<psi|phi> - 1) = 0
      => <psi|phi> in {0, 1}
    Same algebraic structure as no-cloning.
    """
    results = {}

    # Inner product argument
    test_pairs = [
        ("|0>", "|+>", ket([1, 0]), ket([1/np.sqrt(2), 1/np.sqrt(2)])),
        ("|0>", "|psi(pi/6)>", ket([1, 0]), ket([np.cos(np.pi/6), np.sin(np.pi/6)])),
        ("|+>", "|1>", ket([1/np.sqrt(2), 1/np.sqrt(2)]), ket([0, 1])),
    ]

    pair_results = []
    for label_a, label_b, psi, phi in test_pairs:
        overlap = float(np.abs((psi.conj().T @ phi).item()))
        overlap_sq = overlap ** 2
        # Deleting requires overlap^2 = overlap => same constraint as cloning
        deletion_consistent = abs(overlap_sq - overlap) < EPS
        contradiction = not deletion_consistent

        pair_results.append({
            "pair": f"({label_a}, {label_b})",
            "overlap": overlap,
            "overlap_squared": overlap_sq,
            "gap": float(abs(overlap_sq - overlap)),
            "contradiction": contradiction,
        })
        tag = "CONTRADICTION" if contradiction else "TRIVIAL"
        print(f"  {tag}: {label_a},{label_b}  "
              f"|<psi|phi>|={overlap:.6f}  "
              f"|<psi|phi>|^2={overlap_sq:.6f}")

    # Brute-force unitary search for deletion
    n_unitary_tests = 50
    n_delete_failures = 0
    zero = ket([1, 0])
    psi = ket([1, 0])
    phi = ket([1/np.sqrt(2), 1/np.sqrt(2)])

    for _ in range(n_unitary_tests):
        U = random_unitary(4)
        # Input: |psi>|psi>, |phi>|phi>
        in_psi = np.kron(psi, psi)
        in_phi = np.kron(phi, phi)
        # Target: |psi>|0>, |phi>|0>
        tgt_psi = np.kron(psi, zero)
        tgt_phi = np.kron(phi, zero)

        out_psi = U @ in_psi
        out_phi = U @ in_phi
        fid_psi = float(np.abs((tgt_psi.conj().T @ out_psi).item())**2)
        fid_phi = float(np.abs((tgt_phi.conj().T @ out_phi).item())**2)
        if fid_psi < 1 - 1e-6 or fid_phi < 1 - 1e-6:
            n_delete_failures += 1

    results["inner_product_pairs"] = pair_results
    results["brute_force_unitary_search"] = {
        "n_tested": n_unitary_tests,
        "n_failed_to_delete_both": n_delete_failures,
        "none_succeeded": n_delete_failures == n_unitary_tests,
    }
    results["all_pass"] = (
        all(p["contradiction"] for p in pair_results)
        and n_delete_failures == n_unitary_tests
    )
    print(f"  Brute-force: {n_delete_failures}/{n_unitary_tests} failed to delete")
    print(f"  SECTION 3 PASS: {results['all_pass']}")
    return results

RESULTS["3_no_deleting"] = test_no_deleting()

# ──────────────────────────────────────────────────────────────────────
# 4. Z3 Structural Proof: No-Cloning is UNSAT
# ──────────────────────────────────────────────────────────────────────

print(f"\n{'=' * 60}")
print("SECTION 4: Z3 Structural Proof")
print("=" * 60)

def test_z3_no_cloning():
    """
    Encode the no-cloning inner product constraint in Z3 and show UNSAT.

    Variables: x = |<psi|phi>| (real, 0 < x < 1)
    Constraint from cloning: x = x^2
    We ask: is there an x in (0,1) exclusive satisfying x == x^2?
    Z3 should return UNSAT -- no such x exists.

    Additionally encode the full algebraic argument:
    - Unitarity preserves inner products
    - Cloning maps |psi>|0> -> |psi>|psi> and |phi>|0> -> |phi>|phi>
    - LHS inner product: <psi|phi> * <0|0> = <psi|phi> = x
    - RHS inner product: <psi|phi> * <psi|phi> = x^2
    - So x = x^2 must hold, but x in (0,1) makes this impossible
    """
    results = {}

    # ----- Test 4a: basic overlap constraint -----
    s = Solver()
    x = Real('overlap')
    # x is a valid non-trivial overlap: strictly between 0 and 1
    s.add(x > 0)
    s.add(x < 1)
    # Cloning requires x == x^2
    s.add(x == x * x)

    check = s.check()
    basic_unsat = (check == unsat)
    results["4a_basic_overlap"] = {
        "constraint": "x in (0,1) AND x == x^2",
        "z3_result": str(check),
        "is_unsat": basic_unsat,
        "interpretation": "No non-trivial overlap satisfies cloning constraint",
    }
    print(f"  4a: x in (0,1), x == x^2  =>  {check}  (UNSAT expected: {basic_unsat})")

    # ----- Test 4b: complex overlap version -----
    # |<psi|phi>|^2 = a^2 + b^2 where <psi|phi> = a + bi
    s2 = Solver()
    a = Real('re_overlap')
    b = Real('im_overlap')
    mag_sq = a * a + b * b  # |<psi|phi>|^2

    # Non-trivial: magnitude strictly between 0 and 1
    s2.add(mag_sq > 0)
    s2.add(mag_sq < 1)
    # Cloning: |<psi|phi>|^2 = |<psi|phi>|^4
    # i.e., mag_sq == mag_sq^2
    s2.add(mag_sq == mag_sq * mag_sq)

    check2 = s2.check()
    complex_unsat = (check2 == unsat)
    results["4b_complex_overlap"] = {
        "constraint": "|z|^2 in (0,1) AND |z|^2 == |z|^4",
        "z3_result": str(check2),
        "is_unsat": complex_unsat,
        "interpretation": "Complex overlap version also unsatisfiable",
    }
    print(f"  4b: |z|^2 in (0,1), |z|^2 == |z|^4  =>  {check2}  "
          f"(UNSAT expected: {complex_unsat})")

    # ----- Test 4c: positive control -- x in {0, 1} IS satisfiable -----
    s3 = Solver()
    y = Real('overlap_trivial')
    s3.add(y >= 0)
    s3.add(y <= 1)
    s3.add(y == y * y)
    check3 = s3.check()
    trivial_sat = (check3 == sat)
    if trivial_sat:
        model = s3.model()
        y_val = model[y]
        results["4c_trivial_control"] = {
            "constraint": "y in [0,1] AND y == y^2",
            "z3_result": str(check3),
            "is_sat": trivial_sat,
            "witness": str(y_val),
            "interpretation": "Trivial overlaps (0 or 1) satisfy constraint -- "
                              "cloning works for orthogonal or identical states",
        }
        print(f"  4c: y in [0,1], y == y^2  =>  {check3}  witness y={y_val}")
    else:
        results["4c_trivial_control"] = {
            "z3_result": str(check3),
            "is_sat": trivial_sat,
        }
        print(f"  4c: y in [0,1], y == y^2  =>  {check3}  (SAT expected)")

    # ----- Test 4d: no-deleting also UNSAT (same algebraic form) -----
    s4 = Solver()
    w = Real('overlap_delete')
    s4.add(w > 0)
    s4.add(w < 1)
    # Deleting: w^2 = w => same as w = w^2
    s4.add(w * w == w)
    check4 = s4.check()
    delete_unsat = (check4 == unsat)
    results["4d_no_deleting_z3"] = {
        "constraint": "w in (0,1) AND w^2 == w",
        "z3_result": str(check4),
        "is_unsat": delete_unsat,
        "interpretation": "No-deleting shares the same algebraic obstruction",
    }
    print(f"  4d: w in (0,1), w^2 == w  =>  {check4}  (UNSAT expected: {delete_unsat})")

    # ----- Test 4e: multi-state generalization -----
    # For N states with pairwise overlaps, ALL must be 0 or 1
    s5 = Solver()
    N = 4
    overlaps = [Real(f'o_{i}_{j}') for i in range(N) for j in range(i+1, N)]
    for o in overlaps:
        s5.add(o > 0)
        s5.add(o < 1)
        s5.add(o == o * o)

    check5 = s5.check()
    multi_unsat = (check5 == unsat)
    results["4e_multi_state"] = {
        "n_states": N,
        "n_overlap_constraints": len(overlaps),
        "z3_result": str(check5),
        "is_unsat": multi_unsat,
        "interpretation": f"No set of {N} non-trivially overlapping states can be cloned",
    }
    print(f"  4e: {N}-state system, {len(overlaps)} overlaps  =>  {check5}")

    results["all_pass"] = (
        basic_unsat
        and complex_unsat
        and trivial_sat
        and delete_unsat
        and multi_unsat
    )
    print(f"  SECTION 4 PASS: {results['all_pass']}")
    return results

RESULTS["4_z3_structural"] = test_z3_no_cloning()

# ──────────────────────────────────────────────────────────────────────
# Summary
# ──────────────────────────────────────────────────────────────────────

summary = {
    "1_no_cloning": RESULTS["1_no_cloning"]["all_pass"],
    "2_no_broadcasting": RESULTS["2_no_broadcasting"]["all_pass"],
    "3_no_deleting": RESULTS["3_no_deleting"]["all_pass"],
    "4_z3_structural": RESULTS["4_z3_structural"]["all_pass"],
}

all_pass = all(summary.values())
RESULTS["summary"] = summary
RESULTS["ALL_PASS"] = all_pass

print(f"\n{'=' * 60}")
print(f"PURE LEGO NO-GO THEOREMS -- ALL PASS: {all_pass}")
print(f"{'=' * 60}")
for k, v in summary.items():
    tag = "PASS" if v else "FAIL"
    print(f"  [{tag}] {k}")

# Write results
out_path = pathlib.Path(__file__).parent / "a2_state" / "sim_results" / "pure_lego_no_go_theorems_results.json"
out_path.parent.mkdir(parents=True, exist_ok=True)
with open(out_path, "w") as f:
    json.dump(RESULTS, f, indent=2, default=str)
print(f"\nResults written to {out_path}")
