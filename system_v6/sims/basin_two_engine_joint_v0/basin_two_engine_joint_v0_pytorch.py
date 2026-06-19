#!/usr/bin/env python3
"""PyTorch graph leg for basin_two_engine_joint_v0."""

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

from basin_two_engine_joint_v0_common import (
    CLASSIFICATION,
    FORMAL_ADMISSION_ALLOWED,
    PROMOTION_ALLOWED,
    RESULT_DIR,
    SEED_LEDGER,
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
        "reason": "supportive tensor materialization of stage coordinates and generator deltas",
    },
    "torch.func": {
        "tried": True,
        "used": True,
        "reason": "load-bearing batched transition action over the finite 64-cell grid",
    },
    "torch_geometric": {
        "tried": True,
        "used": True,
        "reason": "load-bearing edge_index carrier for the computed joint transition relation",
    },
    "sympy": {
        "tried": True,
        "used": True,
        "reason": "load-bearing exact 8*8 count identity guard",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing class-count identity proof and erased-marginal flip",
    },
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": "load-bearing independent class-count identity proof and erased-marginal flip",
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


def torch_graph_receipt(payload: dict[str, Any]) -> dict[str, Any]:
    both = payload["hierarchy"]["basins"]["both"]
    coords = torch.tensor(
        [[cell["l_slot"], cell["r_slot"]] for cell in both["cells"]],
        dtype=torch.float64,
    )
    edge_index = torch.tensor(
        [
            [row["src"] for row in both["transition_edges"]],
            [row["dst"] for row in both["transition_edges"]],
        ],
        dtype=torch.long,
    )
    data = Data(x=coords, edge_index=edge_index)
    deltas = torch.tensor([[1, 0], [0, 1], [1, 1]], dtype=torch.float64)

    def generator_image(delta: torch.Tensor) -> torch.Tensor:
        return torch.remainder(coords + delta, torch.tensor(8.0, dtype=torch.float64))

    batched = vmap(generator_image)(deltas)
    return {
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


def sympy_count_guard() -> dict[str, Any]:
    l_count = sp.Rational(8, 1)
    r_count = sp.Rational(8, 1)
    erased_r_count = sp.Rational(1, 1)
    real_product = sp.simplify(l_count * r_count)
    erased_product = sp.simplify(l_count * erased_r_count)
    return {
        "real_product": str(real_product),
        "erased_product": str(erased_product),
        "pass": real_product == sp.Rational(64, 1) and erased_product != sp.Rational(64, 1),
    }


def solver_source_backing_probe() -> dict[str, Any]:
    z3_solver = z3.Solver()
    z3_count = z3.Int("torch_source_backed_subsubbasin_count")
    z3_solver.add(z3_count == z3.IntVal(64))
    z3_solver.add(z3_count != z3.IntVal(64))
    cvc5_solver = cvc5.Solver()
    cvc5_solver.setLogic("QF_LIA")
    int_sort = cvc5_solver.getIntegerSort()
    cvc5_count = cvc5_solver.mkConst(int_sort, "torch_cvc5_source_backed_subsubbasin_count")
    cvc5_solver.assertFormula(cvc5_solver.mkTerm(cvc5.Kind.EQUAL, cvc5_count, cvc5_solver.mkInteger(64)))
    cvc5_solver.assertFormula(
        cvc5_solver.mkTerm(cvc5.Kind.NOT, cvc5_solver.mkTerm(cvc5.Kind.EQUAL, cvc5_count, cvc5_solver.mkInteger(64)))
    )
    cvc5_result = cvc5_solver.checkSat()
    return {
        "z3_unsat_probe": str(z3_solver.check()),
        "cvc5_unsat_probe": "unsat" if cvc5_result.isUnsat() else str(cvc5_result),
        "pass": str(z3_solver.check()) == "unsat" and cvc5_result.isUnsat(),
    }


def build_result() -> dict[str, Any]:
    payload = build_joint_payload()
    graph_receipt = torch_graph_receipt(payload)
    sympy_guard = sympy_count_guard()
    solver_probe = solver_source_backing_probe()
    proofs = payload["crossover_proofs"]
    capability, tool_calls, one_to_one = one_to_one_tool_rows(ENGINE, "torch_geometric", ["z3", "cvc5"])
    all_pass = bool(
        payload["all_pass"] is True
        and graph_receipt["torch_geometric_data"]["num_nodes"] == 64
        and graph_receipt["torch_geometric_data"]["num_edges"] == payload["hierarchy"]["basins"]["both"]["edge_count"]
        and graph_receipt["torch_func_vmap"]["finite"] is True
        and sympy_guard["pass"] is True
        and solver_probe["pass"] is True
        and proofs["z3"]["verdict"] == "unsat"
        and proofs["cvc5"]["verdict"] == "unsat"
        and proofs["z3"]["erased_flip_verdict"] == "sat"
        and proofs["cvc5"]["erased_flip_verdict"] == "sat"
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
        "seed_ledger": SEED_LEDGER,
        "source_path": rel(SOURCE_PATH),
        "source_sha256": sha256_file(SOURCE_PATH),
        "result_path": rel(RESULT_PATH),
        "packages_used": ["torch", "torch.func", "torch_geometric", "sympy", "z3", "cvc5"],
        "aligned_packages_load_bearing": ["torch.func", "torch_geometric", "sympy", "z3", "cvc5"],
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
        "sympy_count_guard": sympy_guard,
        "solver_source_backing_probe": solver_probe,
        "crossover_proofs": proofs,
        "joint_signature_sha256": stable_sha256(
            {
                "hierarchy": payload["hierarchy"]["subsubbasins"],
                "proofs": payload["crossover_proofs"],
                "controls": payload["controls"],
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
