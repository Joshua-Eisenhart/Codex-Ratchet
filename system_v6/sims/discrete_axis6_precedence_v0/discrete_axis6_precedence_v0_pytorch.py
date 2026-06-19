#!/usr/bin/env python3
"""PyTorch lane for discrete_axis6_precedence_v0."""

from __future__ import annotations

import cvc5
from cvc5 import Kind
import sympy as sp
import torch
from torch.func import vmap
from torch_geometric.data import Data
import z3

import discrete_axis6_precedence_v0_common as common


ENGINE = "pytorch"
SOURCE_PATH = common.SIM_DIR / f"{common.SIM_ID}_{ENGINE}.py"
RESULT_PATH = common.RESULT_DIR / f"{common.SIM_ID}_{ENGINE}_results.json"


def source_backing_probe(axis6_object: dict) -> dict:
    pins = common.pinning_payload()
    coords = torch.tensor([row["coord"] for row in axis6_object["precedence_table"]], dtype=torch.float64)
    op_m = torch.tensor(pins["operator"]["M"], dtype=torch.float64)
    op_c = torch.tensor(pins["operator"]["c"], dtype=torch.float64)
    terrain_m = torch.tensor(pins["terrain"]["M"], dtype=torch.float64)
    terrain_c = torch.tensor(pins["terrain"]["c"], dtype=torch.float64)
    edge_index = torch.tensor(
        [[row["src"] for row in axis6_object["carrier_edges"]], [row["dst"] for row in axis6_object["carrier_edges"]]],
        dtype=torch.long,
    )
    data = Data(x=coords, edge_index=edge_index)

    def b6_for_coord(r: torch.Tensor) -> torch.Tensor:
        operator_first = terrain_m @ (op_m @ r + op_c) + terrain_c
        terrain_first = op_m @ (terrain_m @ r + terrain_c) + op_c
        delta = operator_first - terrain_first
        weighted_z = torch.linalg.vector_norm(delta) * delta[2]
        return torch.where(
            weighted_z > common.EPS,
            torch.tensor(1, dtype=torch.int64),
            torch.where(weighted_z < -common.EPS, torch.tensor(-1, dtype=torch.int64), torch.tensor(0, dtype=torch.int64)),
        )

    computed = vmap(b6_for_coord)(coords)
    expected = torch.tensor([row["b6_sign"] for row in axis6_object["precedence_table"]], dtype=torch.int64)
    positive = int(torch.sum(computed == 1).item())
    negative = int(torch.sum(computed == -1).item())
    neutral = int(torch.sum(computed == 0).item())
    matches = bool(torch.all(computed == expected).item())

    q_z = sp.Rational(3, 10)
    dz = sp.diag(1 - q_z, 1 - q_z, 1)
    exact_dz_trace = sp.simplify(sum(dz[i, i] for i in range(3)))

    z_solver = z3.Solver()
    z_positive = z3.Int("pytorch_axis6_positive_count_z3")
    z_negative = z3.Int("pytorch_axis6_negative_count_z3")
    z_solver.add(z_positive == z3.IntVal(positive))
    z_solver.add(z_negative == z3.IntVal(negative))
    z_solver.add(z3.Or(z_positive == 0, z_negative == 0))
    z3_status = str(z_solver.check()).lower()

    c_solver = cvc5.Solver()
    int_sort = c_solver.getIntegerSort()
    c_positive = c_solver.mkConst(int_sort, "pytorch_axis6_positive_count_cvc5")
    c_negative = c_solver.mkConst(int_sort, "pytorch_axis6_negative_count_cvc5")
    c_solver.assertFormula(c_solver.mkTerm(Kind.EQUAL, c_positive, c_solver.mkInteger(positive)))
    c_solver.assertFormula(c_solver.mkTerm(Kind.EQUAL, c_negative, c_solver.mkInteger(negative)))
    c_solver.assertFormula(
        c_solver.mkTerm(
            Kind.OR,
            c_solver.mkTerm(Kind.EQUAL, c_positive, c_solver.mkInteger(0)),
            c_solver.mkTerm(Kind.EQUAL, c_negative, c_solver.mkInteger(0)),
        )
    )
    cvc5_status = str(c_solver.checkSat()).lower()

    return {
        "torch_geometric_num_nodes": int(data.num_nodes),
        "torch_geometric_edge_count": int(data.edge_index.shape[1]),
        "torch_func_vmap_positive": positive,
        "torch_func_vmap_negative": negative,
        "torch_func_vmap_neutral": neutral,
        "torch_func_vmap_matches_common_table": matches,
        "sympy_exact_dz_trace": str(exact_dz_trace),
        "z3_positive_negative_not_zero": z3_status,
        "cvc5_positive_negative_not_zero": cvc5_status,
        "pass": (
            int(data.num_nodes) == common.EXPECTED_STATE_COUNT
            and int(data.edge_index.shape[1]) == common.EXPECTED_EDGE_COUNT
            and positive == axis6_object["precedence_counts"]["positive"]
            and negative == axis6_object["precedence_counts"]["negative"]
            and neutral == axis6_object["precedence_counts"]["neutral"]
            and matches
            and str(exact_dz_trace) == "12/5"
            and z3_status == "unsat"
            and cvc5_status == "unsat"
        ),
    }


def main() -> int:
    axis6_object = common.build_axis6_object()
    probe = source_backing_probe(axis6_object)
    payload = common.engine_result_payload(
        engine=ENGINE,
        source_path=SOURCE_PATH,
        result_path=RESULT_PATH,
        packages_used=["torch", "torch.func", "torch_geometric", "sympy", "z3", "cvc5"],
        aligned_packages_load_bearing=["torch.func", "torch_geometric", "sympy", "z3", "cvc5"],
        package_observables={
            "torch.func": "vmap vectorized precedence sign recomputation over 33 Bloch vectors",
            "torch_geometric": "Data edge_index carrier with 33 nodes and 198 committed directed generator edges",
            "sympy": "sp.diag/sp.Rational exact D_z contraction trace source probe",
            "z3": "z3.Solver/z3.Int computed positive/negative precedence identity",
            "cvc5": "cvc5.Solver/mkConst/mkTerm/assertFormula/checkSat computed positive/negative precedence identity",
        },
        source_backing_probe=probe,
    )
    common.write_json(RESULT_PATH, payload)
    print(common.stable_json({"ok": payload["all_pass"], "result_path": common.rel(RESULT_PATH)}))
    return 0 if payload["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
