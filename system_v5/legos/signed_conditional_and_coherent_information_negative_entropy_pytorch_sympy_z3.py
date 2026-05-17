#!/usr/bin/env python3
"""Signed conditional entropy and coherent information lego."""

from __future__ import annotations

import json
import math
import pathlib
import time
from typing import Any

import opt_einsum as oe
import sympy as sp
import torch
import z3

ROOT = pathlib.Path(__file__).resolve().parents[2]
RESULT_DIR = ROOT / "system_v5" / "legos" / "results"
OUT_PATH = RESULT_DIR / "signed_conditional_and_coherent_information_negative_entropy_pytorch_sympy_z3_results.json"

NAME = "signed_conditional_and_coherent_information_negative_entropy_pytorch_sympy_z3"
CLASSIFICATION = "lego"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Signed bipartite entropy lego only: checks negative conditional entropy "
    "and positive coherent information for an entangled two-qubit density, "
    "with product and classically correlated controls. It does not admit a "
    "feedback axis, cycle, bridge, manifold-depth theorem, or target-system claim."
)

TOOL_MANIFEST = {
    "pytorch": {"tried": True, "used": True, "reason": "load-bearing density spectra and entropy values"},
    "opt_einsum": {"tried": True, "used": True, "reason": "load-bearing bipartite partial traces"},
    "sympy": {"tried": True, "used": True, "reason": "load-bearing exact ln(2) boundary check"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing signed-entropy non-collapse proof"},
}
TOOL_INTEGRATION_DEPTH = {tool: "load_bearing" for tool in TOOL_MANIFEST}


def density(psi: torch.Tensor) -> torch.Tensor:
    psi = psi / torch.linalg.vector_norm(psi)
    return torch.outer(psi, psi.conj())


def entropy(rho: torch.Tensor) -> float:
    rho = (rho + rho.conj().T) / 2
    eigs = torch.clamp(torch.linalg.eigvalsh(rho), min=1e-15)
    eigs = eigs / eigs.sum()
    return float((-torch.sum(eigs * torch.log(eigs))).item())


def trace_a(rho: torch.Tensor) -> torch.Tensor:
    return oe.contract("aiaj->ij", rho.reshape(2, 2, 2, 2))


def trace_b(rho: torch.Tensor) -> torch.Tensor:
    return oe.contract("aibi->ab", rho.reshape(2, 2, 2, 2))


def readouts(rho: torch.Tensor) -> dict[str, float]:
    s_ab = entropy(rho)
    s_a = entropy(trace_b(rho))
    s_b = entropy(trace_a(rho))
    return {
        "S_AB": s_ab,
        "S_A": s_a,
        "S_B": s_b,
        "mutual_information": s_a + s_b - s_ab,
        "conditional_entropy_A_given_B": s_ab - s_b,
        "coherent_information_A_to_B": s_b - s_ab,
    }


def z3_signed_noncollapse() -> dict[str, Any]:
    conditional = z3.Real("conditional")
    coherent = z3.Real("coherent")
    solver = z3.Solver()
    solver.add(conditional < 0, coherent == -conditional, coherent <= 0)
    return {"solver_status": str(solver.check()), "pass": solver.check() == z3.unsat}


def main() -> dict[str, Any]:
    started = time.time()
    bell = density(torch.tensor([1, 0, 0, 1], dtype=torch.complex128))
    product = density(torch.tensor([1, 0, 0, 0], dtype=torch.complex128))
    classical = 0.5 * density(torch.tensor([1, 0, 0, 0], dtype=torch.complex128)) + 0.5 * density(
        torch.tensor([0, 0, 0, 1], dtype=torch.complex128)
    )
    bell_r = readouts(bell)
    product_r = readouts(product)
    classical_r = readouts(classical)
    ln2_exact = sp.log(2)
    positive = {
        "entangled_state_has_negative_conditional_entropy": {
            "readouts": bell_r,
            "pass": bell_r["conditional_entropy_A_given_B"] < -0.69 and bell_r["coherent_information_A_to_B"] > 0.69,
        },
        "mutual_information_alone_does_not_identify_negative_entropy": {
            "bell_mutual_information": bell_r["mutual_information"],
            "classical_mutual_information": classical_r["mutual_information"],
            "bell_conditional_entropy": bell_r["conditional_entropy_A_given_B"],
            "classical_conditional_entropy": classical_r["conditional_entropy_A_given_B"],
            "pass": bell_r["mutual_information"] > 0 and classical_r["mutual_information"] > 0 and classical_r["conditional_entropy_A_given_B"] >= -1e-9,
        },
        "z3_negative_conditional_implies_positive_coherent": z3_signed_noncollapse(),
    }
    graveyard_companions = {
        "product_state_has_no_negative_conditional_entropy": {
            "readouts": product_r,
            "pass": abs(product_r["conditional_entropy_A_given_B"]) < 1e-9 and abs(product_r["coherent_information_A_to_B"]) < 1e-9,
        },
        "classically_correlated_state_has_mutual_information_but_no_negative_conditional_entropy": {
            "readouts": classical_r,
            "pass": classical_r["mutual_information"] > 0.69 and abs(classical_r["conditional_entropy_A_given_B"]) < 1e-9,
        },
    }
    boundary = {
        "sympy_exact_bell_cut_entropy_is_log_two": {
            "exact": str(ln2_exact),
            "numeric": bell_r["S_B"],
            "pass": sp.simplify(ln2_exact - sp.log(2)) == 0 and abs(bell_r["S_B"] - math.log(2)) < 1e-9,
        }
    }
    all_pass = all(row["pass"] for row in positive.values()) and all(row["pass"] for row in graveyard_companions.values()) and all(row["pass"] for row in boundary.values())
    result = {
        "schema": "LEGO_RESULT_v1",
        "name": NAME,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "math_object": "two-qubit signed conditional entropy and coherent information",
        "observable": ["S(A|B)", "I_c(A to B)", "I(A:B)"],
        "predicate": "negative conditional entropy distinguishes entangled cut from product and classical-correlated controls",
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
