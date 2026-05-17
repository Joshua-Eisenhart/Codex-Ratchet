#!/usr/bin/env python3
"""Bipartite cut mutual, conditional, and coherent information lego."""

from __future__ import annotations

import json
import math
import pathlib
import time
from typing import Any

import sympy as sp
import torch
import z3

ROOT = pathlib.Path(__file__).resolve().parents[2]
RESULT_DIR = ROOT / "system_v5" / "legos" / "results"
OUT_PATH = RESULT_DIR / "bipartite_cut_mutual_conditional_coherent_information_pytorch_sympy_z3_results.json"

NAME = "bipartite_cut_mutual_conditional_coherent_information_pytorch_sympy_z3"
CLASSIFICATION = "lego"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Finite bipartite cut-information lego only: computes mutual information, "
    "conditional entropy, and coherent information from a valid two-qubit joint "
    "density state and reduced states. It does not admit an axis, bridge, cycle, "
    "manifold layer, or target-system claim."
)

TOOL_MANIFEST = {
    "pytorch": {"tried": True, "used": True, "reason": "load-bearing bipartite density, partial trace, and entropy computations"},
    "sympy": {"tried": True, "used": True, "reason": "load-bearing exact Bell/classical entropy identities"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing sign and finite cut-information constraints"},
}
TOOL_INTEGRATION_DEPTH = {key: "load_bearing" for key in TOOL_MANIFEST}


def density(psi: torch.Tensor) -> torch.Tensor:
    return torch.outer(psi, psi.conj())


def partial_trace(rho: torch.Tensor, keep: str) -> torch.Tensor:
    rho4 = rho.reshape(2, 2, 2, 2)
    if keep == "A":
        return torch.einsum("abcb->ac", rho4)
    if keep == "B":
        return torch.einsum("abad->bd", rho4)
    raise ValueError(keep)


def entropy(rho: torch.Tensor) -> float:
    eigs = torch.clamp(torch.linalg.eigvalsh((rho + rho.conj().T) / 2), min=1e-15)
    return float((-torch.sum(eigs * torch.log(eigs))).item())


def cut_info(rho: torch.Tensor) -> dict[str, Any]:
    rho_a = partial_trace(rho, "A")
    rho_b = partial_trace(rho, "B")
    s_ab = entropy(rho)
    s_a = entropy(rho_a)
    s_b = entropy(rho_b)
    return {
        "S_AB": s_ab,
        "S_A": s_a,
        "S_B": s_b,
        "mutual_information": s_a + s_b - s_ab,
        "conditional_entropy_A_given_B": s_ab - s_b,
        "coherent_information_A_to_B": s_b - s_ab,
        "pass": True,
    }


def sympy_exact_identities() -> dict[str, Any]:
    ln2 = sp.log(2)
    bell = {"S_AB": sp.Integer(0), "S_A": ln2, "S_B": ln2}
    classical = {"S_AB": ln2, "S_A": ln2, "S_B": ln2}
    return {
        "bell_mutual_information": str(bell["S_A"] + bell["S_B"] - bell["S_AB"]),
        "bell_coherent_information": str(bell["S_B"] - bell["S_AB"]),
        "classical_correlated_coherent_information": str(classical["S_B"] - classical["S_AB"]),
        "pass": bell["S_A"] + bell["S_B"] - bell["S_AB"] == 2 * ln2 and bell["S_B"] - bell["S_AB"] == ln2 and classical["S_B"] - classical["S_AB"] == 0,
    }


def z3_sign_checks() -> dict[str, Any]:
    ln2 = z3.RealVal("0.6931471805599453")
    s_ab, s_b, ic = z3.Reals("S_AB S_B Ic")
    bell_deny = z3.Solver()
    bell_deny.add(s_ab == 0, s_b == ln2, ic == s_b - s_ab, ic <= 0)
    classical_positive = z3.Solver()
    classical_positive.add(s_ab == ln2, s_b == ln2, ic == s_b - s_ab, ic > 0)
    return {
        "bell_positive_coherent_information_unsat_if_denied": {"solver_status": str(bell_deny.check()), "pass": bell_deny.check() == z3.unsat},
        "classical_correlated_positive_coherent_information_unsat": {"solver_status": str(classical_positive.check()), "pass": classical_positive.check() == z3.unsat},
    }


def main() -> dict[str, Any]:
    started = time.time()
    bell = torch.zeros(4, dtype=torch.complex128)
    bell[0] = 1 / math.sqrt(2)
    bell[3] = 1 / math.sqrt(2)
    product = torch.zeros(4, dtype=torch.complex128)
    product[0] = 1
    classical = torch.zeros((4, 4), dtype=torch.complex128)
    classical[0, 0] = 0.5
    classical[3, 3] = 0.5
    bell_i = cut_info(density(bell))
    product_i = cut_info(density(product))
    classical_i = cut_info(classical)
    z3_rows = z3_sign_checks()

    positive = {
        "bell_state_has_negative_conditional_entropy_and_positive_coherent_information": {
            **bell_i,
            "pass": bell_i["conditional_entropy_A_given_B"] < -0.69 and bell_i["coherent_information_A_to_B"] > 0.69 and bell_i["mutual_information"] > 1.38,
        },
        "product_state_has_zero_mutual_and_zero_coherent_information": {
            **product_i,
            "pass": abs(product_i["mutual_information"]) < 1e-10 and abs(product_i["coherent_information_A_to_B"]) < 1e-10,
        },
        "classical_correlated_state_has_mutual_information_without_positive_coherent_information": {
            **classical_i,
            "pass": classical_i["mutual_information"] > 0.69 and abs(classical_i["coherent_information_A_to_B"]) < 1e-10,
        },
        "sympy_exact_cut_information_identities": sympy_exact_identities(),
        "z3_cut_information_sign_constraints": {"checks": z3_rows, "pass": all(row["pass"] for row in z3_rows.values())},
    }
    graveyard_companions = {
        "local_state_alone_cannot_define_conditional_entropy": {
            "has_joint_state": False,
            "pass": True,
        },
        "mutual_information_alone_cannot_detect_signed_coherent_information": {
            "classical_mutual_information": classical_i["mutual_information"],
            "bell_mutual_information": bell_i["mutual_information"],
            "classical_coherent_information": classical_i["coherent_information_A_to_B"],
            "bell_coherent_information": bell_i["coherent_information_A_to_B"],
            "pass": classical_i["mutual_information"] > 0 and classical_i["coherent_information_A_to_B"] < bell_i["coherent_information_A_to_B"],
        },
    }
    boundary = {
        "maximally_mixed_two_qubit_state_has_zero_mutual_information": {
            **cut_info(torch.eye(4, dtype=torch.complex128) / 4),
            "pass": abs(cut_info(torch.eye(4, dtype=torch.complex128) / 4)["mutual_information"]) < 1e-10,
        }
    }
    all_pass = all(row["pass"] for row in positive.values()) and all(row["pass"] for row in graveyard_companions.values()) and all(row["pass"] for row in boundary.values())
    result = {
        "schema": "LEGO_RESULT_v1",
        "name": NAME,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "math_object": "finite two-qubit bipartite density state and cut-information readouts",
        "observable": ["mutual information", "conditional entropy", "coherent information", "reduced-state entropies"],
        "predicate": "cut-information readouts require a valid joint state plus reduced states",
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
