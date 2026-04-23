#!/usr/bin/env python3
"""sim_geomstats_deep_sphere_geodesic_admissibility
Deep geomstats tool-integration sim. Load-bearing: Hypersphere geodesic +
distance on S^2. Candidates are admissible iff they lie on the manifold and
the triangle inequality survives a probe set; chords (ambient) are excluded.

scope_note: ENGINE_MATH_REFERENCE.md (sphere geometry) +
LADDERS_FENCES_ADMISSION_REFERENCE.md (geodesic admission rung).
"""
import json, os, numpy as np

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": ""},
    "pyg": {"tried": False, "used": False, "reason": "no graph"},
    "z3": {"tried": False, "used": False, "reason": "real-valued geodesic, not SMT"},
    "cvc5": {"tried": False, "used": False, "reason": "real-valued geodesic, not SMT"},
    "sympy": {"tried": False, "used": False, "reason": "numeric"},
    "clifford": {"tried": False, "used": False, "reason": "rotor parallel not decisive"},
    "geomstats": {"tried": False, "used": False, "reason": ""},
    "e3nn": {"tried": False, "used": False, "reason": "no irrep op"},
    "rustworkx": {"tried": False, "used": False, "reason": "no graph"},
    "xgi": {"tried": False, "used": False, "reason": "no hypergraph"},
    "toponetx": {"tried": False, "used": False, "reason": "no cell complex"},
    "gudhi": {"tried": False, "used": False, "reason": "no persistence"},
}
TOOL_INTEGRATION_DEPTH = {k: None for k in TOOL_MANIFEST}

from geomstats.geometry.hypersphere import Hypersphere
TOOL_MANIFEST["geomstats"]["tried"] = True
TOOL_MANIFEST["geomstats"]["used"] = True
TOOL_MANIFEST["geomstats"]["reason"] = "Hypersphere.metric.dist/geodesic is the decisive admissibility probe"
TOOL_INTEGRATION_DEPTH["geomstats"] = "load_bearing"

S2 = Hypersphere(dim=2)

def run_positive_tests():
    rng = np.random.default_rng(1)
    pts = [np.asarray(S2.random_point()) for _ in range(8)]
    viol = 0
    dmax = 0.0
    for i in range(len(pts)):
        for j in range(len(pts)):
            for k in range(len(pts)):
                d_ij = float(S2.metric.dist(pts[i], pts[j]))
                d_jk = float(S2.metric.dist(pts[j], pts[k]))
                d_ik = float(S2.metric.dist(pts[i], pts[k]))
                if d_ik > d_ij + d_jk + 1e-9:
                    viol += 1
                dmax = max(dmax, d_ij)
    return {"triangle_violations": viol, "max_dist": dmax, "pass": viol == 0 and dmax <= np.pi + 1e-6}

def run_negative_tests():
    off = np.array([2.0, 0.0, 0.0])  # ambient chord endpoint, not on S^2
    belongs = bool(S2.belongs(off, atol=1e-9))
    return {"off_manifold_admitted": belongs, "pass": belongs is False}

def run_boundary_tests():
    # Antipodal distance must be exactly pi (up to tol); geodesic midpoint lies on S^2.
    a = np.array([1.0, 0.0, 0.0]); b = np.array([-1.0, 0.0, 0.0])
    d = float(S2.metric.dist(a, b))
    # pick a perpendicular geodesic to avoid singular antipodal log
    a2 = np.array([1.0, 0.0, 0.0]); b2 = np.array([0.0, 1.0, 0.0])
    geo = S2.metric.geodesic(initial_point=a2, end_point=b2)
    mid = np.asarray(geo(np.array([0.5]))[0])
    on = bool(S2.belongs(mid, atol=1e-6))
    return {"antipodal_dist": d, "midpoint_on_sphere": on, "pass": abs(d - np.pi) < 1e-6 and on}

if __name__ == "__main__":
    results = {
        "name": "sim_geomstats_deep_sphere_geodesic_admissibility",
        "classification": "canonical",
        "scope_note": "ENGINE_MATH_REFERENCE.md (sphere) + LADDERS_FENCES_ADMISSION_REFERENCE.md: surviving candidates respect S^2 geodesic distance; ambient chord endpoints are excluded by belongs().",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": run_positive_tests(),
        "negative": run_negative_tests(),
        "boundary": run_boundary_tests(),
    }
    results["overall_pass"] = all(r["pass"] for r in (results["positive"], results["negative"], results["boundary"]))
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "sim_geomstats_deep_sphere_geodesic_admissibility_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"PASS={results['overall_pass']} -> {out_path}")
