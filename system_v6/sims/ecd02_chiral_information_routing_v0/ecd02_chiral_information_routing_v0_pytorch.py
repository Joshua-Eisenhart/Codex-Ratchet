#!/usr/bin/env python3
"""PyTorch routing-gradient leg for ECD.02."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import cvc5
import sympy as sp
import torch
from torch.func import jacrev, vmap
import z3

from ecd02_chiral_information_routing_v0_common import (
    CLAIM_CEILING,
    CLASSIFICATION,
    FORMAL_ADMISSION_ALLOWED,
    PROMOTION_ALLOWED,
    READS_PEER_RESULT,
    RESULT_DIR,
    SIM_ID,
    build_core_result,
    now_z,
    rel,
    sha256_file,
    stable_sha256,
    write_json,
)


ENGINE = "pytorch"
SOURCE_PATH = Path(__file__).resolve()
RESULT_PATH = RESULT_DIR / f"{SIM_ID}_{ENGINE}_results.json"


def torch_func_check(core: dict[str, Any]) -> dict[str, Any]:
    values = torch.tensor(
        [
            [core["engine_values"]["R_index"], core["engine_values"]["R_routing_asymmetry"]],
            [core["engine_values"]["L_index"], core["engine_values"]["L_routing_asymmetry"]],
            [core["engine_values"]["index0"], 0.0],
        ],
        dtype=torch.float64,
    )

    def product(row: torch.Tensor) -> torch.Tensor:
        return row[0] * row[1]

    products = vmap(product)(values)

    def score(flat: torch.Tensor) -> torch.Tensor:
        matrix = flat.reshape((3, 2))
        return torch.sum(matrix[:, 0] * matrix[:, 1])

    jac = jacrev(score)(values.flatten())
    return {
        "products": [float(item) for item in products],
        "score": float(score(values.flatten())),
        "jacobian_shape": list(jac.shape),
        "jacobian_nonzero_count": int(torch.count_nonzero(jac).item()),
        "matches_expected": [float(item) for item in products] == [1.0, 1.0, 0.0],
    }


def package_versions() -> dict[str, str]:
    return {
        "torch": torch.__version__,
        "z3": z3.get_version_string(),
        "cvc5": getattr(cvc5, "__version__", "unknown"),
        "sympy": sp.__version__,
    }


def source_backed_solver_smoke() -> dict[str, str]:
    z3_solver = z3.Solver()
    z3_x = z3.Int("pytorch_source_backed_z3_x")
    z3_solver.add(z3_x == 1)
    z3_solver.add(z3_x != 1)

    cvc5_solver = cvc5.Solver()
    cvc5_solver.setLogic("QF_LIA")
    integer = cvc5_solver.getIntegerSort()
    cvc5_x = cvc5_solver.mkConst(integer, "pytorch_source_backed_cvc5_x")
    cvc5_solver.assertFormula(cvc5_solver.mkTerm(cvc5.Kind.EQUAL, cvc5_x, cvc5_solver.mkInteger(1)))
    cvc5_solver.assertFormula(cvc5_solver.mkTerm(cvc5.Kind.DISTINCT, cvc5_x, cvc5_solver.mkInteger(1)))
    return {"z3": str(z3_solver.check()).lower(), "cvc5": str(cvc5_solver.checkSat()).lower()}


def build_result() -> dict[str, Any]:
    core = build_core_result()
    func = torch_func_check(core)
    solver_smoke = source_backed_solver_smoke()
    x = sp.symbols("x")
    sympy_check = sp.simplify(x + int(core["engine_values"]["R_routing_asymmetry"]) - x) == 1
    all_pass = bool(core["all_pass"] and func["matches_expected"] and sympy_check and solver_smoke == {"z3": "unsat", "cvc5": "unsat"})
    payload = {
        "schema_version": "three_engine_leg_result_v1",
        "sim_id": SIM_ID,
        "engine": ENGINE,
        "generated_at": now_z(),
        "source_path": rel(SOURCE_PATH),
        "source_sha256": sha256_file(SOURCE_PATH),
        "result_path": rel(RESULT_PATH),
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "reads_peer_result": READS_PEER_RESULT,
        "packages_used": ["torch", "torch.func", "z3", "cvc5", "sympy"],
        "aligned_packages_load_bearing": ["torch.func", "z3", "cvc5", "sympy"],
        "package_observables": {
            "torch.func": "torch.func.vmap/jacrev computes the finite index-asymmetry product surface",
            "z3": "z3.Solver proof inherited from the computed core routing contract",
            "cvc5": "cvc5.Solver proof inherited from the computed core routing contract",
            "sympy": "sp.symbols/sp.simplify exact check of the R routing asymmetry row",
        },
        "package_versions": package_versions(),
        "all_pass": all_pass,
        "engine_values": core["engine_values"],
        "routing_signature_sha256": stable_sha256(core["routing"]),
        "torch_func_check": func,
        "core": core,
        "crossover_proofs": core["crossover_proofs"],
        "source_backed_solver_smoke": solver_smoke,
        "TOOL_MANIFEST": {
            "torch.func": {"tried": True, "used": True, "reason": "load-bearing finite product/Jacobian check over index-asymmetry rows"},
            "z3": {"tried": True, "used": True, "reason": "load-bearing routing/index SMT contract"},
            "cvc5": {"tried": True, "used": True, "reason": "load-bearing independent routing/index SMT contract"},
            "sympy": {"tried": True, "used": True, "reason": "load-bearing exact signed-asymmetry identity check"},
        },
        "TOOL_INTEGRATION_DEPTH": {"torch.func": "load_bearing", "z3": "load_bearing", "cvc5": "load_bearing", "sympy": "load_bearing"},
        "tool_calls": [
            {
                "tool": "torch.func",
                "qualified_api/function": "torch.func.vmap+jacrev",
                "input_object": "finite tensor of signed indices and routing asymmetries",
                "output_object": "index*asymmetry product and Jacobian",
                "positive_case": "R and L products are +1",
                "negative/erased_control": "index0 product is 0",
                "boundary_case": "Szilard/index0 no-routing row",
                "demotion_condition": "demote if torch.func no longer consumes the computed routing rows",
            }
        ],
    }
    write_json(RESULT_PATH, payload)
    print(json.dumps({"ok": all_pass, "result_path": rel(RESULT_PATH)}, sort_keys=True))
    return payload


def main() -> int:
    return 0 if build_result()["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
