#!/usr/bin/env python3
"""Cross-family coupling (classical): entropy x geometry.
Entropy should be nondecreasing along a Fisher-geodesic path from a peaked
simplex point toward the uniform distribution (classical mixing direction).
"""
import json, os, numpy as np

classification = "classical_baseline"

TOOL_MANIFEST = {
    "pytorch": {"tried": True, "used": True, "reason": "supportive cross-check of entropy scalar"},
    "pyg": {"tried": False, "used": False, "reason": "no graph"},
    "z3": {"tried": False, "used": False, "reason": "no proof claim"},
    "cvc5": {"tried": False, "used": False, "reason": "no proof claim"},
    "sympy": {"tried": False, "used": False, "reason": "numeric only"},
    "clifford": {"tried": False, "used": False, "reason": "no multivectors"},
    "geomstats": {"tried": False, "used": False, "reason": "handrolled simplex"},
    "e3nn": {"tried": False, "used": False, "reason": "no equivariance"},
    "rustworkx": {"tried": False, "used": False, "reason": "no graph"},
    "xgi": {"tried": False, "used": False, "reason": "no hypergraph"},
    "toponetx": {"tried": False, "used": False, "reason": "no cell complex"},
    "gudhi": {"tried": False, "used": False, "reason": "no persistence"},
}
TOOL_INTEGRATION_DEPTH = {k: None for k in TOOL_MANIFEST}
TOOL_INTEGRATION_DEPTH["pytorch"] = "supportive"

try:
    import torch
except ImportError:
    torch = None

divergence_log = [
    "Classical Fisher-geodesic entropy monotonicity does NOT capture nonclassical "
    "coupling where distinguishability constraints re-order admissible paths; "
    "constraint-admissibility on the simplex is replaced here by pure Riemannian "
    "geodesic flow (no probe-relative exclusion).",
]

def sqrt_embed(p):
    return np.sqrt(np.clip(p, 0, 1))

def fisher_geodesic(p0, p1, t):
    s0, s1 = sqrt_embed(p0), sqrt_embed(p1)
    cos_phi = np.clip(np.dot(s0, s1), -1.0, 1.0)
    phi = np.arccos(cos_phi)
    if phi < 1e-10:
        s = s0
    else:
        s = (np.sin((1 - t) * phi) * s0 + np.sin(t * phi) * s1) / np.sin(phi)
    p = s * s
    return p / p.sum()

def entropy(p):
    p = np.clip(p, 1e-15, 1)
    return float(-(p * np.log(p)).sum())

def run_positive_tests():
    r = {}
    n = 5
    uniform = np.ones(n) / n
    for seed in range(6):
        rng = np.random.default_rng(seed)
        p0 = rng.dirichlet(np.ones(n) * 0.1)
        H = [entropy(fisher_geodesic(p0, uniform, t)) for t in np.linspace(0, 1, 25)]
        mono = all(H[i + 1] >= H[i] - 1e-9 for i in range(len(H) - 1))
        end_close = abs(H[-1] - np.log(n)) < 1e-6
        r[f"seed_{seed}"] = {"monotone": bool(mono), "end_uniform": bool(end_close),
                             "pass": bool(mono and end_close)}
    if torch is not None:
        p = torch.tensor(uniform)
        r["torch_xcheck"] = {"pass": abs(float(-(p * torch.log(p)).sum()) - np.log(n)) < 1e-6}
    return r

def run_negative_tests():
    r = {}
    n = 5
    rng = np.random.default_rng(0)
    p0 = rng.dirichlet(np.ones(n) * 0.1)
    peaked = np.zeros(n); peaked[0] = 1.0
    H = [entropy(fisher_geodesic(np.ones(n)/n, peaked, t)) for t in np.linspace(0, 1, 20)]
    decreasing = H[0] > H[-1]
    r["uniform_to_peaked_decreases"] = {"pass": bool(decreasing)}
    not_mono = any(H[i+1] < H[i] - 1e-9 for i in range(len(H)-1))
    r["uniform_to_peaked_not_nondecreasing"] = {"pass": bool(not_mono)}
    return r

def run_boundary_tests():
    r = {}
    n = 5
    uniform = np.ones(n)/n
    H = [entropy(fisher_geodesic(uniform, uniform, t)) for t in np.linspace(0,1,10)]
    r["degenerate_same_endpoint"] = {"pass": bool(max(H)-min(H) < 1e-9)}
    p0 = np.array([0.999, 0.0005, 0.0005])
    H2 = entropy(fisher_geodesic(p0, np.ones(3)/3, 0.5))
    r["near_vertex_finite"] = {"pass": bool(np.isfinite(H2))}
    return r

def all_pass(d):
    ok = True
    for v in d.values():
        if isinstance(v, dict):
            if "pass" in v:
                ok = ok and bool(v["pass"])
            else:
                ok = ok and all_pass(v)
    return ok

if __name__ == "__main__":
    pos = run_positive_tests(); neg = run_negative_tests(); bnd = run_boundary_tests()
    ap = all_pass(pos) and all_pass(neg) and all_pass(bnd)
    results = {
        "name": "entropy_fisher_geodesic_crosscouple_classical",
        "classification": classification,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "divergence_log": divergence_log,
        "positive": pos, "negative": neg, "boundary": bnd,
        "all_pass": bool(ap),
        "summary": {"all_pass": bool(ap)},
    }
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "entropy_fisher_geodesic_crosscouple_classical_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"all_pass={ap} -> {out_path}")
