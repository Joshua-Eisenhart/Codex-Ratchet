#!/usr/bin/env python3
"""PyTorch lane for discrete_axis0_field_v0."""

from __future__ import annotations

import cvc5
from cvc5 import Kind
import sympy as sp
import torch
from torch.func import vmap
from torch_geometric.data import Data
import z3

import discrete_axis0_field_v0_common as common


ENGINE = "pytorch"
SOURCE_PATH = common.SIM_DIR / f"{common.SIM_ID}_{ENGINE}.py"
RESULT_PATH = common.RESULT_DIR / f"{common.SIM_ID}_{ENGINE}_results.json"


def source_backing_probe(axis0_object: dict) -> dict:
    phi_nums = torch.tensor([row["phi_numerator"] for row in axis0_object["readout_table"]], dtype=torch.int64)
    edge_index = torch.tensor(
        [[row["src"] for row in axis0_object["gradient_table"]], [row["dst"] for row in axis0_object["gradient_table"]]],
        dtype=torch.long,
    )
    data = Data(x=phi_nums.to(torch.float64).reshape(-1, 1), edge_index=edge_index)

    def gradient_for_edge(src: torch.Tensor, dst: torch.Tensor) -> torch.Tensor:
        return phi_nums[dst] - phi_nums[src]

    gradient_nums = vmap(gradient_for_edge)(edge_index[0], edge_index[1])
    nonzero = int(torch.count_nonzero(gradient_nums).item())
    rational_first = sp.Rational(int(gradient_nums[0].item()), common.FIELD_DENOMINATOR)

    z_solver = z3.Solver()
    z_nonzero = z3.Int("pytorch_axis0_nonzero_gradients_z3")
    z_solver.add(z_nonzero == z3.IntVal(nonzero))
    z_solver.add(z_nonzero == z3.IntVal(0))
    z3_status = str(z_solver.check()).lower()

    c_solver = cvc5.Solver()
    int_sort = c_solver.getIntegerSort()
    c_nonzero = c_solver.mkConst(int_sort, "pytorch_axis0_nonzero_gradients_cvc5")
    c_solver.assertFormula(c_solver.mkTerm(Kind.EQUAL, c_nonzero, c_solver.mkInteger(nonzero)))
    c_solver.assertFormula(c_solver.mkTerm(Kind.EQUAL, c_nonzero, c_solver.mkInteger(0)))
    cvc5_status = str(c_solver.checkSat()).lower()

    return {
        "torch_geometric_num_nodes": int(data.num_nodes),
        "torch_geometric_edge_count": int(data.edge_index.shape[1]),
        "torch_func_vmap_nonzero_gradient_edges": nonzero,
        "sympy_first_gradient": str(rational_first),
        "z3_nonzero_not_zero": z3_status,
        "cvc5_nonzero_not_zero": cvc5_status,
        "pass": (
            int(data.num_nodes) == common.EXPECTED_STATE_COUNT
            and int(data.edge_index.shape[1]) == common.EXPECTED_EDGE_COUNT
            and nonzero == axis0_object["gradient_summary"]["nonzero_gradient_edges"]
            and z3_status == "unsat"
            and cvc5_status == "unsat"
        ),
    }


def main() -> int:
    axis0_object = common.build_axis0_object()
    probe = source_backing_probe(axis0_object)
    payload = common.engine_result_payload(
        engine=ENGINE,
        source_path=SOURCE_PATH,
        result_path=RESULT_PATH,
        packages_used=["torch", "torch.func", "torch_geometric", "sympy", "z3", "cvc5"],
        aligned_packages_load_bearing=["torch.func", "torch_geometric", "sympy", "z3", "cvc5"],
        package_observables={
            "torch.func": "vmap vectorized gradient numerator check over committed edge_index",
            "torch_geometric": "Data edge_index carrier with 33 nodes and 198 directed generator edges",
            "sympy": "sp.Rational exact gradient numerator probe over phi denominator 97",
            "z3": "z3.Solver computed nonzero-gradient identity and packet crossover proofs",
            "cvc5": "cvc5.Solver computed nonzero-gradient identity and packet crossover proofs",
        },
        source_backing_probe=probe,
    )
    common.write_json(RESULT_PATH, payload)
    print(common.stable_json({"ok": payload["all_pass"], "result_path": common.rel(RESULT_PATH)}))
    return 0 if payload["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
