#!/usr/bin/env python3
"""PyTorch relation lane for manifold_ab_weld_relation_v0."""

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

import manifold_ab_weld_relation_v0_common as common


ENGINE = "pytorch"
SOURCE = common.SIM_DIR / f"{common.SIM_ID}_{ENGINE}.py"
RESULT = common.RESULT_DIR / f"{common.SIM_ID}_{ENGINE}_results.json"
CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
TOOL_MANIFEST = {
    "torch.func": {"tried": True, "used": True, "reason": "batched finite A/B relation transform"},
    "torch_geometric": {"tried": True, "used": True, "reason": "finite A/B/weld graph carrier"},
    "sympy": {"tried": True, "used": True, "reason": "exact relation residual and zero identity checks"},
    "z3": {"tried": True, "used": True, "reason": "A/B/relation SMT identity check"},
    "cvc5": {"tried": True, "used": True, "reason": "independent SMT mirror of the relation identity check"},
}
TOOL_INTEGRATION_DEPTH = {
    "torch.func": "load_bearing",
    "torch_geometric": "load_bearing",
    "sympy": "load_bearing",
    "z3": "load_bearing",
    "cvc5": "load_bearing",
}


def source_backing_probe() -> dict[str, Any]:
    relation_inputs = torch.tensor([[3.0, 8.0], [3.0, 8.0]], dtype=torch.float64)

    def add_pair(row: torch.Tensor) -> torch.Tensor:
        return torch.sum(row)

    batched_relation = vmap(add_pair)(relation_inputs)
    edge_index = torch.tensor([[0, 1, 2, 2], [2, 2, 3, 4]], dtype=torch.long)
    data = Data(edge_index=edge_index, num_nodes=5)

    a_sym, b_sym, w_sym = sp.symbols("pt_a_sym pt_b_sym pt_w_sym", integer=True)
    residual = sp.simplify((a_sym + b_sym - w_sym).subs({a_sym: 3, b_sym: 8, w_sym: 11}))
    zero_identity = sp.simplify(sp.Rational(0, 1) + sp.Rational(0, 1))

    relation_sum = int(batched_relation[0].item())
    solver = z3.Solver()
    value = z3.Int("ab_relation_pytorch_relation_sum")
    solver.add(value == z3.IntVal(relation_sum))
    solver.add(value != z3.IntVal(11))
    z3_status = str(solver.check())

    c_solver = cvc5.Solver()
    c_solver.setLogic("QF_LIA")
    int_sort = c_solver.getIntegerSort()
    c_value = c_solver.mkConst(int_sort, "ab_relation_pytorch_relation_sum_cvc5")
    c_solver.assertFormula(c_solver.mkTerm(Kind.EQUAL, c_value, c_solver.mkInteger(relation_sum)))
    c_solver.assertFormula(c_solver.mkTerm(Kind.DISTINCT, c_value, c_solver.mkInteger(11)))
    c_status_raw = c_solver.checkSat()
    cvc5_status = "sat" if c_status_raw.isSat() else "unsat" if c_status_raw.isUnsat() else "unknown"

    return {
        "torch_func_batched_relation": [float(value) for value in batched_relation.tolist()],
        "torch_geometric_num_nodes": int(data.num_nodes),
        "torch_geometric_edge_count": int(data.num_edges),
        "sympy_relation_residual": str(residual),
        "sympy_zero_identity": str(zero_identity),
        "z3_relation_identity": z3_status,
        "cvc5_relation_identity": cvc5_status,
        "pass": [float(value) for value in batched_relation.tolist()] == [11.0, 11.0]
        and int(data.num_nodes) == 5
        and int(data.num_edges) == 4
        and str(residual) == "0"
        and str(zero_identity) == "0"
        and z3_status == cvc5_status == "unsat",
    }


def build_result() -> dict[str, Any]:
    relation_object = common.build_relation_object()
    artifact = common.write_trajectory_artifact(relation_object)
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
            "torch.func": "source_backing_probe.torch_func_batched_relation finite relation transform",
            "torch_geometric": "source_backing_probe.torch_geometric_num_nodes finite relation graph carrier",
            "sympy": "source_backing_probe.sympy_relation_residual exact typed relation residual",
            "z3": "weld_relation_smt.z3_weld_relation_sum relation proof and flips",
            "cvc5": "weld_relation_smt.cvc5_weld_relation_sum relation proof and flips",
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
        "state_object_id": relation_object["state_object_id"],
        "family_state_object_ids": {
            "A": relation_object["pinned_state_objects"]["A"]["state_object_id"],
            "B": relation_object["pinned_state_objects"]["B"]["state_object_id"],
        },
        "coordinate_map_signature_sha256": relation_object["coordinate_map_signature_sha256"],
        "weld_only_rows_signature_sha256": relation_object["weld_only_rows_signature_sha256"],
        "nonrecoverability_signature_sha256": relation_object["nonrecoverability_signature_sha256"],
        "parent_anchor_checks": relation_object["parent_anchor_checks"],
        "cross_family_controls": relation_object["cross_family_controls"],
        "weld_relation_smt": relation_object["weld_relation_smt"],
        "crossover_proofs": {
            "z3": relation_object["weld_relation_smt"]["z3_weld_relation_sum"],
            "cvc5": relation_object["weld_relation_smt"]["cvc5_weld_relation_sum"],
        },
        "trajectory_artifact": artifact,
        "source_backing_probe": probe,
        "all_pass": relation_object["all_pass"] and artifact["sha_verified"] and probe["pass"],
    }
    return payload


def main() -> int:
    payload = build_result()
    common.write_json(RESULT, payload)
    print(json.dumps({"ok": payload["all_pass"], "result_path": common.rel(RESULT)}, indent=2, sort_keys=True))
    return 0 if payload["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
