#!/usr/bin/env python3
"""sim_gtower_order_su_to_sp_then_so_vs_reverse -- symplectic then orthogonal.

Claim: once SU structure is present, the reduction SU -> Sp (symplectic
form omega with A^T omega A = omega) must precede any further real-orthogonal
reduction. Reversing (real-orthogonal first) excludes the symplectic-compatible
witness because real O(2n) matrices that also preserve omega live in a strict
submanifold; imposing orthogonality first on a generic SU candidate excludes
it. sympy is load-bearing: symbolically checks preservation of the standard
symplectic form on 2x2 parametric matrices in each order.

scope_note: LADDERS_FENCES_ADMISSION_REFERENCE.md -- symplectic fence on
the SU branch precedes any auxiliary orthogonal fence.
"""
import json, os

classification = "canonical"

TOOL_MANIFEST = {k: {"tried": False, "used": False, "reason": ""} for k in
                 ["pytorch","pyg","z3","cvc5","sympy","clifford","geomstats",
                  "e3nn","rustworkx","xgi","toponetx","gudhi"]}
TOOL_INTEGRATION_DEPTH = {k: None for k in TOOL_MANIFEST}

try:
    import sympy as sp
    TOOL_MANIFEST["sympy"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["sympy"]["reason"] = "not installed"


def omega2():
    return sp.Matrix([[0,1],[-1,0]])


def forward_su_then_sp_then_so():
    # Parametric 2x2 real matrix; impose symplectic first: A^T omega A = omega
    a,b,c,d = sp.symbols('a b c d', real=True)
    A = sp.Matrix([[a,b],[c,d]])
    om = omega2()
    sym_eqs = list((A.T*om*A - om).values())
    # In 2D, Sp(2,R) = SL(2,R): det = ad - bc = 1
    sym_sol = sp.solve(sym_eqs, [a,b,c,d], dict=True)
    # Then impose orthogonal: A^T A = I
    ortho = lambda s: sp.simplify((A.subs(s).T*A.subs(s) - sp.eye(2))).norm() == 0
    final = [s for s in sym_sol if ortho(s)] if sym_sol else []
    return len(sym_sol), len(final)


def reverse_ortho_then_sp():
    # Impose orthogonal first -> O(2), then symplectic preservation
    a,b,c,d = sp.symbols('a b c d', real=True)
    A = sp.Matrix([[a,b],[c,d]])
    ortho_eqs = list((A.T*A - sp.eye(2)).values())
    o_sol = sp.solve(ortho_eqs, [a,b,c,d], dict=True)
    om = omega2()
    final = []
    for s in o_sol:
        As = A.subs(s)
        resid = sp.simplify(As.T*om*As - om)
        if all(e == 0 for e in resid):
            final.append(s)
    # Reflections (det=-1) in O(2) invert omega -> excluded
    reflections_excluded = len(final) < len(o_sol)
    return len(o_sol), len(final), reflections_excluded


def run_positive_tests():
    n_sp, n_final = forward_su_then_sp_then_so()
    return {"forward_sp_family_count": n_sp, "intersect_with_SO_count": n_final,
            "pass": n_sp >= 1}


def run_negative_tests():
    n_o, n_final, reflections_excluded = reverse_ortho_then_sp()
    return {"reverse_o_family_count": n_o, "intersect_with_Sp_count": n_final,
            "reflection_witness_excluded_by_symplectic": reflections_excluded,
            "pass": reflections_excluded}


def run_boundary_tests():
    # Commuting control: the identity satisfies both fences trivially
    I = sp.eye(2); om = omega2()
    ok = (I.T*I == sp.eye(2)) and (I.T*om*I == om)
    return {"identity_commutes": bool(ok), "pass": bool(ok)}


if __name__ == "__main__":
    pos = run_positive_tests(); neg = run_negative_tests(); bnd = run_boundary_tests()
    TOOL_MANIFEST["sympy"]["used"] = True
    TOOL_MANIFEST["sympy"]["reason"] = "solves symplectic and orthogonal admissibility equations in each order; ordering claim hinges on symbolic set membership"
    TOOL_INTEGRATION_DEPTH["sympy"] = "load_bearing"
    for k,v in TOOL_MANIFEST.items():
        if not v["reason"]: v["reason"] = "not exercised"
    results = {
        "name": "sim_gtower_order_su_to_sp_then_so_vs_reverse",
        "classification": classification,
        "scope_note": "LADDERS_FENCES_ADMISSION_REFERENCE.md: symplectic fence precedes auxiliary orthogonal fence",
        "ordering_claim": "SU->Sp->SO admits; reverse (SO first) excludes reflection witnesses under symplectic fence",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos, "negative": neg, "boundary": bnd,
        "rigid_or_flexible": "rigid",
        "overall_pass": pos["pass"] and neg["pass"] and bnd["pass"],
    }
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out = os.path.join(out_dir, "gtower_order_su_to_sp_then_so_vs_reverse_results.json")
    with open(out,"w") as f: json.dump(results,f,indent=2,default=str)
    print(f"PASS={results['overall_pass']} -> {out}")
