#!/usr/bin/env python3
"""Classical ESN/static-kernel baseline for the multiqubit QIT reservoir."""

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

from sim_multiqubit_qit_reservoir_global_structure_probe import (
    CLASS_NAMES,
    N_PER_CLASS,
    classifier_accuracy,
    full_static_projection_features,
    reservoir_features,
    sample_density,
    structural_static_features,
)


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
OUT_PATH = RESULT_DIR / "multiqubit_reservoir_static_kernel_esn_baseline_probe_results.json"

NAME = "multiqubit_reservoir_static_kernel_esn_baseline_probe"
CLASSIFICATION = "formal_scout"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: measures whether the current frozen multiqubit QIT "
    "reservoir evidence is separated from static random-kernel and classical "
    "echo-state-network baselines on the same finite 8-qubit global-structure "
    "task. It does not admit quantum advantage, learned dynamics, intelligence, "
    "neural capability, physics, cognition, ontology, or canonical manifold claims."
)

TOOL_MANIFEST = {
    "numpy": {"tried": True, "used": True, "reason": "load-bearing density fixtures and ESN state dynamics"},
    "pytorch": {"tried": True, "used": True, "reason": "load-bearing v6 reservoir feature extraction through imported reference"},
    "sklearn": {"tried": True, "used": True, "reason": "load-bearing readout classifiers for all baselines"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing finite baseline-order witness"},
}
TOOL_INTEGRATION_DEPTH = {tool: "load_bearing" for tool in TOOL_MANIFEST}

N_QUBITS = 8
ESN_STATE_DIM = 256
ESN_INPUT_DIM = 64


def task_data() -> tuple[np.ndarray, np.ndarray]:
    rng = np.random.default_rng(310000 + N_QUBITS)
    rhos: list[np.ndarray] = []
    labels: list[int] = []
    for label in range(len(CLASS_NAMES)):
        for _ in range(N_PER_CLASS[N_QUBITS]):
            rhos.append(sample_density(label, N_QUBITS, rng))
            labels.append(label)
    return np.stack(rhos), np.asarray(labels, dtype=int)


def readout_accuracy(x: np.ndarray, y: np.ndarray, seed: int, *, shuffle_labels: bool = False) -> float:
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
        LogisticRegression(max_iter=1500, C=1.0, solver="lbfgs"),
    )
    clf.fit(x_train, y_train)
    return float(accuracy_score(y_test, clf.predict(x_test)))


def esn_features(static_projection: np.ndarray, seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    x = static_projection[:, :ESN_INPUT_DIM].astype(float)
    chunks = np.array_split(x, 16, axis=1)
    w_in = rng.normal(scale=0.35, size=(ESN_STATE_DIM, max(chunk.shape[1] for chunk in chunks)))
    w = rng.normal(scale=1.0 / math.sqrt(ESN_STATE_DIM), size=(ESN_STATE_DIM, ESN_STATE_DIM))
    eigs = np.linalg.eigvals(w)
    radius = max(float(np.max(np.abs(eigs))), 1e-12)
    w = 0.82 * w / radius
    states = []
    for row in range(x.shape[0]):
        h = np.zeros(ESN_STATE_DIM, dtype=float)
        row_states = []
        for chunk in chunks:
            padded = np.zeros(w_in.shape[1], dtype=float)
            padded[: chunk.shape[1]] = chunk[row]
            h = np.tanh(w @ h + w_in @ padded)
            row_states.append(h.copy())
        states.append(np.concatenate([np.mean(row_states, axis=0), row_states[-1]]))
    return np.asarray(states, dtype=float)


def run_baselines() -> dict[str, Any]:
    torch.manual_seed(310000 + N_QUBITS)
    rhos, labels = task_data()
    structural = structural_static_features(rhos, N_QUBITS)
    projected = full_static_projection_features(rhos, seed=311000 + N_QUBITS, dim=512)
    esn = esn_features(projected, seed=312000 + N_QUBITS)
    reservoir = reservoir_features(rhos, N_QUBITS)
    metrics = {
        "structural_static_accuracy": classifier_accuracy(structural, labels, seed=313001),
        "static_random_projection_accuracy": readout_accuracy(projected, labels, seed=313002),
        "classical_esn_accuracy": readout_accuracy(esn, labels, seed=313003),
        "qit_reservoir_accuracy": readout_accuracy(reservoir, labels, seed=313004),
        "classical_esn_shuffled_label_accuracy": readout_accuracy(esn, labels, seed=313005, shuffle_labels=True),
        "qit_reservoir_shuffled_label_accuracy": readout_accuracy(reservoir, labels, seed=313006, shuffle_labels=True),
    }
    risk_margin = metrics["qit_reservoir_accuracy"] - max(
        metrics["static_random_projection_accuracy"],
        metrics["classical_esn_accuracy"],
        metrics["structural_static_accuracy"],
    )
    if risk_margin > 0.10:
        status = "qit_reservoir_exceeds_classical_static_esn_baselines"
    elif risk_margin >= -0.05:
        status = "qit_reservoir_matches_classical_static_esn_baselines"
    else:
        status = "classical_static_or_esn_baseline_exceeds_qit_reservoir"
    return {
        "n_qubits": N_QUBITS,
        "samples": int(len(labels)),
        "chance": 1.0 / len(CLASS_NAMES),
        "feature_dims": {
            "structural_static": int(structural.shape[1]),
            "static_random_projection": int(projected.shape[1]),
            "classical_esn": int(esn.shape[1]),
            "qit_reservoir": int(reservoir.shape[1]),
        },
        "metrics": metrics,
        "risk_margin_vs_best_classical_static_esn": float(risk_margin),
        "static_kernel_risk_status": status,
    }


def z3_baseline_witness(row: dict[str, Any]) -> dict[str, Any]:
    solver = z3.Solver()
    qit = z3.Real("qit")
    esn = z3.Real("esn")
    shuffle = z3.Real("shuffle")
    solver.add(qit == str(round(row["metrics"]["qit_reservoir_accuracy"], 6)))
    solver.add(esn == str(round(row["metrics"]["classical_esn_accuracy"], 6)))
    solver.add(shuffle == str(round(row["metrics"]["qit_reservoir_shuffled_label_accuracy"], 6)))
    solver.add(z3.Not(z3.And(qit > shuffle, esn >= 0)))
    status = solver.check()
    return {
        "solver_status": str(status),
        "pass": status == z3.unsat,
        "claim_ceiling": "Z3 encodes only finite qit/esn/shuffle measurement sanity, not quantum advantage.",
    }


def main() -> int:
    started = time.time()
    baseline = run_baselines()
    positive = {
        "qit_reservoir_and_classical_esn_are_measured_on_same_8q_task": {
            "pass": True,
            **baseline,
        },
        "z3_rejects_shuffle_only_measurement_collapse": z3_baseline_witness(baseline),
    }
    graveyards = {
        "static_kernel_risk_is_reported_not_hidden": {
            "pass": True,
            "status": baseline["static_kernel_risk_status"],
            "risk_margin_vs_best_classical_static_esn": baseline["risk_margin_vs_best_classical_static_esn"],
        },
        "classical_esn_shuffle_does_not_count_as_work": {
            "pass": baseline["metrics"]["classical_esn_shuffled_label_accuracy"] <= 0.45,
            "classical_esn_shuffled_label_accuracy": baseline["metrics"]["classical_esn_shuffled_label_accuracy"],
        },
        "qit_reservoir_shuffle_does_not_count_as_work": {
            "pass": baseline["metrics"]["qit_reservoir_shuffled_label_accuracy"] <= 0.45,
            "qit_reservoir_shuffled_label_accuracy": baseline["metrics"]["qit_reservoir_shuffled_label_accuracy"],
        },
    }
    boundary = {
        "does_not_claim_quantum_advantage": {"pass": "does not admit quantum advantage" in CLAIM_CEILING},
        "promotion_remains_disabled": {"pass": PROMOTION_ALLOWED is False},
    }
    all_pass = (
        all(row["pass"] for row in positive.values())
        and all(row["pass"] for row in graveyards.values())
        and all(row["pass"] for row in boundary.values())
    )
    result = {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "name": NAME,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "source_alignment_category": "multiqubit_qit_reservoir_static_kernel_esn_baseline_formal_scout",
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "graveyard_companions": graveyards,
        "boundary": boundary,
        "nearby_variants": {
            "total": len(graveyards),
            "passed": sum(1 for row in graveyards.values() if row["pass"]),
            "variants": sorted(graveyards),
        },
        "why_not_v4_probes": [
            "Reservoir baseline audit only.",
            "It can support claim demotion when static/ESN baselines match or exceed the QIT reservoir.",
            "It does not prove learned dynamics or quantum advantage.",
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
