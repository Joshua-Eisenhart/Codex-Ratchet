#!/usr/bin/env python3
"""sim_cl3_rotor_associativity -- Cl(3) rotor composition associativity.

Canonical sim: verify (R1*R2)*R3 == R1*(R2*R3) on 100 random rotor triples,
cross-checked with sympy exact quaternion arithmetic. Ablation: numpy matrix
multiply on rotation matrices is NOT a substitute for rotor geometric product
(ablation shows missing spinor double-cover sign info).
"""
import json, os, numpy as np

TOOL_MANIFEST = {
    "pytorch":{"tried":False,"used":False,"reason":""},
    "pyg":{"tried":False,"used":False,"reason":""},
    "z3":{"tried":False,"used":False,"reason":""},
    "cvc5":{"tried":False,"used":False,"reason":""},
    "sympy":{"tried":False,"used":False,"reason":""},
    "clifford":{"tried":False,"used":False,"reason":""},
    "geomstats":{"tried":False,"used":False,"reason":""},
    "e3nn":{"tried":False,"used":False,"reason":""},
    "rustworkx":{"tried":False,"used":False,"reason":""},
    "xgi":{"tried":False,"used":False,"reason":""},
    "toponetx":{"tried":False,"used":False,"reason":""},
    "gudhi":{"tried":False,"used":False,"reason":""},
}
TOOL_INTEGRATION_DEPTH = {k: None for k in TOOL_MANIFEST}

from clifford import Cl
TOOL_MANIFEST["clifford"] = {"tried":True,"used":True,"reason":"Cl(3) rotor geometric product is the object under test"}
TOOL_INTEGRATION_DEPTH["clifford"] = "load_bearing"

import sympy as sp
TOOL_MANIFEST["sympy"] = {"tried":True,"used":True,"reason":"exact symbolic quaternion cross-check for rotor product associativity"}
TOOL_INTEGRATION_DEPTH["sympy"] = "load_bearing"

layout, blades = Cl(3)
e1, e2, e3 = blades['e1'], blades['e2'], blades['e3']

def random_rotor(rng):
    axis = rng.normal(size=3); axis /= np.linalg.norm(axis)
    angle = rng.uniform(0, 2*np.pi)
    B = axis[0]*(e2*e3) + axis[1]*(e3*e1) + axis[2]*(e1*e2)
    return np.cos(angle/2) - np.sin(angle/2)*B, axis, angle

def quat_mul(q1, q2):
    w1,x1,y1,z1 = q1; w2,x2,y2,z2 = q2
    return (w1*w2-x1*x2-y1*y2-z1*z2,
            w1*x2+x1*w2+y1*z2-z1*y2,
            w1*y2-x1*z2+y1*w2+z1*x2,
            w1*z2+x1*y2-y1*x2+z1*w2)

def rotor_to_quat(axis, angle):
    c = sp.cos(sp.Rational(1,2)*sp.nsimplify(angle, rational=False))
    s = sp.sin(sp.Rational(1,2)*sp.nsimplify(angle, rational=False))
    ax = [sp.nsimplify(float(a), rational=False) for a in axis]
    return (c, s*ax[0], s*ax[1], s*ax[2])

def run_positive_tests():
    rng = np.random.default_rng(42)
    max_assoc_err = 0.0
    max_sympy_err = 0.0
    n = 100
    for _ in range(n):
        R1, a1, t1 = random_rotor(rng)
        R2, a2, t2 = random_rotor(rng)
        R3, a3, t3 = random_rotor(rng)
        L = (R1*R2)*R3
        R = R1*(R2*R3)
        diff = (L-R)
        err = float(np.sqrt(sum(float(diff[bl])**2 for bl in [layout.scalar, e1*e2, e2*e3, e3*e1])))
        max_assoc_err = max(max_assoc_err, err)
    # sympy exact cross-check on one representative triple
    q1 = rotor_to_quat(a1, t1); q2 = rotor_to_quat(a2, t2); q3 = rotor_to_quat(a3, t3)
    qL = quat_mul(quat_mul(q1,q2), q3)
    qR = quat_mul(q1, quat_mul(q2,q3))
    sympy_diff = [sp.simplify(a-b) for a,b in zip(qL,qR)]
    max_sympy_err = float(max(abs(float(d)) for d in sympy_diff))
    # Cross-check clifford L against sympy-expected on last triple
    qL_f = [float(x) for x in qL]
    cliff_scalar = float(L[layout.scalar])
    scalar_match = abs(cliff_scalar - qL_f[0]) < 1e-10
    return {
        "n_triples": n,
        "max_associativity_err_clifford": max_assoc_err,
        "sympy_exact_associativity_err": max_sympy_err,
        "clifford_sympy_scalar_match": scalar_match,
        "pass": max_assoc_err < 1e-10 and max_sympy_err < 1e-10 and scalar_match,
    }

def run_negative_tests():
    rng = np.random.default_rng(7)
    R1,_,_ = random_rotor(rng); R2,_,_ = random_rotor(rng); R3,_,_ = random_rotor(rng)
    # Non-associative-looking broken product: swap order
    L = (R1*R2)*R3
    W = (R2*R1)*R3  # generally different (noncommutative)
    diff = L - W
    err = float(np.sqrt(sum(float(diff[bl])**2 for bl in [layout.scalar, e1*e2, e2*e3, e3*e1])))
    return {"swap_detected_as_different": err > 1e-6, "err": err, "pass": err > 1e-6}

def run_boundary_tests():
    # identity and pi-rotations
    R_id = 1.0 + 0*e1
    axis = np.array([0,0,1.0])
    B = axis[0]*(e2*e3) + axis[1]*(e3*e1) + axis[2]*(e1*e2)
    R_pi = np.cos(np.pi/2) - np.sin(np.pi/2)*B
    # identity associativity
    a = (R_id*R_pi)*R_pi
    b = R_id*(R_pi*R_pi)
    diff = a-b
    err = float(np.sqrt(sum(float(diff[bl])**2 for bl in [layout.scalar, e1*e2, e2*e3, e3*e1])))
    # R_pi * R_pi should be -1 (double cover)
    sq = R_pi*R_pi
    minus_one = abs(float(sq[layout.scalar]) + 1) < 1e-10
    return {"identity_boundary_err": err, "double_cover_R_pi_sq_is_minus_one": minus_one,
            "pass": err < 1e-10 and minus_one}

def run_ablation():
    # numpy matrix multiply ablation: loses spinor sign info (R_pi rotation matrix squares to identity,
    # but rotor R_pi squares to -1). So numpy matmul cannot distinguish R from -R.
    theta = np.pi
    c,s = np.cos(theta), np.sin(theta)
    Rz = np.array([[c,-s,0],[s,c,0],[0,0,1]])
    Rz2 = Rz @ Rz
    numpy_sq_is_identity = np.allclose(Rz2, np.eye(3))
    # rotor equivalent
    axis = np.array([0,0,1.0])
    B = axis[0]*(e2*e3) + axis[1]*(e3*e1) + axis[2]*(e1*e2)
    R_pi = np.cos(theta/2) - np.sin(theta/2)*B
    rotor_sq_is_minus_one = abs(float((R_pi*R_pi)[layout.scalar]) + 1) < 1e-10
    return {
        "numpy_matmul_loses_double_cover": numpy_sq_is_identity and rotor_sq_is_minus_one,
        "numpy_Rz_squared_is_identity": numpy_sq_is_identity,
        "clifford_rotor_squared_is_minus_one": rotor_sq_is_minus_one,
        "ablation_shows_numpy_insufficient": numpy_sq_is_identity and rotor_sq_is_minus_one,
    }

if __name__ == "__main__":
    pos = run_positive_tests(); neg = run_negative_tests(); bnd = run_boundary_tests()
    ab = run_ablation()
    results = {
        "name": "sim_cl3_rotor_associativity",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos, "negative": neg, "boundary": bnd, "ablation": ab,
        "classification": "canonical",
        "overall_pass": pos.get("pass") and neg.get("pass") and bnd.get("pass") and ab.get("ablation_shows_numpy_insufficient"),
    }
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "sim_cl3_rotor_associativity_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"PASS={results['overall_pass']} -> {out_path}")
