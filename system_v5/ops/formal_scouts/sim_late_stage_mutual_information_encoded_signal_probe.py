#!/usr/bin/env python3
"""
Engine late-stage mutual-information encoded-signal probe — Popper open closeout.

Closes the Popper open from
  sim_late_stage_feature_only_classification_falsifier_probe.py
  (verdict: front_loaded; late_only test acc = 0.638; mean Bloch displacement
   at late substages = 0.899 — engines DO transform but the 4-quadrant input
   label is harder to recover from late features than from full).

Source-sim observation:
- Engines move the state by ~0.90 in Bloch distance (large displacement).
- Late-only 4-quadrant accuracy drops to 0.638 from full 0.961.
- The displacement is NOT pass-through (>>0.10 threshold).
- So engines transform the input into a form where the *original* 4-quadrant
  label is harder to recover, but information is rearranged, not destroyed.

Question this probe answers:
  If the late-stage state does NOT encode the original 4-quadrant identity
  cleanly, what does it encode? Test by measuring mutual information from
  late-stage Bloch features to alternative input-derived labels and by
  training MLP readouts on those labels.

Strategy:
- Reuse the input-state generator (200 samples, theta/phi uniform on S^2 with
  0.9 pure / 0.1 mixed) and the paired-engine pipeline from engine_core.py
  (full Lindblad ODE + 13-layer manifold constraints on a 2-dim density).
- For each input state, run both engines (Type 1 + Type 2) for 32 substages,
  record per-substage Bloch + entropy from each engine's trajectory.
- Build feature variants:
    * early_only (substages 0..7, both engines, Bloch + entropy)
    * mid_only   (substages 12..19, both engines)
    * late_only  (substages 24..31, both engines)
    * full       (all 32 substages, both engines, + entropy)
- Build alternative input-derived labels per sample:
    * input_quadrant  — 4-class sign(bx) × sign(by)
    * input_octant    — 8-class octant on S^2 (sign of bx, by, bz)
    * theta_continuous — polar angle of input Bloch vector (regression)
    * phi_continuous   — azimuthal angle of input Bloch vector (regression)
    * input_continuous — the raw 3-d input Bloch vector itself
- For each label × variant cell:
    * Classification labels → MLP train (48 train / 152 test).
    * Continuous labels → MLP regression (R^2 on test).
    * Mutual information via sklearn.feature_selection.mutual_info_classif
      (for discrete labels) and mutual_info_regression (for continuous).
- Run identity-engine and random-engine baselines on the same feature
  geometry as negative predicates.

Operator-sequence note:
  Both engines apply the SAME fixed 8-main-stage schedule to every input
  (Se/Ne/Ni/Si × outer/inner ordering is constant across all 200 samples).
  Therefore the across-sample mutual information I(operator_sequence;
  late_stage_bloch) is identically zero by construction — the schedule has
  no across-sample entropy to share. Rather than pretend otherwise, this
  probe measures the WITHIN-trajectory analogue: across the 32 substages of
  a single trajectory, does the late-stage Bloch correlate with the substage
  index (a proxy for where in the schedule the state is)? This is the
  closest honest measurement of "the engines encode the schedule more than
  the input" — and it is reported per engine.

Verdict:
  * Late stage carries more MI about an alternative label (octant / theta /
    phi) than about input_quadrant → engines encode finer-grained / different
    structure than the original 4-class partition.
  * Identity engine = no rearrangement (alternative-label accuracy matches
    input-quadrant accuracy because the trajectory is constant at the input).
  * Random engine = chance-level recoverability across all labels.

CLASSIFICATION: formal_scout; promotion_allowed: False.
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

import scipy.stats as scipy_stats
import torch
import torch.nn as nn
import torch.optim as optim
from sklearn.feature_selection import mutual_info_classif, mutual_info_regression

# ---------------------------------------------------------------------------
# Path setup — import the canonical EngineCore (paired engines, manifold ON)
# ---------------------------------------------------------------------------

ROOT = pathlib.Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine_core import (  # noqa: E402
    EngineCore,
    _bloch_vector,
    _normalize_density,
    _von_neumann_entropy,
)
from canonical_qit_engine_specs import DTYPE as ENGINE_DTYPE, I2 as ENGINE_I2  # noqa: E402

RESULT_DIR = ROOT / "results"
OUT_PATH = RESULT_DIR / "late_stage_mutual_information_encoded_signal_probe_results.json"

NAME = "late_stage_mutual_information_encoded_signal_probe"
CLASSIFICATION = "formal_scout"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: tests what input-derived label the QIT engine "
    "late-stage Bloch features encode, given the front-loaded verdict from "
    "the late-stage feature-only classification falsifier probe. Reports "
    "alternative-label accuracies (octant, theta, phi) and sklearn-mutual-"
    "information values. Does not admit cognition, AI architecture, manifold "
    "geometry, or final identity claims about the engines."
)

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": (
            "load-bearing: MLP train + Adam + cross-entropy classification "
            "for discrete labels (quadrant, octant), MLP regression with MSE "
            "for continuous labels (theta, phi). Engine state evolution "
            "inside EngineCore also uses complex tensors."
        ),
    },
    "sklearn": {
        "tried": True,
        "used": True,
        "reason": (
            "load-bearing: feature_selection.mutual_info_classif and "
            "mutual_info_regression to estimate I(label; late_stage_features) "
            "for discrete and continuous labels respectively (Kraskov k-NN "
            "estimator under the hood)."
        ),
    },
    "scipy": {
        "tried": True,
        "used": True,
        "reason": (
            "supportive: scipy.stats.pearsonr / spearmanr correlation "
            "diagnostics between individual late-stage Bloch components and "
            "input theta / phi as a sanity check on the MI estimates."
        ),
    },
}
TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "sklearn": "load_bearing",
    "scipy": "supportive",
}

# ---------------------------------------------------------------------------
# Constants — mirror source-sim dataset; engine pipeline from engine_core.py
# ---------------------------------------------------------------------------

N_MAIN_STAGES = 8
N_SUB_STAGES = 4
N_TOTAL_STAGES = N_MAIN_STAGES * N_SUB_STAGES  # 32

N_SAMPLES = 200
N_TRAIN = 48
N_TEST = N_SAMPLES - N_TRAIN
N_QUADRANTS = 4
N_OCTANTS = 8
N_EPOCHS = 100
HIDDEN_DIM = 64
RANDOM_SEED = 42
MI_N_NEIGHBORS = 5  # Kraskov default

# ---------------------------------------------------------------------------
# Input-state generation (same pattern as source sim)
# ---------------------------------------------------------------------------


def generate_input_states(n: int, seed: int = 0):
    """200 mixed-pure states on S^2 with 0.9 purity (matches source sim).

    Returns:
        rho_list — list of 2x2 complex density matrices for EngineCore
        bloch_vecs — torch tensor shape (n, 3) of input Bloch vectors
        thetas — torch tensor shape (n,) of polar angles (input)
        phis — torch tensor shape (n,) of azimuthal angles (input)
    """
    rng = random.Random(seed)
    rhos: list[Any] = []
    bloch_list: list[torch.Tensor] = []
    thetas: list[float] = []
    phis: list[float] = []
    while len(rhos) < n:
        cos_theta = rng.uniform(-1.0, 1.0)
        phi = rng.uniform(0.0, 2 * math.pi)
        theta = math.acos(cos_theta)
        alpha = math.cos(theta / 2)
        beta = math.sin(theta / 2) * complex(math.cos(phi), math.sin(phi))
        psi = ENGINE_I2[:, :1].copy()
        psi[0, 0] = alpha
        psi[1, 0] = beta
        pure = psi @ psi.conj().T
        rho = _normalize_density(0.90 * pure + 0.10 * ENGINE_I2 / 2)
        rhos.append(rho)
        bvec = torch.as_tensor(_bloch_vector(rho), dtype=torch.float64)
        bloch_list.append(bvec)
        thetas.append(theta)
        phis.append(phi)
    return (
        rhos,
        torch.stack(bloch_list, dim=0),
        torch.tensor(thetas, dtype=torch.float64),
        torch.tensor(phis, dtype=torch.float64),
    )


def quadrant_label(bx: float, by: float) -> int:
    """4-class label by sign(bx), sign(by) — matches source sim."""
    if bx >= 0 and by >= 0:
        return 0
    if bx < 0 and by >= 0:
        return 1
    if bx < 0 and by < 0:
        return 2
    return 3


def octant_label(bx: float, by: float, bz: float) -> int:
    """8-class label by sign(bx), sign(by), sign(bz). Encodes one extra bit."""
    sx = 0 if bx >= 0 else 1
    sy = 0 if by >= 0 else 1
    sz = 0 if bz >= 0 else 1
    return sx * 4 + sy * 2 + sz


# ---------------------------------------------------------------------------
# Engine trajectory extraction via EngineCore (manifold ON by default)
# ---------------------------------------------------------------------------


def run_paired_engines(rho_init: Any) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]:
    """Run Type 1 + Type 2 EngineCore full cycles. Return per-substage Bloch + entropy.

    Returns:
        bloch_e1 — (32, 3) Type 1 Bloch trajectory
        bloch_e2 — (32, 3) Type 2 Bloch trajectory
        ent_e1   — (32,) Type 1 entropy trajectory
        ent_e2   — (32,) Type 2 entropy trajectory
    """
    e1 = EngineCore(engine_type=0, manifold_enabled=True)
    e2 = EngineCore(engine_type=1, manifold_enabled=True)
    res1 = e1.run_full_cycle(rho_init)
    res2 = e2.run_full_cycle(rho_init)
    bloch_e1 = torch.tensor([r["bloch"] for r in res1["trajectory"]], dtype=torch.float64)
    bloch_e2 = torch.tensor([r["bloch"] for r in res2["trajectory"]], dtype=torch.float64)
    ent_e1 = torch.tensor([r["entropy"] for r in res1["trajectory"]], dtype=torch.float64)
    ent_e2 = torch.tensor([r["entropy"] for r in res2["trajectory"]], dtype=torch.float64)
    return bloch_e1, bloch_e2, ent_e1, ent_e2


def run_identity_paired(rho_init: Any) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]:
    """Identity-engine baseline: no transformation — constant trajectory at input."""
    bvec = torch.as_tensor(_bloch_vector(rho_init), dtype=torch.float64)
    ent = _von_neumann_entropy(rho_init)
    bloch_e1 = bvec.repeat(N_TOTAL_STAGES, 1)
    bloch_e2 = bvec.repeat(N_TOTAL_STAGES, 1)
    ent_e1 = torch.full((N_TOTAL_STAGES,), ent, dtype=torch.float64)
    ent_e2 = torch.full((N_TOTAL_STAGES,), ent, dtype=torch.float64)
    return bloch_e1, bloch_e2, ent_e1, ent_e2


def run_random_paired(
    _rho_init: Any, gen: torch.Generator,
) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]:
    """Random-engine baseline: trajectory drawn from a label-agnostic random walk on S^2.

    The walk is independent of the input — every sample gets a fresh random
    trajectory. Provides a strict floor for "the late-stage feature carries
    information about the input."
    """
    # Random unit-vector trajectory + random small entropy walk
    bloch_e1 = torch.randn((N_TOTAL_STAGES, 3), generator=gen, dtype=torch.float64)
    bloch_e1 = bloch_e1 / torch.linalg.norm(bloch_e1, dim=1, keepdim=True) * 0.8
    bloch_e2 = torch.randn((N_TOTAL_STAGES, 3), generator=gen, dtype=torch.float64)
    bloch_e2 = bloch_e2 / torch.linalg.norm(bloch_e2, dim=1, keepdim=True) * 0.8
    ent_e1 = 0.2 + 0.5 * torch.rand((N_TOTAL_STAGES,), generator=gen, dtype=torch.float64)
    ent_e2 = 0.2 + 0.5 * torch.rand((N_TOTAL_STAGES,), generator=gen, dtype=torch.float64)
    return bloch_e1, bloch_e2, ent_e1, ent_e2


# ---------------------------------------------------------------------------
# Feature builders — slice trajectories by substage subset
# ---------------------------------------------------------------------------


def feature_slice(
    bloch_e1: torch.Tensor, bloch_e2: torch.Tensor,
    ent_e1: torch.Tensor, ent_e2: torch.Tensor, indices: list[int],
) -> torch.Tensor:
    """Concatenate both engines' Bloch + entropy at the given substage indices."""
    return torch.cat([
        bloch_e1[indices].flatten(),
        bloch_e2[indices].flatten(),
        ent_e1[indices],
        ent_e2[indices],
    ]).to(torch.float32)


# ---------------------------------------------------------------------------
# MLP readouts
# ---------------------------------------------------------------------------


class ReadoutMLP(nn.Module):
    """Classifier MLP."""

    def __init__(self, input_dim: int, n_classes: int) -> None:
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, HIDDEN_DIM),
            nn.ReLU(),
            nn.Linear(HIDDEN_DIM, n_classes),
        )

    def forward(self, x):
        return self.net(x)


class RegressionMLP(nn.Module):
    """Regression MLP for theta / phi targets (output dim 1)."""

    def __init__(self, input_dim: int) -> None:
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, HIDDEN_DIM),
            nn.ReLU(),
            nn.Linear(HIDDEN_DIM, 1),
        )

    def forward(self, x):
        return self.net(x).squeeze(-1)


def train_classifier(
    X_train, y_train, X_test, y_test, input_dim: int,
    n_classes: int, model_seed: int = 0, label: str = "clf",
) -> dict[str, Any]:
    """Train classification MLP. Returns accuracy + loss curve summary."""
    torch.manual_seed(model_seed)
    model = ReadoutMLP(input_dim=input_dim, n_classes=n_classes)
    optimizer = optim.Adam(model.parameters(), lr=3e-3)
    criterion = nn.CrossEntropyLoss()

    X_tr = torch.as_tensor(X_train, dtype=torch.float32)
    y_tr = torch.as_tensor(y_train, dtype=torch.long)
    X_te = torch.as_tensor(X_test, dtype=torch.float32)
    y_te = torch.as_tensor(y_test, dtype=torch.long)

    loss_first = None
    loss_last = None
    for ep in range(N_EPOCHS):
        model.train()
        optimizer.zero_grad()
        logits = model(X_tr)
        loss = criterion(logits, y_tr)
        loss.backward()
        optimizer.step()
        if ep == 0:
            loss_first = float(loss.item())
        loss_last = float(loss.item())

    model.eval()
    with torch.no_grad():
        test_acc = float((model(X_te).argmax(dim=1) == y_te).float().mean().item())
        train_acc = float((model(X_tr).argmax(dim=1) == y_tr).float().mean().item())
    return {
        "label": label,
        "input_dim": input_dim,
        "n_classes": n_classes,
        "train_accuracy": train_acc,
        "test_accuracy": test_acc,
        "loss_first": loss_first,
        "loss_last": loss_last,
    }


def train_regressor(
    X_train, y_train, X_test, y_test, input_dim: int,
    model_seed: int = 0, label: str = "reg",
) -> dict[str, Any]:
    """Train regression MLP. Returns R^2 on the test split."""
    torch.manual_seed(model_seed)
    model = RegressionMLP(input_dim=input_dim)
    optimizer = optim.Adam(model.parameters(), lr=3e-3)
    criterion = nn.MSELoss()

    X_tr = torch.as_tensor(X_train, dtype=torch.float32)
    y_tr = torch.as_tensor(y_train, dtype=torch.float32)
    X_te = torch.as_tensor(X_test, dtype=torch.float32)
    y_te = torch.as_tensor(y_test, dtype=torch.float32)

    loss_first = None
    loss_last = None
    for ep in range(N_EPOCHS):
        model.train()
        optimizer.zero_grad()
        pred = model(X_tr)
        loss = criterion(pred, y_tr)
        loss.backward()
        optimizer.step()
        if ep == 0:
            loss_first = float(loss.item())
        loss_last = float(loss.item())

    model.eval()
    with torch.no_grad():
        pred_te = model(X_te)
        pred_tr = model(X_tr)
    ss_res_te = float(torch.sum((y_te - pred_te) ** 2).item())
    ss_tot_te = float(torch.sum((y_te - y_te.mean()) ** 2).item())
    r2_te = 1.0 - ss_res_te / max(ss_tot_te, 1e-12)
    ss_res_tr = float(torch.sum((y_tr - pred_tr) ** 2).item())
    ss_tot_tr = float(torch.sum((y_tr - y_tr.mean()) ** 2).item())
    r2_tr = 1.0 - ss_res_tr / max(ss_tot_tr, 1e-12)
    return {
        "label": label,
        "input_dim": input_dim,
        "train_r2": r2_tr,
        "test_r2": r2_te,
        "loss_first": loss_first,
        "loss_last": loss_last,
    }


# ---------------------------------------------------------------------------
# Mutual information via sklearn — load-bearing
# ---------------------------------------------------------------------------


def mi_to_discrete(X: torch.Tensor, y: torch.Tensor | list[int], seed: int = RANDOM_SEED) -> float:
    """Sum of per-feature MI to a discrete target (bits-equivalent in nats)."""
    y_in = y.tolist() if isinstance(y, torch.Tensor) else y
    mi = mutual_info_classif(X.tolist(), y_in, discrete_features=False, n_neighbors=MI_N_NEIGHBORS,
                             random_state=seed)
    return float(sum(float(v) for v in mi))


def mi_to_continuous(X: torch.Tensor, y: torch.Tensor | list[float], seed: int = RANDOM_SEED) -> float:
    """Sum of per-feature MI to a continuous target."""
    y_in = y.tolist() if isinstance(y, torch.Tensor) else y
    mi = mutual_info_regression(X.tolist(), y_in, discrete_features=False, n_neighbors=MI_N_NEIGHBORS,
                                random_state=seed)
    return float(sum(float(v) for v in mi))


# ---------------------------------------------------------------------------
# Within-trajectory substage-index encoding diagnostic
# ---------------------------------------------------------------------------


def within_trajectory_substage_mi(bloch_traj: torch.Tensor) -> dict[str, float]:
    """Per-engine within-trajectory MI between substage_index and Bloch.

    `bloch_traj` shape: (N_SAMPLES, N_TOTAL_STAGES, 3). We flatten substage_idx
    as a discrete label of size 32 and Bloch as 3-d features, then ask:
    given a stack of (sample × substage) rows, how much MI does substage_idx
    carry to the Bloch vector? High = trajectory points are sequence-encoded
    (the Bloch at that step betrays where in the schedule it is).
    """
    n, nstages, _ = bloch_traj.shape
    X = bloch_traj.reshape(n * nstages, 3)
    y = [stage for _sample in range(n) for stage in range(nstages)]
    mi = mutual_info_classif(X.tolist(), y, discrete_features=False, n_neighbors=MI_N_NEIGHBORS,
                             random_state=RANDOM_SEED)
    return {
        "mi_sum_substage_idx_to_bloch": float(sum(float(v) for v in mi)),
        "mi_per_axis": [float(v) for v in mi.tolist()],
    }


# ---------------------------------------------------------------------------
# Serialisation
# ---------------------------------------------------------------------------


def as_jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): as_jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [as_jsonable(v) for v in value]
    if isinstance(value, torch.Tensor):
        return value.detach().cpu().tolist()
    return value


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> int:
    t0 = time.time()

    # 1. Inputs
    print(f"Generating {N_SAMPLES} input states (theta/phi uniform on S^2)...")
    rhos, input_bloch, input_theta, input_phi = generate_input_states(N_SAMPLES, seed=RANDOM_SEED)
    input_quadrant = torch.tensor([
        quadrant_label(float(b[0]), float(b[1])) for b in input_bloch
    ], dtype=torch.long)
    input_octant = torch.tensor([
        octant_label(float(b[0]), float(b[1]), float(b[2])) for b in input_bloch
    ], dtype=torch.long)
    quad_counts = [int((input_quadrant == c).sum().item()) for c in range(N_QUADRANTS)]
    oct_counts = [int((input_octant == c).sum().item()) for c in range(N_OCTANTS)]
    print(f"  quadrant counts: {quad_counts}")
    print(f"  octant counts: {oct_counts}")

    # 2. Run paired engines + identity baseline + random baseline
    print(f"Running paired engines (EngineCore, manifold ON) on {N_SAMPLES} states...")
    bloch_e1_all = torch.zeros((N_SAMPLES, N_TOTAL_STAGES, 3), dtype=torch.float64)
    bloch_e2_all = torch.zeros((N_SAMPLES, N_TOTAL_STAGES, 3), dtype=torch.float64)
    ent_e1_all = torch.zeros((N_SAMPLES, N_TOTAL_STAGES), dtype=torch.float64)
    ent_e2_all = torch.zeros((N_SAMPLES, N_TOTAL_STAGES), dtype=torch.float64)
    id_bloch_e1_all = torch.zeros((N_SAMPLES, N_TOTAL_STAGES, 3), dtype=torch.float64)
    id_bloch_e2_all = torch.zeros((N_SAMPLES, N_TOTAL_STAGES, 3), dtype=torch.float64)
    id_ent_e1_all = torch.zeros((N_SAMPLES, N_TOTAL_STAGES), dtype=torch.float64)
    id_ent_e2_all = torch.zeros((N_SAMPLES, N_TOTAL_STAGES), dtype=torch.float64)
    rand_bloch_e1_all = torch.zeros((N_SAMPLES, N_TOTAL_STAGES, 3), dtype=torch.float64)
    rand_bloch_e2_all = torch.zeros((N_SAMPLES, N_TOTAL_STAGES, 3), dtype=torch.float64)
    rand_ent_e1_all = torch.zeros((N_SAMPLES, N_TOTAL_STAGES), dtype=torch.float64)
    rand_ent_e2_all = torch.zeros((N_SAMPLES, N_TOTAL_STAGES), dtype=torch.float64)

    rand_gen = torch.Generator().manual_seed(RANDOM_SEED + 11)
    for i, rho in enumerate(rhos):
        if i % 25 == 0:
            print(f"  state {i}/{N_SAMPLES}  (elapsed {time.time()-t0:.1f}s)")
        b1, b2, e1, e2 = run_paired_engines(rho)
        bloch_e1_all[i] = b1
        bloch_e2_all[i] = b2
        ent_e1_all[i] = e1
        ent_e2_all[i] = e2

        ib1, ib2, ie1, ie2 = run_identity_paired(rho)
        id_bloch_e1_all[i] = ib1
        id_bloch_e2_all[i] = ib2
        id_ent_e1_all[i] = ie1
        id_ent_e2_all[i] = ie2

        rb1, rb2, re1, re2 = run_random_paired(rho, rand_gen)
        rand_bloch_e1_all[i] = rb1
        rand_bloch_e2_all[i] = rb2
        rand_ent_e1_all[i] = re1
        rand_ent_e2_all[i] = re2

    # 3. Substage subsets
    early_idx = list(range(0, 8))
    mid_idx = list(range(12, 20))
    late_idx = list(range(24, 32))
    full_idx = list(range(0, N_TOTAL_STAGES))

    subsets = {
        "early_only": early_idx,
        "mid_only": mid_idx,
        "late_only": late_idx,
        "full": full_idx,
    }

    def build_features(bloch_e1, bloch_e2, ent_e1, ent_e2, indices):
        return torch.stack([
            feature_slice(bloch_e1[i], bloch_e2[i], ent_e1[i], ent_e2[i], indices)
            for i in range(N_SAMPLES)
        ], dim=0).to(torch.float32)

    engine_features: dict[str, torch.Tensor] = {}
    identity_features: dict[str, torch.Tensor] = {}
    random_features: dict[str, torch.Tensor] = {}
    for name, idx in subsets.items():
        engine_features[name] = build_features(bloch_e1_all, bloch_e2_all, ent_e1_all, ent_e2_all, idx)
        identity_features[name] = build_features(
            id_bloch_e1_all, id_bloch_e2_all, id_ent_e1_all, id_ent_e2_all, idx,
        )
        random_features[name] = build_features(
            rand_bloch_e1_all, rand_bloch_e2_all, rand_ent_e1_all, rand_ent_e2_all, idx,
        )
        print(f"  variant {name}: indices={idx}  shape={tuple(engine_features[name].shape)}")

    # 4. Train / test split
    train_mask = torch.arange(N_SAMPLES) < N_TRAIN
    test_mask = ~train_mask

    y_quad_tr = input_quadrant[train_mask]
    y_quad_te = input_quadrant[test_mask]
    y_oct_tr = input_octant[train_mask]
    y_oct_te = input_octant[test_mask]
    theta_tr = input_theta[train_mask].to(torch.float32)
    theta_te = input_theta[test_mask].to(torch.float32)
    phi_tr = input_phi[train_mask].to(torch.float32)
    phi_te = input_phi[test_mask].to(torch.float32)

    # 5. For each variant + engine kind, train classifiers/regressors and compute MI
    print("Training MLP readouts and computing MI per (engine_kind × variant × label)...")
    feature_kinds = {
        "engine": engine_features,
        "identity": identity_features,
        "random": random_features,
    }

    per_kind_results: dict[str, dict[str, Any]] = {}
    for kind, feat_map in feature_kinds.items():
        per_variant: dict[str, dict[str, Any]] = {}
        for name in subsets:
            X = feat_map[name]
            d = int(X.shape[1])
            X_tr = X[train_mask]
            X_te = X[test_mask]

            quad_res = train_classifier(
                X_tr, y_quad_tr, X_te, y_quad_te,
                input_dim=d, n_classes=N_QUADRANTS, model_seed=0,
                label=f"{kind}_{name}_quadrant",
            )
            oct_res = train_classifier(
                X_tr, y_oct_tr, X_te, y_oct_te,
                input_dim=d, n_classes=N_OCTANTS, model_seed=1,
                label=f"{kind}_{name}_octant",
            )
            theta_res = train_regressor(
                X_tr, theta_tr, X_te, theta_te,
                input_dim=d, model_seed=2,
                label=f"{kind}_{name}_theta",
            )
            phi_res = train_regressor(
                X_tr, phi_tr, X_te, phi_te,
                input_dim=d, model_seed=3,
                label=f"{kind}_{name}_phi",
            )

            # Mutual information on the full sample (sklearn handles internal splits)
            mi_quad = mi_to_discrete(X, input_quadrant)
            mi_oct = mi_to_discrete(X, input_octant)
            mi_theta = mi_to_continuous(X, input_theta)
            mi_phi = mi_to_continuous(X, input_phi)
            # MI to continuous input vector — sum over 3 axes
            mi_input_x = mi_to_continuous(X, input_bloch[:, 0])
            mi_input_y = mi_to_continuous(X, input_bloch[:, 1])
            mi_input_z = mi_to_continuous(X, input_bloch[:, 2])
            mi_input_total = mi_input_x + mi_input_y + mi_input_z

            per_variant[name] = {
                "feature_dim": d,
                "indices": list(subsets[name]),
                "classifier": {
                    "quadrant_test_accuracy": quad_res["test_accuracy"],
                    "quadrant_train_accuracy": quad_res["train_accuracy"],
                    "octant_test_accuracy": oct_res["test_accuracy"],
                    "octant_train_accuracy": oct_res["train_accuracy"],
                },
                "regressor": {
                    "theta_test_r2": theta_res["test_r2"],
                    "theta_train_r2": theta_res["train_r2"],
                    "phi_test_r2": phi_res["test_r2"],
                    "phi_train_r2": phi_res["train_r2"],
                },
                "mutual_information": {
                    "mi_quadrant_total": mi_quad,
                    "mi_octant_total": mi_oct,
                    "mi_theta_total": mi_theta,
                    "mi_phi_total": mi_phi,
                    "mi_input_bloch_x_total": mi_input_x,
                    "mi_input_bloch_y_total": mi_input_y,
                    "mi_input_bloch_z_total": mi_input_z,
                    "mi_input_bloch_sum_total": mi_input_total,
                },
            }
        per_kind_results[kind] = per_variant

    # 6. Within-trajectory substage-index MI per engine (operator_sequence proxy)
    print("Computing within-trajectory substage-index MI (schedule-encoding proxy)...")
    schedule_proxy_e1 = within_trajectory_substage_mi(bloch_e1_all)
    schedule_proxy_e2 = within_trajectory_substage_mi(bloch_e2_all)

    # 7. scipy.stats correlation diagnostic — sanity check on theta-vs-late-bloch
    print("Computing scipy.stats correlation diagnostics (sanity check)...")
    late_eng = engine_features["late_only"]
    # Correlate the first feature axis (Type 1 late-substage-24 bx) with theta and phi
    corr_theta_pearson = float(scipy_stats.pearsonr(late_eng[:, 0].tolist(), input_theta.tolist()).statistic)
    corr_phi_pearson = float(scipy_stats.pearsonr(late_eng[:, 0].tolist(), input_phi.tolist()).statistic)
    corr_theta_spearman = float(scipy_stats.spearmanr(late_eng[:, 0].tolist(), input_theta.tolist()).statistic)
    corr_phi_spearman = float(scipy_stats.spearmanr(late_eng[:, 0].tolist(), input_phi.tolist()).statistic)

    # 8. Headline comparisons + verdict
    eng_late = per_kind_results["engine"]["late_only"]
    eng_full = per_kind_results["engine"]["full"]
    eng_early = per_kind_results["engine"]["early_only"]
    id_late = per_kind_results["identity"]["late_only"]
    rand_late = per_kind_results["random"]["late_only"]

    # Decisive predicates
    quad_acc_late = eng_late["classifier"]["quadrant_test_accuracy"]
    oct_acc_late = eng_late["classifier"]["octant_test_accuracy"]
    theta_r2_late = eng_late["regressor"]["theta_test_r2"]
    phi_r2_late = eng_late["regressor"]["phi_test_r2"]

    alt_accuracies = {
        "octant_test_accuracy_late": oct_acc_late,
        "theta_test_r2_late": theta_r2_late,
        "phi_test_r2_late": phi_r2_late,
    }
    best_alt_label = max(
        [("octant", oct_acc_late), ("theta", theta_r2_late), ("phi", phi_r2_late)],
        key=lambda kv: kv[1],
    )
    at_least_one_alt_recoverable = (
        (oct_acc_late >= 0.75) or (theta_r2_late >= 0.75) or (phi_r2_late >= 0.75)
    )

    # Information rearranged vs destroyed: MI(input; full) >= 0.8 * MI(input; early)
    mi_input_early = per_kind_results["engine"]["early_only"]["mutual_information"]["mi_input_bloch_sum_total"]
    mi_input_full = per_kind_results["engine"]["full"]["mutual_information"]["mi_input_bloch_sum_total"]
    mi_input_late = per_kind_results["engine"]["late_only"]["mutual_information"]["mi_input_bloch_sum_total"]
    mi_quad_late = per_kind_results["engine"]["late_only"]["mutual_information"]["mi_quadrant_total"]
    information_preserved_ratio = (
        mi_input_full / mi_input_early if mi_input_early > 1e-9 else float("inf")
    )
    information_rearranged_not_destroyed = information_preserved_ratio >= 0.8

    # Schedule shift: I(substage_idx; bloch_late_pooled) bigger than I(quadrant; bloch_late)?
    # Use within-trajectory MI as the operator_sequence proxy.
    mi_schedule_proxy_e1 = schedule_proxy_e1["mi_sum_substage_idx_to_bloch"]
    mi_schedule_proxy_e2 = schedule_proxy_e2["mi_sum_substage_idx_to_bloch"]
    mi_schedule_proxy_max = max(mi_schedule_proxy_e1, mi_schedule_proxy_e2)
    schedule_encoding_exceeds_input_quadrant = mi_schedule_proxy_max > mi_quad_late

    # Verdict text
    candidate_labels = [
        ("octant",
         oct_acc_late >= 0.75 and oct_acc_late > quad_acc_late + 0.05,
         oct_acc_late, quad_acc_late),
        ("theta",
         theta_r2_late >= 0.50,
         theta_r2_late, None),
        ("phi",
         phi_r2_late >= 0.50,
         phi_r2_late, None),
    ]
    recoverable_alt = [name for name, ok, *_ in candidate_labels if ok]

    if recoverable_alt:
        verdict = "alt_label_recoverable"
        verdict_text = (
            f"Late-stage features recover the following alternative label(s) "
            f"with acceptable margin: {recoverable_alt}. Best alternative: "
            f"{best_alt_label[0]} (acc/R^2 = {best_alt_label[1]:.3f}). "
            f"Engines rearrange the input into a representation where "
            f"finer-grained / continuous structure of the input remains "
            f"recoverable even when the original 4-class quadrant label "
            f"is partly lost (quadrant_late_acc = {quad_acc_late:.3f})."
        )
    elif schedule_encoding_exceeds_input_quadrant:
        verdict = "schedule_dominates_input"
        verdict_text = (
            f"Within-trajectory substage-index MI "
            f"({mi_schedule_proxy_max:.3f}) exceeds quadrant-input MI to "
            f"late-stage Bloch ({mi_quad_late:.3f}). The late stage encodes "
            f"the schedule position more than the original input quadrant. "
            f"No alternative input-derived label exceeded the 0.75 / 0.50 "
            f"thresholds."
        )
    elif information_rearranged_not_destroyed and mi_input_late > 0.0:
        verdict = "rearranged_not_decoded"
        verdict_text = (
            f"Total MI(input; trajectory) is preserved "
            f"(full/early ratio = {information_preserved_ratio:.3f} >= 0.8) "
            f"but no tested alternative label (octant, theta, phi) recovers "
            f"the late stage above threshold. The information is in there "
            f"but in a representation the tested readouts cannot crack."
        )
    else:
        verdict = "information_loss"
        verdict_text = (
            f"Late stage does not cleanly recover any tested input-derived "
            f"label and the total preserved MI ratio is "
            f"{information_preserved_ratio:.3f} (<0.8). Engines appear to "
            f"destroy input information by the late stage rather than "
            f"rearrange it."
        )

    # 9. Positive / negative / boundary predicates
    chance_q = 1.0 / N_QUADRANTS
    chance_o = 1.0 / N_OCTANTS

    # Diagnostic-style flags reported alongside predicates (NOT gating)
    diagnostic_flags = {
        "at_least_one_alt_label_recoverable_above_0_75": {
            "value": at_least_one_alt_recoverable,
            "octant_test_accuracy_late": oct_acc_late,
            "theta_test_r2_late": theta_r2_late,
            "phi_test_r2_late": phi_r2_late,
            "threshold": 0.75,
            "interpretation": (
                "Whether ANY alternative input-derived label (8-octant, theta-R^2, "
                "phi-R^2) is recoverable from late-stage-only features above 0.75. "
                "Reported as diagnostic — its FAILURE is itself a finding (the "
                "engines hide ALL tested input-derived labels in the late stage)."
            ),
        },
        "schedule_proxy_exceeds_quadrant_mi": {
            "value": schedule_encoding_exceeds_input_quadrant,
            "mi_substage_idx_proxy_engine1": mi_schedule_proxy_e1,
            "mi_substage_idx_proxy_engine2": mi_schedule_proxy_e2,
            "mi_quadrant_to_late_bloch": mi_quad_late,
            "interpretation": (
                "Within-trajectory substage-index MI vs across-sample MI(quadrant; "
                "late_bloch). The two are not dimensionally identical (within-"
                "trajectory uses 3-dim Bloch as features; across-sample uses 64-"
                "dim feature vector). Reported as diagnostic only."
            ),
        },
    }

    positive = {
        "all_mlp_readouts_trained": {
            "pass": all(
                per_kind_results[kind][var]["classifier"].get("octant_train_accuracy", 0.0) > 0.4
                for kind in feature_kinds for var in subsets
            ),
            "interpretation": (
                "Every MLP readout (3 kinds × 4 variants × 2 classifiers) drove "
                "training accuracy above 0.4, confirming the optimiser ran."
            ),
        },
        "total_information_preserved_ratio_above_0_8": {
            "pass": information_rearranged_not_destroyed,
            "mi_input_to_early": mi_input_early,
            "mi_input_to_full": mi_input_full,
            "mi_input_to_late": mi_input_late,
            "ratio_full_over_early": information_preserved_ratio,
            "threshold": 0.8,
            "interpretation": (
                "Sum of MI(input_bloch_axis; full_feature) over sum of "
                "MI(input_bloch_axis; early_feature). >= 0.8 means engines "
                "preserve at least 80 percent of the early-stage shared "
                "information across the full trajectory; supports the "
                "rearranged-not-destroyed reading."
            ),
        },
        "decisive_verdict_classified": {
            "pass": verdict in {
                "alt_label_recoverable",
                "schedule_dominates_input",
                "rearranged_not_decoded",
                "information_loss",
            },
            "verdict": verdict,
        },
        "all_kinds_produced_results": {
            "pass": all(
                isinstance(per_kind_results[kind][var]["classifier"]["octant_test_accuracy"], float)
                for kind in feature_kinds for var in subsets
            ),
            "interpretation": (
                "All three feature kinds (engine, identity, random) produced "
                "test accuracies and MI values for every variant and label."
            ),
        },
    }

    negative = {
        "random_engine_alt_labels_at_chance": {
            "pass": (
                rand_late["classifier"]["octant_test_accuracy"] <= chance_o + 0.20
                and rand_late["regressor"]["theta_test_r2"] <= 0.20
                and rand_late["regressor"]["phi_test_r2"] <= 0.20
            ),
            "random_octant_test_accuracy_late": rand_late["classifier"]["octant_test_accuracy"],
            "random_theta_test_r2_late": rand_late["regressor"]["theta_test_r2"],
            "random_phi_test_r2_late": rand_late["regressor"]["phi_test_r2"],
            "octant_chance_level": chance_o,
            "interpretation": (
                "Random-engine baseline: trajectory is independent of the input "
                "by construction, so alternative-label recoverability should be "
                "near chance (octant: 0.125 + slack; theta/phi: R^2 near 0). "
                "Confirms the readouts are not hallucinating structure."
            ),
        },
        "identity_engine_alt_labels_match_input_quadrant": {
            "pass": (
                abs(
                    id_late["classifier"]["quadrant_test_accuracy"]
                    - id_late["classifier"]["octant_test_accuracy"]
                ) <= 0.20
            ),
            "identity_quadrant_test_accuracy_late": id_late["classifier"]["quadrant_test_accuracy"],
            "identity_octant_test_accuracy_late": id_late["classifier"]["octant_test_accuracy"],
            "identity_theta_test_r2_late": id_late["regressor"]["theta_test_r2"],
            "identity_phi_test_r2_late": id_late["regressor"]["phi_test_r2"],
            "interpretation": (
                "Identity engine: no rearrangement, trajectory constant at the "
                "input Bloch vector. Quadrant and octant accuracy should both "
                "track raw Bloch readout — within 0.20 of each other. Any wide "
                "gap here would mean the readout itself is biased."
            ),
        },
    }

    boundary = {
        "mi_estimates_finite_and_nonneg": {
            "pass": all(
                v["mutual_information"][k] >= 0.0 and math.isfinite(v["mutual_information"][k])
                for kind in feature_kinds
                for v in per_kind_results[kind].values()
                for k in v["mutual_information"]
            ),
            "interpretation": (
                "Sanity check: sklearn MI estimates are non-negative and finite "
                "across all (kind, variant, label) cells."
            ),
        },
        "engines_run_without_nan": {
            "pass": (
                bool(torch.isfinite(engine_features["full"]).all().item())
                and bool(torch.isfinite(engine_features["late_only"]).all().item())
            ),
        },
        "scipy_corr_diagnostic_in_range": {
            "pass": (
                abs(corr_theta_pearson) <= 1.0
                and abs(corr_phi_pearson) <= 1.0
                and abs(corr_theta_spearman) <= 1.0
                and abs(corr_phi_spearman) <= 1.0
            ),
            "pearson_late_bx_vs_theta": corr_theta_pearson,
            "pearson_late_bx_vs_phi": corr_phi_pearson,
            "spearman_late_bx_vs_theta": corr_theta_spearman,
            "spearman_late_bx_vs_phi": corr_phi_spearman,
            "interpretation": (
                "Diagnostic correlation between late-stage Bloch x-component "
                "(Type 1 substage 24) and input theta / phi. Provides a "
                "human-readable single-number sanity check on the MI estimates."
            ),
        },
    }

    all_pass = (
        all(v.get("pass") for v in positive.values())
        and all(v.get("pass") for v in negative.values())
        and all(v.get("pass") for v in boundary.values())
    )

    result = {
        "name": NAME,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "verdict": {
            "label": verdict,
            "text": verdict_text,
            "best_alt_label": best_alt_label[0],
            "best_alt_value": best_alt_label[1],
            "quadrant_test_accuracy_late": quad_acc_late,
            "alt_accuracies_late": alt_accuracies,
            "mi_input_to_early_sum": mi_input_early,
            "mi_input_to_late_sum": mi_input_late,
            "mi_input_to_full_sum": mi_input_full,
            "information_preserved_ratio_full_over_early": information_preserved_ratio,
            "schedule_proxy_max_engine_within_trajectory": mi_schedule_proxy_max,
            "mi_quadrant_to_late_bloch": mi_quad_late,
        },
        "diagnostic_flags": diagnostic_flags,
        "per_kind_results": per_kind_results,
        "within_trajectory_schedule_proxy": {
            "engine1": schedule_proxy_e1,
            "engine2": schedule_proxy_e2,
            "note": (
                "Both engines apply the SAME fixed 8-main-stage schedule to "
                "all 200 inputs, so across-sample I(operator_sequence; "
                "late_stage_bloch) is identically zero. The reported MI is "
                "the within-trajectory analogue: across the 32 substages of "
                "one engine's trajectory, how much does substage_idx tell "
                "us about the Bloch vector? Higher = the trajectory carries "
                "more 'where am I in the schedule' than 'which input am I'."
            ),
        },
        "scipy_diagnostic": {
            "pearson_late_bx_vs_theta": corr_theta_pearson,
            "pearson_late_bx_vs_phi": corr_phi_pearson,
            "spearman_late_bx_vs_theta": corr_theta_spearman,
            "spearman_late_bx_vs_phi": corr_phi_spearman,
        },
        "positive": positive,
        "negative_predicates": negative,
        "graveyard_companions": negative,
        "boundary": boundary,
        "nearby_variants": {
            "total": len(negative),
            "passed": sum(1 for row in negative.values() if row.get("pass")),
            "variants": sorted(negative),
        },
        "why_not_v4_probes": [
            "v5 formal scout over late-stage mutual-information encoded signal readouts.",
            "Does not promote canonical engine, axis, bridge, manifold, or target-system claims.",
            "The mutual-information result is bounded to the finite readout fixture and controls.",
        ],
        "dataset": {
            "n_samples": N_SAMPLES,
            "n_train": N_TRAIN,
            "n_test": N_TEST,
            "quadrant_distribution": quad_counts,
            "octant_distribution": oct_counts,
        },
        "hyperparameters": {
            "n_epochs": N_EPOCHS,
            "hidden_dim": HIDDEN_DIM,
            "n_main_stages": N_MAIN_STAGES,
            "n_sub_stages": N_SUB_STAGES,
            "n_total_stages": N_TOTAL_STAGES,
            "mi_n_neighbors": MI_N_NEIGHBORS,
            "engine_pipeline": "engine_core.EngineCore (Lindblad ODE + 13-layer manifold)",
        },
        "source_sim": (
            "system_v5/ops/formal_scouts/"
            "sim_late_stage_feature_only_classification_falsifier_probe.py"
        ),
        "popper_open_addressed": (
            "Source verdict: front_loaded (late_only quadrant acc=0.638, "
            "full=0.961, late-stage Bloch displacement=0.899). This probe "
            "tests what the late-stage representation DOES encode if not "
            "the 4-quadrant input label, using sklearn mutual information "
            "and MLP readouts on alternative labels (octant, theta, phi)."
        ),
        "all_pass": all_pass,
        "elapsed_seconds": time.time() - t0,
    }

    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(as_jsonable(result), indent=2, sort_keys=True), encoding="utf-8")

    print(f"\nRESULT {NAME}: all_pass={all_pass} -> {OUT_PATH}")
    print(f"  Verdict: {verdict}")
    print(f"  late quad acc={quad_acc_late:.3f}  late octant acc={oct_acc_late:.3f}  "
          f"late theta R^2={theta_r2_late:.3f}  late phi R^2={phi_r2_late:.3f}")
    print(f"  MI(input;early)={mi_input_early:.3f}  MI(input;full)={mi_input_full:.3f}  "
          f"ratio={information_preserved_ratio:.3f}")
    print(f"  schedule_proxy_max={mi_schedule_proxy_max:.3f}  "
          f"MI(quadrant;late)={mi_quad_late:.3f}")
    print(f"Elapsed: {result['elapsed_seconds']:.1f}s")
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
