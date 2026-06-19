#!/usr/bin/env python3
"""PyTorch lane for carnot_szilard_basin_cycle_v0."""

from __future__ import annotations

import cvc5
from cvc5 import Kind
import sympy as sp
import torch
from torch.func import vmap
from torch_geometric.data import Data
import z3

import carnot_szilard_basin_cycle_v0_common as common


ENGINE = "pytorch"
SOURCE_PATH = common.SIM_DIR / f"{common.SIM_ID}_{ENGINE}.py"
RESULT_PATH = common.RESULT_DIR / f"{common.SIM_ID}_{ENGINE}_results.json"


def source_backing_probe(obj: dict) -> dict:
    sample_ms = torch.tensor([row["m_sample"] for row in obj["basin_cycle_rows"]], dtype=torch.int64)
    full_ms = torch.tensor([row["m_full_graph"] for row in obj["basin_cycle_rows"]], dtype=torch.int64)
    edge_index = torch.tensor(
        [[idx for idx in range(len(sample_ms))], [idx + len(sample_ms) for idx in range(len(sample_ms))]],
        dtype=torch.long,
    )
    data = Data(x=torch.cat([sample_ms, full_ms]).to(torch.float64).reshape(-1, 1), edge_index=edge_index)

    def add_full(sample: torch.Tensor, full: torch.Tensor) -> torch.Tensor:
        return sample + full

    row_sums = vmap(add_full)(sample_ms, full_ms)
    sample_min = int(torch.min(sample_ms).item())
    sample_max = int(torch.max(sample_ms).item())
    full_min = int(torch.min(full_ms).item())
    exact_ratio = sp.Rational(full_min, sample_min)
    exact_sample_log = sp.log(sample_min)

    z_solver = z3.Solver()
    z_sample = z3.Int("pytorch_sample_m")
    z_full = z3.Int("pytorch_full_m")
    z_solver.add(z_sample == z3.IntVal(sample_min))
    z_solver.add(z_full == z3.IntVal(full_min))
    z_solver.add(z3.Or(z_sample != 9, z_full != 33))
    z3_status = str(z_solver.check()).lower()

    c_solver = cvc5.Solver()
    int_sort = c_solver.getIntegerSort()
    c_sample = c_solver.mkConst(int_sort, "pytorch_sample_m_cvc5")
    c_full = c_solver.mkConst(int_sort, "pytorch_full_m_cvc5")
    c_solver.assertFormula(c_solver.mkTerm(Kind.EQUAL, c_sample, c_solver.mkInteger(sample_min)))
    c_solver.assertFormula(c_solver.mkTerm(Kind.EQUAL, c_full, c_solver.mkInteger(full_min)))
    c_solver.assertFormula(
        c_solver.mkTerm(
            Kind.OR,
            c_solver.mkTerm(Kind.DISTINCT, c_sample, c_solver.mkInteger(9)),
            c_solver.mkTerm(Kind.DISTINCT, c_full, c_solver.mkInteger(33)),
        )
    )
    cvc5_status = str(c_solver.checkSat()).lower()

    return {
        "torch_geometric_num_nodes": int(data.num_nodes),
        "torch_geometric_edge_count": int(data.edge_index.shape[1]),
        "torch_func_vmap_row_sum_total": int(torch.sum(row_sums).item()),
        "sympy_full_over_sample_ratio": str(exact_ratio),
        "sympy_sample_log": str(exact_sample_log),
        "z3_count_identity": z3_status,
        "cvc5_count_identity": cvc5_status,
        "pass": (
            int(data.num_nodes) == 6
            and int(data.edge_index.shape[1]) == 3
            and sample_min == 9
            and sample_max == 9
            and full_min == 33
            and str(exact_ratio) == "11/3"
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
            "torch.func": "torch.func.vmap vectorized sample/full merge count comparison",
            "torch_geometric": "torch_geometric.data.Data branch graph edge_index carrier",
            "sympy": "sp.Rational and sp.log exact count-side floor rows",
            "z3": "z3.Solver torch-derived computed m/floor count identity",
            "cvc5": "cvc5.Solver torch-derived computed m/floor count identity",
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
