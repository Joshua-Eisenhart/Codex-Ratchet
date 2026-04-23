#!/usr/bin/env python3
"""sim_gtower_deep_pin3_vs_spin3_reflection -- Deep G-tower lego.

Claim (admissibility):
  Pin(3) admits ODD products of unit vectors (reflections, det=-1 cover).
  Spin(3) admits only EVEN products (rotors, det=+1 cover).
  An odd-vector candidate is EXCLUDED from Spin(3).

scope_note: LADDERS_FENCES_ADMISSION_REFERENCE.md -- Pin/Spin parity fence.
"""
import json, os

TOOL_MANIFEST = {k: {"tried": False, "used": False, "reason": ""} for k in
    ["pytorch","pyg","z3","cvc5","sympy","clifford","geomstats","e3nn","rustworkx","xgi","toponetx","gudhi"]}
TOOL_INTEGRATION_DEPTH = {k: None for k in TOOL_MANIFEST}

try:
    from clifford import Cl
    TOOL_MANIFEST["clifford"]["tried"] = True
    layout, blades = Cl(3)
    e1,e2,e3 = blades['e1'],blades['e2'],blades['e3']
    HAVE = True
except ImportError:
    HAVE = False
    TOOL_MANIFEST["clifford"]["reason"] = "not installed"


def grade_parts(mv):
    """Return dict grade -> norm^2."""
    out = {}
    for g in range(4):
        gp = mv(g)
        out[g] = float((gp * ~gp)[0])
    return out


def run_positive_tests():
    if not HAVE: return {"skipped":"clifford missing"}
    r = {}
    # Even product (rotor): e1*e2 -- grades 0 and 2 only => Spin(3) admissible
    R = e1*e2
    gp = grade_parts(R)
    r["even_is_spin"] = {"grades": gp,
                          "pass": gp[1] < 1e-9 and gp[3] < 1e-9}
    # Odd product (reflection): e1 -- grade 1 => Pin but not Spin
    P = e1
    gp2 = grade_parts(P)
    r["odd_is_pin_not_spin"] = {"grades": gp2,
                                 "pass": gp2[1] > 0.5 and gp2[0] < 1e-9}
    # Three reflections: e1*e2*e3 = pseudoscalar (grade 3), odd -> Pin not Spin
    T = e1*e2*e3
    gp3 = grade_parts(T)
    r["triple_refl_pseudoscalar"] = {"grades": gp3,
                                      "pass": gp3[3] > 0.5 and gp3[0] < 1e-9}
    return r


def run_negative_tests():
    if not HAVE: return {"skipped":"clifford missing"}
    r = {}
    # Mixed grade (not a pure Pin/Spin element): e1 + e1*e2 -- excluded from both
    M = e1 + e1*e2
    gp = grade_parts(M)
    is_pure_even = (gp[1] < 1e-9 and gp[3] < 1e-9)
    is_pure_odd = (gp[0] < 1e-9 and gp[2] < 1e-9)
    r["mixed_excluded"] = {"grades": gp, "pass": (not is_pure_even) and (not is_pure_odd)}
    return r


def run_boundary_tests():
    if not HAVE: return {"skipped":"clifford missing"}
    r = {}
    # Scalar 1 is in Spin (even, trivial)
    one = 1 + 0*e1
    gp = grade_parts(one)
    r["scalar_one_in_spin"] = {"grades": gp, "pass": gp[0] > 0.5}
    # -1 also in Spin (kernel of double cover)
    mone = -1 + 0*e1
    gp2 = grade_parts(mone)
    r["minus_one_in_spin"] = {"grades": gp2, "pass": gp2[0] > 0.5}
    return r


if __name__ == "__main__":
    if HAVE:
        TOOL_MANIFEST["clifford"]["used"] = True
        TOOL_MANIFEST["clifford"]["reason"] = "Cl(3) grade parity decides Pin vs Spin admissibility"
        TOOL_INTEGRATION_DEPTH["clifford"] = "load_bearing"
    results = {
        "name": "sim_gtower_deep_pin3_vs_spin3_reflection",
        "scope_note": "LADDERS_FENCES_ADMISSION_REFERENCE.md: Pin/Spin parity fence",
        "language": "even-grade: Spin-admissible; odd-grade: Pin-only; mixed: excluded",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": run_positive_tests(),
        "negative": run_negative_tests(),
        "boundary": run_boundary_tests(),
        "classification": "canonical",
    }
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out = os.path.join(out_dir, "sim_gtower_deep_pin3_vs_spin3_reflection_results.json")
    with open(out, "w") as f: json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out}")
