#!/usr/bin/env python3
"""CF-25 irreversible-channel vs free-inverse gate."""

from __future__ import annotations

import json
import math
import pathlib
import time
from typing import Any

import torch


HERE = pathlib.Path(__file__).resolve().parent
OUT = HERE / "results" / "cf25_irreversible_channel_vs_free_inverse_gate_results.json"

CDTYPE = torch.complex128
EPS = 1e-10

I2 = torch.eye(2, dtype=CDTYPE)
X = torch.tensor([[0, 1], [1, 0]], dtype=CDTYPE)
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


def density(ket: torch.Tensor) -> torch.Tensor:
    return torch.outer(ket, torch.conj(ket))


def unitary(axis: torch.Tensor, theta: float) -> torch.Tensor:
    return math.cos(theta / 2) * I2 - 1j * math.sin(theta / 2) * axis


def apply_unitary(rho: torch.Tensor, u: torch.Tensor) -> torch.Tensor:
    return hermitize(u @ rho @ torch.conj(u).T)


def amplitude_damping_kraus(gamma: float) -> list[torch.Tensor]:
    k0 = torch.tensor([[1, 0], [0, math.sqrt(1 - gamma)]], dtype=CDTYPE)
    k1 = torch.tensor([[0, math.sqrt(gamma)], [0, 0]], dtype=CDTYPE)
    return [k0, k1]


def apply_channel(rho: torch.Tensor, kraus: list[torch.Tensor]) -> torch.Tensor:
    out = torch.zeros_like(rho)
    for k in kraus:
        out = out + k @ rho @ torch.conj(k).T
    return hermitize(out)


def normalize_state(rho: torch.Tensor) -> torch.Tensor:
    return hermitize(rho / torch.real(torch.trace(rho)))


def trace_distance(a: torch.Tensor, b: torch.Tensor) -> float:
    vals = torch.linalg.eigvalsh(hermitize(a - b)).real
    return float(0.5 * torch.sum(torch.abs(vals)).item())


def positive_inverse_witness_gate() -> dict[str, Any]:
    rho = density(torch.tensor([math.sqrt(0.35), math.sqrt(0.65)], dtype=CDTYPE))
    u = unitary(X, 0.73)
    recovered = apply_unitary(apply_unitary(rho, u), torch.conj(u).T)
    recovery_gap = trace_distance(rho, recovered)
    damped_0 = apply_channel(P0, amplitude_damping_kraus(1.0))
    damped_1 = apply_channel(P1, amplitude_damping_kraus(1.0))
    collapse_gap = trace_distance(damped_0, damped_1)
    return {
        "pass": recovery_gap < EPS and collapse_gap < EPS,
        "inverse_witness": "U then U_dagger",
        "unitary_recovery_gap": recovery_gap,
        "irreversible_channel_control": "amplitude_damping_gamma_1_collapses_|0>_and_|1>",
        "collapsed_output_gap": collapse_gap,
    }


def primitive_inverse_negative_gate() -> dict[str, Any]:
    gamma = 0.6
    rho = density(torch.tensor([1.0, 1.0], dtype=CDTYPE) / math.sqrt(2))
    damped = apply_channel(rho, amplitude_damping_kraus(gamma))
    proposed_no_jump_inverse = torch.diag(torch.tensor([1.0, 1.0 / math.sqrt(1.0 - gamma)], dtype=CDTYPE))
    proposed_recovered = normalize_state(proposed_no_jump_inverse @ damped @ torch.conj(proposed_no_jump_inverse).T)
    recovery_gap = trace_distance(rho, proposed_recovered)
    rejected = recovery_gap > 0.05
    return {
        "pass": False,
        "expected": "fail",
        "negative_case_type": "executable_rejection",
        "negative_rejected": rejected,
        "attempted_claim": {
            "claim": "the amplitude damping channel has a free inverse",
            "inverse_witness_supplied": False,
            "irreversible_channel_control_available": True,
        },
        "gamma": gamma,
        "proposed_inverse": "invert no-jump Kraus branch only, then renormalize",
        "recovery_gap_after_proposed_inverse": recovery_gap,
    }


def unitary_subgroup_boundary_gate() -> dict[str, Any]:
    rho = density(torch.tensor([1.0, 1.0j], dtype=CDTYPE) / math.sqrt(2))
    u = unitary(X, -0.41)
    recovered = apply_unitary(apply_unitary(rho, u), torch.conj(u).T)
    gap = trace_distance(rho, recovered)
    return {
        "pass": gap < EPS,
        "unitary_subgroup_boundary": True,
        "inverse": "U_dagger",
        "recovery_gap": gap,
        "interpretation": "reversibility is admitted for a witnessed unitary subgroup, not for arbitrary channels",
    }


def main() -> int:
    started = time.time()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    positive = positive_inverse_witness_gate()
    negative = primitive_inverse_negative_gate()
    boundary = unitary_subgroup_boundary_gate()
    result = {
        "schema": "cf25_irreversible_channel_vs_free_inverse_gate_result_v1",
        "name": "cf25_irreversible_channel_vs_free_inverse_gate",
        "classification": "constraint_gate",
        "candidate_fence": "CF-25",
        "gate": "EG-CF25-irreversible-channel-vs-free-inverse",
        "claim_ceiling": "Candidate gate receipt only. Passing does not promote CF-25 to accepted DC without non-redundancy audit.",
        "uses_numpy": False,
        "TOOL_MANIFEST": {
            "torch": {
                "tried": True,
                "used": True,
                "reason": "load-bearing finite density states, unitary inverse witness, irreversible amplitude-damping control, and free-inverse rejection",
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
