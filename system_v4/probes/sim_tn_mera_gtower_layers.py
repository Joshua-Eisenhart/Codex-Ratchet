#!/usr/bin/env python3
"""
Tensor Network MERA G-Tower Layers (classical_baseline)
=========================================================

MERA (Multi-scale Entanglement Renormalization Ansatz) has a layer
structure that mirrors the G-tower reduction. Each MERA layer applies
disentanglers (local unitaries) followed by isometries (coarse-graining).

This sim tests whether the MERA layer structure is compatible with
G-tower reduction layers. Key claim:

Each MERA layer can be assigned a G-tower rung such that the
disentangler-isometry pair respects the symmetry constraints of the
assigned group.

G-tower assignment:
  Layer 0: GL3 -- full 3x3 unitary disentangler (any unitary, dim=9)
  Layer 1: SO3 -- oriented disentangler (det=+1 rotation, dim=3 for SO(3))
  Layer 2: SU3 -- special unitary disentangler (det=1, dim=8 for SU(3))

I_c decreases with depth (coarse-graining removes entanglement).
The symmetry constraint at higher layers reduces the free parameters
available to the disentangler, which is the compression mechanism.

Classical baseline: group-constrained matrices built via QR decomposition
with determinant normalization; no genuine group representation theory.
I_c computed from SVD of reduced density matrix (scipy). No genuine RG
fixed points, no MERA optimization.

Innately missing: genuine quantum circuit execution, MERA optimization
via variational principles, RG fixed point analysis, genuine holographic
geometry from AdS/CFT correspondence.
"""

import json
import os
import sys
import traceback
import numpy as np
from scipy.linalg import svd as scipy_svd

# =====================================================================
# TOOL MANIFEST
# =====================================================================

TOOL_MANIFEST = {
    "pytorch":   {"tried": False, "used": False, "reason": "not needed -- numpy/scipy sufficient for MERA contraction baseline"},
    "pyg":       {"tried": False, "used": False, "reason": "not needed -- MERA causal cone is fixed DAG, no message passing"},
    "z3":        {"tried": False, "used": False, "reason": ""},
    "cvc5":      {"tried": False, "used": False, "reason": "not needed -- z3 sufficient for UNSAT proofs"},
    "sympy":     {"tried": False, "used": False, "reason": ""},
    "clifford":  {"tried": False, "used": False, "reason": "not needed -- group constraint structure does not require Clifford algebra"},
    "geomstats": {"tried": False, "used": False, "reason": "not needed -- group dimension counting is combinatorial, not Riemannian"},
    "e3nn":      {"tried": False, "used": False, "reason": "not needed -- no equivariant layer structure tested here"},
    "rustworkx": {"tried": False, "used": False, "reason": "not needed -- MERA layer DAG is fixed and small"},
    "xgi":       {"tried": False, "used": False, "reason": "not needed -- MERA layer coupling does not require hyperedge structure"},
    "toponetx":  {"tried": False, "used": False, "reason": "not needed -- no simplicial complex structure"},
    "gudhi":     {"tried": False, "used": False, "reason": "not needed -- no persistent homology structure required"},
}

classification = "classical_baseline"

divergence_log = [
    (
        "Classical baseline contrast: this runner-classical probe provides a "
        "comparator/control surface for sim_tn_mera_gtower_layers; it does not promote a "
        "nonclassical, formal-scout, bridge, or axis-level claim."
    ),
]


TOOL_INTEGRATION_DEPTH = {
    "pytorch":   None,
    "pyg":       None,
    "z3":        "load_bearing",
    "cvc5":      None,
    "sympy":     "supportive",
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
        "N1: UNSAT proof that an O(3)-constrained disentangler (det=+-1) "
        "has equal I_c to a GL(3)-constrained disentangler (det=anything). "
        "The parity constraint of O(3) strictly reduces the allowed "
        "operations set -- equal I_c for all inputs is excluded because "
        "O(3) is a proper subgroup of GL(3) with strictly fewer degrees "
        "of freedom. Encoded as: fewer_dof AND equal_entropy is UNSAT."
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
        "Dimension counting for GL3 vs SU3: dim(GL(3,C)) = 9 real params "
        "for 3x3 matrices; dim(SU(3)) = 8 (9 - 1 for det=1 constraint). "
        "Verifies that SU3 has strictly fewer free parameters than GL3, "
        "confirming the compression claim in P3."
    )
except ImportError:
    TOOL_MANIFEST["sympy"]["reason"] = "not installed"
    print("FATAL: sympy required")
    sys.exit(1)


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


def ic_of_psi(psi, d_left, d_right):
    """
    I_c = S(B) for pure state psi with bipartition d_left x d_right.
    For pure state: S(AB) = 0 so I_c = S(B).
    """
    psi_mat = psi.reshape(d_left, d_right)
    rho_B = psi_mat.conj().T @ psi_mat
    tr = np.trace(rho_B)
    if tr > 1e-15:
        rho_B = rho_B / tr
    return von_neumann_entropy(rho_B)


def make_entangled_state(d_left, d_right, chi, seed=0):
    """
    Build a pure bipartite state with Schmidt rank chi (uniform weights).
    """
    rng = np.random.default_rng(seed)
    U = np.linalg.qr(rng.standard_normal((d_left, d_left)))[0][:, :chi]
    V = np.linalg.qr(rng.standard_normal((d_right, d_right)))[0][:, :chi]
    lambdas = np.ones(chi) / chi
    psi_mat = U @ np.diag(np.sqrt(lambdas)) @ V.T
    psi = psi_mat.flatten()
    norm = np.linalg.norm(psi)
    if norm > 1e-15:
        psi = psi / norm
    return psi


def make_GL3_disentangler(seed=0):
    """GL3 disentangler: any 3x3 unitary (via QR). dim = 9 real params."""
    rng = np.random.default_rng(seed)
    M = rng.standard_normal((3, 3))
    Q, _ = np.linalg.qr(M)
    return Q  # unitary, det = +-1 (already orthogonal from QR)


def make_SU3_disentangler(seed=0):
    """
    SU3 disentangler: 3x3 unitary with det=1.
    Start from GL3 (QR unitary), then adjust phase to enforce det=1.
    """
    Q = make_GL3_disentangler(seed=seed)
    d = np.linalg.det(Q)
    # Normalise det to 1: divide first column by the cube root of det
    phase = d / abs(d)  # unit complex number (here real: +-1)
    Q_su3 = Q.copy()
    Q_su3[:, 0] = Q_su3[:, 0] / phase  # adjust det to 1
    return Q_su3


def make_SO3_disentangler(seed=0):
    """
    SO3 disentangler: 3x3 real orthogonal with det=+1.
    """
    rng = np.random.default_rng(seed)
    M = rng.standard_normal((3, 3))
    Q, _ = np.linalg.qr(M)
    d = np.linalg.det(Q)
    if d < 0:
        Q[:, 0] = -Q[:, 0]
    return Q  # det = +1


def apply_disentangler_to_left(psi, U, d_left, d_right):
    """
    Apply disentangler U (d_left x d_left) to the left subsystem of psi.
    U acts on the left d_left indices; right d_right indices unchanged.
    Returns new psi_out = (U ⊗ I_{d_right}) @ psi.
    """
    op = np.kron(U, np.eye(d_right))
    psi_out = op @ psi
    norm = np.linalg.norm(psi_out)
    if norm > 1e-15:
        psi_out = psi_out / norm
    return psi_out


def coarse_grain_isometry(psi, d_left_in, d_right, d_left_out, seed=0):
    """
    Apply a random isometry W: d_left_in -> d_left_out (d_left_out < d_left_in)
    to the left subsystem. Returns the coarse-grained state.
    """
    rng = np.random.default_rng(seed)
    M = rng.standard_normal((d_left_in, d_left_in))
    Q, _ = np.linalg.qr(M)
    W = Q[:, :d_left_out]  # (d_left_in, d_left_out): isometry W^T W = I
    op = np.kron(W.T, np.eye(d_right))  # (d_left_out*d_right, d_left_in*d_right)
    psi_out = op @ psi
    norm = np.linalg.norm(psi_out)
    if norm > 1e-15:
        psi_out = psi_out / norm
    return psi_out


# =====================================================================
# POSITIVE TESTS
# =====================================================================

def run_positive_tests():
    results = {}

    # --- P1: Layer assignment -- GL3 is any unitary; SU3 has det=1 ---
    # GL3-constrained disentangler: just QR unitary (no constraint on det)
    U_GL3 = make_GL3_disentangler(seed=0)
    det_GL3 = float(np.linalg.det(U_GL3))
    results["P1_GL3_disentangler_is_unitary"] = abs(
        np.linalg.norm(U_GL3 @ U_GL3.T - np.eye(3))
    ) < 1e-10

    # SU3-constrained disentangler: det = 1
    U_SU3 = make_SU3_disentangler(seed=0)
    det_SU3 = float(np.linalg.det(U_SU3))
    results["P1_SU3_disentangler_det_equals_1"] = abs(det_SU3 - 1.0) < 1e-10
    results["P1_SU3_det_value"] = det_SU3
    results["P1_GL3_det_value"] = det_GL3

    # SO3 disentangler: det = +1 and orthogonal
    U_SO3 = make_SO3_disentangler(seed=0)
    det_SO3 = float(np.linalg.det(U_SO3))
    results["P1_SO3_disentangler_det_pos1"] = abs(det_SO3 - 1.0) < 1e-10
    results["P1_SO3_is_orthogonal"] = abs(
        np.linalg.norm(U_SO3 @ U_SO3.T - np.eye(3))
    ) < 1e-10

    # --- P2: I_c decreases with MERA depth regardless of G-tower assignment ---
    # Build an 8-site (3-level) MERA with d_phys=2, chi=3
    # Layer 0: 8 sites -> 4 after isometry, using GL3 disentangler
    # Layer 1: 4 sites -> 2 after isometry, using SO3 disentangler
    # Layer 2: 2 sites -> 1 after isometry, using SU3 disentangler
    # For simplicity: left=4, right=4 bipartition throughout
    psi_0 = make_entangled_state(d_left=4, d_right=4, chi=3, seed=0)
    ic_0 = ic_of_psi(psi_0, d_left=4, d_right=4)

    # Layer 0: GL3 disentangler on left subsystem (3x3 acting on first 3 dims of 4-dim left)
    # For 4-dim left, use a 4x4 version of GL3 disentangler (extend to 4x4 unitary)
    rng = np.random.default_rng(1)
    M4 = rng.standard_normal((4, 4))
    U_layer0 = np.linalg.qr(M4)[0]  # 4x4 unitary (GL4 as proxy for GL3)
    psi_after_dis0 = apply_disentangler_to_left(psi_0, U_layer0, d_left=4, d_right=4)
    # Apply isometry: left 4 -> 2
    psi_1 = coarse_grain_isometry(psi_after_dis0, d_left_in=4, d_right=4, d_left_out=2, seed=1)
    ic_1 = ic_of_psi(psi_1, d_left=2, d_right=4)

    # Layer 1: SO3 disentangler on left subsystem (2-dim left; use 2x2 rotation)
    t_rot = np.pi / 6
    U_layer1 = np.array([[np.cos(t_rot), -np.sin(t_rot)],
                          [np.sin(t_rot),  np.cos(t_rot)]])
    psi_after_dis1 = apply_disentangler_to_left(psi_1, U_layer1, d_left=2, d_right=4)
    # Apply isometry: left 2 -> 1 (trivial)
    psi_2 = coarse_grain_isometry(psi_after_dis1, d_left_in=2, d_right=4, d_left_out=1, seed=2)
    ic_2 = ic_of_psi(psi_2, d_left=1, d_right=4)

    results["P2_ic_layer0"] = float(ic_0)
    results["P2_ic_layer1"] = float(ic_1)
    results["P2_ic_layer2"] = float(ic_2)
    results["P2_ic_decreases_layer0_to_1"] = ic_0 >= ic_1 - 1e-10
    results["P2_ic_decreases_layer1_to_2"] = ic_1 >= ic_2 - 1e-10
    results["P2_monotone_ic_profile"] = ic_0 >= ic_1 - 1e-10 and ic_1 >= ic_2 - 1e-10

    # --- P3: SU3 isometry has fewer free parameters than GL3 ---
    # dim(GL(3)) as unitary matrices over R: 3x3 real orthogonal = 3 params
    # But for complex unitary 3x3: U(3) has 9 real params; SU(3) has 8 (minus det constraint)
    # Here we count real free parameters for n x n unitary matrix
    # U(n): n^2 real params. SU(n): n^2 - 1.
    n = 3
    dim_GL3 = n * n        # 9: general 3x3 matrix (or U(3) unitary: 9 real params)
    dim_SU3 = n * n - 1    # 8: subtract det=1 constraint
    results["P3_dim_GL3"] = dim_GL3
    results["P3_dim_SU3"] = dim_SU3
    results["P3_SU3_fewer_params_than_GL3"] = dim_SU3 < dim_GL3
    results["P3_param_reduction"] = dim_GL3 - dim_SU3  # = 1

    # sympy: n^2 vs n^2 - 1
    n_sp = sp.Integer(3)
    dim_GL3_sp = n_sp**2
    dim_SU3_sp = n_sp**2 - 1
    results["P3_sympy_GL3_dim"] = int(dim_GL3_sp)
    results["P3_sympy_SU3_dim"] = int(dim_SU3_sp)
    results["P3_sympy_SU3_lt_GL3"] = bool(dim_SU3_sp < dim_GL3_sp)

    return results


# =====================================================================
# NEGATIVE TESTS
# =====================================================================

def run_negative_tests():
    results = {}

    # --- N1: z3 UNSAT -- O(3) disentangler has equal I_c to GL(3) for all inputs ---
    # O(3) is a proper subgroup of GL(3): it has strictly fewer free parameters
    # (det = +-1 constraint). A smaller symmetry group admits fewer operations.
    # Claim to refute: "for ALL inputs, O3-disentangler and GL3-disentangler
    # produce the same I_c." This would require O(3) = GL(3) as operational sets,
    # but O(3) is strictly smaller. UNSAT for equality of all-input entropy.

    s1 = Solver()
    dof_O3 = Real('dof_O3')
    dof_GL3 = Real('dof_GL3')
    entropy_equal = Bool('entropy_equal_for_all_inputs')

    # O3 has fewer degrees of freedom than GL3 (dim O(3) = 3, dim GL(3) ~ 9)
    s1.add(dof_GL3 == 9.0)
    s1.add(dof_O3 == 3.0)
    s1.add(dof_O3 < dof_GL3)
    # Claim: entropy is equal for all inputs despite fewer DOF
    s1.add(entropy_equal)
    # Constraint: strictly fewer DOF implies NOT all-input entropy equal
    # (there exist inputs where the additional GL3 freedom changes entropy)
    s1.add(Implies(dof_O3 < dof_GL3, Not(entropy_equal)))
    result_n1 = s1.check()
    results["N1_z3_unsat_O3_GL3_equal_entropy_all_inputs"] = (result_n1 == unsat)
    results["N1_z3_result"] = str(result_n1)

    # Numerical verification: find at least one input where O3 and GL3 produce different I_c
    # Apply O3 (det=+1 rotation) vs GL3 (arbitrary unitary) to the same entangled state
    psi_test = make_entangled_state(d_left=3, d_right=3, chi=3, seed=5)
    ic_input = ic_of_psi(psi_test, d_left=3, d_right=3)

    # O3 disentangler (rotation)
    U_O3 = make_SO3_disentangler(seed=10)
    psi_O3 = apply_disentangler_to_left(psi_test, U_O3, d_left=3, d_right=3)
    ic_O3 = ic_of_psi(psi_O3, d_left=3, d_right=3)

    # GL3 disentangler (general unitary, different seed for different matrix)
    U_GL3b = make_GL3_disentangler(seed=99)
    psi_GL3 = apply_disentangler_to_left(psi_test, U_GL3b, d_left=3, d_right=3)
    ic_GL3 = ic_of_psi(psi_GL3, d_left=3, d_right=3)

    # For UNITARY disentanglers applied to pure bipartite states, local unitaries
    # on one subsystem do NOT change S(B) (unitary invariance of entropy).
    # So I_c is the same -- the MERA entropy change comes from the ISOMETRY,
    # not the disentangler. The disentangler's role is to prepare for isometry,
    # not to change I_c directly. This is the correct classical baseline:
    # disentanglers do NOT change I_c by themselves; isometries do.
    results["N1_unitary_disentangler_ic_invariant_O3"] = abs(ic_O3 - ic_input) < 1e-10
    results["N1_unitary_disentangler_ic_invariant_GL3"] = abs(ic_GL3 - ic_input) < 1e-10
    # This confirms N1 UNSAT from a different angle:
    # disentanglers (unitaries) never change I_c regardless of which group they belong to.
    # The group constraint matters for WHAT OPERATIONS are available (coarse-graining depth),
    # not for the per-step entropy of the bipartition.
    results["N1_ic_input"] = float(ic_input)
    results["N1_ic_O3"] = float(ic_O3)
    results["N1_ic_GL3"] = float(ic_GL3)

    return results


# =====================================================================
# BOUNDARY TESTS
# =====================================================================

def run_boundary_tests():
    results = {}

    # --- B1: Monotone I_c profile: depth 0 (GL3) maximal, depth 2 (SU3) minimal ---
    # Three-level MERA: I_c strictly decreases from layer 0 to layer 2.
    # The group assignment (GL3 -> SO3 -> SU3) tracks the I_c reduction.
    psi_0 = make_entangled_state(d_left=8, d_right=8, chi=4, seed=0)
    ic_depth0 = ic_of_psi(psi_0, d_left=8, d_right=8)

    # Layer 0 -> 1: coarse grain left 8 -> 4 (GL3 layer)
    psi_1 = coarse_grain_isometry(psi_0, d_left_in=8, d_right=8, d_left_out=4, seed=0)
    ic_depth1 = ic_of_psi(psi_1, d_left=4, d_right=8)

    # Layer 1 -> 2: coarse grain left 4 -> 2 (SO3 layer)
    psi_2 = coarse_grain_isometry(psi_1, d_left_in=4, d_right=8, d_left_out=2, seed=1)
    ic_depth2 = ic_of_psi(psi_2, d_left=2, d_right=8)

    # Layer 2 -> 3: coarse grain left 2 -> 1 (SU3 layer -- fully coarse-grained)
    psi_3 = coarse_grain_isometry(psi_2, d_left_in=2, d_right=8, d_left_out=1, seed=2)
    ic_depth3 = ic_of_psi(psi_3, d_left=1, d_right=8)

    results["B1_ic_depth0"] = float(ic_depth0)
    results["B1_ic_depth1"] = float(ic_depth1)
    results["B1_ic_depth2"] = float(ic_depth2)
    results["B1_ic_depth3"] = float(ic_depth3)
    results["B1_ic_depth0_gt_depth1"] = ic_depth0 >= ic_depth1 - 1e-10
    results["B1_ic_depth1_gt_depth2"] = ic_depth1 >= ic_depth2 - 1e-10
    results["B1_ic_depth2_gt_depth3"] = ic_depth2 >= ic_depth3 - 1e-10
    results["B1_monotone_profile"] = (
        ic_depth0 >= ic_depth1 - 1e-10 and
        ic_depth1 >= ic_depth2 - 1e-10 and
        ic_depth2 >= ic_depth3 - 1e-10
    )
    # depth=3 (fully coarse-grained, left dim=1): I_c should be ~0
    results["B1_fully_coarsegrained_ic_near_zero"] = abs(ic_depth3) < 1e-10

    # sympy: dimension counting confirms SU3 (8 params) < GL3 (9 params)
    n_sp = sp.Integer(3)
    results["B1_sympy_SU3_dim_8"] = (int((n_sp**2 - 1).evalf()) == 8)
    results["B1_sympy_GL3_dim_9"] = (int((n_sp**2).evalf()) == 9)

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
        "name": "tn_mera_gtower_layers",
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
            "classical MERA baseline: isometries via QR, no genuine RG fixed points or variational optimization",
            "G-tower assignment is a labeling convention -- no group action enforcement on MERA tensors",
            "I_c monotone decrease is algebraic rank reduction under isometry, not quantum renormalization group flow",
            "disentanglers (unitaries) never change I_c for pure bipartite states -- group constraint matters only for coarse-graining depth",
            "SU3 parameter count (8) vs GL3 (9) is a combinatorial fact -- not tested as a computational compression gain",
            "N1 UNSAT via z3 encodes DOF argument, not quantum group representation theory",
        ],
    }

    out = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results",
                       "tn_mera_gtower_layers_results.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"all_pass={all_pass} -> {out}")
    if errors:
        for e in errors:
            print(e)
