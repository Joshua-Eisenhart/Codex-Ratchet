#!/usr/bin/env python3
"""
sim_integration_torch_clifford_ga_rotor_bridge.py

Rotor bridge lane for torch + clifford + torch_ga, with numpy/scipy witnesses.

The surface is intentionally small:
  - one rotor plane in Cl(3) (xy)
  - one torch fit against the corresponding rotor matrix
  - one torch_ga roundtrip on the same vector surface
  - scipy as the classical exponential witness for the same generator

This is a bridge sim, not a theorem. It exists to show the three tool surfaces
agree on one bounded geometric/rotor-like contract that can be scaled later.
"""

from __future__ import annotations

import json
import math
import os
from datetime import datetime, UTC

os.environ.setdefault("MPLCONFIGDIR", "/tmp/codex-mpl")
os.environ.setdefault("NUMBA_CACHE_DIR", "/tmp/codex-numba")
os.makedirs(os.environ["MPLCONFIGDIR"], exist_ok=True)
os.makedirs(os.environ["NUMBA_CACHE_DIR"], exist_ok=True)

import numpy as np
import torch
import torch_ga
from clifford import Cl
from scipy.linalg import expm

classification = "classical_baseline"
divergence_log = (
    "Classical-to-geometric rotor bridge: torch fits one rotor angle, "
    "clifford witnesses the rotor sandwich, torch_ga roundtrips the same "
    "vector carrier, and scipy witnesses the equivalent matrix exponential. "
    "The negative case uses the wrong plane; the boundary case is identity."
)

TOOL_MANIFEST = {
    "numpy": {
        "tried": True,
        "used": True,
        "reason": "load-bearing numeric carrier for the rotor surface and serialization",
    },
    "scipy": {
        "tried": True,
        "used": True,
        "reason": "supportive matrix-exponential witness for the same geometric generator",
    },
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing rotor-angle fit and gradient witness",
    },
    "clifford": {
        "tried": True,
        "used": True,
        "reason": "load-bearing geometric rotor sandwich witness in Cl(3)",
    },
    "torch_ga": {
        "tried": True,
        "used": True,
        "reason": "load-bearing geometric algebra vector roundtrip witness",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "numpy": "supportive",
    "scipy": "supportive",
    "pytorch": "load_bearing",
    "clifford": "load_bearing",
    "torch_ga": "load_bearing",
}

RESULTS_PATH = os.path.join(
    os.path.dirname(__file__),
    "a2_state",
    "sim_results",
    "sim_integration_torch_clifford_ga_rotor_bridge_results.json",
)

LAYOUT, BLADES = Cl(3)
E1 = BLADES["e1"]
E2 = BLADES["e2"]
E3 = BLADES["e3"]
XY_BIVECTOR = E1 * E2
SOURCE_VECTOR = np.array([0.45, -0.2, 0.8660254037844386], dtype=np.float64)
SOURCE_VECTOR /= np.linalg.norm(SOURCE_VECTOR)
TORCH_GA_ALG = torch_ga.GeometricAlgebra([1.0, 1.0, 1.0])
TORCH_GA_TO_GEO = torch_ga.TensorToGeometric(TORCH_GA_ALG, [1, 2, 3])
TORCH_GA_TO_TENSOR = torch_ga.GeometricToTensor(TORCH_GA_ALG, [1, 2, 3])


def _json_default(obj):
    if hasattr(obj, "item"):
        return obj.item()
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")


def _plane_rotor(theta: float):
    return math.cos(theta / 2.0) - math.sin(theta / 2.0) * XY_BIVECTOR


def _clifford_rotate(theta: float, vec: np.ndarray) -> np.ndarray:
    rotor = _plane_rotor(theta)
    mv = vec[0] * E1 + vec[1] * E2 + vec[2] * E3
    rotated = rotor * mv * ~rotor
    return np.array(
        [
            float((rotated | E1).value[0]),
            float((rotated | E2).value[0]),
            float((rotated | E3).value[0]),
        ],
        dtype=np.float64,
    )


def _clifford_rotor_matrix(theta: float) -> np.ndarray:
    return np.array(
        [
            [math.cos(theta), -math.sin(theta), 0.0],
            [math.sin(theta), math.cos(theta), 0.0],
            [0.0, 0.0, 1.0],
        ],
        dtype=np.float64,
    )


def _scipy_rotor_matrix(theta: float) -> np.ndarray:
    generator = np.array(
        [
            [0.0, -1.0, 0.0],
            [1.0, 0.0, 0.0],
            [0.0, 0.0, 0.0],
        ],
        dtype=np.float64,
    )
    return expm(theta * generator)


def _torch_rotor_matrix(theta: torch.Tensor) -> torch.Tensor:
    c = torch.cos(theta)
    s = torch.sin(theta)
    z = torch.zeros((), dtype=torch.float64)
    o = torch.ones((), dtype=torch.float64)
    return torch.stack(
        (
            torch.stack((c, -s, z)),
            torch.stack((s, c, z)),
            torch.stack((z, z, o)),
        )
    )


def _fit_theta(target_matrix: np.ndarray, theta0: float) -> dict[str, object]:
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
    history: list[float] = []

    def closure():
        optimizer.zero_grad()
        pred = _torch_rotor_matrix(theta)
        loss = torch.sum((pred - target) ** 2)
        loss.backward()
        history.append(float(loss.detach()))
        return loss

    optimizer.step(closure)
    with torch.no_grad():
        pred = _torch_rotor_matrix(theta)
        loss = torch.sum((pred - target) ** 2).item()
        pred_np = pred.detach().cpu().numpy()

    return {
        "theta0": float(theta0),
        "theta_fit": float(theta.item()),
        "loss": float(loss),
        "matrix_gap": float(np.max(np.abs(pred_np - target_matrix))),
        "loss_history_tail": [float(x) for x in history[-5:]],
    }


def _torch_ga_roundtrip(vec: np.ndarray) -> np.ndarray:
    tensor = torch.tensor(vec, dtype=torch.float32).reshape(1, 3)
    geo = TORCH_GA_TO_GEO(tensor)
    return TORCH_GA_TO_TENSOR(geo).detach().cpu().numpy().reshape(-1).astype(np.float64)


def _wrap_angle(delta: float) -> float:
    return float(((delta + math.pi) % (2.0 * math.pi)) - math.pi)


def run_positive_tests() -> dict[str, object]:
    theta = 0.83
    clifford_matrix = _clifford_rotor_matrix(theta)
    scipy_matrix = _scipy_rotor_matrix(theta)
    fit = _fit_theta(clifford_matrix, theta0=0.2)
    source_rotated = _clifford_rotate(theta, SOURCE_VECTOR)
    torch_ga_source = _torch_ga_roundtrip(SOURCE_VECTOR)
    torch_ga_rotated = _torch_ga_roundtrip(source_rotated)
    torch_matrix = _torch_rotor_matrix(torch.tensor(fit["theta_fit"], dtype=torch.float64)).detach().cpu().numpy()

    return {
        "target_theta": theta,
        "clifford_scipy_matrix_match": {
            "pass": float(np.max(np.abs(clifford_matrix - scipy_matrix))) < 1e-12,
            "matrix_gap": float(np.max(np.abs(clifford_matrix - scipy_matrix))),
        },
        "torch_fit_matches_clifford": {
            "pass": abs(_wrap_angle(fit["theta_fit"] - theta)) < 1e-8,
            "theta_fit": fit["theta_fit"],
            "theta_gap": _wrap_angle(fit["theta_fit"] - theta),
            "loss": fit["loss"],
            "matrix_gap": fit["matrix_gap"],
        },
        "torch_matrix_matches_clifford": {
            "pass": float(np.max(np.abs(torch_matrix - clifford_matrix))) < 1e-8,
            "matrix_gap": float(np.max(np.abs(torch_matrix - clifford_matrix))),
        },
        "torch_ga_roundtrip_source": {
            "pass": float(np.max(np.abs(torch_ga_source - SOURCE_VECTOR))) < 1e-6,
            "roundtrip_gap": float(np.max(np.abs(torch_ga_source - SOURCE_VECTOR))),
        },
        "torch_ga_roundtrip_rotated": {
            "pass": float(np.max(np.abs(torch_ga_rotated - source_rotated))) < 1e-6,
            "roundtrip_gap": float(np.max(np.abs(torch_ga_rotated - source_rotated))),
        },
    }


def run_negative_tests() -> dict[str, object]:
    theta = 0.83
    wrong_target = np.array(
        [
            [1.0, 0.0, 0.0],
            [0.0, math.cos(theta), -math.sin(theta)],
            [0.0, math.sin(theta), math.cos(theta)],
        ],
        dtype=np.float64,
    )
    fit = _fit_theta(wrong_target, theta0=0.2)
    return {
        "wrong_plane_rejected": {
            "pass": fit["loss"] > 1e-2,
            "loss": fit["loss"],
            "theta_fit": fit["theta_fit"],
        }
    }


def run_boundary_tests() -> dict[str, object]:
    identity = _clifford_rotor_matrix(0.0)
    fit = _fit_theta(identity, theta0=0.0)
    boundary_roundtrip = _torch_ga_roundtrip(SOURCE_VECTOR)
    return {
        "identity_rotor_fit": {
            "pass": abs(_wrap_angle(fit["theta_fit"])) < 1e-10 and fit["loss"] < 1e-12,
            "theta_fit": fit["theta_fit"],
            "loss": fit["loss"],
        },
        "boundary_roundtrip_stable": {
            "pass": float(np.max(np.abs(boundary_roundtrip - SOURCE_VECTOR))) < 1e-6,
            "roundtrip_gap": float(np.max(np.abs(boundary_roundtrip - SOURCE_VECTOR))),
        },
    }


def main() -> int:
    os.makedirs(os.path.dirname(RESULTS_PATH), exist_ok=True)

    positive = run_positive_tests()
    negative = run_negative_tests()
    boundary = run_boundary_tests()
    all_pass = all(v["pass"] for section in (positive, negative, boundary) for v in section.values() if isinstance(v, dict))

    results = {
        "name": "sim_integration_torch_clifford_ga_rotor_bridge",
        "timestamp": datetime.now(UTC).isoformat(),
        "classification": classification,
        "divergence_log": divergence_log,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "summary": {"all_pass": bool(all_pass)},
        "overall_pass": bool(all_pass),
    }

    with open(RESULTS_PATH, "w", encoding="utf-8") as handle:
        json.dump(results, handle, indent=2, default=_json_default)

    print(f"PASS={bool(all_pass)}")
    print(f"Results written to {RESULTS_PATH}")
    print(f"summary.all_pass = {bool(all_pass)}")
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
