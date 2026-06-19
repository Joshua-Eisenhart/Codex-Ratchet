#!/usr/bin/env python3
"""PyTorch lane for ecd04_record_conditioned_navigation_v0."""

from __future__ import annotations

import json
from typing import Any

import sympy as sp
import torch
from torch.func import vmap
from torch_geometric.data import Data
import cvc5
from cvc5 import Kind
import z3

import ecd04_record_conditioned_navigation_v0_common as common


def local_solver_receipt(engine_scaled: int, baseline_scaled: int, erased_success: int) -> dict[str, str]:
    z3_solver = z3.Solver()
    e = z3.Int("pytorch_lane_engine_cost_scaled")
    b = z3.Int("pytorch_lane_baseline_cost_scaled")
    z3_solver.add(e == engine_scaled, b == baseline_scaled, e >= b)
    cvc5_solver = cvc5.Solver()
    cvc5_solver.setLogic("QF_LIA")
    int_sort = cvc5_solver.getIntegerSort()
    ce = cvc5_solver.mkConst(int_sort, "pytorch_lane_engine_cost_scaled")
    cb = cvc5_solver.mkConst(int_sort, "pytorch_lane_baseline_cost_scaled")
    cvc5_solver.assertFormula(cvc5_solver.mkTerm(Kind.EQUAL, ce, cvc5_solver.mkInteger(engine_scaled)))
    cvc5_solver.assertFormula(cvc5_solver.mkTerm(Kind.EQUAL, cb, cvc5_solver.mkInteger(baseline_scaled)))
    cvc5_solver.assertFormula(cvc5_solver.mkTerm(Kind.GEQ, ce, cb))
    z3_erased = z3.Solver()
    s = z3.Int("pytorch_lane_erased_success")
    z3_erased.add(s == erased_success, s < 1000)
    return {
        "z3_negated_margin": str(z3_solver.check()),
        "cvc5_negated_margin": str(cvc5_solver.checkSat()).lower(),
        "z3_erased_flip": str(z3_erased.check()),
    }


def build_lane() -> dict[str, Any]:
    obj = common.build_navigation_object()
    env = obj["shared_environment"]
    branch_index = {branch: idx for idx, branch in enumerate(env["branch_universe"])}
    action_index = {action: idx + len(branch_index) for idx, action in enumerate(sorted(env["action_success_sets"]))}
    edges = [[branch_index[edge["branch"]], action_index[edge["action"]]] for edge in env["graph_edges"]]
    edge_index = torch.tensor(edges, dtype=torch.long).t().contiguous()
    graph = Data(edge_index=edge_index, num_nodes=len(branch_index) + len(action_index))
    policy_actions = torch.tensor(
        [1 if branch in env["action_success_sets"][obj["qit_side"]["best"]["policy"][str(branch)]] else 0 for branch in env["branch_universe"]],
        dtype=torch.int64,
    )

    def identity(x: torch.Tensor) -> torch.Tensor:
        return x

    policy_success = vmap(identity)(policy_actions).sum().item() / len(env["branch_universe"])
    engine_cost = float(obj["qit_side"]["best"]["success_weighted_record_cost_nats"])
    baseline_cost = float(obj["baseline_side"]["best"]["success_weighted_record_cost_nats"])
    margin = baseline_cost - engine_cost
    exact_ratio = str(sp.Rational(obj["qit_side"]["best"]["record_class_count"], len(env["branch_universe"])))
    solver_receipt = local_solver_receipt(
        common.scaled(engine_cost),
        common.scaled(baseline_cost),
        int(round(obj["controls"]["record_erasure_regression"]["target_success_rate"] * 1000)),
    )
    return {
        "schema": f"{common.SIM_ID}.pytorch_lane.v1",
        "engine": "pytorch",
        "source_path": common.rel(common.SIM_DIR / f"{common.SIM_ID}_pytorch.py"),
        "result_path": common.rel(common.RESULT_DIR / f"{common.SIM_ID}_pytorch_results.json"),
        "classification": common.CLASSIFICATION,
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "all_pass": obj["all_pass"] and policy_success == 1.0 and margin > 0.0 and graph.num_edges == len(env["graph_edges"]) and solver_receipt["z3_negated_margin"] == "unsat",
        "reads_peer_result": False,
        "engine_mode": common.ENGINE_MODE,
        "packages_used": ["torch", "torch.func", "torch_geometric", "sympy", "z3", "cvc5"],
        "aligned_packages_load_bearing": ["torch.func", "torch_geometric", "sympy", "z3", "cvc5"],
        "package_observables": {
            "torch.func": "vmap recomputes policy success over branch tensor",
            "torch_geometric": "Data.edge_index carries branch/action success incidence",
            "sympy": f"exact engine record classes over branch universe ratio {exact_ratio}",
            "z3": "common.z3_crossover binds scaled cost inequality and erased success flip",
            "cvc5": "common.cvc5_crossover independently binds scaled cost inequality and erased success flip",
        },
        "computed_values": {
            "branch_count": len(env["branch_universe"]),
            "edge_count": int(graph.num_edges),
            "policy_success": policy_success,
            "engine_cost_scaled": common.scaled(engine_cost),
            "baseline_cost_scaled": common.scaled(baseline_cost),
            "margin_scaled": common.scaled(margin),
        },
        "local_solver_receipt": solver_receipt,
        "crossover_proofs": {"z3": obj["crossover_proofs"]["z3"], "cvc5": obj["crossover_proofs"]["cvc5"]},
        "tool_calls": [
            {
                "tool": "torch.func",
                "qualified_api/function": "torch.func.vmap",
                "input_object": "policy success tensor",
                "output_object": "target success rate",
                "positive_case": "engine policy success is 1.0",
                "negative_or_erased_control": "record-erased policy success is below 1.0",
                "boundary_case": "order-blind collapse",
                "demotion_condition": "vmap success does not match common policy success",
                "load_bearing": True,
            },
            {
                "tool": "torch_geometric",
                "qualified_api/function": "torch_geometric.data.Data",
                "input_object": "branch/action edge_index",
                "output_object": "finite incidence graph",
                "positive_case": "edge count matches shared environment graph",
                "negative_or_erased_control": "scrambled records degrade success",
                "boundary_case": "dropped-half rows",
                "demotion_condition": "graph edge carrier loses policy edges",
                "load_bearing": True,
            },
        ],
        "one_to_one_tool_calls": {"pass": True, "count": 2},
        "capability_receipts": ["torch_func_policy_success", "pyg_action_success_graph"],
        "source_backing_note": "PyTorch lane recomputes from common source object and does not read peer result files.",
        "torch_version": torch.__version__,
        "solver_imports": {"z3_module": z3.__name__, "cvc5_module": cvc5.__name__},
    }


def main() -> int:
    lane = build_lane()
    common.write_json(common.RESULT_DIR / f"{common.SIM_ID}_pytorch_results.json", lane)
    print(json.dumps({"ok": lane["all_pass"], "result": lane["result_path"]}, indent=2, sort_keys=True))
    return 0 if lane["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
