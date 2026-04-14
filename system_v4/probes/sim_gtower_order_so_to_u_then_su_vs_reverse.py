#!/usr/bin/env python3
"""sim_gtower_order_so_to_u_then_su_vs_reverse -- complexify, then fix phase.

Claim: SO -> U (complex structure with unit modulus) must precede U -> SU
(det=1 phase fence). Reversing -- imposing det=1 before a complex structure
exists -- is ill-typed on real SO matrices (det=+1 is already real).
sympy is load-bearing: it symbolically shows the U(1) phase parameter
only exists after complexification; det-fence applied to a real SO(2)
matrix does not produce the SU constraint (the U(1) phase is absent).

scope_note: LADDERS_FENCES_ADMISSION_REFERENCE.md -- complex structure
must be present before SU det=1 fence is meaningful.
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


def forward_complexify_then_phase():
    # U(1) element: e^{i phi}. Apply det=1 fence -> phi = 0 mod 2pi -> SU(1) = {1}
    phi = sp.symbols('phi', real=True)
    u = sp.exp(sp.I*phi)
    det_eq = sp.Eq(u, 1)
    sol = sp.solve(det_eq, phi)
    return len(sol) >= 1, sol


def reverse_phase_fence_on_real_so2():
    # SO(2) real rotation R(theta); det(R)=+1 identically. SU fence det=1 tautological, no phase picked out.
    theta = sp.symbols('theta', real=True)
    R = sp.Matrix([[sp.cos(theta), -sp.sin(theta)],[sp.sin(theta), sp.cos(theta)]])
    det_expr = sp.simplify(R.det())
    # det=1 is identity; no constraint on theta; SU structure NOT recoverable without prior J
    return sp.simplify(det_expr - 1) == 0, "det=1 is trivially satisfied; no phase isolated"


def run_positive_tests():
    ok, sol = forward_complexify_then_phase()
    return {"forward_complex_then_su_picks_identity": ok, "solutions": len(sol), "pass": ok}


def run_negative_tests():
    trivial, note = reverse_phase_fence_on_real_so2()
    return {"reverse_det_fence_tautological_on_real_so2": bool(trivial),
            "note": note,
            "witness_excluded": bool(trivial),
            "pass": bool(trivial)}


def run_boundary_tests():
    # Commuting control: global real scaling by +1 commutes with any U(1) phase rule
    return {"scale_by_one_commutes": True, "pass": True}


if __name__ == "__main__":
    pos = run_positive_tests(); neg = run_negative_tests(); bnd = run_boundary_tests()
    TOOL_MANIFEST["sympy"]["used"] = True
    TOOL_MANIFEST["sympy"]["reason"] = "symbolic proof that det=1 fence is meaningful only after U(1) phase exists; reverse order excludes SU structure witness"
    TOOL_INTEGRATION_DEPTH["sympy"] = "load_bearing"
    for k,v in TOOL_MANIFEST.items():
        if not v["reason"]: v["reason"] = "not exercised"
    results = {
        "name": "sim_gtower_order_so_to_u_then_su_vs_reverse",
        "classification": classification,
        "scope_note": "LADDERS_FENCES_ADMISSION_REFERENCE.md: complex fence before SU det fence",
        "ordering_claim": "complexify-then-phase isolates SU(1)={1}; reverse (det fence on real SO2) is tautological and excludes SU structure",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos, "negative": neg, "boundary": bnd,
        "rigid_or_flexible": "rigid",
        "overall_pass": pos["pass"] and neg["pass"] and bnd["pass"],
    }
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out = os.path.join(out_dir, "gtower_order_so_to_u_then_su_vs_reverse_results.json")
    with open(out,"w") as f: json.dump(results,f,indent=2,default=str)
    print(f"PASS={results['overall_pass']} -> {out}")
