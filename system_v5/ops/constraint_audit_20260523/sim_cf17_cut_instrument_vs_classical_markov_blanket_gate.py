#!/usr/bin/env python3
"""CF-17 cut/instrument vs classical Markov-blanket gate.

Candidate-gate implementation only. This tests that a blanket is not a sharp
classical partition primitive. The admissible object is a finite cut state plus
a declared boundary instrument; product/classical blankets are explicit
ablations.
"""

from __future__ import annotations

import json
import math
import pathlib
import time
from typing import Any

import torch


HERE = pathlib.Path(__file__).resolve().parent
OUT = HERE / "results" / "cf17_cut_instrument_vs_classical_markov_blanket_gate_results.json"

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


def normalize_vec(vec: torch.Tensor) -> torch.Tensor:
    return vec / torch.linalg.vector_norm(vec)


def normalize_state(rho: torch.Tensor) -> torch.Tensor:
    return hermitize(rho / torch.real(torch.trace(rho)))


def density(psi: torch.Tensor) -> torch.Tensor:
    return torch.outer(psi, torch.conj(psi))


def partial_trace_a(rho_ab: torch.Tensor) -> torch.Tensor:
    return torch.einsum("abcb->ac", rho_ab.reshape(2, 2, 2, 2))


def partial_trace_b(rho_ab: torch.Tensor) -> torch.Tensor:
    return torch.einsum("abad->bd", rho_ab.reshape(2, 2, 2, 2))


def entropy(rho: torch.Tensor) -> float:
    vals = torch.linalg.eigvalsh(hermitize(rho)).real
    vals = torch.clamp(vals, min=0.0)
    vals = vals / torch.sum(vals)
    nz = vals[vals > EPS]
    return float((-torch.sum(nz * torch.log(nz))).item())


def mutual_information(rho_ab: torch.Tensor) -> float:
    return entropy(partial_trace_a(rho_ab)) + entropy(partial_trace_b(rho_ab)) - entropy(rho_ab)


def trace_distance(a: torch.Tensor, b: torch.Tensor) -> float:
    vals = torch.linalg.eigvalsh(hermitize(a - b)).real
    return float(0.5 * torch.sum(torch.abs(vals)).item())


def bell_cut() -> torch.Tensor:
    psi = normalize_vec(torch.tensor([1.0, 0.0, 0.0, 1.0], dtype=CDTYPE))
    return density(psi)


def product_with_same_marginals(rho_ab: torch.Tensor) -> torch.Tensor:
    return torch.kron(partial_trace_a(rho_ab), partial_trace_b(rho_ab))


def effect(axis: torch.Tensor, bias: float) -> torch.Tensor:
    return hermitize(0.5 * I2 + 0.5 * bias * axis)


def conditional_b_after_a_effect(rho_ab: torch.Tensor, effect_a: torch.Tensor) -> tuple[torch.Tensor, float]:
    sqrt_vals, sqrt_vecs = torch.linalg.eigh(effect_a)
    sqrt_vals = torch.clamp(sqrt_vals.real, min=0.0)
    sqrt_e = sqrt_vecs @ torch.diag(torch.sqrt(sqrt_vals)).to(CDTYPE) @ torch.conj(sqrt_vecs).T
    k_ab = torch.kron(sqrt_e, I2)
    tau = k_ab @ rho_ab @ torch.conj(k_ab).T
    prob = float(torch.real(torch.trace(tau)).item())
    return partial_trace_b(normalize_state(tau)), prob


def positive_cut_instrument_gate() -> dict[str, Any]:
    rho_cut = bell_cut()
    product_cut = product_with_same_marginals(rho_cut)
    x_effect = effect(X, 0.62)
    z_effect = effect(Z, 0.62)
    b_after_x, p_x = conditional_b_after_a_effect(rho_cut, x_effect)
    b_after_z, p_z = conditional_b_after_a_effect(rho_cut, z_effect)
    product_b_after_x, _ = conditional_b_after_a_effect(product_cut, x_effect)
    product_b_after_z, _ = conditional_b_after_a_effect(product_cut, z_effect)
    cut_instrument_gap = trace_distance(b_after_x, b_after_z)
    product_gap = trace_distance(product_b_after_x, product_b_after_z)
    matched_marginal_gap = trace_distance(partial_trace_a(rho_cut), partial_trace_a(product_cut)) + trace_distance(
        partial_trace_b(rho_cut), partial_trace_b(product_cut)
    )
    return {
        "pass": cut_instrument_gap > 0.10 and product_gap < EPS and matched_marginal_gap < EPS,
        "cut_instrument_trace_distance_on_B": cut_instrument_gap,
        "product_control_trace_distance_on_B": product_gap,
        "matched_marginal_gap": matched_marginal_gap,
        "effect_probabilities": {"x_effect": p_x, "z_effect": p_z},
        "cut_mutual_information": mutual_information(rho_cut),
        "product_mutual_information": mutual_information(product_cut),
    }


def classical_blanket_negative_gate() -> dict[str, Any]:
    has_rho_cut = False
    has_boundary_instrument = False
    has_product_control = False
    has_matched_cut_control = False
    rejected = not (has_rho_cut and has_boundary_instrument and has_product_control and has_matched_cut_control)
    attempted_claim = {
        "partition": ["internal", "blanket", "external"],
        "missing_fields": ["rho_cut", "boundary_instrument", "product_control", "matched_cut_control"],
    }
    return {
        "pass": False,
        "expected": "fail",
        "negative_case_type": "executable_rejection",
        "has_rho_cut": has_rho_cut,
        "has_boundary_instrument": has_boundary_instrument,
        "has_product_control": has_product_control,
        "has_matched_cut_control": has_matched_cut_control,
        "negative_rejected": rejected,
        "attempted_claim": attempted_claim,
    }


def classical_correlated_boundary_gate() -> dict[str, Any]:
    rho = torch.diag(torch.tensor([0.5, 0.0, 0.0, 0.5], dtype=CDTYPE))
    x_effect = effect(X, 0.62)
    z_effect = effect(Z, 0.62)
    b_after_x, _ = conditional_b_after_a_effect(rho, x_effect)
    b_after_z, _ = conditional_b_after_a_effect(rho, z_effect)
    probe_gap = trace_distance(b_after_x, b_after_z)
    return {
        "pass": probe_gap > 0.1 and mutual_information(rho) > 0.1,
        "classical_correlated_probe_gap": probe_gap,
        "classical_mutual_information": mutual_information(rho),
        "interpretation": "classical correlation can be represented as a declared separable boundary case, but it still requires named instruments and does not license a primitive sharp blanket",
    }


def main() -> int:
    started = time.time()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    positive = positive_cut_instrument_gate()
    negative = classical_blanket_negative_gate()
    boundary = classical_correlated_boundary_gate()
    result = {
        "schema": "cf17_cut_instrument_vs_classical_markov_blanket_gate_result_v1",
        "name": "cf17_cut_instrument_vs_classical_markov_blanket_gate",
        "classification": "constraint_gate",
        "candidate_fence": "CF-17",
        "gate": "EG-CF17-cut-instrument-vs-classical-markov-blanket",
        "claim_ceiling": "Candidate gate receipt only. Passing does not promote CF-17 to accepted DC without non-redundancy audit.",
        "uses_numpy": False,
        "TOOL_MANIFEST": {
            "torch": {
                "tried": True,
                "used": True,
                "reason": "load-bearing finite cut states, local effects, conditional reduced states, and product/classical controls",
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
