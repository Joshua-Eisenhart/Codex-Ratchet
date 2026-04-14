#!/usr/bin/env python3
"""sim_gtower_deep_su2_so3_double_cover_parity -- Deep G-tower lego.

Claim (admissibility):
  In Cl(3), rotor R = exp(-B theta/2) rotates vectors by theta.
  R at theta=2*pi equals -1 (NOT +1), while SO(3) action returns to identity.
  So {+R, -R} both map to the same SO(3) element -- 2-to-1 cover.
  A candidate spinor that returns after theta=2*pi is EXCLUDED as SO(3);
  only theta=4*pi identifies with identity in SU(2)/Spin(3).

scope_note: LADDERS_FENCES_ADMISSION_REFERENCE.md -- Spin(3) double-cover fence.
"""
import json, os
import numpy as np

TOOL_MANIFEST = {k: {"tried": False, "used": False, "reason": ""} for k in
    ["pytorch","pyg","z3","cvc5","sympy","clifford","geomstats","e3nn","rustworkx","xgi","toponetx","gudhi"]}
TOOL_INTEGRATION_DEPTH = {k: None for k in TOOL_MANIFEST}

try:
    from clifford import Cl
    import numpy as _np
    TOOL_MANIFEST["clifford"]["tried"] = True
    layout, blades = Cl(3)
    e1,e2,e3 = blades['e1'],blades['e2'],blades['e3']
    e12 = e1*e2
    HAVE = True
except ImportError:
    HAVE = False
    TOOL_MANIFEST["clifford"]["reason"] = "not installed"


def rotor(B, theta):
    import math
    return math.cos(theta/2) - B*math.sin(theta/2)


def run_positive_tests():
    if not HAVE: return {"skipped":"clifford missing"}
    r = {}
    import math
    # vector rotation by 2*pi returns (SO(3) identity)
    v = e1
    R = rotor(e12, 2*math.pi)
    vrot = R * v * ~R
    diff = float(((vrot - v)*(vrot - v))[0])
    r["vector_2pi_returns"] = {"diff": diff, "pass": diff < 1e-8}
    # rotor at 2*pi is -1 (scalar part), not +1
    R2pi = rotor(e12, 2*math.pi)
    scalar = float(R2pi[0])
    r["rotor_2pi_is_minus_one"] = {"scalar": scalar, "pass": abs(scalar - (-1.0)) < 1e-8}
    # rotor at 4*pi is +1
    R4pi = rotor(e12, 4*math.pi)
    r["rotor_4pi_is_plus_one"] = {"scalar": float(R4pi[0]),
                                   "pass": abs(float(R4pi[0]) - 1.0) < 1e-8}
    return r


def run_negative_tests():
    if not HAVE: return {"skipped":"clifford missing"}
    r = {}
    import math
    # Spinor-level identity at 2*pi is EXCLUDED: R(2pi) != +1
    R = rotor(e12, 2*math.pi)
    r["spinor_2pi_not_identity"] = {"scalar": float(R[0]),
                                     "pass": abs(float(R[0]) - 1.0) > 0.5}
    return r


def run_boundary_tests():
    if not HAVE: return {"skipped":"clifford missing"}
    r = {}
    import math
    # theta=pi: rotor is purely bivector (-e12)
    R = rotor(e12, math.pi)
    r["pi_is_pure_bivector"] = {"scalar": float(R[0]),
                                "pass": abs(float(R[0])) < 1e-8}
    # theta=0: identity
    R0 = rotor(e12, 0.0)
    r["zero_is_identity"] = {"scalar": float(R0[0]),
                              "pass": abs(float(R0[0]) - 1.0) < 1e-8}
    return r


if __name__ == "__main__":
    if HAVE:
        TOOL_MANIFEST["clifford"]["used"] = True
        TOOL_MANIFEST["clifford"]["reason"] = "Cl(3) rotors decide Spin(3) double-cover parity"
        TOOL_INTEGRATION_DEPTH["clifford"] = "load_bearing"
    results = {
        "name": "sim_gtower_deep_su2_so3_double_cover_parity",
        "scope_note": "LADDERS_FENCES_ADMISSION_REFERENCE.md: Spin(3) double-cover fence",
        "language": "spinor candidates with 2*pi identity are excluded; admissible period is 4*pi",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": run_positive_tests(),
        "negative": run_negative_tests(),
        "boundary": run_boundary_tests(),
        "classification": "canonical",
    }
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out = os.path.join(out_dir, "sim_gtower_deep_su2_so3_double_cover_parity_results.json")
    with open(out, "w") as f: json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out}")
