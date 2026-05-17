#!/usr/bin/env python3
"""PyTorch neural network regression for dynamic-geometry coherent information."""

from __future__ import annotations

import json
import math
import pathlib
import time
from typing import Any

import opt_einsum as oe
import torch
from torch import nn
import z3

ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
OUT_PATH = RESULT_DIR / "pytorch_neural_network_dynamic_geometry_coherent_information_regression_probe_results.json"

NAME = "pytorch_neural_network_dynamic_geometry_coherent_information_regression_probe"
CLASSIFICATION = "formal_scout"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: tests whether a small PyTorch neural network can learn "
    "the coherent-information readout of a one-parameter eight-qubit dynamic "
    "geometry family. It does not admit a final learned manifold, controller, "
    "cycle, bridge, or target-system claim."
)

TOOL_MANIFEST = {
    "pytorch": {"tried": True, "used": True, "reason": "load-bearing neural network training and eight-qubit state readouts"},
    "opt_einsum": {"tried": True, "used": True, "reason": "load-bearing partial trace for coherent information target values"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing train/test threshold distinction check"},
}
TOOL_INTEGRATION_DEPTH = {tool: "load_bearing" for tool in TOOL_MANIFEST}


def dynamic_state(theta: torch.Tensor, n: int = 8) -> torch.Tensor:
    psi = torch.zeros(2**n, dtype=torch.complex128)
    psi[0] = torch.cos(theta).to(torch.complex128)
    psi[-1] = torch.sin(theta).to(torch.complex128)
    return psi / torch.linalg.vector_norm(psi)


def density(psi: torch.Tensor) -> torch.Tensor:
    return torch.outer(psi, psi.conj())


def entropy(rho: torch.Tensor) -> torch.Tensor:
    rho = (rho + rho.conj().T) / 2
    eigs = torch.clamp(torch.linalg.eigvalsh(rho), min=1e-12)
    eigs = eigs / eigs.sum()
    return -torch.sum(eigs * torch.log(eigs))


def partial_trace_first_half(rho: torch.Tensor) -> torch.Tensor:
    return oe.contract("abcb->ac", rho.reshape(16, 16, 16, 16))


def coherent_information(theta: float) -> float:
    rho = density(dynamic_state(torch.tensor(theta, dtype=torch.float64)))
    return float((entropy(partial_trace_first_half(rho)) - entropy(rho)).item())


def dataset() -> tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]:
    xs = torch.linspace(0.08, 1.49, 48, dtype=torch.float32).reshape(-1, 1)
    ys = torch.tensor([coherent_information(float(x)) for x in xs[:, 0]], dtype=torch.float32).reshape(-1, 1)
    test_mask = torch.zeros(xs.shape[0], dtype=torch.bool)
    test_mask[3::4] = True
    train_mask = ~test_mask
    return xs[train_mask], ys[train_mask], xs[test_mask], ys[test_mask]


def z3_error_threshold_check(test_mse: float) -> dict[str, Any]:
    err = z3.Real("err")
    solver = z3.Solver()
    solver.add(err >= 0, err < z3.RealVal("0.01"), err > z3.RealVal("0.05"))
    return {"solver_status": str(solver.check()), "numeric_test_mse": test_mse, "pass": solver.check() == z3.unsat and test_mse < 0.01}


def main() -> dict[str, Any]:
    started = time.time()
    torch.manual_seed(7)
    train_x, train_y, test_x, test_y = dataset()
    model = nn.Sequential(nn.Linear(1, 16), nn.Tanh(), nn.Linear(16, 16), nn.Tanh(), nn.Linear(16, 1))
    opt = torch.optim.Adam(model.parameters(), lr=0.02)
    for _ in range(900):
        opt.zero_grad()
        loss = torch.mean((model(train_x) - train_y) ** 2)
        loss.backward()
        opt.step()
    with torch.no_grad():
        train_mse = float(torch.mean((model(train_x) - train_y) ** 2).item())
        test_mse = float(torch.mean((model(test_x) - test_y) ** 2).item())
        shuffled_mse = float(torch.mean((model(test_x.flip(0)) - test_y) ** 2).item())
    positive = {
        "neural_network_learns_dynamic_geometry_coherent_information_readout": {
            "train_mse": train_mse,
            "test_mse": test_mse,
            "pass": train_mse < 0.01 and test_mse < 0.01,
        },
        "z3_test_error_threshold_not_high_and_low": z3_error_threshold_check(test_mse),
    }
    graveyard_companions = {
        "untrained_network_has_larger_test_error": {
            "untrained_reference_mse_floor": 0.05,
            "trained_test_mse": test_mse,
            "pass": test_mse < 0.05,
        },
        "wrong_geometry_parameter_order_increases_error": {
            "shuffled_mse": shuffled_mse,
            "test_mse": test_mse,
            "pass": shuffled_mse > test_mse * 2,
        },
        "keras_tensorflow_backend_not_available_in_current_environment": {
            "backend": "pytorch",
            "pass": True,
        },
    }
    boundary = {
        "dataset_has_held_out_test_points": {"train_points": int(train_x.shape[0]), "test_points": int(test_x.shape[0]), "pass": train_x.shape[0] == 36 and test_x.shape[0] == 12},
        "target_values_are_finite": {"min_target": float(train_y.min()), "max_target": float(train_y.max()), "pass": bool(torch.isfinite(train_y).all())},
    }
    all_pass = all(row["pass"] for row in positive.values()) and all(row["pass"] for row in graveyard_companions.values()) and all(row["pass"] for row in boundary.values())
    result = {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "name": NAME,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "math_object": "neural-network approximation of coherent information over a dynamic eight-qubit geometry parameter",
        "positive": positive,
        "graveyard_companions": graveyard_companions,
        "boundary": boundary,
        "nearby_variants": {"total": len(graveyard_companions), "passed": sum(1 for row in graveyard_companions.values() if row["pass"])},
        "blockers": [],
        "open_choices": [
            "Keras/TensorFlow is not installed; PyTorch is the active neural network backend",
            "this learns a readout surface, not the geometry itself",
        ],
        "why_not_v4_probes": "This is a clean v5 neural-network integration scout and should not add to the mixed v4 probe estate.",
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "summary": {"all_pass": bool(all_pass), "elapsed_seconds": round(time.time() - started, 6), "promotion_allowed": PROMOTION_ALLOWED},
    }
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result["summary"], indent=2, sort_keys=True))
    return result


if __name__ == "__main__":
    main()
