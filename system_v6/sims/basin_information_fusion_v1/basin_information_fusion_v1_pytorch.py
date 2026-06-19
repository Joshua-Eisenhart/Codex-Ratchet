#!/usr/bin/env python3
"""PyTorch first-class graph leg for basin_information_fusion_v1."""

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

from basin_information_fusion_v1_common import (
    CLASSIFICATION,
    FORMAL_ADMISSION_ALLOWED,
    PROMOTION_ALLOWED,
    RESULT_DIR,
    SEED_LEDGER,
    SIM_ID,
    TOOL_INTENT,
    build_joint_object,
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


def package_version(name: str) -> str:
    try:
        return importlib.metadata.version(name)
    except Exception:
        return "unknown"


def torch_expm(aug: list[list[float]], h: float) -> list[list[float]]:
    mat = torch.tensor(aug, dtype=torch.float64)
    return torch.matrix_exp(torch.tensor(h, dtype=torch.float64) * mat).detach().cpu().tolist()


def source_backing_probe(joint: dict[str, object]) -> dict[str, object]:
    g2 = next(row for row in joint["sweep_partition_rows"] if row["set_id"] == "G2")
    coords = torch.tensor([[float(i), float(i % 3)] for i in range(int(g2["state_count"]))], dtype=torch.float64)
    edge_index = torch.tensor([[0, 1, 2], [1, 2, 0]], dtype=torch.long)
    data = Data(x=coords, edge_index=edge_index)
    matrices = torch.stack([torch.eye(2, dtype=torch.float64), 2.0 * torch.eye(2, dtype=torch.float64)])

    def apply(matrix: torch.Tensor) -> torch.Tensor:
        return coords @ matrix.T

    images = vmap(apply)(matrices)
    solver = z3.Solver()
    x = z3.Int("bif_v1_torch_record_count")
    solver.add(x == z3.IntVal(3))
    csolver = cvc5.Solver()
    csolver.setLogic("QF_LIA")
    y = csolver.mkConst(csolver.getIntegerSort(), "bif_v1_torch_record_count_cvc5")
    csolver.assertFormula(csolver.mkTerm(Kind.EQUAL, y, csolver.mkInteger(3)))
    return {
        "torch_geometric_nodes": int(data.num_nodes),
        "torch_geometric_edges": int(data.num_edges),
        "torch_func_vmap_shape": list(images.shape),
        "torch_images_finite": bool(torch.isfinite(images).all().item()),
        "sympy_log3": str(sp.log(3)),
        "sympy_rational_guard": str(sp.simplify(sp.Rational(1, 2) + sp.Rational(1, 2))),
        "z3_check": str(solver.check()),
        "cvc5_check": "sat" if csolver.checkSat().isSat() else "not_sat",
    }


def build_result() -> dict[str, object]:
    joint = build_joint_object(torch_expm)
    capability, tool_calls, one_to_one = one_to_one_tool_rows(ENGINE, ["torch.func", "torch_geometric", "sympy"], ["z3", "cvc5"])
    all_pass = bool(joint["all_pass"])
    return {
        "schema": "codex_ratchet.engine_leg_result.v1",
        "sim_id": SIM_ID,
        "object_id": f"{SIM_ID}_{ENGINE}",
        "engine": ENGINE,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "reads_peer_result": False,
        "reads_parent_results": True,
        "generated_at": now_z(),
        "seed_ledger": SEED_LEDGER,
        "source_path": rel(SOURCE_PATH),
        "source_sha256": sha256_file(SOURCE_PATH),
        "result_path": rel(RESULT_PATH),
        "packages_used": ["torch", "torch.func", "torch_geometric", "sympy", "z3", "cvc5"],
        "aligned_packages_load_bearing": ["sympy", "z3", "cvc5"],
        "package_observables": {
            "torch.func": "supportive source_backing_probe.torch_func_vmap_shape only; torch_expm uses plain torch.matrix_exp",
            "torch_geometric": "supportive source_backing_probe Data object only; committed graph computation uses shared Python common path",
            "sympy": "record_retention_at_g1_merge exact log-count rows and source_backing_probe.sympy_log3",
            "z3": "crossover_proofs.z3 computed record identity",
            "cvc5": "crossover_proofs.cvc5 computed record identity",
        },
        "package_versions": {
            "torch": package_version("torch"),
            "torch-geometric": package_version("torch-geometric"),
            "sympy": package_version("sympy"),
            "z3-solver": package_version("z3-solver"),
            "cvc5": package_version("cvc5"),
        },
        "TOOL_MANIFEST": {
            "torch": {"tried": True, "used": True, "reason": "supportive terrain matrix exponentials"},
            "torch.func": {"tried": True, "used": True, "reason": "supportive vmap sanity in source_backing_probe only"},
            "torch_geometric": {"tried": True, "used": True, "reason": "supportive Data sanity in source_backing_probe only"},
            "sympy": {"tried": True, "used": True, "reason": "load-bearing exact log-count entropy expression surface"},
            "z3": {"tried": True, "used": True, "reason": "load-bearing computed record identity UNSAT plus erased SAT flip"},
            "cvc5": {"tried": True, "used": True, "reason": "load-bearing independent computed record identity UNSAT plus erased SAT flip"},
        },
        "TOOL_INTEGRATION_DEPTH": {
            "torch": "supportive",
            "torch.func": "supportive",
            "torch_geometric": "supportive",
            "sympy": "load_bearing",
            "z3": "load_bearing",
            "cvc5": "load_bearing",
        },
        "claim_path_tools": ["sympy", "z3", "cvc5"],
        "tool_intent": TOOL_INTENT,
        "parent_lineage": parent_lineage(),
        "capability_receipts": capability,
        "tool_calls": tool_calls,
        "one_to_one_tool_calls": one_to_one,
        "source_backing_probe": source_backing_probe(joint),
        **joint,
        "result_stability_sha256": stable_sha256(
            {
                "entropy_production_along_orbits": joint["entropy_production_along_orbits"],
                "record_retention_at_g1_merge": joint["record_retention_at_g1_merge"],
                "per_class_throughput": joint["per_class_throughput"],
                "basin_conditioned_flow": joint["basin_conditioned_flow"],
                "controls": joint["controls"],
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
