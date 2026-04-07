#!/usr/bin/env python3
"""
PURE LEGO: Projective Z-Measurement on a Qubit
================================================
Foundational building block.  Pure math only -- numpy.
No engine imports.  Every operation verified against theory.

Sections
--------
1. POVM construction: M0 = |0><0|, M1 = |1><1|
2. Born rule: p_k = Tr(M_k rho)
3. Post-measurement collapse: rho -> M_k rho M_k / Tr(M_k rho)
4. Idempotency: measure-then-measure gives same outcome
5. Z-measurement + forget outcome = Z-dephasing channel
6. Negative: non-Hermitian POVM, incomplete POVM
7. Boundary: maximally mixed state, pure eigenstates
"""

import json, os, time, traceback
import numpy as np

np.random.seed(42)
EPS = 1e-12

# =====================================================================
# TOOL MANIFEST
# =====================================================================

TOOL_MANIFEST = {
    "pytorch":    {"tried": False, "used": False, "reason": "classical baseline -- numpy only"},
    "pyg":        {"tried": False, "used": False, "reason": "classical baseline -- numpy only"},
    "z3":         {"tried": False, "used": False, "reason": "not needed for this baseline"},
    "cvc5":       {"tried": False, "used": False, "reason": "not needed for this baseline"},
    "sympy":      {"tried": False, "used": False, "reason": "not needed for this baseline"},
    "clifford":   {"tried": False, "used": False, "reason": "not needed for this baseline"},
    "geomstats":  {"tried": False, "used": False, "reason": "not needed for this baseline"},
    "e3nn":       {"tried": False, "used": False, "reason": "not needed for this baseline"},
    "rustworkx":  {"tried": False, "used": False, "reason": "not needed for this baseline"},
    "xgi":        {"tried": False, "used": False, "reason": "not needed for this baseline"},
    "toponetx":   {"tried": False, "used": False, "reason": "not needed for this baseline"},
    "gudhi":      {"tried": False, "used": False, "reason": "not needed for this baseline"},
}

# ──────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────

def ket(v):
    """Column vector from list."""
    return np.array(v, dtype=complex).reshape(-1, 1)

def dm(v):
    """Density matrix from state vector."""
    k = ket(v)
    return k @ k.conj().T

def is_hermitian(M, tol=1e-10):
    return np.allclose(M, M.conj().T, atol=tol)

def is_psd(M, tol=1e-10):
    evals = np.linalg.eigvalsh(M)
    return np.all(evals > -tol)

def trace_dist(rho, sigma):
    diff = rho - sigma
    evals = np.linalg.eigvalsh(diff)
    return 0.5 * np.sum(np.abs(evals))

# ──────────────────────────────────────────────────────────────────────
# Core: Z-measurement POVM
# ──────────────────────────────────────────────────────────────────────

# Computational basis projectors
KET_0 = ket([1, 0])
KET_1 = ket([0, 1])
M0 = KET_0 @ KET_0.conj().T   # |0><0|
M1 = KET_1 @ KET_1.conj().T   # |1><1|

def z_born_probability(rho, outcome):
    """p_k = Tr(M_k rho)"""
    M = M0 if outcome == 0 else M1
    return np.real(np.trace(M @ rho))

def z_post_measurement(rho, outcome):
    """rho -> M_k rho M_k / Tr(M_k rho)"""
    M = M0 if outcome == 0 else M1
    numerator = M @ rho @ M
    prob = np.real(np.trace(numerator))
    if prob < EPS:
        return None  # outcome has zero probability
    return numerator / prob

def z_dephasing_channel(rho):
    """Z-dephasing: sum_k M_k rho M_k (forget which outcome)."""
    return M0 @ rho @ M0 + M1 @ rho @ M1

# ──────────────────────────────────────────────────────────────────────
# Common test states
# ──────────────────────────────────────────────────────────────────────

RHO_0 = dm([1, 0])                               # |0>
RHO_1 = dm([0, 1])                               # |1>
RHO_PLUS = dm([1/np.sqrt(2), 1/np.sqrt(2)])      # |+>
RHO_MINUS = dm([1/np.sqrt(2), -1/np.sqrt(2)])    # |->
RHO_MIXED = 0.5 * np.eye(2, dtype=complex)       # I/2

# =====================================================================
# POSITIVE TESTS
# =====================================================================

def run_positive_tests():
    results = {}
    t0 = time.time()

    # --- Test 1: POVM validity (Hermitian, PSD, complete) ---
    povm_hermitian = is_hermitian(M0) and is_hermitian(M1)
    povm_psd = is_psd(M0) and is_psd(M1)
    povm_complete = np.allclose(M0 + M1, np.eye(2))
    results["povm_valid"] = {
        "hermitian": bool(povm_hermitian),
        "psd": bool(povm_psd),
        "complete": bool(povm_complete),
        "pass": bool(povm_hermitian and povm_psd and povm_complete),
    }

    # --- Test 2: Born rule on |+> ---
    p0_plus = z_born_probability(RHO_PLUS, 0)
    p1_plus = z_born_probability(RHO_PLUS, 1)
    results["born_rule_plus"] = {
        "p0": float(p0_plus),
        "p1": float(p1_plus),
        "p0_expected": 0.5,
        "p1_expected": 0.5,
        "sum": float(p0_plus + p1_plus),
        "pass": bool(np.isclose(p0_plus, 0.5) and np.isclose(p1_plus, 0.5)),
    }

    # --- Test 3: Born rule on |0> (deterministic) ---
    p0_zero = z_born_probability(RHO_0, 0)
    p1_zero = z_born_probability(RHO_0, 1)
    results["born_rule_zero"] = {
        "p0": float(p0_zero),
        "p1": float(p1_zero),
        "pass": bool(np.isclose(p0_zero, 1.0) and np.isclose(p1_zero, 0.0)),
    }

    # --- Test 4: Post-measurement collapse from |+> ---
    post_0 = z_post_measurement(RHO_PLUS, 0)
    post_1 = z_post_measurement(RHO_PLUS, 1)
    dist_0 = trace_dist(post_0, RHO_0)
    dist_1 = trace_dist(post_1, RHO_1)
    results["collapse_plus"] = {
        "post_0_is_ket0": bool(np.isclose(dist_0, 0.0)),
        "post_1_is_ket1": bool(np.isclose(dist_1, 0.0)),
        "trace_dist_0": float(dist_0),
        "trace_dist_1": float(dist_1),
        "pass": bool(np.isclose(dist_0, 0.0) and np.isclose(dist_1, 0.0)),
    }

    # --- Test 5: Idempotency (measure twice = same result) ---
    post_0_again = z_post_measurement(post_0, 0)
    idempotent_dist = trace_dist(post_0, post_0_again)
    # After outcome 0, probability of outcome 0 should be 1
    p0_after_0 = z_born_probability(post_0, 0)
    p1_after_0 = z_born_probability(post_0, 1)
    results["idempotency"] = {
        "post_measure_unchanged": bool(np.isclose(idempotent_dist, 0.0)),
        "p0_after_outcome0": float(p0_after_0),
        "p1_after_outcome0": float(p1_after_0),
        "pass": bool(
            np.isclose(idempotent_dist, 0.0)
            and np.isclose(p0_after_0, 1.0)
            and np.isclose(p1_after_0, 0.0)
        ),
    }

    # --- Test 6: z_measurement + forget = z_dephasing ---
    # For arbitrary state, sum_k M_k rho M_k should kill off-diagonals
    test_states = {
        "plus": RHO_PLUS,
        "minus": RHO_MINUS,
        "zero": RHO_0,
        "one": RHO_1,
        "mixed": RHO_MIXED,
    }
    dephasing_pass = True
    dephasing_detail = {}
    for name, rho in test_states.items():
        dephased = z_dephasing_channel(rho)
        # Off-diagonals should be zero
        off_diag_zero = np.isclose(dephased[0, 1], 0.0) and np.isclose(dephased[1, 0], 0.0)
        # Diagonals should be preserved
        diag_preserved = np.isclose(dephased[0, 0], rho[0, 0]) and np.isclose(dephased[1, 1], rho[1, 1])
        ok = bool(off_diag_zero and diag_preserved)
        dephasing_detail[name] = {
            "off_diag_killed": bool(off_diag_zero),
            "diag_preserved": bool(diag_preserved),
            "pass": ok,
        }
        if not ok:
            dephasing_pass = False
    results["z_measurement_is_dephasing"] = {
        "detail": dephasing_detail,
        "pass": dephasing_pass,
    }

    # --- Test 7: Born rule on |1> (deterministic, outcome 1) ---
    p0_one = z_born_probability(RHO_1, 0)
    p1_one = z_born_probability(RHO_1, 1)
    results["born_rule_one"] = {
        "p0": float(p0_one),
        "p1": float(p1_one),
        "pass": bool(np.isclose(p0_one, 0.0) and np.isclose(p1_one, 1.0)),
    }

    # --- Test 8: Born rule on |-> ---
    p0_minus = z_born_probability(RHO_MINUS, 0)
    p1_minus = z_born_probability(RHO_MINUS, 1)
    results["born_rule_minus"] = {
        "p0": float(p0_minus),
        "p1": float(p1_minus),
        "pass": bool(np.isclose(p0_minus, 0.5) and np.isclose(p1_minus, 0.5)),
    }

    results["elapsed_s"] = time.time() - t0
    return results

# =====================================================================
# NEGATIVE TESTS
# =====================================================================

def run_negative_tests():
    results = {}
    t0 = time.time()

    # --- Neg 1: Non-Hermitian "POVM" element ---
    bad_M0 = np.array([[1, 1j], [0, 0]], dtype=complex)  # not Hermitian
    bad_M1 = np.eye(2, dtype=complex) - bad_M0
    results["non_hermitian_povm"] = {
        "M0_hermitian": bool(is_hermitian(bad_M0)),
        "M1_hermitian": bool(is_hermitian(bad_M1)),
        "pass": bool(not is_hermitian(bad_M0)),  # should detect non-Hermitian
    }

    # --- Neg 2: Incomplete POVM (doesn't sum to I) ---
    incomplete_M0 = 0.5 * M0  # scale down
    incomplete_M1 = 0.5 * M1
    completeness = np.allclose(incomplete_M0 + incomplete_M1, np.eye(2))
    total_prob = float(np.real(
        np.trace(incomplete_M0 @ RHO_PLUS) + np.trace(incomplete_M1 @ RHO_PLUS)
    ))
    results["incomplete_povm"] = {
        "sums_to_identity": bool(completeness),
        "total_probability": total_prob,
        "total_prob_expected": 0.5,  # should NOT be 1
        "pass": bool(not completeness and not np.isclose(total_prob, 1.0)),
    }

    # --- Neg 3: Non-PSD "POVM" element ---
    bad_psd = np.array([[1, 0], [0, -0.5]], dtype=complex)  # negative eigenvalue
    results["non_psd_povm"] = {
        "is_psd": bool(is_psd(bad_psd)),
        "min_eigenvalue": float(np.min(np.linalg.eigvalsh(bad_psd))),
        "pass": bool(not is_psd(bad_psd)),
    }

    # --- Neg 4: Zero-probability outcome post-measurement returns None ---
    post_impossible = z_post_measurement(RHO_0, 1)  # |0> measured, outcome 1
    results["zero_prob_collapse"] = {
        "returns_none": post_impossible is None,
        "pass": post_impossible is None,
    }

    results["elapsed_s"] = time.time() - t0
    return results

# =====================================================================
# BOUNDARY TESTS
# =====================================================================

def run_boundary_tests():
    results = {}
    t0 = time.time()

    # --- Boundary 1: Maximally mixed state ---
    p0_mixed = z_born_probability(RHO_MIXED, 0)
    p1_mixed = z_born_probability(RHO_MIXED, 1)
    post_mixed_0 = z_post_measurement(RHO_MIXED, 0)
    post_mixed_1 = z_post_measurement(RHO_MIXED, 1)
    results["maximally_mixed"] = {
        "p0": float(p0_mixed),
        "p1": float(p1_mixed),
        "equal_probs": bool(np.isclose(p0_mixed, p1_mixed)),
        "post0_is_ket0": bool(np.isclose(trace_dist(post_mixed_0, RHO_0), 0.0)),
        "post1_is_ket1": bool(np.isclose(trace_dist(post_mixed_1, RHO_1), 0.0)),
        "pass": bool(
            np.isclose(p0_mixed, 0.5)
            and np.isclose(p1_mixed, 0.5)
            and np.isclose(trace_dist(post_mixed_0, RHO_0), 0.0)
            and np.isclose(trace_dist(post_mixed_1, RHO_1), 0.0)
        ),
    }

    # --- Boundary 2: Pure eigenstate |0> (deterministic) ---
    p0_eigen = z_born_probability(RHO_0, 0)
    post_eigen = z_post_measurement(RHO_0, 0)
    results["pure_eigenstate_0"] = {
        "p0": float(p0_eigen),
        "unchanged_after_measurement": bool(np.isclose(trace_dist(post_eigen, RHO_0), 0.0)),
        "pass": bool(np.isclose(p0_eigen, 1.0) and np.isclose(trace_dist(post_eigen, RHO_0), 0.0)),
    }

    # --- Boundary 3: Pure eigenstate |1> (deterministic) ---
    p1_eigen = z_born_probability(RHO_1, 1)
    post_eigen1 = z_post_measurement(RHO_1, 1)
    results["pure_eigenstate_1"] = {
        "p1": float(p1_eigen),
        "unchanged_after_measurement": bool(np.isclose(trace_dist(post_eigen1, RHO_1), 0.0)),
        "pass": bool(np.isclose(p1_eigen, 1.0) and np.isclose(trace_dist(post_eigen1, RHO_1), 0.0)),
    }

    # --- Boundary 4: State approaching eigenstate (theta -> 0) ---
    thetas = [0.001, 0.01, 0.1]
    approach_data = []
    for theta in thetas:
        state = dm([np.cos(theta/2), np.sin(theta/2)])
        p0 = z_born_probability(state, 0)
        approach_data.append({"theta": theta, "p0": float(p0)})
    # p0 should approach 1 as theta -> 0
    monotonic = all(
        approach_data[i]["p0"] >= approach_data[i+1]["p0"]
        for i in range(len(approach_data) - 1)
    )
    results["approaching_eigenstate"] = {
        "data": approach_data,
        "monotonic_toward_1": monotonic,
        "pass": bool(monotonic and approach_data[0]["p0"] > 0.999),
    }

    # --- Boundary 5: Dephasing is idempotent ---
    dephased_once = z_dephasing_channel(RHO_PLUS)
    dephased_twice = z_dephasing_channel(dephased_once)
    idempotent = np.isclose(trace_dist(dephased_once, dephased_twice), 0.0)
    results["dephasing_idempotent"] = {
        "trace_dist": float(trace_dist(dephased_once, dephased_twice)),
        "pass": bool(idempotent),
    }

    results["elapsed_s"] = time.time() - t0
    return results

# =====================================================================
# MAIN
# =====================================================================

if __name__ == "__main__":
    results = {
        "name": "pure_lego_z_measurement",
        "description": "Projective Z-measurement: POVM, Born rule, collapse, idempotency, dephasing link",
        "tool_manifest": TOOL_MANIFEST,
        "positive": run_positive_tests(),
        "negative": run_negative_tests(),
        "boundary": run_boundary_tests(),
        "classification": "classical_baseline",
    }

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "z_measurement_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out_path}")

    # Summary
    all_pass = True
    for section in ["positive", "negative", "boundary"]:
        for k, v in results[section].items():
            if isinstance(v, dict) and "pass" in v:
                status = "PASS" if v["pass"] else "FAIL"
                if not v["pass"]:
                    all_pass = False
                print(f"  [{section}] {k}: {status}")
    print(f"\nOverall: {'ALL PASS' if all_pass else 'FAILURES DETECTED'}")
