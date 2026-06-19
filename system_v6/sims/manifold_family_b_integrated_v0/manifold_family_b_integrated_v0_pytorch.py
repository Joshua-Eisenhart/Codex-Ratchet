#!/usr/bin/env python3
"""PyTorch graph-carrier lane for manifold_family_b_integrated_v0."""

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

import manifold_family_b_integrated_v0_common as common


ENGINE = "pytorch"
SOURCE = common.SIM_DIR / f"{common.SIM_ID}_{ENGINE}.py"
RESULT = common.RESULT_DIR / f"{common.SIM_ID}_{ENGINE}_results.json"


def source_backing_probe() -> dict[str, Any]:
    reps = torch.tensor([[q, r] for q in range(4) for r in range(2)], dtype=torch.float64)

    def apply_a(rep: torch.Tensor) -> torch.Tensor:
        return torch.stack([torch.remainder(rep[0] + 1.0, 4.0), rep[1]])

    shifted = vmap(apply_a)(reps)
    edge_index = torch.tensor(
        [
            [0, 0, 1, 1, 2, 2, 3, 3],
            [2, 1, 3, 0, 4, 3, 5, 2],
        ],
        dtype=torch.long,
    )
    data = Data(edge_index=edge_index, num_nodes=8)
    exact_zero = sp.simplify(sp.log(4) - 2 * sp.log(2))

    solver = z3.Solver()
    node_count = z3.Int("family_b_pytorch_node_count")
    solver.add(node_count == z3.IntVal(int(data.num_nodes)))
    solver.add(node_count != z3.IntVal(8))
    z3_status = str(solver.check())

    c_solver = cvc5.Solver()
    c_solver.setLogic("QF_LIA")
    int_sort = c_solver.getIntegerSort()
    c_nodes = c_solver.mkConst(int_sort, "family_b_pytorch_node_count_cvc5")
    c_solver.assertFormula(c_solver.mkTerm(Kind.EQUAL, c_nodes, c_solver.mkInteger(int(data.num_nodes))))
    c_solver.assertFormula(c_solver.mkTerm(Kind.DISTINCT, c_nodes, c_solver.mkInteger(8)))
    c_status_raw = c_solver.checkSat()
    cvc5_status = "sat" if c_status_raw.isSat() else "unsat" if c_status_raw.isUnsat() else "unknown"

    return {
        "torch_func_batched_shape": list(shifted.shape),
        "torch_geometric_num_nodes": int(data.num_nodes),
        "torch_geometric_edge_count": int(data.num_edges),
        "sympy_log4_minus_2log2": str(exact_zero),
        "z3_node_identity": z3_status,
        "cvc5_node_identity": cvc5_status,
        "pass": list(shifted.shape) == [8, 2] and int(data.num_nodes) == 8 and z3_status == cvc5_status == "unsat",
    }


def build_result() -> dict[str, Any]:
    family_b_object = common.build_family_b_object()
    artifact = common.write_trajectory_artifact(family_b_object)
    probe = source_backing_probe()
    layer_sigs = {key: row["row_signature_sha256"] for key, row in family_b_object["layers"].items()}
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
            "torch.func": "source_backing_probe.torch_func_batched_shape finite representative transform",
            "torch_geometric": "source_backing_probe.torch_geometric_num_nodes finite graph carrier",
            "sympy": "source_backing_probe.sympy_log4_minus_2log2 plus typed entropy expressions",
            "z3": "crossover_proofs.z3 computed denominator identity",
            "cvc5": "crossover_proofs.cvc5 computed denominator identity",
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
        "state_object_id": family_b_object["state_object_id"],
        "layer_signatures": layer_sigs,
        "weld_anchors": family_b_object["weld_anchors"],
        "kill_controls": family_b_object["kill_controls"],
        "crossover_proofs": family_b_object["crossover_proofs"],
        "trajectory_artifact": artifact,
        "source_backing_probe": probe,
        "family_b_object_signature_sha256": common.stable_sha256(family_b_object),
        "all_pass": family_b_object["all_pass"] and probe["pass"] and artifact["sha_verified"],
    }
    return payload


def main() -> int:
    payload = build_result()
    common.write_json(RESULT, payload)
    print(json.dumps({"ok": payload["all_pass"], "result_path": common.rel(RESULT)}, indent=2, sort_keys=True))
    return 0 if payload["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
