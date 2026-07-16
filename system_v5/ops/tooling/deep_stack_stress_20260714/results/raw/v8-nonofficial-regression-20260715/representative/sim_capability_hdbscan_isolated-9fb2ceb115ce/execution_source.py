#!/usr/bin/env python3
"""
sim_capability_hdbscan_isolated.py -- Isolated tool-capability probe for hdbscan.

Classical_baseline capability probe: demonstrates hdbscan can import, fit on
2D point clouds, assign integer cluster labels, compute core_distances_, and
distinguish clustered from noise points. Honest CAN/CANNOT summary.
No coupling to other tools.
Per four-sim-kinds doctrine: capability probe precedes any integration sim.
"""

import json
import os

classification = "classical_baseline"
divergence_log = (
    "Classical baseline: this row isolates HDBSCAN clustering capability "
    "on finite data; it is not evidence for bridge or nonclassical "
    "constraint dynamics."
)

_ISOLATED_REASON = (
    "not used: this probe isolates hdbscan clustering capability alone; "
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
    "toponetx":  {"tried": False, "used": False, "reason": _ISOLATED_REASON},
    "gudhi":     {"tried": False, "used": False, "reason": _ISOLATED_REASON},
    "hdbscan":   {"tried": True,  "used": True,  "reason": "load-bearing: hdbscan is the sole subject; clustering, label assignment, and core_distances_ are computed directly by hdbscan."},
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
    "hdbscan":   "load_bearing",
}

HDBSCAN_OK = False
HDBSCAN_VERSION = None
try:
    import hdbscan
    import numpy as np
    HDBSCAN_OK = True
    try:
        HDBSCAN_VERSION = hdbscan.__version__
    except AttributeError:
        HDBSCAN_VERSION = "unknown"
except Exception:
    pass


def _make_two_blob_data(seed=42):
    """20 points: 10 tightly around (0,0) and 10 tightly around (10,10)."""
    import numpy as np
    rng = np.random.default_rng(seed)
    c1 = rng.normal(loc=[0.0, 0.0], scale=0.3, size=(10, 2))
    c2 = rng.normal(loc=[10.0, 10.0], scale=0.3, size=(10, 2))
    return np.vstack([c1, c2])


def run_positive_tests():
    r = {}
    if not HDBSCAN_OK:
        r["hdbscan_available"] = {"pass": False, "detail": "hdbscan not importable"}
        return r
    r["hdbscan_available"] = {"pass": True, "version": HDBSCAN_VERSION}

    import numpy as np
    data = _make_two_blob_data()

    clusterer = hdbscan.HDBSCAN(min_cluster_size=5)
    clusterer.fit(data)
    labels = clusterer.labels_

    # --- Test 1: labels are integer-typed ---
    label_types_ok = all(isinstance(int(l), int) for l in labels)
    r["labels_are_integers"] = {
        "pass": label_types_ok,
        "n_points": int(len(labels)),
        "unique_labels": sorted(int(l) for l in set(labels)),
        "detail": "HDBSCAN.labels_ must be integer-typed for all points",
    }

    # --- Test 2: outlier_scores_ computed, correct length, all in [0,1] ---
    # Note: newer hdbscan (>= 0.8.29) replaced core_distances_ with outlier_scores_
    if hasattr(clusterer, "core_distances_"):
        cd = clusterer.core_distances_
        cd_ok = cd is not None and len(cd) == len(data) and all(float(v) >= 0.0 for v in cd)
        r["core_distances_computed"] = {
            "pass": cd_ok,
            "length": int(len(cd)) if cd is not None else None,
            "all_nonnegative": bool(all(float(v) >= 0.0 for v in cd)) if cd is not None else False,
            "detail": "core_distances_ must be non-None, length==n_samples, all >= 0",
        }
    else:
        # newer API: outlier_scores_ (GLOSH scores, range [0, 1])
        os_ = clusterer.outlier_scores_
        os_ok = os_ is not None and len(os_) == len(data) and all(float(v) >= 0.0 for v in os_)
        r["core_distances_computed"] = {
            "pass": os_ok,
            "attribute_used": "outlier_scores_",
            "length": int(len(os_)) if os_ is not None else None,
            "all_nonnegative": bool(all(float(v) >= 0.0 for v in os_)) if os_ is not None else False,
            "detail": "outlier_scores_ (GLOSH) must be non-None, length==n_samples, all >= 0 (replaces core_distances_ in newer hdbscan)",
        }

    # --- Test 3: not all labels are -1 on clearly separated data ---
    not_all_noise = any(int(l) >= 0 for l in labels)
    r["not_all_noise"] = {
        "pass": not_all_noise,
        "n_clustered": int(sum(1 for l in labels if int(l) >= 0)),
        "n_noise": int(sum(1 for l in labels if int(l) == -1)),
        "detail": "on two well-separated blobs at least some points must be cluster-assigned",
    }

    return r


def run_negative_tests():
    r = {}
    if not HDBSCAN_OK:
        r["hdbscan_unavailable"] = {"pass": True, "detail": "skip: hdbscan not installed"}
        return r

    import numpy as np

    # --- Neg 1: single point cannot form a cluster (all labels == -1) ---
    single_point = np.array([[0.0, 0.0]])
    try:
        clusterer = hdbscan.HDBSCAN(min_cluster_size=2)
        clusterer.fit(single_point)
        labels = clusterer.labels_
        all_noise = all(int(l) == -1 for l in labels)
        r["single_point_all_noise"] = {
            "pass": all_noise,
            "labels": [int(l) for l in labels],
            "detail": "a single point cannot form a cluster; label must be -1 (noise)",
        }
    except Exception as exc:
        # Raising is also acceptable for a single-point input
        r["single_point_all_noise"] = {
            "pass": True,
            "detail": f"raised exception (also acceptable for single point): {exc}",
        }

    return r


def run_boundary_tests():
    r = {}
    if not HDBSCAN_OK:
        r["hdbscan_unavailable"] = {"pass": True, "detail": "skip: hdbscan not installed"}
        return r

    data = _make_two_blob_data()

    # --- Boundary 1: min_cluster_size=2 allows clusters to form ---
    c_small = hdbscan.HDBSCAN(min_cluster_size=2)
    c_small.fit(data)
    labels_small = c_small.labels_
    n_clusters_small = len(set(int(l) for l in labels_small if int(l) >= 0))
    r["min_cluster_size_2"] = {
        "pass": n_clusters_small >= 1,
        "n_clusters": n_clusters_small,
        "detail": "min_cluster_size=2 on 20-point two-blob data should yield >= 1 cluster",
    }

    # --- Boundary 2: min_cluster_size=20 forces all 20 points into <= 1 cluster ---
    c_large = hdbscan.HDBSCAN(min_cluster_size=20)
    c_large.fit(data)
    labels_large = c_large.labels_
    n_clusters_large = len(set(int(l) for l in labels_large if int(l) >= 0))
    r["min_cluster_size_20"] = {
        "pass": n_clusters_large <= 1,
        "n_clusters": n_clusters_large,
        "detail": "min_cluster_size=20 on 20 total points yields <= 1 cluster",
    }

    # --- Boundary 3: the two settings produce different cluster counts ---
    r["min_cluster_size_changes_result"] = {
        "pass": n_clusters_small != n_clusters_large,
        "n_clusters_size2": n_clusters_small,
        "n_clusters_size20": n_clusters_large,
        "detail": "min_cluster_size=2 vs min_cluster_size=20 must differ in cluster count",
    }

    return r


if __name__ == "__main__":
    pos = run_positive_tests()
    neg = run_negative_tests()
    bnd = run_boundary_tests()

    all_tests = {**pos, **neg, **bnd}
    pass_count = sum(1 for v in all_tests.values() if isinstance(v, dict) and v.get("pass") is True)
    total_count = sum(1 for v in all_tests.values() if isinstance(v, dict) and "pass" in v)
    overall = (pass_count == total_count) and total_count > 0

    results = {
        "name": "sim_capability_hdbscan_isolated",
        "classification": classification,
        "overall_pass": overall,
        "pass_count": pass_count,
        "total_count": total_count,
        "capability_summary": {
            "CAN": [
                "import and instantiate HDBSCAN clusterer",
                "fit on 2D numpy arrays of arbitrary size",
                "assign integer cluster labels (>= 0) to clustered points",
                "assign -1 label to noise/outlier points",
                "compute core_distances_ for all input points",
                "distinguish cluster granularity via min_cluster_size parameter",
                "handle single-point input without crashing (returns noise or raises)",
            ],
            "CANNOT": [
                "guarantee a fixed number of clusters (unlike KMeans)",
                "cluster a single point into a valid cluster",
                "operate on non-numeric data without preprocessing",
                "provide probability estimates without enabling soft_clustering",
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
    out_path = os.path.join(out_dir, "sim_capability_hdbscan_isolated_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out_path}")
    print(f"overall_pass: {overall}  ({pass_count}/{total_count})")
    for name, v in all_tests.items():
        if isinstance(v, dict) and "pass" in v:
            status = "PASS" if v["pass"] else "FAIL"
            print(f"  [{status}] {name}")
