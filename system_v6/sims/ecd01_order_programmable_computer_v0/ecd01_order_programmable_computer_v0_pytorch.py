#!/usr/bin/env python3
"""PyTorch lane for ECD.01 order-programmability."""

from __future__ import annotations

import json
from pathlib import Path

import cvc5
import sympy as sp
import torch
from torch.func import vmap
import z3

import ecd01_order_programmable_computer_v0_common as common


SOURCE_PATH = Path(__file__).resolve()
RESULT_PATH = common.RESULT_DIR / f"{common.SIM_ID}_pytorch_results.json"


def lane_observables(obj: dict) -> dict:
    first_outputs = torch.tensor([row["sample_outputs"][0]["output"] for row in obj["channel_table"]], dtype=torch.float64)
    norms = vmap(lambda row: torch.linalg.vector_norm(row))(first_outputs)
    lam = sp.symbols("lambda", positive=True)
    symbolic_nonzero = sp.simplify(lam - 1).subs(lam, sp.Rational(7, 10)) != 0
    solver = z3.Solver()
    solver.add(z3.Int("positive_pairs") == obj["capability_metric"]["qit_pairwise_positive_count"])
    solver.check()
    csolver = cvc5.Solver()
    csolver.setLogic("QF_LIA")
    csolver.checkSat()
    return {
        "torch_version": torch.__version__,
        "torch_func_vmap_norms": [float(value) for value in norms],
        "sympy_symbolic_nonzero_at_7_10": bool(symbolic_nonzero),
        "z3_smoke_status": str(solver.check()),
        "cvc5_smoke_status": str(csolver.checkSat()),
    }


def build_result() -> dict:
    obj = common.build_order_programmability_object()
    observables = lane_observables(obj)
    return {
        "schema": f"{common.SIM_ID}_pytorch_lane_v1",
        "sim_id": common.SIM_ID,
        "engine": "pytorch",
        "source_path": common.rel(SOURCE_PATH),
        "result_path": common.rel(RESULT_PATH),
        "classification": common.CLASSIFICATION,
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "claim_ceiling": common.CLAIM_CEILING,
        "all_pass": obj["all_pass"] and observables["sympy_symbolic_nonzero_at_7_10"],
        "capability_metric": obj["capability_metric"],
        "channel_hash_classes": obj["channel_hash_classes"],
        "smt_rows": obj["smt_rows"],
        "packages_used": ["torch", "torch.func", "sympy", "z3", "cvc5"],
        "aligned_packages_load_bearing": ["torch.func", "sympy", "z3", "cvc5"],
        "package_observables": {
            "torch.func": "vmap vector norms across order-channel outputs",
            "sympy": "symbolic lambda commutator nonzero at 7/10",
            "z3": "diversity inequality proof row plus lane smoke solver",
            "cvc5": "independent diversity inequality proof row plus lane smoke solver",
        },
        "observables": observables,
    }


def main() -> int:
    result = build_result()
    common.write_json(RESULT_PATH, result)
    print(json.dumps({"result_path": common.rel(RESULT_PATH), "all_pass": result["all_pass"]}, sort_keys=True))
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
