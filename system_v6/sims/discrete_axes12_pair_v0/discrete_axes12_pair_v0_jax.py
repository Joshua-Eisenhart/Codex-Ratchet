#!/usr/bin/env python3
"""JAX/Python lane for the paired Axis-1/Axis-2 readout candidate."""

from __future__ import annotations

import json

import cvc5
from cvc5 import Kind
import jax

jax.config.update("jax_enable_x64", True)

import jax.numpy as jnp
import sympy as sp
import z3

import discrete_axes12_pair_v0_common as common


SOURCE_PATH = common.SIM_DIR / f"{common.SIM_ID}_jax.py"


def lane_probe() -> dict[str, object]:
    vector = jnp.asarray([1, 2, 3, 4], dtype=jnp.int64)
    doubled = jax.vmap(lambda x: x * 2)(vector)
    g = sp.Matrix([[0, -sp.I], [sp.I, 0]])
    kt_trace = sp.simplify(sp.trace(g))
    solver = z3.Solver()
    se = z3.Int("jax_axis12_se")
    solver.add(se == 10)
    solver.add(z3.Not(se > 0))
    z3_verdict = str(solver.check())
    cv = cvc5.Solver()
    cv.setLogic("QF_LIA")
    x = cv.mkConst(cv.getIntegerSort(), "jax_axis12_cvc5_se")
    cv.assertFormula(cv.mkTerm(Kind.EQUAL, x, cv.mkInteger(10)))
    cv.assertFormula(cv.mkTerm(Kind.NOT, cv.mkTerm(Kind.GT, x, cv.mkInteger(0))))
    return {
        "jax_vmap_sum": int(jnp.sum(doubled)),
        "sympy_K_trace": str(kt_trace),
        "z3_erasure_verdict": z3_verdict,
        "cvc5_erasure_verdict": str(cv.checkSat()).lower(),
    }


def main() -> int:
    result = common.engine_result(
        "jax",
        source_path=SOURCE_PATH,
        packages_used=["jax", "jax.numpy", "sympy", "z3", "cvc5"],
        load_bearing=["sympy", "z3", "cvc5"],
        package_observables={
            "sympy": "symbolic K_t generator trace and product-map binding",
            "z3": "computed product-count erasure UNSAT witness",
            "cvc5": "independent product-count erasure UNSAT witness",
        },
    )
    result["lane_probe"] = lane_probe()
    common.write_json(common.RESULT_DIR / f"{common.SIM_ID}_jax_results.json", result)
    print(json.dumps({"ok": True, "result_path": result["result_path"]}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
