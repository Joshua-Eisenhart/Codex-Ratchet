#!/usr/bin/env python3
"""Classical baseline: constraint_probe_admissibility.
Probes represented as linear inequality rows a.x<=b. Checks probe-set intersection
semantics classically. Substrate innately misses nonclassical contextuality
(Kochen-Specker-like probe-set dependence); divergence logged."""
import json, os, numpy as np
classification = "classical_baseline"
divergence_log = "Classical baseline: probe admissibility is modeled here by linear-inequality intersection numerics, not a canonical nonclassical witness."
TOOL_MANIFEST = {
    "numpy": {"tried": True, "used": True, "reason": "linear-constraint admissibility and probe-set numerics"},
}
TOOL_INTEGRATION_DEPTH = {"numpy": "supportive"}
NAME = "constraint_probe_admissibility"

def admissible_under(probes, x):
    A, b = probes
    return np.all(A @ x <= b + 1e-12)

def run_positive_tests():
    r = {}; rng = np.random.default_rng(0)
    d = 3
    A = rng.standard_normal((6, d)); b = np.ones(6)
    X = rng.standard_normal((5000, d))
    adm = np.all((X @ A.T) <= b + 1e-12, axis=1)
    r["nonempty"] = bool(adm.mean() > 0.01)
    # adding a probe can only shrink admissible set
    A2 = np.vstack([A, rng.standard_normal((1, d))]); b2 = np.concatenate([b, [0.5]])
    adm2 = np.all((X @ A2.T) <= b2 + 1e-12, axis=1)
    r["monotone_under_probe_add"] = bool(adm2.sum() <= adm.sum())
    # permutation invariance (classical)
    perm = rng.permutation(A.shape[0])
    adm3 = np.all((X @ A[perm].T) <= b[perm] + 1e-12, axis=1)
    r["probe_order_invariant"] = bool(np.array_equal(adm, adm3))
    return r

def run_negative_tests():
    r = {}; rng = np.random.default_rng(2)
    A = np.array([[1.0, 0], [-1.0, 0]]); b = np.array([-2.0, -2.0])  # x<=-2 and x>=2: infeasible
    X = rng.standard_normal((1000, 2))
    adm = np.all((X @ A.T) <= b + 1e-12, axis=1)
    r["inconsistent_probes_empty"] = bool(adm.sum() == 0)
    # obviously-outside point rejected
    r["reject_point"] = bool(not admissible_under((np.array([[1.0, 0]]), np.array([0.0])), np.array([5.0, 0.0])))
    return r

def run_boundary_tests():
    r = {}
    # boundary point satisfies with equality
    r["boundary_equality"] = bool(admissible_under((np.array([[1.0, 0]]), np.array([1.0])), np.array([1.0, 0.0])))
    # empty probe set -> everything admissible
    r["empty_probes_all_in"] = bool(admissible_under((np.zeros((0, 2)), np.zeros(0)), np.array([999.0, -999.0])))
    return r

if __name__ == "__main__":
    divergence = {
        "note": "classical probe-set admissibility is order-invariant and monotone; nonclassical is not",
        "missing": ["probe-order contextuality", "noncommuting probe incompatibility",
                    "admissibility change under entanglement with probe"],
    }
    results = {"name": NAME, "classification": "classical_baseline",
               "tool_manifest": TOOL_MANIFEST, "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
               "positive": run_positive_tests(), "negative": run_negative_tests(),
               "boundary": run_boundary_tests(),
               "classical_captured": "linear-inequality admissible region, monotonicity, order-invariance",
               "innately_missing": "probe-order contextuality, noncommuting probe incompatibility",
               "divergence_log": divergence}
    results["all_pass"] = all(v for s in ("positive","negative","boundary") for v in results[s].values())
    out = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results", f"{NAME}_classical_results.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out,"w") as f: json.dump(results,f,indent=2,default=str)
    print(f"all_pass={results['all_pass']} -> {out}")
