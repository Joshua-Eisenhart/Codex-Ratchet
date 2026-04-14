#!/usr/bin/env python3
"""Canonical: Entanglement witness on the Werner family.

Witness:  W = (1/2) I_4 - |Phi+><Phi+|
On any separable rho: Tr(W rho) >= 0.
On the maximally entangled |Phi+>: Tr(W |Phi+><Phi+|) = -1/2 < 0.

Werner family:  rho_W(p) = p |Phi+><Phi+| + (1-p)/4 * I_4
 - Entanglement via negativity: entangled iff p > 1/3.
 - Witness detects entanglement iff Tr(W rho_W(p)) < 0, i.e. iff p > 1/2.

Classical baseline: convex mixtures of product states (SEP) cannot have
Tr(W rho) < 0; any sim using only classical correlations must give Tr(W rho) >= 0.

load_bearing: sympy -- exact symbolic eigenstructure of W and the closed-form
Tr(W rho_W(p)) = 1/4 - 3p/4, giving a certified algebraic inequality rather
than a floating-point demonstration.
"""
import json
import os

import numpy as np

classification = "canonical"
divergence_log = None

TOOL_MANIFEST = {
    "numpy":   {"tried": True,  "used": True,  "reason": "numeric cross-check of Tr(W rho)"},
    "sympy":   {"tried": False, "used": False, "reason": "placeholder -- filled below"},
    "pytorch": {"tried": False, "used": False, "reason": "not required; sympy gives exact values"},
    "z3":      {"tried": False, "used": False, "reason": "not required"},
}

TOOL_INTEGRATION_DEPTH = {
    "numpy":   "supportive",
    "sympy":   "load_bearing",
    "pytorch": None,
    "z3":      None,
}

try:
    import sympy as sp
    TOOL_MANIFEST["sympy"]["tried"] = True
    TOOL_MANIFEST["sympy"]["used"] = True
    TOOL_MANIFEST["sympy"]["reason"] = (
        "exact symbolic eigendecomposition of witness W and closed-form "
        "symbolic evaluation of Tr(W rho_W(p)) = 1/4 - 3p/4"
    )
except ImportError:
    TOOL_MANIFEST["sympy"]["reason"] = "not installed"
    sp = None  # type: ignore


# ---------------------------------------------------------------------------
# Symbolic witness construction
# ---------------------------------------------------------------------------

def _witness_and_werner(p):
    """Return (W, rho_W(p)) as sympy matrices in computational basis."""
    half = sp.Rational(1, 2)
    # |Phi+> = (|00> + |11>)/sqrt(2)
    phi_plus = sp.Matrix([1, 0, 0, 1]) / sp.sqrt(2)
    P = phi_plus * phi_plus.T   # real projector
    I4 = sp.eye(4)
    # Witness: W = (1/2) I - |Phi+><Phi+|
    W = half * I4 - P
    rho = p * P + (1 - p) * sp.Rational(1, 4) * I4
    return W, rho


def _tr_W_rho(p_val):
    """Exact Tr(W rho_W(p))."""
    p = sp.symbols('p', real=True)
    W, rho = _witness_and_werner(p)
    expr = sp.trace(W * rho)
    expr = sp.simplify(expr)
    return expr, expr.subs(p, p_val)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

TOL = 1e-10


def run_positive_tests():
    results = {}
    if sp is None:
        results["sympy_available"] = False
        return results

    # Entangled (maximally): p=1 -> Tr(W rho) = 1/4 - 3/4 = -1/2
    expr, val_p1 = _tr_W_rho(sp.Integer(1))
    results["symbolic_expr_tr_W_rho"] = str(expr)
    results["tr_W_rho_at_p1"] = float(val_p1)
    results["witness_fires_on_phi_plus"] = float(val_p1) < -0.4

    # Entangled region: p=0.9 -> 1/4 - 0.675 = -0.425
    _, val_p09 = _tr_W_rho(sp.Rational(9, 10))
    results["tr_W_rho_at_p09"] = float(val_p09)
    results["witness_fires_on_strong_werner"] = float(val_p09) < -TOL

    # Exact eigenvalues of W: {1/2, 1/2, 1/2, -1/2} -> witness is trace-one, sig (+++/-)
    W, _ = _witness_and_werner(sp.symbols('p', real=True))
    eigs = sp.Matrix(list(W.eigenvals().keys()))
    eig_set = {sp.nsimplify(e) for e in eigs}
    results["witness_eigvals"] = sorted([float(e) for e in eig_set])
    results["witness_has_one_neg_eigval"] = sp.Rational(-1, 2) in eig_set
    return results


def run_negative_tests():
    results = {}
    if sp is None:
        results["sympy_available"] = False
        return results

    # Separable region: p <= 1/3 (necessary cond for Werner separability by PPT
    # is p <= 1/3). Here we only assert that the witness (W = I/2 - |Phi+><Phi+|)
    # is nonnegative on the maximally mixed state rho = I/4 (a separable state).
    _, val_p0 = _tr_W_rho(sp.Integer(0))
    results["tr_W_rho_at_p0"] = float(val_p0)
    results["witness_nonneg_on_maxmixed"] = float(val_p0) >= -TOL

    # Pure product state |00>: rho = diag(1,0,0,0). Tr(W rho) = W[0,0] = 1/2 - 1/2 = 0
    # (because <00|Phi+> = 1/sqrt(2) -> |<.>|^2 = 1/2, so Tr = 1/2 - 1/2 = 0)
    rho_prod = sp.zeros(4, 4)
    rho_prod[0, 0] = 1
    W, _ = _witness_and_werner(sp.symbols('p', real=True))
    tr_prod = sp.simplify(sp.trace(W * rho_prod))
    results["tr_W_rho_product_00"] = float(tr_prod)
    results["witness_nonneg_on_product_state"] = float(tr_prod) >= -TOL

    # |01>: <01|Phi+> = 0 -> Tr = 1/2
    rho01 = sp.zeros(4, 4); rho01[1, 1] = 1
    tr_01 = sp.simplify(sp.trace(W * rho01))
    results["tr_W_rho_product_01"] = float(tr_01)
    results["witness_strict_pos_on_01"] = float(tr_01) > TOL
    return results


def run_boundary_tests():
    results = {}
    if sp is None:
        results["sympy_available"] = False
        return results

    # Witness-detection threshold: Tr(W rho_W(p)) = 1/4 - 3p/4 < 0  <=>  p > 1/3
    # (the entanglement witness here detects exactly p > 1/3; note negativity
    # of rho_W is nonzero iff p > 1/3 as well, so this witness is optimal on
    # the Werner family.)
    _, val_third = _tr_W_rho(sp.Rational(1, 3))
    results["tr_W_rho_at_p_third"] = float(val_third)
    results["witness_zero_at_threshold"] = abs(float(val_third)) <= TOL

    # Scan p values and count sign changes.
    scan = {}
    for num in [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]:
        p_val = sp.Rational(num, 10)
        _, v = _tr_W_rho(p_val)
        scan[f"p={float(p_val):.1f}"] = float(v)
    results["scan_tr_W_rho"] = scan
    neg_count = sum(1 for v in scan.values() if v < -TOL)
    pos_count = sum(1 for v in scan.values() if v > TOL)
    results["scan_has_neg_and_pos"] = neg_count > 0 and pos_count > 0

    # Numeric cross-check with numpy.
    phi = np.array([1, 0, 0, 1], dtype=complex) / np.sqrt(2)
    P = np.outer(phi, phi.conj())
    W = 0.5 * np.eye(4) - P
    rho_np = 0.9 * P + 0.1 * np.eye(4) / 4.0
    tr_np = float(np.trace(W @ rho_np).real)
    results["numpy_cross_check_tr_W_rho_p09"] = tr_np
    results["cross_check_matches_sympy"] = abs(tr_np - float(scan["p=0.9"])) < 1e-10
    return results


def _all_bool_pass(d):
    for v in d.values():
        if isinstance(v, bool) and not v:
            return False
    return True


if __name__ == "__main__":
    pos = run_positive_tests()
    neg = run_negative_tests()
    bnd = run_boundary_tests()

    all_pass = _all_bool_pass(pos) and _all_bool_pass(neg) and _all_bool_pass(bnd)

    gap = {
        "classical_separable_bound": "Tr(W rho_sep) >= 0 for all separable rho",
        "measured_tr_W_phi_plus": pos.get("tr_W_rho_at_p1"),
        "witness_expectation_gap": -pos.get("tr_W_rho_at_p1", 0.0),
        "werner_detection_threshold_p": 1.0 / 3.0,
    }

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "werner_entanglement_witness_canonical_results.json")

    payload = {
        "name": "werner_entanglement_witness_canonical",
        "classification": classification,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos,
        "negative": neg,
        "boundary": bnd,
        "all_pass": all_pass,
        "summary": {
            "all_pass": all_pass,
            "gap": gap,
            "classical_baseline_cited": "separable/LHV states satisfy Tr(W rho)>=0 (witness)",
            "measured_quantum_value": pos.get("tr_W_rho_at_p1"),
        },
    }
    with open(out_path, "w") as f:
        json.dump(payload, f, indent=2, default=str)
    print(f"all_pass={all_pass} Tr(W|Phi+>)={pos.get('tr_W_rho_at_p1')} -> {out_path}")
