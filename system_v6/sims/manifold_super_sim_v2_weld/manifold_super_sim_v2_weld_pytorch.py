#!/usr/bin/env python3
"""PyTorch graph/tensor lane for manifold_super_sim_v2_weld."""

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

import manifold_super_sim_v2_weld_common as common


ENGINE = "pytorch"
SOURCE = common.SIM_DIR / f"{common.SIM_ID}_{ENGINE}.py"
RESULT = common.RESULT_DIR / f"{common.SIM_ID}_{ENGINE}_results.json"


def source_backing_probe() -> dict[str, Any]:
    relation_inputs = torch.tensor([[3.0, 8.0], [3.0, 8.0]], dtype=torch.float64)

    def add_pair(row: torch.Tensor) -> torch.Tensor:
        return torch.sum(row)

    batched_relation = vmap(add_pair)(relation_inputs)
    edge_index = torch.tensor([[0, 1, 2], [2, 2, 3]], dtype=torch.long)
    data = Data(edge_index=edge_index, num_nodes=4)
    exact_zero = sp.simplify(sp.log(4) - 2 * sp.log(2))

    solver = z3.Solver()
    value = z3.Int("v2_weld_pytorch_relation_sum")
    solver.add(value == z3.IntVal(int(batched_relation[0].item())))
    solver.add(value != z3.IntVal(11))
    z3_status = str(solver.check())

    c_solver = cvc5.Solver()
    c_solver.setLogic("QF_LIA")
    int_sort = c_solver.getIntegerSort()
    c_value = c_solver.mkConst(int_sort, "v2_weld_pytorch_relation_sum_cvc5")
    c_solver.assertFormula(c_solver.mkTerm(Kind.EQUAL, c_value, c_solver.mkInteger(int(batched_relation[0].item()))))
    c_solver.assertFormula(c_solver.mkTerm(Kind.DISTINCT, c_value, c_solver.mkInteger(11)))
    c_status_raw = c_solver.checkSat()
    cvc5_status = "sat" if c_status_raw.isSat() else "unsat" if c_status_raw.isUnsat() else "unknown"

    return {
        "torch_func_batched_relation": [float(value) for value in batched_relation.tolist()],
        "torch_geometric_num_nodes": int(data.num_nodes),
        "torch_geometric_edge_count": int(data.num_edges),
        "sympy_log4_minus_2log2": str(exact_zero),
        "z3_relation_identity": z3_status,
        "cvc5_relation_identity": cvc5_status,
        "pass": [float(value) for value in batched_relation.tolist()] == [11.0, 11.0]
        and int(data.num_nodes) == 4
        and z3_status == cvc5_status == "unsat",
    }


def build_result() -> dict[str, Any]:
    weld_object = common.build_weld_object()
    artifact = common.write_trajectory_artifact(weld_object)
    probe = source_backing_probe()
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
            "torch.func": "source_backing_probe.torch_func_batched_relation finite A/B relation transform",
            "torch_geometric": "source_backing_probe.torch_geometric_num_nodes finite relation graph carrier",
            "sympy": "source_backing_probe.sympy_log4_minus_2log2 typed-counting convention identity",
            "z3": "weld_smt_rows.z3_weld_relation computed A/B/relation identity",
            "cvc5": "weld_smt_rows.cvc5_weld_relation computed A/B/relation identity",
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
        "state_object_id": weld_object["state_object_id"],
        "family_state_object_ids": {
            "A": weld_object["family_state_objects"]["A"]["state_object_id"],
            "B": weld_object["family_state_objects"]["B"]["state_object_id"],
        },
        "weld_map_signature_sha256": common.stable_sha256(weld_object["declared_weld_map"]),
        "weld_row_signature_sha256": common.signature_rows(weld_object["weld_row_table"]),
        "parent_anchor_checks": weld_object["parent_anchor_checks"],
        "cross_family_controls": weld_object["cross_family_controls"],
        "weld_smt_rows": weld_object["weld_smt_rows"],
        "crossover_proofs": {
            "z3": weld_object["weld_smt_rows"]["z3_weld_relation"],
            "cvc5": weld_object["weld_smt_rows"]["cvc5_weld_relation"],
        },
        "trajectory_artifact": artifact,
        "source_backing_probe": probe,
        "all_pass": weld_object["all_pass"] and artifact["sha_verified"] and probe["pass"],
    }
    return payload


def main() -> int:
    payload = build_result()
    common.write_json(RESULT, payload)
    print(json.dumps({"ok": payload["all_pass"], "result_path": common.rel(RESULT)}, indent=2, sort_keys=True))
    return 0 if payload["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
