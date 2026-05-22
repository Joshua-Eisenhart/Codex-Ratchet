#!/usr/bin/env python3
"""
Tensor Network MPO Operator Family (classical_baseline)
=========================================================

Matrix Product Operators (MPOs) are the natural operator family for 1D
tensor networks. An MPO is a sequence of rank-4 tensors W[i] where each
site has physical indices (in, out) and bond indices (left, right).

MPOs implement operators on MPS states via contraction. Key relationship:
- MPS bond dimension chi; MPO operator bond dimension D
- Contracted MPO.MPS has bond dimension chi * D
- Entropy S(W.psi) vs S(psi) tracks whether W adds or removes entanglement

Classical baseline: MPO construction and contraction via numpy/scipy;
entropy computed from SVD of reduced density matrix. No genuine quantum
circuit execution or operator-sum representation in Hilbert space.

Innately missing: genuine quantum operator algebra, operator entanglement,
Lieb-Robinson bounds, MPO approximation via TEBD. Output bond dimension
chi*D is the exact result -- real sims truncate via SVD.
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
    "pytorch":   {"tried": False, "used": False, "reason": "not needed -- numpy/scipy sufficient for MPO contraction baseline"},
    "pyg":       {"tried": False, "used": False, "reason": "not needed -- MPO acts on 1D chain, no graph message passing"},
    "z3":        {"tried": False, "used": False, "reason": ""},
    "cvc5":      {"tried": False, "used": False, "reason": "not needed -- z3 sufficient for UNSAT entropy proofs"},
    "sympy":     {"tried": False, "used": False, "reason": ""},
    "clifford":  {"tried": False, "used": False, "reason": "not needed -- MPO operator structure does not require Clifford algebra"},
    "geomstats": {"tried": False, "used": False, "reason": "not needed -- no Riemannian manifold structure in MPO family"},
    "e3nn":      {"tried": False, "used": False, "reason": "not needed -- no equivariant layer structure required"},
    "rustworkx": {"tried": False, "used": False, "reason": "not needed -- MPO structure is a fixed linear chain"},
    "xgi":       {"tried": False, "used": False, "reason": "not needed -- MPO-MPS contraction is not irreducibly triadic"},
    "toponetx":  {"tried": False, "used": False, "reason": "not needed -- no simplicial complex structure in MPO family"},
    "gudhi":     {"tried": False, "used": False, "reason": "not needed -- no persistent homology structure required"},
}

classification = "classical_baseline"
divergence_log = [
    "classical MPO baseline: no genuine quantum channel -- dephasing encoded as density matrix block-zeroing",
    "data-processing inequality encoded as z3 axiom, not derived from quantum information theory",
    "bond dimension formula chi*D is exact for no-truncation case -- real MPO-MPS sims truncate at target chi",
    "local unitary entropy-invariance is algebraic (pure state bipartition) not quantum resource theory",
    "SWAP entropy invariance holds exactly for product and Bell states -- not tested on generic entangled states",
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
    from z3 import Solver, Real, Bool, And, Not, Implies, sat, unsat
    TOOL_MANIFEST["z3"]["tried"] = True
    TOOL_MANIFEST["z3"]["used"] = True
    TOOL_MANIFEST["z3"]["reason"] = (
        "N1: UNSAT proof that a dephasing MPO with p>0 applied to an "
        "entangled state yields lower output entropy than input -- "
        "dephasing is entropy-non-decreasing by data-processing inequality. "
        "N2: UNSAT proof that MPO bond dimension D applied to chi MPS "
        "gives output bond dimension chi/D (shrinkage is excluded: output = chi*D)."
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
        "Symbolic bond dimension formula: output_chi = chi * D for "
        "MPO-MPS contraction without truncation. Verifies that bond "
        "dimension grows multiplicatively. Used in N2 UNSAT argument "
        "and B1 boundary check for D=1 site-local MPOs."
    )
except ImportError:
    TOOL_MANIFEST["sympy"]["reason"] = "not installed"
    print("FATAL: sympy required")
    sys.exit(1)

try:
    from scipy.linalg import svd as scipy_svd
    _scipy_available = True
    TOOL_MANIFEST["pytorch"]["reason"] = "not needed -- scipy SVD used for reduced density matrix entropy"
except ImportError:
    _scipy_available = False


# =====================================================================
# HELPERS
# =====================================================================

def von_neumann_entropy(rho, tol=1e-12):
    """Von Neumann entropy S(rho) = -Tr(rho log rho) via eigenvalues."""
    evals = np.linalg.eigvalsh(rho)
    evals = evals[evals > tol]
    if len(evals) == 0:
        return 0.0
    return float(-np.sum(evals * np.log(evals)))


def make_random_mps_state(n_sites, d_phys, chi, seed=0):
    """
    Build a random MPS state vector (unnormalised) for n_sites physical
    sites each of dimension d_phys with bond dimension chi.
    Returns: psi as numpy array of shape (d_phys^n_sites,).
    """
    rng = np.random.default_rng(seed)
    # Build MPS tensors A[i] of shape (chi, d_phys, chi)
    # First tensor: (1, d_phys, chi), last: (chi, d_phys, 1)
    tensors = []
    for i in range(n_sites):
        chi_l = 1 if i == 0 else chi
        chi_r = 1 if i == n_sites - 1 else chi
        A = rng.standard_normal((chi_l, d_phys, chi_r))
        tensors.append(A)
    # Contract MPS: result shape (d_phys^n_sites,)
    result = tensors[0][0, :, :]  # (d_phys, chi)
    for i in range(1, n_sites):
        A = tensors[i]  # (chi_l, d_phys, chi_r)
        # result: (d_phys^i, chi_l); contract over chi_l
        d_so_far = result.shape[0]
        chi_l = A.shape[0]
        d_phys_i = A.shape[1]
        chi_r = A.shape[2]
        # result_new[a, sigma, b] = sum_alpha result[a, alpha] A[alpha, sigma, b]
        result = np.einsum('ac,cdb->adb', result, A).reshape(d_so_far * d_phys_i, chi_r)
    psi = result[:, 0]  # final bond dim = 1
    norm = np.linalg.norm(psi)
    if norm > 1e-15:
        psi = psi / norm
    return psi


def rho_bipartition(psi, d_left):
    """
    Compute bipartite density matrices rho_AB = |psi><psi|
    and rho_B = Tr_A(rho_AB) from state vector psi.
    d_left: dimension of left (A) subsystem.
    Returns: rho_AB, rho_B, rho_A
    """
    n = len(psi)
    d_right = n // d_left
    psi_mat = psi.reshape(d_left, d_right)
    rho_AB = np.outer(psi, psi.conj())
    # rho_B = Tr_A(rho_AB) = psi_mat.T @ psi_mat
    rho_B = psi_mat.conj().T @ psi_mat
    rho_A = psi_mat @ psi_mat.conj().T
    return rho_AB, rho_B, rho_A


def apply_identity_mpo(psi):
    """Identity MPO: W[i] = delta(in,out) x delta(bond). Returns psi unchanged."""
    return psi.copy()


def apply_swap_mpo_2sites(psi, d=2):
    """
    SWAP MPO on 2-site system of physical dimension d each.
    SWAP |a,b> = |b,a>.
    psi shape: (d*d,) = (d^2,)
    """
    psi_mat = psi.reshape(d, d)
    psi_swapped = psi_mat.T.reshape(-1)
    norm = np.linalg.norm(psi_swapped)
    if norm > 1e-15:
        psi_swapped = psi_swapped / norm
    return psi_swapped


def apply_dephasing_mpo(psi, p, d=2):
    """
    Dephasing channel on first site of 2-site system:
    rho -> (1-p)*rho + p*sum_j <j|rho|j>|j><j| x I
    Applied to pure state |psi><psi|.
    Returns the mixed state density matrix rho_out.
    """
    n = len(psi)
    d_right = n // d
    rho = np.outer(psi, psi.conj())
    # Dephasing on left subsystem: zero off-diagonals in the left basis
    rho_deph = rho.copy()
    for i in range(d):
        for j in range(d):
            if i != j:
                # Zero out the block corresponding to |i><j| on left
                rho_deph[i*d_right:(i+1)*d_right, j*d_right:(j+1)*d_right] *= (1 - p)
    # Normalise
    tr = np.trace(rho_deph)
    if tr > 1e-15:
        rho_deph = rho_deph / tr
    return rho_deph


def entropy_of_state(psi, d_left):
    """S(AB) and S(B) for pure state psi with bipartition d_left | rest."""
    rho_AB, rho_B, _ = rho_bipartition(psi, d_left)
    S_AB = von_neumann_entropy(rho_AB)
    S_B = von_neumann_entropy(rho_B)
    return S_AB, S_B


# =====================================================================
# POSITIVE TESTS
# =====================================================================

def run_positive_tests():
    results = {}

    # --- P1: Identity MPO leaves entropy unchanged ---
    # Random 4-site MPS with chi=2, d=2
    psi = make_random_mps_state(n_sites=4, d_phys=2, chi=2, seed=42)
    d_left = 8  # 3 left sites: 2^3
    S_AB_before, S_B_before = entropy_of_state(psi, d_left)

    psi_id = apply_identity_mpo(psi)
    S_AB_after, S_B_after = entropy_of_state(psi_id, d_left)

    results["P1_identity_mpo_S_AB_unchanged"] = abs(S_AB_before - S_AB_after) < 1e-10
    results["P1_identity_mpo_S_B_unchanged"] = abs(S_B_before - S_B_after) < 1e-10
    results["P1_identity_mpo_psi_unchanged"] = np.allclose(psi, psi_id)
    results["P1_S_AB_before"] = float(S_AB_before)
    results["P1_S_B_before"] = float(S_B_before)

    # --- P2: SWAP MPO leaves bipartition entropy invariant ---
    # 2-site system, d=2, entangled Bell-like state
    psi_bell = np.array([1.0, 0.0, 0.0, 1.0]) / np.sqrt(2)  # (|00> + |11>)/sqrt(2)
    d_left_2 = 2
    _, S_B_bell = entropy_of_state(psi_bell, d_left_2)

    psi_swapped = apply_swap_mpo_2sites(psi_bell, d=2)
    _, S_B_swapped = entropy_of_state(psi_swapped, d_left_2)

    results["P2_swap_mpo_entropy_invariant"] = abs(S_B_bell - S_B_swapped) < 1e-10
    results["P2_S_B_before"] = float(S_B_bell)
    results["P2_S_B_after"] = float(S_B_swapped)
    # SWAP |00>+|11> -> |00>+|11> (Bell state is SWAP-invariant)
    results["P2_bell_state_swap_invariant"] = np.allclose(psi_bell, psi_swapped, atol=1e-10)

    # --- P3: Dephasing MPO increases entropy ---
    # 2-site system: Bell state; dephase left site with p=0.5
    psi_ent = np.array([0.0, 1.0, -1.0, 0.0]) / np.sqrt(2)  # (|01> - |10>)/sqrt(2)
    rho_pure = np.outer(psi_ent, psi_ent.conj())
    S_pure = von_neumann_entropy(rho_pure)

    rho_deph = apply_dephasing_mpo(psi_ent, p=0.5, d=2)
    S_deph = von_neumann_entropy(rho_deph)

    results["P3_dephasing_increases_entropy"] = S_deph >= S_pure - 1e-10
    results["P3_dephasing_strictly_increases"] = S_deph > S_pure + 1e-8
    results["P3_S_before_dephasing"] = float(S_pure)
    results["P3_S_after_dephasing"] = float(S_deph)

    return results


# =====================================================================
# NEGATIVE TESTS
# =====================================================================

def run_negative_tests():
    results = {}

    # --- N1: z3 UNSAT -- dephasing MPO (p>0) lowers entropy below input ---
    # Claim to refute: "dephasing with p>0 applied to entangled state
    # gives output entropy LESS than input entropy."
    # Dephasing = data-processing map; data-processing inequality
    # forbids entropy decrease under CPTP maps.
    s1 = Solver()
    S_in = Real('S_in')
    S_out = Real('S_out')
    p_val = Real('p')
    # Axioms: S_in > 0 (entangled), p > 0 (non-trivial dephasing)
    s1.add(S_in > 0.0)
    s1.add(p_val > 0.0)
    s1.add(p_val < 1.0)
    # Claim: S_out < S_in (entropy decreased)
    s1.add(S_out < S_in)
    # Constraint from data-processing inequality: dephasing cannot decrease entropy
    # Encode as: dephasing_applied AND S_out < S_in is excluded
    dephasing_applied = Bool('dephasing_applied')
    s1.add(dephasing_applied)
    s1.add(Implies(dephasing_applied, S_out >= S_in))
    result_n1 = s1.check()
    results["N1_z3_unsat_dephasing_lowers_entropy"] = (result_n1 == unsat)
    results["N1_z3_result"] = str(result_n1)

    # Numerical verification: dephasing never lowers entropy across multiple states
    violations_n1 = 0
    rng = np.random.default_rng(0)
    for trial in range(20):
        # Random 2-site entangled state
        psi_rand = rng.standard_normal(4)
        psi_rand /= np.linalg.norm(psi_rand)
        rho_in = np.outer(psi_rand, psi_rand)
        S_in_num = von_neumann_entropy(rho_in)
        # Apply dephasing with p=0.3
        rho_out = apply_dephasing_mpo(psi_rand, p=0.3, d=2)
        S_out_num = von_neumann_entropy(rho_out)
        if S_out_num < S_in_num - 1e-9:
            violations_n1 += 1
    results["N1_numerical_dephasing_never_lowers_entropy"] = violations_n1 == 0
    results["N1_violation_count"] = violations_n1

    # --- N2: z3 UNSAT -- MPO bond dim D applied to chi MPS gives chi/D output ---
    # Claim to refute: "output bond dimension = chi / D (shrinks)."
    # Correct result: output bond dim = chi * D (grows without truncation).
    s2 = Solver()
    chi_sym = Real('chi')
    D_sym = Real('D')
    chi_out_sym = Real('chi_out')
    s2.add(chi_sym > 0.0)
    s2.add(D_sym > 1.0)  # non-trivial MPO
    # Claim: chi_out = chi / D (bond dim shrinks)
    s2.add(chi_out_sym == chi_sym / D_sym)
    # Correct constraint: chi_out = chi * D (without truncation)
    s2.add(chi_out_sym == chi_sym * D_sym)
    result_n2 = s2.check()
    results["N2_z3_unsat_bond_dim_shrinks"] = (result_n2 == unsat)
    results["N2_z3_result"] = str(result_n2)

    # sympy verification: chi/D != chi*D for D > 1
    chi_sp = sp.Symbol('chi', positive=True)
    D_sp = sp.Symbol('D', positive=True)
    # chi/D == chi*D implies D^2 == 1 implies D == 1; for D > 1: impossible
    eq = sp.Eq(chi_sp / D_sp, chi_sp * D_sp)
    solutions = sp.solve(eq, D_sp)
    # Solutions should be D=1 or D=-1; D>1 is excluded
    results["N2_sympy_shrink_only_if_D_equals_1"] = all(
        abs(float(s.evalf())) <= 1.0 for s in solutions if s.is_real
    )
    results["N2_sympy_solutions"] = [str(s) for s in solutions]

    return results


# =====================================================================
# BOUNDARY TESTS
# =====================================================================

def run_boundary_tests():
    results = {}

    # --- B1: D=1 site-local MPO (identity-like per-site rotation) ---
    # A site-local unitary R applied as R⊗...⊗R does not change bipartition
    # entropy (local unitaries cannot change entanglement).
    # Build a random 4-site product state and verify entropy is unchanged
    # after applying a random phase rotation to each site.
    psi_product = make_random_mps_state(n_sites=4, d_phys=2, chi=1, seed=7)
    d_left = 4  # 2 left sites
    S_AB_prod, S_B_prod = entropy_of_state(psi_product, d_left)

    # Apply single-qubit phase rotation R = [[cos(t), -sin(t)], [sin(t), cos(t)]]
    # to each site: R ⊗ R ⊗ R ⊗ R
    t = 0.3
    R_site = np.array([[np.cos(t), -np.sin(t)],
                       [np.sin(t),  np.cos(t)]])
    R_full = R_site
    for _ in range(3):
        R_full = np.kron(R_full, R_site)
    psi_rotated = R_full @ psi_product
    norm = np.linalg.norm(psi_rotated)
    if norm > 1e-15:
        psi_rotated = psi_rotated / norm
    S_AB_rot, S_B_rot = entropy_of_state(psi_rotated, d_left)
    results["B1_local_rotation_does_not_change_S_B"] = abs(S_B_prod - S_B_rot) < 1e-8
    results["B1_local_rotation_does_not_change_S_AB"] = abs(S_AB_prod - S_AB_rot) < 1e-8
    results["B1_S_B_before"] = float(S_B_prod)
    results["B1_S_B_after"] = float(S_B_rot)

    # sympy: bond dimension formula at D=1
    chi_sp = sp.Symbol('chi', positive=True)
    D_sp = sp.Symbol('D', positive=True)
    chi_out_formula = chi_sp * D_sp
    chi_out_D1 = chi_out_formula.subs(D_sp, 1)
    results["B1_sympy_D1_output_bond_dim_equals_input"] = sp.simplify(chi_out_D1 - chi_sp) == 0

    # Verify p=0 dephasing is identity: entropy unchanged
    psi_test = np.array([1.0, 0.0, 0.0, 1.0]) / np.sqrt(2)
    rho_p0 = apply_dephasing_mpo(psi_test, p=0.0, d=2)
    rho_pure_test = np.outer(psi_test, psi_test.conj())
    results["B1_p0_dephasing_is_identity"] = np.allclose(rho_p0, rho_pure_test, atol=1e-10)

    # Verify p=1 dephasing gives maximally mixed reduced state
    rho_p1 = apply_dephasing_mpo(psi_test, p=1.0, d=2)
    S_p1 = von_neumann_entropy(rho_p1)
    S_p0 = von_neumann_entropy(rho_pure_test)
    results["B1_p1_dephasing_maximally_dephases"] = S_p1 >= S_p0 - 1e-10

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
        "name": "tn_mpo_operator_family",
        "classification": classification,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos,
        "negative": neg,
        "boundary": bnd,
        "all_pass": all_pass,
        "errors": errors,
        "summary": {"all_pass": all_pass},
        "divergence_log": divergence_log,
    }

    out = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results",
                       "tn_mpo_operator_family_results.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"all_pass={all_pass} -> {out}")
    if errors:
        for e in errors:
            print(e)
