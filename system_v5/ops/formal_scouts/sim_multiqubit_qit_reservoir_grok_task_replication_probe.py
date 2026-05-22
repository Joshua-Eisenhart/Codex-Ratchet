#!/usr/bin/env python3
"""Grok-task replication plus baseline controls for the v6 multi-qubit reservoir."""

from __future__ import annotations

import json
import math
import pathlib
import time
from typing import Any

import torch
import z3

import engine_v6_proper_multiqubit_reference as v6
from sim_multiqubit_qit_reservoir_global_structure_probe import (
    CLASS_NAMES as _OLD_CLASS_NAMES,
    DTYPE,
    classifier_accuracy,
    full_static_projection_features,
    kron_all,
    local_bloch_features,
    partial_trace_torch,
    random_unitary_2,
    reservoir_features,
    structural_static_features,
    entropy_torch,
)


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
OUT_PATH = RESULT_DIR / "multiqubit_qit_reservoir_grok_task_replication_probe_results.json"

NAME = "multiqubit_qit_reservoir_grok_task_replication_probe"
CLASSIFICATION = "formal_scout"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: translates the external Grok v6 product/GHZ/W/Haar "
    "multi-qubit task into a repo-grounded benchmark with local, structural-static, "
    "full-static, frozen-reservoir, and shuffled-label controls. It does not prove "
    "learned dynamics and does not admit intelligence, neural capability, canonical "
    "manifold status, physics, cognition, or uniqueness over static global features."
)

TOOL_MANIFEST = {
    "pytorch": {"tried": True, "used": True, "reason": "load-bearing task density construction and v6 frozen reservoir feature extraction"},
    "sklearn": {"tried": False, "used": False, "reason": "not used; imported classifier helper is torch ridge readout"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing finite metric-ordering witness"},
    "engine_v6_reference": {"tried": True, "used": True, "reason": "supportive repo-grounded v6 candidate"},
}
TOOL_INTEGRATION_DEPTH = {
    'pytorch': 'load_bearing',
    'sklearn': None,
    'z3': 'load_bearing',
    'engine_v6_reference': 'supportive',
}

CLASS_NAMES = ["product", "ghz", "w", "haar"]
N_PER_CLASS = {4: 24, 8: 12}


def _complex_normal(shape: tuple[int, ...], generator: torch.Generator) -> torch.Tensor:
    real = torch.randn(shape, generator=generator, dtype=torch.float32)
    imag = torch.randn(shape, generator=generator, dtype=torch.float32)
    return torch.complex(real, imag).to(DTYPE)


def _pure_density(psi: torch.Tensor) -> torch.Tensor:
    psi = psi.to(DTYPE)
    return torch.outer(psi, psi.conj())


def _random_product_density(n_qubits: int, generator: torch.Generator) -> torch.Tensor:
    states = []
    for _ in range(n_qubits):
        psi = _complex_normal((2,), generator)
        states.append(psi / torch.linalg.vector_norm(psi))
    psi_all = kron_all(states)
    return _pure_density(psi_all)


def ghz_density(n_qubits: int, phase: float) -> torch.Tensor:
    d = 2**n_qubits
    psi = torch.zeros(d, dtype=DTYPE)
    psi[0] = 1.0 / math.sqrt(2)
    psi[-1] = complex(math.cos(phase), math.sin(phase)) / math.sqrt(2)
    return _pure_density(psi)


def _w_density(n_qubits: int) -> torch.Tensor:
    d = 2**n_qubits
    psi = torch.zeros(d, dtype=DTYPE)
    amp = 1.0 / math.sqrt(float(n_qubits))
    for q in range(n_qubits):
        psi[1 << q] = amp
    return _pure_density(psi)


def _random_pure_density(n_qubits: int, generator: torch.Generator) -> torch.Tensor:
    psi = _complex_normal((2**n_qubits,), generator)
    return _pure_density(psi / torch.linalg.vector_norm(psi))


def locally_scramble(rho: torch.Tensor, n_qubits: int, generator: torch.Generator) -> torch.Tensor:
    u = kron_all([random_unitary_2(generator) for _ in range(n_qubits)])
    out = u @ rho @ u.conj().T
    out = (out + out.conj().T) / 2
    return (out / torch.trace(out).real).to(DTYPE)


def class_density(label: int, n_qubits: int, generator: torch.Generator) -> torch.Tensor:
    if label == 0:
        rho = _random_product_density(n_qubits, generator)
    elif label == 1:
        phase = float((2 * math.pi * torch.rand((), generator=generator, dtype=torch.float32)).item())
        rho = ghz_density(n_qubits, phase)
    elif label == 2:
        rho = _w_density(n_qubits)
    elif label == 3:
        rho = _random_pure_density(n_qubits, generator)
    else:
        raise ValueError(label)
    return locally_scramble(rho.to(DTYPE), n_qubits, generator)


def local_spectrum_features(rhos: torch.Tensor, n_qubits: int) -> torch.Tensor:
    rows = []
    for rho in rhos:
        feat = []
        for q in range(n_qubits):
            red = partial_trace_torch(rho, n_qubits, [q])
            vals = torch.sort(torch.linalg.eigvalsh((red + red.conj().T) / 2).real).values
            feat.extend([float(vals[0].item()), float(vals[1].item()), entropy_torch(red)])
        rows.append(torch.tensor(feat, dtype=torch.float32))
    return torch.stack(rows)


def run_for_n(n_qubits: int) -> dict[str, Any]:
    generator = torch.Generator().manual_seed(160000 + n_qubits)
    rhos = []
    labels = []
    for label in range(len(CLASS_NAMES)):
        for _ in range(N_PER_CLASS[n_qubits]):
            rhos.append(class_density(label, n_qubits, generator))
            labels.append(label)
    rhos_arr = torch.stack(rhos)
    y = torch.tensor(labels, dtype=torch.long)
    local_bloch = local_bloch_features(rhos_arr, n_qubits)
    local_spectrum = local_spectrum_features(rhos_arr, n_qubits)
    structural = structural_static_features(rhos_arr, n_qubits)
    full_projection = full_static_projection_features(rhos_arr, seed=170000 + n_qubits, dim=512)
    reservoir = reservoir_features(rhos_arr, n_qubits)
    metrics = {
        "local_bloch_accuracy": classifier_accuracy(local_bloch, y, seed=11 + n_qubits),
        "local_spectrum_accuracy": classifier_accuracy(local_spectrum, y, seed=12 + n_qubits),
        "structural_static_accuracy": classifier_accuracy(structural, y, seed=13 + n_qubits),
        "full_static_random_projection_accuracy": classifier_accuracy(full_projection, y, seed=14 + n_qubits),
        "frozen_reservoir_accuracy": classifier_accuracy(reservoir, y, seed=15 + n_qubits),
        "frozen_reservoir_shuffled_label_accuracy": classifier_accuracy(reservoir, y, seed=16 + n_qubits, shuffle_labels=True),
    }
    return {
        "n_qubits": n_qubits,
        "samples": int(len(y)),
        "chance": 1.0 / len(CLASS_NAMES),
        "feature_dims": {
            "local_bloch": int(local_bloch.shape[1]),
            "local_spectrum": int(local_spectrum.shape[1]),
            "structural_static": int(structural.shape[1]),
            "full_static_random_projection": int(full_projection.shape[1]),
            "frozen_reservoir": int(reservoir.shape[1]),
        },
        "metrics": metrics,
        "grok_local_blind_reading_supported": metrics["local_spectrum_accuracy"] <= 0.40,
        "pass": metrics["frozen_reservoir_accuracy"] >= 0.70
        and metrics["frozen_reservoir_shuffled_label_accuracy"] <= 0.45
        and metrics["frozen_reservoir_accuracy"] > metrics["local_bloch_accuracy"],
    }


def z3_grok_task_witness(rows: list[dict[str, Any]]) -> dict[str, Any]:
    row8 = next(row for row in rows if row["n_qubits"] == 8)
    solver = z3.Solver()
    n8 = z3.Int("n8")
    res = z3.Real("reservoir")
    bloch = z3.Real("bloch")
    shuffle = z3.Real("shuffle")
    solver.add(n8 == 8)
    solver.add(res == str(round(row8["metrics"]["frozen_reservoir_accuracy"], 6)))
    solver.add(bloch == str(round(row8["metrics"]["local_bloch_accuracy"], 6)))
    solver.add(shuffle == str(round(row8["metrics"]["frozen_reservoir_shuffled_label_accuracy"], 6)))
    solver.add(z3.Not(z3.And(n8 == 8, res > bloch, shuffle < res)))
    status = solver.check()
    return {
        "solver_status": str(status),
        "pass": status == z3.unsat,
        "claim_ceiling": "Z3 encodes only N=8 finite reservoir/local/shuffle ordering for the Grok task.",
    }


def main() -> int:
    started = time.time()
    rows = [run_for_n(4), run_for_n(8)]
    row8 = next(row for row in rows if row["n_qubits"] == 8)
    positive = {
        "grok_task_frozen_reservoir_beats_local_bloch_at_8q": {
            "class_names": CLASS_NAMES,
            "rows": rows,
            "pass": row8["pass"],
        },
        "z3_rejects_grok_task_local_or_shuffle_explanation": z3_grok_task_witness(rows),
    }
    graveyards = {
        "grok_local_blind_reading_is_audited_not_assumed": {
            "local_spectrum_accuracy_by_n": {str(row["n_qubits"]): row["metrics"]["local_spectrum_accuracy"] for row in rows},
            "supported_by_current_cells": {str(row["n_qubits"]): row["grok_local_blind_reading_supported"] for row in rows},
            "pass": all(row["grok_local_blind_reading_supported"] for row in rows),
            "reason": (
                "This translated task is not local-blind when local-spectrum features solve or match it; "
                "that leakage blocks treating reservoir parity as a Grok-task replication success."
            ),
        },
        "static_global_baselines_are_reported_not_hidden": {
            "structural_static_accuracy_by_n": {str(row["n_qubits"]): row["metrics"]["structural_static_accuracy"] for row in rows},
            "full_static_random_projection_accuracy_by_n": {str(row["n_qubits"]): row["metrics"]["full_static_random_projection_accuracy"] for row in rows},
            "pass": True,
        },
        "shuffled_label_control_stays_near_chance": {
            "shuffled_accuracy_by_n": {str(row["n_qubits"]): row["metrics"]["frozen_reservoir_shuffled_label_accuracy"] for row in rows},
            "pass": row8["metrics"]["frozen_reservoir_shuffled_label_accuracy"] <= 0.45,
        },
    }
    boundary = {
        "grok_result_is_translated_not_promoted": {"pass": PROMOTION_ALLOWED is False},
        "old_class_names_not_reused": {"old_classes": list(_OLD_CLASS_NAMES), "new_classes": CLASS_NAMES, "pass": list(_OLD_CLASS_NAMES) != CLASS_NAMES},
    }
    all_pass = all(row["pass"] for row in positive.values()) and all(row["pass"] for row in graveyards.values()) and all(row["pass"] for row in boundary.values())
    checks = {**positive, **graveyards, **boundary}
    result = {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "name": NAME,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "source_alignment_category": "source_native_multiqubit_qit_reservoir_grok_task_translation_formal_scout",
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "graveyard_companions": graveyards,
        "boundary": boundary,
        "nearby_variants": {"total": len(graveyards), "passed": sum(1 for row in graveyards.values() if row["pass"]), "variants": sorted(graveyards)},
        "why_not_v4_probes": [
            "Grok-task translation and audit only.",
            "Does not prove learned dynamics.",
            "Does not hide static global baselines or local-spectrum leakage.",
        ],
        "blockers": [key for key, row in checks.items() if row.get("pass") is not True],
        "elapsed_seconds": time.time() - started,
        "all_pass": all_pass,
    }
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print(f"RESULT {NAME}: all_pass={all_pass} -> {OUT_PATH}")
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
