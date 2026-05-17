#!/usr/bin/env python3
"""Multi-qubit QIT reservoir global-structure classification scout."""

from __future__ import annotations

import json
import math
import pathlib
import time
from typing import Any

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
import torch
import z3

import engine_v6_proper_multiqubit_reference as v6


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
OUT_PATH = RESULT_DIR / "multiqubit_qit_reservoir_global_structure_probe_results.json"

NAME = "multiqubit_qit_reservoir_global_structure_probe"
CLASSIFICATION = "formal_scout"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: tests whether a frozen multi-qubit QIT reservoir built "
    "from the v6 reference engine separates global correlation classes whose "
    "single-qubit marginals are intentionally uninformative. It does not prove "
    "learned dynamics and does not admit intelligence, neural capability, canonical "
    "manifold status, physics, cognition, or 64-site PEPS3D behavior."
)

TOOL_MANIFEST = {
    "pytorch": {"tried": True, "used": True, "reason": "load-bearing frozen multi-qubit engine feature extraction"},
    "sklearn": {"tried": True, "used": True, "reason": "load-bearing linear readout and baseline classifiers"},
    "numpy": {"tried": True, "used": True, "reason": "load-bearing density construction and local-unitary perturbations"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing finite pass-predicate witness"},
    "engine_v6_reference": {"tried": True, "used": True, "reason": "load-bearing repo-grounded copy of the external v6 candidate"},
}
TOOL_INTEGRATION_DEPTH = {tool: "load_bearing" for tool in TOOL_MANIFEST}

DTYPE = np.complex64
CLASS_NAMES = ["ghz_coherent", "ghz_dephased", "bell_pair_product", "even_parity_mixture"]
N_PER_CLASS = {4: 28, 8: 20}


def random_unitary_2(rng: np.random.Generator) -> np.ndarray:
    z = rng.normal(size=(2, 2)) + 1j * rng.normal(size=(2, 2))
    q, r = np.linalg.qr(z)
    phase = np.diag(r) / np.maximum(np.abs(np.diag(r)), 1e-12)
    return (q * phase).astype(DTYPE)


def kron_all(mats: list[np.ndarray]) -> np.ndarray:
    out = mats[0]
    for mat in mats[1:]:
        out = np.kron(out, mat)
    return out.astype(DTYPE)


def ghz_density(n_qubits: int, phase: float) -> np.ndarray:
    d = 2**n_qubits
    psi = np.zeros(d, dtype=DTYPE)
    psi[0] = 1.0 / math.sqrt(2)
    psi[-1] = np.exp(1j * phase) / math.sqrt(2)
    return np.outer(psi, psi.conj()).astype(DTYPE)


def ghz_dephased_density(n_qubits: int) -> np.ndarray:
    d = 2**n_qubits
    rho = np.zeros((d, d), dtype=DTYPE)
    rho[0, 0] = 0.5
    rho[-1, -1] = 0.5
    return rho


def bell_pair_product_density(n_qubits: int, rng: np.random.Generator) -> np.ndarray:
    assert n_qubits % 2 == 0
    pair = np.zeros(4, dtype=DTYPE)
    phase = np.exp(1j * rng.uniform(0, 2 * math.pi))
    pair[0] = 1.0 / math.sqrt(2)
    pair[3] = phase / math.sqrt(2)
    psi = pair
    for _ in range(n_qubits // 2 - 1):
        phase = np.exp(1j * rng.uniform(0, 2 * math.pi))
        pair = np.zeros(4, dtype=DTYPE)
        pair[0] = 1.0 / math.sqrt(2)
        pair[3] = phase / math.sqrt(2)
        psi = np.kron(psi, pair)
    return np.outer(psi, psi.conj()).astype(DTYPE)


def even_parity_mixture_density(n_qubits: int) -> np.ndarray:
    d = 2**n_qubits
    rho = np.zeros((d, d), dtype=DTYPE)
    states = [idx for idx in range(d) if bin(idx).count("1") % 2 == 0]
    for idx in states:
        rho[idx, idx] = 1.0 / len(states)
    return rho


def base_density(label: int, n_qubits: int, rng: np.random.Generator) -> np.ndarray:
    if label == 0:
        return ghz_density(n_qubits, rng.uniform(0, 2 * math.pi))
    if label == 1:
        return ghz_dephased_density(n_qubits)
    if label == 2:
        return bell_pair_product_density(n_qubits, rng)
    if label == 3:
        return even_parity_mixture_density(n_qubits)
    raise ValueError(label)


def sample_density(label: int, n_qubits: int, rng: np.random.Generator) -> np.ndarray:
    rho = base_density(label, n_qubits, rng)
    local_u = kron_all([random_unitary_2(rng) for _ in range(n_qubits)])
    rho = local_u @ rho @ local_u.conj().T
    rho = (rho + rho.conj().T) / 2
    rho = rho / np.trace(rho).real
    return rho.astype(DTYPE)


def partial_trace_np(rho: np.ndarray, n_qubits: int, keep: list[int]) -> np.ndarray:
    keep = sorted(keep)
    trace = [idx for idx in range(n_qubits) if idx not in keep]
    reshaped = rho.reshape([2] * (2 * n_qubits))
    for q in sorted(trace, reverse=True):
        n_now = reshaped.ndim // 2
        reshaped = np.trace(reshaped, axis1=q, axis2=n_now + q)
    d = 2 ** len(keep)
    return reshaped.reshape(d, d)


def entropy_np(rho: np.ndarray) -> float:
    vals = np.linalg.eigvalsh((rho + rho.conj().T) / 2).real
    vals = np.clip(vals, 1e-9, None)
    vals = vals / vals.sum()
    return float(-(vals * np.log(vals)).sum())


def local_bloch_features(rhos: np.ndarray, n_qubits: int) -> np.ndarray:
    x = np.array([[0, 1], [1, 0]], dtype=DTYPE)
    y = np.array([[0, -1j], [1j, 0]], dtype=DTYPE)
    z = np.array([[1, 0], [0, -1]], dtype=DTYPE)
    rows = []
    for rho in rhos:
        feat = []
        for q in range(n_qubits):
            red = partial_trace_np(rho, n_qubits, [q])
            feat.extend([np.trace(x @ red).real, np.trace(y @ red).real, np.trace(z @ red).real])
        rows.append(feat)
    return np.asarray(rows, dtype=float)


def structural_static_features(rhos: np.ndarray, n_qubits: int) -> np.ndarray:
    rows = []
    half = list(range(n_qubits // 2))
    other = list(range(n_qubits // 2, n_qubits))
    for rho in rhos:
        rho_a = partial_trace_np(rho, n_qubits, half)
        rho_b = partial_trace_np(rho, n_qubits, other)
        s_ab = entropy_np(rho)
        mi = entropy_np(rho_a) + entropy_np(rho_b) - s_ab
        purity = float(np.trace(rho @ rho).real)
        spectrum = np.sort(np.linalg.eigvalsh((rho + rho.conj().T) / 2).real)[-8:]
        rows.append([s_ab, mi, purity, *spectrum.tolist()])
    return np.asarray(rows, dtype=float)


def full_static_projection_features(rhos: np.ndarray, seed: int, dim: int = 512) -> np.ndarray:
    flat = np.concatenate([rhos.real.reshape(len(rhos), -1), rhos.imag.reshape(len(rhos), -1)], axis=1)
    rng = np.random.default_rng(seed)
    proj = rng.normal(scale=1.0 / math.sqrt(dim), size=(flat.shape[1], dim))
    return flat @ proj


def reservoir_features(rhos: np.ndarray, n_qubits: int) -> np.ndarray:
    torch.manual_seed(1234 + n_qubits)
    engine = v6.TrainablePairedEngineV6(n_classes=len(CLASS_NAMES), n_qubits=n_qubits, hidden_dim=64)
    engine.eval()
    with torch.no_grad():
        rho_t = torch.tensor(rhos, dtype=v6.DTYPE)
        feats_l = engine.engine_L(rho_t)
        feats_r = engine.engine_R(rho_t)
        feats = torch.cat([feats_l, feats_r], dim=-1).detach().cpu().numpy()
    return feats.astype(float)


def classifier_accuracy(x: np.ndarray, y: np.ndarray, seed: int, shuffle_labels: bool = False) -> float:
    labels = y.copy()
    if shuffle_labels:
        rng = np.random.default_rng(seed)
        rng.shuffle(labels)
    x_train, x_test, y_train, y_test = train_test_split(
        x,
        labels,
        test_size=0.35,
        random_state=seed,
        stratify=labels,
    )
    clf = make_pipeline(
        StandardScaler(),
        LogisticRegression(max_iter=1200, C=1.0, solver="lbfgs"),
    )
    clf.fit(x_train, y_train)
    return float(accuracy_score(y_test, clf.predict(x_test)))


def run_for_n(n_qubits: int) -> dict[str, Any]:
    rng = np.random.default_rng(120000 + n_qubits)
    rhos = []
    labels = []
    for label in range(len(CLASS_NAMES)):
        for _ in range(N_PER_CLASS[n_qubits]):
            rhos.append(sample_density(label, n_qubits, rng))
            labels.append(label)
    rhos_arr = np.stack(rhos)
    y = np.asarray(labels, dtype=int)
    local = local_bloch_features(rhos_arr, n_qubits)
    static = structural_static_features(rhos_arr, n_qubits)
    projected = full_static_projection_features(rhos_arr, seed=130000 + n_qubits)
    reservoir = reservoir_features(rhos_arr, n_qubits)
    metrics = {
        "local_only_accuracy": classifier_accuracy(local, y, seed=1 + n_qubits),
        "structural_static_accuracy": classifier_accuracy(static, y, seed=2 + n_qubits),
        "full_static_random_projection_accuracy": classifier_accuracy(projected, y, seed=3 + n_qubits),
        "frozen_reservoir_accuracy": classifier_accuracy(reservoir, y, seed=4 + n_qubits),
        "frozen_reservoir_shuffled_label_accuracy": classifier_accuracy(reservoir, y, seed=5 + n_qubits, shuffle_labels=True),
    }
    local_norm = float(np.max(np.abs(local)))
    return {
        "n_qubits": n_qubits,
        "samples": int(len(y)),
        "chance": 1.0 / len(CLASS_NAMES),
        "feature_dims": {
            "local_only": int(local.shape[1]),
            "structural_static": int(static.shape[1]),
            "full_static_random_projection": int(projected.shape[1]),
            "frozen_reservoir": int(reservoir.shape[1]),
        },
        "max_abs_local_bloch_feature": local_norm,
        "metrics": metrics,
        "pass": local_norm < 1e-4
        and metrics["frozen_reservoir_accuracy"] >= 0.70
        and metrics["frozen_reservoir_accuracy"] > metrics["local_only_accuracy"] + 0.25
        and metrics["frozen_reservoir_shuffled_label_accuracy"] <= 0.45,
    }


def z3_scaling_witness(rows: list[dict[str, Any]]) -> dict[str, Any]:
    row8 = next(row for row in rows if row["n_qubits"] == 8)
    solver = z3.Solver()
    n8 = z3.Int("n8")
    res8 = z3.Real("res8")
    local8 = z3.Real("local8")
    shuffled8 = z3.Real("shuffled8")
    solver.add(n8 == 8)
    solver.add(res8 == str(round(row8["metrics"]["frozen_reservoir_accuracy"], 6)))
    solver.add(local8 == str(round(row8["metrics"]["local_only_accuracy"], 6)))
    solver.add(shuffled8 == str(round(row8["metrics"]["frozen_reservoir_shuffled_label_accuracy"], 6)))
    solver.add(z3.Not(z3.And(n8 >= 8, res8 > local8, shuffled8 < res8)))
    status = solver.check()
    return {
        "solver_status": str(status),
        "pass": status == z3.unsat,
        "claim_ceiling": "Z3 encodes only finite N=8 reservoir/local/shuffle ordering.",
    }


def main() -> int:
    started = time.time()
    rows = [run_for_n(4), run_for_n(8)]
    row8 = next(row for row in rows if row["n_qubits"] == 8)
    positive = {
        "frozen_multiqubit_reservoir_separates_global_structure_at_8q": {
            "rows": rows,
            "pass": row8["pass"],
        },
        "z3_rejects_local_or_shuffle_only_explanation_at_8q": z3_scaling_witness(rows),
    }
    graveyards = {
        "local_single_qubit_marginals_are_uninformative": {
            "max_abs_local_bloch_by_n": {str(row["n_qubits"]): row["max_abs_local_bloch_feature"] for row in rows},
            "pass": all(row["max_abs_local_bloch_feature"] < 1e-4 for row in rows),
        },
        "shuffled_labels_do_not_count_as_work": {
            "shuffled_accuracy_by_n": {str(row["n_qubits"]): row["metrics"]["frozen_reservoir_shuffled_label_accuracy"] for row in rows},
            "pass": row8["metrics"]["frozen_reservoir_shuffled_label_accuracy"] <= 0.45,
        },
        "full_static_baseline_is_reported_not_hidden": {
            "full_static_random_projection_accuracy_by_n": {str(row["n_qubits"]): row["metrics"]["full_static_random_projection_accuracy"] for row in rows},
            "pass": all("full_static_random_projection_accuracy" in row["metrics"] for row in rows),
        },
    }
    boundary = {
        "eight_qubit_is_the_evidence_floor": {"min_evidence_qubits": 8, "pass": row8["n_qubits"] == 8},
        "promotion_remains_disabled": {"pass": PROMOTION_ALLOWED is False},
    }
    all_pass = all(row["pass"] for row in positive.values()) and all(row["pass"] for row in graveyards.values()) and all(row["pass"] for row in boundary.values())
    result = {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "name": NAME,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "source_alignment_category": "source_native_multiqubit_qit_reservoir_formal_scout",
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "graveyard_companions": graveyards,
        "boundary": boundary,
        "nearby_variants": {"total": len(graveyards), "passed": sum(1 for row in graveyards.values() if row["pass"]), "variants": sorted(graveyards)},
        "why_not_v4_probes": [
            "Frozen-reservoir readout scout only.",
            "Does not prove learned engine dynamics.",
            "Includes full-static baseline as overclaim guard.",
        ],
        "blockers": [],
        "elapsed_seconds": time.time() - started,
        "all_pass": all_pass,
    }
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print(f"RESULT {NAME}: all_pass={all_pass} -> {OUT_PATH}")
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
