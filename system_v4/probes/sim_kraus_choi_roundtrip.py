#!/usr/bin/env python3
"""
sim_kraus_choi_roundtrip.py

Independent cross-check of the Kraus<->Choi roundtrip for 1-qubit channels,
using the column-major (Fortran) reshape convention.

Claim under test:
  Path 1: Kraus ops -> Choi matrix J_E -> recover Kraus via eigh -> apply to state
  Path 2: Kraus ops -> apply to state directly
  These two paths must agree (max entry-wise error < 1e-8) on all test states.

Convention:
  J_E[2i+a, 2j+b] = <a|E(|i><j|)|b>
  Row/col ordering: (i=0,a=0), (i=0,a=1), (i=1,a=0), (i=1,a=1)

Channel under test: amplitude damping, gamma=0.4
  K0 = [[1,0],[0,sqrt(1-gamma)]]  = [[1,0],[0,sqrt(0.6)]]
  K1 = [[0,sqrt(gamma)],[0,0]]    = [[0,sqrt(0.4)],[0,0]]

Expected J_E (analytically):
  [[1,          0,  0,      sqrt(0.6)],
   [0,          0,  0,      0        ],
   [0,          0,  0.4,    0        ],
   [sqrt(0.6),  0,  0,      0.6      ]]

Kraus recovery from J_E:
  Eigendecompose J_E (eigh), keep eigenpairs with eigenvalue > tol.
  K_k = sqrt(lambda_k) * v_k.reshape(2, 2, order='F')

Classification: classical_baseline (numpy only; torch tried for cross-check)
"""

import json
import os
import numpy as np
classification = "classical_baseline"  # auto-backfill

# =====================================================================
# TOOL MANIFEST
# =====================================================================

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": "optional eigendecomposition parity cross-check against the numpy path"},
    "pyg": {"tried": False, "used": False, "reason": "not relevant: no graph structure in a Kraus/Choi roundtrip"},
    "z3": {"tried": False, "used": False, "reason": "not needed: this baseline checks operator consistency, not satisfiability"},
    "cvc5": {"tried": False, "used": False, "reason": "not needed: no SMT proof surface in this baseline"},
    "sympy": {"tried": False, "used": False, "reason": "optional symbolic sanity check for trace and determinant"},
    "clifford": {"tried": False, "used": False, "reason": "not relevant: no Clifford algebra structure in this channel probe"},
    "geomstats": {"tried": False, "used": False, "reason": "not relevant: no manifold-geometry computation in this baseline"},
    "e3nn": {"tried": False, "used": False, "reason": "not relevant: no equivariant tensor field in this baseline"},
    "rustworkx": {"tried": False, "used": False, "reason": "not relevant: no graph routing or combinatorics in this baseline"},
    "xgi": {"tried": False, "used": False, "reason": "not relevant: no hypergraph structure in this baseline"},
    "toponetx": {"tried": False, "used": False, "reason": "not relevant: no topological complex surface in this baseline"},
    "gudhi": {"tried": False, "used": False, "reason": "not relevant: no persistent homology surface in this baseline"},
}

TOOL_INTEGRATION_DEPTH = {
    "pytorch": None,
    "pyg": None,
    "z3": None,
    "cvc5": None,
    "sympy": None,
    "clifford": None,
    "geomstats": None,
    "e3nn": None,
    "rustworkx": None,
    "xgi": None,
    "toponetx": None,
    "gudhi": None,
}

CLASSIFICATION = "classical_baseline"
CLASSIFICATION_NOTE = (
    "Baseline 1-qubit channel-identity probe for the Kraus<->Choi roundtrip. "
    "Confirms the F-order reshape convention, trace-preserving partial-trace check, "
    "negative controls for wrong reshape / non-CP / non-TP matrices, and boundary "
    "behavior across amplitude-damping extremes."
)
LEGO_IDS = ["kraus_choi_roundtrip"]
PRIMARY_LEGO_IDS = ["kraus_choi_roundtrip"]

# --- Try imports ---

try:
    import torch
    TOOL_MANIFEST["pytorch"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["pytorch"]["reason"] = "not installed"

try:
    import torch_geometric  # noqa: F401
    TOOL_MANIFEST["pyg"]["tried"] = True
    TOOL_MANIFEST["pyg"]["reason"] = (
        "Availability check only; graph tooling is not used in the Kraus/Choi algebra path"
    )
except ImportError:
    TOOL_MANIFEST["pyg"]["reason"] = "not installed"

try:
    from z3 import *  # noqa: F401,F403
    TOOL_MANIFEST["z3"]["tried"] = True
    TOOL_MANIFEST["z3"]["reason"] = (
        "Availability check only; this probe uses direct linear algebra rather than SMT constraints"
    )
except ImportError:
    TOOL_MANIFEST["z3"]["reason"] = "not installed"

try:
    import cvc5  # noqa: F401
    TOOL_MANIFEST["cvc5"]["tried"] = True
    TOOL_MANIFEST["cvc5"]["reason"] = (
        "Availability check only; no satisfiability proof surface is needed for this roundtrip"
    )
except ImportError:
    TOOL_MANIFEST["cvc5"]["reason"] = "not installed"

try:
    import sympy as sp
    TOOL_MANIFEST["sympy"]["tried"] = True
except ImportError:
    sp = None
    TOOL_MANIFEST["sympy"]["reason"] = "not installed"

try:
    from clifford import Cl  # noqa: F401
    TOOL_MANIFEST["clifford"]["tried"] = True
    TOOL_MANIFEST["clifford"]["reason"] = (
        "Availability check only; Clifford algebra is not part of the channel/Choi calculation"
    )
except ImportError:
    TOOL_MANIFEST["clifford"]["reason"] = "not installed"

try:
    import geomstats  # noqa: F401
    TOOL_MANIFEST["geomstats"]["tried"] = True
    TOOL_MANIFEST["geomstats"]["reason"] = (
        "Availability check only; no manifold package is required for the 2x2 Choi construction"
    )
except ImportError:
    TOOL_MANIFEST["geomstats"]["reason"] = "not installed"

try:
    import e3nn  # noqa: F401
    TOOL_MANIFEST["e3nn"]["tried"] = True
    TOOL_MANIFEST["e3nn"]["reason"] = (
        "Availability check only; equivariant neural components are not used in this baseline"
    )
except ImportError:
    TOOL_MANIFEST["e3nn"]["reason"] = "not installed"

try:
    import rustworkx  # noqa: F401
    TOOL_MANIFEST["rustworkx"]["tried"] = True
    TOOL_MANIFEST["rustworkx"]["reason"] = (
        "Availability check only; no graph rewrites or graph search are used here"
    )
except ImportError:
    TOOL_MANIFEST["rustworkx"]["reason"] = "not installed"

try:
    import xgi  # noqa: F401
    TOOL_MANIFEST["xgi"]["tried"] = True
    TOOL_MANIFEST["xgi"]["reason"] = (
        "Availability check only; hypergraph tooling is outside the scope of this channel probe"
    )
except ImportError:
    TOOL_MANIFEST["xgi"]["reason"] = "not installed"

try:
    from toponetx.classes import CellComplex  # noqa: F401
    TOOL_MANIFEST["toponetx"]["tried"] = True
    TOOL_MANIFEST["toponetx"]["reason"] = (
        "Availability check only; cell-complex structure is not used in the roundtrip check"
    )
except ImportError:
    TOOL_MANIFEST["toponetx"]["reason"] = "not installed"

try:
    import gudhi  # noqa: F401
    TOOL_MANIFEST["gudhi"]["tried"] = True
    TOOL_MANIFEST["gudhi"]["reason"] = (
        "Availability check only; persistent-homology tooling is not used in this baseline"
    )
except ImportError:
    TOOL_MANIFEST["gudhi"]["reason"] = "not installed"


# =====================================================================
# HELPERS
# =====================================================================

def apply_kraus(kraus_ops, rho):
    """Apply channel E(rho) = sum_k K_k rho K_k^dag."""
    out = np.zeros_like(rho, dtype=complex)
    for K in kraus_ops:
        out += K @ rho @ K.conj().T
    return out


def build_choi(kraus_ops, d=2):
    """
    Build Choi matrix from Kraus operators.
    Convention: J[2i+a, 2j+b] = <a|E(|i><j|)|b>
    Equivalently: J_E = sum_k (K_k ⊗ I)|Phi+><Phi+|(K_k^dag ⊗ I)
    but computed directly via E(|i><j|).
    """
    J = np.zeros((d * d, d * d), dtype=complex)
    for i in range(d):
        for j in range(d):
            # Build |i><j|
            rho_ij = np.zeros((d, d), dtype=complex)
            rho_ij[i, j] = 1.0
            E_rho = apply_kraus(kraus_ops, rho_ij)
            # Fill J[2i:2i+d, 2j:2j+d] = E(|i><j|)
            J[d * i:d * i + d, d * j:d * j + d] = E_rho
    return J


def recover_kraus_from_choi(J, d=2, tol=1e-10):
    """
    Recover Kraus operators from Choi matrix using eigendecomposition.
    K_k = sqrt(lambda_k) * v_k.reshape(d, d, order='F')
    Returns list of (d x d) Kraus operators for eigenvalues > tol.
    """
    eigenvalues, eigenvectors = np.linalg.eigh(J)
    kraus_recovered = []
    for lam, vec in zip(eigenvalues, eigenvectors.T):
        if lam > tol:
            K = np.sqrt(lam) * vec.reshape(d, d, order='F')
            kraus_recovered.append(K)
    return kraus_recovered, eigenvalues


def check_completeness(kraus_ops, d=2, tol=1e-8):
    """Check sum_k K_k^dag K_k = I (trace-preserving condition)."""
    total = np.zeros((d, d), dtype=complex)
    for K in kraus_ops:
        total += K.conj().T @ K
    return np.allclose(total, np.eye(d), atol=tol), total


def partial_trace_output(J, d=2):
    """
    Compute Tr_output(J_E) — should equal I_d for TP channel.
    Tr_output means tracing over the output (row) index.
    With convention J[d*i+a, d*j+b], Tr_output[i,j] = sum_a J[d*i+a, d*j+a]
    """
    result = np.zeros((d, d), dtype=complex)
    for i in range(d):
        for j in range(d):
            for a in range(d):
                result[i, j] += J[d * i + a, d * j + a]
    return result


def rho_from_state(psi):
    """Pure state density matrix from ket vector."""
    psi = np.array(psi, dtype=complex)
    psi = psi / np.linalg.norm(psi)
    return np.outer(psi, psi.conj())


# =====================================================================
# POSITIVE TESTS
# =====================================================================

def run_positive_tests():
    results = {}
    gamma = 0.4
    sq06 = np.sqrt(1 - gamma)   # sqrt(0.6)
    sq04 = np.sqrt(gamma)        # sqrt(0.4)

    # --- Amplitude damping Kraus operators ---
    K0 = np.array([[1, 0], [0, sq06]], dtype=complex)
    K1 = np.array([[0, sq04], [0, 0]], dtype=complex)
    kraus_original = [K0, K1]

    # --- 1. Build Choi matrix numerically ---
    J_numeric = build_choi(kraus_original)

    # --- 2. Analytic J_E for amplitude damping ---
    J_analytic = np.array([
        [1,       0,    0,    sq06],
        [0,       0,    0,    0   ],
        [0,       0,    0.4,  0   ],
        [sq06,    0,    0,    0.6 ],
    ], dtype=complex)

    choi_match = np.allclose(J_numeric, J_analytic, atol=1e-12)
    results["choi_numeric_vs_analytic"] = {
        "J_numeric": J_numeric.tolist(),
        "J_analytic": J_analytic.tolist(),
        "match": bool(choi_match),
        "max_diff": float(np.max(np.abs(J_numeric - J_analytic))),
    }

    # --- 3. Eigenvalues of J_E ---
    eigenvalues_analytic, _ = np.linalg.eigh(J_analytic)
    all_nonneg = bool(np.all(eigenvalues_analytic >= -1e-12))
    results["choi_eigenvalues"] = {
        "eigenvalues": eigenvalues_analytic.tolist(),
        "all_nonneg": all_nonneg,
        "min_eigenvalue": float(np.min(eigenvalues_analytic)),
    }

    # --- 4. Partial trace check: Tr_output(J_E) = I_2 ---
    pt = partial_trace_output(J_analytic)
    tp_check = np.allclose(pt, np.eye(2), atol=1e-12)
    results["partial_trace_check"] = {
        "Tr_output_J": pt.tolist(),
        "equals_I2": bool(tp_check),
        "max_diff_from_I": float(np.max(np.abs(pt - np.eye(2)))),
    }

    # --- 5. Recover Kraus from Choi (F-order reshape) ---
    kraus_recovered, eigs_used = recover_kraus_from_choi(J_analytic)
    tp_ok, completeness_sum = check_completeness(kraus_recovered)
    results["kraus_recovery"] = {
        "num_recovered_ops": len(kraus_recovered),
        "completeness_sum": completeness_sum.tolist(),
        "trace_preserving": bool(tp_ok),
        "eigenvalues_used": eigs_used.tolist(),
    }

    # --- 6. Roundtrip on test states ---
    # Test states: |0>, |1>, |+>, mixed rho=I/2, partial mix
    test_states = {
        "ket_0": rho_from_state([1, 0]),
        "ket_1": rho_from_state([0, 1]),
        "ket_plus": rho_from_state([1, 1]) / 1,  # normalised inside rho_from_state
        "mixed_I_over_2": np.eye(2, dtype=complex) / 2,
        "partial_mix": 0.7 * rho_from_state([1, 0]) + 0.3 * rho_from_state([0, 1]),
    }

    roundtrip_results = {}
    max_global_err = 0.0
    for name, rho in test_states.items():
        out_original = apply_kraus(kraus_original, rho)
        out_recovered = apply_kraus(kraus_recovered, rho)
        diff = np.max(np.abs(out_original - out_recovered))
        max_global_err = max(max_global_err, float(diff))
        roundtrip_results[name] = {
            "max_entry_error": float(diff),
            "pass": bool(diff < 1e-8),
            "output_original": out_original.tolist(),
            "output_recovered": out_recovered.tolist(),
        }

    results["roundtrip_test_states"] = roundtrip_results
    results["roundtrip_max_global_error"] = max_global_err
    results["roundtrip_pass"] = bool(max_global_err < 1e-8)

    return results


# =====================================================================
# NEGATIVE TESTS
# =====================================================================

def run_negative_tests():
    """
    Negative tests: confirm that the wrong reshape order (C-order) produces
    different (incorrect) Kraus operators that fail the roundtrip.
    Also confirm that a non-CP matrix (negative eigenvalue) is detected.
    """
    results = {}
    gamma = 0.4
    sq06 = np.sqrt(1 - gamma)
    sq04 = np.sqrt(gamma)

    K0 = np.array([[1, 0], [0, sq06]], dtype=complex)
    K1 = np.array([[0, sq04], [0, 0]], dtype=complex)
    kraus_original = [K0, K1]

    J_analytic = np.array([
        [1,    0,   0,   sq06],
        [0,    0,   0,   0   ],
        [0,    0,   0.4, 0   ],
        [sq06, 0,   0,   0.6 ],
    ], dtype=complex)

    # --- Neg-1: C-order reshape should give wrong roundtrip ---
    eigenvalues, eigenvectors = np.linalg.eigh(J_analytic)
    tol = 1e-10
    kraus_c_order = []
    for lam, vec in zip(eigenvalues, eigenvectors.T):
        if lam > tol:
            K = np.sqrt(lam) * vec.reshape(2, 2, order='C')  # Wrong order
            kraus_c_order.append(K)

    rho_test = np.eye(2, dtype=complex) / 2
    out_original = apply_kraus(kraus_original, rho_test)
    out_c_order = apply_kraus(kraus_c_order, rho_test)
    diff_c = float(np.max(np.abs(out_original - out_c_order)))

    results["wrong_reshape_order_C"] = {
        "description": "C-order (row-major) reshape should give DIFFERENT result from correct channel",
        "max_entry_error_from_correct": diff_c,
        "is_different_from_correct": bool(diff_c > 1e-6),
        "pass": bool(diff_c > 1e-6),  # We EXPECT a difference here
    }

    # --- Neg-2: Non-CP matrix (perturb J to have negative eigenvalue) ---
    J_bad = J_analytic.copy()
    J_bad[1, 1] = -0.1  # Break PSD
    eigs_bad = np.linalg.eigvalsh(J_bad)
    has_negative = bool(np.any(eigs_bad < -1e-10))
    results["non_cp_detection"] = {
        "description": "Perturbed J with J[1,1]=-0.1 should have negative eigenvalue",
        "eigenvalues": eigs_bad.tolist(),
        "has_negative_eigenvalue": has_negative,
        "pass": has_negative,
    }

    # --- Neg-3: Non-TP check — scale J by 0.9 ---
    J_scaled = 0.9 * J_analytic
    pt_scaled = np.array([
        [J_scaled[0, 0] + J_scaled[1, 1], J_scaled[0, 2] + J_scaled[1, 3]],
        [J_scaled[2, 0] + J_scaled[3, 1], J_scaled[2, 2] + J_scaled[3, 3]],
    ])
    # Use the proper partial_trace_output function
    pt_correct = np.zeros((2, 2), dtype=complex)
    for i in range(2):
        for j in range(2):
            for a in range(2):
                pt_correct[i, j] += J_scaled[2 * i + a, 2 * j + a]

    equals_I = np.allclose(pt_correct, np.eye(2), atol=1e-10)
    results["non_tp_detection"] = {
        "description": "0.9*J_E should NOT be trace-preserving",
        "Tr_output_of_scaled_J": pt_correct.tolist(),
        "equals_I2": bool(equals_I),
        "pass": bool(not equals_I),  # We EXPECT it to NOT equal I
    }

    return results


# =====================================================================
# BOUNDARY TESTS
# =====================================================================

def run_boundary_tests():
    """
    Boundary tests:
    - gamma=0: identity channel — J_E = maximally entangled state projector / 2
    - gamma=1: complete damping — all population goes to |0>
    - gamma=0.5: balanced case
    - Rank of recovered Kraus set
    """
    results = {}

    for gamma, label in [(0.0, "gamma_0_identity"), (1.0, "gamma_1_full_damp"), (0.5, "gamma_0p5")]:
        sq_comp = np.sqrt(1 - gamma)
        sq_gam = np.sqrt(gamma)
        K0 = np.array([[1, 0], [0, sq_comp]], dtype=complex)
        K1 = np.array([[0, sq_gam], [0, 0]], dtype=complex)
        kraus = [K0, K1]

        J = build_choi(kraus)
        eigs = np.linalg.eigvalsh(J)
        kraus_rec, _ = recover_kraus_from_choi(J)
        tp_ok, _ = check_completeness(kraus_rec)

        # Roundtrip on |+> state
        rho_plus = rho_from_state([1, 1])
        out_orig = apply_kraus(kraus, rho_plus)
        out_rec = apply_kraus(kraus_rec, rho_plus)
        diff = float(np.max(np.abs(out_orig - out_rec)))

        results[label] = {
            "gamma": gamma,
            "choi_eigenvalues": eigs.tolist(),
            "all_nonneg": bool(np.all(eigs >= -1e-12)),
            "num_kraus_recovered": len(kraus_rec),
            "trace_preserving_after_recovery": bool(tp_ok),
            "roundtrip_max_error_ket_plus": diff,
            "roundtrip_pass": bool(diff < 1e-8),
        }

    # --- Sympy cross-check for gamma=0.4 if available ---
    if sp is not None:
        gamma_sym = sp.Rational(2, 5)
        sq06_sym = sp.sqrt(1 - gamma_sym)
        J_sym = sp.Matrix([
            [1, 0, 0, sq06_sym],
            [0, 0, 0, 0],
            [0, 0, sp.Rational(2, 5), 0],
            [sq06_sym, 0, 0, sp.Rational(3, 5)],
        ])
        trace_sym = J_sym.trace()
        det_sym = J_sym.det()
        TOOL_MANIFEST["sympy"]["used"] = True
        TOOL_MANIFEST["sympy"]["reason"] = (
            "Symbolic cross-check of Choi matrix trace and determinant for gamma=2/5"
        )
        TOOL_INTEGRATION_DEPTH["sympy"] = "load_bearing"

        results["sympy_crosscheck_gamma_0p4"] = {
            "trace_J_sym": str(trace_sym),
            "det_J_sym": str(det_sym),
            "trace_equals_2": bool(trace_sym == 2),
            "pass": bool(trace_sym == 2 and det_sym == 0),
        }

    return results


# =====================================================================
# PYTORCH CROSS-CHECK (if available)
# =====================================================================

def run_pytorch_crosscheck():
    """
    Use torch.linalg.eigh to replicate the eigendecomposition.
    Result must agree with numpy path within float32 tolerance.
    """
    try:
        import torch  # local import to isolate
        gamma = 0.4
        sq06 = np.sqrt(0.6)
        J_np = np.array([
            [1, 0, 0, sq06],
            [0, 0, 0, 0],
            [0, 0, 0.4, 0],
            [sq06, 0, 0, 0.6],
        ], dtype=np.float64)
        J_t = torch.tensor(J_np, dtype=torch.float64)
        eigs_t, vecs_t = torch.linalg.eigh(J_t)
        eigs_np = np.linalg.eigvalsh(J_np)
        diff = float(torch.max(torch.abs(eigs_t - torch.tensor(eigs_np))).item())
        TOOL_MANIFEST["pytorch"]["used"] = True
        TOOL_MANIFEST["pytorch"]["reason"] = (
            "torch.linalg.eigh cross-check of Choi eigendecomposition vs numpy"
        )
        TOOL_INTEGRATION_DEPTH["pytorch"] = "load_bearing"
        return {
            "eigs_torch": eigs_t.tolist(),
            "eigs_numpy": eigs_np.tolist(),
            "max_diff": diff,
            "pass": diff < 1e-8,
        }
    except Exception as e:
        return {"error": str(e)}


# =====================================================================
# MAIN
# =====================================================================

if __name__ == "__main__":
    positive = run_positive_tests()
    negative = run_negative_tests()
    boundary = run_boundary_tests()
    pytorch_xcheck = run_pytorch_crosscheck()

    results = {
        "name": "kraus_choi_roundtrip",
        "description": (
            "Independent cross-check of Kraus<->Choi roundtrip for amplitude damping "
            "channel (gamma=0.4). Verifies F-order reshape convention for Kraus recovery "
            "from Choi matrix eigendecomposition."
        ),
        "classification": CLASSIFICATION,
        "classification_note": CLASSIFICATION_NOTE,
        "lego_ids": LEGO_IDS,
        "primary_lego_ids": PRIMARY_LEGO_IDS,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "pytorch_crosscheck": pytorch_xcheck,
        "summary": {
            "roundtrip_pass": bool(positive["roundtrip_pass"]),
            "negative_controls_pass": all(v.get("pass", False) for v in negative.values()),
            "boundary_controls_pass": all(
                v.get("roundtrip_pass", v.get("pass", False)) for v in boundary.values()
            ),
            "scope_note": (
                "Baseline-only identity check for a single qubit amplitude-damping family; "
                "not a broader channel taxonomy or canonical promotion claim."
            ),
        },
    }

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "kraus_choi_roundtrip_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out_path}")
