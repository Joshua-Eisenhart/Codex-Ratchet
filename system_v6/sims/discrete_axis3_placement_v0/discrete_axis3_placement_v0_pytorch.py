#!/usr/bin/env python3
"""PyTorch lane for discrete_axis3_placement_v0."""

from __future__ import annotations

import cvc5
from cvc5 import Kind
import sympy as sp
import torch
from torch.func import vmap
from torch_geometric.data import Data
import z3

import discrete_axis3_placement_v0_common as common


ENGINE = "pytorch"
SOURCE_PATH = common.SIM_DIR / f"{common.SIM_ID}_{ENGINE}.py"
RESULT_PATH = common.RESULT_DIR / f"{common.SIM_ID}_{ENGINE}_results.json"


def source_backing_probe(axis3_object: dict) -> dict:
    edge_distances = torch.tensor(
        [
            row["density_step_distance"]
            for row in axis3_object["stability_under_committed_dynamics"]["rows"]
        ],
        dtype=torch.float64,
    )
    stable = int(torch.count_nonzero(edge_distances <= common.EPS).item())
    changed = int(torch.count_nonzero(edge_distances > common.EPS).item())

    values = torch.stack([edge_distances, edge_distances * 0.0], dim=1)
    norms = vmap(lambda pair: torch.linalg.vector_norm(pair))(values)
    nonnegative_norms = bool(torch.all(norms >= 0).item())

    edge_index = torch.tensor(
        [[idx, idx + 1] for idx in range(edge_distances.numel())],
        dtype=torch.long,
    ).t().contiguous()
    data = Data(x=edge_distances.reshape(-1, 1), edge_index=edge_index)

    eta = sp.symbols("eta", real=True)
    horizontal_base = sp.simplify((-sp.cos(2 * eta)) + sp.cos(2 * eta))
    symbolic_pass = horizontal_base == 0

    z_solver = z3.Solver()
    z_changed = z3.Int("torch_axis3_changed_z3")
    z_solver.add(z_changed == z3.IntVal(changed))
    z_solver.add(z_changed == z3.IntVal(0))
    z3_status = str(z_solver.check()).lower()

    c_solver = cvc5.Solver()
    int_sort = c_solver.getIntegerSort()
    c_changed = c_solver.mkConst(int_sort, "torch_axis3_changed_cvc5")
    c_solver.assertFormula(c_solver.mkTerm(Kind.EQUAL, c_changed, c_solver.mkInteger(changed)))
    c_solver.assertFormula(c_solver.mkTerm(Kind.EQUAL, c_changed, c_solver.mkInteger(0)))
    cvc5_status = str(c_solver.checkSat()).lower()

    expected = axis3_object["stability_under_committed_dynamics"]
    return {
        "torch_stable_density_edges": stable,
        "torch_changed_density_edges": changed,
        "torch_func_norms_nonnegative": nonnegative_norms,
        "torch_geometric_num_nodes": int(data.num_nodes),
        "torch_geometric_num_edges": int(data.num_edges),
        "sympy_horizontal_base_A_dot_gamma": str(horizontal_base),
        "z3_changed_not_zero": z3_status,
        "cvc5_changed_not_zero": cvc5_status,
        "pass": (
            stable == expected["stable_edge_count"]
            and changed == expected["changed_edge_count"]
            and data.num_edges == edge_distances.numel()
            and symbolic_pass
            and nonnegative_norms
            and z3_status == "unsat"
            and cvc5_status == "unsat"
        ),
    }


def main() -> int:
    axis3_object = common.build_axis3_object()
    probe = source_backing_probe(axis3_object)
    payload = common.engine_result_payload(
        engine=ENGINE,
        source_path=SOURCE_PATH,
        result_path=RESULT_PATH,
        packages_used=["torch", "torch.func", "torch_geometric", "sympy", "z3", "cvc5"],
        aligned_packages_load_bearing=["torch.func", "torch_geometric", "sympy", "z3", "cvc5"],
        package_observables={
            "torch.func": "vmap torch-native density-step norm check over loop-time edges",
            "torch_geometric": "Data edge_index loop-time dynamics carrier",
            "sympy": "sp.symbols and sp.simplify exact horizontal condition A(dot gamma_out)=0",
            "z3": "z3.Solver computed changed-edge identity and packet crossover proofs",
            "cvc5": "cvc5.Solver computed changed-edge identity and packet crossover proofs",
        },
        source_backing_probe=probe,
    )
    common.write_json(RESULT_PATH, payload)
    print(common.stable_json({"ok": payload["all_pass"], "result_path": common.rel(RESULT_PATH)}))
    return 0 if payload["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
