#!/usr/bin/env python3
"""
sim_hdbscan_umap_verdict_clustering.py

Canonical sim. Build verdict signatures from real sim result JSONs under
system_v4/probes/a2_state/sim_results/, UMAP-reduce to 2D, HDBSCAN cluster.

Patient-convergence note: we emit cluster count and tool-family coverage
per cluster but do NOT claim a Rosetta-mapping unless at least 3 tool
families overlap within a cluster. Reporting field only.
"""

import json
import os
import glob
import numpy as np

TOOL_MANIFEST = {
    "hdbscan": {"tried": False, "used": False, "reason": ""},
    "umap-learn": {"tried": False, "used": False, "reason": ""},
    "numpy": {"tried": True, "used": True, "reason": "signature vector assembly"},
}
TOOL_INTEGRATION_DEPTH = {
    "hdbscan": None, "umap-learn": None, "numpy": "supportive",
}

try:
    import hdbscan
    TOOL_MANIFEST["hdbscan"]["tried"] = True
    TOOL_MANIFEST["hdbscan"]["used"] = True
    TOOL_MANIFEST["hdbscan"]["reason"] = "density-based clustering of UMAP-reduced verdict signatures"
    TOOL_INTEGRATION_DEPTH["hdbscan"] = "load_bearing"
    HDBSCAN_OK = True
except ImportError:
    HDBSCAN_OK = False

try:
    import umap
    TOOL_MANIFEST["umap-learn"]["tried"] = True
    TOOL_MANIFEST["umap-learn"]["used"] = True
    TOOL_MANIFEST["umap-learn"]["reason"] = "nonlinear dim-reduction of verdict signature space"
    TOOL_INTEGRATION_DEPTH["umap-learn"] = "load_bearing"
    UMAP_OK = True
except ImportError:
    UMAP_OK = False


TOOL_FAMILIES = ["pytorch", "pyg", "z3", "cvc5", "sympy", "clifford",
                 "geomstats", "e3nn", "rustworkx", "xgi", "toponetx", "gudhi"]


def signature_from_result(path):
    try:
        with open(path) as f:
            data = json.load(f)
    except Exception:
        return None, None
    if not isinstance(data, dict):
        return None, None
    tm = data.get("tool_manifest") or {}
    td = data.get("tool_integration_depth") or {}
    if not isinstance(tm, dict):
        tm = {}
    if not isinstance(td, dict):
        td = {}
    vec = []
    tool_presence = {}
    for t in TOOL_FAMILIES:
        entry = tm.get(t)
        if not isinstance(entry, dict):
            entry = {}
        tried = bool(entry.get("tried", False))
        used = bool(entry.get("used", False))
        depth = td.get(t) if isinstance(td, dict) else None
        lb = 1.0 if depth == "load_bearing" else 0.0
        sp = 1.0 if depth == "supportive" else 0.0
        vec.extend([float(tried), float(used), lb, sp])
        tool_presence[t] = used or lb > 0
    # classification bit
    vec.append(1.0 if data.get("classification") == "canonical" else 0.0)
    # positive/negative/boundary presence
    for key in ("positive", "negative", "boundary"):
        vec.append(1.0 if data.get(key) else 0.0)
    return np.array(vec, dtype=float), tool_presence


def collect_signatures(results_dir, max_files=300):
    paths = sorted(glob.glob(os.path.join(results_dir, "*.json")))
    # Prefer fattest files (most information) if we exceed cap
    if len(paths) > max_files:
        paths = sorted(paths, key=lambda p: os.path.getsize(p), reverse=True)[:max_files]
    sigs = []
    presences = []
    names = []
    for p in paths:
        v, tp = signature_from_result(p)
        if v is None:
            continue
        sigs.append(v)
        presences.append(tp)
        names.append(os.path.basename(p))
    if not sigs:
        return None, None, None
    return np.vstack(sigs), presences, names


def run_positive_tests():
    if not (HDBSCAN_OK and UMAP_OK):
        return {"tools_available": False}
    here = os.path.dirname(__file__)
    results_dir = os.path.join(here, "a2_state", "sim_results")
    X, presences, names = collect_signatures(results_dir)
    if X is None or X.shape[0] < 10:
        return {"n_signatures": 0 if X is None else int(X.shape[0]),
                "insufficient_data": True}
    n = X.shape[0]
    # Keep dim-reduction modest
    reducer = umap.UMAP(n_components=2, n_neighbors=min(15, max(2, n - 1)),
                        min_dist=0.1, random_state=1)
    X2 = reducer.fit_transform(X)
    clusterer = hdbscan.HDBSCAN(min_cluster_size=max(5, n // 50))
    labels = clusterer.fit_predict(X2)
    noise_frac = float(np.mean(labels == -1))
    uniq = sorted(set(labels.tolist()) - {-1})
    n_clusters = len(uniq)

    # Tool-family overlap per cluster (reporting only)
    cluster_tool_overlap = {}
    for c in uniq:
        idxs = np.where(labels == c)[0]
        families_present = set()
        for i in idxs:
            for t, ok in presences[i].items():
                if ok:
                    families_present.add(t)
        cluster_tool_overlap[str(c)] = {
            "size": int(len(idxs)),
            "tool_families": sorted(families_present),
            "n_tool_families": len(families_present),
        }
    rosetta_eligible = any(v["n_tool_families"] >= 3
                           for v in cluster_tool_overlap.values())
    return {
        "n_signatures": int(n),
        "n_clusters": n_clusters,
        "noise_fraction": noise_frac,
        "cluster_tool_overlap": cluster_tool_overlap,
        "rosetta_eligible_report_only": bool(rosetta_eligible),
        "cluster_found": n_clusters >= 1,
        "noise_below_0_95": noise_frac < 0.95,
    }


def run_negative_tests():
    # Negative: pure-noise random signatures should yield no meaningful cluster
    # (or nearly all noise). Report observed noise fraction.
    if not (HDBSCAN_OK and UMAP_OK):
        return {"skipped": True}
    rng = np.random.default_rng(0)
    X = rng.normal(size=(80, 8))
    reducer = umap.UMAP(n_components=2, n_neighbors=10, random_state=1)
    X2 = reducer.fit_transform(X)
    labels = hdbscan.HDBSCAN(min_cluster_size=10).fit_predict(X2)
    noise_frac = float(np.mean(labels == -1))
    n_clusters = len(set(labels.tolist()) - {-1})
    return {"random_noise_frac": noise_frac, "random_n_clusters": n_clusters,
            "noise_dominant_or_few_clusters": noise_frac > 0.2 or n_clusters <= 5}


def run_boundary_tests():
    # Boundary: signature length is stable across a known file (if present).
    here = os.path.dirname(__file__)
    results_dir = os.path.join(here, "a2_state", "sim_results")
    any_json = sorted(glob.glob(os.path.join(results_dir, "*.json")))
    if not any_json:
        return {"skipped": True}
    v, _ = signature_from_result(any_json[0])
    return {"signature_dim": None if v is None else int(v.shape[0])}


if __name__ == "__main__":
    pos = run_positive_tests()
    neg = run_negative_tests()
    bnd = run_boundary_tests()
    passed = (
        HDBSCAN_OK and UMAP_OK
        and pos.get("cluster_found", False)
        and pos.get("noise_below_0_95", False)
    )
    results = {
        "name": "sim_hdbscan_umap_verdict_clustering",
        "classification": "canonical",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos,
        "negative": neg,
        "boundary": bnd,
        "passed": bool(passed),
    }
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "sim_hdbscan_umap_verdict_clustering_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"PASS={passed} -> {out_path}")
