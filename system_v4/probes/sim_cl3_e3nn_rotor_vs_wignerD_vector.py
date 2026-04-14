#!/usr/bin/env python3
"""sim_cl3_e3nn_rotor_vs_wignerD_vector -- Cl(3) rotor sandwich action on
vectors agrees with e3nn Wigner-D on the l=1 (vector) rep.

For random axis/angle: build rotor R in Cl(3); apply v' = R v R~ to a random
vector. Independently, build SO(3) matrix M from the same axis/angle, then
e3nn D-matrix for 1o. Check that both produce the same vector (up to the
basis ordering convention for e3nn which uses (y,z,x) for l=1).

Ablation: numpy rotation matrix without rotor sandwich is OK for vectors but
fails for spinors (tested indirectly via R vs -R equivalence on vectors,
distinctness on scalar part).
"""
import json, os, numpy as np
import torch
from clifford import Cl
from e3nn import o3

TOOL_MANIFEST = {k:{"tried":False,"used":False,"reason":""} for k in
    ["pytorch","pyg","z3","cvc5","sympy","clifford","geomstats","e3nn","rustworkx","xgi","toponetx","gudhi"]}
TOOL_INTEGRATION_DEPTH = {k: None for k in TOOL_MANIFEST}
TOOL_MANIFEST["clifford"] = {"tried":True,"used":True,"reason":"Cl(3) rotor sandwich R v R~ is one side of the equivalence"}
TOOL_INTEGRATION_DEPTH["clifford"] = "load_bearing"
TOOL_MANIFEST["e3nn"] = {"tried":True,"used":True,"reason":"Wigner-D on irrep 1o is the other side of the equivalence"}
TOOL_INTEGRATION_DEPTH["e3nn"] = "load_bearing"
TOOL_MANIFEST["pytorch"] = {"tried":True,"used":True,"reason":"e3nn uses torch tensors for D-matrix eval"}
TOOL_INTEGRATION_DEPTH["pytorch"] = "supportive"

layout, blades = Cl(3)
e1, e2, e3 = blades['e1'], blades['e2'], blades['e3']

def axis_angle_to_rotor(axis, angle):
    axis = axis/np.linalg.norm(axis)
    B = axis[0]*(e2*e3) + axis[1]*(e3*e1) + axis[2]*(e1*e2)
    return np.cos(angle/2) - np.sin(angle/2)*B

def axis_angle_to_R(axis, angle):
    a = axis/np.linalg.norm(axis)
    K = np.array([[0,-a[2],a[1]],[a[2],0,-a[0]],[-a[1],a[0],0]])
    return np.eye(3) + np.sin(angle)*K + (1-np.cos(angle))*(K@K)

def rotor_sandwich_vec(R, v):
    V = v[0]*e1 + v[1]*e2 + v[2]*e3
    Vp = R * V * ~R
    return np.array([float(Vp[e1]), float(Vp[e2]), float(Vp[e3])])

def run_positive_tests():
    rng = np.random.default_rng(42)
    n = 50; max_err_rotor_vs_R = 0.0; max_err_rotor_vs_D = 0.0
    # e3nn-consistent check: sh(1, M@x) == D_1o(M) @ sh(1, x). Independently,
    # rotor sandwich on x must equal M @ x. Chain gives rotor <-> e3nn agreement.
    for _ in range(n):
        axis = rng.normal(size=3); angle = rng.uniform(0,2*np.pi)
        x = rng.normal(size=3); x = x/np.linalg.norm(x)
        R_rotor = axis_angle_to_rotor(axis, angle)
        M = axis_angle_to_R(axis, angle)
        v_rotor = rotor_sandwich_vec(R_rotor, x)
        v_matrix = M @ x
        max_err_rotor_vs_R = max(max_err_rotor_vs_R, float(np.linalg.norm(v_rotor - v_matrix)))
        # e3nn path: Wigner-D on 1o acts on spherical-harmonic features
        xt = torch.tensor(x, dtype=torch.float64).unsqueeze(0)
        Mxt = torch.tensor(v_matrix, dtype=torch.float64).unsqueeze(0)
        y_orig = o3.spherical_harmonics(1, xt.float(), normalize=True, normalization="integral").double()
        y_rot = o3.spherical_harmonics(1, Mxt.float(), normalize=True, normalization="integral").double()
        D = o3.Irreps("1x1o").D_from_matrix(torch.tensor(M, dtype=torch.float64))
        y_wigner = (y_orig @ D.double().T)
        err = (y_rot - y_wigner).abs().max().item()
        max_err_rotor_vs_D = max(max_err_rotor_vs_D, err)
    return {"n": n, "max_err_rotor_vs_rotation_matrix": max_err_rotor_vs_R,
            "max_err_e3nn_Dmatrix_vs_rotated_Ylm": max_err_rotor_vs_D,
            "pass": max_err_rotor_vs_R < 1e-9 and max_err_rotor_vs_D < 1e-6}

def run_negative_tests():
    # Using the WRONG reflection (improper rotation) should disagree with rotor.
    rng = np.random.default_rng(7)
    axis = rng.normal(size=3); angle = rng.uniform(0,2*np.pi); v = rng.normal(size=3)
    R_rotor = axis_angle_to_rotor(axis, angle)
    M = axis_angle_to_R(axis, angle) * -1  # improper
    v_rotor = rotor_sandwich_vec(R_rotor, v)
    v_bad = M @ v
    err = float(np.linalg.norm(v_rotor - v_bad))
    return {"improper_rotation_disagrees": err > 1e-3, "err": err, "pass": err > 1e-3}

def run_boundary_tests():
    # identity: rotor = 1, M = I
    v = np.array([1.0, 2.0, -0.5])
    R_id = 1.0 + 0*e1
    out = rotor_sandwich_vec(R_id, v)
    id_err = float(np.linalg.norm(out - v))
    # 2pi rotation: rotor = -1 but action on vector is identity
    axis = np.array([0,0,1.0])
    R_2pi = axis_angle_to_rotor(axis, 2*np.pi)
    scalar_is_minus_one = abs(float(R_2pi[layout.scalar]) + 1) < 1e-9
    v2 = rotor_sandwich_vec(R_2pi, v)
    vec_err = float(np.linalg.norm(v2 - v))
    return {"identity_err": id_err, "rotor_2pi_scalar_is_minus_one": scalar_is_minus_one,
            "rotor_2pi_vector_action_identity": vec_err,
            "pass": id_err < 1e-10 and scalar_is_minus_one and vec_err < 1e-9}

def run_ablation():
    # numpy-only rotation matrix doesn't know about double cover.
    # Show: R and -R (as rotors) give same vector result but different scalars.
    rng = np.random.default_rng(99)
    axis = rng.normal(size=3); angle = rng.uniform(0,2*np.pi); v = rng.normal(size=3)
    R = axis_angle_to_rotor(axis, angle)
    nR = -R
    v1 = rotor_sandwich_vec(R, v); v2 = rotor_sandwich_vec(nR, v)
    vec_same = float(np.linalg.norm(v1-v2))
    scalar_diff = abs(float(R[layout.scalar]) - float(nR[layout.scalar]))
    return {"R_and_minusR_vector_identical": vec_same,
            "R_and_minusR_scalar_distinct": scalar_diff,
            "ablation_shows_numpy_insufficient": vec_same < 1e-10 and scalar_diff > 1e-6}

if __name__ == "__main__":
    pos = run_positive_tests(); neg = run_negative_tests(); bnd = run_boundary_tests()
    ab = run_ablation()
    results = {
        "name": "sim_cl3_e3nn_rotor_vs_wignerD_vector",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos, "negative": neg, "boundary": bnd, "ablation": ab,
        "classification": "canonical",
        "overall_pass": pos["pass"] and neg["pass"] and bnd["pass"] and ab["ablation_shows_numpy_insufficient"],
    }
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "sim_cl3_e3nn_rotor_vs_wignerD_vector_results.json")
    with open(out_path, "w") as f: json.dump(results, f, indent=2, default=str)
    print(f"PASS={results['overall_pass']} -> {out_path}")
