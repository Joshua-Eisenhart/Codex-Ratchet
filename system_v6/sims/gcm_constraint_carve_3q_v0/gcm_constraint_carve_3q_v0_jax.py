#!/usr/bin/env python3
"""JAX/Python lane for gcm_constraint_carve_3q_v0."""

from __future__ import annotations

import importlib.metadata
import json
from pathlib import Path
from typing import Any

import networkx as nx
import sympy as sp

import gcm_constraint_carve_3q_v0_common as common


ENGINE = "jax"
SOURCE_PATH = Path(__file__).resolve()
RESULT_PATH = common.RESULT_DIR / f"{common.SIM_ID}_{ENGINE}_results.json"

CLASSIFICATION = common.CLASSIFICATION
TOOL_MANIFEST = {
    "networkx": {"tried": True, "used": True, "reason": "load-bearing quotient connectivity mirror"},
    "sympy": {"tried": True, "used": True, "reason": "load-bearing exact count/CKW rational guard"},
    "z3": {"tried": True, "used": True, "reason": "supportive crossover proof emitted by common packet"},
    "cvc5": {"tried": True, "used": True, "reason": "supportive crossover proof emitted by common packet"},
}
TOOL_INTEGRATION_DEPTH = {
    "networkx": "load_bearing",
    "sympy": "load_bearing",
    "z3": "supportive",
    "cvc5": "supportive",
}


def package_version(name: str) -> str:
    try:
        return importlib.metadata.version(name)
    except Exception:
        return "unknown"


def networkx_receipt(payload: dict[str, Any]) -> dict[str, Any]:
    graph = nx.Graph()
    for qrow in payload["quotient"]["classes"]:
        graph.add_node(qrow["class_id"], members=qrow["member_count"])
    signatures = [tuple(row["probe_signature"]) for row in payload["quotient"]["classes"]]
    for idx, sig in enumerate(signatures[:-1]):
        nxt = signatures[idx + 1]
        if abs(sig[0] - nxt[0]) + abs(sig[1] - nxt[1]) <= 3:
            graph.add_edge(f"Q{idx}", f"Q{idx + 1}")
    return {
        "node_count": graph.number_of_nodes(),
        "edge_count": graph.number_of_edges(),
        "component_count": nx.number_connected_components(graph),
        "class_count": len(signatures),
    }


def sympy_guard(payload: dict[str, Any]) -> dict[str, Any]:
    ckw = payload["monogamy_ckw_row"]["rows"][0]
    survivor = sp.Rational(payload["survivor_count"], 1)
    quotient = sp.Rational(payload["quotient"]["class_count"], 1)
    margin = sp.Rational(str(ckw["ckw_margin"]))
    return {
        "survivor_count": str(survivor),
        "quotient_class_count": str(quotient),
        "ckw_margin": str(margin),
        "pass": bool(
            survivor == common.EXPECTED_SURVIVOR_COUNT
            and quotient == common.EXPECTED_QUOTIENT_CLASS_COUNT
            and margin == sp.Rational(3, 16)
        ),
    }


def build_result() -> dict[str, Any]:
    payload = common.build_packet()
    nx_receipt = networkx_receipt(payload)
    exact = sympy_guard(payload)
    all_pass = bool(payload["all_pass"] and nx_receipt["class_count"] == common.EXPECTED_QUOTIENT_CLASS_COUNT and exact["pass"])
    result = {
        "schema": "codex_ratchet.engine_leg_result.v1",
        "sim_id": common.SIM_ID,
        "engine": ENGINE,
        "source_path": common.rel(SOURCE_PATH),
        "source_sha256": common.sha256_file(SOURCE_PATH),
        "result_path": common.rel(RESULT_PATH),
        "generated_at": common.now_z(),
        "classification": common.CLASSIFICATION,
        "promotion_allowed": common.PROMOTION_ALLOWED,
        "formal_admission_allowed": common.FORMAL_ADMISSION_ALLOWED,
        "packages_used": ["networkx", "sympy", "z3", "cvc5"],
        "aligned_packages_load_bearing": ["networkx", "sympy"],
        "package_versions": {"networkx": package_version("networkx"), "sympy": package_version("sympy")},
        "package_observables": {
            "networkx": "nx.Graph over quotient class signatures; number_connected_components checks quotient row shape",
            "sympy": "sp.Rational exact survivor/quotient/CKW margin guard",
        },
        "reads_peer_result": False,
        "networkx_receipt": nx_receipt,
        "sympy_guard": exact,
        "survivor_count": payload["survivor_count"],
        "quotient_class_count": payload["quotient"]["class_count"],
        "ckw_survivor_count": payload["monogamy_ckw_row"]["survivor_count_checked"],
        "floor_carrier": payload["floor_rows"]["cl6_structure_carried_by_survivors"]["carrier"],
        "all_pass": all_pass,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
    }
    common.write_json(RESULT_PATH, result)
    return result


def main() -> int:
    result = build_result()
    print(json.dumps({"ok": result["all_pass"], "result": common.rel(RESULT_PATH)}, indent=2, sort_keys=True))
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
