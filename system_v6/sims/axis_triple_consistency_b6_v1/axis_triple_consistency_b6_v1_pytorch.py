#!/usr/bin/env python3
"""PyTorch lane for axis_triple_consistency_b6_v1."""

from __future__ import annotations

from typing import Any

import cvc5
from cvc5 import Kind
import sympy as sp
import torch
import torch.func
from torch.func import vmap
from torch_geometric.data import Data
import z3

import axis_triple_consistency_b6_v1_common as common


ENGINE = "pytorch"
SOURCE_PATH = common.SIM_DIR / f"{common.SIM_ID}_{ENGINE}.py"
RESULT_PATH = common.RESULT_DIR / f"{common.SIM_ID}_{ENGINE}_results.json"


def torch_relation_probe(obj: dict[str, Any]) -> dict[str, Any]:
    rows = obj["consistency_table"]
    signs = torch.tensor(
        [[row["b0_sign"], row["b3_panel_relation_sign"], row["b6_sign"]] for row in rows],
        dtype=torch.int64,
    )

    def relation_kernel(row: torch.Tensor) -> torch.Tensor:
        expected = -(row[0] * row[1])
        return torch.stack([expected, (row[2] == expected).to(torch.int64)])

    out = vmap(relation_kernel)(signs)
    edge_index = torch.tensor(
        [
            [int(edge["src"]) for edge in common.axis0_common.rebuild_committed_carrier()["edges"]],
            [int(edge["dst"]) for edge in common.axis0_common.rebuild_committed_carrier()["edges"]],
        ],
        dtype=torch.long,
    )
    graph = Data(edge_index=edge_index, num_nodes=common.EXPECTED_STATE_COUNT)
    expected_values = out[:, 0].detach().cpu().tolist()
    holds = [bool(value) for value in out[:, 1].detach().cpu().tolist()]
    vector = [
        {
            "row_id": row["row_id"],
            "b0": int(signs[idx, 0].item()),
            "b3": int(signs[idx, 1].item()),
            "b6": int(signs[idx, 2].item()),
            "expected": int(expected_values[idx]),
            "holds": holds[idx],
        }
        for idx, row in enumerate(rows)
    ]
    return {
        "sign_vector_sha256": common.stable_sha256(vector),
        "agreement_count": int(out[:, 1].sum().item()),
        "violation_count": int(len(rows) - int(out[:, 1].sum().item())),
        "torch_geometric_num_nodes": int(graph.num_nodes),
        "torch_geometric_edge_count": int(graph.edge_index.shape[1]),
    }


def sympy_panel_probe() -> dict[str, Any]:
    eta_fiber, eta_base = sp.symbols("eta_fiber eta_base")
    substitutions = {eta_fiber: sp.pi / 6, eta_base: sp.pi / 3}
    b0_fiber = sp.sign(sp.cos(2 * eta_fiber).subs(substitutions))
    b0_base = sp.sign(sp.cos(2 * eta_base).subs(substitutions))
    matrix = sp.Matrix([[-(b0_fiber * 1), -(b0_base * -1)]])
    return {
        "expected_b6_fiber": int(sp.simplify(matrix[0, 0])),
        "expected_b6_base": int(sp.simplify(matrix[0, 1])),
        "pass": int(matrix[0, 0]) == -1 and int(matrix[0, 1]) == -1,
    }


def z3_probe(obj: dict[str, Any]) -> str:
    values = common.engine_computed_values(obj)
    solver = z3.Solver()
    total = z3.Int("torch_v1_total")
    violations = z3.Int("torch_v1_violations")
    faithful = z3.Int("torch_v1_faithful_adapter")
    solver.add(total == z3.IntVal(values["sample_total"]))
    solver.add(violations == z3.IntVal(values["violation_count"]))
    solver.add(faithful == z3.IntVal(1 if values["faithful_33_cell_placement_possible"] else 0))
    solver.add(total == common.EXPECTED_STATE_COUNT)
    solver.add(violations > 0)
    solver.add(faithful == 0)
    return str(solver.check()).lower()


def cvc5_probe(obj: dict[str, Any]) -> str:
    values = common.engine_computed_values(obj)
    solver = cvc5.Solver()
    solver.setLogic("QF_LIA")
    int_sort = solver.getIntegerSort()
    total = solver.mkConst(int_sort, "torch_v1_total_cvc5")
    violations = solver.mkConst(int_sort, "torch_v1_violations_cvc5")
    faithful = solver.mkConst(int_sort, "torch_v1_faithful_adapter_cvc5")
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, total, solver.mkInteger(values["sample_total"])))
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, violations, solver.mkInteger(values["violation_count"])))
    solver.assertFormula(
        solver.mkTerm(Kind.EQUAL, faithful, solver.mkInteger(1 if values["faithful_33_cell_placement_possible"] else 0))
    )
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, total, solver.mkInteger(common.EXPECTED_STATE_COUNT)))
    solver.assertFormula(solver.mkTerm(Kind.GT, violations, solver.mkInteger(0)))
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, faithful, solver.mkInteger(0)))
    result = solver.checkSat()
    return "sat" if result.isSat() else "unsat" if result.isUnsat() else str(result).lower()


def build_result() -> dict[str, Any]:
    obj = common.build_axis_triple_object()
    vector = torch_relation_probe(obj)
    panel = sympy_panel_probe()
    z3_status = z3_probe(obj)
    cvc5_status = cvc5_probe(obj)
    expected_hash = common.engine_computed_values(obj)["sign_vector_sha256"]
    probe = {
        "pass": (
            vector["sign_vector_sha256"] == expected_hash
            and vector["torch_geometric_num_nodes"] == common.EXPECTED_STATE_COUNT
            and vector["torch_geometric_edge_count"] == common.EXPECTED_EDGE_COUNT
            and panel["pass"]
            and z3_status == "sat"
            and cvc5_status == "sat"
        ),
        "sign_vector_sha256": vector["sign_vector_sha256"],
        "torch_relation_probe": vector,
        "sympy_panel_probe": panel,
        "z3_gate_status": z3_status,
        "cvc5_gate_status": cvc5_status,
    }
    return common.engine_result_payload(
        engine=ENGINE,
        source_path=SOURCE_PATH,
        result_path=RESULT_PATH,
        packages_used=["torch", "torch.func", "torch_geometric", "sympy", "z3", "cvc5"],
        aligned_packages_load_bearing=["torch.func", "torch_geometric", "sympy", "z3", "cvc5"],
        package_observables={
            "torch.func": "torch.func.vmap vectorizes the row-local relation kernel over b0/b3/b6 signs",
            "torch_geometric": "torch_geometric.data.Data carries the 33-cell edge_index carrier",
            "sympy": "sp.symbols/sp.Matrix computes exact panel signs",
            "z3": "z3.Solver binds proxy violations and faithful-adapter blocker",
            "cvc5": "cvc5.Solver independently binds proxy violations and faithful-adapter blocker",
        },
        source_backing_probe=probe,
    )


def main() -> int:
    common.write_json(RESULT_PATH, build_result())
    print(common.stable_json({"ok": True, "result_path": common.rel(RESULT_PATH)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
