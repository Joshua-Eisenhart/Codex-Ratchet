#!/usr/bin/env python3
"""
sim_capability_gudhi_isolated.py -- Isolated tool-capability probe for gudhi.

Classical_baseline capability probe: demonstrates gudhi topological data analysis:
Rips complex, alpha complex, persistence diagrams, Betti numbers, and
persistent homology computation. Honest CAN/CANNOT summary. No coupling to other tools.
Per four-sim-kinds doctrine: capability probe precedes any integration sim.
"""

import json
import os

classification = "classical_baseline"

_ISOLATED_REASON = (
    "not used: this probe isolates gudhi persistent homology capabilities alone; "
    "cross-tool coupling is deferred to a separate integration sim "
    "per the four-sim-kinds doctrine (capability vs integration separation)."
)

TOOL_MANIFEST = {
    "pytorch":   {"tried": False, "used": False, "reason": _ISOLATED_REASON},
    "pyg":       {"tried": False, "used": False, "reason": _ISOLATED_REASON},
    "z3":        {"tried": False, "used": False, "reason": _ISOLATED_REASON},
    "cvc5":      {"tried": False, "used": False, "reason": _ISOLATED_REASON},
    "sympy":     {"tried": False, "used": False, "reason": _ISOLATED_REASON},
    "clifford":  {"tried": False, "used": False, "reason": _ISOLATED_REASON},
    "geomstats": {"tried": False, "used": False, "reason": _ISOLATED_REASON},
    "e3nn":      {"tried": False, "used": False, "reason": _ISOLATED_REASON},
    "rustworkx": {"tried": False, "used": False, "reason": _ISOLATED_REASON},
    "xgi":       {"tried": False, "used": False, "reason": _ISOLATED_REASON},
    "toponetx":  {"tried": False, "used": False, "reason": "toponetx handles topological signal processing on complexes; gudhi handles persistent homology barcodes; complementary but not needed for this isolated probe."},
    "gudhi":     {"tried": True,  "used": True,  "reason": "load-bearing: gudhi RipsComplex, SimplexTree, persistence barcodes, and Betti numbers are the sole subject of this capability probe."},
}

TOOL_INTEGRATION_DEPTH = {
    "pytorch": None, "pyg": None, "z3": None, "cvc5": None,
    "sympy": None, "clifford": None, "geomstats": None, "e3nn": None,
    "rustworkx": None, "xgi": None, "toponetx": None, "gudhi": "load_bearing",
}

GUDHI_OK = False
try:
    import gudhi
    GUDHI_OK = True
except Exception:
    pass


def run_positive_tests():
    r = {}
    if not GUDHI_OK:
        r["gudhi_available"] = {"pass": False, "detail": "gudhi not importable"}
        return r

    import gudhi
    import numpy as np

    r["gudhi_available"] = {"pass": True, "version": gudhi.__version__}

    # --- Test 1: Rips complex on circle-like point cloud ---
    # 8 points on a circle → H0=1 connected component, H1=1 loop (finite bar)
    theta = np.linspace(0, 2 * np.pi, 8, endpoint=False)
    pts = np.column_stack([np.cos(theta), np.sin(theta)])

    rips = gudhi.RipsComplex(points=pts, max_edge_length=2.0)
    st = rips.create_simplex_tree(max_dimension=2)
    st.compute_persistence()

    dgm_all = st.persistence()
    h0_inf = [(b, d) for (dim, (b, d)) in dgm_all if dim == 0 and d == float("inf")]
    h1_bars = [(b, d) for (dim, (b, d)) in dgm_all if dim == 1]
    r["rips_circle_topology"] = {
        "pass": len(h0_inf) == 1 and len(h1_bars) >= 1,
        "h0_infinite_bars": len(h0_inf),
        "h1_bars": len(h1_bars),
        "detail": "Circle: H0=1 infinite component, H1>=1 finite loop bar",
    }

    # --- Test 2: persistence diagram structure ---
    dgm = st.persistence()
    r["persistence_diagram_nonempty"] = {
        "pass": len(dgm) > 0,
        "num_pairs": len(dgm),
        "detail": "Persistence diagram must have at least one (birth, death) pair",
    }

    # --- Test 3: H0 always has at least 1 infinite bar ---
    h0_inf = [(b, d) for (dim, (b, d)) in dgm if dim == 0 and d == float("inf")]
    r["h0_infinite_bar"] = {
        "pass": len(h0_inf) >= 1,
        "h0_inf_count": len(h0_inf),
        "detail": "Connected point cloud: at least 1 H0 bar lives forever",
    }

    # --- Test 4: alpha complex on convex hull ---
    pts_sq = np.array([[0.0, 0.0], [1.0, 0.0], [1.0, 1.0], [0.0, 1.0]])
    alpha = gudhi.AlphaComplex(points=pts_sq)
    st_alpha = alpha.create_simplex_tree()
    st_alpha.compute_persistence()
    betti_sq = st_alpha.betti_numbers()
    r["alpha_complex_square"] = {
        "pass": betti_sq[0] == 1,
        "betti": betti_sq,
        "detail": "Square point cloud: H0=1 (one connected component)",
    }

    # --- Test 5: simplex tree manual construction ---
    st2 = gudhi.SimplexTree()
    st2.insert([0, 1], filtration=0.0)
    st2.insert([1, 2], filtration=0.0)
    st2.insert([0, 2], filtration=0.5)  # closes a triangle at 0.5
    st2.compute_persistence()
    dgm2 = st2.persistence()
    r["simplex_tree_manual"] = {
        "pass": len(dgm2) > 0,
        "num_pairs": len(dgm2),
        "detail": "Manually built simplex tree with persistence",
    }

    return r


def run_negative_tests():
    r = {}
    if not GUDHI_OK:
        r["gudhi_unavailable"] = {"pass": True, "detail": "skip: gudhi not installed"}
        return r

    import gudhi
    import numpy as np

    # --- Neg 1: two separate clusters have H0 >= 2 ---
    pts_two_clusters = np.array([
        [0.0, 0.0], [0.1, 0.0], [0.0, 0.1],  # cluster 1
        [5.0, 5.0], [5.1, 5.0], [5.0, 5.1],  # cluster 2 (far away)
    ])
    rips = gudhi.RipsComplex(points=pts_two_clusters, max_edge_length=0.5)
    st = rips.create_simplex_tree(max_dimension=1)
    st.compute_persistence()
    betti = st.betti_numbers()
    r["two_clusters_h0_equals_2"] = {
        "pass": betti[0] >= 2,
        "betti_h0": betti[0],
        "detail": "Two separate clusters: H0 >= 2 (at least 2 connected components)",
    }

    # --- Neg 2: filled triangle has no H1 loop ---
    # 3 colinear points: no loop
    pts_line = np.array([[0.0, 0.0], [1.0, 0.0], [2.0, 0.0]])
    rips2 = gudhi.RipsComplex(points=pts_line, max_edge_length=3.0)
    st2 = rips2.create_simplex_tree(max_dimension=2)
    st2.compute_persistence()
    betti2 = st2.betti_numbers()
    h1 = betti2[1] if len(betti2) > 1 else 0
    r["line_no_h1_loop"] = {
        "pass": h1 == 0,
        "betti_h1": h1,
        "detail": "Collinear points: no H1 loop (Betti_1 = 0)",
    }

    return r


def run_boundary_tests():
    r = {}
    if not GUDHI_OK:
        r["gudhi_unavailable"] = {"pass": True, "detail": "skip: gudhi not installed"}
        return r

    import gudhi
    import numpy as np

    # --- Boundary 1: two nearby points merge into 1 component ---
    # gudhi doesn't report essential H0 bars for single-point complexes,
    # but for 2+ points we get the full persistence story
    pts_nearby = np.array([[0.0, 0.0], [0.1, 0.0]])
    rips = gudhi.RipsComplex(points=pts_nearby, max_edge_length=0.5)
    st = rips.create_simplex_tree(max_dimension=1)
    st.compute_persistence()
    dgm_near = st.persistence()
    h0_inf_near = [(b, d) for (dim, (b, d)) in dgm_near if dim == 0 and d == float("inf")]
    r["two_nearby_points_one_component"] = {
        "pass": len(h0_inf_near) == 1,
        "h0_inf_bars": len(h0_inf_near),
        "detail": "Two close points: 1 infinite H0 bar (merged into one component)",
    }

    # --- Boundary 2: two identical points ---
    pts_same = np.array([[0.0, 0.0], [0.0, 0.0]])
    rips2 = gudhi.RipsComplex(points=pts_same, max_edge_length=1.0)
    st2 = rips2.create_simplex_tree(max_dimension=1)
    st2.compute_persistence()
    betti2 = st2.betti_numbers()
    r["two_identical_points"] = {
        "pass": betti2[0] == 1,
        "betti": betti2,
        "detail": "Two identical points: merged into H0=1 immediately",
    }

    return r


if __name__ == "__main__":
    pos = run_positive_tests()
    neg = run_negative_tests()
    bnd = run_boundary_tests()

    all_tests = {**pos, **neg, **bnd}
    overall = all([v.get("pass", False) for v in all_tests.values() if isinstance(v, dict) and "pass" in v])

    results = {
        "name": "sim_capability_gudhi_isolated",
        "classification": classification,
        "overall_pass": overall,
        "capability_summary": {
            "CAN": [
                "compute persistent homology (Rips, alpha, Čech complexes)",
                "produce persistence barcodes and diagrams",
                "compute Betti numbers (H0=components, H1=loops, H2=voids)",
                "build simplex trees manually with custom filtrations",
                "detect topological features: connected components, loops, voids",
                "distinguish topologically different point clouds",
            ],
            "CANNOT": [
                "handle topological signal processing on complexes (use toponetx)",
                "learn from topology with gradients (use pytorch + differentiable TDA)",
                "represent hyperedges (use xgi for hypergraphs)",
                "prove topological claims formally (use z3 for logical proofs)",
            ],
        },
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos,
        "negative": neg,
        "boundary": bnd,
    }

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "sim_capability_gudhi_isolated_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out_path}")
    print(f"overall_pass: {overall}")
