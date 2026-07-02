#!/usr/bin/env python3
"""CF-22 order-race vs primitive-simultaneity gate."""

from __future__ import annotations

import json
import math
import pathlib
import time
from typing import Any

import torch


HERE = pathlib.Path(__file__).resolve().parent
OUT = HERE / "results" / "cf22_order_race_vs_primitive_simultaneity_gate_results.json"

CDTYPE = torch.complex128
EPS = 1e-10

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
    if isinstance(value, complex):
        return {"real": value.real, "imag": value.imag}
    return value


def hermitize(rho: torch.Tensor) -> torch.Tensor:
    return (rho + torch.conj(rho).T) / 2


def normalize_state(rho: torch.Tensor) -> torch.Tensor:
    return hermitize(rho / torch.real(torch.trace(rho)))


def rho_from_bloch(x: float, z: float) -> torch.Tensor:
    return normalize_state(0.5 * (I2 + x * X + z * Z))


def unitary(axis: torch.Tensor, theta: float) -> torch.Tensor:
    return math.cos(theta / 2) * I2 - 1j * math.sin(theta / 2) * axis


def evolve(rho: torch.Tensor, ops: list[torch.Tensor]) -> torch.Tensor:
    out = rho
    for op in ops:
        out = op @ out @ torch.conj(op).T
    return hermitize(out)


def trace_distance(a: torch.Tensor, b: torch.Tensor) -> float:
    vals = torch.linalg.eigvalsh(hermitize(a - b)).real
    return float(0.5 * torch.sum(torch.abs(vals)).item())


def positive_order_contract_gate() -> dict[str, Any]:
    rho = rho_from_bloch(0.43, 0.51)
    a = unitary(X, 0.91)
    b = unitary(Z, -0.73)
    ab = evolve(rho, [a, b])
    ba = evolve(rho, [b, a])
    race_gap = trace_distance(ab, ba)
    return {
        "pass": race_gap > 0.1,
        "merge_contract_declared": ["A_then_B", "B_then_A"],
        "no_global_now": True,
        "order_race_trace_distance": race_gap,
    }


def primitive_simultaneity_negative_gate() -> dict[str, Any]:
    rho = rho_from_bloch(0.43, 0.51)
    a = unitary(X, 0.91)
    b = unitary(Z, -0.73)
    ab = evolve(rho, [a, b])
    ba = evolve(rho, [b, a])
    order_race_gap = trace_distance(ab, ba)
    same_time_average = hermitize(0.5 * (ab + ba))
    average_to_ab_gap = trace_distance(same_time_average, ab)
    average_to_ba_gap = trace_distance(same_time_average, ba)
    lost_order_gap = min(average_to_ab_gap, average_to_ba_gap)
    rejected = order_race_gap > 0.1 and lost_order_gap > 0.05
    return {
        "pass": False,
        "expected": "fail",
        "negative_case_type": "executable_rejection",
        "negative_rejected": rejected,
        "attempted_claim": {
            "claim": "A and B happen at one primitive same-time state",
            "merge_contract_declared": False,
            "order_race_control_available": True,
        },
        "order_race_gap_before_erasure": order_race_gap,
        "same_time_average_to_ab_gap": average_to_ab_gap,
        "same_time_average_to_ba_gap": average_to_ba_gap,
        "lost_order_gap_to_nearest_ordered_state": lost_order_gap,
    }


def commuting_boundary_gate() -> dict[str, Any]:
    rho = rho_from_bloch(0.43, 0.51)
    a = unitary(Z, 0.91)
    b = unitary(Z, -0.73)
    ab = evolve(rho, [a, b])
    ba = evolve(rho, [b, a])
    gap = trace_distance(ab, ba)
    return {
        "pass": gap < EPS,
        "commuting_collapse_control": True,
        "order_gap": gap,
        "interpretation": "simultaneity-like collapse is allowed only when the declared operations commute",
    }


def main() -> int:
    started = time.time()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    positive = positive_order_contract_gate()
    negative = primitive_simultaneity_negative_gate()
    boundary = commuting_boundary_gate()
    result = {
        "schema": "cf22_order_race_vs_primitive_simultaneity_gate_result_v1",
        "name": "cf22_order_race_vs_primitive_simultaneity_gate",
        "classification": "constraint_gate",
        "candidate_fence": "CF-22",
        "gate": "EG-CF22-order-race-vs-primitive-simultaneity",
        "claim_ceiling": "Candidate gate receipt only. Passing does not promote CF-22 to accepted DC without non-redundancy audit.",
        "uses_numpy": False,
        "TOOL_MANIFEST": {
            "torch": {
                "tried": True,
                "used": True,
                "reason": "load-bearing finite density states, noncommuting order-race control, and commuting collapse boundary",
            },
            "python_json": {"tried": True, "used": True, "reason": "supportive result serialization"},
        },
        "TOOL_INTEGRATION_DEPTH": {"torch": "load_bearing", "python_json": "supportive"},
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "runtime_seconds": time.time() - started,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "all_pass": positive["pass"] and negative["pass"] is False and negative["negative_rejected"] and boundary["pass"],
    }
    OUT.write_text(json.dumps(as_jsonable(result), indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"all_pass": result["all_pass"], "out": str(OUT)}, indent=2))
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
