#!/usr/bin/env python3
"""
sim_capability_hdbscan_isolated.py
HDBSCAN isolated capability probe.
Isolates and characterizes density-based clustering via hdbscan.
classification = "classical_baseline"
"""

import json
import os
import numpy as np

# =====================================================================
# TOOL MANIFEST -- 12 standard tools, all not-used (isolation probe)
# =====================================================================

TOOL_MANIFEST = {
    "pytorch":    {"tried": False, "used": False, "reason": "not used: this probe isolates hdbscan density-based clustering capability; cross-tool coupling deferred to a separate integration sim per the four-sim-kinds doctrine"},
    "pyg":        {"tried": False, "used": False, "reason": "not used: this probe isolates hdbscan density-based clustering capability; cross-tool coupling deferred to a separate integration sim per the four-sim-kinds doctrine"},
    "z3":         {"tried": False, "used": False, "reason": "not used: this probe isolates hdbscan density-based clustering capability; cross-tool coupling deferred to a separate integration sim per the four-sim-kinds doctrine"},
    "cvc5":       {"tried": False, "used": False, "reason": "not used: this probe isolates hdbscan density-based clustering capability; cross-tool coupling deferred to a separate integration sim per the four-sim-kinds doctrine"},
    "sympy":      {"tried": False, "used": False, "reason": "not used: this probe isolates hdbscan density-based clustering capability; cross-tool coupling deferred to a separate integration sim per the four-sim-kinds doctrine"},
    "clifford":   {"tried": False, "used": False, "reason": "not used: this probe isolates hdbscan density-based clustering capability; cross-tool coupling deferred to a separate integration sim per the four-sim-kinds doctrine"},
    "geomstats":  {"tried": False, "used": False, "reason": "not used: this probe isolates hdbscan density-based clustering capability; cross-tool coupling deferred to a separate integration sim per the four-sim-kinds doctrine"},
    "e3nn":       {"tried": False, "used": False, "reason": "not used: this probe isolates hdbscan density-based clustering capability; cross-tool coupling deferred to a separate integration sim per the four-sim-kinds doctrine"},
    "rustworkx":  {"tried": False, "used": False, "reason": "not used: this probe isolates hdbscan density-based clustering capability; cross-tool coupling deferred to a separate integration sim per the four-sim-kinds doctrine"},
    "xgi":        {"tried": False, "used": False, "reason": "not used: this probe isolates hdbscan density-based clustering capability; cross-tool coupling deferred to a separate integration sim per the four-sim-kinds doctrine"},
    "toponetx":   {"tried": False, "used": False, "reason": "not used: this probe isolates hdbscan density-based clustering capability; cross-tool coupling deferred to a separate integration sim per the four-sim-kinds doctrine"},
    "gudhi":      {"tried": False, "used": False, "reason": "not used: this probe isolates hdbscan density-based clustering capability; cross-tool coupling deferred to a separate integration sim per the four-sim-kinds doctrine"},
}

TOOL_INTEGRATION_DEPTH = {
    "pytorch": None, "pyg": None, "z3": None, "cvc5": None,
    "sympy": None, "clifford": None, "geomstats": None, "e3nn": None,
    "rustworkx": None, "xgi": None, "toponetx": None, "gudhi": None,
}

# Target tool (outside 12-tool manifest)
TARGET_TOOL = {
    "name": "hdbscan",
    "import": "import hdbscan; hdbscan.HDBSCAN",
    "role": "load_bearing",
    "can": [
        "density-based clustering that handles noise natively via -1 label",
        "variable cluster sizes with no need to specify k in advance",
        "cluster persistence scores quantify stability of each cluster",
    ],
    "cannot": [
        "determine optimal number of clusters without running the algorithm",
        "handle high-dimensional data well without dimensionality reduction preprocessing",
        "replace z3 for logical constraint checking or formal proof",
    ],
}

import hdbscan as hdbscan_lib


# =====================================================================
# POSITIVE TESTS
# =====================================================================

def run_positive_tests():
    results = {}

    # 3 tight clusters, 20 points each, seed=42
    rng = np.random.default_rng(42)
    centers = np.array([[0.0, 0.0], [5.0, 0.0], [2.5, 4.0]])
    X = np.vstack([rng.normal(loc=c, scale=0.3, size=(20, 2)) for c in centers])

    clusterer = hdbscan_lib.HDBSCAN(min_cluster_size=5)
    clusterer.fit(X)
    labels = clusterer.labels_

    unique_labels = set(labels) - {-1}
    noise_count = int(np.sum(labels == -1))
    n_clusters = len(unique_labels)

    # Persistence scores: clusterer.cluster_persistence_ (one per cluster)
    persistence_scores = clusterer.cluster_persistence_.tolist() if hasattr(clusterer, "cluster_persistence_") else []
    all_persistence_nonzero = all(p > 0 for p in persistence_scores) if persistence_scores else False

    cluster_labels_found = sorted(unique_labels)
    clusters_match = (n_clusters == 3 and set(cluster_labels_found) == {0, 1, 2})
    noise_low = noise_count < 5

    results["positive_3_tight_clusters"] = {
        "n_clusters_found": n_clusters,
        "cluster_labels": cluster_labels_found,
        "noise_count": noise_count,
        "persistence_scores": persistence_scores,
        "all_persistence_nonzero": all_persistence_nonzero,
        "pass_clusters_3": clusters_match,
        "pass_noise_low": noise_low,
        "pass_persistence_nonzero": all_persistence_nonzero,
        "pass": clusters_match and noise_low and all_persistence_nonzero,
    }

    return results


# =====================================================================
# NEGATIVE TESTS
# =====================================================================

def run_negative_tests():
    results = {}

    # Pure uniform noise, no structure.
    # HDBSCAN may still find low-persistence clusters in uniform data due to
    # random density fluctuations. The correct negative signal is that any
    # clusters found have LOW persistence (< 0.3) compared to the positive
    # test's well-separated clusters (~0.6-0.7). High persistence requires
    # true density separation, which uniform noise cannot provide.
    rng = np.random.default_rng(7)
    X_noise = rng.uniform(low=0.0, high=10.0, size=(100, 2))

    clusterer = hdbscan_lib.HDBSCAN(min_cluster_size=5)
    clusterer.fit(X_noise)
    labels = clusterer.labels_

    noise_count = int(np.sum(labels == -1))
    unique_clusters = set(labels) - {-1}
    n_clusters = len(unique_clusters)

    persistence_scores = clusterer.cluster_persistence_.tolist() if hasattr(clusterer, "cluster_persistence_") and len(clusterer.cluster_persistence_) > 0 else []

    # Negative criterion: no cluster has high persistence (>= 0.3)
    # Uniform noise produces only low-persistence spurious clusters, not stable ones
    no_high_persistence = all(p < 0.3 for p in persistence_scores) if persistence_scores else True

    results["negative_pure_noise"] = {
        "n_clusters_found": n_clusters,
        "noise_count": noise_count,
        "total_points": 100,
        "persistence_scores": persistence_scores,
        "pass_no_high_persistence": no_high_persistence,
        "criterion": "no cluster persistence >= 0.3 (noise lacks true density structure)",
        "pass": no_high_persistence,
    }

    return results


# =====================================================================
# BOUNDARY TESTS
# =====================================================================

def run_boundary_tests():
    results = {}

    # 2 points only
    X_tiny = np.array([[0.0, 0.0], [0.1, 0.1]])
    error_msg = None
    completed = False
    labels = []
    try:
        clusterer = hdbscan_lib.HDBSCAN(min_cluster_size=2)
        clusterer.fit(X_tiny)
        labels = clusterer.labels_.tolist()
        completed = True
    except Exception as e:
        error_msg = str(e)

    # Pass if ran without crashing (result may be 1 cluster or all noise)
    results["boundary_2_points"] = {
        "completed_without_error": completed,
        "labels": labels,
        "error": error_msg,
        "pass": completed,
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
        pos["positive_3_tight_clusters"]["pass"]
        and neg["negative_pure_noise"]["pass"]
        and bnd["boundary_2_points"]["pass"]
    )

    results = {
        "name": "sim_capability_hdbscan_isolated",
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
    out_path = os.path.join(out_dir, "sim_capability_hdbscan_isolated_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out_path}")
    print(f"overall_pass: {all_pass}")
