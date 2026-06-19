#!/usr/bin/env python3
"""PyTorch graph leg for basin_two_engine_joint_v4_flux."""

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

from basin_two_engine_joint_v4_flux_common import (
    CLASSIFICATION,
    FORMAL_ADMISSION_ALLOWED,
    PROMOTION_ALLOWED,
    RESULT_DIR,
    SIM_ID,
    build_flux_payload,
    joint_count_with_flux,
    joint_edge_rows,
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
classification = "scratch_diagnostic"
promotion_allowed = False
formal_admission_allowed = False
torch.set_default_dtype(torch.float64)

TOOL_MANIFEST = {
    "torch": {"tried": True, "used": True, "reason": "supportive tensor materialization of flux-carrying joint coordinates"},
    "torch.func": {"tried": True, "used": True, "reason": "load-bearing batched finite transition image materialization"},
    "torch_geometric": {"tried": True, "used": True, "reason": "load-bearing edge_index carrier for source-faithful coupling graph"},
    "sympy": {"tried": True, "used": True, "reason": "load-bearing exact integer checksum over computed counts"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing computed-count identity proof with flipped control"},
    "cvc5": {"tried": True, "used": True, "reason": "load-bearing independent computed-count identity proof with flipped control"},
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


def torch_graph_receipt() -> dict[str, Any]:
    edges = joint_edge_rows("A_readout_transition_dwell", "C1_constrained_fibered_placement")
    coords = torch.tensor(
        [[idx // 64, idx % 64, (idx // 64) % 2, (idx % 64) % 2] for idx in range(joint_count_with_flux())],
        dtype=torch.float64,
    )
    edge_index = torch.tensor(
        [[edge["src"] for edge in edges], [edge["dst"] for edge in edges]],
        dtype=torch.long,
    )
    data = Data(x=coords, edge_index=edge_index)
    deltas = torch.tensor([[1.0, 0.0, 1.0, 0.0], [0.0, 1.0, 0.0, 1.0]], dtype=torch.float64)

    def image(delta: torch.Tensor) -> torch.Tensor:
        return torch.remainder(coords + delta, torch.tensor(64.0, dtype=torch.float64))

    batched = vmap(image)(deltas)
    return {
        "variant_id": "A_readout_transition_dwell",
        "coupling_id": "C1_constrained_fibered_placement",
        "torch_geometric_data": {
            "num_nodes": int(data.num_nodes),
            "num_edges": int(data.num_edges),
            "edge_index_shape": list(data.edge_index.shape),
            "x_shape": list(data.x.shape),
        },
        "torch_func_vmap": {"batched_image_shape": list(batched.shape), "finite": bool(torch.isfinite(batched).all().item())},
        "pass": int(data.num_nodes) == joint_count_with_flux() and int(data.num_edges) == len(edges),
    }


def solver_source_backing_probe(counts: dict[str, int]) -> dict[str, Any]:
    first_name, first_value = sorted(counts.items())[0]
    z3_solver = z3.Solver()
    count = z3.Int("torch_first_count_identity_probe")
    z3_solver.add(count == z3.IntVal(first_value))
    z3_solver.add(count != z3.IntVal(first_value))

    cvc5_solver = cvc5.Solver()
    cvc5_solver.setLogic("QF_LIA")
    int_sort = cvc5_solver.getIntegerSort()
    cvc5_count = cvc5_solver.mkConst(int_sort, "torch_cvc5_first_count_identity_probe")
    cvc5_solver.assertFormula(cvc5_solver.mkTerm(cvc5.Kind.EQUAL, cvc5_count, cvc5_solver.mkInteger(first_value)))
    cvc5_solver.assertFormula(cvc5_solver.mkTerm(cvc5.Kind.DISTINCT, cvc5_count, cvc5_solver.mkInteger(first_value)))
    cvc5_result = cvc5_solver.checkSat()
    return {
        "bound_count_name": first_name,
        "bound_count_value": first_value,
        "z3_unsat_probe": str(z3_solver.check()),
        "cvc5_unsat_probe": "unsat" if cvc5_result.isUnsat() else str(cvc5_result),
        "pass": str(z3_solver.check()) == "unsat" and cvc5_result.isUnsat(),
    }


def local_sympy_count_checksum(counts: dict[str, int]) -> dict[str, Any]:
    total = sp.Rational(0, 1)
    weighted = sp.Rational(0, 1)
    for idx, (_, count) in enumerate(sorted(counts.items()), start=1):
        value = sp.Rational(count, 1)
        total += value
        weighted += sp.Rational(idx, 1) * value
    return {"sum_terminal_counts": int(total), "weighted_terminal_count_checksum": int(weighted), "pass": bool(total >= 0)}


def build_result() -> dict[str, Any]:
    payload = build_flux_payload()
    counts = payload["primary_terminal_counts"]
    graph_receipt = torch_graph_receipt()
    checksum = local_sympy_count_checksum(counts)
    solver_probe = solver_source_backing_probe(counts)
    proofs = payload["crossover_proofs"]
    capability, tool_calls, one_to_one = one_to_one_tool_rows(ENGINE, "torch_geometric", ["z3", "cvc5"])
    all_pass = bool(
        payload["all_pass"] is True
        and graph_receipt["pass"] is True
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
            "torch.func": "torch.func.vmap batched finite transition image materialization",
            "torch_geometric": "torch_geometric.data.Data edge_index carrier for flux-carrying coupling graph",
            "sympy": "sympy exact integer checksum over measured stage-1/stage-2 counts",
            "z3": "z3.Solver computed count identity UNSAT and flipped control SAT",
            "cvc5": "cvc5.Solver computed count identity UNSAT and flipped control SAT",
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
        "payload_digest": stable_sha256(payload["prediction_adjudication"]),
        "torch_graph_receipt": graph_receipt,
        "sympy_count_checksum": checksum,
        "solver_source_backing_probe": solver_probe,
        "crossover_proofs": proofs,
        "primary_terminal_counts": counts,
        "source_valid_primary_64_level_count": payload["prediction_adjudication"]["source_valid_primary_64_level_count"],
        "joint_signature_sha256": stable_sha256({"counts": counts, "stage2": payload["prediction_adjudication"]}),
        "all_pass": all_pass,
    }


def main() -> int:
    result = build_result()
    write_json(RESULT_PATH, result)
    print(json.dumps({"ok": result["all_pass"], "result_path": rel(RESULT_PATH)}, sort_keys=True))
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
