#!/usr/bin/env python3
"""JAX/Python lane for engine_16_stage_definition_correspondence_v0."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import jax

jax.config.update("jax_enable_x64", True)

import jax.numpy as jnp
import networkx as nx
import sympy as sp

import engine_16_stage_definition_correspondence_v0_common as common


ENGINE = "jax"
SOURCE_PATH = Path(__file__).resolve()
RESULT_PATH = common.RESULT_DIR / f"{common.SIM_ID}_{ENGINE}_results.json"


TOOL_MANIFEST = {
    "jax": {"tried": True, "used": True, "reason": "supportive x64 array materialization for stage matrices."},
    "jax.numpy": {"tried": True, "used": True, "reason": "supportive vectorized matrix shape check."},
    "networkx": {"tried": True, "used": True, "reason": "load-bearing alias graph over exact fingerprint classes."},
    "sympy": {"tried": True, "used": True, "reason": "load-bearing exact 16x16 matrix dimension and component-count guard."},
}
TOOL_INTEGRATION_DEPTH = {
    "jax": "supportive",
    "jax.numpy": "supportive",
    "networkx": "load_bearing",
    "sympy": "load_bearing",
}


def alias_graph_receipt(payload: dict[str, Any]) -> dict[str, Any]:
    graph = nx.Graph()
    rows = payload["defined_stage_rows"]
    graph.add_nodes_from(row["stage_token"] for row in rows)
    for i, left in enumerate(rows):
        for right in rows[i + 1 :]:
            if left["component_id"] == right["component_id"]:
                graph.add_edge(left["stage_token"], right["stage_token"])
    components = [sorted(component) for component in nx.connected_components(graph)]
    return {
        "node_count": graph.number_of_nodes(),
        "edge_count": graph.number_of_edges(),
        "component_count": len(components),
        "alias_components": [component for component in components if len(component) > 1],
        "finite_stage_graph": graph.number_of_nodes() == 16,
    }


def sympy_guard(payload: dict[str, Any]) -> dict[str, Any]:
    match_rows = sp.Rational(len(payload["correspondence"]["match_matrix_16x16"]), 1)
    match_cols = sp.Rational(len(payload["correspondence"]["match_matrix_16x16"][0]), 1)
    discovered = sp.Rational(payload["correspondence"]["discovered_component_count"], 1)
    stage_count = sp.Rational(len(payload["defined_stage_rows"]), 1)
    return {
        "stage_count": str(stage_count),
        "match_rows": str(match_rows),
        "match_cols": str(match_cols),
        "discovered_count": str(discovered),
        "pass": bool(stage_count == 16 and match_rows == 16 and match_cols == 16 and discovered == 16),
    }


def jax_matrix_receipt(payload: dict[str, Any]) -> dict[str, Any]:
    matrices = jnp.array([row["matrix_bloch_3x3"] for row in payload["defined_stage_rows"]], dtype=jnp.float64)
    bloch = jnp.array(payload["defined_stage_rows"][0]["bloch_input"], dtype=jnp.float64)
    outputs = jnp.einsum("nij,j->ni", matrices, bloch)
    return {
        "matrix_tensor_shape": list(matrices.shape),
        "output_tensor_shape": list(outputs.shape),
        "finite": bool(jnp.isfinite(outputs).all().item()),
        "output_norms": [round(float(value), 12) for value in jax.device_get(jnp.linalg.norm(outputs, axis=1)).tolist()],
    }


def build_result() -> dict[str, Any]:
    payload = common.build_packet()
    graph = alias_graph_receipt(payload)
    exact = sympy_guard(payload)
    array_receipt = jax_matrix_receipt(payload)
    all_pass = bool(payload["all_pass"] and graph["finite_stage_graph"] and exact["pass"] and array_receipt["finite"])
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
            "networkx": common.package_version("networkx"),
            "sympy": common.package_version("sympy"),
        },
        "package_observables": {
            "networkx": "nx.Graph alias components over exact stage fingerprint IDs",
            "sympy": "sp.Rational exact guard for 16 stage rows, 16 discovered rows, and 16x16 matrix shape",
        },
        "reads_peer_result": False,
        "alias_graph_receipt": graph,
        "sympy_guard": exact,
        "jax_matrix_receipt": array_receipt,
        "computed_values": {
            "stage_count": len(payload["defined_stage_rows"]),
            "defined_distinct_component_count": payload["summary"]["defined_distinct_component_count"],
            "discovered_component_count": payload["summary"]["discovered_component_count"],
            "exact_matched_component_count": payload["summary"]["exact_matched_component_count"],
            "perfect_bijection": payload["summary"]["perfect_bijection"],
            "normal_component_ids": [row["component_id"] for row in payload["defined_stage_rows"]],
            "match_matrix_sha256": common.stable_sha256(payload["correspondence"]["match_matrix_16x16"]),
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
