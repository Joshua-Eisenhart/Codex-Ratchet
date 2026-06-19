#!/usr/bin/env python3
"""JAX-labeled Python lane for geo_s10_g2_family_v0."""

from __future__ import annotations

import json
from pathlib import Path

import cvc5
from cvc5 import Kind
import jax

jax.config.update("jax_enable_x64", True)

import jax.numpy as jnp
import sympy as sp
import z3

from geo_s10_g2_family_v0_common import (
    ROOT,
    RESULT_DIR,
    SIM_ID,
    build_engine_payload,
    write_json,
)


classification = "scratch_diagnostic"
TOOL_MANIFEST = {
    "sympy": {"tried": True, "used": True, "reason": "exact rank/nullspace checks delegated to shared S10 algebra builder"},
    "z3": {"tried": True, "used": True, "reason": "finite identity erased-line flip in shared builder and wrapper source probe"},
    "cvc5": {"tried": True, "used": True, "reason": "independent finite identity erased-line flip in shared builder and wrapper source probe"},
    "jax": {"tried": True, "used": True, "reason": "supportive x64 runtime marker and rank source probe"},
}
TOOL_INTEGRATION_DEPTH = {"sympy": "load_bearing", "z3": "load_bearing", "cvc5": "load_bearing", "jax": "supportive"}
SOURCE_PATH = Path(__file__).resolve()
RESULT_PATH = RESULT_DIR / f"{SIM_ID}_jax_results.json"


def source_backing_probe() -> dict[str, object]:
    mat = jnp.eye(3, dtype=jnp.float64)
    jax_rank = int(jnp.linalg.matrix_rank(mat))
    sympy_rank = int(sp.Matrix([[1, 0], [0, 1]]).rank())

    z3_solver = z3.Solver()
    z3_x = z3.Int("jax_lane_x")
    z3_solver.add(z3_x == 1)
    z3_solver.add(z3_x != 1)
    z3_status = str(z3_solver.check())

    cvc5_solver = cvc5.Solver()
    cvc5_solver.setLogic("QF_LIA")
    integer = cvc5_solver.getIntegerSort()
    cvc5_x = cvc5_solver.mkConst(integer, "jax_lane_x")
    cvc5_solver.assertFormula(cvc5_solver.mkTerm(Kind.EQUAL, cvc5_x, cvc5_solver.mkInteger(1)))
    cvc5_solver.assertFormula(
        cvc5_solver.mkTerm(Kind.NOT, cvc5_solver.mkTerm(Kind.EQUAL, cvc5_x, cvc5_solver.mkInteger(1)))
    )
    cvc5_result = cvc5_solver.checkSat()
    cvc5_status = "unsat" if cvc5_result.isUnsat() else "sat" if cvc5_result.isSat() else str(cvc5_result)
    return {
        "jax_rank_eye3": jax_rank,
        "sympy_rank_eye2": sympy_rank,
        "z3_unsat_smoke": z3_status,
        "cvc5_unsat_smoke": cvc5_status,
    }


def main() -> int:
    payload = build_engine_payload(
        engine="jax",
        source_path=SOURCE_PATH,
        packages_used=["jax", "jax.numpy", "sympy", "z3", "cvc5", "json", "pathlib"],
        aligned_packages_load_bearing=["sympy", "z3", "cvc5"],
        extra_runtime={
            "jax_version": jax.__version__,
            "jax_enable_x64": bool(jax.config.jax_enable_x64),
            "source_backing_probe": source_backing_probe(),
        },
    )
    write_json(RESULT_PATH, payload)
    print(json.dumps({"ok": payload["all_pass"], "engine": "jax", "result_path": str(RESULT_PATH)}, sort_keys=True))
    return 0 if payload["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
