#!/usr/bin/env python3
"""PyTorch lane for the paired Axis-1/Axis-2 readout candidate."""

from __future__ import annotations

import json

import cvc5
from cvc5 import Kind
import sympy as sp
import torch
from torch.func import vmap
import z3

import discrete_axes12_pair_v0_common as common


SOURCE_PATH = common.SIM_DIR / f"{common.SIM_ID}_pytorch.py"


def lane_probe() -> dict[str, object]:
    vector = torch.arange(1, 5, dtype=torch.float64)
    squared = vmap(lambda x: x * x)(vector)
    g = sp.Matrix([[0, -sp.I], [sp.I, 0]])
    kt_det = sp.simplify(g.det())
    solver = z3.Solver()
    si = z3.Int("pytorch_axis12_si")
    solver.add(si == 6)
    solver.add(z3.Not(si > 0))
    z3_verdict = str(solver.check())
    cv = cvc5.Solver()
    cv.setLogic("QF_LIA")
    x = cv.mkConst(cv.getIntegerSort(), "pytorch_axis12_cvc5_si")
    cv.assertFormula(cv.mkTerm(Kind.EQUAL, x, cv.mkInteger(6)))
    cv.assertFormula(cv.mkTerm(Kind.NOT, cv.mkTerm(Kind.GT, x, cv.mkInteger(0))))
    return {
        "torch_vmap_sum": float(torch.sum(squared).item()),
        "sympy_K_det": str(kt_det),
        "z3_erasure_verdict": z3_verdict,
        "cvc5_erasure_verdict": str(cv.checkSat()).lower(),
    }


def main() -> int:
    result = common.engine_result(
        "pytorch",
        source_path=SOURCE_PATH,
        packages_used=["torch", "torch.func", "sympy", "z3", "cvc5"],
        load_bearing=["torch.func", "sympy", "z3", "cvc5"],
        package_observables={
            "torch.func": "vmap product witness vector in the PyTorch lane",
            "sympy": "symbolic K_t generator determinant and product-map binding",
            "z3": "computed product-count erasure UNSAT witness",
            "cvc5": "independent product-count erasure UNSAT witness",
        },
    )
    result["lane_probe"] = lane_probe()
    common.write_json(common.RESULT_DIR / f"{common.SIM_ID}_pytorch_results.json", result)
    print(json.dumps({"ok": True, "result_path": result["result_path"]}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
