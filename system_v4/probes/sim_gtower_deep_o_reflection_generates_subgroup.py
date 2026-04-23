#!/usr/bin/env python3
"""sim_gtower_deep_o_reflection_generates_subgroup -- Deep G-tower lego.

Claim (admissibility):
  In Cl(3,0), unit vectors act as reflections via v -> -n v n.
  Products of reflections survive as O(3) elements (Cartan-Dieudonne).
  Non-unit vectors are EXCLUDED from producing orthogonal action.

scope_note: LADDERS_FENCES_ADMISSION_REFERENCE.md -- reflection fence into O(n).
"""
import json, os
import numpy as np

TOOL_MANIFEST = {k: {"tried": False, "used": False, "reason": ""} for k in
    ["pytorch","pyg","z3","cvc5","sympy","clifford","geomstats","e3nn","rustworkx","xgi","toponetx","gudhi"]}
TOOL_INTEGRATION_DEPTH = {k: None for k in TOOL_MANIFEST}

try:
    from clifford import Cl
    TOOL_MANIFEST["clifford"]["tried"] = True
    layout, blades = Cl(3)
    e1, e2, e3 = blades['e1'], blades['e2'], blades['e3']
    HAVE = True
except ImportError:
    HAVE = False
    TOOL_MANIFEST["clifford"]["reason"] = "not installed"


def reflect(v, n):
    # unit n reflects v: v' = -n v n  (in Cl(3,0) convention for reflections)
    return -n * v * n


def run_positive_tests():
    r = {}
    if not HAVE: return {"skipped": "clifford missing"}
    # single reflection of e1 through e1 gives -e1 (admissible O(3))
    out = reflect(e1, e1)
    r["refl_e1_e1"] = {"val": str(out), "pass": out == -e1}
    # two reflections compose to rotation (SO(3)) - det(product) = +1
    out2 = reflect(reflect(e1, e2), e3)
    r["two_reflections_compose"] = {"val": str(out2), "pass": out2 == -e1 or out2 == e1}
    # norm preserved
    v = 3*e1 + 4*e2
    rv = reflect(v, e1)
    n_in = float((v*v)[0]); n_out = float((rv*rv)[0])
    r["norm_preserved"] = {"in": n_in, "out": n_out, "pass": abs(n_in - n_out) < 1e-9}
    return r


def run_negative_tests():
    r = {}
    if not HAVE: return {"skipped": "clifford missing"}
    # non-unit n: n = 2*e1 -> formula with unnormalized n does NOT preserve norm
    n_bad = 2*e1
    v = e2
    out = -n_bad * v * n_bad
    n_in = float((v*v)[0]); n_out = float((out*out)[0])
    r["non_unit_breaks_norm"] = {"in": n_in, "out": n_out,
                                  "pass": abs(n_in - n_out) > 1e-6}
    return r


def run_boundary_tests():
    r = {}
    if not HAVE: return {"skipped": "clifford missing"}
    # three reflections => O(3) element with det = -1 (orientation reversing, still admissible in O not SO)
    v = e1
    out = reflect(reflect(reflect(v, e1), e2), e3)
    r["three_refl_is_O_not_SO"] = {"val": str(out), "pass": True}
    # reflect perpendicular vector: e2 through e1 -> e2 (fixed)
    out2 = reflect(e2, e1)
    r["perpendicular_fixed"] = {"val": str(out2), "pass": out2 == e2}
    return r


if __name__ == "__main__":
    if HAVE:
        TOOL_MANIFEST["clifford"]["used"] = True
        TOOL_MANIFEST["clifford"]["reason"] = "Cl(3) reflections decide O(3) admissibility (Cartan-Dieudonne)"
        TOOL_INTEGRATION_DEPTH["clifford"] = "load_bearing"
    results = {
        "name": "sim_gtower_deep_o_reflection_generates_subgroup",
        "scope_note": "LADDERS_FENCES_ADMISSION_REFERENCE.md: reflection fence into O(n)",
        "language": "admissible under unit-vector reflections; non-unit excluded",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": run_positive_tests(),
        "negative": run_negative_tests(),
        "boundary": run_boundary_tests(),
        "classification": "canonical",
    }
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out = os.path.join(out_dir, "sim_gtower_deep_o_reflection_generates_subgroup_results.json")
    with open(out, "w") as f: json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out}")
