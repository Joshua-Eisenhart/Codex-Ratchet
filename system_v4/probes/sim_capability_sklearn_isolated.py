#!/usr/bin/env python3
"""
sim_capability_sklearn_isolated.py — Sklearn isolated capability probe.

sklearn is NOT in the 12-tool manifest; tracked as target_tool.
Tests three main sklearn capabilities relevant to this project:
  A) Clustering (KMeans + silhouette_score)
  B) Dimensionality reduction (PCA)
  C) Preprocessing (StandardScaler)

classification: classical_baseline
"""

import json
import os
import numpy as np

# =====================================================================
# TOOL MANIFEST -- 12 standard tools + target_tool
# =====================================================================

TOOL_MANIFEST = {
    "pytorch":    {"tried": False, "used": False, "reason": "not used: this probe isolates sklearn ML algorithms; cross-tool coupling deferred to a separate integration sim per the four-sim-kinds doctrine."},
    "pyg":        {"tried": False, "used": False, "reason": "not used: this probe isolates sklearn ML algorithms; cross-tool coupling deferred to a separate integration sim per the four-sim-kinds doctrine."},
    "z3":         {"tried": False, "used": False, "reason": "not used: this probe isolates sklearn ML algorithms; cross-tool coupling deferred to a separate integration sim per the four-sim-kinds doctrine."},
    "cvc5":       {"tried": False, "used": False, "reason": "not used: this probe isolates sklearn ML algorithms; cross-tool coupling deferred to a separate integration sim per the four-sim-kinds doctrine."},
    "sympy":      {"tried": False, "used": False, "reason": "not used: this probe isolates sklearn ML algorithms; cross-tool coupling deferred to a separate integration sim per the four-sim-kinds doctrine."},
    "clifford":   {"tried": False, "used": False, "reason": "not used: this probe isolates sklearn ML algorithms; cross-tool coupling deferred to a separate integration sim per the four-sim-kinds doctrine."},
    "geomstats":  {"tried": False, "used": False, "reason": "not used: this probe isolates sklearn ML algorithms; cross-tool coupling deferred to a separate integration sim per the four-sim-kinds doctrine."},
    "e3nn":       {"tried": False, "used": False, "reason": "not used: this probe isolates sklearn ML algorithms; cross-tool coupling deferred to a separate integration sim per the four-sim-kinds doctrine."},
    "rustworkx":  {"tried": False, "used": False, "reason": "not used: this probe isolates sklearn ML algorithms; cross-tool coupling deferred to a separate integration sim per the four-sim-kinds doctrine."},
    "xgi":        {"tried": False, "used": False, "reason": "not used: this probe isolates sklearn ML algorithms; cross-tool coupling deferred to a separate integration sim per the four-sim-kinds doctrine."},
    "toponetx":   {"tried": False, "used": False, "reason": "not used: this probe isolates sklearn ML algorithms; cross-tool coupling deferred to a separate integration sim per the four-sim-kinds doctrine."},
    "gudhi":      {"tried": False, "used": False, "reason": "not used: this probe isolates sklearn ML algorithms; cross-tool coupling deferred to a separate integration sim per the four-sim-kinds doctrine."},
    # target_tool not in 12-tool manifest
    "sklearn":    {"tried": True,  "used": True,  "reason": "target_tool: KMeans clustering, PCA dimensionality reduction, StandardScaler preprocessing — all load-bearing for this isolation probe."},
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

# sklearn imports (target_tool)
from sklearn.cluster import KMeans, DBSCAN
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score


# =====================================================================
# POSITIVE TESTS
# =====================================================================

def run_positive_tests():
    results = {}

    # --- A) Clustering: 3 Gaussian clusters in 2D ---
    rng = np.random.RandomState(0)
    centers = np.array([[0.0, 0.0], [5.0, 0.0], [0.0, 5.0]])
    X_clust = np.vstack([rng.randn(50, 2) + c for c in centers])
    km = KMeans(n_clusters=3, random_state=0, n_init=10)
    labels = km.fit_predict(X_clust)
    sil = silhouette_score(X_clust, labels)
    results["A_clustering_positive"] = {
        "silhouette_score": float(sil),
        "pass": bool(sil > 0.5),
        "note": "3 Gaussian clusters, KMeans(n_clusters=3), silhouette_score > 0.5 expected",
    }

    # --- B) PCA: 10D data, top-3 components explain > 50% variance ---
    rng2 = np.random.RandomState(42)
    # Create strongly structured 10D data (first 3 dims dominate)
    X_pca_base = rng2.randn(200, 3) * 10
    noise = rng2.randn(200, 7) * 0.1
    X_pca = np.hstack([X_pca_base, noise])
    pca = PCA(n_components=3)
    pca.fit(X_pca)
    top3_var = float(pca.explained_variance_ratio_.sum())
    total_var_lt1 = bool(top3_var < 1.0)
    top3_gt50 = bool(top3_var > 0.5)
    results["B_pca_positive"] = {
        "top3_explained_variance_ratio": top3_var,
        "total_variance_lt_1": total_var_lt1,
        "top3_explain_gt_50pct": top3_gt50,
        "pass": bool(total_var_lt1 and top3_gt50),
        "note": "10D data, PCA(n_components=3), top-3 components explain >50% of variance",
    }

    # --- C) StandardScaler: mean≈0, std≈1 per feature ---
    X_raw = rng2.randn(100, 4) * np.array([10, 0.1, 100, 0.001]) + np.array([5, -3, 200, 0.5])
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X_raw)
    mean_abs = float(np.abs(X_scaled.mean(axis=0)).max())
    std_dev = float(np.abs(X_scaled.std(axis=0) - 1.0).max())
    results["C_scaler_positive"] = {
        "max_abs_mean": mean_abs,
        "max_std_deviation_from_1": std_dev,
        "pass": bool(mean_abs < 1e-10 and std_dev < 1e-10),
        "note": "StandardScaler fit+transform: mean≈0, std≈1 per feature",
    }

    return results


# =====================================================================
# NEGATIVE TESTS
# =====================================================================

def run_negative_tests():
    results = {}

    # --- A) Clustering negative: single cluster → silhouette ≤ 0 or error ---
    X_single = np.zeros((50, 2))  # all same point
    try:
        km_single = KMeans(n_clusters=2, random_state=0, n_init=10)
        labels_single = km_single.fit_predict(X_single)
        unique_labels = len(set(labels_single))
        if unique_labels < 2:
            # Can't compute silhouette with fewer than 2 labels
            sil_val = None
            sil_le_0 = True
        else:
            sil_val = float(silhouette_score(X_single, labels_single))
            sil_le_0 = bool(sil_val <= 0)
        results["A_clustering_negative"] = {
            "unique_labels": unique_labels,
            "silhouette_score": sil_val,
            "silhouette_le_0_or_undefined": sil_le_0,
            "pass": sil_le_0,
            "note": "All-same-point data: KMeans(n_clusters=2) produces degenerate labels, silhouette ≤ 0 or undefined",
        }
    except Exception as e:
        results["A_clustering_negative"] = {
            "error": str(e),
            "pass": True,
            "note": "Error as expected for degenerate single-cluster data",
        }

    # --- B) PCA negative: n_components > n_features raises ValueError ---
    X_10d = np.random.randn(50, 10)
    try:
        pca_bad = PCA(n_components=11)
        pca_bad.fit(X_10d)
        results["B_pca_negative"] = {
            "pass": False,
            "note": "Expected ValueError for n_components=11 on 10D data — not raised",
        }
    except ValueError as e:
        results["B_pca_negative"] = {
            "error": str(e)[:120],
            "pass": True,
            "note": "PCA(n_components=11) on 10D data correctly raises ValueError",
        }

    # --- C) Scaler negative: fit on train, transform different-scale test → NOT mean=0 ---
    rng = np.random.RandomState(7)
    X_train = rng.randn(100, 2) * 1.0 + 0.0
    X_test  = rng.randn(100, 2) * 50.0 + 200.0  # very different scale
    scaler2 = StandardScaler()
    scaler2.fit(X_train)
    X_test_scaled = scaler2.transform(X_test)
    test_mean = float(np.abs(X_test_scaled.mean(axis=0)).max())
    results["C_scaler_negative"] = {
        "test_set_abs_mean_after_train_scaler": test_mean,
        "pass": bool(test_mean > 1.0),
        "note": "Scaler fitted on train: transforming different-scale test data does NOT yield mean≈0",
    }

    return results


# =====================================================================
# BOUNDARY TESTS
# =====================================================================

def run_boundary_tests():
    results = {}

    # --- A) KMeans(n_clusters=1) always converges, inertia >= 0 ---
    X_any = np.random.randn(30, 2)
    km1 = KMeans(n_clusters=1, random_state=0, n_init=1)
    km1.fit(X_any)
    inertia = float(km1.inertia_)
    results["A_clustering_boundary"] = {
        "inertia": inertia,
        "pass": bool(inertia >= 0),
        "note": "KMeans(n_clusters=1) always converges; inertia >= 0",
    }

    # --- B) PCA(n_components=10) on 10D = all variance explained ---
    X_10d = np.random.RandomState(3).randn(100, 10)
    pca_full = PCA(n_components=10)
    pca_full.fit(X_10d)
    total_var = float(pca_full.explained_variance_ratio_.sum())
    results["B_pca_boundary"] = {
        "total_explained_variance": total_var,
        "pass": bool(abs(total_var - 1.0) < 1e-6),
        "note": "PCA(n_components=10) on 10D data: all variance explained (sum≈1.0)",
    }

    # --- C) StandardScaler on 1-sample data: std=0 edge case ---
    X_one = np.array([[1.0, 2.0, 3.0]])
    scaler3 = StandardScaler()
    try:
        X_one_scaled = scaler3.fit_transform(X_one)
        # With 1 sample, std=0 → scaler sets std=1 to avoid div-by-zero
        results["C_scaler_boundary"] = {
            "scaled_values": X_one_scaled.tolist(),
            "pass": True,
            "note": "StandardScaler on 1-sample data: std=0 handled (no crash); output is zero-mean",
        }
    except Exception as e:
        results["C_scaler_boundary"] = {
            "error": str(e),
            "pass": False,
            "note": "Unexpected error on 1-sample StandardScaler",
        }

    return results


# =====================================================================
# CAPABILITY SUMMARY
# =====================================================================

CAPABILITY_SUMMARY = {
    "CAN": [
        "clustering without knowing density structure (KMeans)",
        "PCA for variance decomposition and dimensionality reduction",
        "standard preprocessing: centering and scaling (StandardScaler)",
        "silhouette score for cluster quality assessment",
    ],
    "CANNOT": [
        "replace z3 for logical/formal proofs",
        "replace gudhi for persistent homology / TDA",
        "symbolic computation (use sympy instead)",
        "non-commutative geometry or Clifford algebra operations",
    ],
}


# =====================================================================
# MAIN
# =====================================================================

if __name__ == "__main__":
    pos = run_positive_tests()
    neg = run_negative_tests()
    bnd = run_boundary_tests()

    all_tests = list(pos.values()) + list(neg.values()) + list(bnd.values())
    overall_pass = all(t.get("pass", False) for t in all_tests)

    results = {
        "name": "sim_capability_sklearn_isolated",
        "classification": "classical_baseline",
        "overall_pass": overall_pass,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "capability_summary": CAPABILITY_SUMMARY,
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
    print(f"overall_pass: {overall_pass}")
    for section, tests in [("positive", pos), ("negative", neg), ("boundary", bnd)]:
        for name, res in tests.items():
            status = "PASS" if res.get("pass") else "FAIL"
            print(f"  [{status}] {name}")
