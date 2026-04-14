#!/usr/bin/env python3
"""
sim_gudhi_deep_persistent_h1_excludes_trivial_homology

Scope note: admissibility claim -- a filtration built over an annulus-shaped
point cloud must admit one persistent H_1 class whose (birth, death) interval
has positive length, while a filtration over a convex blob must exclude any
such class (no persistent loop). See
system_v5/new docs/CONSTRAINT_ON_DISTINGUISHABILITY_FULL_MATH.md (persistent
classes as distinguishability witnesses). Without gudhi computing persistence
pairs on a filtered SimplexTree, there is no admissibility operator at all --
recomputing persistence in numpy would replicate exactly the tool under test.
gudhi is load_bearing.

Classification: canonical.
"""
import json, os, sys
import numpy as np

TOOL_MANIFEST = {k: {"tried": False, "used": False, "reason": ""} for k in
    ["pytorch","pyg","z3","cvc5","sympy","clifford","geomstats","e3nn","rustworkx","xgi","toponetx","gudhi"]}
TOOL_INTEGRATION_DEPTH = {k: None for k in TOOL_MANIFEST}

try:
    import gudhi
    TOOL_MANIFEST["gudhi"] = {"tried": True, "used": True,
        "reason": "RipsComplex + SimplexTree.persistence_intervals_in_dimension "
                  "is the only admissibility probe for persistent H_k. Removing "
                  "gudhi removes the claim's referent -- load_bearing."}
    TOOL_INTEGRATION_DEPTH["gudhi"] = "load_bearing"
except ImportError as e:
    print(f"BROKEN ENV: gudhi missing: {e}", file=sys.stderr); sys.exit(2)


def _annulus(n=40, r1=1.0, r2=2.0, seed=0):
    rng = np.random.default_rng(seed)
    thetas = rng.uniform(0, 2*np.pi, n)
    rs = rng.uniform(r1, r2, n)
    return np.stack([rs*np.cos(thetas), rs*np.sin(thetas)], axis=1)


def _blob(n=40, seed=0):
    rng = np.random.default_rng(seed)
    return rng.normal(0, 1, size=(n, 2))


def _persistent_h1(points, max_edge=3.0):
    rc = gudhi.RipsComplex(points=points.tolist(), max_edge_length=max_edge)
    st = rc.create_simplex_tree(max_dimension=2)
    st.compute_persistence()
    return st.persistence_intervals_in_dimension(1)


def run_positive_tests():
    out = {}
    ivs = _persistent_h1(_annulus())
    # require at least one interval with death-birth larger than any blob interval
    lifetimes = [float(d-b) for b, d in ivs if np.isfinite(d)]
    max_life = max(lifetimes) if lifetimes else 0.0
    out["annulus_persistent_loop"] = {
        "PASS": max_life > 0.3, "max_lifetime": max_life,
        "n_intervals": len(ivs),
        "language": "admissible: persistent 1-cycle survives filtration"}
    return out


def run_negative_tests():
    out = {}
    ivs = _persistent_h1(_blob())
    lifetimes = [float(d-b) for b, d in ivs if np.isfinite(d)]
    max_life = max(lifetimes) if lifetimes else 0.0
    out["blob_excludes_persistent_loop"] = {
        "PASS": max_life < 0.3, "max_lifetime": max_life,
        "language": "excluded: convex cloud admits no persistent 1-cycle"}
    # Negative 2: two separate clusters -> persistent H0 classes, no persistent H1
    pts = np.concatenate([_blob(20, seed=1) - 5, _blob(20, seed=2) + 5])
    ivs2 = _persistent_h1(pts, max_edge=2.0)
    lifetimes2 = [float(d-b) for b, d in ivs2 if np.isfinite(d)]
    out["two_clusters_no_h1"] = {
        "PASS": (max(lifetimes2) if lifetimes2 else 0.0) < 0.3,
        "max_lifetime": max(lifetimes2) if lifetimes2 else 0.0,
        "language": "excluded: disjoint clusters admit no persistent loop"}
    return out


def run_boundary_tests():
    out = {}
    # tight annulus (thin): loop still detected
    # evenly sampled thin annulus to ensure loop closure
    import numpy as _np
    n = 60
    ang = _np.linspace(0, 2*_np.pi, n, endpoint=False)
    pts = _np.stack([2.0*_np.cos(ang), 2.0*_np.sin(ang)], axis=1)
    ivs = _persistent_h1(pts, max_edge=4.5)
    lifetimes = [float(d-b) for b, d in ivs if np.isfinite(d)]
    out["thin_annulus_still_admissible"] = {
        "PASS": (max(lifetimes) if lifetimes else 0) > 0.5,
        "max_lifetime": max(lifetimes) if lifetimes else 0.0}
    # tiny point cloud (3 pts): cannot form a persistent H1
    ivs_tiny = _persistent_h1(np.array([[0,0],[1,0],[0,1]]), max_edge=2.0)
    lifetimes_t = [float(d-b) for b, d in ivs_tiny if np.isfinite(d)]
    out["tiny_cloud_no_h1"] = {
        "PASS": (max(lifetimes_t) if lifetimes_t else 0.0) < 0.1,
        "max_lifetime": max(lifetimes_t) if lifetimes_t else 0.0}
    return out


if __name__ == "__main__":
    name = "sim_gudhi_deep_persistent_h1_excludes_trivial_homology"
    pos, neg, bnd = run_positive_tests(), run_negative_tests(), run_boundary_tests()
    all_pass = all(v["PASS"] for v in pos.values()) and all(v["PASS"] for v in neg.values()) and all(v["PASS"] for v in bnd.values())
    results = {"name": name, "classification": "canonical",
        "scope_note": "CONSTRAINT_ON_DISTINGUISHABILITY_FULL_MATH.md (persistent class distinguishability)",
        "tool_manifest": TOOL_MANIFEST, "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos, "negative": neg, "boundary": bnd, "ALL_PASS": all_pass}
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    p = os.path.join(out_dir, f"{name}_results.json")
    with open(p, "w") as f: json.dump(results, f, indent=2, default=str)
    print(f"{name}: ALL_PASS={all_pass} -> {p}")
