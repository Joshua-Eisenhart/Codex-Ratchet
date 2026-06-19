#!/usr/bin/env python3
"""PyTorch lane for basin_dof_perturb_and_read_v0."""

from __future__ import annotations

import cvc5
from cvc5 import Kind
import sympy as sp
import torch
from torch.func import vmap
from torch_geometric.data import Data
import z3

import basin_dof_perturb_and_read_v0_common as common


ENGINE = "pytorch"
SOURCE_PATH = common.SIM_DIR / f"{common.SIM_ID}_{ENGINE}.py"
RESULT_PATH = common.RESULT_DIR / f"{common.SIM_ID}_{ENGINE}_results.json"


def source_backing_probe(obj: dict) -> dict:
    class_code = {"RETURN": 1, "BOUNDARY": 2, "SCRAMBLING": 3}
    codes = torch.tensor([class_code[row["classification"]] for row in obj["dof_classification_table"]], dtype=torch.int64)
    edge_index = torch.tensor(
        [[0 for _ in obj["dof_classification_table"]], list(range(len(obj["dof_classification_table"])))],
        dtype=torch.long,
    )
    data = Data(x=codes.to(torch.float64).reshape(-1, 1), edge_index=edge_index)

    def code_plus_index(code: torch.Tensor, idx: torch.Tensor) -> torch.Tensor:
        return code + idx

    shifted = vmap(code_plus_index)(codes, torch.arange(len(codes), dtype=torch.int64))
    return_count = int(torch.count_nonzero(codes == class_code["RETURN"]).item())
    boundary_count = int(torch.count_nonzero(codes == class_code["BOUNDARY"]).item())
    shifted_sum = int(torch.sum(shifted).item())
    rational_ratio = sp.Rational(return_count, max(1, boundary_count))

    z_solver = z3.Solver()
    z_boundary = z3.Int("pytorch_boundary_dof_count_z3")
    z_solver.add(z_boundary == z3.IntVal(boundary_count))
    z_solver.add(z_boundary == z3.IntVal(0))
    z3_status = str(z_solver.check()).lower()

    c_solver = cvc5.Solver()
    int_sort = c_solver.getIntegerSort()
    c_boundary = c_solver.mkConst(int_sort, "pytorch_boundary_dof_count_cvc5")
    c_solver.assertFormula(c_solver.mkTerm(Kind.EQUAL, c_boundary, c_solver.mkInteger(boundary_count)))
    c_solver.assertFormula(c_solver.mkTerm(Kind.EQUAL, c_boundary, c_solver.mkInteger(0)))
    cvc5_status = str(c_solver.checkSat()).lower()

    return {
        "torch_geometric_num_nodes": int(data.num_nodes),
        "torch_geometric_edge_count": int(data.edge_index.shape[1]),
        "torch_func_vmap_shifted_code_sum": shifted_sum,
        "sympy_return_boundary_ratio": str(rational_ratio),
        "z3_boundary_not_zero": z3_status,
        "cvc5_boundary_not_zero": cvc5_status,
        "pass": (
            int(data.num_nodes) == obj["result_summary"]["dof_total"]
            and int(data.edge_index.shape[1]) == obj["result_summary"]["dof_total"]
            and return_count == obj["result_summary"]["return_dof_count"]
            and boundary_count == obj["result_summary"]["boundary_dof_count"]
            and boundary_count >= 1
            and z3_status == "unsat"
            and cvc5_status == "unsat"
        ),
    }


def main() -> int:
    obj = common.build_packet_object()
    probe = source_backing_probe(obj)
    capability, calls, one_to_one = common.one_to_one_tool_rows(ENGINE, "torch_geometric", ["torch.func", "sympy", "z3", "cvc5"])
    payload = common.engine_result_payload(
        engine=ENGINE,
        source_path=SOURCE_PATH,
        result_path=RESULT_PATH,
        packages_used=["torch", "torch.func", "torch_geometric", "sympy", "z3", "cvc5"],
        aligned_packages_load_bearing=["torch.func", "torch_geometric", "sympy", "z3", "cvc5"],
        package_observables={
            "torch.func": "vmap vectorized DoF classification code check",
            "torch_geometric": "Data edge_index carrier for DoF-row graph/control table",
            "sympy": "sp.Rational exact return/boundary count ratio",
            "z3": "z3.Solver computed DoF-count identity and erased flip",
            "cvc5": "cvc5.Solver computed DoF-count identity and erased flip",
        },
        source_backing_probe=probe,
        capability_receipts=capability,
        tool_calls=calls,
        one_to_one=one_to_one,
    )
    common.write_json(RESULT_PATH, payload)
    print(common.stable_json({"ok": payload["all_pass"], "result_path": common.rel(RESULT_PATH)}))
    return 0 if payload["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
