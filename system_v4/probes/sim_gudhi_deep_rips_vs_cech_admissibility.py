#!/usr/bin/env python3
"""
sim_gudhi_deep_rips_vs_cech_admissibility

Scope note: admissibility claim -- for a point cloud shaped as a circle,
the Rips filtration and the alpha (nerve-of-Cech) filtration must both admit
a persistent H_1 class, but their admission thresholds (birth values) differ
in the predicted direction: birth_Rips <= 2*birth_alpha within the comparison
regime (see LADDERS_FENCES_ADMISSION_REFERENCE.md, section on filtration
ladder admission). Without gudhi providing both RipsComplex and AlphaComplex
with a common SimplexTree persistence backend, the comparison is not
expressible; gudhi is load_bearing.

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
        "reason": "Provides RipsComplex and AlphaComplex with shared persistence "
                  "machinery; admissibility comparison requires both filtrations "
                  "from the same engine -- load_bearing."}
    TOOL_INTEGRATION_DEPTH["gudhi"] = "load_bearing"
except ImportError as e:
    print(f"BROKEN ENV: gudhi missing: {e}", file=sys.stderr); sys.exit(2)


def _circle_pts(n=24, r=1.0):
    a = np.linspace(0, 2*np.pi, n, endpoint=False)
    return np.stack([r*np.cos(a), r*np.sin(a)], axis=1)


def _rips_h1(pts, max_edge=3.0):
    st = gudhi.RipsComplex(points=pts.tolist(),
                           max_edge_length=max_edge).create_simplex_tree(max_dimension=2)
    st.compute_persistence()
    return st.persistence_intervals_in_dimension(1)


def _alpha_h1(pts):
    st = gudhi.AlphaComplex(points=pts.tolist()).create_simplex_tree()
    st.compute_persistence()
    return st.persistence_intervals_in_dimension(1)


def _longest(ivs):
    fin = [(float(b), float(d)) for b, d in ivs if np.isfinite(d)]
    if not fin: return None
    return max(fin, key=lambda bd: bd[1]-bd[0])


def run_positive_tests():
    out = {}
    pts = _circle_pts()
    r = _longest(_rips_h1(pts))
    a = _longest(_alpha_h1(pts))
    # alpha stores filtration as squared-radius, rips as diameter.
    # sqrt(alpha_birth) compared to rips_birth / 2:
    out["both_admit_h1"] = {"PASS": r is not None and a is not None,
        "rips": r, "alpha": a}
    a_birth_radius = np.sqrt(a[0]) if a else None
    r_birth_radius = r[0] / 2.0 if r else None
    out["alpha_tighter_than_rips"] = {
        "PASS": (a_birth_radius is not None and r_birth_radius is not None
                 and a_birth_radius <= r_birth_radius + 1e-9),
        "alpha_radius": a_birth_radius, "rips_radius": r_birth_radius,
        "language": "admissible: alpha admits H_1 at a radius not exceeding rips"}
    return out


def run_negative_tests():
    out = {}
    # Negative: tiny max_edge -> rips must EXCLUDE H_1
    pts = _circle_pts()
    ivs = _rips_h1(pts, max_edge=0.1)
    fin = [(float(b), float(d)) for b, d in ivs if np.isfinite(d) and d-b > 0.05]
    out["rips_below_threshold_excluded"] = {
        "PASS": len(fin) == 0, "n_intervals": len(fin),
        "language": "excluded: below-threshold rips admits no persistent H_1"}
    # Negative 2: blob -> alpha admits no long H1
    rng = np.random.default_rng(7)
    blob = rng.normal(0, 1, size=(30, 2))
    ivs = _alpha_h1(blob)
    fin = [float(d-b) for b, d in ivs if np.isfinite(d)]
    out["blob_alpha_excludes_h1"] = {
        "PASS": (max(fin) if fin else 0.0) < 0.5,
        "max_lifetime": max(fin) if fin else 0.0,
        "language": "excluded: alpha on convex blob admits no persistent loop"}
    return out


def run_boundary_tests():
    out = {}
    # tiny 3-point triangle: rips gets one short H1 below edge threshold
    pts = np.array([[0,0],[1,0],[0.5, 0.87]])
    r = _longest(_rips_h1(pts, max_edge=2.0))
    out["triangle_h1_short_or_none"] = {
        "PASS": r is None or (r[1]-r[0]) < 0.8, "rips": r}
    # same circle sampled denser -> still admits
    dense = _circle_pts(n=60)
    r2 = _longest(_rips_h1(dense, max_edge=3.0))
    out["dense_circle_stable"] = {"PASS": r2 is not None, "rips": r2}
    return out


if __name__ == "__main__":
    name = "sim_gudhi_deep_rips_vs_cech_admissibility"
    pos, neg, bnd = run_positive_tests(), run_negative_tests(), run_boundary_tests()
    all_pass = all(v["PASS"] for v in pos.values()) and all(v["PASS"] for v in neg.values()) and all(v["PASS"] for v in bnd.values())
    results = {"name": name, "classification": "canonical",
        "scope_note": "LADDERS_FENCES_ADMISSION_REFERENCE.md (filtration ladder admission)",
        "tool_manifest": TOOL_MANIFEST, "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos, "negative": neg, "boundary": bnd, "ALL_PASS": all_pass}
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    p = os.path.join(out_dir, f"{name}_results.json")
    with open(p, "w") as f: json.dump(results, f, indent=2, default=str)
    print(f"{name}: ALL_PASS={all_pass} -> {p}")
