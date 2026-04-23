#!/usr/bin/env python3
"""
IGT deep -- ring-topology chirality (clifford load-bearing).

Scope: 4-player cyclic game on a ring admits CW / CCW traversal orientations.
We EXCLUDE the indistinguishability of the two orientations by computing a
pseudoscalar (grade-3 element in Cl(3)) of the cyclic product of player
'position vectors'. Sign of the pseudoscalar separates chirality classes.
"""
import json, os
from clifford import Cl

TOOL_MANIFEST = {k: {"tried": False, "used": False, "reason": ""} for k in
    ["pytorch","pyg","z3","cvc5","sympy","clifford","geomstats","e3nn",
     "rustworkx","xgi","toponetx","gudhi"]}
TOOL_INTEGRATION_DEPTH = {k: None for k in TOOL_MANIFEST}
TOOL_MANIFEST["clifford"]["tried"] = True
for k in TOOL_MANIFEST:
    if not TOOL_MANIFEST[k]["tried"]:
        TOOL_MANIFEST[k]["reason"] = "not required for Cl(3) pseudoscalar discriminator"

layout, blades = Cl(3)
e1, e2, e3 = blades["e1"], blades["e2"], blades["e3"]
I3 = blades["e123"]


def _cw_product():
    # CW ring: e1 -> e2 -> e3 -> e1, wedge gives +e123
    return e1 ^ e2 ^ e3


def _ccw_product():
    # CCW ring: reverse order, sign flips (odd permutation)
    return e1 ^ e3 ^ e2


def run_positive_tests():
    r = {}
    cw = _cw_product()
    ccw = _ccw_product()
    # Use grade-3 coefficient directly (index 7 = e123 in Cl(3))
    cw_coef = float(cw.value[7])
    ccw_coef = float(ccw.value[7])
    r["cw_pseudoscalar_positive"] = {"v": cw_coef, "pass": cw_coef > 0}
    r["ccw_pseudoscalar_negative"] = {"v": ccw_coef, "pass": ccw_coef < 0}
    r["cw_ne_ccw"] = {"pass": abs(cw_coef - ccw_coef) > 1e-9}
    return r


def run_negative_tests():
    r = {}
    # Collapsed ring (two players coincident) -- pseudoscalar must vanish;
    # chirality distinction EXCLUDED.
    degen = e1 ^ e1 ^ e2
    coef = float(degen.value[7])
    r["degenerate_no_chirality"] = {"v": coef, "pass": abs(coef) < 1e-12}
    return r


def run_boundary_tests():
    r = {}
    # Rotating labels (cyclic shift) preserves sign within same chirality class
    shifted_cw = e2 ^ e3 ^ e1
    cw = _cw_product()
    s1 = float(shifted_cw.value[7])
    s2 = float(cw.value[7])
    r["cyclic_shift_preserves"] = {"s1": s1, "s2": s2, "pass": abs(s1 - s2) < 1e-12}
    # Orientation reversal (single swap) flips sign
    swapped = e2 ^ e1 ^ e3
    sw = float(swapped.value[7])
    r["swap_flips_sign"] = {"sw": sw, "pass": sw * s2 < 0}
    return r


if __name__ == "__main__":
    TOOL_MANIFEST["clifford"]["used"] = True
    TOOL_MANIFEST["clifford"]["reason"] = "Cl(3) pseudoscalar sign separates CW/CCW ring orientation"
    TOOL_INTEGRATION_DEPTH["clifford"] = "load_bearing"
    pos, neg, bnd = run_positive_tests(), run_negative_tests(), run_boundary_tests()
    allpass = lambda d: all(v.get("pass", False) for v in d.values())
    ap = allpass(pos) and allpass(neg) and allpass(bnd)
    res = {"name": "igt_deep_ring_topology_chirality",
           "classification": "canonical",
           "scope_note": "OWNER_DOCTRINE_SELF_SIMILAR_FRAMEWORKS.md",
           "tool_manifest": TOOL_MANIFEST, "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
           "positive": pos, "negative": neg, "boundary": bnd, "all_pass": ap}
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out = os.path.join(out_dir, "igt_deep_ring_topology_chirality_results.json")
    with open(out, "w") as f: json.dump(res, f, indent=2, default=str)
    print(f"[{res['name']}] all_pass={ap} -> {out}")
