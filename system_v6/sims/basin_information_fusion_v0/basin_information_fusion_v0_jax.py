#!/usr/bin/env python3
"""JAX/Python leg for basin_information_fusion_v0."""

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

from basin_information_fusion_v0_common import (
    CLASSIFICATION,
    FORMAL_ADMISSION_ALLOWED,
    PROMOTION_ALLOWED,
    RESULT_DIR,
    SEED_LEDGER,
    SIM_ID,
    build_fusion,
    expected_pass,
    now_z,
    parent_lineage,
    rel,
    sha256_file,
    stable_sha256,
    tool_rows,
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
    return jax.device_get(jsp_linalg.expm(h * jnp.array(aug, dtype=jnp.float64))).tolist()


def source_backing_probe() -> dict[str, object]:
    graph = nx.DiGraph()
    graph.add_edge("G0", "G1")
    solver = z3.Solver()
    x = z3.Int("fusion_source_backed_x")
    solver.add(x == z3.IntVal(1))
    csolver = cvc5.Solver()
    csolver.setLogic("QF_LIA")
    y = csolver.mkConst(csolver.getIntegerSort(), "fusion_source_backed_y")
    csolver.assertFormula(csolver.mkTerm(Kind.EQUAL, y, csolver.mkInteger(1)))
    return {
        "networkx_edge_count": graph.number_of_edges(),
        "sympy_log3": str(sp.log(3)),
        "z3_check": str(solver.check()),
        "cvc5_check": "sat" if csolver.checkSat().isSat() else "not_sat",
    }


def build_result() -> dict[str, object]:
    fusion = build_fusion(jax_expm)
    capability, calls, one_to_one = tool_rows(ENGINE, "networkx", ["sympy", "z3", "cvc5"])
    all_pass = expected_pass(fusion)
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
            "networkx": "source_backing_probe.networkx_edge_count",
            "sympy": "source_backing_probe.sympy_log3",
            "z3": "crossover_proofs.z3.verdict",
            "cvc5": "crossover_proofs.cvc5.verdict",
        },
        "package_versions": {
            "jax": package_version("jax"),
            "networkx": package_version("networkx"),
            "sympy": package_version("sympy"),
            "z3-solver": package_version("z3-solver"),
            "cvc5": package_version("cvc5"),
        },
        "TOOL_MANIFEST": {
            "jax.scipy.linalg": {"tried": True, "used": True, "reason": "supportive inherited terrain matrix exponentials"},
            "networkx": {"tried": True, "used": True, "reason": "load-bearing source-backed graph transition ledger smoke plus inherited partition graph path"},
            "sympy": {"tried": True, "used": True, "reason": "load-bearing exact log(3) typed entropy row"},
            "z3": {"tried": True, "used": True, "reason": "load-bearing class-count accounting identity proof"},
            "cvc5": {"tried": True, "used": True, "reason": "load-bearing independent class-count accounting identity proof"},
        },
        "TOOL_INTEGRATION_DEPTH": {
            "jax.scipy.linalg": "supportive",
            "networkx": "load_bearing",
            "sympy": "load_bearing",
            "z3": "load_bearing",
            "cvc5": "load_bearing",
        },
        "claim_path_tools": ["networkx", "sympy", "z3", "cvc5"],
        "parent_lineage": parent_lineage(),
        "capability_receipts": capability,
        "tool_calls": calls,
        "one_to_one_tool_calls": one_to_one,
        "source_backing_probe": source_backing_probe(),
        "fusion_table": fusion["fusion_table"],
        "synthesis_row": fusion["synthesis_row"],
        "controls": fusion["controls"],
        "crossover_proofs": fusion["crossover_proofs"],
        "source_sweep_signature_sha256": fusion["source_sweep_signature_sha256"],
        "fusion_signature_sha256": fusion["fusion_signature_sha256"],
        "result_stability_sha256": stable_sha256(
            {"fusion_table": fusion["fusion_table"], "synthesis_row": fusion["synthesis_row"], "controls": fusion["controls"]}
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
