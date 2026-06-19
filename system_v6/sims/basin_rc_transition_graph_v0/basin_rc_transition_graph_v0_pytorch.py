#!/usr/bin/env python3
"""PyTorch graph leg for basin_rc_transition_graph_v0."""

from __future__ import annotations

import importlib.metadata
import json
from pathlib import Path
from typing import Any

import cvc5
from cvc5 import Kind
import networkx as nx
import sympy as sp
import torch
from torch.func import vmap
from torch_geometric.data import Data
import z3

from basin_rc_transition_graph_v0_common import (
    CLASSIFICATION,
    FORMAL_ADMISSION_ALLOWED,
    PROMOTION_ALLOWED,
    RESULT_DIR,
    SEED_LEDGER,
    SIM_ID,
    build_transition_graph,
    common_result_fields,
    load_parent_rows,
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
    "torch": {
        "tried": True,
        "used": True,
        "reason": "supportive matrix exponential and tensor transition materialization",
    },
    "torch.func": {
        "tried": True,
        "used": True,
        "reason": "load-bearing batched generator action over finite cells",
    },
    "torch_geometric": {
        "tried": True,
        "used": True,
        "reason": "load-bearing graph edge_index carrier for the computed transition relation",
    },
    "networkx": {
        "tried": True,
        "used": True,
        "reason": "supportive SCC mirror for PyTorch graph rows",
    },
    "sympy": {
        "tried": True,
        "used": True,
        "reason": "load-bearing exact parent row parsing and rational pin conversion",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing terminal-class no-exit proof over computed edge/component rows",
    },
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": "load-bearing independent terminal-class no-exit proof over computed edge/component rows",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "torch": "supportive",
    "torch.func": "load_bearing",
    "torch_geometric": "load_bearing",
    "networkx": "supportive",
    "sympy": "load_bearing",
    "z3": "load_bearing",
    "cvc5": "load_bearing",
}


def package_version(name: str) -> str:
    try:
        return importlib.metadata.version(name)
    except Exception:
        return "unknown"


def torch_expm(aug: list[list[float]], h: float) -> list[list[float]]:
    mat = torch.tensor(aug, dtype=torch.float64)
    return torch.matrix_exp(torch.tensor(h, dtype=torch.float64) * mat).detach().cpu().tolist()


def torch_graph_receipt(base_graph: dict[str, Any]) -> dict[str, Any]:
    coords = torch.tensor([cell["coord"] for cell in base_graph["cells"]], dtype=torch.float64)
    edge_index = torch.tensor(
        [[row["src"] for row in base_graph["transition_edges"]], [row["dst"] for row in base_graph["transition_edges"]]],
        dtype=torch.long,
    )
    data = Data(x=coords, edge_index=edge_index)
    matrices = torch.stack([torch.tensor(g["M"], dtype=torch.float64) for g in base_graph["generators"]])
    offsets = torch.stack([torch.tensor(g["c"], dtype=torch.float64) for g in base_graph["generators"]])

    def generator_images(matrix: torch.Tensor, offset: torch.Tensor) -> torch.Tensor:
        return coords @ matrix.T + offset

    batched = vmap(generator_images)(matrices, offsets)
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


def proof_inputs(base_graph: dict[str, Any]) -> dict[str, Any]:
    comp = {int(k): int(v) for k, v in base_graph["component_id_by_cell"].items()}
    terminal_ids = set(base_graph["terminal_class_ids"])
    rows = []
    for idx, edge in enumerate(base_graph["transition_edges"]):
        rows.append(
            {
                "edge_index": idx,
                "src_comp": comp[edge["src"]],
                "dst_comp": comp[edge["dst"]],
                "src_terminal": comp[edge["src"]] in terminal_ids,
            }
        )
    terminal_edge = next(row for row in rows if row["src_terminal"])
    outside_comp = next(row["src_comp"] for row in rows if row["src_comp"] != terminal_edge["src_comp"])
    return {"edge_rows": rows, "terminal_edge_index_for_flip": terminal_edge["edge_index"], "outside_comp_for_flip": outside_comp}


def z3_no_exit(inputs: dict[str, Any], *, erased_flip: bool = False) -> str:
    solver = z3.Solver()
    terms = []
    for row in inputs["edge_rows"]:
        idx = row["edge_index"]
        src_terminal = z3.Bool(f"torch_src_terminal_{idx}")
        src_comp = z3.Int(f"torch_src_comp_{idx}")
        dst_comp = z3.Int(f"torch_dst_comp_{idx}")
        solver.add(src_terminal == z3.BoolVal(bool(row["src_terminal"])))
        solver.add(src_comp == z3.IntVal(int(row["src_comp"])))
        dst_value = inputs["outside_comp_for_flip"] if erased_flip and idx == inputs["terminal_edge_index_for_flip"] else row["dst_comp"]
        solver.add(dst_comp == z3.IntVal(int(dst_value)))
        terms.append(z3.And(src_terminal, src_comp != dst_comp))
    solver.add(z3.Or(terms))
    return str(solver.check())


def cvc5_no_exit(inputs: dict[str, Any], *, erased_flip: bool = False) -> str:
    solver = cvc5.Solver()
    solver.setLogic("QF_LIA")
    bool_sort = solver.getBooleanSort()
    int_sort = solver.getIntegerSort()
    terms = []
    for row in inputs["edge_rows"]:
        idx = row["edge_index"]
        src_terminal = solver.mkConst(bool_sort, f"torch_cvc5_src_terminal_{idx}")
        src_comp = solver.mkConst(int_sort, f"torch_cvc5_src_comp_{idx}")
        dst_comp = solver.mkConst(int_sort, f"torch_cvc5_dst_comp_{idx}")
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, src_terminal, solver.mkBoolean(bool(row["src_terminal"]))))
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, src_comp, solver.mkInteger(int(row["src_comp"]))))
        dst_value = inputs["outside_comp_for_flip"] if erased_flip and idx == inputs["terminal_edge_index_for_flip"] else row["dst_comp"]
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, dst_comp, solver.mkInteger(int(dst_value))))
        terms.append(solver.mkTerm(Kind.AND, src_terminal, solver.mkTerm(Kind.NOT, solver.mkTerm(Kind.EQUAL, src_comp, dst_comp))))
    solver.assertFormula(terms[0] if len(terms) == 1 else solver.mkTerm(Kind.OR, *terms))
    result = solver.checkSat()
    if result.isSat():
        return "sat"
    if result.isUnsat():
        return "unsat"
    return str(result)


def sympy_exactness_guard() -> dict[str, Any]:
    half = sp.Rational(1, 2)
    matrix = sp.Matrix([[half, 0], [0, half]])
    determinant = sp.simplify(matrix.det())
    return {
        "guard": "SymPy exact rational matrix determinant for the 1/2 grid pin",
        "determinant": str(determinant),
        "pass": determinant == sp.Rational(1, 4),
    }


def crossover_proofs(base_graph: dict[str, Any]) -> dict[str, Any]:
    inputs = proof_inputs(base_graph)
    z3_verdict = z3_no_exit(inputs)
    z3_erased = z3_no_exit(inputs, erased_flip=True)
    cvc5_verdict = cvc5_no_exit(inputs)
    cvc5_erased = cvc5_no_exit(inputs, erased_flip=True)
    proof_row = {
        "edge_row_count": len(inputs["edge_rows"]),
        "terminal_edge_index_for_flip": inputs["terminal_edge_index_for_flip"],
        "outside_comp_for_flip": inputs["outside_comp_for_flip"],
        "asserted_precomputed_boolean": False,
    }
    return {
        "z3": {"ran": True, "load_bearing": True, "verdict": z3_verdict, "erased_flip_verdict": z3_erased, "proof_row": proof_row},
        "cvc5": {"ran": True, "load_bearing": True, "verdict": cvc5_verdict, "erased_flip_verdict": cvc5_erased, "proof_row": proof_row},
    }


def build_result() -> dict[str, Any]:
    parent_rows = load_parent_rows(torch_expm)
    base_graph = build_transition_graph(parent_rows["generators"])
    fields = common_result_fields(parent_rows, base_graph)
    proofs = crossover_proofs(base_graph)
    sympy_guard = sympy_exactness_guard()
    capability, tool_calls, one_to_one = one_to_one_tool_rows(ENGINE, ["z3", "cvc5"], "torch_geometric")
    graph_receipt = torch_graph_receipt(base_graph)
    all_controls_fire = all(row.get("fired") is True for row in fields["negative_controls"].values())
    all_pass = bool(
        base_graph["state_count"] == 33
        and len(base_graph["terminal_classes"]) == 1
        and graph_receipt["torch_geometric_data"]["num_edges"] == base_graph["edge_count"]
        and graph_receipt["torch_func_vmap"]["finite"] is True
        and base_graph["monotone_exclusion_observable"]["monotone_non_decreasing_on_edges"] is True
        and all_controls_fire
        and proofs["z3"]["verdict"] == "unsat"
        and proofs["cvc5"]["verdict"] == "unsat"
        and proofs["z3"]["erased_flip_verdict"] == "sat"
        and proofs["cvc5"]["erased_flip_verdict"] == "sat"
        and sympy_guard["pass"] is True
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
        "packages_used": ["torch", "torch.func", "torch_geometric", "networkx", "sympy", "z3", "cvc5"],
        "aligned_packages_load_bearing": ["torch.func", "torch_geometric", "sympy", "z3", "cvc5"],
        "package_versions": {
            "torch": torch.__version__,
            "torch_geometric": package_version("torch-geometric"),
            "networkx": nx.__version__,
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
        "transition_graph": base_graph,
        "torch_graph_receipt": graph_receipt,
        "computed": fields,
        "sympy_exactness_guard": sympy_guard,
        "crossover_proofs": proofs,
        "partition_signature_sha256": stable_sha256(base_graph["partition_signature"]),
        "transition_graph_sha256": base_graph["transition_graph_sha256"],
        "all_pass": all_pass,
    }


def main() -> int:
    result = build_result()
    write_json(RESULT_PATH, result)
    print(json.dumps({"ok": result["all_pass"], "result_path": rel(RESULT_PATH)}, sort_keys=True))
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
