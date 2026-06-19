#!/usr/bin/env python3
"""JAX/Python lane for gcm_constraint_carve_2q_v0."""

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

import gcm_constraint_carve_2q_v0_common as common


ENGINE = "jax"
SOURCE_PATH = Path(__file__).resolve()
RESULT_PATH = common.RESULT_DIR / f"{common.SIM_ID}_{ENGINE}_results.json"


def package_version(name: str) -> str:
    try:
        return importlib.metadata.version(name)
    except Exception:
        return "unknown"


def networkx_receipt(payload: dict[str, Any]) -> dict[str, Any]:
    graph = nx.Graph()
    graph.add_nodes_from(row["survivor_id"] for row in payload["survivors"])
    graph.add_edges_from((edge["src"], edge["dst"]) for edge in payload["adjacency_connectivity"]["survivor_edges"])
    components = [sorted(component) for component in nx.connected_components(graph)]

    q_graph = nx.Graph()
    q_graph.add_nodes_from(row["class_id"] for row in payload["quotient"]["classes"])
    q_graph.add_edges_from(
        (edge["src_class"], edge["dst_class"]) for edge in payload["adjacency_connectivity"]["quotient_edges"]
    )
    q_components = [sorted(component) for component in nx.connected_components(q_graph)]
    return {
        "survivor_node_count": graph.number_of_nodes(),
        "survivor_edge_count": graph.number_of_edges(),
        "survivor_components": components,
        "quotient_node_count": q_graph.number_of_nodes(),
        "quotient_edge_count": q_graph.number_of_edges(),
        "quotient_components": q_components,
        "component_match": components == payload["adjacency_connectivity"]["survivor_components"],
        "quotient_component_match": q_components == payload["adjacency_connectivity"]["quotient_components"],
    }


def jax_probe_receipt(payload: dict[str, Any]) -> dict[str, Any]:
    first = jnp.array([row["first_bloch"] for row in payload["survivors"]], dtype=jnp.float64)
    signatures = jnp.stack([first[:, 0] * 2.0, first[:, 2] * 2.0], axis=1).astype(jnp.int32)
    unique_signatures = jnp.unique(signatures, axis=0)
    active = jnp.logical_or(first[:, 0] != 0.0, first[:, 2] != 0.0)
    entangled = jnp.array([1 if row["entangled"] else 0 for row in payload["survivors"]], dtype=jnp.int32)
    return {
        "coord_shape": list(first.shape),
        "unique_probe_signature_count": int(unique_signatures.shape[0]),
        "all_active_probe_valid": bool(jax.device_get(jnp.all(active))),
        "entangled_survivor_count": int(jax.device_get(jnp.sum(entangled))),
        "x64_enabled": bool(jax.config.jax_enable_x64),
    }


def sympy_guard(payload: dict[str, Any]) -> dict[str, Any]:
    candidates = sp.Rational(payload["candidate_space"]["candidate_count"], 1)
    survivors = sp.Rational(payload["survivor_count"], 1)
    killed = sp.Rational(len(payload["kill_ledger"]), 1)
    quotient_classes = sp.Rational(payload["quotient"]["class_count"], 1)
    embedded = sp.Rational(payload["cross_rung_lineage_row"]["product_control_embedding_count"], 1)
    entangled = sp.Rational(payload["entangled_survivor_count"], 1)
    return {
        "candidate_partition_identity": str(sp.simplify(candidates - survivors - killed)),
        "survivor_count": str(survivors),
        "quotient_class_count": str(quotient_classes),
        "embedded_1q_count": str(embedded),
        "entangled_survivor_count": str(entangled),
        "pass": bool(
            sp.simplify(candidates - survivors - killed) == 0
            and survivors == common.EXPECTED_SURVIVOR_COUNT
            and quotient_classes == common.EXPECTED_QUOTIENT_CLASS_COUNT
            and embedded == common.EXPECTED_ONE_Q_SURVIVOR_COUNT
            and entangled == common.EXPECTED_ENTANGLED_SURVIVOR_COUNT
        ),
    }


def build_result() -> dict[str, Any]:
    payload = common.build_packet()
    graph = networkx_receipt(payload)
    probes = jax_probe_receipt(payload)
    exact = sympy_guard(payload)
    all_pass = bool(
        payload["all_pass"]
        and graph["component_match"]
        and graph["quotient_component_match"]
        and probes["all_active_probe_valid"]
        and probes["unique_probe_signature_count"] == common.EXPECTED_QUOTIENT_CLASS_COUNT
        and probes["entangled_survivor_count"] == common.EXPECTED_ENTANGLED_SURVIVOR_COUNT
        and exact["pass"]
    )
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
            "networkx": "nx.Graph connected_components over 2Q survivor and quotient adjacency",
            "sympy": "sp.Rational exact 2Q candidate/survivor/quotient/cross-rung count guard",
        },
        "reads_peer_result": False,
        "networkx_receipt": graph,
        "jax_probe_receipt": probes,
        "sympy_guard": exact,
        "survivor_count": payload["survivor_count"],
        "quotient_class_count": payload["quotient"]["class_count"],
        "component_count": len(graph["survivor_components"]),
        "entangled_survivor_count": payload["entangled_survivor_count"],
        "embedded_1q_count": payload["cross_rung_lineage_row"]["product_control_embedding_count"],
        "all_pass": all_pass,
        "TOOL_MANIFEST": {
            "networkx": {"tried": True, "used": True, "reason": "load-bearing graph component recomputation"},
            "sympy": {"tried": True, "used": True, "reason": "load-bearing exact count guard"},
            "jax": {"tried": True, "used": True, "reason": "supportive x64 vector materialization"},
            "jax.numpy": {"tried": True, "used": True, "reason": "supportive vectorized probe checks"},
        },
        "TOOL_INTEGRATION_DEPTH": {
            "networkx": "load_bearing",
            "sympy": "load_bearing",
            "jax": "supportive",
            "jax.numpy": "supportive",
        },
    }
    common.write_json(RESULT_PATH, result)
    return result


def main() -> int:
    result = build_result()
    print(json.dumps({"ok": result["all_pass"], "result": common.rel(RESULT_PATH)}, indent=2, sort_keys=True))
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
