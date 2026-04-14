#!/usr/bin/env python3
"""sim_geomstats_deep_so3_exp_log_consistency
Deep geomstats tool-integration sim. Load-bearing: geomstats SpecialOrthogonal
exp/log on the Lie group SO(3); admissibility = candidates that survive
exp(log(R)) round-trip under the group's own matrix representation.

scope_note: see system_v5/new docs/ENGINE_MATH_REFERENCE.md (rotor/SO(3) layer)
and LADDERS_FENCES_ADMISSION_REFERENCE.md (exp/log fence).
"""
import json, os, numpy as np

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": ""},
    "pyg": {"tried": False, "used": False, "reason": "not required for Lie group exp/log"},
    "z3": {"tried": False, "used": False, "reason": "real-valued manifold check, not SMT"},
    "cvc5": {"tried": False, "used": False, "reason": "real-valued manifold check, not SMT"},
    "sympy": {"tried": False, "used": False, "reason": "numeric tolerance, not symbolic"},
    "clifford": {"tried": False, "used": False, "reason": "parallel rotor layer, supportive only"},
    "geomstats": {"tried": False, "used": False, "reason": ""},
    "e3nn": {"tried": False, "used": False, "reason": "irreps not involved here"},
    "rustworkx": {"tried": False, "used": False, "reason": "no graph"},
    "xgi": {"tried": False, "used": False, "reason": "no hypergraph"},
    "toponetx": {"tried": False, "used": False, "reason": "no cell complex"},
    "gudhi": {"tried": False, "used": False, "reason": "no persistence"},
}
TOOL_INTEGRATION_DEPTH = {k: None for k in TOOL_MANIFEST}

import geomstats.backend as gs  # noqa
from geomstats.geometry.special_orthogonal import SpecialOrthogonal
TOOL_MANIFEST["geomstats"]["tried"] = True
TOOL_MANIFEST["geomstats"]["used"] = True
TOOL_MANIFEST["geomstats"]["reason"] = "SO(3) group exp/log invertibility is the decisive check"
TOOL_INTEGRATION_DEPTH["geomstats"] = "load_bearing"

SO3 = SpecialOrthogonal(n=3, point_type="matrix")

def _rand_rot(rng):
    pt = SO3.random_point()
    return np.asarray(pt)

def run_positive_tests():
    rng = np.random.default_rng(0)
    errs = []
    for _ in range(20):
        R = _rand_rot(rng)
        xi = SO3.log(R, base_point=SO3.identity)
        R2 = SO3.exp(xi, base_point=SO3.identity)
        errs.append(float(np.linalg.norm(np.asarray(R) - np.asarray(R2))))
    max_err = max(errs)
    return {"roundtrip_max_err": max_err, "pass": max_err < 1e-6, "n": len(errs)}

def run_negative_tests():
    # A non-orthogonal matrix must be excluded by SO(3) membership test.
    M = np.eye(3) + 0.5 * np.array([[0, 1, 0], [0, 0, 0], [0, 0, 0]], dtype=float)
    belongs = bool(SO3.belongs(M, atol=1e-6))
    return {"non_orthogonal_admitted": belongs, "pass": (belongs is False)}

def run_boundary_tests():
    # Near-pi rotation: log is near the branch; exp(log(R)) must still round-trip.
    axis = np.array([0.0, 0.0, 1.0])
    theta = np.pi - 1e-4
    K = np.array([[0, -axis[2], axis[1]], [axis[2], 0, -axis[0]], [-axis[1], axis[0], 0]])
    R = np.eye(3) + np.sin(theta) * K + (1 - np.cos(theta)) * (K @ K)
    xi = SO3.log(R, base_point=SO3.identity)
    R2 = np.asarray(SO3.exp(xi, base_point=SO3.identity))
    err = float(np.linalg.norm(R - R2))
    return {"near_pi_err": err, "pass": err < 1e-4}

if __name__ == "__main__":
    results = {
        "name": "sim_geomstats_deep_so3_exp_log_consistency",
        "classification": "canonical",
        "scope_note": "ENGINE_MATH_REFERENCE.md (SO(3) exp/log) + LADDERS_FENCES_ADMISSION_REFERENCE.md (exp/log fence); survived candidates are those whose SO(3) log/exp round-trip is stable; non-orthogonal matrices are excluded (not constructed).",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": run_positive_tests(),
        "negative": run_negative_tests(),
        "boundary": run_boundary_tests(),
    }
    results["overall_pass"] = all(r["pass"] for r in (results["positive"], results["negative"], results["boundary"]))
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "sim_geomstats_deep_so3_exp_log_consistency_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"PASS={results['overall_pass']} -> {out_path}")
