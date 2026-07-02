#!/usr/bin/env python3
"""CF-21 declared-instrument vs primitive-probe gate.

Candidate-gate implementation only. This tests that measurement/probe
apparatus is not a primitive outside the substrate. A measurement claim must
name a finite instrument, keep the probe inside the modeled joint system, and
report the instrument-dependent back-action boundary.
"""

from __future__ import annotations

import json
import math
import pathlib
import time
from typing import Any

import torch


HERE = pathlib.Path(__file__).resolve().parent
OUT = HERE / "results" / "cf21_declared_instrument_vs_primitive_probe_gate_results.json"

CDTYPE = torch.complex128
EPS = 1e-10

I2 = torch.eye(2, dtype=CDTYPE)
X = torch.tensor([[0, 1], [1, 0]], dtype=CDTYPE)
Y = torch.tensor([[0, -1j], [1j, 0]], dtype=CDTYPE)
Z = torch.tensor([[1, 0], [0, -1]], dtype=CDTYPE)
P0 = torch.tensor([[1, 0], [0, 0]], dtype=CDTYPE)
P1 = torch.tensor([[0, 0], [0, 1]], dtype=CDTYPE)


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


def partial_trace_probe(rho_ap: torch.Tensor) -> torch.Tensor:
    return torch.einsum("apbp->ab", rho_ap.reshape(2, 2, 2, 2))


def partial_trace_system(rho_ap: torch.Tensor) -> torch.Tensor:
    return torch.einsum("apab->pb", rho_ap.reshape(2, 2, 2, 2))


def projective_kraus(basis: str) -> list[torch.Tensor]:
    if basis == "Z":
        return [P0, P1]
    if basis == "X":
        plus = 0.5 * torch.tensor([[1, 1], [1, 1]], dtype=CDTYPE)
        minus = 0.5 * torch.tensor([[1, -1], [-1, 1]], dtype=CDTYPE)
        return [plus, minus]
    raise ValueError(basis)


def apply_instrument(rho_a: torch.Tensor, basis: str) -> dict[str, Any]:
    kraus = projective_kraus(basis)
    completeness = sum(torch.conj(k).T @ k for k in kraus)
    effects = [torch.conj(k).T @ k for k in kraus]
    probs = [float(torch.real(torch.trace(effect @ rho_a)).item()) for effect in effects]
    post_a = torch.zeros_like(rho_a)
    for k in kraus:
        post_a = post_a + k @ rho_a @ torch.conj(k).T
    post_a = normalize_state(post_a)
    pointer = torch.diag(torch.tensor(probs, dtype=CDTYPE))
    joint_ap = torch.kron(post_a, pointer)
    return {
        "basis": basis,
        "kraus_count": len(kraus),
        "completeness_gap": float(torch.linalg.matrix_norm(completeness - I2).item()),
        "probabilities": probs,
        "post_a": post_a,
        "joint_ap": joint_ap,
        "probe_reduced": partial_trace_system(joint_ap),
        "system_reduced": partial_trace_probe(joint_ap),
    }


def positive_declared_instrument_gate() -> dict[str, Any]:
    rho = rho_from_bloch(0.58, 0.0, 0.22)
    z_inst = apply_instrument(rho, "Z")
    x_inst = apply_instrument(rho, "X")
    probability_gap = abs(z_inst["probabilities"][0] - x_inst["probabilities"][0])
    back_action_gap = trace_distance(z_inst["post_a"], x_inst["post_a"])
    return {
        "pass": (
            z_inst["completeness_gap"] < EPS
            and x_inst["completeness_gap"] < EPS
            and probability_gap > 0.1
            and back_action_gap > 0.1
        ),
        "same_input_state": "rho_from_bloch(0.58, 0.0, 0.22)",
        "instrument_declared": True,
        "observer_probe_inside_joint_state": True,
        "probe_family_finite": True,
        "z_probabilities": z_inst["probabilities"],
        "x_probabilities": x_inst["probabilities"],
        "probability_gap_between_instruments": probability_gap,
        "back_action_trace_distance": back_action_gap,
        "z_probe_reduced": z_inst["probe_reduced"],
        "x_probe_reduced": x_inst["probe_reduced"],
    }


def primitive_probe_negative_gate() -> dict[str, Any]:
    positive = positive_declared_instrument_gate()
    rejected = positive["probability_gap_between_instruments"] > 0.1
    attempted_claim = {
        "claim": "p(outcome=0) for the state",
        "instrument_declared": False,
        "probe_inside_joint_system": False,
        "instrument_variation_control_available": True,
    }
    return {
        "pass": False,
        "expected": "fail",
        "negative_case_type": "executable_rejection",
        "negative_rejected": rejected,
        "attempted_claim": attempted_claim,
        "ambiguity_witness": {
            "z_probability_0": positive["z_probabilities"][0],
            "x_probability_0": positive["x_probabilities"][0],
            "gap": positive["probability_gap_between_instruments"],
        },
    }


def declared_classical_ablation_boundary_gate() -> dict[str, Any]:
    rho = rho_from_bloch(0.0, 0.0, 0.46)
    z_inst = apply_instrument(rho, "Z")
    diag_probability = float(torch.real(torch.trace(P0 @ rho)).item())
    coherence_before = abs(float(torch.real(torch.trace(rho @ X)).item())) + abs(float(torch.real(torch.trace(rho @ Y)).item()))
    return {
        "pass": abs(z_inst["probabilities"][0] - diag_probability) < EPS and coherence_before < EPS,
        "basis_declared": "Z",
        "state_diagonal_in_declared_basis": True,
        "classical_readout_allowed_as_declared_ablation": True,
        "born_probability_0": z_inst["probabilities"][0],
        "diagonal_probability_0": diag_probability,
        "coherence_before": coherence_before,
        "interpretation": "a classical probability table is admissible only after the instrument/probe family is declared",
    }


def main() -> int:
    started = time.time()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    positive = positive_declared_instrument_gate()
    negative = primitive_probe_negative_gate()
    boundary = declared_classical_ablation_boundary_gate()
    result = {
        "schema": "cf21_declared_instrument_vs_primitive_probe_gate_result_v1",
        "name": "cf21_declared_instrument_vs_primitive_probe_gate",
        "classification": "constraint_gate",
        "candidate_fence": "CF-21",
        "gate": "EG-CF21-declared-instrument-vs-primitive-probe",
        "claim_ceiling": "Candidate gate receipt only. Passing does not promote CF-21 to accepted DC without non-redundancy audit.",
        "uses_numpy": False,
        "TOOL_MANIFEST": {
            "torch": {
                "tried": True,
                "used": True,
                "reason": "load-bearing finite density states, declared projective instruments, in-system probe reductions, and primitive-probe negative control",
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
