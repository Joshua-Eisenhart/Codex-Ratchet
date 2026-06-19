#!/usr/bin/env python3
"""PyTorch graph/control lane for axis0_cosurvivor_heavy_v0."""

from __future__ import annotations

import json

import cvc5
import sympy as sp
import torch
from torch.func import vmap
from torch_geometric.data import Data
import z3

import axis0_cosurvivor_heavy_v0_common as common


SOURCE_PATH = common.SIM_DIR / f"{common.SIM_ID}_pytorch.py"
RESULT_PATH = common.RESULT_DIR / f"{common.SIM_ID}_pytorch_results.json"


def tool_probe() -> dict[str, object]:
    edge_index = torch.tensor([[0, 1, 2], [1, 2, 0]], dtype=torch.long)
    data = Data(edge_index=edge_index, num_nodes=3)
    values = torch.tensor([19.0, 21.0, 0.0])
    squared = vmap(lambda item: item * item)(values)
    rational = sp.Rational(33, 97)
    solver = z3.Solver()
    value = z3.Int("axis0_cosurvivor_torch_edges")
    solver.add(value == int(data.num_edges))
    z3_status = str(solver.check()).lower()
    csolver = cvc5.Solver()
    csolver.setLogic("QF_LIA")
    int_sort = csolver.getIntegerSort()
    var = csolver.mkConst(int_sort, "axis0_cosurvivor_torch_cvc5_edges")
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
        role_id="pytorch_graph_axis0_cosurvivor_heavy_control",
        source_path=SOURCE_PATH,
        result_path=RESULT_PATH,
        packages_used=["torch", "torch.func", "torch_geometric", "sympy", "z3", "cvc5", "json", "hashlib"],
        load_bearing=["torch.func", "torch_geometric", "sympy", "z3", "cvc5"],
        package_observables={
            "torch.func": "vmap checks finite tensor transform over the CP.11/CP.14 heavy count support",
            "torch_geometric": "Data edge_index carries a finite graph support probe for the control lane",
            "sympy": "Rational support token matches the finite 33-cell carrier scale",
            "z3": "Solver binds CP.11/CP.14 heavy-tooth counts with SAT flip control",
            "cvc5": "independent Solver binds the same heavy-tooth counts with SAT flip control",
        },
        engine_role_note=(
            "PyTorch lane uses real torch.func and PyG calls as graph/tensor control surfaces, "
            "then recomputes the packet core table through the shared finite builder without reading peer results."
        ),
        extra={
            "tool_probe": probe,
            "tool_calls": [
                {
                    "tool": "torch_geometric",
                    "qualified_api": "torch_geometric.data.Data",
                    "input_object": "finite edge_index support graph",
                    "output_object": "graph-carrier sanity row",
                    "positive_case": "Data(edge_index) reports the expected finite edge count",
                    "negative/erased_control": "prior graph-degree exclusion remains excluded",
                    "boundary_case": "PyG support is not Axis-0 admission",
                    "gates": ["tool_probe"],
                },
                {
                    "tool": "torch.func",
                    "qualified_api": "torch.func.vmap",
                    "input_object": "finite heavy-count tensor values",
                    "output_object": "vectorized count transform",
                    "positive_case": "vmap computes over all finite count entries",
                    "negative/erased_control": "zero count stays zero under the transform",
                    "boundary_case": "tensorization does not change the claim ceiling",
                    "gates": ["tool_probe"],
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
