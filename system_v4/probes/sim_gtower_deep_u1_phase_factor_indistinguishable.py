#!/usr/bin/env python3
"""sim_gtower_deep_u1_phase_factor_indistinguishable -- Deep G-tower lego.

Claim (admissibility, distinguishability):
  Global U(1) phase e^{i*theta} on a pure state is INDISTINGUISHABLE
  under any self-adjoint probe <psi|A|psi>. Candidates differing only
  by a global phase are not separated by probes (admissibility equivalence).

scope_note: LADDERS_FENCES_ADMISSION_REFERENCE.md -- U(1) global-phase fence.
"""
import json, os
import numpy as np

TOOL_MANIFEST = {k: {"tried": False, "used": False, "reason": ""} for k in
    ["pytorch","pyg","z3","cvc5","sympy","clifford","geomstats","e3nn","rustworkx","xgi","toponetx","gudhi"]}
TOOL_INTEGRATION_DEPTH = {k: None for k in TOOL_MANIFEST}

try:
    import sympy as sp
    TOOL_MANIFEST["sympy"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["sympy"]["reason"] = "not installed"


def run_positive_tests():
    r = {}
    theta, a, b = sp.symbols('theta a b', real=True)
    psi = sp.Matrix([a, b])
    phase = sp.exp(sp.I*theta)
    psi2 = phase * psi
    # self-adjoint probe sigma_z
    sz = sp.Matrix([[1,0],[0,-1]])
    exp1 = (psi.H * sz * psi)[0]
    exp2 = (psi2.H * sz * psi2)[0]
    diff = sp.simplify(exp1 - exp2)
    r["sigma_z_indistinguishable"] = {"diff": str(diff), "pass": diff == 0}
    # sigma_x
    sx = sp.Matrix([[0,1],[1,0]])
    diff_x = sp.simplify((psi.H*sx*psi)[0] - (psi2.H*sx*psi2)[0])
    r["sigma_x_indistinguishable"] = {"diff": str(diff_x), "pass": diff_x == 0}
    # identity expectation: norm preserved
    n_diff = sp.simplify((psi.H*psi)[0] - (psi2.H*psi2)[0])
    r["norm_preserved"] = {"pass": n_diff == 0}
    return r


def run_negative_tests():
    r = {}
    # RELATIVE phase IS distinguishable
    theta = sp.symbols('theta', real=True)
    psi = sp.Matrix([1, 1]) / sp.sqrt(2)
    psi2 = sp.Matrix([1, sp.exp(sp.I*theta)]) / sp.sqrt(2)
    sx = sp.Matrix([[0,1],[1,0]])
    diff = sp.simplify((psi.H*sx*psi)[0] - (psi2.H*sx*psi2)[0])
    # differ generically (not identically zero)
    r["relative_phase_distinguishable"] = {"diff": str(diff), "pass": sp.simplify(diff) != 0}
    return r


def run_boundary_tests():
    r = {}
    # theta = 0: trivially equal
    psi = sp.Matrix([sp.Rational(1,2), sp.Rational(1,2)])
    psi2 = sp.exp(sp.I*0) * psi
    r["theta_zero_identity"] = {"pass": psi == psi2}
    # theta = 2*pi: returns to same state
    psi3 = sp.exp(sp.I*2*sp.pi) * psi
    r["theta_2pi_period"] = {"pass": sp.simplify(psi3 - psi) == sp.zeros(2,1)}
    return r


if __name__ == "__main__":
    TOOL_MANIFEST["sympy"]["used"] = True
    TOOL_MANIFEST["sympy"]["reason"] = "symbolic expectation values decide U(1) phase indistinguishability"
    TOOL_INTEGRATION_DEPTH["sympy"] = "load_bearing"
    results = {
        "name": "sim_gtower_deep_u1_phase_factor_indistinguishable",
        "scope_note": "LADDERS_FENCES_ADMISSION_REFERENCE.md: U(1) global-phase fence",
        "language": "global phase: indistinguishable; relative phase: distinguishable",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": run_positive_tests(),
        "negative": run_negative_tests(),
        "boundary": run_boundary_tests(),
        "classification": "canonical",
    }
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out = os.path.join(out_dir, "sim_gtower_deep_u1_phase_factor_indistinguishable_results.json")
    with open(out, "w") as f: json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out}")
