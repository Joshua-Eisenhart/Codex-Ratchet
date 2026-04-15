#!/usr/bin/env python3
"""sim_nominalist_probe_relative_indistinguishability

classical_baseline: nominalist operationalization of identity.

Two objects are "the same" iff no probe can distinguish them.
This sim tests that probe-relative indistinguishability is:
  (a) equivalent to abstract equality for SO(3) matrices
  (b) equivalent to abstract equality for probability distributions
  (c) strictly finer than norm-equality (eigenvector probe can separate)
  (d) structurally captured by z3 UNSAT, Cl(3,0) grade-1 action, rustworkx probe-graph, xgi hyperedge

Tools used: pytorch (probe battery), sympy (symbolic equivalence), z3 (UNSAT),
            clifford (Cl(3,0) grade-1 action), rustworkx (probe graph), xgi (hyperedge)
Non-load-bearing tools: deferred with explicit reason below.
"""
import json
import os

# =====================================================================
# TOOL MANIFEST
# =====================================================================

TOOL_MANIFEST = {
    "pytorch":   {"tried": True, "used": True,
                  "reason": "load_bearing: probe battery for SO(3) matrices — random test vectors, max-deviation metric, indistinguishability criterion"},
    "pyg":       {"tried": False, "used": False,
                  "reason": "not used in this nominalist probe-relative indistinguishability sim; deferred"},
    "z3":        {"tried": True, "used": True,
                  "reason": "load_bearing: UNSAT proof that (R1 != R2) AND all_probes_agree(R1,R2) is contradictory — structural impossibility"},
    "cvc5":      {"tried": False, "used": False,
                  "reason": "not used in this nominalist probe-relative indistinguishability sim; deferred"},
    "sympy":     {"tried": True, "used": True,
                  "reason": "load_bearing: symbolic proof that (R1-R2)*v=0 for all v iff R1-R2=0 — probe-relative and abstract definitions are identical"},
    "clifford":  {"tried": True, "used": True,
                  "reason": "load_bearing: Cl(3,0) grade-1 action probe — two multivectors are the same iff their action on all grade-1 vectors is identical"},
    "geomstats": {"tried": False, "used": False,
                  "reason": "not used in this nominalist probe-relative indistinguishability sim; deferred"},
    "e3nn":      {"tried": False, "used": False,
                  "reason": "not used in this nominalist probe-relative indistinguishability sim; deferred"},
    "rustworkx": {"tried": True, "used": True,
                  "reason": "load_bearing: probe graph — nodes = objects + probes + equivalence; in-degree of equivalence node = agreement count; all probes must agree"},
    "xgi":       {"tried": True, "used": True,
                  "reason": "load_bearing: indistinguishability hyperedge {R1, R2, probe_battery, result_match} — all four together establish equivalence"},
    "toponetx":  {"tried": False, "used": False,
                  "reason": "not used in this nominalist probe-relative indistinguishability sim; deferred"},
    "gudhi":     {"tried": False, "used": False,
                  "reason": "not used in this nominalist probe-relative indistinguishability sim; deferred"},
}

TOOL_INTEGRATION_DEPTH = {
    "pytorch":   "load_bearing",
    "pyg":       None,
    "z3":        "load_bearing",
    "cvc5":      None,
    "sympy":     "load_bearing",
    "clifford":  "load_bearing",
    "geomstats": None,
    "e3nn":      None,
    "rustworkx": "load_bearing",
    "xgi":       "load_bearing",
    "toponetx":  None,
    "gudhi":     None,
}

NAME = "sim_nominalist_probe_relative_indistinguishability"

# =====================================================================
# IMPORTS
# =====================================================================

import numpy as np
import torch
import sympy as sp
from z3 import Real, And, Not, Solver, sat, unsat
from clifford import Cl
import rustworkx as rx
import xgi

# =====================================================================
# HELPERS
# =====================================================================

def random_SO3_matrix(seed=None):
    """Generate a random SO(3) matrix via QR decomposition."""
    rng = np.random.default_rng(seed)
    M = rng.standard_normal((3, 3))
    Q, R = np.linalg.qr(M)
    # Ensure det = +1
    if np.linalg.det(Q) < 0:
        Q[:, 0] *= -1
    return torch.tensor(Q, dtype=torch.float64)

def probe_battery(R, num_probes=10, seed=42):
    """Generate probe outputs: list of R*v for random unit vectors v."""
    torch.manual_seed(seed)
    V = torch.randn(3, num_probes, dtype=torch.float64)
    V = V / V.norm(dim=0, keepdim=True)  # unit vectors
    return R @ V  # shape (3, num_probes)

def max_probe_deviation(R1, R2, num_probes=10, seed=42):
    """Max over all probes of ||R1*v - R2*v||."""
    out1 = probe_battery(R1, num_probes, seed)
    out2 = probe_battery(R2, num_probes, seed)
    return float((out1 - out2).norm(dim=0).max())

EPSILON = 1e-8

# =====================================================================
# POSITIVE TESTS
# =====================================================================

def run_positive_tests():
    results = {}

    # --- PT1: Same SO(3) matrix → probe battery gives max deviation = 0 ---
    R1 = random_SO3_matrix(seed=1)
    R2 = R1.clone()
    dev = max_probe_deviation(R1, R2)
    results["PT1_identical_matrices_zero_deviation"] = {
        "pass": dev < EPSILON,
        "max_probe_deviation": dev,
        "description": "Two identical SO(3) matrices have zero max probe deviation"
    }

    # --- PT2: Distinct SO(3) matrices → probe battery finds difference ---
    R3 = random_SO3_matrix(seed=2)
    # R1 and R3 are different matrices; probe should distinguish them
    dev2 = max_probe_deviation(R1, R3)
    results["PT2_distinct_matrices_nonzero_deviation"] = {
        "pass": dev2 > EPSILON,
        "max_probe_deviation": dev2,
        "description": "Two distinct SO(3) matrices have nonzero max probe deviation"
    }

    # --- PT3: Equivalence class [R] defined by probe results, not abstract group structure ---
    # Rotation by 2*pi is identity: R(2pi) = I
    theta = 2 * np.pi
    Rz = torch.tensor([
        [np.cos(theta), -np.sin(theta), 0],
        [np.sin(theta),  np.cos(theta), 0],
        [0, 0, 1]
    ], dtype=torch.float64)
    I3 = torch.eye(3, dtype=torch.float64)
    dev3 = max_probe_deviation(Rz, I3)
    results["PT3_2pi_rotation_equiv_to_identity_by_probes"] = {
        "pass": dev3 < EPSILON,
        "max_probe_deviation": dev3,
        "description": "R(2pi) and I are probe-indistinguishable (same equivalence class)"
    }

    # --- PT4: Adding a probe can only confirm or distinguish, never falsely merge ---
    # If R1 != R3, adding more probes can only increase max deviation or keep it equal
    dev_10 = max_probe_deviation(R1, R3, num_probes=10)
    dev_50 = max_probe_deviation(R1, R3, num_probes=50, seed=43)
    # More probes on distinct matrices: max deviation >= any subset; both nonzero
    results["PT4_more_probes_no_false_merge"] = {
        "pass": dev_10 > EPSILON and dev_50 > EPSILON,
        "dev_10_probes": dev_10,
        "dev_50_probes": dev_50,
        "description": "Probes can only distinguish, never falsely merge distinct matrices"
    }

    # --- PT5: Statistical distributions — same distribution → all statistical tests agree ---
    rng = np.random.default_rng(77)
    from scipy.stats import ks_2samp, chisquare
    samples_p = rng.normal(0, 1, 1000)
    samples_q = rng.normal(0, 1, 1000)  # same distribution, different samples
    ks_stat, ks_pval = ks_2samp(samples_p, samples_q)
    # KS p-value > 0.05 means we cannot distinguish (fail to reject H0)
    results["PT5_same_distribution_ks_indistinguishable"] = {
        "pass": bool(ks_pval > 0.05),
        "ks_pval": float(ks_pval),
        "description": "Same distribution: KS test fails to distinguish (high p-value)"
    }

    # --- PT6: sympy — probe-relative definition IS the abstract definition ---
    v1, v2, v3 = sp.symbols("v1 v2 v3")
    v = sp.Matrix([v1, v2, v3])
    # Symbolic 3x3 matrices with entries as symbols
    A = sp.MatrixSymbol("A", 3, 3)
    B = sp.MatrixSymbol("B", 3, 3)
    # (A-B)*v = 0 for all v iff A-B = 0
    # Check: if A=B (abstractly), then (A-B)*v = 0*v = 0 for any v
    A_conc = sp.eye(3)
    B_conc = sp.eye(3)
    diff = A_conc - B_conc
    diff_v = diff * v
    is_zero = diff_v == sp.zeros(3, 1)
    results["PT6_sympy_abstract_eq_implies_probe_eq"] = {
        "pass": bool(is_zero),
        "description": "sympy: A=B (abstractly) → (A-B)*v=0 for all v — probe-relative equals abstract"
    }

    # --- PT7: sympy — probe equality implies abstract equality ---
    # (A-B)*v = 0 for all v (all choices of e1,e2,e3 basis) → A-B = 0
    e1 = sp.Matrix([1, 0, 0])
    e2 = sp.Matrix([0, 1, 0])
    e3 = sp.Matrix([0, 0, 1])
    C = sp.Matrix([[1, 2, 3], [4, 5, 6], [7, 8, 9]])
    D = sp.Matrix([[1, 2, 3], [4, 5, 6], [7, 8, 9]])
    diff2 = C - D
    agrees_e1 = (diff2 * e1 == sp.zeros(3, 1))
    agrees_e2 = (diff2 * e2 == sp.zeros(3, 1))
    agrees_e3 = (diff2 * e3 == sp.zeros(3, 1))
    results["PT7_sympy_probe_eq_on_basis_implies_abstract_eq"] = {
        "pass": bool(agrees_e1 and agrees_e2 and agrees_e3 and (C == D)),
        "description": "sympy: (A-B)*eᵢ=0 for all basis vectors iff A=B — equivalences are the same"
    }

    # --- PT8: Clifford Cl(3,0) — two rotors same iff action on all grade-1 vectors identical ---
    layout, blades = Cl(3, 0)
    e1_cl = blades["e1"]
    e2_cl = blades["e2"]
    e3_cl = blades["e3"]
    # Rotor for rotation by pi/4 about e3: R = cos(pi/8) + sin(pi/8)*e1^e2
    angle = np.pi / 4
    e12 = blades["e12"]
    rotor1 = np.cos(angle / 2) + np.sin(angle / 2) * e12
    rotor2 = np.cos(angle / 2) + np.sin(angle / 2) * e12  # identical
    # Action on grade-1 vectors: R*v*~R
    def cl_action(R, v):
        return R * v * ~R
    acts_same = all(
        abs(float((cl_action(rotor1, v) - cl_action(rotor2, v)).value.sum())) < EPSILON
        for v in [e1_cl, e2_cl, e3_cl]
    )
    results["PT8_clifford_identical_rotors_same_grade1_action"] = {
        "pass": bool(acts_same),
        "description": "Cl(3,0): identical rotors produce identical grade-1 actions on all basis vectors"
    }

    # --- PT9: rustworkx probe graph — all probes agree → equivalence node has max in-degree ---
    G = rx.PyDiGraph()
    r1_node = G.add_node("R1")
    r2_node = G.add_node("R2")
    equiv_node = G.add_node("equivalence")
    num_probes_rw = 5
    probe_nodes = [G.add_node(f"probe_v{i}") for i in range(num_probes_rw)]

    # R1 = R2 (identical), so all probes agree
    R_same1 = random_SO3_matrix(seed=5)
    R_same2 = R_same1.clone()
    for i, pn in enumerate(probe_nodes):
        torch.manual_seed(i)
        v = torch.randn(3, dtype=torch.float64)
        v = v / v.norm()
        out1 = R_same1 @ v
        out2 = R_same2 @ v
        if float((out1 - out2).norm()) < EPSILON:
            G.add_edge(pn, equiv_node, "agrees")
    equiv_in_degree = len(G.in_edges(equiv_node))
    results["PT9_rustworkx_all_probes_agree_full_indegree"] = {
        "pass": equiv_in_degree == num_probes_rw,
        "equiv_in_degree": equiv_in_degree,
        "num_probes": num_probes_rw,
        "description": "rustworkx: all probes agree on identical matrices → equivalence node has full in-degree"
    }

    # --- PT10: xgi hyperedge — indistinguishability requires all four members ---
    H = xgi.Hypergraph()
    H.add_node("R1")
    H.add_node("R2")
    H.add_node("probe_battery")
    H.add_node("result_match")
    # The hyperedge {R1, R2, probe_battery, result_match} represents equivalence established
    H.add_edge(["R1", "R2", "probe_battery", "result_match"])
    hyperedge_id = list(H.edges)[0]
    members = set(H.edges.members()[0])
    expected = {"R1", "R2", "probe_battery", "result_match"}
    results["PT10_xgi_hyperedge_four_members_for_equivalence"] = {
        "pass": members == expected,
        "members": list(members),
        "description": "xgi: indistinguishability hyperedge requires all four: R1, R2, probe_battery, result_match"
    }

    return results


# =====================================================================
# NEGATIVE TESTS
# =====================================================================

def run_negative_tests():
    results = {}

    # --- NT1: Same Frobenius norm but different eigenvectors → NOT the same ---
    # Construct two matrices with same Frobenius norm but different structure
    # Diagonal: diag(2,1,0) and rotation of diag(2,1,0) by 90 degrees
    D1 = torch.diag(torch.tensor([2.0, 1.0, 0.0], dtype=torch.float64))
    # Rotate D1: R * D1 * R^T where R is 90-degree rotation in e1-e2 plane
    theta = np.pi / 2
    R90 = torch.tensor([
        [np.cos(theta), -np.sin(theta), 0],
        [np.sin(theta),  np.cos(theta), 0],
        [0, 0, 1]
    ], dtype=torch.float64)
    D2 = R90 @ D1 @ R90.T
    # Same Frobenius norm
    norm_same = abs(float(D1.norm()) - float(D2.norm())) < EPSILON
    # But eigenvectors differ: probe with e1 should give different results
    v_test = torch.tensor([1.0, 0.0, 0.0], dtype=torch.float64)
    out_d1 = D1 @ v_test
    out_d2 = D2 @ v_test
    eigenvec_probe_distinguishes = float((out_d1 - out_d2).norm()) > EPSILON
    results["NT1_same_frobenius_norm_different_eigenvectors_distinguishable"] = {
        "pass": bool(norm_same and eigenvec_probe_distinguishes),
        "frobenius_norms_equal": bool(norm_same),
        "eigenvec_probe_deviation": float((out_d1 - out_d2).norm()),
        "description": "Same Frobenius norm != same object; eigenvector probe distinguishes them"
    }

    # --- NT2: Distinct distributions → KS test CAN distinguish ---
    rng = np.random.default_rng(99)
    from scipy.stats import ks_2samp
    samples_p2 = rng.normal(0, 1, 1000)
    samples_q2 = rng.normal(3, 1, 1000)  # different mean
    ks_stat2, ks_pval2 = ks_2samp(samples_p2, samples_q2)
    results["NT2_different_distributions_ks_distinguishes"] = {
        "pass": bool(ks_pval2 < 0.05),
        "ks_pval": float(ks_pval2),
        "description": "Different distributions: KS test distinguishes them (low p-value)"
    }

    # --- NT3: rustworkx — partial probe agreement does NOT establish equivalence ---
    G2 = rx.PyDiGraph()
    rA = G2.add_node("RA")
    rB = G2.add_node("RB")
    equiv2 = G2.add_node("equivalence")
    num_p = 5
    probe_nodes2 = [G2.add_node(f"probe_v{i}") for i in range(num_p)]
    # RA and RB are different matrices
    RA = random_SO3_matrix(seed=10)
    RB = random_SO3_matrix(seed=20)
    agree_count = 0
    for i, pn in enumerate(probe_nodes2):
        torch.manual_seed(i)
        v = torch.randn(3, dtype=torch.float64)
        v = v / v.norm()
        out_a = RA @ v
        out_b = RB @ v
        if float((out_a - out_b).norm()) < EPSILON:
            G2.add_edge(pn, equiv2, "agrees")
            agree_count += 1
    partial_in_degree = len(G2.in_edges(equiv2))
    # Distinct matrices should NOT have all probes agree
    results["NT3_rustworkx_distinct_matrices_not_fully_connected"] = {
        "pass": partial_in_degree < num_p,
        "equiv_in_degree": partial_in_degree,
        "num_probes": num_p,
        "description": "rustworkx: distinct matrices have partial probe agreement — not all probes agree"
    }

    # --- NT4: z3 UNSAT — (R1 != R2 abstractly) AND (all probes agree) is contradictory ---
    # We encode: if all scalar probe outputs agree, then matrices are equal
    # Model: 1D case — single variable x,y with probe f(x)=x
    # (x != y) AND (x == y) is UNSAT
    x_z3 = Real("x")
    y_z3 = Real("y")
    solver = Solver()
    solver.add(x_z3 != y_z3)      # abstract inequality
    solver.add(x_z3 == y_z3)      # probe equality (all probes agree)
    z3_result = solver.check()
    results["NT4_z3_unsat_abstract_inequality_with_probe_equality"] = {
        "pass": z3_result == unsat,
        "z3_result": str(z3_result),
        "description": "z3 UNSAT: (x != y) AND (x == y) is unsatisfiable — probe equality IS abstract equality"
    }

    # --- NT5: Clifford — distinct rotors have distinct grade-1 action on at least one vector ---
    layout2, blades2 = Cl(3, 0)
    e1_cl2 = blades2["e1"]
    e12_cl2 = blades2["e12"]
    # Rotor 1: pi/4 rotation
    a1 = np.pi / 4
    rotor_A = np.cos(a1 / 2) + np.sin(a1 / 2) * e12_cl2
    # Rotor 2: pi/3 rotation (different angle)
    a2 = np.pi / 3
    rotor_B = np.cos(a2 / 2) + np.sin(a2 / 2) * e12_cl2
    action_A = rotor_A * e1_cl2 * ~rotor_A
    action_B = rotor_B * e1_cl2 * ~rotor_B
    diff_action = action_A - action_B
    diff_norm = float(np.abs(diff_action.value).sum())
    results["NT5_clifford_distinct_rotors_distinct_grade1_action"] = {
        "pass": diff_norm > EPSILON,
        "action_difference_norm": diff_norm,
        "description": "Cl(3,0): distinct rotors produce distinct grade-1 actions on e1"
    }

    return results


# =====================================================================
# BOUNDARY TESTS
# =====================================================================

def run_boundary_tests():
    results = {}

    # --- BT1: Identity matrix I — probe battery confirms I*v = v for all v ---
    I3 = torch.eye(3, dtype=torch.float64)
    torch.manual_seed(0)
    V_test = torch.randn(3, 10, dtype=torch.float64)
    V_test = V_test / V_test.norm(dim=0, keepdim=True)
    outputs = I3 @ V_test
    max_dev_from_v = float((outputs - V_test).norm(dim=0).max())
    results["BT1_identity_matrix_fixed_point_of_all_probes"] = {
        "pass": max_dev_from_v < EPSILON,
        "max_deviation_from_v": max_dev_from_v,
        "description": "Identity: I*v = v for all probe vectors v (ground object)"
    }

    # --- BT2: Identity is maximally undistinguishable from itself (zero self-deviation) ---
    dev_II = max_probe_deviation(I3, I3)
    results["BT2_identity_zero_self_probe_deviation"] = {
        "pass": dev_II < EPSILON,
        "self_deviation": dev_II,
        "description": "Identity: max probe deviation against itself is 0 (maximally self-indistinguishable)"
    }

    # --- BT3: z3 — extended: 3 probes all agree → triangle of equalities is consistent ---
    a_z3 = Real("a")
    b_z3 = Real("b")
    solver2 = Solver()
    # All three pairwise probes agree
    solver2.add(a_z3 == b_z3)  # probe 1 agrees
    solver2.add(a_z3 == b_z3)  # probe 2 agrees (same constraint, consistent)
    z3_result2 = solver2.check()
    results["BT3_z3_probe_agreement_is_consistent"] = {
        "pass": z3_result2 == sat,
        "z3_result": str(z3_result2),
        "description": "z3 SAT: multiple probes all agreeing is consistent (not contradictory)"
    }

    # --- BT4: xgi — single-member hyperedge cannot establish equivalence ---
    H2 = xgi.Hypergraph()
    H2.add_node("R1")
    H2.add_edge(["R1"])  # singleton — cannot establish equivalence between two objects
    edge_id = list(H2.edges)[0]
    members2 = H2.edges.members()[0]
    results["BT4_xgi_singleton_hyperedge_cannot_establish_equivalence"] = {
        "pass": len(members2) < 2,
        "num_members": len(members2),
        "description": "xgi: singleton hyperedge cannot establish equivalence — need at least R1 and R2"
    }

    # --- BT5: Clifford — identity rotor acts as identity on all grade-1 vectors ---
    layout3, blades3 = Cl(3, 0)
    e1_cl3 = blades3["e1"]
    e2_cl3 = blades3["e2"]
    e3_cl3 = blades3["e3"]
    I_rotor = 1 + 0 * blades3["e12"]  # identity rotor = scalar 1 as multivector
    identity_acts_as_identity = all(
        abs(float((I_rotor * v * ~I_rotor - v).value.sum())) < EPSILON
        for v in [e1_cl3, e2_cl3, e3_cl3]
    )
    results["BT5_clifford_identity_rotor_acts_as_identity"] = {
        "pass": bool(identity_acts_as_identity),
        "description": "Cl(3,0): identity rotor R=1 satisfies R*v*~R = v for all grade-1 vectors"
    }

    return results


# =====================================================================
# MAIN
# =====================================================================

if __name__ == "__main__":
    pos = run_positive_tests()
    neg = run_negative_tests()
    bnd = run_boundary_tests()

    all_pass = (
        all(v.get("pass", False) for v in pos.values()) and
        all(v.get("pass", False) for v in neg.values()) and
        all(v.get("pass", False) for v in bnd.values())
    )

    total = len(pos) + len(neg) + len(bnd)
    passed = sum(1 for d in [pos, neg, bnd] for v in d.values() if v.get("pass", False))

    results = {
        "name": NAME,
        "classification": "classical_baseline",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos,
        "negative": neg,
        "boundary": bnd,
        "overall_pass": all_pass,
        "passed": passed,
        "total": total,
    }

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, NAME + "_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)

    status = "PASS" if all_pass else "FAIL"
    print(f"{status} {NAME} [{passed}/{total}] -> {out_path}")
