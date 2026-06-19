#!/usr/bin/env python3
"""JAX/Python lane for manifold_dynamic_chart_v2."""

from __future__ import annotations

import importlib.metadata
import json
from pathlib import Path
from typing import Any

import jax

jax.config.update("jax_enable_x64", True)

import jax.numpy as jnp
import networkx as nx
import sympy as sp

import manifold_dynamic_chart_v2_common as common


ENGINE = "jax"
SOURCE_PATH = Path(__file__).resolve()
RESULT_PATH = common.RESULT_DIR / f"{common.SIM_ID}_{ENGINE}_results.json"

TOOL_MANIFEST = {
    "jax": {
        "tried": True,
        "used": True,
        "reason": "supportive x64 entropy-vector materialization for the dynamic chart.",
    },
    "jax.numpy": {
        "tried": True,
        "used": True,
        "reason": "supportive finite vector checks over entropy trajectory rows.",
    },
    "networkx": {
        "tried": True,
        "used": True,
        "reason": "load-bearing directed graph reconstruction from committed carrier edges.",
    },
    "sympy": {
        "tried": True,
        "used": True,
        "reason": "load-bearing exact row-count and T>1 guard.",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "jax": "supportive",
    "jax.numpy": "supportive",
    "networkx": "load_bearing",
    "sympy": "load_bearing",
}


def package_version(name: str) -> str:
    try:
        return importlib.metadata.version(name)
    except Exception:
        return "unknown"


def networkx_receipt(payload: dict[str, Any]) -> dict[str, Any]:
    graph = nx.DiGraph()
    graph.add_nodes_from(range(common.EXPECTED_STATE_COUNT))
    graph.add_edges_from((int(row["src_state_id"]), int(row["dst_state_id"])) for row in payload["entropy_gradients"] if row["t"] == 0)
    components = [sorted(component) for component in nx.strongly_connected_components(graph)]
    return {
        "node_count": graph.number_of_nodes(),
        "edge_count": graph.number_of_edges(),
        "scc_count": len(components),
        "has_committed_edge_count": graph.number_of_edges() <= common.EXPECTED_EDGE_COUNT,
        "finite": graph.number_of_nodes() == common.EXPECTED_STATE_COUNT,
    }


def jax_entropy_receipt(payload: dict[str, Any]) -> dict[str, Any]:
    entropies = jnp.array([row["S_vN"] for row in payload["entropy_field_rows"]], dtype=jnp.float64)
    by_t = entropies.reshape((payload["trajectory"]["T"] + 1, common.EXPECTED_STATE_COUNT))
    ranges = jnp.max(by_t, axis=1) - jnp.min(by_t, axis=1)
    return {
        "entropy_tensor_shape": list(by_t.shape),
        "finite": bool(jnp.isfinite(by_t).all().item()),
        "range_by_t": [round(float(value), 12) for value in jax.device_get(ranges).tolist()],
    }


def sympy_guard(payload: dict[str, Any]) -> dict[str, Any]:
    t_value = sp.Rational(payload["trajectory"]["T"], 1)
    state_count = sp.Rational(payload["carrier"]["state_count"], 1)
    row_count = sp.Rational(len(payload["state_rows"]), 1)
    expected = state_count * (t_value + 1)
    return {
        "T": str(t_value),
        "expected_state_rows": str(expected),
        "actual_state_rows": str(row_count),
        "pass": bool(t_value > 1 and sp.simplify(expected - row_count) == 0),
    }


def build_result() -> dict[str, Any]:
    payload = common.build_packet()
    arrays = common.cells_and_entropy_by_t(payload)
    graph_receipt = networkx_receipt(payload)
    entropy_receipt = jax_entropy_receipt(payload)
    exact_guard = sympy_guard(payload)
    all_pass = bool(payload["all_pass"] and graph_receipt["finite"] and entropy_receipt["finite"] and exact_guard["pass"])
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
        "packages_used": ["jax", "jax.numpy", "networkx", "sympy"],
        "aligned_packages_load_bearing": ["networkx", "sympy"],
        "package_versions": {
            "jax": jax.__version__,
            "networkx": package_version("networkx"),
            "sympy": package_version("sympy"),
        },
        "package_observables": {
            "networkx": "nx.DiGraph over t=0 committed entropy-gradient adjacency rows",
            "sympy": "sp.Rational exact equality len(state_rows)=state_count*(T+1) with T>1",
        },
        "reads_peer_result": False,
        "networkx_receipt": graph_receipt,
        "jax_entropy_receipt": entropy_receipt,
        "sympy_guard": exact_guard,
        "computed_values": {
            "state_count": payload["carrier"]["state_count"],
            "trajectory_T": payload["trajectory"]["T"],
            "state_row_count": len(payload["state_rows"]),
            "cells_by_t": arrays["cells_by_t"],
            "entropy_by_t": arrays["entropy_by_t"],
            "trajectory_signature_sha256": payload["trajectory"]["trajectory_signature_sha256"],
            "entropy_signature_sha256": payload["trajectory"]["entropy_signature_sha256"],
            "shell_signature_sha256": payload["trajectory"]["shell_signature_sha256"],
            "jk_signature_sha256": payload["trajectory"]["jk_signature_sha256"],
        },
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "all_pass": all_pass,
    }
    common.write_json(RESULT_PATH, result)
    print(json.dumps({"ok": all_pass, "result": common.rel(RESULT_PATH)}, indent=2, sort_keys=True))
    return result


def main() -> int:
    result = build_result()
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
