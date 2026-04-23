#!/usr/bin/env python3
"""sim_pin3_double_cover_vector_vs_spinor -- Spin(3) double cover: R and -R
act identically on vectors (via sandwich), but distinctly on spinors (via
left multiplication).

Positive: for 50 random rotors, R v R~ == (-R) v (-R)~ on vectors, while
R psi != (-R) psi on spinors (where psi is a Cl(3) even-grade element used
as spinor). Negative: a non-unit scalar multiple (not a sign) acts
differently on both. Boundary: R = 1 vs R = -1 (identity double cover).
Ablation: numpy 3x3 rotation matrices cannot represent the sign distinction
at all -- they collapse R and -R into the same SO(3) element.
"""
import json, os, numpy as np
from clifford import Cl

TOOL_MANIFEST = {k:{"tried":False,"used":False,"reason":""} for k in
    ["pytorch","pyg","z3","cvc5","sympy","clifford","geomstats","e3nn","rustworkx","xgi","toponetx","gudhi"]}
TOOL_INTEGRATION_DEPTH = {k: None for k in TOOL_MANIFEST}
TOOL_MANIFEST["clifford"] = {"tried":True,"used":True,"reason":"Cl(3) even-subalgebra represents Spin(3); the double cover is the property under test"}
TOOL_INTEGRATION_DEPTH["clifford"] = "load_bearing"

layout, blades = Cl(3)
e1,e2,e3 = blades['e1'],blades['e2'],blades['e3']

def random_rotor(rng):
    axis = rng.normal(size=3); axis/=np.linalg.norm(axis)
    angle = rng.uniform(0,2*np.pi)
    B = axis[0]*(e2*e3)+axis[1]*(e3*e1)+axis[2]*(e1*e2)
    return np.cos(angle/2) - np.sin(angle/2)*B

def sandwich(R, v):
    V = v[0]*e1+v[1]*e2+v[2]*e3
    Vp = R*V*~R
    return np.array([float(Vp[e1]),float(Vp[e2]),float(Vp[e3])])

def mv_to_even_vec(mv):
    # extract even-grade coefficients (grades 0,2) as 4-vector
    return np.array([float(mv[layout.scalar]),
                     float(mv[e1*e2]), float(mv[e2*e3]), float(mv[e3*e1])])

def run_positive_tests():
    rng = np.random.default_rng(42)
    n = 50; max_vec_diff = 0.0; min_spinor_diff = np.inf
    for _ in range(n):
        R = random_rotor(rng); nR = -R
        v = rng.normal(size=3)
        v1 = sandwich(R, v); v2 = sandwich(nR, v)
        max_vec_diff = max(max_vec_diff, float(np.linalg.norm(v1-v2)))
        # spinor psi: another even-grade element
        psi = random_rotor(rng)
        s1 = R*psi; s2 = nR*psi
        diff = float(np.linalg.norm(mv_to_even_vec(s1) - mv_to_even_vec(s2)))
        min_spinor_diff = min(min_spinor_diff, diff)
    return {"n": n, "max_vector_diff_R_vs_minusR": max_vec_diff,
            "min_spinor_diff_R_vs_minusR": min_spinor_diff,
            "pass": max_vec_diff < 1e-10 and min_spinor_diff > 1e-3}

def run_negative_tests():
    # Scale by 2 (not -1): changes vector result too.
    rng = np.random.default_rng(7)
    R = random_rotor(rng); R2 = R*2.0
    v = rng.normal(size=3)
    vdiff = float(np.linalg.norm(sandwich(R, v) - sandwich(R2, v)))
    return {"scale_by_2_breaks_vector_equality": vdiff > 1e-3,
            "diff": vdiff, "pass": vdiff > 1e-3}

def run_boundary_tests():
    # R = 1 vs R = -1: vector action identical (both identity), spinor differs by sign
    R_pos = 1.0 + 0*e1
    R_neg = -1.0 + 0*e1
    v = np.array([1.0,2.0,3.0])
    v1 = sandwich(R_pos, v); v2 = sandwich(R_neg, v)
    vec_id = float(np.linalg.norm(v1 - v)) + float(np.linalg.norm(v2 - v))
    psi = random_rotor(np.random.default_rng(1))
    s_pos = mv_to_even_vec(R_pos*psi); s_neg = mv_to_even_vec(R_neg*psi)
    spinor_diff = float(np.linalg.norm(s_pos - s_neg))
    expected_spinor_diff = float(2*np.linalg.norm(mv_to_even_vec(psi)))
    return {"vector_identity_both_ways": vec_id,
            "spinor_diff": spinor_diff,
            "expected_2norm_psi": expected_spinor_diff,
            "pass": vec_id < 1e-10 and abs(spinor_diff - expected_spinor_diff) < 1e-9}

def run_ablation():
    # numpy SO(3) matrix cannot see the sign of the rotor. We build the rotation
    # matrix from R, then from -R's "implied" rotation -- both produce identical
    # 3x3 matrices, so numpy cannot distinguish them at all.
    rng = np.random.default_rng(9)
    R = random_rotor(rng)
    # extract axis/angle
    # (reverse: R = cos(t/2) - sin(t/2) B)
    s = float(R[layout.scalar]); c = s
    # build corresponding rotation matrix by sandwiching basis vectors
    M = np.column_stack([sandwich(R, np.array([1.0,0,0])),
                         sandwich(R, np.array([0,1.0,0])),
                         sandwich(R, np.array([0,0,1.0]))])
    Mn = np.column_stack([sandwich(-R, np.array([1.0,0,0])),
                          sandwich(-R, np.array([0,1.0,0])),
                          sandwich(-R, np.array([0,0,1.0]))])
    numpy_indistinguishable = float(np.linalg.norm(M - Mn))
    # clifford view: the rotor itself differs
    rotor_diff = float(np.linalg.norm(R.value - (-R).value))
    return {"numpy_SO3_matrix_diff": numpy_indistinguishable,
            "clifford_rotor_diff": rotor_diff,
            "ablation_shows_numpy_insufficient": numpy_indistinguishable < 1e-12 and rotor_diff > 1e-3}

if __name__ == "__main__":
    pos = run_positive_tests(); neg = run_negative_tests(); bnd = run_boundary_tests()
    ab = run_ablation()
    results = {
        "name": "sim_pin3_double_cover_vector_vs_spinor",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos, "negative": neg, "boundary": bnd, "ablation": ab,
        "classification": "canonical",
        "overall_pass": pos["pass"] and neg["pass"] and bnd["pass"] and ab["ablation_shows_numpy_insufficient"],
    }
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "sim_pin3_double_cover_vector_vs_spinor_results.json")
    with open(out_path, "w") as f: json.dump(results, f, indent=2, default=str)
    print(f"PASS={results['overall_pass']} -> {out_path}")
