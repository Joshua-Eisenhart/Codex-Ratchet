#!/usr/bin/env python3
"""
sim_gtower_gudhi_persistence_reduction.py

Persistent homology of the G-tower reduction sequence. Each G-tower layer is
represented by a point cloud. Layers with U(1) fiber structure (U3, SU3) are
sampled as circles; other layers are tight clusters. Rips filtration is applied
to the full point cloud to track which topological features appear and die
as the constraint depth increases.

classification: canonical
"""

import json
import os
import numpy as np

# =====================================================================
# TOOL MANIFEST
# =====================================================================

classification = "tool_lego_fit_probe"

TOOL_MANIFEST = {
    "pytorch":    {"tried": False, "used": False, "reason": "not needed; no autograd"},
    "pyg":        {"tried": False, "used": False, "reason": "not needed; not a GNN task"},
    "z3":         {"tried": False, "used": False, "reason": "not needed; topological claims proved by gudhi"},
    "cvc5":       {"tried": False, "used": False, "reason": "not needed"},
    "sympy":      {"tried": False, "used": False, "reason": "not needed"},
    "clifford":   {"tried": False, "used": False, "reason": "not needed"},
    "geomstats":  {"tried": False, "used": False, "reason": "not needed; using direct geometric sampling"},
    "e3nn":       {"tried": False, "used": False, "reason": "not needed"},
    "rustworkx":  {"tried": False, "used": False, "reason": "not needed"},
    "xgi":        {"tried": False, "used": False, "reason": "not needed; hypergraph sim separate"},
    "toponetx":   {"tried": False, "used": False, "reason": "not needed; CellComplex sim separate"},
    "gudhi":      {"tried": True,  "used": False, "reason": ""},
}

TOOL_INTEGRATION_DEPTH = {
    "pytorch":   None,
    "pyg":       None,
    "z3":        None,
    "cvc5":      None,
    "sympy":     None,
    "clifford":  None,
    "geomstats": None,
    "e3nn":      None,
    "rustworkx": None,
    "xgi":       None,
    "toponetx":  None,
    "gudhi":     None,
}

# ---- imports ----
try:
    import gudhi
    TOOL_MANIFEST["gudhi"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["gudhi"]["reason"] = "not installed"
    gudhi = None

# G-tower layers with their structural properties
# (layer_name, index, has_u1_fiber, circle_radius)
GTOWER_LAYERS = [
    ("GL3",  0, False, 0.0),
    ("O3",   1, False, 0.0),
    ("SO3",  2, False, 0.0),
    ("U3",   3, True,  0.5),   # U(1) fiber => circle
    ("SU3",  4, True,  0.3),   # det=1 constraint => smaller circle
    ("Sp6",  5, False, 0.0),
    ("F4",   6, False, 0.0),
]

LAYER_SPACING = 1.8   # spatial separation between layers
N_PER_LAYER   = 30    # points per layer
MAX_EDGE_LEN  = 2.5   # Rips filtration max edge length
RNG_SEED      = 42


def build_point_cloud():
    """
    Sample representative point clouds for each G-tower layer.
    Layers with U(1) fiber (U3, SU3) are sampled as circles in the xy-plane.
    All other layers are tight Gaussian clusters.
    """
    rng = np.random.default_rng(RNG_SEED)
    all_pts = []
    layer_assignments = []

    for name, idx, has_fiber, radius in GTOWER_LAYERS:
        x_offset = idx * LAYER_SPACING
        if has_fiber:
            # Circle of n_per_layer points: models the U(1) fiber loop
            theta = np.linspace(0, 2 * np.pi, N_PER_LAYER, endpoint=False)
            pts = np.column_stack([
                np.cos(theta) * radius + x_offset,
                np.sin(theta) * radius,
                np.zeros(N_PER_LAYER),
            ])
        else:
            # Tight cluster: no loop structure
            pts = rng.standard_normal((N_PER_LAYER, 3)) * 0.05
            pts[:, 0] += x_offset

        all_pts.append(pts)
        layer_assignments.extend([name] * N_PER_LAYER)

    return np.vstack(all_pts), layer_assignments


def compute_persistence(pts, max_edge_length=MAX_EDGE_LEN):
    """Run Rips persistence on the point cloud."""
    rips = gudhi.RipsComplex(points=pts, max_edge_length=max_edge_length)
    st = rips.create_simplex_tree(max_dimension=2)
    st.compute_persistence()
    diag = st.persistence()
    return diag


def split_by_dim(diag):
    """Split persistence diagram by homology dimension."""
    h = {0: [], 1: [], 2: []}
    for dim, (b, d) in diag:
        if dim in h:
            h[dim].append((b, d))
    return h


# =====================================================================
# POSITIVE TESTS
# =====================================================================

def run_positive_tests():
    results = {}

    if gudhi is None:
        return {"error": "gudhi not installed"}

    pts, labels = build_point_cloud()
    diag = compute_persistence(pts)
    TOOL_MANIFEST["gudhi"]["used"] = True

    hom = split_by_dim(diag)

    # P1: beta_0 = 1 at the end (exactly one infinite H0 feature = connected)
    h0_inf = [(b, d) for b, d in hom[0] if d == float("inf")]
    h0_inf_count = len(h0_inf)
    results["P1_beta0_connected"] = {
        "status": "PASS" if h0_inf_count == 1 else "FAIL",
        "h0_infinite_features": h0_inf_count,
        "expected": 1,
        "note": "Exactly one persistent H0 feature = all points merge into one connected component"
    }

    # P2: U3 and SU3 are the two most persistent H1 features
    # The U(1) fiber (circle) at U3 (r=0.5) creates a larger, longer-lived H1 than SU3 (r=0.3)
    h1_finite = [(b, d) for b, d in hom[1] if d != float("inf")]
    h1_by_persistence = sorted(h1_finite, key=lambda x: x[1] - x[0], reverse=True)
    top2_persistences = [(d - b) for b, d in h1_by_persistence[:2]] if len(h1_by_persistence) >= 2 else []

    # The top H1 feature should have persistence > 0.5 (U3 circle diameter ~ 1.0)
    # The second should be > 0.3 (SU3 circle diameter ~ 0.6)
    top1_ok = len(top2_persistences) >= 1 and top2_persistences[0] > 0.5
    top2_ok = len(top2_persistences) >= 2 and top2_persistences[1] > 0.3
    # U3 loop > SU3 loop (larger radius = longer lifetime)
    u3_dominates = len(top2_persistences) >= 2 and top2_persistences[0] > top2_persistences[1]

    results["P2_u3_su3_dominant_h1_loops"] = {
        "status": "PASS" if (top1_ok and top2_ok and u3_dominates) else "FAIL",
        "h1_finite_total": len(h1_finite),
        "top2_persistences": top2_persistences,
        "top1_persistence_gt_0.5": top1_ok,
        "top2_persistence_gt_0.3": top2_ok,
        "u3_dominates_su3": u3_dominates,
        "note": "U3 circle (r=0.5) creates longer-lived H1 than SU3 circle (r=0.3)"
    }

    # P3: H1 features from circles exist and are distinguishable from noise
    # Noise H1 features (from tight clusters) have very short persistence < 0.05
    # Signal H1 features (from circles) have persistence > 0.3
    h1_signal = [(b, d) for b, d in h1_finite if (d - b) > 0.3]
    h1_noise  = [(b, d) for b, d in h1_finite if (d - b) <= 0.1]
    # Exactly 2 signal features (one per circle layer: U3, SU3)
    signal_count_ok = len(h1_signal) == 2

    results["P3_h1_signal_noise_separation"] = {
        "status": "PASS" if signal_count_ok else "FAIL",
        "h1_signal_features": len(h1_signal),
        "h1_noise_features": len(h1_noise),
        "expected_signal": 2,
        "signal_details": [(float(b), float(d), float(d-b)) for b, d in h1_signal],
        "note": "Exactly 2 long-lived H1 features (U3 and SU3 circles) above noise threshold 0.3"
    }

    return results


# =====================================================================
# NEGATIVE TESTS
# =====================================================================

def run_negative_tests():
    results = {}

    if gudhi is None:
        return {"error": "gudhi not installed"}

    pts, labels = build_point_cloud()
    diag = compute_persistence(pts)
    hom = split_by_dim(diag)

    # N1: No H2 features persist through the full G-tower chain
    # The Rips complex of the G-tower point cloud has no persistent 2-spheres
    h2_all   = hom[2]
    h2_long  = [(b, d) for b, d in h2_all if d == float("inf") or (d - b) > 0.5]
    no_h2    = len(h2_long) == 0

    results["N1_no_persistent_h2"] = {
        "status": "PASS" if no_h2 else "FAIL",
        "h2_total":     len(h2_all),
        "h2_long_lived": len(h2_long),
        "expected_long_lived_h2": 0,
        "note": "G-tower path has no persistent 2-sphere embedding; H2 stays zero"
    }

    # N2: Removing the circular layers (run without U3/SU3 circles)
    # should eliminate the long-lived H1 features
    rng = np.random.default_rng(RNG_SEED)
    pts_no_circles = []
    for name, idx, has_fiber, radius in GTOWER_LAYERS:
        x_offset = idx * LAYER_SPACING
        # Force all layers to clusters (no circles)
        pts_layer = rng.standard_normal((N_PER_LAYER, 3)) * 0.05
        pts_layer[:, 0] += x_offset
        pts_no_circles.append(pts_layer)
    pts_no_circles = np.vstack(pts_no_circles)

    rips_nc = gudhi.RipsComplex(points=pts_no_circles, max_edge_length=MAX_EDGE_LEN)
    st_nc = rips_nc.create_simplex_tree(max_dimension=2)
    st_nc.compute_persistence()
    diag_nc = st_nc.persistence()
    hom_nc = split_by_dim(diag_nc)

    h1_nc_finite  = [(b, d) for b, d in hom_nc[1] if d != float("inf")]
    h1_nc_signal  = [(b, d) for b, d in h1_nc_finite if (d - b) > 0.3]
    circles_gone  = len(h1_nc_signal) == 0

    results["N2_circles_removed_kills_h1_signal"] = {
        "status": "PASS" if circles_gone else "FAIL",
        "h1_signal_without_circles": len(h1_nc_signal),
        "expected": 0,
        "note": "Without circular layers, no long-lived H1 features remain (confirms circles are source)"
    }
    TOOL_MANIFEST["gudhi"]["used"] = True

    return results


# =====================================================================
# BOUNDARY TESTS
# =====================================================================

def run_boundary_tests():
    results = {}

    if gudhi is None:
        return {"error": "gudhi not installed"}

    pts, labels = build_point_cloud()
    diag = compute_persistence(pts)
    hom = split_by_dim(diag)

    # B1: At short max_edge_length (0.1), hypergraph is fully disconnected: many H0 components
    rips_short = gudhi.RipsComplex(points=pts, max_edge_length=0.1)
    st_short = rips_short.create_simplex_tree(max_dimension=1)
    st_short.compute_persistence()
    diag_short = st_short.persistence()
    h0_short = [(b, d) for dim, (b, d) in diag_short if dim == 0]
    h0_short_inf = [(b, d) for b, d in h0_short if d == float("inf")]

    n_expected_components = len(pts)  # all isolated = 210
    short_disconnected = len(h0_short_inf) > 1  # more than 1 component

    results["B1_short_filtration_disconnected"] = {
        "status": "PASS" if short_disconnected else "FAIL",
        "h0_infinite_at_short_length": len(h0_short_inf),
        "n_pts": len(pts),
        "short_edge_disconnected": short_disconnected,
        "note": "At very short max_edge_length, all points isolated => many H0 components"
    }

    # B2: The two most persistent H1 features have distinct persistence values
    # (U3 circle r=0.5 should outlive SU3 circle r=0.3 by a detectably different margin)
    h1_finite = [(b, d) for b, d in hom[1] if d != float("inf")]
    h1_sorted = sorted(h1_finite, key=lambda x: x[1] - x[0], reverse=True)
    if len(h1_sorted) >= 2:
        p1 = h1_sorted[0][1] - h1_sorted[0][0]
        p2 = h1_sorted[1][1] - h1_sorted[1][0]
        gap = p1 - p2
        gap_ok = gap > 0.1  # persistence gap between the two circles > 0.1
    else:
        gap_ok = False
        p1 = p2 = gap = 0.0

    results["B2_u3_su3_persistence_gap"] = {
        "status": "PASS" if gap_ok else "FAIL",
        "persistence_U3_circle": float(p1),
        "persistence_SU3_circle": float(p2),
        "gap": float(gap),
        "expected_gap_gt_0.1": gap_ok,
        "note": "Radius difference 0.5 vs 0.3 creates detectably different persistence lifetimes"
    }

    # B3: H0 merge event at layer boundaries
    # When max_edge_length crosses the inter-layer nearest-neighbor distance (~1.63),
    # isolated cluster components merge into one. Test at thresholds below and above.
    # At thresh=1.5: multiple isolated components exist
    # At thresh=1.7: all clusters have connected (H0_inf = 1)
    rips_below = gudhi.RipsComplex(points=pts, max_edge_length=1.5)
    st_below = rips_below.create_simplex_tree(max_dimension=1)
    st_below.compute_persistence()
    diag_below = st_below.persistence()
    h0_below_inf = [(b, d) for dim, (b, d) in diag_below if dim == 0 and d == float("inf")]

    rips_above = gudhi.RipsComplex(points=pts, max_edge_length=1.7)
    st_above = rips_above.create_simplex_tree(max_dimension=1)
    st_above.compute_persistence()
    diag_above = st_above.persistence()
    h0_above_inf = [(b, d) for dim, (b, d) in diag_above if dim == 0 and d == float("inf")]

    # Below threshold: multiple disconnected components; above: fully merged
    below_disconnected = len(h0_below_inf) > 1
    above_connected    = len(h0_above_inf) == 1
    merge_detected     = below_disconnected and above_connected

    results["B3_h0_merge_at_layer_boundary"] = {
        "status": "PASS" if merge_detected else "FAIL",
        "h0_inf_at_thresh_1.5": len(h0_below_inf),
        "h0_inf_at_thresh_1.7": len(h0_above_inf),
        "below_disconnected": below_disconnected,
        "above_connected": above_connected,
        "merge_detected": merge_detected,
        "note": "Layers are separate clusters at short edge length; merge into one component above ~1.63"
    }

    return results


# =====================================================================
# MAIN
# =====================================================================

if __name__ == "__main__":
    pos = run_positive_tests()
    neg = run_negative_tests()
    bnd = run_boundary_tests()

    if TOOL_MANIFEST["gudhi"]["used"]:
        TOOL_INTEGRATION_DEPTH["gudhi"] = "load_bearing"
    TOOL_INTEGRATION_DEPTH["pytorch"]   = None
    TOOL_INTEGRATION_DEPTH["pyg"]       = None
    TOOL_INTEGRATION_DEPTH["z3"]        = None
    TOOL_INTEGRATION_DEPTH["cvc5"]      = None
    TOOL_INTEGRATION_DEPTH["sympy"]     = None
    TOOL_INTEGRATION_DEPTH["clifford"]  = None
    TOOL_INTEGRATION_DEPTH["geomstats"] = None
    TOOL_INTEGRATION_DEPTH["e3nn"]      = None
    TOOL_INTEGRATION_DEPTH["rustworkx"] = None
    TOOL_INTEGRATION_DEPTH["xgi"]       = None
    TOOL_INTEGRATION_DEPTH["toponetx"]  = None

    results = {
        "name": "sim_gtower_gudhi_persistence_reduction",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos,
        "negative": neg,
        "boundary": bnd,
        "classification": "canonical",
    }

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "sim_gtower_gudhi_persistence_reduction_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out_path}")

    all_tests = {}
    all_tests.update(pos if isinstance(pos, dict) else {})
    all_tests.update(neg if isinstance(neg, dict) else {})
    all_tests.update(bnd if isinstance(bnd, dict) else {})
    passed = sum(1 for v in all_tests.values() if isinstance(v, dict) and v.get("status") == "PASS")
    total  = sum(1 for v in all_tests.values() if isinstance(v, dict) and "status" in v)
    print(f"Tests: {passed}/{total} PASS")
    for k, v in all_tests.items():
        if isinstance(v, dict) and "status" in v:
            print(f"  {v['status']:4s}  {k}")
