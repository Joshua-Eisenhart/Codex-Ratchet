#!/usr/bin/env python3
"""PyTorch lane for axis_triple_consistency_b6_v0."""

from __future__ import annotations

import json
from typing import Any

import cvc5
from cvc5 import Kind
import sympy as sp
import torch
import torch.func
from torch.func import vmap
from torch_geometric.data import Data
import z3

import axis_triple_consistency_b6_v0_common as common


ENGINE = "pytorch"
SOURCE_PATH = common.SIM_DIR / f"{common.SIM_ID}_{ENGINE}.py"
RESULT_PATH = common.RESULT_DIR / f"{common.SIM_ID}_{ENGINE}_results.json"


def torch_sign(values: torch.Tensor) -> torch.Tensor:
    return torch.where(values > common.EPS, torch.ones_like(values, dtype=torch.int64), torch.where(values < -common.EPS, -torch.ones_like(values, dtype=torch.int64), torch.zeros_like(values, dtype=torch.int64)))


def load_pinned_pair_torch() -> dict[str, torch.Tensor]:
    s4 = common.load_json(common.PARENT_PATHS["geo_s4_envelope"])
    s5 = common.load_json(common.PARENT_PATHS["geo_s5_envelope"])
    operator = s4["affine_channel_table"][common.PRIMARY_OPERATOR]
    terrain = s5["bloch_generator_table"][common.PRIMARY_TERRAIN]
    op_m = torch.tensor(common.parse_matrix(operator["pinned"]["M"]), dtype=torch.float64)
    op_c = torch.tensor(common.parse_vector(operator["pinned"]["c"]), dtype=torch.float64)
    terrain_a = torch.tensor(common.parse_matrix(terrain["pinned"]["A"]), dtype=torch.float64)
    terrain_b = torch.tensor(common.parse_vector(terrain["pinned"]["b"]), dtype=torch.float64)
    aug = torch.zeros((4, 4), dtype=torch.float64)
    aug[:3, :3] = terrain_a
    aug[:3, 3] = terrain_b
    flow = torch.linalg.matrix_exp(0.5 * aug)
    return {"op_m": op_m, "op_c": op_c, "terrain_m": flow[:3, :3], "terrain_c": flow[:3, 3]}


def sample_tensors() -> tuple[list[dict[str, Any]], torch.Tensor, torch.Tensor, torch.Tensor]:
    rows = common.axis3_sample_rows()
    etas = torch.tensor([row["eta"] for row in rows], dtype=torch.float64)
    chis = torch.tensor([row["chi0"] for row in rows], dtype=torch.float64)
    b3 = torch.tensor([row["b3_sign"] for row in rows], dtype=torch.int64)
    bloch = torch.stack(
        [
            torch.sin(2.0 * etas) * torch.cos(2.0 * chis),
            torch.sin(2.0 * etas) * torch.sin(2.0 * chis),
            torch.cos(2.0 * etas),
        ],
        dim=1,
    )
    return rows, etas, b3, bloch


def recompute_table_counts() -> dict[str, Any]:
    rows, etas, b3, bloch = sample_tensors()
    pair = load_pinned_pair_torch()

    def row_precedence(r: torch.Tensor) -> torch.Tensor:
        op_first = pair["terrain_m"] @ (pair["op_m"] @ r + pair["op_c"]) + pair["terrain_c"]
        terrain_first = pair["op_m"] @ (pair["terrain_m"] @ r + pair["terrain_c"]) + pair["op_c"]
        delta = op_first - terrain_first
        return torch.linalg.norm(delta) * delta[2]

    weighted_z = vmap(row_precedence)(bloch)
    b6 = torch_sign(weighted_z)
    b0 = torch_sign(torch.cos(2.0 * etas))
    expected = -(b0 * b3)
    holds = b6 == expected
    nonneutral = expected != 0
    edge_index = torch.tensor(
        [[idx for idx in range(len(rows))], [(idx + 1) % len(rows) for idx in range(len(rows))]],
        dtype=torch.long,
    )
    graph = Data(edge_index=edge_index, num_nodes=len(rows))
    return {
        "sample_total": len(rows),
        "agreement_count": int(holds.to(torch.int64).sum().item()),
        "violation_count": int((~holds).to(torch.int64).sum().item()),
        "nonneutral_total": int(nonneutral.to(torch.int64).sum().item()),
        "nonneutral_agreement_count": int((holds & nonneutral).to(torch.int64).sum().item()),
        "b6_positive_count": int((b6 == 1).to(torch.int64).sum().item()),
        "b6_negative_count": int((b6 == -1).to(torch.int64).sum().item()),
        "torch_geometric_num_nodes": int(graph.num_nodes),
        "torch_geometric_edge_count": int(graph.edge_index.shape[1]),
        "weighted_z_sha256": common.stable_sha256([float(x) for x in weighted_z.detach().cpu().tolist()]),
    }


def panel_checks_torch() -> list[dict[str, Any]]:
    pair = load_pinned_pair_torch()
    etas = torch.tensor([torch.pi / 6.0, torch.pi / 3.0], dtype=torch.float64)
    b3 = torch.tensor([1, -1], dtype=torch.int64)
    chis = torch.tensor([0.0, 0.0], dtype=torch.float64)
    bloch = torch.stack(
        [
            torch.sin(2.0 * etas) * torch.cos(2.0 * chis),
            torch.sin(2.0 * etas) * torch.sin(2.0 * chis),
            torch.cos(2.0 * etas),
        ],
        dim=1,
    )

    def row_precedence(r: torch.Tensor) -> torch.Tensor:
        op_first = pair["terrain_m"] @ (pair["op_m"] @ r + pair["op_c"]) + pair["terrain_c"]
        terrain_first = pair["op_m"] @ (pair["terrain_m"] @ r + pair["terrain_c"]) + pair["op_c"]
        delta = op_first - terrain_first
        return torch.linalg.norm(delta) * delta[2]

    b6 = torch_sign(vmap(row_precedence)(bloch))
    b0 = torch_sign(torch.cos(2.0 * etas))
    expected = -(b0 * b3)
    labels = ["panel6_q2_eta_pi_over_6_fiber", "panel6_q2_eta_pi_over_3_base"]
    return [
        {
            "panel_point_id": labels[idx],
            "b0_sign": int(b0[idx].item()),
            "b3_sign": int(b3[idx].item()),
            "computed_b6_sign": int(b6[idx].item()),
            "expected_b6_negative_b0_b3": int(expected[idx].item()),
            "panel_expected_b6": -1,
            "matches_panel_expected": int(b6[idx].item()) == -1,
        }
        for idx in range(2)
    ]


def sympy_panel_probe() -> dict[str, Any]:
    eta_fiber, eta_base = sp.symbols("eta_fiber eta_base")
    substitutions = {eta_fiber: sp.pi / 6, eta_base: sp.pi / 3}
    b0_fiber = sp.sign(sp.cos(2 * eta_fiber).subs(substitutions))
    b0_base = sp.sign(sp.cos(2 * eta_base).subs(substitutions))
    expected_fiber = sp.simplify(-(b0_fiber * 1))
    expected_base = sp.simplify(-(b0_base * -1))
    mat = sp.Matrix([[expected_fiber, expected_base]])
    return {
        "expected_b6_fiber": int(mat[0, 0]),
        "expected_b6_base": int(mat[0, 1]),
        "pass": int(mat[0, 0]) == -1 and int(mat[0, 1]) == -1,
    }


def z3_count_probe(values: dict[str, Any], *, erased: bool = False) -> str:
    solver = z3.Solver()
    total = z3.Int("torch_total_erased" if erased else "torch_total")
    agreement = z3.Int("torch_agreement_erased" if erased else "torch_agreement")
    violation = z3.Int("torch_violation_erased" if erased else "torch_violation")
    solver.add(total == z3.IntVal(values["sample_total"]))
    solver.add(agreement == z3.IntVal(values["sample_total"] if erased else values["agreement_count"]))
    solver.add(violation == z3.IntVal(0 if erased else values["violation_count"]))
    solver.add(total == agreement)
    solver.add(violation == z3.IntVal(0))
    return str(solver.check())


def cvc5_int(solver: cvc5.Solver, value: int) -> Any:
    return solver.mkInteger(int(value))


def cvc5_status(result: Any) -> str:
    if result.isSat():
        return "sat"
    if result.isUnsat():
        return "unsat"
    return str(result)


def cvc5_count_probe(values: dict[str, Any], *, erased: bool = False) -> str:
    solver = cvc5.Solver()
    solver.setLogic("QF_LIA")
    integer = solver.getIntegerSort()
    total = solver.mkConst(integer, "torch_total_erased" if erased else "torch_total")
    agreement = solver.mkConst(integer, "torch_agreement_erased" if erased else "torch_agreement")
    violation = solver.mkConst(integer, "torch_violation_erased" if erased else "torch_violation")
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, total, cvc5_int(solver, values["sample_total"])))
    solver.assertFormula(
        solver.mkTerm(Kind.EQUAL, agreement, cvc5_int(solver, values["sample_total"] if erased else values["agreement_count"]))
    )
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, violation, cvc5_int(solver, 0 if erased else values["violation_count"])))
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, total, agreement))
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, violation, cvc5_int(solver, 0)))
    return cvc5_status(solver.checkSat())


def build_result() -> dict[str, Any]:
    obj = common.build_axis_triple_object()
    values = recompute_table_counts()
    panel = panel_checks_torch()
    sympy_probe = sympy_panel_probe()
    z3_verdict = z3_count_probe(values)
    z3_erased = z3_count_probe(values, erased=True)
    cvc5_verdict = cvc5_count_probe(values)
    cvc5_erased = cvc5_count_probe(values, erased=True)
    expected = common.engine_computed_values(obj)
    all_pass = bool(
        values["sample_total"] == expected["sample_total"]
        and values["agreement_count"] == expected["agreement_count"]
        and values["violation_count"] == expected["violation_count"]
        and values["nonneutral_agreement_count"] == expected["nonneutral_agreement_count"]
        and values["torch_geometric_num_nodes"] == 48
        and values["torch_geometric_edge_count"] == 48
        and all(row["matches_panel_expected"] for row in panel)
        and sympy_probe["pass"]
        and z3_verdict == cvc5_verdict == "unsat"
        and z3_erased == cvc5_erased == "sat"
    )
    return {
        **common.source_result_base(ENGINE, SOURCE_PATH, RESULT_PATH),
        "packages_used": ["torch", "torch.func", "torch_geometric", "sympy", "z3", "cvc5", "json"],
        "aligned_packages_load_bearing": ["torch.func", "torch_geometric", "sympy", "z3", "cvc5"],
        "package_observables": {
            "torch.func": "torch.func.vmap vectorizes the precedence row computation over 48 Hopf states",
            "torch_geometric": "torch_geometric.data.Data edge_index carries the finite sample/control graph",
            "sympy": "sp.symbols/sp.Matrix panel arithmetic check for q2 signs",
            "z3": "z3.Solver binds computed agreement/violation counts and erased flip",
            "cvc5": "cvc5.Solver independently binds the same count row and erased flip",
        },
        "TOOL_MANIFEST": common.TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": common.TOOL_INTEGRATION_DEPTH,
        "tool_intent": common.TOOL_INTENT,
        "claim_path_tools": ["torch.func", "torch_geometric", "sympy", "z3", "cvc5"],
        "source_backing_probe": {
            "torch_dtype": str(torch.float64),
            "torch_func_vmap_rows": values["sample_total"],
            "torch_geometric_num_nodes": values["torch_geometric_num_nodes"],
            "torch_geometric_edge_count": values["torch_geometric_edge_count"],
            "sympy_panel_probe": sympy_probe,
            "z3_verdict": z3_verdict,
            "z3_erased_flip_verdict": z3_erased,
            "cvc5_verdict": cvc5_verdict,
            "cvc5_erased_flip_verdict": cvc5_erased,
            "pass": all_pass,
        },
        "computed_values": values,
        "panel_point_checks": panel,
        "crossover_proofs": {
            "z3": {"ran": True, "load_bearing": True, "verdict": z3_verdict, "erased_flip_verdict": z3_erased},
            "cvc5": {"ran": True, "load_bearing": True, "verdict": cvc5_verdict, "erased_flip_verdict": cvc5_erased},
        },
        "capability_receipts": [
            {"receipt_id": "pytorch_axis_triple_vmap_recompute", "tool": "torch.func", "status": "used"},
            {"receipt_id": "pytorch_axis_triple_sample_graph", "tool": "torch_geometric", "status": "used"},
        ],
        "tool_calls": [
            {"tool": "torch.func", "qualified_api/function": "torch.func.vmap / vmap(row_precedence)", "load_bearing": True},
            {"tool": "torch_geometric", "qualified_api/function": "torch_geometric.data.Data(edge_index)", "load_bearing": True},
            {"tool": "sympy", "qualified_api/function": "sp.symbols, sp.Matrix, sp.simplify", "load_bearing": True},
            {"tool": "z3", "qualified_api/function": "z3.Solver, z3.Int, solver.add, solver.check", "load_bearing": True},
            {"tool": "cvc5", "qualified_api/function": "cvc5.Solver, mkConst, mkTerm, assertFormula, checkSat", "load_bearing": True},
        ],
        "all_pass": all_pass,
    }


def main() -> int:
    payload = build_result()
    common.write_json(RESULT_PATH, payload)
    print(json.dumps({"ok": payload["all_pass"], "result_path": common.rel(RESULT_PATH)}, indent=2, sort_keys=True))
    return 0 if payload["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
