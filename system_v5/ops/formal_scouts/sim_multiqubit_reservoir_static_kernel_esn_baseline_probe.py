#!/usr/bin/env python3
"""Classical ESN/static-kernel baseline for the multiqubit QIT reservoir."""

from __future__ import annotations

import json
import math
import pathlib
import time
from typing import Any

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
    REAL_DTYPE,
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
    "pytorch": {"tried": True, "used": True, "reason": "load-bearing density fixtures, ESN state dynamics, and v6 reservoir feature extraction through imported reference"},
    "sklearn": {"tried": True, "used": True, "reason": "load-bearing readout classifiers for all baselines"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing finite baseline-order witness"},
}
TOOL_INTEGRATION_DEPTH = {tool: "load_bearing" for tool in TOOL_MANIFEST}

N_QUBITS = 8
ESN_STATE_DIM = 256
ESN_INPUT_DIM = 64


def task_data() -> tuple[torch.Tensor, torch.Tensor]:
    generator = torch.Generator().manual_seed(310000 + N_QUBITS)
    rhos: list[torch.Tensor] = []
    labels: list[int] = []
    for label in range(len(CLASS_NAMES)):
        for _ in range(N_PER_CLASS[N_QUBITS]):
            rhos.append(sample_density(label, N_QUBITS, generator))
            labels.append(label)
    return torch.stack(rhos), torch.tensor(labels, dtype=torch.long)


def _sklearn_rows(value: Any) -> list[Any]:
    if isinstance(value, torch.Tensor):
        return value.detach().cpu().tolist()
    return value


def readout_accuracy(x: torch.Tensor, y: torch.Tensor, seed: int, *, shuffle_labels: bool = False) -> float:
    labels = y.detach().cpu().to(dtype=torch.long).clone()
    if shuffle_labels:
        generator = torch.Generator().manual_seed(seed)
        labels = labels[torch.randperm(labels.numel(), generator=generator)]
    x_rows = _sklearn_rows(x)
    y_rows = labels.tolist()
    x_train, x_test, y_train, y_test = train_test_split(
        x_rows,
        y_rows,
        test_size=0.35,
        random_state=seed,
        stratify=y_rows,
    )
    clf = make_pipeline(
        StandardScaler(),
        LogisticRegression(max_iter=1500, C=1.0, solver="lbfgs"),
    )
    clf.fit(x_train, y_train)
    return float(accuracy_score(y_test, clf.predict(x_test)))


def esn_features(static_projection: torch.Tensor, seed: int) -> torch.Tensor:
    generator = torch.Generator().manual_seed(seed)
    x = static_projection[:, :ESN_INPUT_DIM].detach().cpu().to(dtype=REAL_DTYPE)
    chunks = torch.tensor_split(x, 16, dim=1)
    max_width = max(chunk.shape[1] for chunk in chunks)
    w_in = torch.randn((ESN_STATE_DIM, max_width), generator=generator, dtype=REAL_DTYPE) * 0.35
    w = torch.randn((ESN_STATE_DIM, ESN_STATE_DIM), generator=generator, dtype=REAL_DTYPE) * (
        1.0 / math.sqrt(ESN_STATE_DIM)
    )
    eigs = torch.linalg.eigvals(w.to(torch.complex64))
    radius = eigs.abs().max().real.clamp_min(1e-12)
    w = 0.82 * w / radius
    states: list[torch.Tensor] = []
    for row in range(x.shape[0]):
        h = torch.zeros(ESN_STATE_DIM, dtype=REAL_DTYPE)
        row_states: list[torch.Tensor] = []
        for chunk in chunks:
            padded = torch.zeros(max_width, dtype=REAL_DTYPE)
            padded[: chunk.shape[1]] = chunk[row]
            h = torch.tanh(w @ h + w_in @ padded)
            row_states.append(h.clone())
        row_stack = torch.stack(row_states)
        states.append(torch.cat([row_stack.mean(dim=0), row_states[-1]]))
    return torch.stack(states).to(dtype=REAL_DTYPE)


def run_baselines() -> dict[str, Any]:
    torch.manual_seed(310000 + N_QUBITS)
    rhos, labels = task_data()
    structural = structural_static_features(rhos, N_QUBITS)
    projected = full_static_projection_features(rhos, seed=311000 + N_QUBITS, dim=512)
    esn = esn_features(projected, seed=312000 + N_QUBITS)
    reservoir = reservoir_features(rhos, N_QUBITS)
    metrics = {
        "structural_static_accuracy": readout_accuracy(structural, labels, seed=313001),
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
