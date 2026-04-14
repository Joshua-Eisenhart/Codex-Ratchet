#!/usr/bin/env python3
"""
SA12 — Wilczek-Zee Curvature Probe: Symbolic Cross-Checks
==========================================================

Two sympy-level proofs about F_θφ = ∂_θA_φ - ∂_φA_θ + [A_θ, A_φ]:

  (S1) Tr([A, B]) = 0  →  Tr(F_θφ) = ∂_θTr(A_φ) - ∂_φTr(A_θ)
  (S2) Anti-Hermitian inheritance: A†=-A, B†=-B  ⟹  [A,B]† = -[A,B]

Plus a numerical cross-check that Tr(F_θφ) agrees with the abelian
derivative ∂_θTr(A_φ) - ∂_φTr(A_θ) to < 1e-8.

Classification: canonical
Output: sim_results/SA12_wilczek_zee_curvature_sympy_results.json
"""

import json
import os
import time
import traceback
classification = "canonical"

# =====================================================================
# TOOL MANIFEST
# =====================================================================

TOOL_MANIFEST = {
    "pytorch":   {"tried": True,  "used": True,
                  "reason": "Numerical ground-truth for connection A_θ, A_φ and Tr(F) cross-check"},
    "pyg":       {"tried": False, "used": False, "reason": "not needed — no graph structure"},
    "z3":        {"tried": False, "used": False, "reason": "not needed — algebraic identity, not constraint sat"},
    "cvc5":      {"tried": False, "used": False, "reason": "not needed"},
    "sympy":     {"tried": True,  "used": True,
                  "reason": "Load-bearing: symbolic proof of Tr([A,B])=0 and anti-Hermitian commutator inheritance"},
    "clifford":  {"tried": False, "used": False, "reason": "not needed"},
    "geomstats": {"tried": False, "used": False, "reason": "not needed"},
    "e3nn":      {"tried": False, "used": False, "reason": "not needed"},
    "rustworkx": {"tried": False, "used": False, "reason": "not needed"},
    "xgi":       {"tried": False, "used": False, "reason": "not needed"},
    "toponetx":  {"tried": False, "used": False, "reason": "not needed"},
    "gudhi":     {"tried": False, "used": False, "reason": "not needed"},
}

TOOL_INTEGRATION_DEPTH = {
    "pytorch":   "supportive",
    "sympy":     "load_bearing",
    "pyg":       None, "z3": None, "cvc5": None,
    "clifford":  None, "geomstats": None, "e3nn": None,
    "rustworkx": None, "xgi": None, "toponetx": None, "gudhi": None,
}

import sympy as sp
import torch
torch.set_default_dtype(torch.float64)

# Re-use connection utilities from the main Wilczek-Zee probe.
import sys, importlib.util
_probe_dir = os.path.dirname(__file__)
_wz_path   = os.path.join(_probe_dir, "sim_lego_wilczek_zee.py")
_spec = importlib.util.spec_from_file_location("wz_lego", _wz_path)
_wz = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_wz)
compute_connection = _wz.compute_connection


# =====================================================================
# POSITIVE TESTS
# =====================================================================

def run_positive_tests():
    results = {}
    t0 = time.time()

    # ------------------------------------------------------------------
    # S1: Tr([A, B]) = 0  for ANY 2×2 matrices (symbolic proof)
    # ------------------------------------------------------------------
    try:
        a11, a12, a21, a22 = sp.symbols("a11 a12 a21 a22")
        b11, b12, b21, b22 = sp.symbols("b11 b12 b21 b22")
        A = sp.Matrix([[a11, a12], [a21, a22]])
        B = sp.Matrix([[b11, b12], [b21, b22]])
        C = A * B - B * A                   # commutator
        tr_C = sp.trace(C)                  # must simplify to 0
        tr_simplified = sp.simplify(tr_C)
        is_zero = tr_simplified == 0

        results["S1_trace_commutator_zero"] = {
            "pass": is_zero,
            "tr_commutator_simplified": str(tr_simplified),
            "interpretation": (
                "Tr([A,B])=0 ⟹ Tr(F_θφ)=∂_θTr(A_φ)-∂_φTr(A_θ) "
                "(abelian curvature = full trace)"
            ),
        }
    except Exception:
        results["S1_trace_commutator_zero"] = {"pass": False, "error": traceback.format_exc()}

    # ------------------------------------------------------------------
    # S2: Anti-Hermitian inheritance  [A,B]† = -[A,B]
    #     when A†=-A, B†=-B
    #     Proof path: (AB)†=B†A† = (-B)(-A) = BA; (BA)†=AB; so (AB-BA)†=BA-AB=-[A,B]
    # ------------------------------------------------------------------
    try:
        # Use concrete anti-Hermitian parametrisation:
        #   A = i * [[r, s+it], [s-it, -r]]    (r,s,t real)
        #   B = i * [[p, q+iu], [q-iu, -p]]
        r, s, t, p, q, u = sp.symbols("r s t p q u", real=True)
        i = sp.I
        A_ah = i * sp.Matrix([[r,     s + i*t],
                               [s - i*t,   -r]])
        B_ah = i * sp.Matrix([[p,     q + i*u],
                               [q - i*u,   -p]])

        comm_ah = A_ah * B_ah - B_ah * A_ah
        comm_dag = comm_ah.conjugate().T          # † = conj-transpose
        residual = sp.simplify(comm_dag + comm_ah)  # should be zero matrix if [A,B]†=-[A,B]
        is_antiherm = residual == sp.zeros(2, 2)

        # Fallback: check every element individually
        if not is_antiherm:
            is_antiherm = all(
                sp.simplify(residual[i_, j_]) == 0
                for i_ in range(2) for j_ in range(2)
            )

        results["S2_antiherm_inheritance"] = {
            "pass": is_antiherm,
            "residual_matrix": str(residual),
            "interpretation": (
                "[A,B]†=-[A,B] confirmed: F_θφ ∈ u(2) when A_θ,A_φ ∈ u(2)"
            ),
        }
    except Exception:
        results["S2_antiherm_inheritance"] = {"pass": False, "error": traceback.format_exc()}

    results["elapsed_s"] = time.time() - t0
    return results


# =====================================================================
# NEGATIVE TESTS
# =====================================================================

def run_negative_tests():
    results = {}
    t0 = time.time()

    # ------------------------------------------------------------------
    # N1: Tr([A, B]) ≠ 0 for INDIVIDUAL terms AB or BA (sanity)
    #     Confirms we are checking the right thing: commutator, not product.
    # ------------------------------------------------------------------
    try:
        a11, a12, a21, a22 = sp.symbols("a11 a12 a21 a22")
        b11, b12, b21, b22 = sp.symbols("b11 b12 b21 b22")
        A = sp.Matrix([[a11, a12], [a21, a22]])
        B = sp.Matrix([[b11, b12], [b21, b22]])
        tr_AB = sp.trace(A * B)
        # Tr(AB) generally ≠ 0 → ensure it's not identically zero
        is_nonzero = sp.simplify(tr_AB) != 0
        results["N1_tr_AB_not_identically_zero"] = {
            "pass": is_nonzero,
            "tr_AB": str(sp.simplify(tr_AB)),
            "note": "Confirms Tr(AB)≠0 in general, so Tr([A,B])=0 is non-trivial",
        }
    except Exception:
        results["N1_tr_AB_not_identically_zero"] = {"pass": False, "error": traceback.format_exc()}

    # ------------------------------------------------------------------
    # N2: Non-anti-Hermitian matrix does NOT produce [A,B]†=-[A,B]
    #     Use a general complex matrix; expect residual ≠ 0.
    # ------------------------------------------------------------------
    try:
        a, b, c, d = sp.symbols("a b c d")
        A_gen = sp.Matrix([[a, b], [c, d]])       # NOT constrained anti-Hermitian
        B_gen = sp.Matrix([[1, 0], [0, -1]])       # fixed reference
        comm_gen = A_gen * B_gen - B_gen * A_gen
        comm_gen_dag = comm_gen.conjugate().T
        residual_gen = sp.simplify(comm_gen_dag + comm_gen)
        is_nonzero_residual = residual_gen != sp.zeros(2, 2)
        results["N2_noantiherm_no_inheritance"] = {
            "pass": is_nonzero_residual,
            "residual_sample": str(residual_gen[0, 1]),
            "note": "General A does not guarantee [A,B]† = -[A,B]",
        }
    except Exception:
        results["N2_noantiherm_no_inheritance"] = {"pass": False, "error": traceback.format_exc()}

    results["elapsed_s"] = time.time() - t0
    return results


# =====================================================================
# BOUNDARY TESTS
# =====================================================================

def run_boundary_tests():
    results = {}
    t0 = time.time()

    # ------------------------------------------------------------------
    # B1: Numerical Tr(F_θφ) vs ∂_θTr(A_φ) - ∂_φTr(A_θ)  < 1e-8
    #     The symbolic S1 proof guarantees this; numerical check confirms
    #     the connection code is consistent.
    # ------------------------------------------------------------------
    try:
        eps = 1e-5
        theta0, phi0 = 0.7, 0.5

        def tr_A_phi(th, ph):
            _, A_ph, _ = compute_connection(th, ph)
            return torch.trace(A_ph).real.item()

        def tr_A_theta(th, ph):
            A_th, _, _ = compute_connection(th, ph)
            return torch.trace(A_th).real.item()

        # Numerical ∂_θTr(A_φ)
        d_theta_tr_Aphi = (tr_A_phi(theta0 + eps, phi0) - tr_A_phi(theta0 - eps, phi0)) / (2 * eps)
        # Numerical ∂_φTr(A_θ)
        d_phi_tr_Atheta = (tr_A_theta(theta0, phi0 + eps) - tr_A_theta(theta0, phi0 - eps)) / (2 * eps)
        abelian_curv = d_theta_tr_Aphi - d_phi_tr_Atheta

        # Direct Tr(F_θφ) via finite diff on A components
        A_th_pp, A_ph_pp, _ = compute_connection(theta0 + eps, phi0)
        A_th_mm, A_ph_mm, _ = compute_connection(theta0 - eps, phi0)
        A_th_0p, A_ph_0p, _ = compute_connection(theta0, phi0 + eps)
        A_th_0m, A_ph_0m, _ = compute_connection(theta0, phi0 - eps)

        dA_phi_dtheta   = (A_ph_pp - A_ph_mm) / (2 * eps)
        dA_theta_dphi   = (A_th_0p - A_th_0m) / (2 * eps)
        A_th_0, A_ph_0, _ = compute_connection(theta0, phi0)
        comm_0 = A_th_0 @ A_ph_0 - A_ph_0 @ A_th_0

        F_full  = dA_phi_dtheta - dA_theta_dphi + comm_0
        tr_F    = torch.trace(F_full).real.item()
        # By S1, Tr(comm_0)=0, so tr_F should equal abelian_curv
        error   = abs(tr_F - abelian_curv)

        results["B1_numerical_trace_curvature"] = {
            "pass": error < 1e-8,
            "tr_F_numerical": tr_F,
            "abelian_deriv":  abelian_curv,
            "error":          error,
            "tolerance":      1e-8,
        }
    except Exception:
        results["B1_numerical_trace_curvature"] = {"pass": False, "error": traceback.format_exc()}

    # ------------------------------------------------------------------
    # B2: SU(2) projection — Tr(F_SU2) = 0 by construction
    #     F_SU2 = F - (Tr(F)/2) I  =>  Tr(F_SU2) = Tr(F) - Tr(F) = 0
    # ------------------------------------------------------------------
    try:
        A_th, A_ph, _ = compute_connection(0.7, 0.5)
        dA_ph_dth = (
            compute_connection(0.7 + 1e-5, 0.5)[1]
            - compute_connection(0.7 - 1e-5, 0.5)[1]
        ) / (2e-5)
        dA_th_dph = (
            compute_connection(0.7, 0.5 + 1e-5)[0]
            - compute_connection(0.7, 0.5 - 1e-5)[0]
        ) / (2e-5)
        F2 = dA_ph_dth - dA_th_dph + A_th @ A_ph - A_ph @ A_th
        tr_F2 = torch.trace(F2)
        F_su2 = F2 - (tr_F2 / 2) * torch.eye(2, dtype=torch.complex128)
        tr_F_su2 = torch.trace(F_su2).real.item()

        results["B2_su2_projection_traceless"] = {
            "pass": abs(tr_F_su2) < 1e-12,
            "tr_F_su2": tr_F_su2,
        }
    except Exception:
        results["B2_su2_projection_traceless"] = {"pass": False, "error": traceback.format_exc()}

    results["elapsed_s"] = time.time() - t0
    return results


# =====================================================================
# SUMMARY / MAIN
# =====================================================================

def build_summary(results):
    total = passed = 0
    failed = []
    for section in ("positive", "negative", "boundary"):
        for k, v in results[section].items():
            if k == "elapsed_s":
                continue
            total += 1
            if v.get("pass", False):
                passed += 1
            else:
                failed.append(k)
    return {"total": total, "passed": passed, "failed": total - passed, "failed_tests": failed}


if __name__ == "__main__":
    print("=" * 60)
    print("SA12 — Wilczek-Zee Curvature Sympy Cross-Checks")
    print("=" * 60)

    results = {
        "name":           "SA12 Wilczek-Zee Curvature Sympy Cross-Check",
        "probe":          "SA12_wilczek_zee_curvature_sympy",
        "purpose":        "Symbolic proof that Tr([A,B])=0 and [A,B]†=-[A,B] for anti-Hermitian A,B",
        "tool_manifest":  TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive":       run_positive_tests(),
        "negative":       run_negative_tests(),
        "boundary":       run_boundary_tests(),
        "classification": "canonical",
    }
    results["summary"] = build_summary(results)

    for section in ("positive", "negative", "boundary"):
        for k, v in results[section].items():
            if k == "elapsed_s":
                continue
            label = "PASS" if v.get("pass", False) else "FAIL"
            print(f"  {label}  {k}")

    s = results["summary"]
    print(f"\n{s['passed']}/{s['total']} tests passed")

    out_dir = os.path.join(_probe_dir, "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "SA12_wilczek_zee_curvature_sympy_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out_path}")
