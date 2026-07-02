#!/usr/bin/env python3
"""CF-16 CPTP instrument vs classical Markov-chain gate.

Candidate-gate implementation only. This tests that the process primitive is a
finite operator/instrument registry, not a primitive stochastic transition
matrix. A commuting diagonal channel is allowed as an explicit ablation, but it
cannot be the root process model for noncommuting carriers.
"""

from __future__ import annotations

import json
import math
import pathlib
import time
from typing import Any

import torch


HERE = pathlib.Path(__file__).resolve().parent
OUT = HERE / "results" / "cf16_cptp_instrument_vs_classical_markov_chain_gate_results.json"

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


def dephase(axis: torch.Tensor, q: float) -> list[torch.Tensor]:
    return [math.sqrt(1.0 - q) * I2, math.sqrt(q) * axis]


def amplitude_down(gamma: float) -> list[torch.Tensor]:
    k0 = torch.tensor([[1, 0], [0, math.sqrt(1.0 - gamma)]], dtype=CDTYPE)
    k1 = torch.tensor([[0, math.sqrt(gamma)], [0, 0]], dtype=CDTYPE)
    return [k0, k1]


def apply_kraus(rho: torch.Tensor, kraus: list[torch.Tensor]) -> torch.Tensor:
    out = torch.zeros_like(rho)
    for k in kraus:
        out = out + k @ rho @ torch.conj(k).T
    return normalize_state(out)


def compose(rho: torch.Tensor, channels: list[list[torch.Tensor]]) -> torch.Tensor:
    out = rho
    for channel in channels:
        out = apply_kraus(out, channel)
    return out


def kraus_completeness_gap(kraus: list[torch.Tensor]) -> float:
    acc = torch.zeros((2, 2), dtype=CDTYPE)
    for k in kraus:
        acc = acc + torch.conj(k).T @ k
    return float(torch.linalg.matrix_norm(acc - I2).real.item())


def trace_distance(a: torch.Tensor, b: torch.Tensor) -> float:
    vals = torch.linalg.eigvalsh(hermitize(a - b)).real
    return float(0.5 * torch.sum(torch.abs(vals)).item())


def diagonal_part(rho: torch.Tensor) -> torch.Tensor:
    return torch.diag(torch.diag(rho)).to(CDTYPE)


def positive_cptp_order_gate() -> dict[str, Any]:
    rho = rho_from_bloch(0.37, -0.29, 0.41)
    channel_a = [unitary(X, 0.73)]
    channel_b = dephase(Z, 0.31)
    channel_c = amplitude_down(0.17)
    forward = compose(rho, [channel_a, channel_b, channel_c])
    reversed_order = compose(rho, [channel_c, channel_b, channel_a])
    order_gap = trace_distance(forward, reversed_order)
    offdiag_after = float(torch.linalg.matrix_norm(forward - diagonal_part(forward)).real.item())
    return {
        "pass": (
            max(kraus_completeness_gap(channel) for channel in (channel_a, channel_b, channel_c)) < EPS
            and order_gap > 0.02
            and offdiag_after > 0.02
        ),
        "path_count": len(channel_a) * len(channel_b) * len(channel_c),
        "kraus_completeness_gaps": [
            kraus_completeness_gap(channel_a),
            kraus_completeness_gap(channel_b),
            kraus_completeness_gap(channel_c),
        ],
        "noncommuting_order_trace_distance": order_gap,
        "coherence_norm_after_channel": offdiag_after,
    }


def commuting_markov_boundary_gate() -> dict[str, Any]:
    rho = diagonal_part(rho_from_bloch(0.37, -0.29, 0.41))
    channel_a = dephase(Z, 0.31)
    channel_b = [unitary(Z, -0.22)]
    forward = compose(rho, [channel_a, channel_b])
    reversed_order = compose(rho, [channel_b, channel_a])
    order_gap = trace_distance(forward, reversed_order)
    coherence_norm = float(torch.linalg.matrix_norm(forward - diagonal_part(forward)).real.item())
    return {
        "pass": order_gap < EPS and coherence_norm < EPS,
        "commuting_order_trace_distance": order_gap,
        "coherence_norm": coherence_norm,
        "interpretation": "diagonal commuting CPTP ablation may be represented by a classical Markov chain, but only as a derived boundary case",
    }


def primitive_markov_negative_gate() -> dict[str, Any]:
    transition = torch.tensor([[0.82, 0.18], [0.11, 0.89]], dtype=torch.float64)
    row_stochastic_gap = float(torch.max(torch.abs(torch.sum(transition, dim=1) - 1.0)).item())
    has_complex_coherence_carrier = False
    has_kraus_registry = False
    has_probe = False
    rejected = row_stochastic_gap < EPS and not (has_complex_coherence_carrier and has_kraus_registry and has_probe)
    attempted_claim = {
        "transition_matrix": transition.tolist(),
        "missing_fields": ["kraus_registry", "measurement_probe", "coherence_carrier", "commuting_ablation"],
    }
    return {
        "pass": False,
        "expected": "fail",
        "negative_case_type": "executable_rejection",
        "row_stochastic_gap": row_stochastic_gap,
        "has_complex_coherence_carrier": has_complex_coherence_carrier,
        "has_kraus_registry": has_kraus_registry,
        "has_probe": has_probe,
        "negative_rejected": rejected,
        "attempted_claim": attempted_claim,
    }


def main() -> int:
    started = time.time()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    positive = positive_cptp_order_gate()
    negative = primitive_markov_negative_gate()
    boundary = commuting_markov_boundary_gate()
    result = {
        "schema": "cf16_cptp_instrument_vs_classical_markov_chain_gate_result_v1",
        "name": "cf16_cptp_instrument_vs_classical_markov_chain_gate",
        "classification": "constraint_gate",
        "candidate_fence": "CF-16",
        "gate": "EG-CF16-cptp-instrument-vs-classical-markov-chain",
        "claim_ceiling": "Candidate gate receipt only. Passing does not promote CF-16 to accepted DC without non-redundancy audit.",
        "uses_numpy": False,
        "TOOL_MANIFEST": {
            "torch": {
                "tried": True,
                "used": True,
                "reason": "load-bearing finite density state evolution, Kraus completeness, order gap, and commuting Markov ablation",
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
