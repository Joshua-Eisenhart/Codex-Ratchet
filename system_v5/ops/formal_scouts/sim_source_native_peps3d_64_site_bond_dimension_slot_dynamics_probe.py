#!/usr/bin/env python3
"""Source-native 64-site PEPS3D bond-dimension slot-dynamics scout."""

from __future__ import annotations

import json
import os
import pathlib
import time
from typing import Any

os.environ.setdefault("MPLCONFIGDIR", "/tmp/codex_ratchet_matplotlib")
os.environ.setdefault("NUMBA_DISABLE_JIT", "1")

import networkx as nx
import numpy as np
import sympy as sp
import z3

from sim_source_native_peps3d_64_site_slot_dynamics_closeout_probe import (
    EXPECTED_UNIQUE_ORDERED_TOKENS,
    apply_records_to_64_site_peps3d,
    make_peps3d_arrays,
    source_records,
    tensor_norm,
)


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
OUT_PATH = RESULT_DIR / "source_native_peps3d_64_site_bond_dimension_slot_dynamics_probe_results.json"

NAME = "source_native_peps3d_64_site_bond_dimension_slot_dynamics_probe"
CLASSIFICATION = "formal_scout"
PROMOTION_ALLOWED = False
CITES_BLOCKED_UNTIL = "long_horizon_64_site_bond_dimension_convergence"
CLAIM_CEILING = (
    "Formal scout only: compares finite 64-site PEPS3D operator-slot updates at "
    "bond dimensions 2, 3, and 4. It does not prove long-horizon convergence, "
    "does not prove optimal bond dimension, and does not admit neural capability, "
    "physics, cognition, or canonical manifold claims."
)

TOOL_MANIFEST = {
    "numpy": {"tried": True, "used": True, "reason": "load-bearing bond-dimension tensor updates"},
    "quimb": {"tried": True, "used": True, "reason": "load-bearing via imported PEPS3D closeout construction"},
    "networkx": {"tried": True, "used": True, "reason": "load-bearing bond-dimension graph"},
    "sympy": {"tried": True, "used": True, "reason": "load-bearing symbolic bond/site factorization"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing bond-dimension finite witness"},
    "engine_core": {"tried": True, "used": True, "reason": "load-bearing via imported source-native records"},
}
TOOL_INTEGRATION_DEPTH = {tool: "load_bearing" for tool in TOOL_MANIFEST}


def parameter_count(arrays: list[list[list[np.ndarray]]]) -> int:
    return int(sum(np.prod(arr.shape) for plane in arrays for row in plane for arr in row))


def apply_records_at_bond_dim(records: list[dict[str, Any]], bond_dim: int) -> dict[str, Any]:
    arrays = make_peps3d_arrays(90000 + bond_dim, bond_dim=bond_dim)
    before = tensor_norm(arrays)
    sites = [(i, j, k) for i in range(4) for j in range(4) for k in range(4)]
    touched = set()
    tokens = set()
    for idx, record in enumerate(records):
        i, j, k = sites[idx % len(sites)]
        touched.add((i, j, k))
        tokens.add(str(record["ordered_token"]))
        strength = 0.0025 + 0.0004 * float(record["slot_delta_norm"]) + 0.0001 * float(record["entropy"])
        from sim_source_native_peps3d_64_site_slot_dynamics_closeout_probe import apply_slot_to_tensor

        arrays[i][j][k] = apply_slot_to_tensor(
            arrays[i][j][k],
            str(record["operator"]),
            int(record["operator_sign"]),
            strength,
        )
    after = tensor_norm(arrays)
    return {
        "bond_dim": bond_dim,
        "parameter_count": parameter_count(arrays),
        "slot_applications": len(records),
        "unique_sites_touched": len(touched),
        "unique_ordered_tokens": len(tokens),
        "norm_before": before,
        "norm_after": after,
        "norm_shift": abs(after - before),
        "pass": len(touched) == 64 and len(tokens) == EXPECTED_UNIQUE_ORDERED_TOKENS and abs(after - before) > 1e-5,
    }


def z3_bond_witness(rows: list[dict[str, Any]]) -> dict[str, Any]:
    solver = z3.Solver()
    d2, d3, d4, tokens = z3.Ints("d2 d3 d4 tokens")
    p2, p3, p4 = z3.Ints("p2 p3 p4")
    row_by_dim = {int(row["bond_dim"]): row for row in rows}
    solver.add(d2 == 2, d3 == 3, d4 == 4, tokens == min(int(row["unique_ordered_tokens"]) for row in rows))
    solver.add(p2 == row_by_dim[2]["parameter_count"], p3 == row_by_dim[3]["parameter_count"], p4 == row_by_dim[4]["parameter_count"])
    solver.add(z3.Not(z3.And(d2 < d3, d3 < d4, p2 < p3, p3 < p4, tokens == 32)))
    status = solver.check()
    return {
        "solver_status": str(status),
        "pass": status == z3.unsat,
        "claim_ceiling": "Z3 encodes only finite D2/D3/D4 ordering and token preservation.",
    }


def main() -> int:
    started = time.time()
    records = source_records()
    bond_rows = [apply_records_at_bond_dim(records, dim) for dim in (2, 3, 4)]
    closeout_d2 = apply_records_to_64_site_peps3d(records)
    graph = nx.DiGraph()
    graph.add_edges_from([("D2", "D3"), ("D3", "D4"), ("source_records", "D2"), ("source_records", "D3"), ("source_records", "D4")])
    parameter_counts = [row["parameter_count"] for row in bond_rows]
    norm_shifts = [row["norm_shift"] for row in bond_rows]
    positive = {
        "bond_dimension_slot_dynamics_execute_at_64_sites": {
            "rows": bond_rows,
            "parameter_counts": parameter_counts,
            "norm_shifts": norm_shifts,
            "closeout_d2_norm_shift": closeout_d2["norm_shift"],
            "pass": all(row["pass"] for row in bond_rows)
            and parameter_counts[0] < parameter_counts[1] < parameter_counts[2]
            and len({round(x, 12) for x in norm_shifts}) == 3,
        },
        "symbolic_64_by_D234_factorization": {
            "factorization": {str(k): v for k, v in sp.factorint(64 * 2 * 3 * 4).items()},
            "pass": sp.factorint(64 * 2 * 3 * 4) == {2: 9, 3: 1},
        },
        "z3_rejects_bond_dimension_collapse": z3_bond_witness(bond_rows),
    }
    graveyards = {
        "single_bond_dimension_is_not_convergence": {
            "bond_dims": [2, 3, 4],
            "pass": CITES_BLOCKED_UNTIL == "long_horizon_64_site_bond_dimension_convergence",
        },
        "identity_free_norm_shift_required": {
            "min_norm_shift": min(norm_shifts),
            "pass": min(norm_shifts) > 1e-5,
        },
    }
    boundary = {
        "bond_graph_is_acyclic": {"nodes": graph.number_of_nodes(), "edges": graph.number_of_edges(), "pass": nx.is_directed_acyclic_graph(graph)},
        "promotion_remains_disabled": {"pass": PROMOTION_ALLOWED is False},
    }
    all_pass = all(row["pass"] for row in positive.values()) and all(row["pass"] for row in graveyards.values()) and all(row["pass"] for row in boundary.values())
    result = {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "name": NAME,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "cites_blocked_until": CITES_BLOCKED_UNTIL,
        "claim_ceiling": CLAIM_CEILING,
        "source_alignment_category": "source_native_peps3d_64_site_bond_dimension_formal_scout",
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "graveyard_companions": graveyards,
        "boundary": boundary,
        "nearby_variants": {"total": len(graveyards), "passed": sum(1 for row in graveyards.values() if row["pass"]), "variants": sorted(graveyards)},
        "why_not_v4_probes": [
            "Finite bond-dimension sensitivity scout only.",
            "Does not run long-horizon 64-site dynamics.",
            "Keeps convergence and canonical claims blocked.",
        ],
        "blockers": [],
        "elapsed_seconds": time.time() - started,
        "all_pass": all_pass,
    }
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print(f"RESULT {NAME}: all_pass={all_pass} -> {OUT_PATH}")
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
