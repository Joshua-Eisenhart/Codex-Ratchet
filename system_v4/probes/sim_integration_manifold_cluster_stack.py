#!/usr/bin/env python3
"""
sim_integration_manifold_cluster_stack.py
Deep integration reference sim for the manifold/cluster tool bundle:
  pytorch + datasketch + pynndescent + umap + hdbscan + sklearn

Claim:
one latent cluster structure should survive six different computational views:
  - pytorch builds and measures the synthetic tensor manifold.
  - datasketch witnesses token-signature similarity with MinHash/LSH.
  - pynndescent finds approximate nearest-neighbor coherence.
  - umap compresses the manifold to 2D without collapsing the clusters.
  - hdbscan recovers density clusters without fixing k in advance.
  - sklearn scores the recovered partition with ARI + silhouette.

This is a reusable reference lane for scaling the same tool bundle into the
broader system instead of wiring each tool ad hoc in isolation.
"""

import json
import os
import warnings

os.environ.setdefault("MPLCONFIGDIR", "/tmp/codex-mpl")
os.environ.setdefault("NUMBA_CACHE_DIR", "/tmp/codex-numba")
os.makedirs(os.environ["MPLCONFIGDIR"], exist_ok=True)
os.makedirs(os.environ["NUMBA_CACHE_DIR"], exist_ok=True)

import hdbscan
import numpy as np
import torch
import umap
from datasketch import MinHash, MinHashLSH
from pynndescent import NNDescent
from sklearn.metrics import adjusted_rand_score, silhouette_score


classification = "classical_baseline"
divergence_log = (
    "Classical integration baseline: this is a deep bundle reference sim for "
    "the manifold/cluster tool lane, not a canonical nonclassical witness."
)

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing tensor generator and separation witness for the latent manifold samples",
    },
    "datasketch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing MinHash/LSH witness for cluster-signature similarity before any geometric embedding",
    },
    "pynndescent": {
        "tried": True,
        "used": True,
        "reason": "load-bearing approximate nearest-neighbor witness on the raw manifold coordinates",
    },
    "umap": {
        "tried": True,
        "used": True,
        "reason": "load-bearing nonlinear manifold compression from 12D to 2D",
    },
    "hdbscan": {
        "tried": True,
        "used": True,
        "reason": "load-bearing density clustering on the embedded manifold without fixing cluster count",
    },
    "sklearn": {
        "tried": True,
        "used": True,
        "reason": "load-bearing ARI and silhouette validation of the recovered cluster structure",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "datasketch": "load_bearing",
    "pynndescent": "load_bearing",
    "umap": "load_bearing",
    "hdbscan": "load_bearing",
    "sklearn": "load_bearing",
}


warnings.filterwarnings(
    "ignore",
    message="n_jobs value 1 overridden to 1 by setting random_state",
    category=UserWarning,
)


def _make_dataset(mode: str, n_per_cluster: int = 15, dims: int = 12, seed: int = 0):
    generator = torch.Generator().manual_seed(seed)
    prototypes = torch.zeros(3, dims, dtype=torch.float32)
    if mode == "good":
        value = 2.2
    elif mode == "boundary":
        value = 1.2
    elif mode == "collapsed":
        prototypes[:] = 1.6
        value = None
    else:
        raise ValueError(f"unknown mode: {mode}")

    if value is not None:
        prototypes[0, [0, 1, 8, 9]] = value
        prototypes[1, [2, 3, 8, 10]] = value
        prototypes[2, [4, 5, 8, 11]] = value

    xs = []
    ys = []
    for cluster_id in range(3):
        noise = 0.45 * torch.randn(n_per_cluster, dims, generator=generator)
        xs.append(prototypes[cluster_id].unsqueeze(0) + noise)
        ys.extend([cluster_id] * n_per_cluster)
    return torch.cat(xs, dim=0), np.array(ys, dtype=int)


def _signature_tokens(row: torch.Tensor, topk: int = 5) -> set[str]:
    values, indices = torch.topk(row, k=topk)
    return {
        f"d{index}"
        for index, value in zip(indices.tolist(), values.tolist())
        if value > 0.1
    }


def _minhash(tokens: set[str], num_perm: int = 64) -> MinHash:
    mh = MinHash(num_perm=num_perm)
    for token in sorted(tokens):
        mh.update(token.encode("utf-8"))
    return mh


def _datasketch_metrics(x: torch.Tensor, labels: np.ndarray) -> dict[str, float]:
    signatures = [_signature_tokens(row) for row in x]
    centroid_signatures = [
        _signature_tokens(x[torch.tensor(labels == cluster_id)].mean(dim=0))
        for cluster_id in range(3)
    ]
    centroid_hashes = [_minhash(sig) for sig in centroid_signatures]

    assignment_hits = 0
    lsh = MinHashLSH(threshold=0.5, num_perm=64)
    hashes: list[MinHash] = []
    for idx, signature in enumerate(signatures):
        mh = _minhash(signature)
        hashes.append(mh)
        lsh.insert(str(idx), mh)
        estimates = [mh.jaccard(ref) for ref in centroid_hashes]
        if int(np.argmax(estimates)) == int(labels[idx]):
            assignment_hits += 1

    precisions = []
    recalls = []
    edge_count = 0
    for idx, mh in enumerate(hashes):
        neighbors = [int(raw) for raw in lsh.query(mh) if int(raw) != idx]
        if neighbors:
            precisions.append(float(np.mean(labels[neighbors] == labels[idx])))
            edge_count += len(neighbors)
        same_truth = [j for j in range(len(labels)) if j != idx and labels[j] == labels[idx]]
        if same_truth:
            recalls.append(float(sum(j in neighbors for j in same_truth) / len(same_truth)))

    return {
        "assignment_accuracy": assignment_hits / len(signatures),
        "lsh_precision": float(np.mean(precisions)) if precisions else 0.0,
        "lsh_recall": float(np.mean(recalls)) if recalls else 0.0,
        "lsh_edge_count": float(edge_count),
    }


def _pynndescent_purity(x_np: np.ndarray, labels: np.ndarray, n_neighbors: int = 8) -> float:
    index = NNDescent(x_np, n_neighbors=n_neighbors, random_state=42)
    neighbors, _ = index.query(x_np, k=7)
    purities = [
        float(np.mean(labels[row[1:]] == labels[idx]))
        for idx, row in enumerate(neighbors)
    ]
    return float(np.mean(purities))


def _embedding_cluster_metrics(x_np: np.ndarray, labels: np.ndarray, min_cluster_size: int) -> dict[str, object]:
    embedding = umap.UMAP(
        n_components=2,
        n_neighbors=10,
        min_dist=0.05,
        random_state=42,
        low_memory=True,
    ).fit_transform(x_np)
    predicted = hdbscan.HDBSCAN(min_cluster_size=min_cluster_size).fit_predict(embedding)
    ari = float(adjusted_rand_score(labels, predicted))
    active = predicted >= 0
    if active.sum() >= 6 and len(set(predicted[active])) > 1:
        silhouette = float(silhouette_score(embedding[active], predicted[active]))
    else:
        silhouette = None

    embedding_tensor = torch.tensor(embedding, dtype=torch.float32)
    centers = []
    intra = []
    for cluster_id in range(3):
        pts = embedding_tensor[torch.tensor(labels == cluster_id)]
        center = pts.mean(dim=0)
        centers.append(center)
        intra.append(torch.norm(pts - center, dim=1).mean().item())
    inter = []
    for a in range(3):
        for b in range(a + 1, 3):
            inter.append(torch.norm(centers[a] - centers[b]).item())
    margin_ratio = float(min(inter) / (sum(intra) / len(intra)))

    return {
        "embedding_shape": list(embedding.shape),
        "predicted_cluster_count": len(set(predicted.tolist()) - {-1}),
        "noise_count": int(np.sum(predicted == -1)),
        "predicted_labels": sorted(set(int(v) for v in predicted.tolist())),
        "ari": ari,
        "silhouette": silhouette,
        "margin_ratio": margin_ratio,
    }


def _run_case(mode: str, min_cluster_size: int) -> dict[str, object]:
    x, labels = _make_dataset(mode)
    x_np = x.numpy().astype(np.float32)

    datasketch_metrics = _datasketch_metrics(x, labels)
    purity = _pynndescent_purity(x_np, labels)
    embedding_metrics = _embedding_cluster_metrics(x_np, labels, min_cluster_size=min_cluster_size)

    result = {
        "sample_count": int(x.shape[0]),
        "feature_dim": int(x.shape[1]),
        "datasketch_assignment_accuracy": float(datasketch_metrics["assignment_accuracy"]),
        "datasketch_lsh_precision": float(datasketch_metrics["lsh_precision"]),
        "datasketch_lsh_recall": float(datasketch_metrics["lsh_recall"]),
        "datasketch_lsh_edge_count": int(datasketch_metrics["lsh_edge_count"]),
        "pynndescent_knn_purity": purity,
        **embedding_metrics,
    }

    if mode == "good":
        result["pass"] = bool(
            result["datasketch_assignment_accuracy"] >= 0.95
            and result["datasketch_lsh_precision"] >= 0.75
            and result["pynndescent_knn_purity"] >= 0.95
            and result["predicted_cluster_count"] == 3
            and result["ari"] >= 0.95
            and (result["silhouette"] or 0.0) >= 0.85
            and result["margin_ratio"] >= 10.0
        )
    elif mode == "collapsed":
        result["pass"] = bool(
            result["datasketch_assignment_accuracy"] <= 0.75
            and result["datasketch_lsh_precision"] <= 0.5
            and result["pynndescent_knn_purity"] <= 0.6
            and result["predicted_cluster_count"] <= 2
            and result["ari"] <= 0.2
            and result["margin_ratio"] <= 1.5
        )
    elif mode == "boundary":
        result["pass"] = bool(
            result["datasketch_assignment_accuracy"] >= 0.95
            and result["datasketch_lsh_precision"] >= 0.7
            and result["pynndescent_knn_purity"] >= 0.95
            and result["predicted_cluster_count"] >= 2
            and result["ari"] >= 0.95
            and (result["silhouette"] or 0.0) >= 0.85
            and result["margin_ratio"] >= 5.0
        )
    else:
        raise ValueError(f"unknown mode: {mode}")
    return result


def run_positive_tests() -> dict[str, object]:
    return _run_case("good", min_cluster_size=7)


def run_negative_tests() -> dict[str, object]:
    return _run_case("collapsed", min_cluster_size=7)


def run_boundary_tests() -> dict[str, object]:
    return _run_case("boundary", min_cluster_size=7)


if __name__ == "__main__":
    positive = run_positive_tests()
    negative = run_negative_tests()
    boundary = run_boundary_tests()
    overall_pass = bool(positive["pass"] and negative["pass"] and boundary["pass"])

    results = {
        "name": "sim_integration_manifold_cluster_stack",
        "classification": classification,
        "divergence_log": divergence_log,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "tool_bundle": "manifold_cluster_stack",
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "overall_pass": overall_pass,
    }

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "sim_integration_manifold_cluster_stack_results.json")
    with open(out_path, "w", encoding="utf-8") as handle:
        json.dump(results, handle, indent=2, default=str)
    print(f"overall_pass={results['overall_pass']} -> {out_path}")
