#!/usr/bin/env python3
"""
sim_capability_sklearn_isolated.py -- Isolated tool-capability probe for sklearn.

Classical_baseline capability probe: demonstrates sklearn KMeans clustering,
StandardScaler preprocessing, and silhouette_score evaluation on clearly
separated 2D data. Honest CAN/CANNOT summary. No coupling to other tools.
Per four-sim-kinds doctrine: capability probe precedes any integration sim.
"""

import json
import os

classification = "classical_baseline"

_ISOLATED_REASON = (
    "not used: this probe isolates sklearn capability alone; "
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
    "sklearn":   {"tried": True,  "used": True,  "reason": "load-bearing: sklearn KMeans, StandardScaler, and silhouette_score are the sole subjects; all cluster fitting, scaling, and metric computation is performed directly by sklearn."},
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
    "sklearn":   "load_bearing",
}

SKLEARN_OK = False
SKLEARN_VERSION = None
try:
    from sklearn.cluster import KMeans
    from sklearn.preprocessing import StandardScaler
    from sklearn.metrics import silhouette_score
    import numpy as np
    SKLEARN_OK = True
    try:
        import sklearn
        SKLEARN_VERSION = sklearn.__version__
    except AttributeError:
        SKLEARN_VERSION = "unknown"
except Exception:
    pass


def _make_two_cluster_data(seed=0):
    """40 clearly separated 2D points: 20 near (0,0) and 20 near (10,0)."""
    import numpy as np
    rng = np.random.default_rng(seed)
    c1 = rng.normal(loc=[0.0, 0.0], scale=0.4, size=(20, 2))
    c2 = rng.normal(loc=[10.0, 0.0], scale=0.4, size=(20, 2))
    return np.vstack([c1, c2])


def run_positive_tests():
    r = {}
    if not SKLEARN_OK:
        r["sklearn_available"] = {"pass": False, "detail": "sklearn not importable"}
        return r
    r["sklearn_available"] = {"pass": True, "version": SKLEARN_VERSION}

    import numpy as np
    from sklearn.cluster import KMeans
    from sklearn.preprocessing import StandardScaler
    from sklearn.metrics import silhouette_score

    data = _make_two_cluster_data(seed=0)

    # --- Test 1: KMeans(n_clusters=2) on 40 clearly separated 2D points ---
    km = KMeans(n_clusters=2, random_state=0, n_init=10)
    km.fit(data)
    labels = km.labels_

    inertia_finite = bool(np.isfinite(km.inertia_))
    labels_in_01 = bool(set(int(l) for l in labels).issubset({0, 1}))
    r["kmeans_fit_two_clusters"] = {
        "pass": inertia_finite and labels_in_01,
        "inertia": float(km.inertia_),
        "inertia_finite": inertia_finite,
        "unique_labels": sorted(int(l) for l in set(labels)),
        "labels_in_0_1": labels_in_01,
        "detail": "KMeans(n_clusters=2) on 40 points: inertia finite, labels in {0, 1}",
    }

    # --- Test 2: StandardScaler — mean ~ 0, std ~ 1 after transform ---
    scaler = StandardScaler()
    data_scaled = scaler.fit_transform(data)
    mean_abs_max = float(np.abs(data_scaled.mean(axis=0)).max())
    std_dev_from_1_max = float(np.abs(data_scaled.std(axis=0) - 1.0).max())
    scaler_ok = mean_abs_max < 1e-10 and std_dev_from_1_max < 1e-10
    r["standard_scaler_mean0_std1"] = {
        "pass": scaler_ok,
        "max_abs_mean": mean_abs_max,
        "max_std_deviation_from_1": std_dev_from_1_max,
        "detail": "StandardScaler fit+transform: column means ~ 0, column stds ~ 1",
    }

    # --- Test 3: silhouette_score on well-separated clusters > 0.5 ---
    sil = float(silhouette_score(data, labels))
    r["silhouette_score_gt_0_5"] = {
        "pass": sil > 0.5,
        "silhouette_score": sil,
        "detail": "silhouette_score on well-separated 2-cluster data must be > 0.5",
    }

    return r


def run_negative_tests():
    r = {}
    if not SKLEARN_OK:
        r["sklearn_unavailable"] = {"pass": True, "detail": "skip: sklearn not installed"}
        return r

    import numpy as np
    from sklearn.cluster import KMeans

    # --- Neg 1: KMeans with n_clusters > n_samples raises ValueError ---
    X_tiny = np.array([[0.0, 0.0], [1.0, 1.0]])  # 2 samples
    error_raised = False
    error_msg = None
    try:
        km_bad = KMeans(n_clusters=5, random_state=0, n_init=1)
        km_bad.fit(X_tiny)
    except ValueError as exc:
        error_raised = True
        error_msg = str(exc)[:200]

    r["kmeans_n_clusters_exceeds_n_samples"] = {
        "pass": error_raised,
        "error_raised": error_raised,
        "error_msg": error_msg,
        "detail": "KMeans(n_clusters=5) on 2 samples must raise ValueError",
    }

    return r


def run_boundary_tests():
    r = {}
    if not SKLEARN_OK:
        r["sklearn_unavailable"] = {"pass": True, "detail": "skip: sklearn not installed"}
        return r

    import numpy as np
    from sklearn.cluster import KMeans

    data = _make_two_cluster_data(seed=0)

    # --- Boundary 1: random_state=0 vs random_state=1 give same cluster assignments ---
    # On clearly separated data the solution is stable across seeds
    km0 = KMeans(n_clusters=2, random_state=0, n_init=10)
    km0.fit(data)
    labels0 = km0.labels_

    km1 = KMeans(n_clusters=2, random_state=1, n_init=10)
    km1.fit(data)
    labels1 = km1.labels_

    # Labels may be permuted (cluster 0 vs cluster 1 is arbitrary), so check
    # that either labels match exactly or the permuted version matches
    labels0_arr = np.array(labels0)
    labels1_arr = np.array(labels1)
    match_direct = bool(np.all(labels0_arr == labels1_arr))
    match_flipped = bool(np.all(labels0_arr == (1 - labels1_arr)))
    stable = match_direct or match_flipped

    r["random_state_0_vs_1_stable"] = {
        "pass": stable,
        "match_direct": match_direct,
        "match_flipped": match_flipped,
        "detail": "random_state=0 vs random_state=1 should give same cluster partition on clearly separated data (up to label permutation)",
    }

    # --- Boundary 2: KMeans(n_clusters=1) always converges, inertia >= 0 ---
    km_one = KMeans(n_clusters=1, random_state=0, n_init=1)
    km_one.fit(data)
    r["kmeans_n_clusters_1_inertia_nonneg"] = {
        "pass": bool(np.isfinite(km_one.inertia_) and km_one.inertia_ >= 0),
        "inertia": float(km_one.inertia_),
        "detail": "KMeans(n_clusters=1) always converges; inertia must be finite and >= 0",
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
        "name": "sim_capability_sklearn_isolated",
        "classification": classification,
        "overall_pass": overall,
        "pass_count": pass_count,
        "total_count": total_count,
        "capability_summary": {
            "CAN": [
                "fit KMeans clustering and produce finite inertia with labels in {0,...,k-1}",
                "scale data to zero mean and unit variance with StandardScaler",
                "compute silhouette_score for cluster quality assessment (expected > 0.5 on well-separated data)",
                "produce stable cluster assignments across different random_state values on clear data",
                "converge KMeans(n_clusters=1) on any data with non-negative inertia",
            ],
            "CANNOT": [
                "fit KMeans when n_clusters > n_samples (raises ValueError)",
                "replace formal proof tools (use z3 for logical constraints)",
                "replace persistent homology (use gudhi for TDA)",
                "guarantee deterministic label ordering (cluster 0/1 assignment is arbitrary)",
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
    out_path = os.path.join(out_dir, "sim_capability_sklearn_isolated_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out_path}")
    print(f"overall_pass: {overall}  ({pass_count}/{total_count})")
    for name, v in all_tests.items():
        if isinstance(v, dict) and "pass" in v:
            status = "PASS" if v["pass"] else "FAIL"
            print(f"  [{status}] {name}")
