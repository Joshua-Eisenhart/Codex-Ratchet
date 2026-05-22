#!/usr/bin/env python3
"""
Tensor Network G-Tower Bond Dimension (classical_baseline)
===========================================================

Each G-tower layer (GL3, O3, SO3, U3, SU3, Sp6) has a natural
representation on a tensor network: the representation dimension of
its natural action on C^n gives the bond dimension chi.

G-tower reduction chain maps to a bond dimension hierarchy and
tests entropy implications via I_c = log(chi) for pure Schmidt states.

Bond dimensions from group representations (n=3 case):
- GL(3): natural rep C^3 -> chi=3; adjoint rep -> chi=9
- O(3):  natural rep C^3 -> chi=3 (orthogonal subgroup of GL3)
- SO(3): irreps dim 2j+1; minimal non-trivial j=1 -> chi=3
- U(3):  natural rep C^3 -> chi=3; adjoint -> chi=9
- SU(3): fundamental rep C^3 -> chi=3; adjoint -> chi=8
- Sp(6): fundamental rep C^6 -> chi=6

The symplectic step Sp(6) EXPANDS chi from 3 to 6. This is the
symplectic "expansion step" in the G-tower. I_c(Sp6) - I_c(SU3) = log(2).

Classical baseline: I_c = log(chi) computed for uniform Schmidt state;
no genuine quantum group structure. Group constraints not verified
beyond representation dimension counts.

Innately missing: genuine representation theory, Clebsch-Gordan
decompositions, non-trivial group element actions on MPS tensors.
"""

import json
import os
import sys
import traceback
import numpy as np

# =====================================================================
# TOOL MANIFEST
# =====================================================================

TOOL_MANIFEST = {
    "pytorch":   {"tried": False, "used": False, "reason": "not needed -- I_c = log(chi) is a simple numpy computation"},
    "pyg":       {"tried": False, "used": False, "reason": "not needed -- G-tower is a fixed chain, no message passing"},
    "z3":        {"tried": False, "used": False, "reason": ""},
    "cvc5":      {"tried": False, "used": False, "reason": "not needed -- z3 sufficient for bond dimension ordering proofs"},
    "sympy":     {"tried": False, "used": False, "reason": ""},
    "clifford":  {"tried": False, "used": False, "reason": "not needed -- G-tower reps do not require Clifford algebra structure"},
    "geomstats": {"tried": False, "used": False, "reason": "not needed -- group geometry not needed for bond dim counting"},
    "e3nn":      {"tried": False, "used": False, "reason": "not needed -- no equivariant layers in this bond dim test"},
    "rustworkx": {"tried": False, "used": False, "reason": "not needed -- G-tower chain is fixed linear ordering"},
    "xgi":       {"tried": False, "used": False, "reason": "not needed -- no hyperedge structure required"},
    "toponetx":  {"tried": False, "used": False, "reason": "not needed -- no simplicial complex structure"},
    "gudhi":     {"tried": False, "used": False, "reason": "not needed -- no persistent homology structure required"},
}

classification = "classical_baseline"

divergence_log = [
    (
        "Classical baseline contrast: this runner-classical probe provides a "
        "comparator/control surface for sim_tn_gtower_bond_dimension; it does not promote a "
        "nonclassical, formal-scout, bridge, or axis-level claim."
    ),
]


TOOL_INTEGRATION_DEPTH = {
    "pytorch":   None,
    "pyg":       None,
    "z3":        "load_bearing",
    "cvc5":      None,
    "sympy":     "load_bearing",
    "clifford":  None,
    "geomstats": None,
    "e3nn":      None,
    "rustworkx": None,
    "xgi":       None,
    "toponetx":  None,
    "gudhi":     None,
}

# =====================================================================
# IMPORTS
# =====================================================================

try:
    from z3 import Solver, Real, And, Not, sat, unsat
    TOOL_MANIFEST["z3"]["tried"] = True
    TOOL_MANIFEST["z3"]["used"] = True
    TOOL_MANIFEST["z3"]["reason"] = (
        "N1: UNSAT proof that bond dimension decreases at SU3->Sp6 step "
        "(chi(SU3)=3, chi(Sp6)=6 -- Sp6 strictly expands, shrinkage is excluded). "
        "N2: UNSAT proof that I_c(Sp6) < I_c(SU3) (log(6) > log(3) by construction)."
    )
except ImportError:
    TOOL_MANIFEST["z3"]["reason"] = "not installed"
    print("FATAL: z3 required")
    sys.exit(1)

try:
    import sympy as sp
    TOOL_MANIFEST["sympy"]["tried"] = True
    TOOL_MANIFEST["sympy"]["used"] = True
    TOOL_MANIFEST["sympy"]["reason"] = (
        "Symbolic log computation and ordering proof: log(6) > log(3) "
        "and log(6) - log(3) = log(2). Verifies the entropy gap at the "
        "symplectic expansion step to symbolic precision. Used in P3, N2, B1."
    )
except ImportError:
    TOOL_MANIFEST["sympy"]["reason"] = "not installed"
    print("FATAL: sympy required")
    sys.exit(1)


# =====================================================================
# G-TOWER LAYER DEFINITIONS
# =====================================================================

# (name, chi, group_description)
G_TOWER_LAYERS = [
    ("GL3",  3, "GL(3,C): natural rep C^3, full linear group"),
    ("O3",   3, "O(3): orthogonal subgroup of GL(3), preserves inner product"),
    ("SO3",  3, "SO(3): special orthogonal, det=+1, irrep dim 2*1+1=3 at j=1"),
    ("U3",   3, "U(3): unitary matrices on C^3, natural rep"),
    ("SU3",  3, "SU(3): special unitary, det=1, fundamental rep C^3"),
    ("Sp6",  6, "Sp(6): symplectic group, fundamental rep C^6, EXPANDS chi"),
]

# Expected I_c = log(chi) for uniform Schmidt state
def ic_from_chi(chi):
    """I_c for a pure state with uniform Schmidt weights and Schmidt rank chi."""
    if chi <= 0:
        return 0.0
    return float(np.log(chi))


# =====================================================================
# HELPERS
# =====================================================================

def von_neumann_entropy(rho, tol=1e-12):
    """Von Neumann entropy S(rho) = -Tr(rho log rho)."""
    evals = np.linalg.eigvalsh(rho)
    evals = evals[evals > tol]
    if len(evals) == 0:
        return 0.0
    return float(-np.sum(evals * np.log(evals)))


def make_uniform_schmidt_state(chi, d_left, d_right, seed=0):
    """
    Build a pure bipartite state with uniform Schmidt decomposition:
    |psi> = (1/sqrt(chi)) sum_{k=1}^{chi} |u_k> |v_k>
    Returns psi as a flat vector of length d_left * d_right.
    """
    rng = np.random.default_rng(seed)
    U = np.linalg.qr(rng.standard_normal((d_left, d_left)))[0][:, :chi]
    V = np.linalg.qr(rng.standard_normal((d_right, d_right)))[0][:, :chi]
    lambdas = np.ones(chi) / chi
    psi_mat = U @ np.diag(np.sqrt(lambdas)) @ V.T  # (d_left, d_right)
    psi = psi_mat.flatten()
    norm = np.linalg.norm(psi)
    if norm > 1e-15:
        psi = psi / norm
    return psi


def ic_of_psi(psi, d_left, d_right):
    """I_c = S(B) for pure bipartite state psi (S(AB)=0 for pure state)."""
    psi_mat = psi.reshape(d_left, d_right)
    rho_B = psi_mat.conj().T @ psi_mat
    tr = np.trace(rho_B)
    if tr > 1e-15:
        rho_B = rho_B / tr
    return von_neumann_entropy(rho_B)


# =====================================================================
# POSITIVE TESTS
# =====================================================================

def run_positive_tests():
    results = {}

    # --- P1: I_c = log(chi) for each G-tower layer ---
    # For a uniform Schmidt state with Schmidt rank chi,
    # S(B) = -sum_k (1/chi) log(1/chi) = log(chi)
    layer_ic = {}
    for name, chi, desc in G_TOWER_LAYERS:
        d = max(chi, 6)  # use d >= chi for both subsystems
        psi = make_uniform_schmidt_state(chi, d_left=d, d_right=d, seed=0)
        ic_num = ic_of_psi(psi, d_left=d, d_right=d)
        ic_expected = ic_from_chi(chi)
        layer_ic[name] = {
            "chi": chi,
            "ic_numerical": float(ic_num),
            "ic_expected_log_chi": float(ic_expected),
            "match": abs(ic_num - ic_expected) < 1e-8,
        }
    results["P1_layer_ic_values"] = layer_ic
    results["P1_all_layers_ic_match_log_chi"] = all(v["match"] for v in layer_ic.values())

    # Spot-check: GL3/O3/SO3/U3/SU3 all have chi=3, I_c = log(3)
    expected_chi3_ic = float(np.log(3))
    chi3_layers = ["GL3", "O3", "SO3", "U3", "SU3"]
    results["P1_chi3_layers_ic_approx_log3"] = all(
        abs(layer_ic[n]["ic_numerical"] - expected_chi3_ic) < 1e-8
        for n in chi3_layers
    )
    results["P1_chi3_ic_value"] = expected_chi3_ic
    # Sp6 has chi=6, I_c = log(6)
    expected_chi6_ic = float(np.log(6))
    results["P1_Sp6_ic_approx_log6"] = abs(layer_ic["Sp6"]["ic_numerical"] - expected_chi6_ic) < 1e-8
    results["P1_chi6_ic_value"] = expected_chi6_ic

    # --- P2: All GL3->SU3 have chi<=3; Sp6 has chi=6 ---
    chi_vals = {name: chi for name, chi, _ in G_TOWER_LAYERS}
    results["P2_GL3_to_SU3_chi_leq_3"] = all(
        chi_vals[n] <= 3 for n in ["GL3", "O3", "SO3", "U3", "SU3"]
    )
    results["P2_Sp6_chi_equals_6"] = chi_vals["Sp6"] == 6
    results["P2_Sp6_expands_chi_from_SU3"] = chi_vals["Sp6"] > chi_vals["SU3"]

    # --- P3: Entropy gap at Sp6: I_c(Sp6) - I_c(SU3) = log(2) ---
    ic_Sp6 = layer_ic["Sp6"]["ic_numerical"]
    ic_SU3 = layer_ic["SU3"]["ic_numerical"]
    gap = ic_Sp6 - ic_SU3
    expected_gap = float(np.log(2))  # log(6) - log(3) = log(2)
    results["P3_entropy_gap_Sp6_minus_SU3"] = float(gap)
    results["P3_entropy_gap_equals_log2"] = abs(gap - expected_gap) < 1e-6
    results["P3_expected_gap_log2"] = expected_gap

    # sympy verification: log(6) - log(3) = log(2)
    gap_sympy = sp.log(6) - sp.log(3)
    gap_simplified = sp.simplify(gap_sympy - sp.log(2))
    results["P3_sympy_log6_minus_log3_equals_log2"] = (gap_simplified == 0)

    return results


# =====================================================================
# NEGATIVE TESTS
# =====================================================================

def run_negative_tests():
    results = {}

    # --- N1: z3 UNSAT -- bond dimension decreases at SU3->Sp6 step ---
    # chi(SU3) = 3, chi(Sp6) = 6: Sp6 strictly expands.
    # Claim to refute: chi_out < chi_in at SU3->Sp6.
    s1 = Solver()
    chi_SU3 = Real('chi_SU3')
    chi_Sp6 = Real('chi_Sp6')
    s1.add(chi_SU3 == 3.0)
    s1.add(chi_Sp6 == 6.0)
    # Claim: chi_Sp6 < chi_SU3 (bond dimension decreases)
    s1.add(chi_Sp6 < chi_SU3)
    result_n1 = s1.check()
    results["N1_z3_unsat_Sp6_bond_dim_less_than_SU3"] = (result_n1 == unsat)
    results["N1_z3_result"] = str(result_n1)

    # Numerical check: chi values from G-tower
    chi_vals = {name: chi for name, chi, _ in G_TOWER_LAYERS}
    results["N1_Sp6_chi_gt_SU3_chi"] = chi_vals["Sp6"] > chi_vals["SU3"]
    results["N1_chi_SU3"] = chi_vals["SU3"]
    results["N1_chi_Sp6"] = chi_vals["Sp6"]

    # --- N2: z3 UNSAT -- I_c(Sp6) < I_c(SU3) ---
    # log(6) > log(3), so I_c(Sp6) > I_c(SU3). The claim of less-than is excluded.
    s2 = Solver()
    ic_SU3_z3 = Real('ic_SU3')
    ic_Sp6_z3 = Real('ic_Sp6')
    # Axioms encoding the actual values
    s2.add(ic_SU3_z3 == float(np.log(3)))
    s2.add(ic_Sp6_z3 == float(np.log(6)))
    # Claim: ic_Sp6 < ic_SU3
    s2.add(ic_Sp6_z3 < ic_SU3_z3)
    result_n2 = s2.check()
    results["N2_z3_unsat_Sp6_ic_less_than_SU3"] = (result_n2 == unsat)
    results["N2_z3_result"] = str(result_n2)

    # sympy: log(6) > log(3)
    log6 = sp.log(6)
    log3 = sp.log(3)
    results["N2_sympy_log6_gt_log3"] = bool(sp.simplify(log6 - log3) > 0)
    results["N2_sympy_log6_minus_log3"] = float(float(log6.evalf()) - float(log3.evalf()))

    return results


# =====================================================================
# BOUNDARY TESTS
# =====================================================================

def run_boundary_tests():
    results = {}

    # --- B1: chi=1 product state: I_c = log(1) = 0 ---
    # At chi=1, any G-tower layer with trivial representation has zero I_c.
    # This is the chi=1 boundary: no entanglement, Axis 0 gradient = 0.
    for name, chi, _ in G_TOWER_LAYERS:
        d = 6
        psi_chi1 = make_uniform_schmidt_state(chi=1, d_left=d, d_right=d, seed=0)
        ic_chi1 = ic_of_psi(psi_chi1, d_left=d, d_right=d)
        results[f"B1_{name}_chi1_ic_zero"] = abs(ic_chi1) < 1e-10

    # sympy: log(1) = 0
    results["B1_sympy_log1_equals_0"] = (sp.log(1) == 0)

    # Numerical: I_c = log(chi) at chi=1 gives 0
    results["B1_ic_log1_is_zero"] = abs(float(np.log(1))) < 1e-15

    # --- B1b: monotone I_c profile across G-tower layers ---
    # GL3, O3, SO3, U3, SU3 all have chi=3 (same I_c).
    # Sp6 has chi=6 (higher I_c). So the profile is flat then jumps at Sp6.
    ic_profile = {name: ic_from_chi(chi) for name, chi, _ in G_TOWER_LAYERS}
    # All chi=3 layers have equal I_c
    chi3_names = ["GL3", "O3", "SO3", "U3", "SU3"]
    ic_chi3 = ic_profile["GL3"]
    results["B1_chi3_layers_equal_ic"] = all(
        abs(ic_profile[n] - ic_chi3) < 1e-12 for n in chi3_names
    )
    # Sp6 strictly higher
    results["B1_Sp6_ic_strictly_greater_than_chi3"] = ic_profile["Sp6"] > ic_chi3 + 0.5

    # sympy confirms: log(6) - log(3) = log(2) > 0
    jump = sp.simplify(sp.log(6) - sp.log(3))
    results["B1_sympy_Sp6_jump_is_log2"] = (sp.simplify(jump - sp.log(2)) == 0)
    results["B1_sympy_jump_positive"] = bool(jump > 0)

    return results


# =====================================================================
# MAIN
# =====================================================================

if __name__ == "__main__":
    errors = []
    pos = {}
    neg = {}
    bnd = {}

    try:
        pos = run_positive_tests()
    except Exception as e:
        errors.append(f"positive: {e}\n{traceback.format_exc()}")

    try:
        neg = run_negative_tests()
    except Exception as e:
        errors.append(f"negative: {e}\n{traceback.format_exc()}")

    try:
        bnd = run_boundary_tests()
    except Exception as e:
        errors.append(f"boundary: {e}\n{traceback.format_exc()}")

    bool_pos = {k: v for k, v in pos.items() if isinstance(v, bool)}
    bool_neg = {k: v for k, v in neg.items() if isinstance(v, bool)}
    bool_bnd = {k: v for k, v in bnd.items() if isinstance(v, bool)}
    all_pass = (
        all(bool_pos.values()) and
        all(bool_neg.values()) and
        all(bool_bnd.values()) and
        len(errors) == 0
    )

    results = {
        "name": "tn_gtower_bond_dimension",
        "classification": classification,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos,
        "negative": neg,
        "boundary": bnd,
        "all_pass": all_pass,
        "errors": errors,
        "summary": {"all_pass": all_pass},
        "divergence_log": [
            "classical bond dimension assignment: chi values are counts from representation theory, not computed group actions",
            "I_c = log(chi) holds exactly for uniform Schmidt states -- generic states have different I_c profiles",
            "G-tower reduction chain is a labeling; group constraints on MPS tensors not enforced or tested here",
            "Sp6 expansion step is an arithmetic fact about representation dimensions, not a quantum phase transition",
            "z3 UNSAT proofs are over Real arithmetic encoding of specific chi values, not group theory axioms",
        ],
    }

    out = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results",
                       "tn_gtower_bond_dimension_results.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"all_pass={all_pass} -> {out}")
    if errors:
        for e in errors:
            print(e)
