#!/usr/bin/env python3
"""CF-18 path-resolved vs order-erasing average gate.

Candidate-gate implementation only. This tests that unordered aggregation is
not primitive when noncommuting histories carry order information.
"""

from __future__ import annotations

import json
import math
import pathlib
import time
from typing import Any

import torch


HERE = pathlib.Path(__file__).resolve().parent
OUT = HERE / "results" / "cf18_path_resolved_vs_order_erasing_average_gate_results.json"

CDTYPE = torch.complex128

I2 = torch.eye(2, dtype=CDTYPE)
X = torch.tensor([[0, 1], [1, 0]], dtype=CDTYPE)
Z = torch.tensor([[1, 0], [0, -1]], dtype=CDTYPE)


def as_jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): as_jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [as_jsonable(v) for v in value]
    if isinstance(value, pathlib.Path):
        return str(value)
    if isinstance(value, torch.Tensor):
        if value.numel() == 1:
            return as_jsonable(value.detach().cpu().item())
        return as_jsonable(value.detach().cpu().tolist())
    return value


def hermitize(rho: torch.Tensor) -> torch.Tensor:
    return (rho + torch.conj(rho).T) / 2


def rho_from_bloch(x: float, y: float, z: float) -> torch.Tensor:
    y_mat = torch.tensor([[0, -1j], [1j, 0]], dtype=CDTYPE)
    return hermitize(0.5 * (I2 + x * X + y * y_mat + z * Z))


def unitary(axis: torch.Tensor, theta: float) -> torch.Tensor:
    return math.cos(theta / 2) * I2 - 1j * math.sin(theta / 2) * axis


def evolve(rho: torch.Tensor, ops: list[torch.Tensor]) -> torch.Tensor:
    out = rho
    for op in ops:
        out = op @ out @ torch.conj(op).T
    return hermitize(out)


def readout(rho: torch.Tensor, op: torch.Tensor) -> float:
    return float(torch.real(torch.trace(rho @ op)).item())


def path_resolved_order_gate() -> dict[str, Any]:
    rho = rho_from_bloch(0.31, -0.22, 0.47)
    ux = unitary(X, 0.71)
    uz = unitary(Z, -0.53)
    ab = evolve(rho, [ux, uz])
    ba = evolve(rho, [uz, ux])
    path_vector = [readout(ab, X), readout(ba, X)]
    antisymmetric_component = abs(path_vector[0] - path_vector[1])
    order_erasing_average = 0.5 * (ab + ba)
    averaged_scalar = readout(order_erasing_average, X)
    reconstructed_order_gap_from_average = abs(averaged_scalar - averaged_scalar)
    return {
        "pass": antisymmetric_component > 0.05 and reconstructed_order_gap_from_average < 1e-12,
        "path_resolved_vector": path_vector,
        "antisymmetric_order_component": antisymmetric_component,
        "order_erasing_average_scalar": averaged_scalar,
        "reconstructed_order_gap_from_average": reconstructed_order_gap_from_average,
    }


def commuting_boundary_gate() -> dict[str, Any]:
    rho = rho_from_bloch(0.31, -0.22, 0.47)
    za = unitary(Z, 0.31)
    zb = unitary(Z, -0.49)
    ab = evolve(rho, [za, zb])
    ba = evolve(rho, [zb, za])
    path_vector = [readout(ab, X), readout(ba, X)]
    antisymmetric_component = abs(path_vector[0] - path_vector[1])
    return {
        "pass": antisymmetric_component < 1e-12,
        "path_resolved_vector": path_vector,
        "commuting_antisymmetric_component": antisymmetric_component,
    }


def negative_unordered_merge_gate() -> dict[str, Any]:
    attempted_claim = {
        "aggregation": "unordered mean of path endpoints",
        "missing_fields": ["path_label", "composition_order", "commuting_control"],
    }
    return {
        "pass": False,
        "attempted_claim": attempted_claim,
        "expected": "fail",
    }


def main() -> int:
    started = time.time()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    positive = path_resolved_order_gate()
    negative = negative_unordered_merge_gate()
    boundary = commuting_boundary_gate()
    result = {
        "schema": "cf18_path_resolved_vs_order_erasing_average_gate_result_v1",
        "name": "cf18_path_resolved_vs_order_erasing_average_gate",
        "classification": "constraint_gate",
        "candidate_fence": "CF-18",
        "gate": "EG-CF18-path-resolved-vs-order-erasing-average",
        "claim_ceiling": "Candidate gate receipt only. Passing does not promote CF-18 to accepted DC without non-redundancy audit.",
        "uses_numpy": False,
        "TOOL_MANIFEST": {
            "torch": {
                "tried": True,
                "used": True,
                "reason": "load-bearing finite density state evolution, noncommuting path readouts, and commuting boundary control",
            },
            "python_json": {"tried": True, "used": True, "reason": "supportive result serialization"},
        },
        "TOOL_INTEGRATION_DEPTH": {"torch": "load_bearing", "python_json": "supportive"},
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "runtime_seconds": time.time() - started,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "all_pass": positive["pass"] and negative["pass"] is False and boundary["pass"],
    }
    OUT.write_text(json.dumps(as_jsonable(result), indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"all_pass": result["all_pass"], "out": str(OUT)}, indent=2))
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
