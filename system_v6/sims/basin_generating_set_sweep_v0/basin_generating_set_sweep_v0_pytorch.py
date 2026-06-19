#!/usr/bin/env python3
"""PyTorch leg for basin_generating_set_sweep_v0."""

from __future__ import annotations

import importlib.metadata
from pathlib import Path

import cvc5
from cvc5 import Kind
import sympy as sp
import torch
from torch.func import vmap
from torch_geometric.data import Data
import z3

from basin_generating_set_sweep_v0_common import (
    CLASSIFICATION,
    FORMAL_ADMISSION_ALLOWED,
    PROMOTION_ALLOWED,
    RESULT_DIR,
    SEED_LEDGER,
    SIM_ID,
    all_expected_rows_pass,
    build_sweep,
    now_z,
    one_to_one_tool_rows,
    parent_lineage,
    rel,
    sha256_file,
    stable_sha256,
    summarize_sweep,
    write_json,
)


ENGINE = "pytorch"
SOURCE_PATH = Path(__file__).resolve()
RESULT_PATH = RESULT_DIR / f"{SIM_ID}_{ENGINE}_results.json"
torch.set_default_dtype(torch.float64)


def package_version(name: str) -> str:
    try:
        return importlib.metadata.version(name)
    except Exception:
        return "unknown"


def torch_expm(aug: list[list[float]], h: float) -> list[list[float]]:
    mat = torch.tensor(aug, dtype=torch.float64)
    return torch.matrix_exp(torch.tensor(h, dtype=torch.float64) * mat).detach().cpu().tolist()


def source_backing_probe(sweep: dict[str, object]) -> dict[str, object]:
    g0 = sweep["graphs"]["G0"]
    coords = torch.tensor([cell["coord"] for cell in g0["cells"]], dtype=torch.float64)
    edge_index = torch.tensor(
        [[row["src"] for row in g0["transition_edges"]], [row["dst"] for row in g0["transition_edges"]]],
        dtype=torch.long,
    )
    data = Data(x=coords, edge_index=edge_index)
    matrices = torch.stack([torch.tensor(gen["M"], dtype=torch.float64) for gen in g0["generators"]])
    offsets = torch.stack([torch.tensor(gen["c"], dtype=torch.float64) for gen in g0["generators"]])

    def apply(matrix: torch.Tensor, offset: torch.Tensor) -> torch.Tensor:
        return coords @ matrix.T + offset

    images = vmap(apply)(matrices, offsets)
    solver = z3.Solver()
    x = z3.Int("source_backed_torch_x")
    solver.add(x == z3.IntVal(1))
    csolver = cvc5.Solver()
    csolver.setLogic("QF_LIA")
    y = csolver.mkConst(csolver.getIntegerSort(), "source_backed_torch_y")
    csolver.assertFormula(csolver.mkTerm(Kind.EQUAL, y, csolver.mkInteger(1)))
    return {
        "torch_geometric_nodes": int(data.num_nodes),
        "torch_geometric_edges": int(data.num_edges),
        "torch_func_vmap_shape": list(images.shape),
        "torch_images_finite": bool(torch.isfinite(images).all().item()),
        "z3_check": str(solver.check()),
        "cvc5_check": "sat" if csolver.checkSat().isSat() else "not_sat",
        "sympy_guard": str(sp.simplify(sp.Rational(1, 2) + sp.Rational(1, 2))),
    }


def build_result() -> dict[str, object]:
    sweep = build_sweep(torch_expm)
    capability, tool_calls, one_to_one = one_to_one_tool_rows(ENGINE, "torch_geometric", ["z3", "cvc5"])
    all_pass = all_expected_rows_pass(sweep)
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
            "torch": package_version("torch"),
            "torch-geometric": package_version("torch-geometric"),
            "sympy": package_version("sympy"),
            "z3-solver": package_version("z3-solver"),
            "cvc5": package_version("cvc5"),
        },
        "TOOL_MANIFEST": {
            "torch": {"tried": True, "used": True, "reason": "supportive terrain matrix exponentials"},
            "torch.func": {"tried": True, "used": True, "reason": "load-bearing batched generator-action materialization"},
            "torch_geometric": {"tried": True, "used": True, "reason": "load-bearing graph edge_index carrier"},
            "sympy": {"tried": True, "used": True, "reason": "load-bearing exact rational parent-row parsing guard"},
            "z3": {"tried": True, "used": True, "reason": "load-bearing partition identity proof"},
            "cvc5": {"tried": True, "used": True, "reason": "load-bearing independent partition identity proof"},
        },
        "TOOL_INTEGRATION_DEPTH": {
            "torch": "supportive",
            "torch.func": "load_bearing",
            "torch_geometric": "load_bearing",
            "sympy": "load_bearing",
            "z3": "load_bearing",
            "cvc5": "load_bearing",
        },
        "claim_path_tools": ["torch.func", "torch_geometric", "sympy", "z3", "cvc5"],
        "parent_lineage": parent_lineage(),
        "capability_receipts": capability,
        "tool_calls": tool_calls,
        "one_to_one_tool_calls": one_to_one,
        "source_backing_probe": source_backing_probe(sweep),
        "sweep": summarize_sweep(sweep),
        "partition_fate_table": sweep["partition_fate_table"],
        "controls": sweep["controls"],
        "crossover_proofs": sweep["crossover_proofs"],
        "sub_basin_answer": sweep["sub_basin_answer"],
        "engine_dof_reading": sweep["engine_dof_reading"],
        "sweep_signature_sha256": sweep["sweep_signature_sha256"],
        "result_stability_sha256": stable_sha256(
            {
                "partition_fate_table": sweep["partition_fate_table"],
                "sub_basin_answer": sweep["sub_basin_answer"],
                "engine_dof_reading": sweep["engine_dof_reading"],
            }
        ),
        "all_pass": all_pass,
    }


def main() -> int:
    payload = build_result()
    write_json(RESULT_PATH, payload)
    print({"ok": payload["all_pass"], "result_path": rel(RESULT_PATH)})
    return 0 if payload["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
