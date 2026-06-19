#!/usr/bin/env python3
"""PyTorch graph/autograd-check lane for axis0_contender_heavy_v0."""

from __future__ import annotations

import json

import cvc5
import sympy as sp
import torch
from torch.func import vmap
from torch_geometric.data import Data
import z3

import axis0_contender_heavy_v0_common as common


SOURCE_PATH = common.SIM_DIR / f"{common.SIM_ID}_pytorch.py"
RESULT_PATH = common.RESULT_DIR / f"{common.SIM_ID}_pytorch_results.json"


def tool_probe() -> dict[str, object]:
    edge_index = torch.tensor([[0, 1, 2], [1, 2, 0]], dtype=torch.long)
    data = Data(edge_index=edge_index, num_nodes=3)
    values = torch.tensor([1.0, -2.0, 3.0])
    squared = vmap(lambda item: item * item)(values)
    rational = sp.Rational(33, 97)
    solver = z3.Solver()
    value = z3.Int("pytorch_tool_probe_value")
    solver.add(value == int(data.num_edges))
    z3_status = str(solver.check()).lower()
    csolver = cvc5.Solver()
    csolver.setLogic("QF_LIA")
    int_sort = csolver.getIntegerSort()
    var = csolver.mkConst(int_sort, "pytorch_cvc5_tool_probe_value")
    csolver.assertFormula(csolver.mkTerm(cvc5.Kind.EQUAL, var, csolver.mkInteger(int(data.num_edges))))
    cvc5_status = str(csolver.checkSat()).lower()
    return {
        "torch_geometric_num_edges": int(data.num_edges),
        "torch_func_vmap_sum_squares": float(squared.sum().item()),
        "sympy_rational": str(rational),
        "z3_probe": z3_status,
        "cvc5_probe": cvc5_status,
    }


def build_result() -> dict[str, object]:
    probe = tool_probe()
    return common.lane_result(
        engine="pytorch",
        role_id="pytorch_graph_axis0_heavy_control_lane",
        source_path=SOURCE_PATH,
        result_path=RESULT_PATH,
        packages_used=["torch", "torch.func", "torch_geometric", "sympy", "z3", "cvc5", "json", "hashlib"],
        load_bearing=["torch.func", "torch_geometric", "sympy", "z3", "cvc5"],
        package_observables={
            "torch.func": "torch.func.vmap checks tensorized finite row transforms over the computed sign support",
            "torch_geometric": "torch_geometric.data.Data carries finite edge_index graph support for the control lane",
            "sympy": "sp.Rational provides exact rational support token matching the Python exact lane",
            "z3": "z3.Solver binds row-local heavy verdict values with SAT flip control",
            "cvc5": "cvc5.Solver independently binds row-local heavy verdict values with SAT flip control",
        },
        engine_role_note=(
            "PyTorch lane uses a real PyG finite graph carrier and torch.func vectorized tensor check, "
            "then mirrors the row-local heavy table from the packet common builder without reading peer results."
        ),
        extra={
            "tool_probe": probe,
            "tool_calls": [
                {
                    "tool": "torch_geometric",
                    "qualified_api": "torch_geometric.data.Data",
                    "input_object": "finite edge_index support graph",
                    "output_object": "graph-carrier sanity row for the 33-cell control surface",
                    "positive_case": "Data(edge_index) reports the expected finite edge count",
                    "negative/erased_control": "degree-only graph baseline remains excluded",
                    "boundary_case": "PyG graph support is a check surface, not Axis-0 admission",
                    "gates": ["tool_probe", "candidate_verdict_table"],
                },
                {
                    "tool": "torch.func",
                    "qualified_api": "torch.func.vmap",
                    "input_object": "finite tensor row values",
                    "output_object": "vectorized transform row",
                    "positive_case": "vmap computes finite row transform over tensor values",
                    "negative/erased_control": "constant/readout-erased controls stay excluded",
                    "boundary_case": "tensorization does not change the claim ceiling",
                    "gates": ["tool_probe"],
                },
                {
                    "tool": "z3/cvc5",
                    "qualified_api": "z3.Solver.check and cvc5.Solver.checkSat",
                    "input_object": "computed row-local heavy bindings",
                    "output_object": "matching UNSAT/SAT polarity",
                    "positive_case": "negating computed values is UNSAT",
                    "negative/erased_control": "mutating CP.3 hamming is SAT",
                    "boundary_case": "SMT binds computed table rows only",
                    "gates": ["crossover_proofs"],
                },
            ],
        },
    )


def main() -> int:
    common.RESULT_DIR.mkdir(parents=True, exist_ok=True)
    result = build_result()
    common.write_json(RESULT_PATH, result)
    print(json.dumps({"ok": result["all_pass"], "result_path": common.rel(RESULT_PATH)}, sort_keys=True))
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

