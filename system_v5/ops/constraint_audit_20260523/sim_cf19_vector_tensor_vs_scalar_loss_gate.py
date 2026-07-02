#!/usr/bin/env python3
"""CF-19 vector/tensor vs scalar-loss gate.

Candidate-gate implementation only. This tests that a scalar score is a
declared projection, not primitive ontology. A vector readout can distinguish
states or candidates that a scalar aggregate collapses.
"""

from __future__ import annotations

import json
import pathlib
import time
from typing import Any

import torch


HERE = pathlib.Path(__file__).resolve().parent
OUT = HERE / "results" / "cf19_vector_tensor_vs_scalar_loss_gate_results.json"

CDTYPE = torch.complex128
DTYPE = torch.float64
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


def readout_vector(rho: torch.Tensor) -> torch.Tensor:
    return torch.tensor(
        [
            torch.real(torch.trace(rho @ X)).item(),
            torch.real(torch.trace(rho @ Z)).item(),
        ],
        dtype=DTYPE,
    )


def scalar_sum_abs(vec: torch.Tensor) -> float:
    return float(torch.sum(torch.abs(vec)).item())


def positive_vector_before_scalar_gate() -> dict[str, Any]:
    rho_x = rho_from_bloch(0.62, 0.0, 0.0)
    rho_z = rho_from_bloch(0.0, 0.0, 0.62)
    vec_x = readout_vector(rho_x)
    vec_z = readout_vector(rho_z)
    vector_gap = float(torch.linalg.vector_norm(vec_x - vec_z).item())
    scalar_x = scalar_sum_abs(vec_x)
    scalar_z = scalar_sum_abs(vec_z)
    scalar_gap = abs(scalar_x - scalar_z)
    return {
        "pass": vector_gap > 0.5 and scalar_gap < EPS,
        "readout_basis": ["X_expectation", "Z_expectation"],
        "vector_x": vec_x,
        "vector_z": vec_z,
        "vector_gap": vector_gap,
        "scalar_sum_abs_x": scalar_x,
        "scalar_sum_abs_z": scalar_z,
        "scalar_gap": scalar_gap,
    }


def primitive_scalar_negative_gate() -> dict[str, Any]:
    positive = positive_vector_before_scalar_gate()
    rejected = positive["vector_gap"] > 0.5 and positive["scalar_gap"] < EPS
    attempted_claim = {
        "scalar": "sum(abs([X_expectation, Z_expectation]))",
        "projection_declared": False,
        "loss_reported": False,
        "vector_readout_available": True,
    }
    return {
        "pass": False,
        "expected": "fail",
        "negative_case_type": "executable_rejection",
        "negative_rejected": rejected,
        "attempted_claim": attempted_claim,
        "lost_vector_gap": positive["vector_gap"],
        "scalar_gap_after_loss": positive["scalar_gap"],
    }


def declared_projection_boundary_gate() -> dict[str, Any]:
    rho_x = rho_from_bloch(0.62, 0.0, 0.0)
    rho_z = rho_from_bloch(0.0, 0.0, 0.62)
    vec_x = readout_vector(rho_x)
    vec_z = readout_vector(rho_z)
    weights = torch.tensor([1.0, 0.0], dtype=DTYPE)
    projected_x = float(torch.dot(weights, vec_x).item())
    projected_z = float(torch.dot(weights, vec_z).item())
    projected_gap = abs(projected_x - projected_z)
    return {
        "pass": projected_gap > 0.5,
        "projection_declared": True,
        "weights": weights,
        "loss_declared": "Z component intentionally discarded by X-only probe",
        "projected_x": projected_x,
        "projected_z": projected_z,
        "projected_gap": projected_gap,
        "interpretation": "a scalar is admissible as a declared projection with stated loss, not as a primitive total order",
    }


def main() -> int:
    started = time.time()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    positive = positive_vector_before_scalar_gate()
    negative = primitive_scalar_negative_gate()
    boundary = declared_projection_boundary_gate()
    result = {
        "schema": "cf19_vector_tensor_vs_scalar_loss_gate_result_v1",
        "name": "cf19_vector_tensor_vs_scalar_loss_gate",
        "classification": "constraint_gate",
        "candidate_fence": "CF-19",
        "gate": "EG-CF19-vector-tensor-vs-scalar-loss",
        "claim_ceiling": "Candidate gate receipt only. Passing does not promote CF-19 to accepted DC without non-redundancy audit.",
        "uses_numpy": False,
        "TOOL_MANIFEST": {
            "torch": {
                "tried": True,
                "used": True,
                "reason": "load-bearing finite density states, vector readouts, scalar-collapse control, and declared projection boundary",
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
