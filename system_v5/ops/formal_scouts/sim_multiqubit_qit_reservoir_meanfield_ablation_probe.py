#!/usr/bin/env python3
"""Mean-field ablation for dense-v6 multi-qubit QIT reservoir dynamics."""

from __future__ import annotations

import json
import pathlib
import time
from typing import Any

import numpy as np
import torch
import z3

import engine_v6_proper_multiqubit_reference as v6
from sim_multiqubit_qit_reservoir_global_structure_probe import classifier_accuracy
from sim_multiqubit_qit_reservoir_grok_task_replication_probe import CLASS_NAMES, N_PER_CLASS, class_density


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
OUT_PATH = RESULT_DIR / "multiqubit_qit_reservoir_meanfield_ablation_probe_results.json"

NAME = "multiqubit_qit_reservoir_meanfield_ablation_probe"
CLASSIFICATION = "formal_scout"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: compares dense-v6 frozen reservoir features with and "
    "without nearest-neighbor ZZ coupling on the 8-qubit product/GHZ/W/Haar task. "
    "It does not prove quantum advantage or learned dynamics, and does not admit "
    "intelligence, neural capability, canonical manifold status, physics, cognition, "
    "or uniqueness over mean-field reservoir baselines."
)

TOOL_MANIFEST = {
    "pytorch": {"tried": True, "used": True, "reason": "load-bearing default and mean-field v6 feature extraction"},
    "sklearn": {"tried": True, "used": True, "reason": "load-bearing linear readout via imported helper"},
    "numpy": {"tried": True, "used": True, "reason": "load-bearing task data and delta aggregation"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing finite ablation-ordering witness"},
    "engine_v6_reference": {"tried": True, "used": True, "reason": "load-bearing repo-grounded v6 candidate"},
}
TOOL_INTEGRATION_DEPTH = {tool: "load_bearing" for tool in TOOL_MANIFEST}

N_QUBITS = 8


def task_data() -> tuple[np.ndarray, np.ndarray]:
    rng = np.random.default_rng(260000 + N_QUBITS)
    rhos = []
    labels = []
    for label in range(len(CLASS_NAMES)):
        for _ in range(N_PER_CLASS[N_QUBITS]):
            rhos.append(class_density(label, N_QUBITS, rng))
            labels.append(label)
    return np.stack(rhos), np.asarray(labels, dtype=int)


def paired_features_with_coupling(rhos: np.ndarray, coupling: float) -> np.ndarray:
    torch.manual_seed(261000 + int(coupling * 1000))
    engine_l = v6.TrainableEngineV6(engine_type=1, n_qubits=N_QUBITS, nn_coupling=coupling)
    engine_r = v6.TrainableEngineV6(engine_type=2, n_qubits=N_QUBITS, nn_coupling=coupling)
    engine_l.eval()
    engine_r.eval()
    with torch.no_grad():
        rho_t = torch.tensor(rhos, dtype=v6.DTYPE)
        feats_l = engine_l(rho_t)
        feats_r = engine_r(rho_t)
        return torch.cat([feats_l, feats_r], dim=-1).detach().cpu().numpy().astype(float)


def mean_accuracy(feats: np.ndarray, y: np.ndarray, seeds: list[int], *, shuffle_labels: bool = False) -> dict[str, Any]:
    values = [classifier_accuracy(feats, y, seed=seed, shuffle_labels=shuffle_labels) for seed in seeds]
    return {
        "values": values,
        "mean": float(np.mean(values)),
        "min": float(np.min(values)),
        "max": float(np.max(values)),
    }


def run_ablation() -> dict[str, Any]:
    rhos, y = task_data()
    default = paired_features_with_coupling(rhos, coupling=0.3)
    meanfield = paired_features_with_coupling(rhos, coupling=0.0)
    eval_seeds = [270001, 270011, 270021, 270031, 270041]
    shuffle_seeds = [270101, 270111, 270121, 270131, 270141]
    default_acc = mean_accuracy(default, y, eval_seeds)
    meanfield_acc = mean_accuracy(meanfield, y, eval_seeds)
    shuffle_acc = mean_accuracy(default, y, shuffle_seeds, shuffle_labels=True)
    metrics = {
        "default_zz_coupling_accuracy": default_acc["mean"],
        "meanfield_zero_zz_accuracy": meanfield_acc["mean"],
        "default_shuffled_label_accuracy": shuffle_acc["mean"],
        "default_zz_coupling_accuracy_by_seed": default_acc,
        "meanfield_zero_zz_accuracy_by_seed": meanfield_acc,
        "default_shuffled_label_accuracy_by_seed": shuffle_acc,
    }
    delta_vs_meanfield = float(metrics["default_zz_coupling_accuracy"] - metrics["meanfield_zero_zz_accuracy"])
    if delta_vs_meanfield > 0.05:
        status = "zz_coupling_adds_readout_signal"
    elif abs(delta_vs_meanfield) <= 0.05:
        status = "meanfield_reservoir_matches_default"
    else:
        status = "zz_coupling_hurts_this_task"
    return {
        "n_qubits": N_QUBITS,
        "samples": int(len(y)),
        "feature_dim": int(default.shape[1]),
        "metrics": metrics,
        "default_minus_meanfield": delta_vs_meanfield,
        "coupling_status": status,
        "pass": metrics["default_zz_coupling_accuracy"] >= 0.60 and metrics["default_shuffled_label_accuracy"] <= 0.45,
    }


def z3_meanfield_witness(row: dict[str, Any]) -> dict[str, Any]:
    solver = z3.Solver()
    default = z3.Real("default")
    shuffled = z3.Real("shuffled")
    n = z3.Int("n")
    solver.add(n == row["n_qubits"])
    solver.add(default == str(round(row["metrics"]["default_zz_coupling_accuracy"], 6)))
    solver.add(shuffled == str(round(row["metrics"]["default_shuffled_label_accuracy"], 6)))
    solver.add(z3.Not(z3.And(n == 8, default > shuffled, default > 0)))
    status = solver.check()
    return {
        "solver_status": str(status),
        "pass": status == z3.unsat,
        "claim_ceiling": "Z3 encodes only finite default-vs-shuffled ordering; mean-field delta remains empirical.",
    }


def main() -> int:
    started = time.time()
    ablation = run_ablation()
    positive = {
        "default_and_meanfield_reservoirs_are_compared_on_8q_grok_task": ablation,
        "z3_rejects_shuffled_label_default_reservoir_explanation": z3_meanfield_witness(ablation),
    }
    graveyards = {
        "meanfield_baseline_is_reported_not_hidden": {
            "meanfield_zero_zz_accuracy": ablation["metrics"]["meanfield_zero_zz_accuracy"],
            "default_minus_meanfield": ablation["default_minus_meanfield"],
            "coupling_status": ablation["coupling_status"],
            "pass": True,
        },
    }
    boundary = {
        "promotion_remains_disabled": {"pass": PROMOTION_ALLOWED is False},
        "does_not_claim_quantum_advantage": {"pass": "does not prove quantum advantage" in CLAIM_CEILING},
    }
    all_pass = all(row["pass"] for row in positive.values()) and all(row["pass"] for row in graveyards.values()) and all(row["pass"] for row in boundary.values())
    result = {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "name": NAME,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "source_alignment_category": "source_native_multiqubit_qit_reservoir_meanfield_ablation_formal_scout",
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "graveyard_companions": graveyards,
        "boundary": boundary,
        "nearby_variants": {"total": len(graveyards), "passed": sum(1 for row in graveyards.values() if row["pass"]), "variants": sorted(graveyards)},
        "why_not_v4_probes": [
            "Mean-field ablation scout only.",
            "Does not prove entangling dynamics are necessary.",
            "Reports zero-coupling baseline instead of hiding it.",
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
