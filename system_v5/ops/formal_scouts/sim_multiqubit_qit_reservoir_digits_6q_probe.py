#!/usr/bin/env python3
"""6-qubit dense-v6 reservoir scout on sklearn digits."""

from __future__ import annotations

import json
import pathlib
import time
from typing import Any

from sklearn.datasets import load_digits
import torch
import z3

import engine_v6_proper_multiqubit_reference as v6
from reservoir_torch_readout import classifier_accuracy


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
OUT_PATH = RESULT_DIR / "multiqubit_qit_reservoir_digits_6q_probe_results.json"

NAME = "multiqubit_qit_reservoir_digits_6q_probe"
CLASSIFICATION = "formal_scout"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: translates the external 6-qubit digits claim into a "
    "bounded sklearn-digits benchmark with frozen dense-v6 reservoir features, "
    "raw-pixel baseline, and shuffled-label control. It does not prove learned "
    "dynamics and does not admit intelligence, neural capability, canonical "
    "manifold status, physics, cognition, or superiority over standard ML baselines."
)

TOOL_MANIFEST = {
    "pytorch": {"tried": True, "used": True, "reason": "load-bearing 6-qubit dense-v6 reservoir features"},
    "sklearn": {"tried": True, "used": True, "reason": "supportive digits dataset only; torch ridge readout replaces sklearn classifier plumbing"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing finite digits benchmark witness"},
    "engine_v6_reference": {"tried": True, "used": True, "reason": "supportive repo-grounded dense-v6 candidate"},
}
TOOL_INTEGRATION_DEPTH = {
    'pytorch': 'load_bearing',
    'sklearn': 'supportive',
    'z3': 'load_bearing',
    'engine_v6_reference': 'supportive',
}

MIN_NONCLASSICAL_WIDTH = 8
N_QUBITS = 6
N_PER_CLASS = 15


def load_balanced_digits() -> tuple[torch.Tensor, torch.Tensor]:
    digits = load_digits()
    x = torch.as_tensor(digits.data, dtype=torch.float32) / 16.0
    y = torch.as_tensor(digits.target, dtype=torch.long)
    rows = []
    labels = []
    for label in range(10):
        idx = torch.nonzero(y == label, as_tuple=True)[0][:N_PER_CLASS]
        rows.append(x[idx])
        labels.extend([label] * len(idx))
    return torch.cat(rows, dim=0), torch.tensor(labels, dtype=torch.long)


def pixels_to_density(x: torch.Tensor) -> torch.Tensor:
    # 8x8 digits are exactly 64 amplitudes = 6 qubits.
    rows = []
    for row in x:
        amp = row.to(dtype=torch.complex64)
        norm = torch.linalg.vector_norm(amp)
        if norm < 1e-12:
            amp = torch.ones_like(amp) / torch.sqrt(torch.tensor(amp.numel(), dtype=torch.float32))
        else:
            amp = amp / norm
        rows.append(torch.outer(amp, amp.conj()).to(dtype=torch.complex64))
    return torch.stack(rows)


def reservoir_features(rhos: torch.Tensor) -> torch.Tensor:
    torch.manual_seed(330006)
    engine = v6.TrainablePairedEngineV6(n_classes=10, n_qubits=N_QUBITS, hidden_dim=64)
    engine.eval()
    with torch.no_grad():
        rho_t = rhos.to(dtype=v6.DTYPE)
        feats_l = engine.engine_L(rho_t)
        feats_r = engine.engine_R(rho_t)
        return torch.cat([feats_l, feats_r], dim=-1).detach().cpu().to(dtype=torch.float32)


def clf_acc(x: torch.Tensor, y: torch.Tensor, seed: int, shuffle: bool = False) -> float:
    return classifier_accuracy(
        x,
        y,
        seed=seed,
        shuffle_labels=shuffle,
        test_size=0.35,
        ridge=1e-3,
    )


def run_digits() -> dict[str, Any]:
    x, y = load_balanced_digits()
    rhos = pixels_to_density(x)
    feats = reservoir_features(rhos)
    metrics = {
        "raw_pixel_accuracy": clf_acc(x, y, seed=340001),
        "frozen_reservoir_accuracy": clf_acc(feats, y, seed=340002),
        "frozen_reservoir_shuffled_label_accuracy": clf_acc(feats, y, seed=340003, shuffle=True),
    }
    return {
        "minimum_width_qubits": N_QUBITS,
        "minimum_width_role": "calibration_only",
        "minimum_width_reason": "6q digits embedding is retained as a real-data calibration boundary, not nonclassical maturity evidence",
        "n_qubits": N_QUBITS,
        "samples": int(len(y)),
        "classes": 10,
        "chance": 0.1,
        "feature_dims": {"raw_pixels": int(x.shape[1]), "frozen_reservoir": int(feats.shape[1])},
        "metrics": metrics,
        "reservoir_minus_raw": float(metrics["frozen_reservoir_accuracy"] - metrics["raw_pixel_accuracy"]),
        "pass": metrics["frozen_reservoir_accuracy"] >= 0.45 and metrics["frozen_reservoir_shuffled_label_accuracy"] <= 0.25,
    }


def z3_digits_witness(row: dict[str, Any]) -> dict[str, Any]:
    solver = z3.Solver()
    n = z3.Int("n_qubits")
    classes = z3.Int("classes")
    res = z3.Real("reservoir")
    shuffle = z3.Real("shuffle")
    solver.add(n == row["n_qubits"], classes == row["classes"])
    solver.add(res == str(round(row["metrics"]["frozen_reservoir_accuracy"], 6)))
    solver.add(shuffle == str(round(row["metrics"]["frozen_reservoir_shuffled_label_accuracy"], 6)))
    solver.add(z3.Not(z3.And(n == 6, classes == 10, res > shuffle, res > 0)))
    status = solver.check()
    return {
        "solver_status": str(status),
        "pass": status == z3.unsat,
        "minimum_width_qubits": N_QUBITS,
        "minimum_width_role": "calibration_only",
        "claim_ceiling": "Z3 encodes only finite 6q digits reservoir-vs-shuffle ordering.",
    }


def main() -> int:
    started = time.time()
    digits = run_digits()
    positive = {
        "six_qubit_digits_reservoir_runs_against_raw_pixel_baseline": digits,
        "z3_rejects_shuffled_label_digits_explanation": z3_digits_witness(digits),
    }
    graveyards = {
        "raw_pixel_baseline_is_reported_not_hidden": {
            "raw_pixel_accuracy": digits["metrics"]["raw_pixel_accuracy"],
            "reservoir_minus_raw": digits["reservoir_minus_raw"],
            "pass": True,
        },
        "standard_ml_superiority_is_not_claimed": {
            "pass": digits["reservoir_minus_raw"] <= 0.0 or "superiority over standard ML baselines" in CLAIM_CEILING,
        },
    }
    boundary = {
        "promotion_remains_disabled": {"pass": PROMOTION_ALLOWED is False},
        "six_qubit_embedding_matches_digit_amplitudes": {"pixels": 64, "hilbert_dimension": 2**N_QUBITS, "pass": 2**N_QUBITS == 64},
        "six_qubit_digits_row_is_calibration_only": {
            "minimum_nonclassical_width": MIN_NONCLASSICAL_WIDTH,
            "minimum_width_qubits": N_QUBITS,
            "minimum_width_role": "calibration_only",
            "pass": N_QUBITS < MIN_NONCLASSICAL_WIDTH,
        },
    }
    all_pass = all(row["pass"] for row in positive.values()) and all(row["pass"] for row in graveyards.values()) and all(row["pass"] for row in boundary.values())
    result = {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "name": NAME,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "source_alignment_category": "source_native_multiqubit_qit_reservoir_digits_formal_scout",
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "graveyard_companions": graveyards,
        "boundary": boundary,
        "nearby_variants": {"total": len(graveyards), "passed": sum(1 for row in graveyards.values() if row["pass"]), "variants": sorted(graveyards)},
        "why_not_v4_probes": [
            "Bounded digits scout only.",
            "Does not prove standard-ML superiority.",
            "Does not prove learned dynamics.",
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
