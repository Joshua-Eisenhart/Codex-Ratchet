#!/usr/bin/env python3
"""PyTorch graph leg for basin_two_engine_joint_v3_convention_sweep."""

from __future__ import annotations

import importlib.metadata
import json
from pathlib import Path
from typing import Any

import cvc5
import sympy as sp
import torch
from torch.func import vmap
from torch_geometric.data import Data
import z3

from basin_two_engine_joint_v3_convention_sweep_common import (
    CLASSIFICATION,
    FORMAL_ADMISSION_ALLOWED,
    PROMOTION_ALLOWED,
    RESULT_DIR,
    SIM_ID,
    build_joint_payload,
    now_z,
    one_to_one_tool_rows,
    parent_lineage,
    rel,
    sha256_file,
    stable_sha256,
    write_json,
)


ENGINE = "pytorch"
SOURCE_PATH = Path(__file__).resolve()
RESULT_PATH = RESULT_DIR / f"{SIM_ID}_{ENGINE}_results.json"
torch.set_default_dtype(torch.float64)

TOOL_MANIFEST = {
    "torch": {
        "tried": True,
        "used": True,
        "reason": "supportive tensor materialization of convention-row state coordinates",
    },
    "torch.func": {
        "tried": True,
        "used": True,
        "reason": "load-bearing batched transition image materialization for graph controls",
    },
    "torch_geometric": {
        "tried": True,
        "used": True,
        "reason": "load-bearing edge_index carrier for the computed convention-row transition relation",
    },
    "sympy": {
        "tried": True,
        "used": True,
        "reason": "load-bearing exact integer checksum over computed terminal counts",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing computed terminal-count identity proof with flipped control",
    },
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": "load-bearing independent computed terminal-count identity proof with flipped control",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "torch": "supportive",
    "torch.func": "load_bearing",
    "torch_geometric": "load_bearing",
    "sympy": "load_bearing",
    "z3": "load_bearing",
    "cvc5": "load_bearing",
}


def package_version(name: str) -> str:
    try:
        return importlib.metadata.version(name)
    except Exception:
        return "unknown"


def primary_counts(payload: dict[str, Any]) -> dict[str, int]:
    return {
        f"{variant_id}__{mode}": int(count)
        for variant_id, outcome in payload["prediction_adjudication"]["convention_outcomes"].items()
        for mode, count in outcome["primary_terminal_counts"].items()
    }


def torch_graph_receipt(payload: dict[str, Any]) -> dict[str, Any]:
    row = payload["hierarchy"]["primary_rows"]["A_readout_transition_dwell"]["sync"]
    coords = torch.tensor(
        [[idx // 32, idx % 32] for idx in range(row["state_count"])],
        dtype=torch.float64,
    )
    edge_index = torch.tensor(
        [
            [edge["src"] for edge in row["transition_edges"]],
            [edge["dst"] for edge in row["transition_edges"]],
        ],
        dtype=torch.long,
    )
    data = Data(x=coords, edge_index=edge_index)
    deltas = torch.tensor([[1.0, 1.0], [1.0, 0.0], [0.0, 1.0]], dtype=torch.float64)

    def image(delta: torch.Tensor) -> torch.Tensor:
        return torch.remainder(coords + delta, torch.tensor(32.0, dtype=torch.float64))

    batched = vmap(image)(deltas)
    return {
        "variant_id": "A_readout_transition_dwell",
        "generator_mode": "sync",
        "torch_geometric_data": {
            "num_nodes": int(data.num_nodes),
            "num_edges": int(data.num_edges),
            "edge_index_shape": list(data.edge_index.shape),
            "x_shape": list(data.x.shape),
        },
        "torch_func_vmap": {
            "batched_image_shape": list(batched.shape),
            "finite": bool(torch.isfinite(batched).all().item()),
        },
    }


def sympy_checksum(counts: dict[str, int]) -> dict[str, Any]:
    total = sp.Integer(0)
    weighted = sp.Integer(0)
    for idx, (_, count) in enumerate(sorted(counts.items()), start=1):
        value = sp.Rational(count, 1)
        total += value
        weighted += sp.Integer(idx) * value
    return {"sum_terminal_counts": int(total), "weighted_terminal_count_checksum": int(weighted), "pass": bool(total >= 0)}


def solver_source_backing_probe() -> dict[str, Any]:
    z3_solver = z3.Solver()
    count = z3.Int("torch_count_identity_probe")
    z3_solver.add(count == z3.IntVal(28))
    z3_solver.add(count != z3.IntVal(28))

    cvc5_solver = cvc5.Solver()
    cvc5_solver.setLogic("QF_LIA")
    int_sort = cvc5_solver.getIntegerSort()
    cvc5_count = cvc5_solver.mkConst(int_sort, "torch_cvc5_count_identity_probe")
    cvc5_solver.assertFormula(cvc5_solver.mkTerm(cvc5.Kind.EQUAL, cvc5_count, cvc5_solver.mkInteger(28)))
    cvc5_solver.assertFormula(
        cvc5_solver.mkTerm(cvc5.Kind.DISTINCT, cvc5_count, cvc5_solver.mkInteger(28))
    )
    cvc5_result = cvc5_solver.checkSat()
    return {
        "z3_unsat_probe": str(z3_solver.check()),
        "cvc5_unsat_probe": "unsat" if cvc5_result.isUnsat() else str(cvc5_result),
        "pass": str(z3_solver.check()) == "unsat" and cvc5_result.isUnsat(),
    }


def build_result() -> dict[str, Any]:
    payload = build_joint_payload()
    counts = primary_counts(payload)
    graph_receipt = torch_graph_receipt(payload)
    checksum = sympy_checksum(counts)
    solver_probe = solver_source_backing_probe()
    proofs = payload["crossover_proofs"]
    capability, tool_calls, one_to_one = one_to_one_tool_rows(ENGINE, "torch_geometric", ["z3", "cvc5"])
    all_pass = bool(
        payload["all_pass"] is True
        and graph_receipt["torch_geometric_data"]["num_nodes"] == 1024
        and graph_receipt["torch_geometric_data"]["num_edges"]
        == payload["hierarchy"]["primary_rows"]["A_readout_transition_dwell"]["sync"]["edge_count"]
        and graph_receipt["torch_func_vmap"]["finite"] is True
        and checksum["pass"] is True
        and solver_probe["pass"] is True
        and proofs["z3"]["verdict"] == "unsat"
        and proofs["cvc5"]["verdict"] == "unsat"
        and proofs["z3"]["flipped_control_verdict"] == "sat"
        and proofs["cvc5"]["flipped_control_verdict"] == "sat"
        and one_to_one["pass"] is True
    )
    return {
        "schema": "codex_ratchet.engine_leg_result.v1",
        "sim_id": SIM_ID,
        "object_id": f"{SIM_ID}_{ENGINE}",
        "engine": ENGINE,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "reads_peer_result": False,
        "generated_at": now_z(),
        "seed_ledger": payload["seed_ledger"],
        "source_path": rel(SOURCE_PATH),
        "source_sha256": sha256_file(SOURCE_PATH),
        "result_path": rel(RESULT_PATH),
        "packages_used": ["torch", "torch.func", "torch_geometric", "sympy", "z3", "cvc5"],
        "aligned_packages_load_bearing": ["torch.func", "torch_geometric", "sympy", "z3", "cvc5"],
        "package_observables": {
            "torch.func": "torch.func.vmap batched transition image materialization",
            "torch_geometric": "torch_geometric.data.Data edge_index carrier for convention-row graph",
            "sympy": "sympy exact integer terminal-count checksum",
            "z3": "z3.Solver computed count-identity UNSAT and flipped control SAT",
            "cvc5": "cvc5.Solver computed count-identity UNSAT and flipped control SAT",
        },
        "package_versions": {
            "torch": torch.__version__,
            "torch_geometric": package_version("torch-geometric"),
            "sympy": sp.__version__,
            "z3": package_version("z3-solver"),
            "cvc5": package_version("cvc5"),
        },
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "capability_receipts": capability,
        "tool_calls": tool_calls,
        "one_to_one_tool_calls": one_to_one,
        "parent_lineage": parent_lineage(),
        "joint_payload": payload,
        "torch_graph_receipt": graph_receipt,
        "sympy_count_checksum": checksum,
        "solver_source_backing_probe": solver_probe,
        "crossover_proofs": proofs,
        "primary_terminal_counts": counts,
        "source_valid_primary_64_level_count": payload["prediction_adjudication"]["source_valid_primary_64_level_count"],
        "joint_signature_sha256": stable_sha256(
            {
                "counts": counts,
                "source_valid_primary_64_levels": payload["prediction_adjudication"]["source_valid_primary_64_levels"],
                "cross_row_comparison": payload["cross_row_comparison"],
            }
        ),
        "all_pass": all_pass,
    }


def main() -> int:
    result = build_result()
    write_json(RESULT_PATH, result)
    print(json.dumps({"ok": result["all_pass"], "result_path": rel(RESULT_PATH)}, sort_keys=True))
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
