#!/usr/bin/env python3
"""sim_gtower_clifford_spin_double_cover -- Spin(3) -> SO(3) via Cl(3).

Scope note: LADDERS_FENCES_ADMISSION_REFERENCE.md: SO(n) fence has a
double-cover Spin(n) realized in Cl(n); rotors R and -R give the same SO
element. Load-bearing: python-clifford computes rotor sandwich R x R^~
to produce an SO(3) rotation and verifies the 2:1 relation.
"""
import json, os
import numpy as np

classification = "canonical"

TOOL_MANIFEST = {k: {"tried": False, "used": False, "reason": ""} for k in
    ["pytorch","pyg","z3","cvc5","sympy","clifford","geomstats","e3nn","rustworkx","xgi","toponetx","gudhi"]}
TOOL_INTEGRATION_DEPTH = {k: None for k in TOOL_MANIFEST}

try:
    from clifford import Cl
    TOOL_MANIFEST["clifford"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["clifford"]["reason"] = "not installed"

from _gtower_common import in_SOn


def rotor_to_matrix(R, layout):
    e1, e2, e3 = [layout.blades[b] for b in ("e1", "e2", "e3")]
    basis = [e1, e2, e3]
    cols = []
    for v in basis:
        w = R * v * ~R
        cols.append([float((w | b).value[0]) for b in basis])
    # cols are images as rows; matrix columns are images of e_i
    M = np.array(cols).T
    return M


def run_positive_tests():
    r = {}
    if not TOOL_MANIFEST["clifford"]["tried"]:
        r["clifford_available"] = False
        return r
    layout, blades = Cl(3)
    e1, e2, e3 = blades["e1"], blades["e2"], blades["e3"]
    # rotor for pi/2 rotation in e1^e2 plane
    theta = np.pi / 2
    B = e1 * e2
    R = np.cos(theta / 2) - np.sin(theta / 2) * B
    M = rotor_to_matrix(R, layout)
    r["rotor_in_SO3"] = in_SOn(M)
    # expected: rotate e1 -> e2
    r["rotor_rotates_e1_to_e2"] = np.allclose(M @ np.array([1, 0, 0]),
                                              np.array([0, 1, 0]), atol=1e-10)
    TOOL_MANIFEST["clifford"]["used"] = True
    TOOL_MANIFEST["clifford"]["reason"] = "rotor sandwich computes SO(3) element"
    TOOL_INTEGRATION_DEPTH["clifford"] = "load_bearing"
    return r


def run_negative_tests():
    r = {}
    if not TOOL_MANIFEST["clifford"]["tried"]:
        return {"skipped": True}
    layout, blades = Cl(3)
    e1, e2 = blades["e1"], blades["e2"]
    # non-rotor (scalar != 1) does NOT correspond to a valid Spin element
    bad = 2.0 + 0 * e1
    M = rotor_to_matrix(bad, layout)
    r["nonrotor_not_SO"] = not in_SOn(M)
    return r


def run_boundary_tests():
    r = {}
    if not TOOL_MANIFEST["clifford"]["tried"]:
        return {"skipped": True}
    layout, blades = Cl(3)
    e1, e2 = blades["e1"], blades["e2"]
    theta = 0.7
    B = e1 * e2
    R = np.cos(theta / 2) - np.sin(theta / 2) * B
    Rn = -R  # 2:1 cover: -R yields same SO element
    M1 = rotor_to_matrix(R, layout)
    M2 = rotor_to_matrix(Rn, layout)
    r["double_cover_2to1"] = np.allclose(M1, M2, atol=1e-10)
    # boundary: identity rotor -> identity SO
    Rid = 1.0 + 0 * e1
    Mid = rotor_to_matrix(Rid, layout)
    r["identity_rotor_ok"] = np.allclose(Mid, np.eye(3), atol=1e-10)
    return r


if __name__ == "__main__":
    pos, neg, bnd = run_positive_tests(), run_negative_tests(), run_boundary_tests()
    def _t(v): return bool(v) is True
    keys_pos = ["rotor_in_SO3", "rotor_rotates_e1_to_e2"]
    keys_neg = ["nonrotor_not_SO"]
    keys_bnd = ["double_cover_2to1", "identity_rotor_ok"]
    all_pass = (all(_t(pos.get(k)) for k in keys_pos)
                and all(_t(neg.get(k)) for k in keys_neg)
                and all(_t(bnd.get(k)) for k in keys_bnd))
    results = {
        "name": "sim_gtower_clifford_spin_double_cover",
        "classification": "canonical",
        "scope_note": "LADDERS_FENCES_ADMISSION_REFERENCE.md: SO->Spin double cover via Cl(3)",
        "tool_manifest": TOOL_MANIFEST, "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos, "negative": neg, "boundary": bnd,
        "status": "PASS" if all_pass else "FAIL",
    }
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "sim_gtower_clifford_spin_double_cover_results.json"), "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"{results['name']}: {results['status']}")
