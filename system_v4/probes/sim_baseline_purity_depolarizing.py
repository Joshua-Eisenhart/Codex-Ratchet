#!/usr/bin/env python3
"""Classical baseline: purity tr(rho^2) along depolarizing parameter."""
import json, os, numpy as np

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": "numpy baseline"},
    "pyg": {"tried": False, "used": False, "reason": "no graph"},
    "z3": {"tried": False, "used": False, "reason": "numeric"},
    "cvc5": {"tried": False, "used": False, "reason": "numeric"},
    "sympy": {"tried": False, "used": False, "reason": "numeric"},
    "clifford": {"tried": False, "used": False, "reason": "no GA"},
    "geomstats": {"tried": False, "used": False, "reason": "no manifold"},
    "e3nn": {"tried": False, "used": False, "reason": "no equivariance"},
    "rustworkx": {"tried": False, "used": False, "reason": "no graph"},
    "xgi": {"tried": False, "used": False, "reason": "no hypergraph"},
    "toponetx": {"tried": False, "used": False, "reason": "no complex"},
    "gudhi": {"tried": False, "used": False, "reason": "no persistence"},
}
TOOL_INTEGRATION_DEPTH = {k: None for k in TOOL_MANIFEST}
NUMPY_ROLE = "load_bearing"

def depolarize(rho, p, d=2):
    return (1-p)*rho + p*np.eye(d, dtype=complex)/d

def purity(rho):
    return float(np.trace(rho @ rho).real)

def run_positive_tests():
    r = {}
    # Pure state: p=0 purity=1
    v = np.array([1,0], dtype=complex); rho0 = np.outer(v, v.conj())
    r["pure_p0"] = {"val": purity(rho0), "pass": abs(purity(rho0)-1) < 1e-12}
    # p=1 => I/d, purity = 1/d
    r["p1_maxmixed"] = {"val": purity(depolarize(rho0, 1.0)),
                        "pass": abs(purity(depolarize(rho0, 1.0)) - 0.5) < 1e-12}
    # Analytic: purity(p) = (1-p)^2 + 2(1-p)p/d + p^2/d
    d = 2
    ps = np.linspace(0, 1, 11)
    ok = True
    for p in ps:
        analytic = (1-p)**2 + 2*(1-p)*p/d + p**2/d
        if abs(purity(depolarize(rho0, p)) - analytic) > 1e-12:
            ok = False; break
    r["analytic_curve_match"] = {"pass": ok}
    # Monotone decrease
    vals = [purity(depolarize(rho0, p)) for p in ps]
    r["monotone_decrease"] = {"pass": all(vals[i] >= vals[i+1] - 1e-12 for i in range(len(vals)-1))}
    return r

def run_negative_tests():
    r = {}
    # purity > 1 impossible for valid rho
    v = np.array([1,0], dtype=complex); rho = np.outer(v, v.conj())
    ps = np.linspace(0, 1, 21)
    maxp = max(purity(depolarize(rho, p)) for p in ps)
    r["never_exceeds_1"] = {"max": maxp, "pass": maxp <= 1 + 1e-12}
    # Below lower bound 1/d impossible for depolarizing from pure
    minp = min(purity(depolarize(rho, p)) for p in ps)
    r["never_below_1_over_d"] = {"min": minp, "pass": minp >= 0.5 - 1e-12}
    return r

def run_boundary_tests():
    r = {}
    # d=4 pure state endpoint
    v = np.zeros(4, dtype=complex); v[0] = 1; rho = np.outer(v, v.conj())
    r["d4_p1_purity"] = {"val": purity(depolarize(rho, 1.0, d=4)),
                         "pass": abs(purity(depolarize(rho,1.0,d=4)) - 0.25) < 1e-12}
    # Already mixed state: no change if depolarizing with p=0
    mixed = 0.5*np.eye(2, dtype=complex)
    r["mixed_p0_invariant"] = {"pass": np.allclose(depolarize(mixed, 0.0), mixed, atol=1e-12)}
    # p=1 on any state -> I/d
    rng = np.random.default_rng(7)
    v = rng.normal(size=2) + 1j*rng.normal(size=2); v /= np.linalg.norm(v)
    rho = np.outer(v, v.conj())
    r["p1_invariant_on_any"] = {"pass": np.allclose(depolarize(rho, 1.0), 0.5*np.eye(2), atol=1e-12)}
    return r

if __name__ == "__main__":
    results = {
        "name": "baseline_purity_depolarizing",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "numpy_role": NUMPY_ROLE,
        "positive": run_positive_tests(),
        "negative": run_negative_tests(),
        "boundary": run_boundary_tests(),
        "classification": "classical_baseline",
    }
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "baseline_purity_depolarizing_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    all_pass = all(v.get("pass", False) for sec in ("positive","negative","boundary")
                   for v in results[sec].values())
    print(f"PASS={all_pass} -> {out_path}")
