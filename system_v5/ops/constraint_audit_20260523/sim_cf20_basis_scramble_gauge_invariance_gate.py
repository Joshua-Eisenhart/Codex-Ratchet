#!/usr/bin/env python3
"""CF-20 basis-scramble / gauge-invariance gate.

Candidate-gate implementation only. This tests that a raw basis coordinate is
not an invariant claim. Invariant readouts must survive unitary basis changes;
coordinate readouts are admitted only when the basis/probe is explicitly part
of the claim.
"""

from __future__ import annotations

import json
import math
import pathlib
import time
from typing import Any

import torch


HERE = pathlib.Path(__file__).resolve().parent
OUT = HERE / "results" / "cf20_basis_scramble_gauge_invariance_gate_results.json"

CDTYPE = torch.complex128
EPS = 1e-10

I2 = torch.eye(2, dtype=CDTYPE)
X = torch.tensor([[0, 1], [1, 0]], dtype=CDTYPE)
Y = torch.tensor([[0, -1j], [1j, 0]], dtype=CDTYPE)
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


def rho_from_bloch(x: float, y: float, z: float) -> torch.Tensor:
    return normalize_state(0.5 * (I2 + x * X + y * Y + z * Z))


def unitary(axis: torch.Tensor, theta: float) -> torch.Tensor:
    return math.cos(theta / 2) * I2 - 1j * math.sin(theta / 2) * axis


def trace_distance(a: torch.Tensor, b: torch.Tensor) -> float:
    vals = torch.linalg.eigvalsh(hermitize(a - b)).real
    return float(0.5 * torch.sum(torch.abs(vals)).item())


def z_coordinate(rho: torch.Tensor) -> float:
    return float(torch.real(torch.trace(rho @ Z)).item())


def basis_transform(rho: torch.Tensor, u: torch.Tensor) -> torch.Tensor:
    return hermitize(u @ rho @ torch.conj(u).T)


def positive_invariant_gate() -> dict[str, Any]:
    rho = rho_from_bloch(0.41, -0.23, 0.35)
    sigma = rho_from_bloch(-0.18, 0.32, 0.27)
    u = unitary(X, 0.71) @ unitary(Z, -0.43)
    invariant_before = trace_distance(rho, sigma)
    invariant_after = trace_distance(basis_transform(rho, u), basis_transform(sigma, u))
    raw_before = abs(z_coordinate(rho) - z_coordinate(sigma))
    raw_after = abs(z_coordinate(basis_transform(rho, u)) - z_coordinate(basis_transform(sigma, u)))
    return {
        "pass": abs(invariant_before - invariant_after) < EPS and abs(raw_before - raw_after) > 0.05,
        "trace_distance_before": invariant_before,
        "trace_distance_after_basis_scramble": invariant_after,
        "trace_distance_scramble_gap": abs(invariant_before - invariant_after),
        "raw_z_gap_before": raw_before,
        "raw_z_gap_after_basis_scramble": raw_after,
        "raw_z_scramble_gap": abs(raw_before - raw_after),
    }


def primitive_basis_negative_gate() -> dict[str, Any]:
    rho = rho_from_bloch(0.41, -0.23, 0.35)
    sigma = rho_from_bloch(-0.18, 0.32, 0.27)
    u = unitary(X, 0.71) @ unitary(Z, -0.43)
    raw_before = abs(z_coordinate(rho) - z_coordinate(sigma))
    raw_after = abs(z_coordinate(basis_transform(rho, u)) - z_coordinate(basis_transform(sigma, u)))
    rejected = abs(raw_before - raw_after) > 0.05
    attempted_claim = {
        "readout": "raw z-coordinate gap",
        "basis_declared": False,
        "basis_scramble_control_present": True,
    }
    return {
        "pass": False,
        "expected": "fail",
        "negative_case_type": "executable_rejection",
        "negative_rejected": rejected,
        "raw_z_gap_before": raw_before,
        "raw_z_gap_after_basis_scramble": raw_after,
        "attempted_claim": attempted_claim,
    }


def declared_basis_boundary_gate() -> dict[str, Any]:
    rho = rho_from_bloch(0.0, 0.0, 0.64)
    sigma = rho_from_bloch(0.0, 0.0, -0.12)
    raw_z_gap = abs(z_coordinate(rho) - z_coordinate(sigma))
    invariant_gap = trace_distance(rho, sigma)
    return {
        "pass": raw_z_gap > 0.1 and abs(0.5 * raw_z_gap - invariant_gap) < EPS,
        "basis_declared": "Z",
        "states_diagonal_in_declared_basis": True,
        "raw_z_gap": raw_z_gap,
        "trace_distance": invariant_gap,
        "interpretation": "basis-specific readout is admissible only as a declared probe/boundary case, not as basis-free ontology",
    }


def main() -> int:
    started = time.time()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    positive = positive_invariant_gate()
    negative = primitive_basis_negative_gate()
    boundary = declared_basis_boundary_gate()
    result = {
        "schema": "cf20_basis_scramble_gauge_invariance_gate_result_v1",
        "name": "cf20_basis_scramble_gauge_invariance_gate",
        "classification": "constraint_gate",
        "candidate_fence": "CF-20",
        "gate": "EG-CF20-basis-scramble-gauge-invariance",
        "claim_ceiling": "Candidate gate receipt only. Passing does not promote CF-20 to accepted DC without non-redundancy audit.",
        "uses_numpy": False,
        "TOOL_MANIFEST": {
            "torch": {
                "tried": True,
                "used": True,
                "reason": "load-bearing finite density states, unitary basis scramble, invariant trace-distance readout, and raw-coordinate negative control",
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
