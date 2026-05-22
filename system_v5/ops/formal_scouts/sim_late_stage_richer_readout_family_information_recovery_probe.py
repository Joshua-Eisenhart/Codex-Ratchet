#!/usr/bin/env python3
"""Late-stage richer-readout-family information-recovery probe.

Torch-native source repair of the prior richer-readout scout. The formal
question is unchanged: can richer readouts recover input information from
late-stage paired-engine features after the baseline MLP/MI scout found
``rearranged_not_decoded``?

The scout intentionally has no source-level NumPy import, NumPy alias call, or
tensor-to-array escape. EngineCore remains the canonical engine runner and may
use its own internal backend; this scout's source surface and receipt are
PyTorch/sklearn only.

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
from typing import Any, Callable

os.environ.setdefault("MPLCONFIGDIR", "/tmp/codex_ratchet_matplotlib")
os.environ.setdefault("NUMBA_DISABLE_JIT", "1")

import torch
import torch.nn as nn
import torch.optim as optim
from sklearn.ensemble import (
    GradientBoostingClassifier,
    GradientBoostingRegressor,
    RandomForestClassifier,
    RandomForestRegressor,
)
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.model_selection import KFold
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC, SVR

ROOT = pathlib.Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from canonical_qit_engine_specs import I2 as ENGINE_I2  # noqa: E402
from engine_core import EngineCore, _bloch_vector, _normalize_density, _purity, _von_neumann_entropy  # noqa: E402

RESULT_DIR = ROOT / "results"
OUT_PATH = RESULT_DIR / "late_stage_richer_readout_family_information_recovery_probe_results.json"

NAME = "late_stage_richer_readout_family_information_recovery_probe"
CLASSIFICATION = "formal_scout"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: tests whether a richer readout family can recover input "
    "information from late-stage engine features after the baseline scout found "
    "rearranged_not_decoded. Does not admit cognition, AI architecture, engine "
    "canon, or final manifold claims."
)

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": (
            "load-bearing: feature tensors, random baseline tensors, MLP readouts, "
            "R2 computations, final-density Kronecker features, and JSON-safe tensor receipts"
        ),
    },
    "sklearn": {
        "tried": True,
        "used": True,
        "reason": (
            "load-bearing: linear, RBF SVM, random forest, gradient boosting, "
            "KFold diagnostics, and feature scaling for non-MLP readouts"
        ),
    },
}
TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "sklearn": "load_bearing",
}

N_MAIN_STAGES = 8
N_SUB_STAGES = 4
N_TOTAL_STAGES = N_MAIN_STAGES * N_SUB_STAGES
N_SAMPLES = 200
N_TRAIN = 48
N_QUADRANTS = 4
N_OCTANTS = 8
N_EPOCHS = 100
HIDDEN_DIM = 64
RANDOM_SEED = 42

LATE_INDICES = list(range(24, 32))
FULL_INDICES = list(range(0, N_TOTAL_STAGES))
SVM_GAMMA_GRID = [0.1, 0.5, 1.0, 5.0]
RF_N_TREES = 100
GB_N_ESTIMATORS = 100
KFOLD_K = 5

THRESHOLD_DECODABLE = 0.75
THRESHOLD_PARTIAL_LOW = 0.55


def generate_input_states(n: int, seed: int = 0) -> tuple[list[Any], torch.Tensor, torch.Tensor, torch.Tensor]:
    rng = random.Random(seed)
    rhos: list[Any] = []
    bloch_rows: list[torch.Tensor] = []
    thetas: list[float] = []
    phis: list[float] = []
    while len(rhos) < n:
        cos_theta = rng.uniform(-1.0, 1.0)
        phi = rng.uniform(0.0, 2.0 * math.pi)
        theta = math.acos(cos_theta)
        alpha = math.cos(theta / 2.0)
        beta = math.sin(theta / 2.0) * complex(math.cos(phi), math.sin(phi))
        psi = ENGINE_I2[:, :1].copy()
        psi[0, 0] = alpha
        psi[1, 0] = beta
        pure = psi @ psi.conj().T
        rho = _normalize_density(0.90 * pure + 0.10 * ENGINE_I2 / 2.0)
        rhos.append(rho)
        bloch_rows.append(torch.as_tensor(_bloch_vector(rho), dtype=torch.float64))
        thetas.append(theta)
        phis.append(phi)
    return (
        rhos,
        torch.stack(bloch_rows, dim=0),
        torch.tensor(thetas, dtype=torch.float64),
        torch.tensor(phis, dtype=torch.float64),
    )


def quadrant_label(bx: float, by: float) -> int:
    if bx >= 0 and by >= 0:
        return 0
    if bx < 0 and by >= 0:
        return 1
    if bx < 0 and by < 0:
        return 2
    return 3


def octant_label(bx: float, by: float, bz: float) -> int:
    sx = 0 if bx >= 0 else 1
    sy = 0 if by >= 0 else 1
    sz = 0 if bz >= 0 else 1
    return sx * 4 + sy * 2 + sz


def holonomy_phase_from_density(rho: Any) -> float:
    off = complex(rho[0, 1])
    if abs(off) < 1e-18:
        return 0.0
    return math.atan2(off.imag, off.real)


def holonomy_phase_from_bloch(bloch_row: torch.Tensor) -> float:
    bx = float(bloch_row[0].item())
    by = float(bloch_row[1].item())
    if abs(bx) + abs(by) < 1e-18:
        return 0.0
    return math.atan2(by, bx)


def manifold_frob_diffs(bloch: torch.Tensor) -> torch.Tensor:
    diffs = torch.zeros((bloch.shape[0],), dtype=torch.float64)
    if bloch.shape[0] > 1:
        deltas = bloch[1:] - bloch[:-1]
        diffs[1:] = 0.5 * math.sqrt(2.0) * torch.linalg.norm(deltas, dim=1)
    return diffs


def run_paired_engines(rho_init: Any) -> dict[str, Any]:
    e1 = EngineCore(engine_type=0, manifold_enabled=True)
    e2 = EngineCore(engine_type=1, manifold_enabled=True)
    res1 = e1.run_full_cycle(rho_init)
    res2 = e2.run_full_cycle(rho_init)
    bloch_e1 = torch.tensor([row["bloch"] for row in res1["trajectory"]], dtype=torch.float64)
    bloch_e2 = torch.tensor([row["bloch"] for row in res2["trajectory"]], dtype=torch.float64)
    ent_e1 = torch.tensor([row["entropy"] for row in res1["trajectory"]], dtype=torch.float64)
    ent_e2 = torch.tensor([row["entropy"] for row in res2["trajectory"]], dtype=torch.float64)
    pur_e1 = torch.tensor([row["purity"] for row in res1["trajectory"]], dtype=torch.float64)
    pur_e2 = torch.tensor([row["purity"] for row in res2["trajectory"]], dtype=torch.float64)
    holo_e1 = torch.tensor([holonomy_phase_from_bloch(row) for row in bloch_e1], dtype=torch.float64)
    holo_e2 = torch.tensor([holonomy_phase_from_bloch(row) for row in bloch_e2], dtype=torch.float64)
    final_rho_e1 = torch.as_tensor(res1["final_rho"], dtype=torch.complex128)
    final_rho_e2 = torch.as_tensor(res2["final_rho"], dtype=torch.complex128)
    return {
        "bloch_e1": bloch_e1,
        "bloch_e2": bloch_e2,
        "ent_e1": ent_e1,
        "ent_e2": ent_e2,
        "pur_e1": pur_e1,
        "pur_e2": pur_e2,
        "holo_e1": holo_e1,
        "holo_e2": holo_e2,
        "mfrob_e1": manifold_frob_diffs(bloch_e1),
        "mfrob_e2": manifold_frob_diffs(bloch_e2),
        "final_rho_e1": final_rho_e1,
        "final_rho_e2": final_rho_e2,
    }


def run_identity_paired(rho_init: Any) -> dict[str, Any]:
    bvec = torch.as_tensor(_bloch_vector(rho_init), dtype=torch.float64)
    ent = float(_von_neumann_entropy(rho_init))
    pur = float(_purity(rho_init))
    holo = holonomy_phase_from_density(rho_init)
    return {
        "bloch_e1": bvec.repeat(N_TOTAL_STAGES, 1),
        "bloch_e2": bvec.repeat(N_TOTAL_STAGES, 1),
        "ent_e1": torch.full((N_TOTAL_STAGES,), ent, dtype=torch.float64),
        "ent_e2": torch.full((N_TOTAL_STAGES,), ent, dtype=torch.float64),
        "pur_e1": torch.full((N_TOTAL_STAGES,), pur, dtype=torch.float64),
        "pur_e2": torch.full((N_TOTAL_STAGES,), pur, dtype=torch.float64),
        "holo_e1": torch.full((N_TOTAL_STAGES,), holo, dtype=torch.float64),
        "holo_e2": torch.full((N_TOTAL_STAGES,), holo, dtype=torch.float64),
        "mfrob_e1": torch.zeros((N_TOTAL_STAGES,), dtype=torch.float64),
        "mfrob_e2": torch.zeros((N_TOTAL_STAGES,), dtype=torch.float64),
        "final_rho_e1": torch.as_tensor(rho_init, dtype=torch.complex128),
        "final_rho_e2": torch.as_tensor(rho_init, dtype=torch.complex128),
    }


def random_density(gen: torch.Generator) -> torch.Tensor:
    real = torch.randn((2, 2), generator=gen, dtype=torch.float64)
    imag = torch.randn((2, 2), generator=gen, dtype=torch.float64)
    a = torch.complex(real, imag)
    h = a @ a.conj().T
    return (h / torch.real(torch.trace(h))).to(torch.complex128)


def run_random_paired(_rho_init: Any, gen: torch.Generator) -> dict[str, Any]:
    b1 = torch.randn((N_TOTAL_STAGES, 3), generator=gen, dtype=torch.float64)
    b1 = b1 / torch.linalg.norm(b1, dim=1, keepdim=True) * 0.8
    b2 = torch.randn((N_TOTAL_STAGES, 3), generator=gen, dtype=torch.float64)
    b2 = b2 / torch.linalg.norm(b2, dim=1, keepdim=True) * 0.8
    return {
        "bloch_e1": b1,
        "bloch_e2": b2,
        "ent_e1": 0.2 + 0.5 * torch.rand((N_TOTAL_STAGES,), generator=gen, dtype=torch.float64),
        "ent_e2": 0.2 + 0.5 * torch.rand((N_TOTAL_STAGES,), generator=gen, dtype=torch.float64),
        "pur_e1": 0.3 + 0.6 * torch.rand((N_TOTAL_STAGES,), generator=gen, dtype=torch.float64),
        "pur_e2": 0.3 + 0.6 * torch.rand((N_TOTAL_STAGES,), generator=gen, dtype=torch.float64),
        "holo_e1": -math.pi + 2.0 * math.pi * torch.rand((N_TOTAL_STAGES,), generator=gen, dtype=torch.float64),
        "holo_e2": -math.pi + 2.0 * math.pi * torch.rand((N_TOTAL_STAGES,), generator=gen, dtype=torch.float64),
        "mfrob_e1": 0.6 * torch.rand((N_TOTAL_STAGES,), generator=gen, dtype=torch.float64),
        "mfrob_e2": 0.6 * torch.rand((N_TOTAL_STAGES,), generator=gen, dtype=torch.float64),
        "final_rho_e1": random_density(gen),
        "final_rho_e2": random_density(gen),
    }


def feat_bloch_entropy_at(traj: dict[str, Any], indices: list[int]) -> torch.Tensor:
    return torch.cat([
        traj["bloch_e1"][indices].flatten(),
        traj["bloch_e2"][indices].flatten(),
        traj["ent_e1"][indices],
        traj["ent_e2"][indices],
    ]).to(torch.float32)


def feat_extended_at(traj: dict[str, Any], indices: list[int]) -> torch.Tensor:
    parts: list[torch.Tensor] = []
    for eng in ("e1", "e2"):
        parts.append(traj[f"bloch_{eng}"][indices].flatten())
        parts.append(traj[f"ent_{eng}"][indices])
        parts.append(traj[f"pur_{eng}"][indices])
        parts.append(traj[f"holo_{eng}"][indices])
        parts.append(traj[f"mfrob_{eng}"][indices])
    return torch.cat(parts).to(torch.float32)


def feat_final_density(traj: dict[str, Any]) -> torch.Tensor:
    rho4 = torch.kron(traj["final_rho_e1"], traj["final_rho_e2"])
    return torch.real(rho4).flatten().to(torch.float32)


def manifold_metric_only(traj: dict[str, Any]) -> torch.Tensor:
    return torch.cat([traj["mfrob_e1"], traj["mfrob_e2"]]).to(torch.float32)


class ReadoutMLP(nn.Module):
    def __init__(self, input_dim: int, n_classes: int) -> None:
        super().__init__()
        self.net = nn.Sequential(nn.Linear(input_dim, HIDDEN_DIM), nn.ReLU(), nn.Linear(HIDDEN_DIM, n_classes))

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x)


class RegressionMLP(nn.Module):
    def __init__(self, input_dim: int) -> None:
        super().__init__()
        self.net = nn.Sequential(nn.Linear(input_dim, HIDDEN_DIM), nn.ReLU(), nn.Linear(HIDDEN_DIM, 1))

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x).squeeze(-1)


def mlp_classifier_test_accuracy(X_train: torch.Tensor, y_train: torch.Tensor, X_test: torch.Tensor, y_test: torch.Tensor, n_classes: int, seed: int = 0) -> float:
    torch.manual_seed(seed)
    model = ReadoutMLP(input_dim=X_train.shape[1], n_classes=n_classes)
    optimizer = optim.Adam(model.parameters(), lr=3e-3)
    criterion = nn.CrossEntropyLoss()
    X_tr = X_train.to(torch.float32)
    y_tr = y_train.to(torch.long)
    X_te = X_test.to(torch.float32)
    y_te = y_test.to(torch.long)
    for _ in range(N_EPOCHS):
        model.train()
        optimizer.zero_grad()
        loss = criterion(model(X_tr), y_tr)
        loss.backward()
        optimizer.step()
    model.eval()
    with torch.no_grad():
        return float((model(X_te).argmax(dim=1) == y_te).float().mean().item())


def mlp_regressor_test_r2(X_train: torch.Tensor, y_train: torch.Tensor, X_test: torch.Tensor, y_test: torch.Tensor, seed: int = 0) -> float:
    torch.manual_seed(seed)
    model = RegressionMLP(input_dim=X_train.shape[1])
    optimizer = optim.Adam(model.parameters(), lr=3e-3)
    criterion = nn.MSELoss()
    X_tr = X_train.to(torch.float32)
    y_tr = y_train.to(torch.float32)
    X_te = X_test.to(torch.float32)
    y_te = y_test.to(torch.float32)
    for _ in range(N_EPOCHS):
        model.train()
        optimizer.zero_grad()
        pred = model(X_tr)
        loss = criterion(pred, y_tr)
        loss.backward()
        optimizer.step()
    model.eval()
    with torch.no_grad():
        pred_te = model(X_te)
    ss_res = float(torch.sum((y_te - pred_te) ** 2).item())
    ss_tot = float(torch.sum((y_te - y_te.mean()) ** 2).item())
    return 1.0 - ss_res / max(ss_tot, 1e-12)


def scale_lists(X_train: torch.Tensor, X_test: torch.Tensor) -> tuple[Any, Any]:
    scaler = StandardScaler()
    X_tr = scaler.fit_transform(X_train.tolist())
    X_te = scaler.transform(X_test.tolist())
    return X_tr, X_te


def linear_classifier_test_accuracy(X_train: torch.Tensor, y_train: torch.Tensor, X_test: torch.Tensor, y_test: torch.Tensor) -> float:
    X_tr, X_te = scale_lists(X_train, X_test)
    clf = LogisticRegression(max_iter=2000, random_state=RANDOM_SEED)
    clf.fit(X_tr, y_train.tolist())
    return float(clf.score(X_te, y_test.tolist()))


def linear_regressor_test_r2(X_train: torch.Tensor, y_train: torch.Tensor, X_test: torch.Tensor, y_test: torch.Tensor) -> float:
    X_tr, X_te = scale_lists(X_train, X_test)
    reg = Ridge(alpha=1.0, random_state=RANDOM_SEED)
    reg.fit(X_tr, y_train.tolist())
    return float(reg.score(X_te, y_test.tolist()))


def svm_classifier_test_accuracy(X_train: torch.Tensor, y_train: torch.Tensor, X_test: torch.Tensor, y_test: torch.Tensor) -> tuple[float, float]:
    X_tr, X_te = scale_lists(X_train, X_test)
    best = -1.0
    best_gamma = SVM_GAMMA_GRID[0]
    for gamma in SVM_GAMMA_GRID:
        clf = SVC(kernel="rbf", gamma=gamma, C=1.0, random_state=RANDOM_SEED)
        clf.fit(X_tr, y_train.tolist())
        acc = float(clf.score(X_te, y_test.tolist()))
        if acc > best:
            best = acc
            best_gamma = gamma
    return best, best_gamma


def svm_regressor_test_r2(X_train: torch.Tensor, y_train: torch.Tensor, X_test: torch.Tensor, y_test: torch.Tensor) -> tuple[float, float]:
    X_tr, X_te = scale_lists(X_train, X_test)
    best = -float("inf")
    best_gamma = SVM_GAMMA_GRID[0]
    for gamma in SVM_GAMMA_GRID:
        reg = SVR(kernel="rbf", gamma=gamma, C=1.0)
        reg.fit(X_tr, y_train.tolist())
        r2 = float(reg.score(X_te, y_test.tolist()))
        if r2 > best:
            best = r2
            best_gamma = gamma
    return best, best_gamma


def rf_classifier_test_accuracy(X_train: torch.Tensor, y_train: torch.Tensor, X_test: torch.Tensor, y_test: torch.Tensor) -> float:
    clf = RandomForestClassifier(n_estimators=RF_N_TREES, random_state=RANDOM_SEED)
    clf.fit(X_train.tolist(), y_train.tolist())
    return float(clf.score(X_test.tolist(), y_test.tolist()))


def rf_regressor_test_r2(X_train: torch.Tensor, y_train: torch.Tensor, X_test: torch.Tensor, y_test: torch.Tensor) -> float:
    reg = RandomForestRegressor(n_estimators=RF_N_TREES, random_state=RANDOM_SEED)
    reg.fit(X_train.tolist(), y_train.tolist())
    return float(reg.score(X_test.tolist(), y_test.tolist()))


def gb_classifier_test_accuracy(X_train: torch.Tensor, y_train: torch.Tensor, X_test: torch.Tensor, y_test: torch.Tensor) -> float:
    clf = GradientBoostingClassifier(n_estimators=GB_N_ESTIMATORS, random_state=RANDOM_SEED)
    clf.fit(X_train.tolist(), y_train.tolist())
    return float(clf.score(X_test.tolist(), y_test.tolist()))


def gb_regressor_test_r2(X_train: torch.Tensor, y_train: torch.Tensor, X_test: torch.Tensor, y_test: torch.Tensor) -> float:
    reg = GradientBoostingRegressor(n_estimators=GB_N_ESTIMATORS, random_state=RANDOM_SEED)
    reg.fit(X_train.tolist(), y_train.tolist())
    return float(reg.score(X_test.tolist(), y_test.tolist()))


def cv_score(X_train: torch.Tensor, y_train: torch.Tensor, fit_fn: Callable[[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor], float | tuple[float, float]]) -> float:
    kf = KFold(n_splits=KFOLD_K, shuffle=True, random_state=RANDOM_SEED)
    scores: list[float] = []
    for tr_idx, te_idx in kf.split(X_train.tolist()):
        score = fit_fn(X_train[tr_idx], y_train[tr_idx], X_train[te_idx], y_train[te_idx])
        scores.append(float(score[0] if isinstance(score, tuple) else score))
    return sum(scores) / max(len(scores), 1)


def sweep_classification(X_tr: torch.Tensor, y_tr: torch.Tensor, X_te: torch.Tensor, y_te: torch.Tensor, n_classes: int) -> dict[str, Any]:
    out: dict[str, Any] = {}
    out["linear"] = {
        "test_accuracy": linear_classifier_test_accuracy(X_tr, y_tr, X_te, y_te),
        "cv_mean_accuracy": cv_score(X_tr, y_tr, linear_classifier_test_accuracy),
    }
    out["mlp_small"] = {"test_accuracy": mlp_classifier_test_accuracy(X_tr, y_tr, X_te, y_te, n_classes=n_classes, seed=0)}
    svm_acc, gamma = svm_classifier_test_accuracy(X_tr, y_tr, X_te, y_te)
    out["svm_rbf"] = {"test_accuracy": svm_acc, "best_gamma": gamma}
    out["random_forest"] = {"test_accuracy": rf_classifier_test_accuracy(X_tr, y_tr, X_te, y_te)}
    out["gradient_boosting"] = {"test_accuracy": gb_classifier_test_accuracy(X_tr, y_tr, X_te, y_te)}
    return out


def sweep_regression(X_tr: torch.Tensor, y_tr: torch.Tensor, X_te: torch.Tensor, y_te: torch.Tensor) -> dict[str, Any]:
    out: dict[str, Any] = {}
    out["linear"] = {
        "test_r2": linear_regressor_test_r2(X_tr, y_tr, X_te, y_te),
        "cv_mean_r2": cv_score(X_tr, y_tr, linear_regressor_test_r2),
    }
    out["mlp_small"] = {"test_r2": mlp_regressor_test_r2(X_tr, y_tr, X_te, y_te, seed=0)}
    svm_r2, gamma = svm_regressor_test_r2(X_tr, y_tr, X_te, y_te)
    out["svm_rbf"] = {"test_r2": svm_r2, "best_gamma": gamma}
    out["random_forest"] = {"test_r2": rf_regressor_test_r2(X_tr, y_tr, X_te, y_te)}
    out["gradient_boosting"] = {"test_r2": gb_regressor_test_r2(X_tr, y_tr, X_te, y_te)}
    return out


def build_feature_matrix(trajs: list[dict[str, Any]], variant: str) -> torch.Tensor:
    if variant == "feat_bloch_entropy":
        rows = [feat_bloch_entropy_at(t, LATE_INDICES) for t in trajs]
    elif variant == "feat_extended":
        rows = [feat_extended_at(t, LATE_INDICES) for t in trajs]
    elif variant == "feat_final_density":
        rows = [feat_final_density(t) for t in trajs]
    elif variant == "manifold_metric_only":
        rows = [manifold_metric_only(t) for t in trajs]
    elif variant == "feat_extended_full":
        rows = [feat_extended_at(t, FULL_INDICES) for t in trajs]
    else:
        raise ValueError(variant)
    return torch.stack(rows, dim=0).to(torch.float32)


def best_classifier_score(cell: dict[str, Any]) -> float:
    return max(float(v["test_accuracy"]) for v in cell.values())


def best_regressor_score(cell: dict[str, Any]) -> float:
    return max(float(v["test_r2"]) for v in cell.values())


def as_jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): as_jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [as_jsonable(v) for v in value]
    if isinstance(value, torch.Tensor):
        return value.detach().cpu().tolist()
    return value


def main() -> int:
    started = time.time()
    print(f"Generating {N_SAMPLES} input states...")
    rhos, input_bloch, input_theta, input_phi = generate_input_states(N_SAMPLES, seed=RANDOM_SEED)
    input_quadrant = torch.tensor([quadrant_label(float(b[0]), float(b[1])) for b in input_bloch], dtype=torch.long)
    input_octant = torch.tensor([octant_label(float(b[0]), float(b[1]), float(b[2])) for b in input_bloch], dtype=torch.long)
    print(f"  quadrant counts: {[int((input_quadrant == c).sum().item()) for c in range(N_QUADRANTS)]}")
    print(f"  octant counts: {[int((input_octant == c).sum().item()) for c in range(N_OCTANTS)]}")

    engine_trajs: list[dict[str, Any]] = []
    identity_trajs: list[dict[str, Any]] = []
    random_trajs: list[dict[str, Any]] = []
    rand_gen = torch.Generator().manual_seed(RANDOM_SEED + 11)
    for i, rho in enumerate(rhos):
        if i % 25 == 0:
            print(f"  state {i}/{N_SAMPLES} elapsed={time.time() - started:.1f}s")
        engine_trajs.append(run_paired_engines(rho))
        identity_trajs.append(run_identity_paired(rho))
        random_trajs.append(run_random_paired(rho, rand_gen))

    feature_variants = ["feat_bloch_entropy", "feat_extended", "feat_final_density", "manifold_metric_only", "feat_extended_full"]
    feature_matrices = {
        "engine": {v: build_feature_matrix(engine_trajs, v) for v in feature_variants},
        "identity": {v: build_feature_matrix(identity_trajs, v) for v in feature_variants},
        "random": {v: build_feature_matrix(random_trajs, v) for v in feature_variants},
    }
    train_mask = torch.arange(N_SAMPLES) < N_TRAIN
    test_mask = ~train_mask
    targets = {
        "quadrant": (input_quadrant, N_QUADRANTS, "classification"),
        "octant": (input_octant, N_OCTANTS, "classification"),
        "theta": (input_theta.to(torch.float32), 1, "regression"),
        "phi": (input_phi.to(torch.float32), 1, "regression"),
    }

    matrix: dict[str, dict[str, dict[str, dict[str, Any]]]] = {}
    for kind, variants in feature_matrices.items():
        matrix[kind] = {}
        for variant, X in variants.items():
            matrix[kind][variant] = {}
            X_tr = X[train_mask]
            X_te = X[test_mask]
            for label, (y, n_classes, task_type) in targets.items():
                y_tr = y[train_mask]
                y_te = y[test_mask]
                if task_type == "classification":
                    matrix[kind][variant][label] = sweep_classification(X_tr, y_tr, X_te, y_te, n_classes)
                else:
                    matrix[kind][variant][label] = sweep_regression(X_tr, y_tr, X_te, y_te)

    engine_best = {
        "classification": max(
            best_classifier_score(matrix["engine"][variant][label])
            for variant in feature_variants
            for label in ("quadrant", "octant")
        ),
        "regression": max(
            best_regressor_score(matrix["engine"][variant][label])
            for variant in feature_variants
            for label in ("theta", "phi")
        ),
    }
    identity_best = {
        "classification": max(
            best_classifier_score(matrix["identity"][variant][label])
            for variant in feature_variants
            for label in ("quadrant", "octant")
        ),
        "regression": max(
            best_regressor_score(matrix["identity"][variant][label])
            for variant in feature_variants
            for label in ("theta", "phi")
        ),
    }
    random_best = {
        "classification": max(
            best_classifier_score(matrix["random"][variant][label])
            for variant in feature_variants
            for label in ("quadrant", "octant")
        ),
        "regression": max(
            best_regressor_score(matrix["random"][variant][label])
            for variant in feature_variants
            for label in ("theta", "phi")
        ),
    }
    best_engine_score = max(engine_best["classification"], engine_best["regression"])
    if best_engine_score >= THRESHOLD_DECODABLE:
        verdict = "decodable_with_richer_readout"
    elif best_engine_score >= THRESHOLD_PARTIAL_LOW:
        verdict = "partial_recovery"
    else:
        verdict = "rearrangement_destroys_label_universally"

    positive = {
        "all_readout_families_trained": {
            "pass": all(name in matrix["engine"]["feat_bloch_entropy"]["quadrant"] for name in ["linear", "mlp_small", "svm_rbf", "random_forest", "gradient_boosting"]),
        },
        "identity_engine_has_recoverable_label": {
            "pass": identity_best["classification"] >= 0.85 or identity_best["regression"] >= 0.85,
            "identity_best": identity_best,
        },
        "definitive_verdict_reached": {"pass": verdict in {"decodable_with_richer_readout", "partial_recovery", "rearrangement_destroys_label_universally"}, "verdict": verdict},
    }
    negative = {
        "random_engine_not_stronger_than_identity": {
            "pass": random_best["classification"] < identity_best["classification"] and random_best["regression"] < identity_best["regression"],
            "random_best": random_best,
        },
        "richer_readout_does_not_promote_engine_claim": {
            "pass": PROMOTION_ALLOWED is False and CLASSIFICATION == "formal_scout",
        },
    }
    boundary = {
        "features_are_finite": {
            "pass": all(bool(torch.isfinite(X).all().item()) for kind in feature_matrices.values() for X in kind.values()),
        },
        "claim_ceiling_present": {"pass": "Formal scout only" in CLAIM_CEILING},
    }
    all_pass = all(row["pass"] for row in positive.values()) and all(row["pass"] for row in negative.values()) and all(row["pass"] for row in boundary.values())

    result = {
        "name": NAME,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "config": {
            "n_samples": N_SAMPLES,
            "n_train": N_TRAIN,
            "late_indices": LATE_INDICES,
            "feature_variants": feature_variants,
            "readouts": ["linear", "mlp_small", "svm_rbf", "random_forest", "gradient_boosting"],
        },
        "headline": {
            "verdict": verdict,
            "engine_best": engine_best,
            "identity_best": identity_best,
            "random_best": random_best,
        },
        "positive": positive,
        "negative": negative,
        "graveyard_companions": negative,
        "boundary": boundary,
        "nearby_variants": {
            "total": len(negative),
            "passed": sum(1 for row in negative.values() if row.get("pass")),
            "variants": sorted(negative),
        },
        "why_not_v4_probes": [
            "v5 formal scout over richer late-stage readout-family information recovery.",
            "Does not promote canonical engine, axis, bridge, manifold, or target-system claims.",
            "The readout-family comparison is bounded to the finite fixture and controls.",
        ],
        "readout_matrix": matrix,
        "all_pass": all_pass,
        "elapsed_seconds": time.time() - started,
    }
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(as_jsonable(result), indent=2, sort_keys=True), encoding="utf-8")
    print(f"RESULT {NAME}: all_pass={all_pass} -> {OUT_PATH}")
    print(f"  verdict={verdict} engine_best={engine_best} identity_best={identity_best} random_best={random_best}")
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
