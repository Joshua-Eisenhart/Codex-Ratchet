#!/usr/bin/env python3
"""sim_geomstats_deep_lie_group_bch_agreement
Deep geomstats tool-integration sim. Load-bearing: SO(3) group composition
exp(X)*exp(Y) agrees with exp(BCH_2(X,Y)) to second order when ||X||,||Y||
small; noncommuting generators are distinguished from commuting ones.

scope_note: ENGINE_MATH_REFERENCE.md (Lie algebra / BCH layer) +
LADDERS_FENCES_ADMISSION_REFERENCE.md (commutator admission fence).
"""
import json, os, numpy as np

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": ""},
    "pyg": {"tried": False, "used": False, "reason": "no graph"},
    "z3": {"tried": False, "used": False, "reason": "continuous"},
    "cvc5": {"tried": False, "used": False, "reason": "continuous"},
    "sympy": {"tried": False, "used": False, "reason": "numeric"},
    "clifford": {"tried": False, "used": False, "reason": "not decisive here"},
    "geomstats": {"tried": False, "used": False, "reason": ""},
    "e3nn": {"tried": False, "used": False, "reason": "no irrep"},
    "rustworkx": {"tried": False, "used": False, "reason": "no graph"},
    "xgi": {"tried": False, "used": False, "reason": "no hypergraph"},
    "toponetx": {"tried": False, "used": False, "reason": "no cell complex"},
    "gudhi": {"tried": False, "used": False, "reason": "no persistence"},
}
TOOL_INTEGRATION_DEPTH = {k: None for k in TOOL_MANIFEST}

from geomstats.geometry.special_orthogonal import SpecialOrthogonal
TOOL_MANIFEST["geomstats"]["tried"] = True
TOOL_MANIFEST["geomstats"]["used"] = True
TOOL_MANIFEST["geomstats"]["reason"] = "SO(3) group exp + composition are decisive for BCH-admissibility probe"
TOOL_INTEGRATION_DEPTH["geomstats"] = "load_bearing"

SO3 = SpecialOrthogonal(n=3, point_type="matrix")

def _skew(v):
    x, y, z = v
    return np.array([[0, -z, y], [z, 0, -x], [-y, x, 0]], dtype=float)

def run_positive_tests():
    rng = np.random.default_rng(13)
    errs = []
    for _ in range(10):
        u = rng.normal(size=3) * 0.05
        v = rng.normal(size=3) * 0.05
        X = _skew(u); Y = _skew(v)
        Rx = np.asarray(SO3.exp(X, base_point=SO3.identity))
        Ry = np.asarray(SO3.exp(Y, base_point=SO3.identity))
        R_comp = Rx @ Ry
        bch2 = X + Y + 0.5 * (X @ Y - Y @ X)
        R_bch = np.asarray(SO3.exp(bch2, base_point=SO3.identity))
        errs.append(float(np.linalg.norm(R_comp - R_bch)))
    return {"max_err": max(errs), "pass": max(errs) < 1e-3}

def run_negative_tests():
    # Linear approx exp(X+Y) disagrees with Rx@Ry for noncommuting X,Y (excluded).
    X = _skew(np.array([0.3, 0, 0])); Y = _skew(np.array([0, 0.3, 0]))
    Rx = np.asarray(SO3.exp(X, base_point=SO3.identity))
    Ry = np.asarray(SO3.exp(Y, base_point=SO3.identity))
    R_comp = Rx @ Ry
    R_lin = np.asarray(SO3.exp(X + Y, base_point=SO3.identity))
    err = float(np.linalg.norm(R_comp - R_lin))
    return {"noncommuting_gap": err, "pass": err > 1e-3}

def run_boundary_tests():
    # Commuting generators (same axis): exp(X)*exp(Y) = exp(X+Y) exactly.
    X = _skew(np.array([0.4, 0, 0])); Y = _skew(np.array([0.3, 0, 0]))
    Rx = np.asarray(SO3.exp(X, base_point=SO3.identity))
    Ry = np.asarray(SO3.exp(Y, base_point=SO3.identity))
    R_comp = Rx @ Ry
    R_sum = np.asarray(SO3.exp(X + Y, base_point=SO3.identity))
    err = float(np.linalg.norm(R_comp - R_sum))
    return {"commuting_err": err, "pass": err < 1e-8}

if __name__ == "__main__":
    results = {
        "name": "sim_geomstats_deep_lie_group_bch_agreement",
        "classification": "canonical",
        "scope_note": "ENGINE_MATH_REFERENCE.md (Lie algebra/BCH) + LADDERS_FENCES_ADMISSION_REFERENCE.md: small-generator candidates survive under BCH_2; the linear-sum approximation is excluded for noncommuting generators; commuting case collapses to exact equality.",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": run_positive_tests(),
        "negative": run_negative_tests(),
        "boundary": run_boundary_tests(),
    }
    results["overall_pass"] = all(r["pass"] for r in (results["positive"], results["negative"], results["boundary"]))
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "sim_geomstats_deep_lie_group_bch_agreement_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"PASS={results['overall_pass']} -> {out_path}")
