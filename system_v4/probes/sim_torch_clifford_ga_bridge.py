#!/usr/bin/env python3
"""
sim_torch_clifford_ga_bridge.py
===============================

Torch <-> Clifford geometric-algebra bridge probe.

This is a classical-to-nonclassical style bridge:
  - torch optimizes a single-plane rotor fit in a differentiable way
  - clifford provides the geometric-algebra rotor sandwich witness
  - the positive case fits the same GA plane, the negative case does not
  - the boundary case is the identity rotor
"""

from __future__ import annotations

import json
import math
import os

import numpy as np
import torch
os.environ.setdefault("NUMBA_CACHE_DIR", "/tmp/codex-numba")
from clifford import Cl

classification = "classical_baseline"
divergence_log = (
    "Bridge probe: torch fits a classical rotation parameter while clifford "
    "witnesses the corresponding geometric-algebra rotor action; this is a "
    "bridge test, not a theorem."
)

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing autograd and optimization for fitting a rotor angle against the GA witness",
    },
    "clifford": {
        "tried": True,
        "used": True,
        "reason": "load-bearing geometric-algebra rotor sandwich witness for the same rotation",
    },
    "numpy": {
        "tried": True,
        "used": True,
        "reason": "supporting numeric conversion and result serialization",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "clifford": "load_bearing",
    "numpy": "supportive",
}

RESULTS_PATH = os.path.join(
    os.path.dirname(__file__),
    "a2_state",
    "sim_results",
    "sim_torch_clifford_ga_bridge_results.json",
)

LAYOUT, BLADES = Cl(3)
E1 = BLADES["e1"]
E2 = BLADES["e2"]
E3 = BLADES["e3"]


def plane_bivector(plane: str):
    if plane == "xy":
        return E1 * E2
    if plane == "yz":
        return E2 * E3
    if plane == "zx":
        return E3 * E1
    raise ValueError(f"unknown plane: {plane}")


def clifford_rotor_matrix(theta: float, plane: str) -> np.ndarray:
    bivector = plane_bivector(plane)
    rotor = math.cos(theta / 2.0) - math.sin(theta / 2.0) * bivector
    transformed = []
    for basis_vec in (E1, E2, E3):
        image = rotor * basis_vec * ~rotor
        transformed.append([
            float((image | E1).value[0]),
            float((image | E2).value[0]),
            float((image | E3).value[0]),
        ])
    return np.array(transformed, dtype=np.float64).T


def torch_rotor_matrix(theta: torch.Tensor, plane: str) -> torch.Tensor:
    c = torch.cos(theta)
    s = torch.sin(theta)
    z = torch.zeros((), dtype=torch.float64)
    o = torch.ones((), dtype=torch.float64)

    if plane == "xy":
        rows = [
            torch.stack([c, -s, z]),
            torch.stack([s, c, z]),
            torch.stack([z, z, o]),
        ]
    elif plane == "yz":
        rows = [
            torch.stack([o, z, z]),
            torch.stack([z, c, -s]),
            torch.stack([z, s, c]),
        ]
    elif plane == "zx":
        rows = [
            torch.stack([c, z, s]),
            torch.stack([z, o, z]),
            torch.stack([-s, z, c]),
        ]
    else:
        raise ValueError(f"unknown plane: {plane}")

    return torch.stack(rows)


def fit_rotation(target_matrix: np.ndarray, plane: str, theta0: float) -> dict:
    target = torch.tensor(target_matrix, dtype=torch.float64)
    theta = torch.nn.Parameter(torch.tensor(theta0, dtype=torch.float64))
    optimizer = torch.optim.LBFGS(
        [theta],
        lr=1.0,
        max_iter=80,
        tolerance_grad=1e-14,
        tolerance_change=1e-14,
        line_search_fn="strong_wolfe",
    )
    history = []

    def closure():
        optimizer.zero_grad()
        pred = torch_rotor_matrix(theta, plane)
        loss = torch.sum((pred - target) ** 2)
        loss.backward()
        history.append(float(loss.detach()))
        return loss

    optimizer.step(closure)

    with torch.no_grad():
        pred = torch_rotor_matrix(theta, plane)
        loss = torch.sum((pred - target) ** 2).item()
        pred_np = pred.cpu().numpy()
        clifford_np = clifford_rotor_matrix(float(theta.item()), plane)
        gap = float(np.max(np.abs(pred_np - clifford_np)))

    return {
        "plane": plane,
        "theta0": float(theta0),
        "theta_fit": float(theta.item()),
        "loss": float(loss),
        "clifford_gap": gap,
        "loss_history_tail": [float(x) for x in history[-5:]],
        "pass": bool(loss < 1e-12 and gap < 1e-12),
    }


def run_positive_tests() -> dict:
    theta_target = 1.0471975511965976
    target = clifford_rotor_matrix(theta_target, "xy")
    fit = fit_rotation(target, "xy", theta0=0.35)
    gap_to_target = float(np.max(np.abs(torch_rotor_matrix(torch.tensor(fit["theta_fit"], dtype=torch.float64), "xy").detach().cpu().numpy() - target)))
    return {
        "target_plane": "xy",
        "target_theta": theta_target,
        "fit": fit,
        "target_gap": gap_to_target,
        "pass": bool(fit["pass"]),
    }


def run_negative_tests() -> dict:
    theta_target = 1.0471975511965976
    target = clifford_rotor_matrix(theta_target, "yz")
    fit = fit_rotation(target, "xy", theta0=0.35)
    return {
        "target_plane": "yz",
        "target_theta": theta_target,
        "fit": fit,
        "pass": bool(fit["loss"] > 1e-2),
    }


def run_boundary_tests() -> dict:
    target = clifford_rotor_matrix(0.0, "zx")
    fit = fit_rotation(target, "zx", theta0=0.0)
    return {
        "target_plane": "zx",
        "fit": fit,
        "pass": bool(fit["pass"]),
    }


def main() -> int:
    os.makedirs(os.path.dirname(RESULTS_PATH), exist_ok=True)

    positive = run_positive_tests()
    negative = run_negative_tests()
    boundary = run_boundary_tests()

    overall_pass = positive["pass"] and negative["pass"] and boundary["pass"]
    results = {
        "name": "sim_torch_clifford_ga_bridge",
        "timestamp": __import__("datetime").datetime.now(__import__("datetime").UTC).isoformat(),
        "classification": classification,
        "original_classification": "canonical",
        "downgrade_reason": "canonical_failed_checks_2026-05-01",
        "divergence_log": divergence_log,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "overall_pass": overall_pass,
    }

    with open(RESULTS_PATH, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, default=str)

    print(f"PASS={overall_pass}")
    print(f"positive_loss={positive['fit']['loss']:.6e}")
    print(f"negative_loss={negative['fit']['loss']:.6e}")
    print(f"boundary_loss={boundary['fit']['loss']:.6e}")
    print(f"Results written to {RESULTS_PATH}")
    return 0 if overall_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
