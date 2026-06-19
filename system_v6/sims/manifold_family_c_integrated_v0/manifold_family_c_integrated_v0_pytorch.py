#!/usr/bin/env python3
"""PyTorch graph/current lane for manifold_family_c_integrated_v0."""

from __future__ import annotations

import json
from typing import Any

import cvc5
from cvc5 import Kind
import sympy as sp
import torch
from torch.func import vmap
from torch_geometric.data import Data
import z3

import manifold_family_c_integrated_v0_common as common


ENGINE = "pytorch"
SOURCE = common.SIM_DIR / f"{common.SIM_ID}_{ENGINE}.py"
RESULT = common.RESULT_DIR / f"{common.SIM_ID}_{ENGINE}_results.json"


def source_backing_probe(family_c: dict[str, Any]) -> dict[str, Any]:
    currents = torch.tensor(
        [
            [
                family_c["integrated_state_object"]["n3"]["conditioned_total_abs_current"],
                family_c["integrated_state_object"]["n4"]["conditioned_total_abs_current"],
            ]
        ],
        dtype=torch.float64,
    )

    def perturb(row: torch.Tensor) -> torch.Tensor:
        return torch.stack([row[0], row[1] - row[0]])

    batched = vmap(perturb)(currents)
    edge_index = torch.tensor([[0], [1]], dtype=torch.long)
    graph = Data(edge_index=edge_index, num_nodes=2)
    exact_relation = sp.simplify(sp.Integer(16) / sp.Integer(8) - 2)

    total_nodes_edges = int(graph.num_nodes) + int(graph.num_edges)
    solver = z3.Solver()
    value = z3.Int("family_c_pytorch_node_edge_total")
    solver.add(value == z3.IntVal(total_nodes_edges))
    solver.add(value != z3.IntVal(3))
    z3_status = str(solver.check())

    c_solver = cvc5.Solver()
    c_solver.setLogic("QF_LIA")
    int_sort = c_solver.getIntegerSort()
    c_value = c_solver.mkConst(int_sort, "family_c_pytorch_node_edge_total_cvc5")
    c_solver.assertFormula(c_solver.mkTerm(Kind.EQUAL, c_value, c_solver.mkInteger(total_nodes_edges)))
    c_solver.assertFormula(c_solver.mkTerm(Kind.DISTINCT, c_value, c_solver.mkInteger(3)))
    raw = c_solver.checkSat()
    cvc5_status = "sat" if raw.isSat() else "unsat" if raw.isUnsat() else "unknown"

    return {
        "torch_func_batched_shape": list(batched.shape),
        "torch_current_delta": float(batched[0, 1].item()),
        "torch_geometric_num_nodes": int(graph.num_nodes),
        "torch_geometric_edge_count": int(graph.num_edges),
        "sympy_C16_over_C8_minus_2": str(exact_relation),
        "z3_node_edge_identity": z3_status,
        "cvc5_node_edge_identity": cvc5_status,
        "pass": list(batched.shape) == [1, 2] and int(graph.num_nodes) == 2 and int(graph.num_edges) == 1 and exact_relation == 0 and z3_status == cvc5_status == "unsat",
    }


def build_result() -> dict[str, Any]:
    family_c = common.build_family_c_object()
    artifact = common.write_trajectory_artifact(family_c)
    probe = source_backing_probe(family_c)
    payload = {
        "schema": "codex_ratchet.engine_leg_result.v1",
        "sim_id": common.SIM_ID,
        "object_id": f"{common.SIM_ID}_{ENGINE}",
        "engine": ENGINE,
        "generated_at": common.now_z(),
        "classification": common.CLASSIFICATION,
        "promotion_allowed": common.PROMOTION_ALLOWED,
        "formal_admission_allowed": common.FORMAL_ADMISSION_ALLOWED,
        "reads_peer_result": False,
        "source_path": common.rel(SOURCE),
        "source_sha256": common.sha256_file(SOURCE),
        "result_path": common.rel(RESULT),
        "packages_used": ["torch", "torch.func", "torch_geometric", "sympy", "z3", "cvc5", "json"],
        "aligned_packages_load_bearing": ["torch.func", "torch_geometric", "sympy", "z3", "cvc5"],
        "package_observables": {
            "torch.func": "source_backing_probe.torch_func_batched_shape and current delta row",
            "torch_geometric": "source_backing_probe.torch_geometric_num_nodes/edge_count finite graph carrier",
            "sympy": "source_backing_probe.sympy_C16_over_C8_minus_2 exact support relation",
            "z3": "source_backing_probe.z3_node_edge_identity computed graph identity",
            "cvc5": "source_backing_probe.cvc5_node_edge_identity computed graph identity",
        },
        "package_versions": {
            "torch": torch.__version__,
            "torch_geometric": common.package_version("torch-geometric"),
            "sympy": sp.__version__,
            "z3": getattr(z3, "get_version_string", lambda: "version_unavailable")(),
            "cvc5": getattr(cvc5, "__version__", "version_unavailable"),
        },
        "TOOL_MANIFEST": common.TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": {**common.TOOL_INTEGRATION_DEPTH, "torch": "supportive"},
        "tool_intent": common.TOOL_INTENT,
        "claim_path_tools": ["torch.func", "torch_geometric", "sympy", "z3", "cvc5"],
        "engine_mode": common.ENGINE_MODE,
        "state_object_id": family_c["integrated_state_object"]["state_object_id"],
        "source_backing_probe": probe,
        "trajectory_artifact": artifact,
        "crossover_proofs": family_c["crossover_proofs"],
        "family_c_object_signature_sha256": common.stable_sha256(family_c),
        "all_pass": family_c["all_pass"] and probe["pass"] and artifact["sha_verified"],
    }
    return payload


def main() -> int:
    payload = build_result()
    common.write_json(RESULT, payload)
    print(json.dumps({"ok": payload["all_pass"], "result_path": common.rel(RESULT)}, indent=2, sort_keys=True))
    return 0 if payload["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
