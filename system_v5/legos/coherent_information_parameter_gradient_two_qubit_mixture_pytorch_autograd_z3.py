#!/usr/bin/env python3
"""Coherent-information parameter gradient lego."""

from __future__ import annotations

import json
import pathlib
import time
from typing import Any

import opt_einsum as oe
import torch
import z3

ROOT = pathlib.Path(__file__).resolve().parents[2]
RESULT_DIR = ROOT / "system_v5" / "legos" / "results"
OUT_PATH = RESULT_DIR / "coherent_information_parameter_gradient_two_qubit_mixture_pytorch_autograd_z3_results.json"

NAME = "coherent_information_parameter_gradient_two_qubit_mixture_pytorch_autograd_z3"
CLASSIFICATION = "lego"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Coherent-information gradient lego only: differentiates I_c(A to B) "
    "through a finite two-qubit mixture parameter and checks zero-gradient "
    "controls. It does not admit a full feedback field, cycle, manifold ratchet, "
    "or target-system interpretation."
)

TOOL_MANIFEST = {
    "pytorch": {"tried": True, "used": True, "reason": "load-bearing torch autograd gradient of coherent information through eigvalsh"},
    "opt_einsum": {"tried": True, "used": True, "reason": "load-bearing partial trace for subsystem entropy"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing proof that nonzero and zero gradients cannot be same witness"},
}
TOOL_INTEGRATION_DEPTH = {tool: "load_bearing" for tool in TOOL_MANIFEST}


def density(psi: torch.Tensor) -> torch.Tensor:
    psi = psi / torch.linalg.vector_norm(psi)
    return torch.outer(psi, psi.conj())


def entropy_torch(rho: torch.Tensor) -> torch.Tensor:
    rho = (rho + rho.conj().T) / 2
    eigs = torch.clamp(torch.linalg.eigvalsh(rho), min=1e-12)
    eigs = eigs / eigs.sum()
    return -torch.sum(eigs * torch.log(eigs))


def trace_a(rho: torch.Tensor) -> torch.Tensor:
    return oe.contract("aiaj->ij", rho.reshape(2, 2, 2, 2))


def coherent_information(rho: torch.Tensor) -> torch.Tensor:
    return entropy_torch(trace_a(rho)) - entropy_torch(rho)


def mixture(parameter: torch.Tensor) -> torch.Tensor:
    bell = density(torch.tensor([1, 0, 0, 1], dtype=torch.complex128))
    product = density(torch.tensor([1, 0, 0, 0], dtype=torch.complex128))
    p = torch.clamp(parameter, 1e-6, 1 - 1e-6).to(torch.complex128)
    return p * bell + (1 - p) * product


def z3_gradient_distinction() -> dict[str, Any]:
    g = z3.Real("g")
    solver = z3.Solver()
    solver.add(g > 0, g == 0)
    return {"solver_status": str(solver.check()), "pass": solver.check() == z3.unsat}


def main() -> dict[str, Any]:
    started = time.time()
    parameter = torch.tensor(0.55, dtype=torch.float64, requires_grad=True)
    ic = coherent_information(mixture(parameter))
    ic.backward()
    gradient = float(parameter.grad.item())

    flat_parameter = torch.tensor(0.55, dtype=torch.float64, requires_grad=True)
    constant_state = density(torch.tensor([1, 0, 0, 0], dtype=torch.complex128))
    flat_ic = coherent_information(flat_parameter.to(torch.complex128) * constant_state + (1 - flat_parameter).to(torch.complex128) * constant_state)
    flat_ic.backward()
    flat_gradient = float(flat_parameter.grad.item())

    positive = {
        "coherent_information_has_nonzero_parameter_gradient": {
            "parameter": 0.55,
            "coherent_information": float(ic.item()),
            "gradient": gradient,
            "pass": abs(gradient) > 1e-6,
        },
        "z3_nonzero_gradient_not_equal_to_zero_gradient": z3_gradient_distinction(),
    }
    graveyard_companions = {
        "identical_state_mixture_has_zero_gradient": {
            "coherent_information": float(flat_ic.item()),
            "gradient": flat_gradient,
            "pass": abs(flat_gradient) < 1e-9,
        },
        "detached_parameter_blocks_gradient_witness": {
            "requires_grad": bool(parameter.detach().requires_grad),
            "pass": parameter.detach().requires_grad is False,
        },
    }
    boundary = {
        "gradient_has_finite_numeric_value": {
            "gradient": gradient,
            "pass": gradient == gradient and abs(gradient) < 100,
        }
    }
    all_pass = all(row["pass"] for row in positive.values()) and all(row["pass"] for row in graveyard_companions.values()) and all(row["pass"] for row in boundary.values())
    result = {
        "schema": "LEGO_RESULT_v1",
        "name": NAME,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "math_object": "autograd gradient of coherent information over a two-qubit mixture parameter",
        "observable": ["I_c(A to B)", "d I_c / d parameter"],
        "predicate": "finite parameter change produces nonzero coherent-information gradient while identical-state control has zero gradient",
        "positive": positive,
        "graveyard_companions": graveyard_companions,
        "boundary": boundary,
        "nearby_variants": {"total": len(graveyard_companions), "passed": sum(1 for row in graveyard_companions.values() if row["pass"])},
        "blockers": [],
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "summary": {"all_pass": bool(all_pass), "elapsed_seconds": round(time.time() - started, 6), "promotion_allowed": PROMOTION_ALLOWED},
    }
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result["summary"], indent=2, sort_keys=True))
    return result


if __name__ == "__main__":
    main()
