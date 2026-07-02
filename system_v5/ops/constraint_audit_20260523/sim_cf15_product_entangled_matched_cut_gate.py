#!/usr/bin/env python3
"""CF-15 product/entangled/matched-cut gate.

Candidate-gate implementation only. This tests that tensor factorization and
independence are not primitive: the same marginals can support product,
classically correlated, or entangled joint states.
"""

from __future__ import annotations

import json
import math
import pathlib
import time
from typing import Any

import torch


HERE = pathlib.Path(__file__).resolve().parent
OUT = HERE / "results" / "cf15_product_entangled_matched_cut_gate_results.json"

CDTYPE = torch.complex128
EPS = 1e-10

I2 = torch.eye(2, dtype=CDTYPE)


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


def density(psi: torch.Tensor) -> torch.Tensor:
    return torch.outer(psi, torch.conj(psi))


def entropy(rho: torch.Tensor) -> float:
    vals = torch.linalg.eigvalsh(hermitize(rho)).real
    vals = torch.clamp(vals, min=0.0)
    vals = vals / torch.sum(vals)
    nz = vals[vals > EPS]
    return float((-torch.sum(nz * torch.log(nz))).item())


def partial_trace_a(rho_ab: torch.Tensor) -> torch.Tensor:
    return torch.einsum("abcb->ac", rho_ab.reshape(2, 2, 2, 2))


def partial_trace_b(rho_ab: torch.Tensor) -> torch.Tensor:
    return torch.einsum("abad->bd", rho_ab.reshape(2, 2, 2, 2))


def mutual_info(rho_ab: torch.Tensor) -> float:
    return entropy(partial_trace_a(rho_ab)) + entropy(partial_trace_b(rho_ab)) - entropy(rho_ab)


def trace_distance(rho: torch.Tensor, sigma: torch.Tensor) -> float:
    vals = torch.linalg.eigvalsh(hermitize(rho - sigma)).real
    return float((0.5 * torch.sum(torch.abs(vals))).item())


def partial_transpose_b(rho_ab: torch.Tensor) -> torch.Tensor:
    return rho_ab.reshape(2, 2, 2, 2).permute(0, 3, 2, 1).reshape(4, 4)


def negativity(rho_ab: torch.Tensor) -> float:
    vals = torch.linalg.eigvalsh(hermitize(partial_transpose_b(rho_ab))).real
    return float(torch.sum(torch.abs(vals[vals < 0.0])).item())


def bell_state() -> torch.Tensor:
    psi = torch.tensor([1.0, 0.0, 0.0, 1.0], dtype=CDTYPE) / math.sqrt(2)
    return density(psi)


def product_maxmix() -> torch.Tensor:
    return torch.kron(I2 / 2.0, I2 / 2.0)


def classical_correlated() -> torch.Tensor:
    zero_zero = torch.tensor([1.0, 0.0, 0.0, 0.0], dtype=CDTYPE)
    one_one = torch.tensor([0.0, 0.0, 0.0, 1.0], dtype=CDTYPE)
    return 0.5 * density(zero_zero) + 0.5 * density(one_one)


def main() -> int:
    started = time.time()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    product = product_maxmix()
    entangled = bell_state()
    classical = classical_correlated()
    product_from_entangled_marginals = torch.kron(partial_trace_b(entangled), partial_trace_a(entangled))
    matched_marginal_gap = max(
        trace_distance(partial_trace_a(entangled), partial_trace_a(product)),
        trace_distance(partial_trace_b(entangled), partial_trace_b(product)),
    )
    primitive_factorization_error = trace_distance(entangled, product_from_entangled_marginals)
    product_mi = mutual_info(product)
    entangled_mi = mutual_info(entangled)
    classical_mi = mutual_info(classical)
    product_neg = negativity(product)
    entangled_neg = negativity(entangled)
    classical_neg = negativity(classical)
    result = {
        "schema": "cf15_product_entangled_matched_cut_gate_result_v1",
        "name": "cf15_product_entangled_matched_cut_gate",
        "classification": "constraint_gate",
        "candidate_fence": "CF-15",
        "gate": "EG-CF15-product-entangled-matched-cut",
        "claim_ceiling": "Candidate gate receipt only. Passing does not promote CF-15 to accepted DC without non-redundancy audit.",
        "uses_numpy": False,
        "TOOL_MANIFEST": {
            "torch": {
                "tried": True,
                "used": True,
                "reason": "load-bearing finite density matrices, partial traces, mutual information, and negativity controls",
            },
            "python_json": {"tried": True, "used": True, "reason": "supportive result serialization"},
        },
        "TOOL_INTEGRATION_DEPTH": {"torch": "load_bearing", "python_json": "supportive"},
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "runtime_seconds": time.time() - started,
        "positive": {
            "pass": primitive_factorization_error > 0.25 and entangled_mi > 1.0 and entangled_neg > 0.45,
            "primitive_factorization_error": primitive_factorization_error,
            "entangled_mutual_info": entangled_mi,
            "entangled_negativity": entangled_neg,
        },
        "negative": {
            "pass": product_mi < 1e-10 and product_neg < 1e-10,
            "product_mutual_info": product_mi,
            "product_negativity": product_neg,
        },
        "matched_control": {
            "pass": matched_marginal_gap < 1e-10 and primitive_factorization_error > 0.25,
            "matched_marginal_gap": matched_marginal_gap,
            "same_marginals_product_vs_entangled_state_gap": primitive_factorization_error,
        },
        "boundary": {
            "pass": classical_mi > 0.5 and classical_neg < 1e-10,
            "classical_correlated_mutual_info": classical_mi,
            "classical_correlated_negativity": classical_neg,
            "verdict": "correlation need not be entanglement; independence/factorization must be separately witnessed",
        },
    }
    result["all_pass"] = all(section["pass"] for section in (result["positive"], result["negative"], result["matched_control"], result["boundary"]))
    OUT.write_text(json.dumps(as_jsonable(result), indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"all_pass": result["all_pass"], "out": str(OUT)}, indent=2))
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
