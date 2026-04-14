#!/usr/bin/env python3
"""sim_gtower_u1_hopf_fiber_reduction -- U(1) Hopf fiber reduction SU(2)->SO(3).

Scope note: LADDERS_FENCES_ADMISSION_REFERENCE.md: SU(2) -> SO(3) via
Hopf fibration; U(1) fibers quotient to points. Load-bearing: Cl(3) rotor
of form exp(theta e1 e2) acts on R^3 preserving the e3 axis (U(1) fiber
stabilizer maps to an SO(3) rotation around e3).
"""
import json, os
import numpy as np

classification = "classical_baseline"
DEMOTE_REASON = "no non-numpy load_bearing tool; numeric numpy only"

TOOL_MANIFEST = {k: {"tried": False, "used": False, "reason": ""} for k in
    ["pytorch","pyg","z3","cvc5","sympy","clifford","geomstats","e3nn","rustworkx","xgi","toponetx","gudhi"]}
TOOL_INTEGRATION_DEPTH = {k: None for k in TOOL_MANIFEST}

try:
    from clifford import Cl
    TOOL_MANIFEST["clifford"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["clifford"]["reason"] = "not installed"

from _gtower_common import in_SOn


def apply_rotor(R, v, layout):
    e1, e2, e3 = [layout.blades[b] for b in ("e1", "e2", "e3")]
    basis = [e1, e2, e3]
    vb = sum(vi * bi for vi, bi in zip(v, basis))
    w = R * vb * ~R
    return np.array([float((w | b).value[0]) for b in basis])


def run_positive_tests():
    r = {}
    if not TOOL_MANIFEST["clifford"]["tried"]:
        return {"skipped": True}
    layout, blades = Cl(3)
    e1, e2, e3 = blades["e1"], blades["e2"], blades["e3"]
    B = e1 * e2  # bivector = U(1) generator of e3-axis rotation
    # U(1) fiber: parameterize theta in [0, 2*pi]
    fixed = []
    for theta in np.linspace(0, 2 * np.pi, 8, endpoint=False):
        R = np.cos(theta / 2) - np.sin(theta / 2) * B
        w = apply_rotor(R, [0, 0, 1], layout)
        fixed.append(np.allclose(w, [0, 0, 1], atol=1e-10))
    r["u1_fiber_fixes_e3"] = all(fixed)
    TOOL_MANIFEST["clifford"]["used"] = True
    TOOL_MANIFEST["clifford"]["reason"] = "rotor exp(theta e12) computes U(1) action preserving e3 axis"
    TOOL_INTEGRATION_DEPTH["clifford"] = "load_bearing"
    # equator point gets rotated: full orbit non-trivial
    theta = np.pi / 2
    R = np.cos(theta / 2) - np.sin(theta / 2) * B
    w = apply_rotor(R, [1, 0, 0], layout)
    r["equator_moves"] = not np.allclose(w, [1, 0, 0], atol=1e-6)
    return r


def run_negative_tests():
    r = {}
    if not TOOL_MANIFEST["clifford"]["tried"]:
        return {"skipped": True}
    layout, blades = Cl(3)
    e1, e2, e3 = blades["e1"], blades["e2"], blades["e3"]
    # Wrong-axis rotor (e2 e3) does NOT fix e3
    B = e2 * e3
    R = np.cos(0.5) - np.sin(0.5) * B
    w = apply_rotor(R, [0, 0, 1], layout)
    r["wrong_axis_does_not_fix_e3"] = not np.allclose(w, [0, 0, 1], atol=1e-6)
    return r


def run_boundary_tests():
    r = {}
    if not TOOL_MANIFEST["clifford"]["tried"]:
        return {"skipped": True}
    layout, blades = Cl(3)
    e1, e2, e3 = blades["e1"], blades["e2"], blades["e3"]
    B = e1 * e2
    # theta = 2pi gives -1 rotor (double-cover), same SO element as identity
    R2pi = np.cos(np.pi) - np.sin(np.pi) * B
    w = apply_rotor(R2pi, [1, 0, 0], layout)
    r["2pi_same_as_identity_on_vectors"] = np.allclose(w, [1, 0, 0], atol=1e-10)
    # theta=0 gives identity
    R0 = 1.0 + 0 * e1
    w0 = apply_rotor(R0, [0.3, 0.4, 0.5], layout)
    r["identity_rotor"] = np.allclose(w0, [0.3, 0.4, 0.5], atol=1e-10)
    return r


if __name__ == "__main__":
    pos, neg, bnd = run_positive_tests(), run_negative_tests(), run_boundary_tests()
    def _t(v): return bool(v) is True
    keys_pos = ["u1_fiber_fixes_e3", "equator_moves"]
    keys_neg = ["wrong_axis_does_not_fix_e3"]
    keys_bnd = ["2pi_same_as_identity_on_vectors", "identity_rotor"]
    all_pass = (all(_t(pos.get(k)) for k in keys_pos)
                and all(_t(neg.get(k)) for k in keys_neg)
                and all(_t(bnd.get(k)) for k in keys_bnd))
    results = {
        "name": "sim_gtower_u1_hopf_fiber_reduction",
        "classification": "canonical",
        "scope_note": "LADDERS_FENCES_ADMISSION_REFERENCE.md: U(1) Hopf fiber in SU(2)->SO(3)",
        "tool_manifest": TOOL_MANIFEST, "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos, "negative": neg, "boundary": bnd,
        "status": "PASS" if all_pass else "FAIL",
    }
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "sim_gtower_u1_hopf_fiber_reduction_results.json"), "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"{results['name']}: {results['status']}")
