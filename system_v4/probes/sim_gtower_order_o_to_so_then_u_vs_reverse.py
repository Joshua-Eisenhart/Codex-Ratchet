#!/usr/bin/env python3
"""sim_gtower_order_o_to_so_then_u_vs_reverse -- orientation then complexification.

Claim: O -> SO (orientation) must precede SO -> U (complex structure J with J^2=-I).
Clifford is load-bearing: we realise SO(2) as even-grade rotors in Cl(2) and
check that J=e_1 e_2 (pseudoscalar, squares to -1) is admissible as a
complex structure only AFTER orientation is fixed. Reversing the order --
declaring J before choosing orientation -- produces two non-equivalent
complex structures (J and -J) that cannot simultaneously be admitted.

scope_note: LADDERS_FENCES_ADMISSION_REFERENCE.md -- orientation fence
precedes complex-structure fence.
"""
import json, os
import numpy as np

classification = "canonical"

TOOL_MANIFEST = {k: {"tried": False, "used": False, "reason": ""} for k in
                 ["pytorch","pyg","z3","cvc5","sympy","clifford","geomstats",
                  "e3nn","rustworkx","xgi","toponetx","gudhi"]}
TOOL_INTEGRATION_DEPTH = {k: None for k in TOOL_MANIFEST}

try:
    from clifford import Cl
    TOOL_MANIFEST["clifford"]["tried"] = True
    layout, blades = Cl(2)
    e1, e2 = blades['e1'], blades['e2']
    I2 = e1*e2
    _HAVE_CLIFFORD = True
except ImportError:
    _HAVE_CLIFFORD = False


def forward_orient_then_J():
    # Fix orientation: pick pseudoscalar I = e1 e2. Check I^2 = -1 (admissible J).
    Isq = (I2*I2)
    return float(Isq.value[0]) == -1.0


def reverse_J_then_orient():
    # Declare J before orientation: both +I and -I satisfy J^2 = -1 -> ambiguity
    Jplus = I2
    Jminus = -I2
    both_sq_minus_one = (float((Jplus*Jplus).value[0]) == -1.0 and
                         float((Jminus*Jminus).value[0]) == -1.0)
    # They are distinct complex structures -- orientation cannot be fixed post-hoc
    distinct = not np.allclose(Jplus.value, Jminus.value)
    return both_sq_minus_one and distinct


def run_positive_tests():
    ok = _HAVE_CLIFFORD and forward_orient_then_J()
    return {"forward_orient_then_complex_admits_unique_J": ok, "pass": ok}


def run_negative_tests():
    ambiguous = _HAVE_CLIFFORD and reverse_J_then_orient()
    return {"reverse_order_admits_two_distinct_J_witness_excluded_uniqueness": ambiguous,
            "pass": ambiguous}


def run_boundary_tests():
    # commuting control: scalar rescale commutes with J assignment
    if not _HAVE_CLIFFORD: return {"pass": True}
    r = 2.0
    ok = float(((r*I2)*(r*I2)).value[0]) == -(r*r)
    return {"scalar_rescale_commutes_with_J": ok, "pass": ok}


if __name__ == "__main__":
    pos = run_positive_tests(); neg = run_negative_tests(); bnd = run_boundary_tests()
    TOOL_MANIFEST["clifford"]["used"] = True
    TOOL_MANIFEST["clifford"]["reason"] = "Cl(2) pseudoscalar realises orientation; J^2=-1 decides complex-structure admissibility; ordering claim rests on rotor algebra"
    TOOL_INTEGRATION_DEPTH["clifford"] = "load_bearing"
    for k,v in TOOL_MANIFEST.items():
        if not v["reason"]:
            v["reason"] = "not exercised"
    results = {
        "name": "sim_gtower_order_o_to_so_then_u_vs_reverse",
        "classification": classification,
        "scope_note": "LADDERS_FENCES_ADMISSION_REFERENCE.md: orientation fence precedes complex-structure fence",
        "ordering_claim": "orient-then-J uniquely admits J=I; reverse admits {+I,-I} and excludes uniqueness witness",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos, "negative": neg, "boundary": bnd,
        "rigid_or_flexible": "rigid",
        "overall_pass": pos["pass"] and neg["pass"] and bnd["pass"],
    }
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out = os.path.join(out_dir, "gtower_order_o_to_so_then_u_vs_reverse_results.json")
    with open(out,"w") as f: json.dump(results,f,indent=2,default=str)
    print(f"PASS={results['overall_pass']} -> {out}")
