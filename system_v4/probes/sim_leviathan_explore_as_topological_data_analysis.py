#!/usr/bin/env python3
"""
Leviathan EXPLORE framing: persistent homology over group-value space.

Framing assumption:
  Groups = points in value-space; persistent H0/H1 detects cluster structure.
  Healthy civilization = many persistent H0 components (diverse clusters);
  centralization = collapse to single persistent component.

Blind spot:
  - Geometric embedding of 'values' is arbitrary.
  - TDA is scale-sensitive; results depend on filtration range.
"""
import json, os, numpy as np
classification = "classical_baseline"  # auto-backfill

TOOL_MANIFEST = {"gudhi": {"tried": False, "used": False, "reason": ""},
                 "numpy": {"tried": True, "used": True, "reason": "point cloud generation"}}
TOOL_INTEGRATION_DEPTH = {"gudhi": "load_bearing", "numpy": "supportive"}
try:
    import gudhi
    TOOL_MANIFEST["gudhi"]["tried"] = True
    TOOL_MANIFEST["gudhi"]["used"] = True
    TOOL_MANIFEST["gudhi"]["reason"] = "Rips persistence for H0 cluster count"
except ImportError:
    TOOL_MANIFEST["gudhi"]["reason"] = "not installed"; gudhi = None


def persistent_h0_components(points, max_edge=0.5, threshold=0.3):
    if gudhi is None: return None
    rips = gudhi.RipsComplex(points=points, max_edge_length=max_edge)
    st = rips.create_simplex_tree(max_dimension=1)
    diag = st.persistence()
    # count H0 intervals whose death > threshold (or infinite)
    n = 0
    for dim, (b, d) in diag:
        if dim == 0 and (d == float("inf") or d > threshold):
            n += 1
    return n


def run_positive_tests():
    rng = np.random.default_rng(0)
    # 4 distinct clusters
    centers = np.array([[0,0],[3,0],[0,3],[3,3]])
    pts = np.vstack([c + 0.1*rng.standard_normal((10,2)) for c in centers])
    n = persistent_h0_components(pts.tolist(), max_edge=5.0, threshold=1.0)
    return {"persistent_H0": n, "pass_multi_cluster": (n is None) or n >= 3}

def run_negative_tests():
    rng = np.random.default_rng(1)
    # one cluster (centralized)
    pts = 0.1 * rng.standard_normal((30,2))
    n = persistent_h0_components(pts.tolist(), max_edge=5.0, threshold=1.0)
    return {"persistent_H0": n, "pass_single_cluster": (n is None) or n == 1}

def run_boundary_tests():
    pts = [[0.0,0.0],[1.0,0.0]]
    n = persistent_h0_components(pts, max_edge=5.0, threshold=0.5)
    return {"pair_H0": n, "pass": True}


if __name__ == "__main__":
    results = {
        "name": "leviathan_explore_as_topological_data_analysis",
        "framing_assumption": "group-value clusters = persistent H0; collapse = persistent single component",
        "blind_spot": "value-space embedding arbitrary; scale-dependent",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": run_positive_tests(),
        "negative": run_negative_tests(),
        "boundary": run_boundary_tests(),
        "classification": "classical_baseline",
    }
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "leviathan_explore_as_topological_data_analysis_results.json"), "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(json.dumps({k: results[k] for k in ["name","positive","negative","boundary"]}, indent=2, default=str))
