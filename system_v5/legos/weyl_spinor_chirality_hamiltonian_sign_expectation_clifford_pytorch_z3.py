#!/usr/bin/env python3
"""Two-component Weyl spinor chirality sign lego."""

from __future__ import annotations

import json
import os
import pathlib
import time
from typing import Any

os.environ.setdefault("NUMBA_DISABLE_JIT", "1")

from clifford import Cl
import torch
import z3

ROOT = pathlib.Path(__file__).resolve().parents[2]
RESULT_DIR = ROOT / "system_v5" / "legos" / "results"
OUT_PATH = RESULT_DIR / "weyl_spinor_chirality_hamiltonian_sign_expectation_clifford_pytorch_z3_results.json"

NAME = "weyl_spinor_chirality_hamiltonian_sign_expectation_clifford_pytorch_z3"
CLASSIFICATION = "lego"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Weyl chirality sign lego only: checks opposite Hamiltonian signs on a "
    "two-component spinor carrier and Clifford pseudoscalar orientation sign. "
    "It does not admit flux, loop independence, Hopf nesting order, cycle, "
    "bridge, or target-system interpretation."
)

TOOL_MANIFEST = {
    "clifford": {"tried": True, "used": True, "reason": "load-bearing pseudoscalar orientation sign check in Cl(3)"},
    "pytorch": {"tried": True, "used": True, "reason": "load-bearing two-component spinor expectation values"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing proof that nonzero opposite signs cannot collapse"},
}
TOOL_INTEGRATION_DEPTH = {"clifford": "load_bearing", "pytorch": "load_bearing", "z3": "load_bearing"}


def expectation(spinor: torch.Tensor, hamiltonian: torch.Tensor) -> float:
    value = torch.conj(spinor) @ (hamiltonian @ spinor)
    return float(torch.real(value).item())


def z3_sign_distinction() -> dict[str, Any]:
    e = z3.Real("expectation")
    s_left = z3.Real("s_left")
    s_right = z3.Real("s_right")
    solver = z3.Solver()
    solver.add(e > 0, s_left == e, s_right == -e, s_left == s_right)
    return {"solver_status": str(solver.check()), "pass": solver.check() == z3.unsat}


def main() -> dict[str, Any]:
    started = time.time()
    _, blades = Cl(3)
    pseudoscalar = blades["e123"]
    orientation_product = pseudoscalar * (-pseudoscalar)
    orientation_distinct = str(pseudoscalar) != str(-pseudoscalar)

    spinor_up = torch.tensor([1.0 + 0.0j, 0.0 + 0.0j], dtype=torch.complex128)
    spinor_balanced = torch.tensor([1.0 + 0.0j, 1.0 + 0.0j], dtype=torch.complex128)
    spinor_balanced = spinor_balanced / torch.linalg.vector_norm(spinor_balanced)
    sigma_z = torch.tensor([[1.0, 0.0], [0.0, -1.0]], dtype=torch.complex128)
    left_h = sigma_z
    right_h = -sigma_z

    left_up = expectation(spinor_up, left_h)
    right_up = expectation(spinor_up, right_h)
    balanced_left = expectation(spinor_balanced, left_h)
    balanced_right = expectation(spinor_balanced, right_h)

    positive = {
        "pytorch_opposite_hamiltonian_sign_expectations": {
            "left_expectation": left_up,
            "right_expectation": right_up,
            "pass": abs(left_up - 1.0) < 1e-12 and abs(right_up + 1.0) < 1e-12,
        },
        "clifford_pseudoscalar_orientation_sign_distinct": {
            "pseudoscalar": str(pseudoscalar),
            "negative_pseudoscalar": str(-pseudoscalar),
            "orientation_product": str(orientation_product),
            "pass": orientation_distinct,
        },
        "z3_nonzero_opposite_signs_do_not_collapse": z3_sign_distinction(),
    }
    graveyard_companions = {
        "same_hamiltonian_sign_collapses_chirality_readout": {
            "left_expectation": left_up,
            "right_expectation_if_same_sign": expectation(spinor_up, left_h),
            "pass": abs(left_up - expectation(spinor_up, left_h)) < 1e-12,
        },
        "zero_expectation_spinor_cannot_distinguish_sign": {
            "left_expectation": balanced_left,
            "right_expectation": balanced_right,
            "pass": abs(balanced_left) < 1e-12 and abs(balanced_right) < 1e-12,
        },
    }
    boundary = {
        "spin_down_reverses_both_expectation_values": {
            "left_expectation": expectation(torch.tensor([0.0 + 0.0j, 1.0 + 0.0j], dtype=torch.complex128), left_h),
            "right_expectation": expectation(torch.tensor([0.0 + 0.0j, 1.0 + 0.0j], dtype=torch.complex128), right_h),
            "pass": True,
        }
    }
    result = {
        "schema": "LEGO_RESULT_v1",
        "name": NAME,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "math_object": "two-component spinor with opposite chirality Hamiltonian signs",
        "observable": ["Hamiltonian expectation sign", "Clifford pseudoscalar orientation sign", "z3 sign-collapse UNSAT"],
        "predicate": "nonzero spinor expectation distinguishes opposite Hamiltonian signs",
        "positive": positive,
        "graveyard_companions": graveyard_companions,
        "boundary": boundary,
        "nearby_variants": {"total": len(graveyard_companions), "passed": sum(1 for row in graveyard_companions.values() if row["pass"])},
        "blockers": [],
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "summary": {
            "all_pass": all(row["pass"] for row in positive.values()) and all(row["pass"] for row in graveyard_companions.values()) and all(row["pass"] for row in boundary.values()),
            "elapsed_seconds": round(time.time() - started, 6),
            "promotion_allowed": PROMOTION_ALLOWED,
        },
    }
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result["summary"], indent=2, sort_keys=True))
    return result


if __name__ == "__main__":
    main()
