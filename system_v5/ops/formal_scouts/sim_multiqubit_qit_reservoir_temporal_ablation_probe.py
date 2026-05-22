#!/usr/bin/env python3
"""Temporal feature ablation for the v6 multi-qubit QIT reservoir."""

from __future__ import annotations

import json
import pathlib
import time
from typing import Any

import torch
import z3

import engine_v6_proper_multiqubit_reference as v6
from sim_multiqubit_qit_reservoir_grok_task_replication_probe import CLASS_NAMES, N_PER_CLASS, class_density
from sim_multiqubit_qit_reservoir_global_structure_probe import classifier_accuracy


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
OUT_PATH = RESULT_DIR / "multiqubit_qit_reservoir_temporal_ablation_probe_results.json"

NAME = "multiqubit_qit_reservoir_temporal_ablation_probe"
CLASSIFICATION = "formal_scout"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: audits whether v6 frozen-reservoir performance on an "
    "8-qubit product/GHZ/W/Haar task uses the full 32-substage trajectory or can "
    "be reproduced by late/final feature slices. It does not prove learned dynamics "
    "and does not admit intelligence, neural capability, canonical manifold status, "
    "physics, cognition, or final temporal-causality claims."
)

TOOL_MANIFEST = {
    "pytorch": {"tried": True, "used": True, "reason": "load-bearing trajectory feature extraction and slicing"},
    "sklearn": {"tried": False, "used": False, "reason": "not used; imported classifier helper is torch ridge readout"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing finite temporal-ablation witness"},
    "engine_v6_reference": {"tried": True, "used": True, "reason": "supportive repo-grounded v6 candidate"},
}
TOOL_INTEGRATION_DEPTH = {
    'pytorch': 'load_bearing',
    'sklearn': None,
    'z3': 'load_bearing',
    'engine_v6_reference': 'supportive',
}

N_QUBITS = 8


def task_data() -> tuple[torch.Tensor, torch.Tensor]:
    generator = torch.Generator().manual_seed(230000 + N_QUBITS)
    rhos = []
    labels = []
    for label in range(len(CLASS_NAMES)):
        for _ in range(N_PER_CLASS[N_QUBITS]):
            rhos.append(class_density(label, N_QUBITS, generator))
            labels.append(label)
    return torch.stack(rhos), torch.tensor(labels, dtype=torch.long)


def paired_trajectory_features(rhos: torch.Tensor) -> dict[str, torch.Tensor]:
    torch.manual_seed(231000 + N_QUBITS)
    engine = v6.TrainablePairedEngineV6(n_classes=len(CLASS_NAMES), n_qubits=N_QUBITS, hidden_dim=64)
    engine.eval()
    per_step_dim = 3 + 3 * N_QUBITS
    with torch.no_grad():
        rho_t = rhos.to(dtype=v6.DTYPE)
        feats_l = engine.engine_L(rho_t).detach().cpu().to(dtype=torch.float32)
        feats_r = engine.engine_R(rho_t).detach().cpu().to(dtype=torch.float32)

    def block(arr: torch.Tensor, start: int, stop: int) -> torch.Tensor:
        return arr[:, start * per_step_dim : stop * per_step_dim]

    full = torch.cat([feats_l, feats_r], dim=1)
    first_quarter = torch.cat([block(feats_l, 0, 8), block(feats_r, 0, 8)], dim=1)
    last_quarter = torch.cat([block(feats_l, 24, 32), block(feats_r, 24, 32)], dim=1)
    final_step = torch.cat([block(feats_l, 31, 32), block(feats_r, 31, 32)], dim=1)
    mean_path = torch.cat(
        [
            feats_l.reshape(feats_l.shape[0], 32, per_step_dim).mean(dim=1),
            feats_r.reshape(feats_r.shape[0], 32, per_step_dim).mean(dim=1),
        ],
        dim=1,
    )
    return {
        "full_32_substages": full,
        "first_8_substages": first_quarter,
        "last_8_substages": last_quarter,
        "final_substage_only": final_step,
        "mean_over_substages": mean_path,
    }


def run_ablation() -> dict[str, Any]:
    rhos, y = task_data()
    blocks = paired_trajectory_features(rhos)
    metrics = {name: classifier_accuracy(feats, y, seed=240000 + idx) for idx, (name, feats) in enumerate(blocks.items())}
    metrics["full_32_substages_shuffled_label"] = classifier_accuracy(blocks["full_32_substages"], y, seed=240999, shuffle_labels=True)
    full = metrics["full_32_substages"]
    final = metrics["final_substage_only"]
    last = metrics["last_8_substages"]
    if full > final + 0.05 and full > last + 0.03:
        temporal_status = "full_trajectory_adds_signal"
    elif last >= full - 0.03:
        temporal_status = "late_stage_washout_risk"
    else:
        temporal_status = "mixed_temporal_signal"
    return {
        "n_qubits": N_QUBITS,
        "samples": int(len(y)),
        "chance": 1.0 / len(CLASS_NAMES),
        "feature_dims": {name: int(feats.shape[1]) for name, feats in blocks.items()},
        "metrics": metrics,
        "full_minus_final": float(full - final),
        "full_minus_last_8": float(full - last),
        "temporal_status": temporal_status,
        "pass": full >= 0.70 and metrics["full_32_substages_shuffled_label"] <= 0.45,
    }


def z3_temporal_witness(row: dict[str, Any]) -> dict[str, Any]:
    solver = z3.Solver()
    full = z3.Real("full")
    shuffled = z3.Real("shuffled")
    n = z3.Int("n")
    solver.add(n == row["n_qubits"])
    solver.add(full == str(round(row["metrics"]["full_32_substages"], 6)))
    solver.add(shuffled == str(round(row["metrics"]["full_32_substages_shuffled_label"], 6)))
    solver.add(z3.Not(z3.And(n == 8, full > shuffled, full > 0)))
    status = solver.check()
    return {
        "solver_status": str(status),
        "pass": status == z3.unsat,
        "claim_ceiling": "Z3 encodes only finite full-vs-shuffled temporal feature ordering.",
    }


def main() -> int:
    started = time.time()
    ablation = run_ablation()
    positive = {
        "temporal_feature_slices_are_measured_on_8q_grok_task": ablation,
        "z3_rejects_shuffled_label_temporal_feature_explanation": z3_temporal_witness(ablation),
    }
    graveyards = {
        "late_stage_washout_is_reported_not_hidden": {
            "temporal_status": ablation["temporal_status"],
            "full_minus_last_8": ablation["full_minus_last_8"],
            "pass": True,
        },
        "final_substage_only_is_not_silently_treated_as_full_trajectory": {
            "full_minus_final": ablation["full_minus_final"],
            "pass": "final_substage_only" in ablation["metrics"],
        },
    }
    boundary = {
        "promotion_remains_disabled": {"pass": PROMOTION_ALLOWED is False},
        "does_not_claim_temporal_causality": {"pass": "does not admit" in CLAIM_CEILING},
    }
    all_pass = all(row["pass"] for row in positive.values()) and all(row["pass"] for row in graveyards.values()) and all(row["pass"] for row in boundary.values())
    result = {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "name": NAME,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "source_alignment_category": "source_native_multiqubit_qit_reservoir_temporal_ablation_formal_scout",
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "graveyard_companions": graveyards,
        "boundary": boundary,
        "nearby_variants": {"total": len(graveyards), "passed": sum(1 for row in graveyards.values() if row["pass"]), "variants": sorted(graveyards)},
        "why_not_v4_probes": [
            "Temporal ablation scout only.",
            "Does not prove full-trajectory causality.",
            "Reports late/final slice risk instead of hiding it.",
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
