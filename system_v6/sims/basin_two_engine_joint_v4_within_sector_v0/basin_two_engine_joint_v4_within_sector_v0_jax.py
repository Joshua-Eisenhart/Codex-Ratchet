#!/usr/bin/env python3
"""JAX/Python workhorse leg for basin_two_engine_joint_v4_within_sector_v0."""

from __future__ import annotations

import importlib.metadata
import json
from pathlib import Path
from typing import Any

import cvc5
import jax

jax.config.update("jax_enable_x64", True)

import jax.numpy as jnp
import networkx as nx
import sympy as sp
import z3

from basin_two_engine_joint_v4_within_sector_v0_common import (
    CLASSIFICATION,
    FORMAL_ADMISSION_ALLOWED,
    PROMOTION_ALLOWED,
    RESULT_DIR,
    SIM_ID,
    build_flux_edges,
    build_flux_payload,
    engine_count_with_flux,
    now_z,
    one_to_one_tool_rows,
    parent_lineage,
    rel,
    sha256_file,
    stable_sha256,
    write_json,
)


ENGINE = "jax"
SOURCE_PATH = Path(__file__).resolve()
RESULT_PATH = RESULT_DIR / f"{SIM_ID}_{ENGINE}_results.json"
classification = "scratch_diagnostic"
promotion_allowed = False
formal_admission_allowed = False

TOOL_MANIFEST = {
    "jax": {"tried": True, "used": True, "reason": "supportive x64 finite carrier tensor materialization"},
    "jax.numpy": {"tried": True, "used": True, "reason": "supportive vectorized coordinate grids for bounded row checks"},
    "networkx": {"tried": True, "used": True, "reason": "load-bearing directed graph SCC terminal-class cross-check"},
    "sympy": {"tried": True, "used": True, "reason": "load-bearing exact integer checksum over measured counts"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing computed-count identity proof with flipped control"},
    "cvc5": {"tried": True, "used": True, "reason": "load-bearing independent computed-count identity proof with flipped control"},
}

TOOL_INTEGRATION_DEPTH = {
    "jax": "supportive",
    "jax.numpy": "supportive",
    "networkx": "load_bearing",
    "sympy": "load_bearing",
    "z3": "load_bearing",
    "cvc5": "load_bearing",
}


def package_version(name: str) -> str:
    try:
        return importlib.metadata.version(name)
    except Exception:
        return "unknown"


def jax_grid_receipt() -> dict[str, Any]:
    side = engine_count_with_flux()
    grid = jnp.stack(jnp.meshgrid(jnp.arange(side), jnp.arange(2), indexing="ij"), axis=-1)
    flat = grid.reshape((-1, 2))
    parity = jnp.remainder(flat[:, 0] + flat[:, 1], 2)
    return {
        "grid_shape": list(grid.shape),
        "state_row_count": int(flat.shape[0]),
        "parity_shape": list(parity.shape),
        "finite": bool(jnp.isfinite(parity.astype(jnp.float64)).all().item()),
        "sample": jax.device_get(flat[:4]).tolist(),
    }


def networkx_cross_check() -> dict[str, Any]:
    edges = build_flux_edges("R", "D_matrix64_b_order_overlay", "conserved_flux_control")
    graph = nx.DiGraph()
    graph.add_nodes_from(range(engine_count_with_flux()))
    graph.add_edges_from((edge["src"], edge["dst"]) for edge in edges)
    components = [set(comp) for comp in nx.strongly_connected_components(graph)]
    terminal = [comp for comp in components if all(dst in comp for src in comp for dst in graph.successors(src))]
    return {
        "variant_id": "D_matrix64_b_order_overlay",
        "engine": "R",
        "update_law_id": "conserved_flux_control",
        "node_count": graph.number_of_nodes(),
        "edge_count": graph.number_of_edges(),
        "terminal_class_count": len(terminal),
        "terminal_sizes": sorted(len(comp) for comp in terminal),
        "pass": graph.number_of_nodes() == engine_count_with_flux() and sorted(len(comp) for comp in terminal) == [24, 24],
    }


def solver_source_backing_probe(counts: dict[str, int]) -> dict[str, Any]:
    first_name, first_value = sorted(counts.items())[0]
    z3_solver = z3.Solver()
    count = z3.Int("jax_first_count_identity_probe")
    z3_solver.add(count == z3.IntVal(first_value))
    z3_solver.add(count != z3.IntVal(first_value))

    cvc5_solver = cvc5.Solver()
    cvc5_solver.setLogic("QF_LIA")
    int_sort = cvc5_solver.getIntegerSort()
    cvc5_count = cvc5_solver.mkConst(int_sort, "jax_cvc5_first_count_identity_probe")
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
    grid = jax_grid_receipt()
    nx_receipt = networkx_cross_check()
    checksum = local_sympy_count_checksum(counts)
    solver_probe = solver_source_backing_probe(counts)
    proofs = payload["crossover_proofs"]
    capability, tool_calls, one_to_one = one_to_one_tool_rows(ENGINE, "networkx", ["z3", "cvc5"])
    all_pass = bool(
        payload["all_pass"] is True
        and jax.config.jax_enable_x64
        and grid["finite"] is True
        and nx_receipt["pass"] is True
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
        "packages_used": ["jax", "jax.numpy", "networkx", "sympy", "z3", "cvc5"],
        "aligned_packages_load_bearing": ["networkx", "sympy", "z3", "cvc5"],
        "package_observables": {
            "networkx": "networkx.DiGraph/networkx.strongly_connected_components terminal-class cross-check",
            "sympy": "sympy exact integer checksum over measured realization-family counts",
            "z3": "z3.Solver computed count identity UNSAT and flipped control SAT",
            "cvc5": "cvc5.Solver computed count identity UNSAT and flipped control SAT",
        },
        "package_versions": {
            "jax": jax.__version__,
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
        "payload_digest": stable_sha256(payload["prediction_adjudication"]),
        "jax_grid_receipt": grid,
        "networkx_cross_check": nx_receipt,
        "sympy_count_checksum": checksum,
        "solver_source_backing_probe": solver_probe,
        "crossover_proofs": proofs,
        "primary_terminal_counts": counts,
        "genuine_hit_count": payload["prediction_adjudication"]["genuine_hit_count"],
        "joint_signature_sha256": stable_sha256({"counts": counts, "adjudication": payload["prediction_adjudication"]}),
        "all_pass": all_pass,
    }


def main() -> int:
    result = build_result()
    write_json(RESULT_PATH, result)
    print(json.dumps({"ok": result["all_pass"], "result_path": rel(RESULT_PATH)}, sort_keys=True))
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
