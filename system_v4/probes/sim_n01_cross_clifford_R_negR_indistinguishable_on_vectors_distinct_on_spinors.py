#!/usr/bin/env python3
"""sim_n01_cross_clifford_R_negR_indistinguishable_on_vectors_distinct_on_spinors --
In Cl(3), the rotor R and -R act identically on vectors (R v R~ = (-R) v (-R)~)
but distinctly on spinors. Identity under N01 is probe-relative: with 'vector
probes' R~-R; with 'spinor probes' they are distinct. clifford load-bearing.
"""
import json, os, numpy as np

TOOL_MANIFEST = {k: {"tried": False, "used": False, "reason": ""} for k in
    ["pytorch","pyg","z3","cvc5","sympy","clifford","geomstats","e3nn","rustworkx","xgi","toponetx","gudhi"]}
TOOL_INTEGRATION_DEPTH = {k: None for k in TOOL_MANIFEST}

try:
    from clifford import Cl; TOOL_MANIFEST["clifford"]["tried"] = True
except ImportError: TOOL_MANIFEST["clifford"]["reason"] = "not installed"


def run_positive_tests():
    layout, blades = Cl(3)
    e1, e2, e3 = blades["e1"], blades["e2"], blades["e3"]
    # Rotor R: pi/2 rotation in e12-plane; spinor half-angle pi/4.
    theta = np.pi / 2
    B = e1 * e2
    R = np.cos(theta/2) - np.sin(theta/2) * B
    negR = -R
    v = e1 + 2*e2 + 3*e3
    vR = R * v * ~R
    vnR = negR * v * ~negR
    vec_same = np.allclose((vR - vnR).value, 0, atol=1e-10)
    # Spinor action: psi -> R psi; (R - (-R)) psi = 2R psi != 0
    psi = 1 + e1*e2
    spin_diff = (R * psi - negR * psi)
    spin_distinct = not np.allclose(spin_diff.value, 0, atol=1e-10)
    TOOL_MANIFEST["clifford"]["used"] = True
    TOOL_MANIFEST["clifford"]["reason"] = "load-bearing: Cl(3) rotor/vector/spinor action"
    TOOL_INTEGRATION_DEPTH["clifford"] = "load_bearing"
    return {"vector_same": bool(vec_same), "spinor_distinct": bool(spin_distinct),
            "pass": bool(vec_same) and bool(spin_distinct)}


def run_negative_tests():
    # Falsification: claim R,-R distinct on vectors -> must fail.
    layout, blades = Cl(3)
    e1, e2 = blades["e1"], blades["e2"]
    B = e1*e2; theta = 1.0
    R = np.cos(theta/2) - np.sin(theta/2)*B
    v = e1
    diff = (R * v * ~R) - ((-R) * v * ~(-R))
    vec_distinct_claim = not np.allclose(diff.value, 0, atol=1e-10)
    return {"claim_vec_distinct": vec_distinct_claim, "pass": vec_distinct_claim is False}


def run_boundary_tests():
    # Identity rotor (theta=0): R=1, -R=-1. Vectors: same. Spinors: distinct.
    layout, blades = Cl(3)
    e1 = blades["e1"]
    R = layout.scalar  # 1
    v = e1
    vec_same = np.allclose(((R*v*~R) - ((-R)*v*~(-R))).value, 0, atol=1e-10)
    return {"identity_rotor_vec_same": bool(vec_same), "pass": bool(vec_same)}


if __name__ == "__main__":
    pos = run_positive_tests(); neg = run_negative_tests(); bnd = run_boundary_tests()
    ok = bool(pos["pass"] and neg["pass"] and bnd["pass"])
    name = "sim_n01_cross_clifford_R_negR_indistinguishable_on_vectors_distinct_on_spinors"
    results = {"name": name, "classification": "canonical",
        "tool_manifest": TOOL_MANIFEST, "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos, "negative": neg, "boundary": bnd, "pass": ok}
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out = os.path.join(out_dir, name + "_results.json")
    with open(out, "w") as f: json.dump(results, f, indent=2, default=str)
    print(f"{'PASS' if ok else 'FAIL'} -> {out}")
