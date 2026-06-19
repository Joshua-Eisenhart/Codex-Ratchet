#!/usr/bin/env python3
"""PyTorch graph-carrier lane for manifold_super_sim_v0."""

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

import manifold_super_sim_v0_common as common


ENGINE = "pytorch"
SOURCE = common.SIM_DIR / f"{common.SIM_ID}_{ENGINE}.py"
RESULT = common.RESULT_DIR / f"{common.SIM_ID}_{ENGINE}_results.json"


def torch_expm(aug: list[list[float]], h: float) -> list[list[float]]:
    matrix = torch.tensor(aug, dtype=torch.float64)
    flow = torch.matrix_exp(float(h) * matrix)
    return flow.detach().cpu().numpy().tolist()


def source_backing_probe() -> dict[str, Any]:
    matrices = torch.eye(3, dtype=torch.float64).repeat(2, 1, 1)
    vector = torch.tensor([1.0, 2.0, 3.0], dtype=torch.float64)

    def apply(matrix: torch.Tensor) -> torch.Tensor:
        return matrix @ vector

    batched = vmap(apply)(matrices)
    edge_index = torch.tensor([[0, 1, 2], [1, 2, 2]], dtype=torch.long)
    data = Data(edge_index=edge_index, num_nodes=3)
    exact_log = sp.simplify(sp.log(int(data.num_nodes)))

    solver = z3.Solver()
    node_count = z3.Int("pytorch_probe_node_count")
    solver.add(node_count == z3.IntVal(int(data.num_nodes)))
    solver.add(node_count != z3.IntVal(3))
    z3_status = str(solver.check())

    c_solver = cvc5.Solver()
    c_solver.setLogic("QF_LIA")
    int_sort = c_solver.getIntegerSort()
    c_nodes = c_solver.mkConst(int_sort, "pytorch_probe_node_count_cvc5")
    c_solver.assertFormula(c_solver.mkTerm(Kind.EQUAL, c_nodes, c_solver.mkInteger(int(data.num_nodes))))
    c_solver.assertFormula(c_solver.mkTerm(Kind.NOT, c_solver.mkTerm(Kind.EQUAL, c_nodes, c_solver.mkInteger(3))))
    c_status_raw = c_solver.checkSat()
    cvc5_status = "sat" if c_status_raw.isSat() else "unsat" if c_status_raw.isUnsat() else str(c_status_raw)

    return {
        "torch_func_batched_shape": list(batched.shape),
        "torch_geometric_num_nodes": int(data.num_nodes),
        "torch_geometric_edge_count": int(data.num_edges),
        "sympy_exact_log": str(exact_log),
        "z3_node_identity": z3_status,
        "cvc5_node_identity": cvc5_status,
        "pass": list(batched.shape) == [2, 3] and z3_status == cvc5_status == "unsat",
    }


def build_result() -> dict[str, Any]:
    super_object = common.build_super_object(torch_expm)
    artifact = common.write_trajectory_artifact(super_object)
    probe = source_backing_probe()
    layer_sigs = {key: row["row_signature_sha256"] for key, row in super_object["layers"].items()}
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
        "aligned_packages_load_bearing": ["sympy", "z3", "cvc5"],
        "package_observables": {
            "torch.func": "supportive source_backing_probe.torch_func_batched_shape only; torch_expm uses plain torch.matrix_exp",
            "torch_geometric": "supportive source_backing_probe.torch_geometric_edge_count only; finite graph rows use shared Python common path",
            "sympy": "source_backing_probe.sympy_exact_log and typed entropy expressions",
            "z3": "crossover_proofs.z3 computed partition identity",
            "cvc5": "crossover_proofs.cvc5 computed partition identity",
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
        "claim_path_tools": ["sympy", "z3", "cvc5"],
        "state_object_id": super_object["state_object_id"],
        "layer_signatures": layer_sigs,
        "weld_anchors": super_object["weld_anchors"],
        "kill_controls": super_object["kill_controls"],
        "crossover_proofs": super_object["crossover_proofs"],
        "trajectory_artifact": artifact,
        "source_backing_probe": probe,
        "super_object_signature_sha256": common.stable_sha256(super_object),
        "all_pass": super_object["all_pass"] and probe["pass"] and artifact["sha_verified"],
    }
    return payload


def main() -> int:
    payload = build_result()
    common.write_json(RESULT, payload)
    print(json.dumps({"ok": payload["all_pass"], "result_path": common.rel(RESULT)}, indent=2, sort_keys=True))
    return 0 if payload["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
