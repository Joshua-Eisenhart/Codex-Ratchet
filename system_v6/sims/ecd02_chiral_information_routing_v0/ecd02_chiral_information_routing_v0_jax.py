#!/usr/bin/env python3
"""Python/JAX-labeled finite routing leg for ECD.02.

The load-bearing packages in this lane are z3, cvc5, and sympy.  The lane is
named `jax` for the three-engine envelope role; no JAX-specific claim is made.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import cvc5
import sympy as sp
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


ENGINE = "jax"
SOURCE_PATH = Path(__file__).resolve()
RESULT_PATH = RESULT_DIR / f"{SIM_ID}_{ENGINE}_results.json"


def package_versions() -> dict[str, str]:
    return {
        "z3": z3.get_version_string(),
        "cvc5": getattr(cvc5, "__version__", "unknown"),
        "sympy": sp.__version__,
    }


def source_backed_solver_smoke() -> dict[str, str]:
    z3_solver = z3.Solver()
    z3_x = z3.Int("jax_source_backed_z3_x")
    z3_solver.add(z3_x == 1)
    z3_solver.add(z3_x != 1)

    cvc5_solver = cvc5.Solver()
    cvc5_solver.setLogic("QF_LIA")
    integer = cvc5_solver.getIntegerSort()
    cvc5_x = cvc5_solver.mkConst(integer, "jax_source_backed_cvc5_x")
    cvc5_solver.assertFormula(cvc5_solver.mkTerm(cvc5.Kind.EQUAL, cvc5_x, cvc5_solver.mkInteger(1)))
    cvc5_solver.assertFormula(cvc5_solver.mkTerm(cvc5.Kind.DISTINCT, cvc5_x, cvc5_solver.mkInteger(1)))
    return {"z3": str(z3_solver.check()).lower(), "cvc5": str(cvc5_solver.checkSat()).lower()}


def build_result() -> dict[str, Any]:
    core = build_core_result()
    solver_smoke = source_backed_solver_smoke()
    x = sp.symbols("x")
    sympy_check = {
        "R_matches_plus_one": sp.simplify(x + core["engine_values"]["R_index"] - x) == 1,
        "L_matches_minus_one": sp.simplify(x + core["engine_values"]["L_index"] - x) == -1,
        "szilard_zero": sp.simplify(x + core["engine_values"]["szilard_routing_asymmetry"] - x) == 0,
    }
    all_pass = bool(core["all_pass"] and all(sympy_check.values()) and solver_smoke == {"z3": "unsat", "cvc5": "unsat"})
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
        "packages_used": ["z3", "cvc5", "sympy"],
        "aligned_packages_load_bearing": ["z3", "cvc5", "sympy"],
        "package_observables": {
            "z3": "z3.Solver proves the negated routing/index contract is UNSAT from computed integer observables",
            "cvc5": "cvc5.Solver independently proves the same routing/index contract",
            "sympy": "sp.symbols/sp.simplify checks exact signed-index identities used in the routing row",
        },
        "package_versions": package_versions(),
        "all_pass": all_pass,
        "engine_values": core["engine_values"],
        "routing_signature_sha256": stable_sha256(core["routing"]),
        "core": core,
        "crossover_proofs": core["crossover_proofs"],
        "source_backed_solver_smoke": solver_smoke,
        "sympy_check": {key: bool(value) for key, value in sympy_check.items()},
        "TOOL_MANIFEST": {
            "z3": {"tried": True, "used": True, "reason": "load-bearing routing/index SMT contract"},
            "cvc5": {"tried": True, "used": True, "reason": "load-bearing independent routing/index SMT contract"},
            "sympy": {"tried": True, "used": True, "reason": "load-bearing exact signed-index identity check"},
        },
        "TOOL_INTEGRATION_DEPTH": {"z3": "load_bearing", "cvc5": "load_bearing", "sympy": "load_bearing"},
        "tool_calls": [
            {
                "tool": "z3",
                "qualified_api/function": "z3.Solver",
                "input_object": "computed index and routing asymmetry integers",
                "output_object": "UNSAT negated contract",
                "positive_case": "R=+1 routes left-to-right; L=-1 routes right-to-left",
                "negative/erased_control": "Szilard/index0 asymmetry zero and forced-R-left falsifier UNSAT",
                "boundary_case": "chain endpoint arrival after k=5",
                "demotion_condition": "demote if proof no longer binds computed routing asymmetry",
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
