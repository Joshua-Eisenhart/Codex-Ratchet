#!/usr/bin/env python3
"""
sim_integration_manifold_search_archive_stack.py

Deep bridge sim for two previously separate lanes:
  pytorch + datasketch + pynndescent + umap + hdbscan + sklearn + optuna + ribs

Claim:
one shared latent-manifold pipeline should support both structure recovery
and search discipline.
  - pytorch builds the synthetic manifold and candidate score surface.
  - datasketch measures token-signature locality before embedding.
  - pynndescent measures approximate neighbor purity on the raw manifold.
  - umap projects the manifold to 2D under searched hyperparameters.
  - hdbscan clusters the projected manifold without fixing k in advance.
  - sklearn scores the recovered partition with ARI and silhouette.
  - optuna searches the hyperparameter surface.
  - ribs archives candidate configurations by coverage-oriented behaviors.

This is a classical integration baseline: the point is a reusable large-stack
reference lane, not a canonical nonclassical witness.
"""

from __future__ import annotations

import json
import os
import warnings

os.environ.setdefault("MPLCONFIGDIR", "/tmp/codex-mpl")
os.environ.setdefault("NUMBA_CACHE_DIR", "/tmp/codex-numba")
os.makedirs(os.environ["MPLCONFIGDIR"], exist_ok=True)
os.makedirs(os.environ["NUMBA_CACHE_DIR"], exist_ok=True)

import hdbscan
import numpy as np
import optuna
import torch
import umap
from datasketch import MinHash, MinHashLSH
from pynndescent import NNDescent
from ribs.archives import GridArchive
from sklearn.metrics import adjusted_rand_score, silhouette_score


classification = "classical_baseline"
divergence_log = (
    "Classical integration baseline: this bridges the manifold/cluster and "
    "search/archive lanes into one reusable large-stack witness."
)

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing manifold generator and score surface for all searched configurations",
    },
    "datasketch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing MinHash/LSH locality witness on raw manifold signatures",
    },
    "pynndescent": {
        "tried": True,
        "used": True,
        "reason": "load-bearing approximate nearest-neighbor purity witness on raw coordinates",
    },
    "umap": {
        "tried": True,
        "used": True,
        "reason": "load-bearing nonlinear embedding under searched hyperparameters",
    },
    "hdbscan": {
        "tried": True,
        "used": True,
        "reason": "load-bearing density clustering on searched embeddings without fixing k in advance",
    },
    "sklearn": {
        "tried": True,
        "used": True,
        "reason": "load-bearing ARI and silhouette validation of searched clustering outcomes",
    },
    "optuna": {
        "tried": True,
        "used": True,
        "reason": "load-bearing search over embedding and clustering hyperparameters",
    },
    "ribs": {
        "tried": True,
        "used": True,
        "reason": "load-bearing archive of searched configurations by assignment and silhouette behaviors",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "datasketch": "load_bearing",
    "pynndescent": "load_bearing",
    "umap": "load_bearing",
    "hdbscan": "load_bearing",
    "sklearn": "load_bearing",
    "optuna": "load_bearing",
    "ribs": "load_bearing",
}


warnings.filterwarnings(
    "ignore",
    message="n_jobs value 1 overridden to 1 by setting random_state",
    category=UserWarning,
)
optuna.logging.set_verbosity(optuna.logging.WARNING)


def _make_dataset(mode: str, seed: int = 0, n_per_cluster: int = 16, dims: int = 12):
    generator = torch.Generator().manual_seed(seed)
    prototypes = torch.zeros(3, dims, dtype=torch.float32)
    if mode == "good":
        amplitude = 2.4
        noise_scale = 0.35
    elif mode == "boundary":
        amplitude = 1.45
        noise_scale = 0.5
    elif mode == "collapsed":
        amplitude = 0.7
        noise_scale = 0.95
    else:
        raise ValueError(f"unknown mode: {mode}")

    prototypes[0, [0, 1, 8, 9]] = amplitude
    prototypes[1, [2, 3, 8, 10]] = amplitude
    prototypes[2, [4, 5, 8, 11]] = amplitude
    if mode == "collapsed":
        prototypes += 0.35

    xs = []
    ys = []
    for cluster_id in range(3):
        noise = noise_scale * torch.randn(n_per_cluster, dims, generator=generator)
        xs.append(prototypes[cluster_id].unsqueeze(0) + noise)
        ys.extend([cluster_id] * n_per_cluster)
    x_t = torch.cat(xs, dim=0)
    y = np.array(ys, dtype=int)
    return x_t, y


def _signature_tokens(row: torch.Tensor, topk: int = 5) -> set[str]:
    values, indices = torch.topk(row, k=topk)
    return {
        f"d{index}"
        for index, value in zip(indices.tolist(), values.tolist())
        if value > 0.15
    }


def _minhash(tokens: set[str], num_perm: int = 64) -> MinHash:
    mh = MinHash(num_perm=num_perm)
    for token in sorted(tokens):
        mh.update(token.encode("utf-8"))
    return mh


def _lsh_precision(x_t: torch.Tensor, labels: np.ndarray) -> float:
    token_sets = [_signature_tokens(row) for row in x_t]
    minhashes = [_minhash(tokens) for tokens in token_sets]
    lsh = MinHashLSH(threshold=0.55, num_perm=64)
    for idx, mh in enumerate(minhashes):
        lsh.insert(f"p{idx}", mh)

    scores = []
    for idx, mh in enumerate(minhashes):
        matches = [int(key[1:]) for key in lsh.query(mh) if key != f"p{idx}"]
        if not matches:
            continue
        same = sum(labels[j] == labels[idx] for j in matches)
        scores.append(same / len(matches))
    return float(np.mean(scores)) if scores else 0.0


def _nn_purity(x_np: np.ndarray, labels: np.ndarray) -> float:
    index = NNDescent(x_np, n_neighbors=6, random_state=0)
    neighbors, _ = index.query(x_np, k=6)
    scores = []
    for idx, row in enumerate(neighbors):
        local = [nbr for nbr in row.tolist() if nbr != idx]
        if not local:
            continue
        same = sum(labels[nbr] == labels[idx] for nbr in local)
        scores.append(same / len(local))
    return float(np.mean(scores)) if scores else 0.0


def _config_from_trial(trial: optuna.trial.Trial) -> dict[str, float]:
    return {
        "n_neighbors": float(trial.suggest_int("n_neighbors", 4, 18)),
        "min_dist": float(trial.suggest_float("min_dist", 0.0, 0.45)),
        "min_cluster_size": float(trial.suggest_int("min_cluster_size", 4, 10)),
        "min_samples": float(trial.suggest_int("min_samples", 1, 5)),
    }


def _run_pipeline(mode: str, config: dict[str, float], seed: int = 0) -> dict[str, float]:
    x_t, labels = _make_dataset(mode, seed=seed)
    x_np = x_t.numpy()
    lsh_precision = _lsh_precision(x_t, labels)
    nn_purity = _nn_purity(x_np, labels)

    reducer = umap.UMAP(
        n_components=2,
        n_neighbors=int(config["n_neighbors"]),
        min_dist=float(config["min_dist"]),
        metric="euclidean",
        random_state=0,
    )
    embedding = reducer.fit_transform(x_np)

    clusterer = hdbscan.HDBSCAN(
        min_cluster_size=int(config["min_cluster_size"]),
        min_samples=int(config["min_samples"]),
    )
    predicted = clusterer.fit_predict(embedding)
    assignment_rate = float(np.mean(predicted != -1))

    ari = float(adjusted_rand_score(labels, predicted))
    assigned_mask = predicted != -1
    assigned_labels = predicted[assigned_mask]
    silhouette = -1.0
    if assigned_mask.sum() >= 4 and len(set(assigned_labels.tolist())) >= 2:
        silhouette = float(silhouette_score(embedding[assigned_mask], assigned_labels))

    cluster_count = len(set(predicted.tolist()) - {-1})
    score = (
        1.6 * ari
        + 0.45 * max(silhouette, 0.0)
        + 0.35 * assignment_rate
        + 0.25 * lsh_precision
        + 0.25 * nn_purity
    )
    return {
        "score": float(score),
        "assignment_rate": assignment_rate,
        "ari": ari,
        "silhouette": float(silhouette),
        "cluster_count": float(cluster_count),
        "lsh_precision": float(lsh_precision),
        "nn_purity": float(nn_purity),
    }


def _archive_from_trials(trials: list[dict[str, float]]) -> GridArchive:
    archive = GridArchive(
        solution_dim=4,
        dims=[6, 6],
        ranges=[(0.0, 1.0), (0.0, 1.0)],
    )
    for row in trials:
        archive.add_single(
            solution=np.array(
                [
                    row["n_neighbors"],
                    row["min_dist"],
                    row["min_cluster_size"],
                    row["min_samples"],
                ],
                dtype=float,
            ),
            objective=float(row["score"]),
            measures=np.array(
                [
                    float((row["n_neighbors"] - 4.0) / 14.0),
                    float((row["min_cluster_size"] - 4.0) / 6.0),
                ],
                dtype=float,
            ),
        )
    return archive


def _search_mode(mode: str, n_trials: int, seed: int) -> dict[str, object]:
    rows: list[dict[str, float]] = []

    def objective(trial: optuna.trial.Trial) -> float:
        config = _config_from_trial(trial)
        metrics = _run_pipeline(mode, config, seed=seed)
        rows.append({**config, **metrics})
        return float(metrics["score"])

    sampler = optuna.samplers.TPESampler(seed=seed)
    study = optuna.create_study(direction="maximize", sampler=sampler)
    study.optimize(objective, n_trials=n_trials, show_progress_bar=False)

    archive = _archive_from_trials(rows)
    best = max(rows, key=lambda row: row["score"])
    return {
        "best_score": float(best["score"]),
        "best_ari": float(best["ari"]),
        "best_silhouette": float(best["silhouette"]),
        "best_assignment_rate": float(best["assignment_rate"]),
        "best_lsh_precision": float(best["lsh_precision"]),
        "best_nn_purity": float(best["nn_purity"]),
        "best_cluster_count": int(best["cluster_count"]),
        "archive_coverage": float(archive.stats.coverage),
        "archive_num_elites": int(archive.stats.num_elites),
        "archive_best_objective": float(archive.stats.obj_max),
        "best_config": {
            "n_neighbors": int(best["n_neighbors"]),
            "min_dist": float(best["min_dist"]),
            "min_cluster_size": int(best["min_cluster_size"]),
            "min_samples": int(best["min_samples"]),
        },
        "trial_count": len(rows),
    }


def run_positive_tests() -> dict[str, object]:
    metrics = _search_mode("good", n_trials=14, seed=11)
    metrics["pass"] = bool(
        metrics["best_ari"] >= 0.95
        and metrics["best_silhouette"] >= 0.55
        and metrics["best_assignment_rate"] >= 0.95
        and metrics["best_lsh_precision"] >= 0.8
        and metrics["best_nn_purity"] >= 0.95
        and metrics["archive_coverage"] >= 0.20
        and metrics["best_cluster_count"] == 3
    )
    return metrics


def run_negative_tests() -> dict[str, object]:
    metrics = _search_mode("collapsed", n_trials=10, seed=17)
    metrics["pass"] = bool(
        metrics["best_ari"] <= 0.30
        and metrics["best_silhouette"] <= 0.45
        and metrics["best_lsh_precision"] <= 0.60
        and metrics["best_nn_purity"] <= 0.60
        and metrics["archive_coverage"] >= 0.12
        and metrics["best_cluster_count"] <= 4
    )
    return metrics


def run_boundary_tests() -> dict[str, object]:
    metrics = _search_mode("boundary", n_trials=12, seed=23)
    metrics["pass"] = bool(
        metrics["best_ari"] >= 0.70
        and metrics["best_silhouette"] >= 0.30
        and metrics["best_assignment_rate"] >= 0.80
        and metrics["archive_coverage"] >= 0.12
        and metrics["best_cluster_count"] >= 2
    )
    return metrics


def main() -> None:
    positive = run_positive_tests()
    negative = run_negative_tests()
    boundary = run_boundary_tests()
    overall_pass = bool(positive["pass"] and negative["pass"] and boundary["pass"])

    results = {
        "classification": classification,
        "divergence_log": divergence_log,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "overall_pass": overall_pass,
    }

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(
        out_dir,
        "sim_integration_manifold_search_archive_stack_results.json",
    )
    with open(out_path, "w", encoding="utf-8") as handle:
        json.dump(results, handle, indent=2, sort_keys=True)
    print(f"overall_pass={results['overall_pass']} -> {out_path}")


if __name__ == "__main__":
    main()
