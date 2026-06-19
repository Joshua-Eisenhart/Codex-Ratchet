#!/usr/bin/env python3
"""JAX/Python workhorse leg for basin_information_fusion_v1."""

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
    graph = nx.DiGraph()
    graph.add_edge("G1_chart_relative", "G2_remerged")
    solver = z3.Solver()
    x = z3.Int("bif_v1_jax_record_count")
    solver.add(x == z3.IntVal(3))
    csolver = cvc5.Solver()
    csolver.setLogic("QF_LIA")
    y = csolver.mkConst(csolver.getIntegerSort(), "bif_v1_jax_record_count_cvc5")
    csolver.assertFormula(csolver.mkTerm(Kind.EQUAL, y, csolver.mkInteger(3)))
    return {
        "networkx_edge_count": graph.number_of_edges(),
        "sympy_log3": str(sp.log(3)),
        "sympy_rational_guard": str(sp.simplify(sp.Rational(1, 2) + sp.Rational(1, 2))),
        "z3_check": str(solver.check()),
        "cvc5_check": "sat" if csolver.checkSat().isSat() else "not_sat",
        "jax_expm_shape": list(jnp.shape(jsp_linalg.expm(jnp.eye(2, dtype=jnp.float64)))),
    }


def build_result() -> dict[str, object]:
    joint = build_joint_object(jax_expm)
    capability, tool_calls, one_to_one = one_to_one_tool_rows(ENGINE, ["networkx", "sympy"], ["z3", "cvc5"])
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
        "packages_used": ["jax", "jax.numpy", "jax.scipy.linalg", "networkx", "sympy", "z3", "cvc5"],
        "aligned_packages_load_bearing": ["networkx", "sympy", "z3", "cvc5"],
        "package_observables": {
            "networkx": "joint_object.basin_conditioned_flow and source_backing_probe.networkx_edge_count",
            "sympy": "record_retention_at_g1_merge exact log-count rows and source_backing_probe.sympy_log3",
            "z3": "crossover_proofs.z3 computed record identity",
            "cvc5": "crossover_proofs.cvc5 computed record identity",
        },
        "package_versions": {
            "jax": package_version("jax"),
            "networkx": package_version("networkx"),
            "sympy": package_version("sympy"),
            "z3-solver": package_version("z3-solver"),
            "cvc5": package_version("cvc5"),
        },
        "TOOL_MANIFEST": {
            "jax.scipy.linalg": {"tried": True, "used": True, "reason": "supportive terrain matrix exponentials inherited from G-row graph rebuild"},
            "networkx": {"tried": True, "used": True, "reason": "load-bearing finite graph/orbit and basin-conditioned readout workhorse"},
            "sympy": {"tried": True, "used": True, "reason": "load-bearing exact log-count entropy expression surface"},
            "z3": {"tried": True, "used": True, "reason": "load-bearing computed record identity UNSAT plus erased SAT flip"},
            "cvc5": {"tried": True, "used": True, "reason": "load-bearing independent computed record identity UNSAT plus erased SAT flip"},
        },
        "TOOL_INTEGRATION_DEPTH": {
            "jax.scipy.linalg": "supportive",
            "networkx": "load_bearing",
            "sympy": "load_bearing",
            "z3": "load_bearing",
            "cvc5": "load_bearing",
        },
        "claim_path_tools": ["networkx", "sympy", "z3", "cvc5"],
        "tool_intent": TOOL_INTENT,
        "parent_lineage": parent_lineage(),
        "capability_receipts": capability,
        "tool_calls": tool_calls,
        "one_to_one_tool_calls": one_to_one,
        "source_backing_probe": source_backing_probe(),
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
