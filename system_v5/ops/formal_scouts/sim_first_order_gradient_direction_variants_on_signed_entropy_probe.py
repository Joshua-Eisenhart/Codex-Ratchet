#!/usr/bin/env python3
"""First-order gradient direction variants on signed entropy."""

from __future__ import annotations

import json
import math
import pathlib
import time
from typing import Any

import opt_einsum as oe
import torch
import z3

ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
OUT_PATH = RESULT_DIR / "first_order_gradient_direction_variants_on_signed_entropy_probe_results.json"

NAME = "first_order_gradient_direction_variants_on_signed_entropy_probe"
CLASSIFICATION = "formal_scout"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: compares first-order gradient descent, ascent, "
    "sign-flipped, and zero-gradient variants on unsigned entropy and coherent "
    "information for a finite dynamic state family. It does not admit any "
    "downstream label, cycle, bridge, final feedback geometry, or target-system claim."
)

TOOL_MANIFEST = {
    "pytorch_autograd": {"tried": True, "used": True, "reason": "load-bearing objective gradients and update steps"},
    "opt_einsum": {"tried": True, "used": True, "reason": "load-bearing partial trace for coherent information"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing direction-collapse impossibility checks"},
}
TOOL_INTEGRATION_DEPTH = {tool: "load_bearing" for tool in TOOL_MANIFEST}


def dynamic_state(theta: torch.Tensor) -> torch.Tensor:
    psi = torch.zeros(16, dtype=torch.complex128)
    psi[0] = torch.cos(theta).to(torch.complex128)
    psi[-1] = torch.sin(theta).to(torch.complex128)
    return psi / torch.linalg.vector_norm(psi)


def density(psi: torch.Tensor) -> torch.Tensor:
    return torch.outer(psi, psi.conj())


def entropy(rho: torch.Tensor) -> torch.Tensor:
    rho = (rho + rho.conj().T) / 2
    eigs = torch.clamp(torch.linalg.eigvalsh(rho), min=1e-12)
    eigs = eigs / eigs.sum()
    return -torch.sum(eigs * torch.log(eigs))


def trace_first_qubit(rho: torch.Tensor) -> torch.Tensor:
    return oe.contract("aibi->ab", rho.reshape(2, 8, 2, 8))


def objectives(theta: torch.Tensor) -> dict[str, torch.Tensor]:
    rho = density(dynamic_state(theta))
    reduced = trace_first_qubit(rho)
    unsigned = entropy(reduced)
    coherent = unsigned - entropy(rho)
    return {"unsigned_cut_entropy": unsigned, "coherent_information": coherent}


def gradient_of(theta_value: float, objective_name: str) -> tuple[float, float]:
    theta = torch.tensor(theta_value, dtype=torch.float64, requires_grad=True)
    objective = objectives(theta)[objective_name]
    objective.backward()
    return float(objective.item()), float(theta.grad.item())


def step(theta_value: float, objective_name: str, direction: str, step_size: float = 0.08) -> dict[str, float | str]:
    before, grad = gradient_of(theta_value, objective_name)
    if direction == "descent":
        theta_after = theta_value - step_size * grad
    elif direction == "ascent":
        theta_after = theta_value + step_size * grad
    elif direction == "sign_flipped_descent":
        theta_after = theta_value + step_size * grad
    elif direction == "zero_gradient_hold":
        theta_after = theta_value
    else:
        raise ValueError(direction)
    after, _ = gradient_of(theta_after, objective_name)
    return {
        "objective": objective_name,
        "direction": direction,
        "theta_before": theta_value,
        "theta_after": theta_after,
        "value_before": before,
        "value_after": after,
        "delta": after - before,
        "gradient": grad,
    }


def z3_ascent_descent_distinct() -> dict[str, Any]:
    grad = z3.Real("grad")
    step_size = z3.Real("step_size")
    descent_delta = z3.Real("descent_delta")
    ascent_delta = z3.Real("ascent_delta")
    solver = z3.Solver()
    solver.add(grad > 0, step_size > 0)
    solver.add(descent_delta == -step_size * grad * grad)
    solver.add(ascent_delta == step_size * grad * grad)
    solver.add(descent_delta == ascent_delta)
    return {"solver_status": str(solver.check()), "pass": solver.check() == z3.unsat}


def main() -> dict[str, Any]:
    started = time.time()
    theta = 0.73
    unsigned_descent = step(theta, "unsigned_cut_entropy", "descent")
    unsigned_ascent = step(theta, "unsigned_cut_entropy", "ascent")
    coherent_descent = step(theta, "coherent_information", "descent")
    coherent_ascent = step(theta, "coherent_information", "ascent")
    hold = step(theta, "coherent_information", "zero_gradient_hold")
    flipped = step(theta, "coherent_information", "sign_flipped_descent")

    positive = {
        "gradient_descent_decreases_unsigned_cut_entropy": {
            "step": unsigned_descent,
            "pass": unsigned_descent["delta"] < 0,
        },
        "gradient_ascent_increases_unsigned_cut_entropy": {
            "step": unsigned_ascent,
            "pass": unsigned_ascent["delta"] > 0,
        },
        "coherent_information_ascent_increases_signed_readout": {
            "step": coherent_ascent,
            "pass": coherent_ascent["delta"] > 0,
        },
        "coherent_information_descent_decreases_signed_readout": {
            "step": coherent_descent,
            "pass": coherent_descent["delta"] < 0,
        },
        "z3_ascent_and_descent_do_not_collapse_for_nonzero_gradient": z3_ascent_descent_distinct(),
    }
    graveyard_companions = {
        "zero_gradient_hold_changes_no_objective_value": {
            "step": hold,
            "pass": abs(hold["delta"]) < 1e-12,
        },
        "sign_flipped_descent_matches_ascent_not_descent": {
            "flipped": flipped,
            "coherent_ascent_delta": coherent_ascent["delta"],
            "coherent_descent_delta": coherent_descent["delta"],
            "pass": abs(flipped["delta"] - coherent_ascent["delta"]) < 1e-12 and abs(flipped["delta"] - coherent_descent["delta"]) > 1e-6,
        },
        "stationary_boundary_near_max_entropy_has_small_gradient": {
            "theta": math.pi / 4,
            "gradient": gradient_of(math.pi / 4, "coherent_information")[1],
            "pass": abs(gradient_of(math.pi / 4, "coherent_information")[1]) < 1e-5,
        },
    }
    boundary = {
        "initial_gradient_is_nonzero": {
            "coherent_gradient": gradient_of(theta, "coherent_information")[1],
            "pass": abs(gradient_of(theta, "coherent_information")[1]) > 1e-6,
        }
    }
    all_pass = all(row["pass"] for row in positive.values()) and all(row["pass"] for row in graveyard_companions.values()) and all(row["pass"] for row in boundary.values())
    result = {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "name": NAME,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "math_object": "first-order gradient direction variants over unsigned cut entropy and coherent information",
        "operator_variants": [
            "gradient_descent_on_unsigned_cut_entropy",
            "gradient_ascent_on_unsigned_cut_entropy",
            "gradient_descent_on_coherent_information",
            "gradient_ascent_on_coherent_information",
            "sign_flipped_gradient_descent_on_coherent_information",
            "zero_gradient_hold",
        ],
        "positive": positive,
        "graveyard_companions": graveyard_companions,
        "boundary": boundary,
        "nearby_variants": {"total": len(graveyard_companions), "passed": sum(1 for row in graveyard_companions.values() if row["pass"])},
        "blockers": [],
        "open_choices": [
            "downstream labels can map to these operators later, but executable names stay mathematical",
            "next version should run the same variants on multi-parameter geometry, not one theta only",
        ],
        "why_not_v4_probes": "This is a clean v5 gradient-direction scout and should not add to the mixed v4 probe estate.",
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
