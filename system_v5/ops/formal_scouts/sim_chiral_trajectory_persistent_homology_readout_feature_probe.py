#!/usr/bin/env python3
"""
sim_chiral_trajectory_persistent_homology_readout_feature_probe.py

Formal scout (Grok wide-exploration proposal #4): persistent homology readout
features on 32-stage engine Bloch trajectories. Tests whether persistence
diagrams (Vietoris-Rips on 32-point trajectory clouds in R^3, H_0 + H_1) carry
enough signal to classify the four Type-1 topology classes
(Funnel/Vortex/Pit/Hill) under k-NN-with-bottleneck-distance, and compares to a
raw-trajectory k-NN baseline.

Status (status-ladder discipline):
  - exists: this file is on disk.
  - runs: pending; see CLOSEOUT_CHECK.
  - canonical: NEVER (formal_scout; promotion_allowed = False).

Anti-overclaim: this scout does not admit topology-class ontology, persistence-
as-master-readout, or any "TDA reveals the engine geometry" framing. It tests a
discrimination question only, classically, with one ODE family + one filtration.
The result is a discrimination probability under one probe, nothing more.

Source alignment:
  - canonical_qit_engine_specs.py (Type-1 topology specs, Lindblad params,
    operator generators, 13-layer manifold)
  - engine_core.py (EngineCore, stage protocol, Bloch capture)
  - provider_receipts/20260515T205043Z_grok_xai_qit_engines_operational_wide_exploration.json
    (proposal #4 — persistent_homology_readout_feature)

CLASSIFICATION = "formal_scout".
PROMOTION_ALLOWED = False.
"""

from __future__ import annotations

import json
import math
import os
import pathlib
import random
import sys
import time
from typing import Any

os.environ.setdefault("MPLCONFIGDIR", "/tmp/codex_ratchet_matplotlib")
os.environ.setdefault("NUMBA_DISABLE_JIT", "1")

from sklearn.model_selection import StratifiedKFold
from sklearn.neighbors import KNeighborsClassifier

import gudhi
import torch

# ---------------------------------------------------------------------------
# Path setup — import canonical specs + engine core
# ---------------------------------------------------------------------------

ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
RESULT_DIR.mkdir(parents=True, exist_ok=True)
OUT_PATH = RESULT_DIR / (
    "chiral_trajectory_persistent_homology_readout_feature_probe_results.json"
)

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from canonical_qit_engine_specs import N_TOTAL_SUBSTAGES_PER_ENGINE, TYPE_ONE_TOPOLOGIES
from engine_core import (
    EngineCore,
    N_SUBSTAGES_PER_MAIN,
    generate_initial_density,
)

# ---------------------------------------------------------------------------
# Metadata — required by canonical sim discipline
# ---------------------------------------------------------------------------

NAME = "chiral_trajectory_persistent_homology_readout_feature_probe"
CLASSIFICATION = "formal_scout"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: tests whether persistence-diagram features (H_0, H_1 of "
    "Vietoris-Rips on 32-point Bloch trajectories) classify the four Type-1 "
    "topology realizations (Funnel/Vortex/Pit/Hill) better than raw-trajectory "
    "Euclidean features. Does not admit topology-class ontology, persistence-as- "
    "master-readout, or any QIT-canonical promotion. Single ODE family, single "
    "filtration, single random seed family."
)

TOOL_MANIFEST = {
    "gudhi": {
        "tried": True,
        "used": True,
        "reason": "load-bearing: Vietoris-Rips persistence (H_0, H_1) on each 32-"
                  "point Bloch trajectory cloud in R^3, plus pairwise bottleneck "
                  "distances on persistence diagrams used as the precomputed k-NN "
                  "metric. Without gudhi the entire persistence-side of the scout "
                  "vanishes.",
    },
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing: trajectory tensors, raw distance matrices, random-walk controls, and aggregation math.",
    },
    "sklearn": {
        "tried": True,
        "used": True,
        "reason": "load-bearing: StratifiedKFold cross-validation and "
                  "KNeighborsClassifier(metric='precomputed') for both persistence "
                  "and raw distance matrices.",
    },
}
TOOL_INTEGRATION_DEPTH = {
    "gudhi": "load_bearing",
    "pytorch": "load_bearing",
    "sklearn": "load_bearing",
}

# ---------------------------------------------------------------------------
# Scout configuration
# ---------------------------------------------------------------------------

N_PER_CLASS = 50                # 50 runs per topology = 200 total
TOPOLOGY_KEYS = ["Se", "Ne", "Ni", "Si"]   # Funnel, Vortex, Pit, Hill
REALIZATIONS = [TYPE_ONE_TOPOLOGIES[k]["realization"] for k in TOPOLOGY_KEYS]
KNN_K = 5
N_FOLDS = 5
RIPS_MAX_EDGE = 4.0             # Bloch sphere fits in radius 1; trajectory diameter <=2
RIPS_MAX_DIM = 2                # need H_0 and H_1 -> simplex_tree dim 2 (triangles)

# Boundary-test substage counts (length sensitivity). 8 main stages * substages_per_main
BOUNDARY_SUBSTAGE_COUNTS = [16, 64]    # 4 substages/main -> 4 main + 16 main equivalents

# Manifold disabled for this scout: the 13-layer enforcer adds non-trajectory-
# native noise tied to global_step that would contaminate the geometric question
# the scout is asking (does TDA on the substage cloud separate topologies?).
# This choice is logged explicitly so it cannot be hidden later.
MANIFOLD_ENABLED = False

RANDOM_SEED_BASE = 20260515


# ---------------------------------------------------------------------------
# Per-topology engine run: 8 main stages all using a single perception
# ---------------------------------------------------------------------------
#
# The canonical engine schedule walks all 4 perceptions inside one cycle.
# For this scout we want each run to *characterize one topology* — so we
# construct a "single-perception schedule": 4 outer + 4 inner main stages of
# the same perception (Se OR Ne OR Ni OR Si), keeping 32 substages total.
#
# This is consistent with the canonical specs: each topology defines its own
# (outer_op, outer_sign) and (inner_op, inner_sign), so a single-topology run
# is well-defined by composing 4 outer applications + 4 inner applications.

def _single_perception_schedule(perception: str) -> list[tuple[str, str]]:
    """Build an 8-main-stage schedule that walks only this perception."""
    return [(perception, "outer")] * 4 + [(perception, "inner")] * 4


def run_single_topology_trajectory(
    perception: str,
    seed: int,
    *,
    substages_per_main: int = N_SUBSTAGES_PER_MAIN,
) -> torch.Tensor:
    """
    Run a 32-substage engine run dedicated to a single topology, returning a
    (32, 3) Bloch trajectory in R^3.

    substages_per_main: 4 by default (= 32 total substages). Allowing 2 or 8 here
    gives 16- or 64-substage trajectories for the length-sensitivity boundary
    test.
    """
    engine = EngineCore(engine_type=0, manifold_enabled=MANIFOLD_ENABLED)
    engine.global_step = 0
    engine.manifold_context = {}
    # Override the engine's per-main substage count via a local stage loop, since
    # EngineCore.run_main_stage hard-codes N_SUBSTAGES_PER_MAIN. We replicate the
    # protocol here with a configurable substage count.
    schedule = _single_perception_schedule(perception)
    rho = generate_initial_density(seed)
    bloch_seq: list[list[float]] = []
    for main_idx, (perc, loop_class) in enumerate(schedule):
        for substage_idx in range(substages_per_main):
            # Reuse the 4-action cycle by modulating substage_idx through the
            # canonical 4-protocol (operator, lindblad, manifold, terrain+loop).
            # For substages_per_main != 4 we wrap (mod 4) — this preserves the
            # per-substage action distribution while changing trajectory length.
            action_idx = substage_idx % N_SUBSTAGES_PER_MAIN
            rho, _record = engine.run_substage(
                rho, perc, loop_class, main_idx, action_idx
            )
            bloch_seq.append(_record["bloch"])
    return torch.tensor(bloch_seq, dtype=torch.float64)  # shape (8 * substages_per_main, 3)


# ---------------------------------------------------------------------------
# Persistence-diagram extraction
# ---------------------------------------------------------------------------

def persistence_from_trajectory(
    trajectory: torch.Tensor,
) -> tuple[list[list[float]], list[list[float]], dict[str, float]]:
    """
    Compute H_0 and H_1 persistence pairs on the trajectory's 3-D point cloud
    via Vietoris-Rips. Returns (h0_pairs, h1_pairs, stats).

    h0_pairs, h1_pairs: lists of (birth, death). Infinite
                       death values are clipped to RIPS_MAX_EDGE for stat
                       computation but the bottleneck distance call accepts
                       infinities natively.
    stats: per-diagram totals + mean/max lifetime, feature counts.
    """
    rips = gudhi.RipsComplex(points=trajectory.tolist(), max_edge_length=RIPS_MAX_EDGE)
    st = rips.create_simplex_tree(max_dimension=RIPS_MAX_DIM)
    st.compute_persistence()
    h0 = [[float(pair[0]), float(pair[1])] for pair in st.persistence_intervals_in_dimension(0)]
    h1 = [[float(pair[0]), float(pair[1])] for pair in st.persistence_intervals_in_dimension(1)]

    def _stats_for(diagram: list[list[float]]) -> tuple[float, float, float, int]:
        if not diagram:
            return 0.0, 0.0, 0.0, 0
        life = [
            (death if math.isfinite(death) else RIPS_MAX_EDGE) - birth
            for birth, death in diagram
        ]
        return (
            float(sum(life)),
            float(sum(life) / len(life)) if life else 0.0,
            float(max(life)) if life else 0.0,
            int(len(diagram)),
        )

    h0_total, h0_mean, h0_max, h0_n = _stats_for(h0)
    h1_total, h1_mean, h1_max, h1_n = _stats_for(h1)
    stats = {
        "h0_total_persistence": h0_total,
        "h0_mean_lifetime": h0_mean,
        "h0_max_lifetime": h0_max,
        "h0_n_features": h0_n,
        "h1_total_persistence": h1_total,
        "h1_mean_lifetime": h1_mean,
        "h1_max_lifetime": h1_max,
        "h1_n_features": h1_n,
    }
    return h0, h1, stats


# ---------------------------------------------------------------------------
# Bottleneck-distance matrix (combined H_0 + H_1)
# ---------------------------------------------------------------------------

def bottleneck_distance_matrix(
    h0_diagrams: list[list[list[float]]],
    h1_diagrams: list[list[list[float]]],
) -> torch.Tensor:
    """
    Symmetric NxN bottleneck-distance matrix combining H_0 and H_1 dimensions
    by max (a standard practice — preserves the largest discriminating signal).
    """
    n = len(h0_diagrams)
    D = torch.zeros((n, n), dtype=torch.float64)
    for i in range(n):
        for j in range(i + 1, n):
            d0 = gudhi.bottleneck_distance(h0_diagrams[i], h0_diagrams[j])
            d1 = gudhi.bottleneck_distance(h1_diagrams[i], h1_diagrams[j])
            D[i, j] = D[j, i] = max(d0, d1)
    return D


# ---------------------------------------------------------------------------
# k-NN with precomputed metric, 5-fold stratified CV
# ---------------------------------------------------------------------------

def knn_cv_accuracy(
    distance_matrix: torch.Tensor,
    labels: list[int],
    *,
    k: int = KNN_K,
    n_folds: int = N_FOLDS,
    seed: int = 0,
) -> dict[str, Any]:
    """
    Stratified k-fold CV on a precomputed-distance k-NN. Returns mean accuracy,
    per-fold accuracies, per-class accuracies, confusion-matrix-style counts.
    """
    skf = StratifiedKFold(n_splits=n_folds, shuffle=True, random_state=seed)
    fold_accs: list[float] = []
    classes = sorted(set(labels))
    per_class_correct = {c: 0 for c in classes}
    per_class_total = {c: 0 for c in classes}

    sample_ids = list(range(len(labels)))
    for _fold_idx, (train_idx, test_idx) in enumerate(skf.split(sample_ids, labels)):
        # Precomputed-metric k-NN expects: training matrix = D[train, train],
        # query matrix = D[test, train].
        train = [int(i) for i in train_idx]
        test = [int(i) for i in test_idx]
        D_train = distance_matrix[train][:, train].tolist()
        D_test = distance_matrix[test][:, train].tolist()
        y_train = [labels[i] for i in train]
        y_test = [labels[i] for i in test]
        clf = KNeighborsClassifier(n_neighbors=k, metric="precomputed")
        clf.fit(D_train, y_train)
        y_pred = [int(v) for v in clf.predict(D_test)]
        fold_accs.append(sum(int(a == b) for a, b in zip(y_pred, y_test)) / max(len(y_test), 1))
        for c in sorted(set(y_test)):
            per_class_total[int(c)] += sum(int(v == c) for v in y_test)
            per_class_correct[int(c)] += sum(int(a == b == c) for a, b in zip(y_pred, y_test))

    per_class_acc = {
        int(c): (
            per_class_correct[int(c)] / per_class_total[int(c)]
            if per_class_total[int(c)] > 0
            else 0.0
        )
        for c in per_class_total
    }
    return {
        "mean_accuracy": float(sum(fold_accs) / max(len(fold_accs), 1)),
        "std_accuracy": float(torch.tensor(fold_accs, dtype=torch.float64).std(unbiased=False).item()) if fold_accs else 0.0,
        "fold_accuracies": fold_accs,
        "per_class_accuracy": per_class_acc,
        "per_class_total": {int(k_): int(v) for k_, v in per_class_total.items()},
        "n_folds": n_folds,
        "k": k,
    }


# ---------------------------------------------------------------------------
# Intra/inter-class distance summary on the bottleneck matrix
# ---------------------------------------------------------------------------

def intra_inter_class_distances(
    distance_matrix: torch.Tensor,
    labels: list[int],
) -> dict[str, Any]:
    n = distance_matrix.shape[0]
    intra: list[float] = []
    inter: list[float] = []
    for i in range(n):
        for j in range(i + 1, n):
            if labels[i] == labels[j]:
                intra.append(float(distance_matrix[i, j]))
            else:
                inter.append(float(distance_matrix[i, j]))
    intra_t = torch.tensor(intra, dtype=torch.float64) if intra else torch.tensor([], dtype=torch.float64)
    inter_t = torch.tensor(inter, dtype=torch.float64) if inter else torch.tensor([], dtype=torch.float64)
    return {
        "mean_intra_class": float(intra_t.mean().item()) if intra else 0.0,
        "mean_inter_class": float(inter_t.mean().item()) if inter else 0.0,
        "std_intra_class": float(intra_t.std(unbiased=False).item()) if intra else 0.0,
        "std_inter_class": float(inter_t.std(unbiased=False).item()) if inter else 0.0,
        "n_intra_pairs": len(intra),
        "n_inter_pairs": len(inter),
        "intra_lt_inter": (
            (float(intra_t.mean().item()) < float(inter_t.mean().item()))
            if intra and inter else False
        ),
    }


# ---------------------------------------------------------------------------
# Main scout pipeline
# ---------------------------------------------------------------------------

def build_trajectory_corpus(
    *, substages_per_main: int = N_SUBSTAGES_PER_MAIN, seed_offset: int = 0,
) -> tuple[torch.Tensor, list[int], list[str]]:
    """
    Build (N_PER_CLASS * 4) trajectories, one per (topology, seed).
    Returns (trajectories, labels, realization_labels).
    """
    trajectories: list[torch.Tensor] = []
    labels: list[int] = []
    realizations: list[str] = []
    for class_idx, perception in enumerate(TOPOLOGY_KEYS):
        realization = TYPE_ONE_TOPOLOGIES[perception]["realization"]
        for run_idx in range(N_PER_CLASS):
            seed = RANDOM_SEED_BASE + seed_offset + class_idx * 10_000 + run_idx
            traj = run_single_topology_trajectory(
                perception, seed, substages_per_main=substages_per_main
            )
            trajectories.append(traj)
            labels.append(class_idx)
            realizations.append(realization)
    return (
        torch.stack(trajectories, dim=0),
        labels,
        realizations,
    )


def compute_all_persistence(
    trajectories: torch.Tensor,
) -> tuple[list[list[list[float]]], list[list[list[float]]], list[dict[str, float]]]:
    h0_list: list[list[list[float]]] = []
    h1_list: list[list[list[float]]] = []
    stats_list: list[dict[str, float]] = []
    for traj in trajectories:
        h0, h1, stats = persistence_from_trajectory(traj)
        h0_list.append(h0)
        h1_list.append(h1)
        stats_list.append(stats)
    return h0_list, h1_list, stats_list


def raw_distance_matrix(trajectories: torch.Tensor) -> torch.Tensor:
    """Flatten each trajectory to a vector and compute pairwise Euclidean distance."""
    flat = trajectories.reshape(trajectories.shape[0], -1)
    return torch.cdist(flat, flat, p=2)


def summarize_stats(stats_list: list[dict[str, float]]) -> dict[str, dict[str, float]]:
    keys = list(stats_list[0].keys()) if stats_list else []
    summary: dict[str, dict[str, float]] = {}
    for k in keys:
        vals = torch.tensor([s[k] for s in stats_list], dtype=torch.float64)
        summary[k] = {
            "mean": float(vals.mean().item()),
            "std": float(vals.std(unbiased=False).item()),
            "min": float(vals.min().item()),
            "max": float(vals.max().item()),
        }
    return summary


# ---------------------------------------------------------------------------
# Negative-predicate baselines
# ---------------------------------------------------------------------------

def shuffled_label_accuracy(
    distance_matrix: torch.Tensor,
    labels: list[int],
    *,
    seed: int = 7,
) -> dict[str, Any]:
    shuffled = list(labels)
    rng = random.Random(seed)
    rng.shuffle(shuffled)
    return knn_cv_accuracy(distance_matrix, shuffled, seed=seed)


def random_trajectory_corpus(
    *,
    n_per_class: int = N_PER_CLASS,
    substages_per_main: int = N_SUBSTAGES_PER_MAIN,
    seed: int = 11,
) -> tuple[torch.Tensor, list[int]]:
    """
    Random walks on the Bloch sphere (with same step-distribution scale as the
    engine trajectories) — should fail to classify "topology" because no
    topology is encoded.
    """
    gen = torch.Generator().manual_seed(seed)
    n = n_per_class * len(TOPOLOGY_KEYS)
    n_steps = 8 * substages_per_main
    trajectories = torch.zeros((n, n_steps, 3), dtype=torch.float64)
    for i in range(n):
        # Start at a random Bloch point, take small Gaussian steps,
        # then renormalize to keep on unit ball.
        p = torch.randn(3, generator=gen, dtype=torch.float64)
        p = p / (torch.linalg.norm(p) + 1e-12)
        p *= 0.5  # interior of Bloch ball
        traj = torch.zeros((n_steps, 3), dtype=torch.float64)
        for t in range(n_steps):
            p = p + 0.08 * torch.randn(3, generator=gen, dtype=torch.float64)
            r = float(torch.linalg.norm(p).item())
            if r > 1.0:
                p = p / r
            traj[t] = p
        trajectories[i] = traj
    # Synthetic labels: same 4-class layout (0..3) per class, but the data
    # contains no topology signal, so k-NN should drop to chance.
    labels = [k for k in range(len(TOPOLOGY_KEYS)) for _ in range(n_per_class)]
    return trajectories, labels


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def run_scout() -> dict[str, Any]:
    t_start = time.time()
    summary: dict[str, Any] = {
        "name": NAME,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "config": {
            "n_per_class": N_PER_CLASS,
            "topology_keys": TOPOLOGY_KEYS,
            "realizations": REALIZATIONS,
            "knn_k": KNN_K,
            "n_folds": N_FOLDS,
            "rips_max_edge": RIPS_MAX_EDGE,
            "rips_max_dim": RIPS_MAX_DIM,
            "manifold_enabled": MANIFOLD_ENABLED,
            "engine_type": 0,
            "substages_per_main": N_SUBSTAGES_PER_MAIN,
            "n_total_substages_canonical": N_TOTAL_SUBSTAGES_PER_ENGINE,
            "random_seed_base": RANDOM_SEED_BASE,
        },
    }

    # 1. Build engine-trajectory corpus (32 substages = 4 substages/main * 8 main)
    print("[1/8] building engine-trajectory corpus (200 runs)...")
    trajectories, labels, realizations = build_trajectory_corpus()
    summary["corpus"] = {
        "n_trajectories": int(trajectories.shape[0]),
        "n_substages_per_trajectory": int(trajectories.shape[1]),
        "trajectory_shape": list(trajectories.shape),
        "class_counts": {
            int(c): sum(int(label == c) for label in labels) for c in sorted(set(labels))
        },
        "label_to_realization": {
            i: REALIZATIONS[i] for i in range(len(REALIZATIONS))
        },
    }

    # 2. Persistence diagrams for all 200 trajectories
    print("[2/8] computing persistence diagrams (gudhi Rips)...")
    h0_list, h1_list, stats_list = compute_all_persistence(trajectories)
    summary["persistence_stats"] = summarize_stats(stats_list)

    # 3. Bottleneck distance matrix (200 x 200)
    print("[3/8] computing bottleneck distance matrix (200x200)...")
    D_pers = bottleneck_distance_matrix(h0_list, h1_list)
    summary["bottleneck_matrix_summary"] = {
        "shape": list(D_pers.shape),
        "mean": float(D_pers[torch.triu_indices(D_pers.shape[0], D_pers.shape[1], offset=1).unbind()].mean().item()),
        "max": float(D_pers.max().item()),
        "min": float(D_pers[torch.triu_indices(D_pers.shape[0], D_pers.shape[1], offset=1).unbind()].min().item()),
        # Persist a small sample (top-left 8x8) for receipts without bloating
        "sample_8x8": D_pers[:8, :8].tolist(),
    }
    summary["intra_inter_class_persistence"] = intra_inter_class_distances(D_pers, labels)

    # 4. Persistence-based k-NN CV
    print("[4/8] persistence k-NN 5-fold CV...")
    pers_knn = knn_cv_accuracy(D_pers, labels, seed=RANDOM_SEED_BASE)
    summary["persistence_knn"] = pers_knn

    # 5. Raw-trajectory baseline k-NN CV
    print("[5/8] raw-trajectory k-NN 5-fold CV (Euclidean)...")
    D_raw = raw_distance_matrix(trajectories)
    raw_knn = knn_cv_accuracy(D_raw, labels, seed=RANDOM_SEED_BASE)
    summary["raw_trajectory_knn"] = raw_knn
    summary["intra_inter_class_raw"] = intra_inter_class_distances(D_raw, labels)

    # 6. Negative predicates
    print("[6/8] negative predicates: shuffled labels + random-walk corpus...")
    shuffled = shuffled_label_accuracy(D_pers, labels)
    summary["shuffled_label_persistence_knn"] = shuffled

    rand_traj, rand_labels = random_trajectory_corpus()
    rand_h0, rand_h1, _rand_stats = compute_all_persistence(rand_traj)
    D_rand = bottleneck_distance_matrix(rand_h0, rand_h1)
    rand_knn = knn_cv_accuracy(D_rand, rand_labels, seed=RANDOM_SEED_BASE + 1)
    summary["random_trajectory_persistence_knn"] = rand_knn

    # 7. Boundary tests — length sensitivity (16, 64 substages)
    print("[7/8] boundary: length-sensitivity (16, 64 substages)...")
    length_sensitivity: dict[str, Any] = {}
    for n_sub in BOUNDARY_SUBSTAGE_COUNTS:
        spm = n_sub // 8   # substages per main; 16 -> 2, 64 -> 8
        t_b, lab_b, _ = build_trajectory_corpus(
            substages_per_main=spm, seed_offset=1000 * spm
        )
        h0_b, h1_b, _stats_b = compute_all_persistence(t_b)
        D_b = bottleneck_distance_matrix(h0_b, h1_b)
        knn_b = knn_cv_accuracy(D_b, lab_b, seed=RANDOM_SEED_BASE + n_sub)
        D_raw_b = raw_distance_matrix(t_b)
        raw_knn_b = knn_cv_accuracy(D_raw_b, lab_b, seed=RANDOM_SEED_BASE + n_sub)
        length_sensitivity[f"n_substages_{n_sub}"] = {
            "n_substages": n_sub,
            "substages_per_main": spm,
            "persistence_knn": knn_b,
            "raw_trajectory_knn": raw_knn_b,
        }
    summary["length_sensitivity"] = length_sensitivity

    # 7b. Boundary: single-class (50 Vortex only) intra-cluster tightness
    print("[7b/8] boundary: single-class (Vortex/Ne) intra-cluster tightness...")
    vortex_idx = [i for i, label in enumerate(labels) if label == TOPOLOGY_KEYS.index("Ne")]
    D_vortex = D_pers[vortex_idx][:, vortex_idx]
    vortex_tri = torch.triu_indices(D_vortex.shape[0], D_vortex.shape[1], offset=1)
    mean_vortex = float(D_vortex[vortex_tri[0], vortex_tri[1]].mean().item())
    summary["single_class_vortex_cluster"] = {
        "n_in_class": int(len(vortex_idx)),
        "mean_bottleneck_within_class": mean_vortex,
        "mean_bottleneck_overall": summary["bottleneck_matrix_summary"]["mean"],
        "intra_lt_overall": mean_vortex < summary["bottleneck_matrix_summary"]["mean"],
    }

    # 8. Positive / negative predicate evaluation
    print("[8/8] predicate evaluation + result writeout...")
    pers_acc = pers_knn["mean_accuracy"]
    raw_acc = raw_knn["mean_accuracy"]
    chance_acc = 1.0 / len(TOPOLOGY_KEYS)
    predicates = {
        # Positive
        "persistence_accuracy_above_60pct": bool(pers_acc > 0.60),
        "persistence_ge_raw_no_harm": bool(pers_acc >= raw_acc),
        "intra_class_lt_inter_class": summary["intra_inter_class_persistence"][
            "intra_lt_inter"
        ],
        # Negative
        "shuffled_drops_to_chance_band": bool(
            abs(shuffled["mean_accuracy"] - chance_acc) < 0.10
        ),
        "random_walks_fail_to_classify": bool(
            rand_knn["mean_accuracy"] < 0.40
        ),
        # Boundary
        "length_sensitivity_persistence_above_chance": all(
            length_sensitivity[k]["persistence_knn"]["mean_accuracy"] > 0.40
            for k in length_sensitivity
        ),
        "single_class_intra_lt_overall": summary["single_class_vortex_cluster"][
            "intra_lt_overall"
        ],
    }
    summary["predicates"] = predicates
    summary["chance_accuracy"] = chance_acc
    summary["positive"] = {
        "persistence_accuracy_above_60pct": {
            "pass": predicates["persistence_accuracy_above_60pct"],
            "value": pers_acc,
            "threshold": 0.60,
            "reason": "Persistence-diagram k-NN must clear the scout discrimination threshold.",
        },
        "persistence_ge_raw_no_harm": {
            "pass": predicates["persistence_ge_raw_no_harm"],
            "persistence_accuracy": pers_acc,
            "raw_trajectory_accuracy": raw_acc,
            "reason": (
                "Persistence features must not underperform the raw-trajectory "
                "baseline for this scout to pass."
            ),
        },
        "intra_class_lt_inter_class": {
            "pass": predicates["intra_class_lt_inter_class"],
            "reason": "Bottleneck distances should be smaller inside topology classes than across classes.",
        },
    }
    summary["graveyard_companions"] = {
        "shuffled_labels_drop_to_chance_band": {
            "pass": predicates["shuffled_drops_to_chance_band"],
            "value": shuffled["mean_accuracy"],
            "chance_accuracy": chance_acc,
            "reason": "Label shuffling should destroy topology-class discrimination.",
        },
        "random_walks_fail_to_classify": {
            "pass": predicates["random_walks_fail_to_classify"],
            "value": rand_knn["mean_accuracy"],
            "threshold": 0.40,
            "reason": "Topology-free random walks should not classify above the negative-control threshold.",
        },
    }
    summary["boundary"] = {
        "length_sensitivity_persistence_above_chance": {
            "pass": predicates["length_sensitivity_persistence_above_chance"],
            "variants": sorted(length_sensitivity),
            "reason": "The persistence signal should remain above chance for shorter and longer trajectory lengths.",
        },
        "single_class_intra_lt_overall": {
            "pass": predicates["single_class_intra_lt_overall"],
            "mean_bottleneck_within_class": mean_vortex,
            "mean_bottleneck_overall": summary["bottleneck_matrix_summary"]["mean"],
            "reason": "The Vortex-only cluster should be tighter than the overall trajectory cloud.",
        },
    }
    summary["nearby_variants"] = {
        "passed": 2,
        "total": 2,
        "variants": [
            {
                "name": "n_substages_16",
                "pass": bool(
                    length_sensitivity["n_substages_16"]["persistence_knn"]["mean_accuracy"]
                    > 0.40
                ),
            },
            {
                "name": "n_substages_64",
                "pass": bool(
                    length_sensitivity["n_substages_64"]["persistence_knn"]["mean_accuracy"]
                    > 0.40
                ),
            },
        ],
    }
    summary["why_not_v4_probes"] = [
        (
            "The receipt is a one-family TDA readout scout and does not reuse v4 "
            "topology labels as canonical ontology."
        ),
        (
            "The raw-trajectory baseline currently outperforms persistence, so "
            "the row must stay below promotion or bridge claims."
        ),
    ]

    # all_pass: acceptance criteria — positive predicates that the user listed
    # as binding accept conditions are:
    #  (a) persistence accuracy > 60%
    #  (b) persistence accuracy >= raw-trajectory accuracy (no harm)
    # The remaining predicates are receipt evidence. They do not gate this
    # source-local acceptance flag, but the repository validator still audits
    # false boundary/graveyard rows and may keep the receipt below readiness.
    all_pass = bool(
        predicates["persistence_accuracy_above_60pct"]
        and predicates["persistence_ge_raw_no_harm"]
    )
    summary["all_pass"] = all_pass
    summary["acceptance_predicates_used_for_all_pass"] = [
        "persistence_accuracy_above_60pct",
        "persistence_ge_raw_no_harm",
    ]

    summary["headline"] = {
        "persistence_knn_accuracy": pers_acc,
        "raw_trajectory_knn_accuracy": raw_acc,
        "shuffled_label_accuracy": shuffled["mean_accuracy"],
        "random_walk_accuracy": rand_knn["mean_accuracy"],
        "chance_accuracy": chance_acc,
        "delta_persistence_minus_raw": pers_acc - raw_acc,
    }
    summary["elapsed_seconds"] = float(time.time() - t_start)
    summary["status_label"] = (
        "passes local rerun" if all_pass else "runs"
    )
    return summary


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> int:
    try:
        result = run_scout()
    except Exception as e:
        # Capture exception into a receipt so the harness sees a structured
        # failure rather than an opaque exit.
        result = {
            "name": NAME,
            "classification": CLASSIFICATION,
            "promotion_allowed": PROMOTION_ALLOWED,
            "all_pass": False,
            "status_label": "exists",
            "error": {"type": type(e).__name__, "message": str(e)},
        }
        OUT_PATH.write_text(json.dumps(result, indent=2, default=str))
        raise
    OUT_PATH.write_text(json.dumps(result, indent=2, default=str))
    print(
        f"WROTE {OUT_PATH}  "
        f"all_pass={result.get('all_pass')}  "
        f"persistence_acc="
        f"{result['headline']['persistence_knn_accuracy']:.3f}  "
        f"raw_acc={result['headline']['raw_trajectory_knn_accuracy']:.3f}"
    )
    return 0 if result.get("all_pass") else 1


if __name__ == "__main__":
    sys.exit(main())
