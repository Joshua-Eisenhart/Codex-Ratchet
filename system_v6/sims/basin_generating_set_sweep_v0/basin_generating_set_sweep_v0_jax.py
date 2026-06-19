#!/usr/bin/env python3
"""JAX/Python leg for basin_generating_set_sweep_v0."""

from __future__ import annotations

import importlib.metadata
from pathlib import Path

import cvc5
from cvc5 import Kind
import jax

jax.config.update("jax_enable_x64", True)

import jax.numpy as jnp
import jax.scipy.linalg as jsp_linalg
import networkx as nx
import sympy as sp
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


ENGINE = "jax"
SOURCE_PATH = Path(__file__).resolve()
RESULT_PATH = RESULT_DIR / f"{SIM_ID}_{ENGINE}_results.json"


def package_version(name: str) -> str:
    try:
        return importlib.metadata.version(name)
    except Exception:
        return "unknown"


def jax_expm(aug: list[list[float]], h: float) -> list[list[float]]:
    mat = jnp.array(aug, dtype=jnp.float64)
    out = jsp_linalg.expm(h * mat)
    return jax.device_get(out).tolist()


def source_backing_probe() -> dict[str, object]:
    solver = z3.Solver()
    x = z3.Int("source_backed_jax_x")
    solver.add(x == z3.IntVal(1))
    csolver = cvc5.Solver()
    csolver.setLogic("QF_LIA")
    y = csolver.mkConst(csolver.getIntegerSort(), "source_backed_jax_y")
    csolver.assertFormula(csolver.mkTerm(Kind.EQUAL, y, csolver.mkInteger(1)))
    half = sp.Rational(1, 2)
    graph = nx.DiGraph()
    graph.add_edge(0, 1)
    return {
        "jax_expm_shape": list(jnp.shape(jsp_linalg.expm(jnp.eye(2, dtype=jnp.float64)))),
        "z3_check": str(solver.check()),
        "cvc5_check": "sat" if csolver.checkSat().isSat() else "not_sat",
        "sympy_half": str(sp.simplify(half + half)),
        "networkx_edge_count": graph.number_of_edges(),
    }


def build_result() -> dict[str, object]:
    sweep = build_sweep(jax_expm)
    capability, tool_calls, one_to_one = one_to_one_tool_rows(ENGINE, "networkx", ["z3", "cvc5"])
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
        "packages_used": ["jax", "jax.numpy", "jax.scipy.linalg", "networkx", "sympy", "z3", "cvc5"],
        "aligned_packages_load_bearing": ["sympy", "z3", "cvc5"],
        "package_versions": {
            "jax": package_version("jax"),
            "networkx": package_version("networkx"),
            "sympy": package_version("sympy"),
            "z3-solver": package_version("z3-solver"),
            "cvc5": package_version("cvc5"),
        },
        "TOOL_MANIFEST": {
            "jax.scipy.linalg": {"tried": True, "used": True, "reason": "supportive terrain matrix exponentials"},
            "networkx": {"tried": True, "used": True, "reason": "supportive SCC/reachability graph partition mirror"},
            "sympy": {"tried": True, "used": True, "reason": "load-bearing exact rational parent-row parsing guard"},
            "z3": {"tried": True, "used": True, "reason": "load-bearing partition identity proof"},
            "cvc5": {"tried": True, "used": True, "reason": "load-bearing independent partition identity proof"},
        },
        "TOOL_INTEGRATION_DEPTH": {
            "jax.scipy.linalg": "supportive",
            "networkx": "supportive",
            "sympy": "load_bearing",
            "z3": "load_bearing",
            "cvc5": "load_bearing",
        },
        "claim_path_tools": ["sympy", "z3", "cvc5"],
        "parent_lineage": parent_lineage(),
        "capability_receipts": capability,
        "tool_calls": tool_calls,
        "one_to_one_tool_calls": one_to_one,
        "source_backing_probe": source_backing_probe(),
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
