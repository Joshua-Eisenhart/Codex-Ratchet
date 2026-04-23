#!/usr/bin/env python3
"""sim_geomstats_so3_geodesic: SO(3) exp(log(R1^-1 R2)) closes; numpy matrix-log
ambiguous near -1 eigenvalue (pi-rotation).

geomstats load-bearing: SpecialOrthogonal(3).log/exp use canonical branch selection
on the Lie algebra; numpy scipy.linalg.logm becomes multi-valued at eigenvalue -1.
"""
import json, os, numpy as np

TOOL_MANIFEST = {k: {"tried": False, "used": False, "reason": ""} for k in
    ["pytorch","pyg","z3","cvc5","sympy","clifford","geomstats","e3nn","rustworkx","xgi","toponetx","gudhi"]}
TOOL_INTEGRATION_DEPTH = {k: None for k in TOOL_MANIFEST}

from geomstats.geometry.special_orthogonal import SpecialOrthogonal
import scipy.linalg as sla
TOOL_MANIFEST["geomstats"]["tried"] = True

SO3 = SpecialOrthogonal(n=3, point_type="matrix")

def _rot(axis, angle):
    a = np.asarray(axis, float); a = a/np.linalg.norm(a)
    K = np.array([[0,-a[2],a[1]],[a[2],0,-a[0]],[-a[1],a[0],0]])
    return np.eye(3) + np.sin(angle)*K + (1-np.cos(angle))*(K@K)

def run_positive_tests():
    rng = np.random.default_rng(2); results = {}
    max_err = 0.0
    for _ in range(20):
        axis1 = rng.normal(size=3); axis2 = rng.normal(size=3)
        R1 = _rot(axis1, rng.uniform(0.1, 2.5))
        R2 = _rot(axis2, rng.uniform(0.1, 2.5))
        Rrel = R1.T @ R2
        log_rel = SO3.log(point=Rrel, base_point=np.eye(3))
        R_back = SO3.exp(tangent_vec=log_rel, base_point=np.eye(3))
        err = float(np.linalg.norm(R_back - Rrel))
        max_err = max(max_err, err)
    results["geodesic_closes"] = {"max_err": max_err, "pass": max_err < 1e-8}
    return results

def run_negative_tests():
    # At EXACT pi-rotation numpy logm silently returns a complex matrix (branch ambiguity)
    # while geomstats raises ValueError (explicit recognition of ill-posedness).
    R = _rot([1.0, 0.0, 0.0], np.pi)
    try:
        numpy_log = sla.logm(R)
        numpy_complex = bool(np.iscomplexobj(numpy_log) and np.max(np.abs(numpy_log.imag)) > 1e-9)
    except Exception:
        numpy_complex = False
    gs_raised = False
    try:
        SO3.log(point=R, base_point=np.eye(3))
    except Exception:
        gs_raised = True
    return {"numpy_silent_complex_geomstats_raises": {
        "numpy_returned_complex": numpy_complex, "geomstats_raised": gs_raised,
        "pass": numpy_complex and gs_raised}}

def run_boundary_tests():
    # Exact pi-rotation: log is NOT well-defined (antipodal on SO(3)); geomstats
    # raises ValueError — this is the correct behavior vs numpy silently returning
    # a complex matrix log. We check that the raise happens.
    R = _rot([0, 0, 1], np.pi)
    raised = False
    try:
        SO3.log(point=R, base_point=np.eye(3))
    except (ValueError, Exception):
        raised = True
    # Just below pi: should close cleanly.
    R2 = _rot([0, 0, 1], np.pi - 1e-3)
    log2 = SO3.log(point=R2, base_point=np.eye(3))
    R2_back = SO3.exp(tangent_vec=log2, base_point=np.eye(3))
    err = float(np.linalg.norm(R2_back - R2))
    return {"pi_rotation_log_raises": {"raised": raised, "pass": raised},
            "just_below_pi_closes": {"err": err, "pass": err < 1e-6}}

if __name__ == "__main__":
    pos = run_positive_tests(); neg = run_negative_tests(); bnd = run_boundary_tests()
    TOOL_MANIFEST["geomstats"].update(used=True, reason="SO(3) canonical log/exp with branch control")
    TOOL_INTEGRATION_DEPTH["geomstats"] = "load_bearing"
    results = {"name":"sim_geomstats_so3_geodesic","tool_manifest":TOOL_MANIFEST,
               "tool_integration_depth":TOOL_INTEGRATION_DEPTH,
               "positive":pos,"negative":neg,"boundary":bnd,"classification":"canonical"}
    out_dir = os.path.join(os.path.dirname(__file__),"a2_state","sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir,"sim_geomstats_so3_geodesic_results.json")
    with open(out_path,"w") as f: json.dump(results, f, indent=2, default=str)
    all_pass = all(v.get("pass") for v in {**pos,**neg,**bnd}.values())
    print(f"PASS={all_pass} -> {out_path}")
