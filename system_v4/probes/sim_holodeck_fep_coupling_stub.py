#!/usr/bin/env python3
"""sim_holodeck_fep_coupling_stub.

Thesis: the holodeck couples to a FEP (free-energy principle) layer
via KL divergence between a carrier-induced distribution q and a prior
p. Stub interface only -- the FEP family is owned by another agent;
we test the coupling *shape* (nonneg, zero iff identical, monotone in
perturbation), not FEP content.
"""
import numpy as np
import sys, os
classification = "classical_baseline"  # auto-backfill
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _holodeck_common import write_results, summary_ok

divergence_log = "Classical baseline: holodeck-FEP coupling is represented here by a KL-shape stub, not a canonical nonclassical witness."
TOOL_MANIFEST = {
    "numpy": {"tried": True, "used": True, "reason": "KL divergence and distribution-shape numerics"},
    "clifford": {"tried": False, "used": False, "reason": "not needed"},
    "pytorch": {"tried": False, "used": False, "reason": "not needed"},
    "pyg": {"tried": False, "used": False, "reason": "not needed"},
    "z3": {"tried": False, "used": False, "reason": "not needed"},
    "cvc5": {"tried": False, "used": False, "reason": "not needed"},
    "sympy": {"tried": False, "used": False, "reason": "not needed"},
    "geomstats": {"tried": False, "used": False, "reason": "not needed"},
    "e3nn": {"tried": False, "used": False, "reason": "not needed"},
    "rustworkx": {"tried": False, "used": False, "reason": "not needed"},
    "xgi": {"tried": False, "used": False, "reason": "not needed"},
    "toponetx": {"tried": False, "used": False, "reason": "not needed"},
    "gudhi": {"tried": False, "used": False, "reason": "not needed"},
}
TOOL_INTEGRATION_DEPTH = {
    "numpy": "supportive",
    "clifford": None,
    "pytorch": None,
    "pyg": None,
    "z3": None,
    "cvc5": None,
    "sympy": None,
    "geomstats": None,
    "e3nn": None,
    "rustworkx": None,
    "xgi": None,
    "toponetx": None,
    "gudhi": None,
}


def kl(q, p, eps=1e-12):
    q = np.asarray(q) + eps
    p = np.asarray(p) + eps
    q /= q.sum(); p /= p.sum()
    return float(np.sum(q * np.log(q / p)))


def carrier_to_dist(v):
    v = np.abs(np.asarray(v, dtype=float))
    s = v.sum()
    return v / s if s > 0 else np.ones_like(v) / len(v)


def run_positive_tests():
    r = {}
    q = carrier_to_dist([1.0, 2.0, 3.0, 4.0])
    p = carrier_to_dist([1.0, 2.0, 3.0, 4.0])
    r["zero_on_match"] = abs(kl(q, p)) < 1e-9
    p2 = carrier_to_dist([4.0, 3.0, 2.0, 1.0])
    r["positive_on_mismatch"] = kl(q, p2) > 0
    # monotone: bigger perturbation -> bigger KL
    p3 = carrier_to_dist([1.0, 2.0, 3.0, 40.0])
    r["monotone_perturbation"] = kl(q, p3) > kl(q, carrier_to_dist([1.0, 2.0, 3.0, 5.0]))
    return r


def run_negative_tests():
    r = {}
    q = carrier_to_dist([1, 2, 3, 4])
    p = carrier_to_dist([1, 2, 3, 4])
    # Claim KL is negative for identical -- should be False
    r["negative_kl"] = kl(q, p) < -1e-9
    # Claim zero KL for clearly different distributions -- False
    q2 = carrier_to_dist([10, 1, 1, 1])
    p2 = carrier_to_dist([1, 1, 1, 10])
    r["zero_kl_for_different"] = abs(kl(q2, p2)) < 1e-6
    return r


def run_boundary_tests():
    r = {}
    # uniform vs uniform
    u = np.ones(5) / 5
    r["uniform_uniform"] = abs(kl(u, u)) < 1e-9
    # near-degenerate
    q = carrier_to_dist([1e-6, 1, 1, 1])
    p = carrier_to_dist([1, 1, 1, 1e-6])
    r["near_degenerate_finite"] = np.isfinite(kl(q, p))
    return r


if __name__ == "__main__":
    results = {
        "name": "sim_holodeck_fep_coupling_stub",
        "classification": "classical_baseline",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": run_positive_tests(),
        "negative": run_negative_tests(),
        "boundary": run_boundary_tests(),
    }
    results["pass"] = summary_ok(results)
    path = write_results("sim_holodeck_fep_coupling_stub", results)
    print(f"pass={results['pass']} -> {path}")
    sys.exit(0 if results["pass"] else 1)
