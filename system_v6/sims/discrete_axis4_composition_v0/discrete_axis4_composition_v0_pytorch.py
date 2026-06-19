#!/usr/bin/env python3
"""PyTorch lane for discrete_axis4_composition_v0."""

from __future__ import annotations

import cvc5
from cvc5 import Kind
import sympy as sp
import torch
from torch.func import vmap
from torch_geometric.data import Data
import z3

import discrete_axis4_composition_v0_common as common


ENGINE = "pytorch"
SOURCE_PATH = common.SIM_DIR / f"{common.SIM_ID}_{ENGINE}.py"
RESULT_PATH = common.RESULT_DIR / f"{common.SIM_ID}_{ENGINE}_results.json"


def source_backing_probe(axis4_object: dict) -> dict:
    pins = common.pinning_payload()
    coords = torch.tensor([row["coord"] for row in axis4_object["axis4_readout_table"]], dtype=torch.float64)
    r_map = torch.tensor(pins["R"]["M"], dtype=torch.float64)
    c_map = torch.tensor(pins["C"]["M"], dtype=torch.float64)
    edge_index = torch.tensor(
        [[row["src"] for row in axis4_object["carrier_edges"]], [row["dst"] for row in axis4_object["carrier_edges"]]],
        dtype=torch.long,
    )
    data = Data(x=coords, edge_index=edge_index)

    def axis4_for_coord(r: torch.Tensor) -> torch.Tensor:
        phi_d = r_map @ (c_map @ r)
        phi_i = c_map @ (r_map @ r)
        delta = phi_d - phi_i
        norm = torch.linalg.vector_norm(delta)
        y_sign = torch.where(delta[1] > common.EPS, torch.tensor(1), torch.tensor(-1))
        z_sign = torch.where(delta[2] > common.EPS, torch.tensor(1), torch.tensor(-1))
        x_sign = torch.where(
            delta[0] > common.EPS,
            torch.tensor(1),
            torch.where(delta[0] < -common.EPS, torch.tensor(-1), torch.tensor(0)),
        )
        yz_sign = torch.where(torch.abs(delta[1]) > common.EPS, y_sign, torch.where(torch.abs(delta[2]) > common.EPS, z_sign, x_sign))
        return torch.where(norm <= common.EPS, torch.tensor(0), yz_sign)

    computed = vmap(axis4_for_coord)(coords).to(torch.int64)
    expected = torch.tensor([row["axis4_sign"] for row in axis4_object["axis4_readout_table"]], dtype=torch.int64)
    positive = int(torch.sum(computed == 1).item())
    negative = int(torch.sum(computed == -1).item())
    neutral = int(torch.sum(computed == 0).item())
    matches = bool(torch.all(computed == expected).item())

    theta = sp.pi / 2
    l_r = sp.Matrix([[0, 0, 0], [0, 0, -theta], [0, theta, 0]])
    l_c = sp.diag(sp.log(sp.Rational(7, 10)), sp.log(sp.Rational(7, 10)), 0)
    commutator = sp.simplify(l_r * l_c - l_c * l_r)
    symbolic_nonzero_entries = int(sum(1 for value in commutator if value != 0))

    z_solver = z3.Solver()
    z_positive = z3.Int("pytorch_axis4_positive_count_z3")
    z_negative = z3.Int("pytorch_axis4_negative_count_z3")
    z_solver.add(z_positive == z3.IntVal(positive))
    z_solver.add(z_negative == z3.IntVal(negative))
    z_solver.add(z3.Or(z_positive == 0, z_negative == 0))
    z3_status = str(z_solver.check()).lower()

    c_solver = cvc5.Solver()
    int_sort = c_solver.getIntegerSort()
    c_positive = c_solver.mkConst(int_sort, "pytorch_axis4_positive_count_cvc5")
    c_negative = c_solver.mkConst(int_sort, "pytorch_axis4_negative_count_cvc5")
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
        "sympy_commutator_nonzero_entries": symbolic_nonzero_entries,
        "sympy_commutator": str(commutator),
        "z3_positive_negative_not_zero": z3_status,
        "cvc5_positive_negative_not_zero": cvc5_status,
        "pass": (
            int(data.num_nodes) == common.EXPECTED_STATE_COUNT
            and int(data.edge_index.shape[1]) == common.EXPECTED_EDGE_COUNT
            and positive == axis4_object["axis4_counts"]["positive"]
            and negative == axis4_object["axis4_counts"]["negative"]
            and neutral == axis4_object["axis4_counts"]["neutral"]
            and matches
            and symbolic_nonzero_entries > 0
            and z3_status == "unsat"
            and cvc5_status == "unsat"
        ),
    }


def main() -> int:
    axis4_object = common.build_axis4_object()
    probe = source_backing_probe(axis4_object)
    payload = common.engine_result_payload(
        engine=ENGINE,
        source_path=SOURCE_PATH,
        result_path=RESULT_PATH,
        packages_used=["torch", "torch.func", "torch_geometric", "sympy", "z3", "cvc5"],
        aligned_packages_load_bearing=["torch.func", "torch_geometric", "sympy", "z3", "cvc5"],
        package_observables={
            "torch.func": "vmap vectorized Axis-4 sign recomputation over 33 Bloch vectors",
            "torch_geometric": "Data edge_index carrier with 33 nodes and 198 committed directed generator edges",
            "sympy": "sp.Matrix/sp.log exact R_x/D_z generator commutator source probe",
            "z3": "z3.Solver/z3.Int computed positive/negative Axis-4 identity",
            "cvc5": "cvc5.Solver/mkConst/mkTerm/assertFormula/checkSat computed positive/negative Axis-4 identity",
        },
        source_backing_probe=probe,
    )
    common.write_json(RESULT_PATH, payload)
    print(common.stable_json({"ok": payload["all_pass"], "result_path": common.rel(RESULT_PATH)}))
    return 0 if payload["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
