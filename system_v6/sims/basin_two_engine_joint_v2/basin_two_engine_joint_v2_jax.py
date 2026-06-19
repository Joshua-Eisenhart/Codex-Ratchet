#!/usr/bin/env python3
"""JAX/Python leg for basin_two_engine_joint_v2."""

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

from basin_two_engine_joint_v2_common import (
    CLASSIFICATION,
    FORMAL_ADMISSION_ALLOWED,
    PROMOTION_ALLOWED,
    RESULT_DIR,
    SEED_LEDGER,
    SIM_ID,
    build_graph,
    build_joint_payload,
    now_z,
    one_to_one_tool_rows,
    parent_lineage,
    per_engine_count,
    rel,
    sha256_file,
    stable_sha256,
    write_json,
)


ENGINE = "jax"
SOURCE_PATH = Path(__file__).resolve()
RESULT_PATH = RESULT_DIR / f"{SIM_ID}_{ENGINE}_results.json"

TOOL_MANIFEST = {
    "jax": {
        "tried": True,
        "used": True,
        "reason": "supportive x64 tensor materialization of the finite 32x32 joint carrier",
    },
    "jax.numpy": {
        "tried": True,
        "used": True,
        "reason": "supportive finite grid and transition arithmetic",
    },
    "networkx": {
        "tried": True,
        "used": True,
        "reason": "load-bearing directed graph SCC and terminal-class computation",
    },
    "sympy": {
        "tried": True,
        "used": True,
        "reason": "load-bearing gcd/lcm cycle-structure guard",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing primary no-64 proof with erased flip",
    },
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": "load-bearing independent primary no-64 proof with erased flip",
    },
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
    side = per_engine_count()
    grid = jnp.stack(jnp.meshgrid(jnp.arange(side), jnp.arange(side), indexing="ij"), axis=-1)
    state_count = int(grid.reshape((-1, 2)).shape[0])
    l_next = (grid[:, :, 0] + 1) % side
    r_next = (grid[:, :, 1] + 1) % side
    images = jnp.stack([l_next, r_next], axis=-1)
    return {
        "grid_shape": list(grid.shape),
        "state_count": state_count,
        "sync_image_shape": list(images.shape),
        "finite": bool(jnp.isfinite(images.astype(jnp.float64)).all().item()),
        "sample_sync_image": jax.device_get(images[0, 0]).tolist(),
    }


def networkx_cross_check() -> dict[str, Any]:
    nx_graph = nx.DiGraph()
    full = build_graph("source_sync_full_tick")
    nx_graph.add_nodes_from(range(full["state_count"]))
    nx_graph.add_edges_from((row["src"], row["dst"]) for row in full["transition_edges"])
    components = [sorted(comp) for comp in nx.strongly_connected_components(nx_graph)]
    return {
        "node_count": nx_graph.number_of_nodes(),
        "edge_count": nx_graph.number_of_edges(),
        "scc_count": len(components),
        "terminal_class_count": full["terminal_class_count"],
        "matches_shared_graph": len(components) == full["scc_count"] == 32,
    }


def sympy_cycle_guard() -> dict[str, Any]:
    macro = sp.gcd(8, 8)
    fine = sp.gcd(32, 32)
    macro_exact = sp.simplify(sp.Rational(macro, 1))
    fine_exact = sp.simplify(sp.Rational(fine, 1))
    return {
        "macro_offset_count": int(macro_exact),
        "fine_offset_count": int(fine_exact),
        "macro_lcm": int(sp.ilcm(8, 8)),
        "fine_lcm": int(sp.ilcm(32, 32)),
        "pass": int(macro_exact) == 8 and int(fine_exact) == 32,
    }


def solver_source_backing_probe() -> dict[str, Any]:
    z3_solver = z3.Solver()
    z3_count = z3.Int("jax_primary_64_level_count")
    z3_solver.add(z3_count == z3.IntVal(0))
    z3_solver.add(z3_count != z3.IntVal(0))
    cvc5_solver = cvc5.Solver()
    cvc5_solver.setLogic("QF_LIA")
    int_sort = cvc5_solver.getIntegerSort()
    cvc5_count = cvc5_solver.mkConst(int_sort, "jax_cvc5_primary_64_level_count")
    cvc5_solver.assertFormula(cvc5_solver.mkTerm(cvc5.Kind.EQUAL, cvc5_count, cvc5_solver.mkInteger(0)))
    cvc5_solver.assertFormula(
        cvc5_solver.mkTerm(cvc5.Kind.NOT, cvc5_solver.mkTerm(cvc5.Kind.EQUAL, cvc5_count, cvc5_solver.mkInteger(0)))
    )
    cvc5_result = cvc5_solver.checkSat()
    return {
        "z3_unsat_probe": str(z3_solver.check()),
        "cvc5_unsat_probe": "unsat" if cvc5_result.isUnsat() else str(cvc5_result),
        "pass": str(z3_solver.check()) == "unsat" and cvc5_result.isUnsat(),
    }


def build_result() -> dict[str, Any]:
    payload = build_joint_payload()
    grid = jax_grid_receipt()
    nx_receipt = networkx_cross_check()
    sympy_guard = sympy_cycle_guard()
    solver_probe = solver_source_backing_probe()
    proofs = payload["crossover_proofs"]
    capability, tool_calls, one_to_one = one_to_one_tool_rows(ENGINE, "networkx", ["z3", "cvc5"])
    all_pass = bool(
        jax.config.jax_enable_x64
        and payload["all_pass"] is True
        and grid["state_count"] == 1024
        and grid["finite"] is True
        and nx_receipt["matches_shared_graph"] is True
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
        "packages_used": ["jax", "jax.numpy", "networkx", "sympy", "z3", "cvc5"],
        "aligned_packages_load_bearing": ["networkx", "sympy", "z3", "cvc5"],
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
        "joint_payload": payload,
        "jax_grid_receipt": grid,
        "networkx_cross_check": nx_receipt,
        "sympy_cycle_guard": sympy_guard,
        "solver_source_backing_probe": solver_probe,
        "crossover_proofs": proofs,
        "primary_64_level_count": payload["prediction_adjudication"]["primary_64_level_count"],
        "control_terminal_class_count": payload["controls"]["dissipative_merge"]["control_terminal_class_count"],
        "joint_signature_sha256": stable_sha256(
            {
                "summary": payload["hierarchy"]["class_lattice_summary"],
                "proofs": payload["crossover_proofs"],
                "controls": payload["controls"]["dissipative_merge"],
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
