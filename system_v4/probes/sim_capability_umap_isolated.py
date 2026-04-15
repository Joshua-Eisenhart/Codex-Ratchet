#!/usr/bin/env python3
"""
sim_capability_umap_isolated.py
UMAP isolated capability probe.
Isolates and characterizes nonlinear dimensionality reduction via umap-learn.
classification = "classical_baseline"
"""

import json
import os
import numpy as np

# =====================================================================
# TOOL MANIFEST -- 12 standard tools, all not-used (isolation probe)
# =====================================================================

TOOL_MANIFEST = {
    "pytorch":    {"tried": False, "used": False, "reason": "not used: this probe isolates umap nonlinear dimensionality reduction capability; cross-tool coupling deferred to a separate integration sim per the four-sim-kinds doctrine"},
    "pyg":        {"tried": False, "used": False, "reason": "not used: this probe isolates umap nonlinear dimensionality reduction capability; cross-tool coupling deferred to a separate integration sim per the four-sim-kinds doctrine"},
    "z3":         {"tried": False, "used": False, "reason": "not used: this probe isolates umap nonlinear dimensionality reduction capability; cross-tool coupling deferred to a separate integration sim per the four-sim-kinds doctrine"},
    "cvc5":       {"tried": False, "used": False, "reason": "not used: this probe isolates umap nonlinear dimensionality reduction capability; cross-tool coupling deferred to a separate integration sim per the four-sim-kinds doctrine"},
    "sympy":      {"tried": False, "used": False, "reason": "not used: this probe isolates umap nonlinear dimensionality reduction capability; cross-tool coupling deferred to a separate integration sim per the four-sim-kinds doctrine"},
    "clifford":   {"tried": False, "used": False, "reason": "not used: this probe isolates umap nonlinear dimensionality reduction capability; cross-tool coupling deferred to a separate integration sim per the four-sim-kinds doctrine"},
    "geomstats":  {"tried": False, "used": False, "reason": "not used: this probe isolates umap nonlinear dimensionality reduction capability; cross-tool coupling deferred to a separate integration sim per the four-sim-kinds doctrine"},
    "e3nn":       {"tried": False, "used": False, "reason": "not used: this probe isolates umap nonlinear dimensionality reduction capability; cross-tool coupling deferred to a separate integration sim per the four-sim-kinds doctrine"},
    "rustworkx":  {"tried": False, "used": False, "reason": "not used: this probe isolates umap nonlinear dimensionality reduction capability; cross-tool coupling deferred to a separate integration sim per the four-sim-kinds doctrine"},
    "xgi":        {"tried": False, "used": False, "reason": "not used: this probe isolates umap nonlinear dimensionality reduction capability; cross-tool coupling deferred to a separate integration sim per the four-sim-kinds doctrine"},
    "toponetx":   {"tried": False, "used": False, "reason": "not used: this probe isolates umap nonlinear dimensionality reduction capability; cross-tool coupling deferred to a separate integration sim per the four-sim-kinds doctrine"},
    "gudhi":      {"tried": False, "used": False, "reason": "not used: this probe isolates umap nonlinear dimensionality reduction capability; cross-tool coupling deferred to a separate integration sim per the four-sim-kinds doctrine"},
}

TOOL_INTEGRATION_DEPTH = {
    "pytorch": None, "pyg": None, "z3": None, "cvc5": None,
    "sympy": None, "clifford": None, "geomstats": None, "e3nn": None,
    "rustworkx": None, "xgi": None, "toponetx": None, "gudhi": None,
}

# Target tool (outside 12-tool manifest)
TARGET_TOOL = {
    "name": "umap",
    "import": "import umap; umap.UMAP(n_components=2, random_state=42)",
    "role": "load_bearing",
    "can": [
        "nonlinear dimensionality reduction preserving local topology of high-dim manifolds",
        "work on high-dimensional data while maintaining cluster structure better than PCA",
        "run faster than t-SNE on large datasets while preserving meaningful neighborhood structure",
    ],
    "cannot": [
        "guarantee global structure preservation, only local neighborhood relationships are reliable",
        "run fully deterministically without random_state because stochastic optimization is used",
        "replace persistent homology tools like gudhi for formal topological analysis",
    ],
}

import umap as umap_lib


def _cluster_separation_ratio(embedding, labels):
    """Compute ratio of mean inter-cluster distance to mean intra-cluster distance."""
    unique_labels = sorted(set(labels))
    centers = []
    intra_dists = []
    for lbl in unique_labels:
        pts = embedding[labels == lbl]
        c = pts.mean(axis=0)
        centers.append(c)
        dists = np.linalg.norm(pts - c, axis=1)
        intra_dists.append(dists.mean())

    centers = np.array(centers)
    mean_intra = float(np.mean(intra_dists))

    # inter-cluster: mean pairwise centroid distance
    inter_dists = []
    for i in range(len(centers)):
        for j in range(i + 1, len(centers)):
            inter_dists.append(np.linalg.norm(centers[i] - centers[j]))
    mean_inter = float(np.mean(inter_dists)) if inter_dists else 0.0

    return mean_inter, mean_intra


# =====================================================================
# POSITIVE TESTS
# =====================================================================

def run_positive_tests():
    results = {}

    # 3 well-separated clusters in 5D, 30 points each, seed=0
    rng = np.random.default_rng(0)
    centers_5d = np.array([
        [0.0, 0.0, 0.0, 0.0, 0.0],
        [8.0, 8.0, 0.0, 0.0, 0.0],
        [0.0, 8.0, 8.0, 0.0, 0.0],
    ])
    X = np.vstack([rng.normal(loc=c, scale=0.5, size=(30, 5)) for c in centers_5d])
    true_labels = np.array([0]*30 + [1]*30 + [2]*30)

    reducer = umap_lib.UMAP(n_components=2, random_state=42)
    embedding = reducer.fit_transform(X)

    shape_ok = (embedding.shape == (90, 2))
    mean_inter, mean_intra = _cluster_separation_ratio(embedding, true_labels)
    separation_ok = mean_inter > mean_intra

    results["positive_3_clusters_5d_to_2d"] = {
        "input_shape": list(X.shape),
        "output_shape": list(embedding.shape),
        "shape_pass": shape_ok,
        "mean_inter_cluster_dist_2d": round(mean_inter, 4),
        "mean_intra_cluster_dist_2d": round(mean_intra, 4),
        "separation_preserved": separation_ok,
        "pass": shape_ok and separation_ok,
    }

    return results


# =====================================================================
# NEGATIVE TESTS
# =====================================================================

def run_negative_tests():
    results = {}

    # n_samples=2 with n_neighbors default (15) should fail; use n_neighbors=1
    X_tiny = np.array([[0.0, 0.0, 0.0], [1.0, 1.0, 1.0]])
    error_caught = False
    error_msg = None
    completed = False
    try:
        # n_neighbors must be < n_samples; 2 samples, n_neighbors=15 will fail
        reducer = umap_lib.UMAP(n_components=2, random_state=42, n_neighbors=15)
        reducer.fit_transform(X_tiny)
        completed = True
    except Exception as e:
        error_caught = True
        error_msg = str(e)

    # Pass if error was raised (expected for 2 points with n_neighbors=15)
    results["negative_too_few_points_default_neighbors"] = {
        "n_samples": 2,
        "n_neighbors_requested": 15,
        "error_caught": error_caught,
        "error_msg": error_msg,
        "completed_unexpectedly": completed,
        "pass": error_caught and not completed,
    }

    return results


# =====================================================================
# BOUNDARY TESTS
# =====================================================================

def run_boundary_tests():
    results = {}

    # 2D → 2D: no actual reduction, UMAP should still run
    rng = np.random.default_rng(1)
    X_2d = rng.normal(size=(30, 2))

    completed = False
    error_msg = None
    output_shape = None
    try:
        reducer = umap_lib.UMAP(n_components=2, random_state=42)
        out = reducer.fit_transform(X_2d)
        output_shape = list(out.shape)
        completed = True
    except Exception as e:
        error_msg = str(e)

    shape_preserved = (output_shape == [30, 2]) if output_shape else False

    results["boundary_2d_to_2d_no_reduction"] = {
        "input_shape": [30, 2],
        "output_shape": output_shape,
        "completed_without_error": completed,
        "shape_preserved": shape_preserved,
        "error": error_msg,
        "pass": completed and shape_preserved,
    }

    return results


# =====================================================================
# MAIN
# =====================================================================

if __name__ == "__main__":
    pos = run_positive_tests()
    neg = run_negative_tests()
    bnd = run_boundary_tests()

    all_pass = (
        pos["positive_3_clusters_5d_to_2d"]["pass"]
        and neg["negative_too_few_points_default_neighbors"]["pass"]
        and bnd["boundary_2d_to_2d_no_reduction"]["pass"]
    )

    results = {
        "name": "sim_capability_umap_isolated",
        "classification": "classical_baseline",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "target_tool": TARGET_TOOL,
        "positive": pos,
        "negative": neg,
        "boundary": bnd,
        "overall_pass": all_pass,
    }

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "sim_capability_umap_isolated_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out_path}")
    print(f"overall_pass: {all_pass}")
