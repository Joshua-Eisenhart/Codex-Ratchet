#!/usr/bin/env python3
"""JAX/Python lane for gcm_connection_flux_attach_v0."""

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

import gcm_connection_flux_attach_v0_common as common


ENGINE = "jax"
SOURCE_PATH = Path(__file__).resolve()
RESULT_PATH = common.RESULT_DIR / f"{common.SIM_ID}_{ENGINE}_results.json"


def package_version(name: str) -> str:
    try:
        return importlib.metadata.version(name)
    except Exception:
        return "unknown"


def lineage_graph_receipt(payload: dict[str, Any]) -> dict[str, Any]:
    graph = nx.Graph()
    for row in payload["gcm_lineage"]["object_maps"]:
        graph.add_edge(row["survivor_id"], row["quotient_class_id"], relation="survivor_to_class")
        graph.add_edge(row["quotient_class_id"], row["candidate_region_id"], relation="class_to_region")
        graph.add_edge(row["survivor_id"], row["shell_id"], relation="survivor_to_shell")
    resolved = []
    by_shell = {row["T_eta_label"]: row for row in payload["connection_flux_attachment"]["shell_rows"]}
    for shell in by_shell.values():
        for sid in shell["survivor_ids"]:
            resolved.append(any(nx.has_path(graph, sid, rid) for rid in shell["candidate_region_ids"]))
    return {
        "node_count": graph.number_of_nodes(),
        "edge_count": graph.number_of_edges(),
        "component_count": nx.number_connected_components(graph),
        "all_shell_survivors_resolve_to_region": all(resolved),
        "resolved_survivor_count": len(resolved),
    }


def jax_flux_receipt(payload: dict[str, Any]) -> dict[str, Any]:
    rows = payload["connection_flux_attachment"]["shell_rows"]
    eta = jnp.array([row["T_eta_rad"] for row in rows], dtype=jnp.float64)
    holonomy = -2.0 * jnp.pi * jnp.cos(2.0 * eta)
    curvature = -2.0 * jnp.sin(2.0 * eta)
    expected_h = jnp.array([row["holonomy_lifted_cycle"]["value"] for row in rows], dtype=jnp.float64)
    expected_f = jnp.array([row["curvature"]["F_eta_chi"] for row in rows], dtype=jnp.float64)
    return {
        "eta_shape": list(eta.shape),
        "max_holonomy_error": float(jax.device_get(jnp.max(jnp.abs(holonomy - expected_h)))),
        "max_curvature_error": float(jax.device_get(jnp.max(jnp.abs(curvature - expected_f)))),
        "x64_enabled": bool(jax.config.jax_enable_x64),
        "holonomy_values": [float(value) for value in jax.device_get(holonomy)],
        "curvature_values": [float(value) for value in jax.device_get(curvature)],
    }


def sympy_guard(payload: dict[str, Any]) -> dict[str, Any]:
    rows = payload["connection_flux_attachment"]["shell_rows"]
    counts = [sp.Rational(row["occupied_survivor_count"], 1) for row in rows]
    return {
        "shell_count": str(sp.Rational(len(rows), 1)),
        "survivor_total": str(sum(counts)),
        "signature": "-".join(str(int(value)) for value in counts),
        "pass": bool(
            len(rows) == common.EXPECTED_SHELL_COUNT
            and sum(counts) == common.EXPECTED_SURVIVOR_COUNT
            and "-".join(str(int(value)) for value in counts) == common.EXPECTED_SHELL_SIGNATURE
        ),
    }


def build_result() -> dict[str, Any]:
    payload = common.build_packet()
    lineage = lineage_graph_receipt(payload)
    flux = jax_flux_receipt(payload)
    exact = sympy_guard(payload)
    all_pass = bool(
        payload["all_pass"]
        and lineage["all_shell_survivors_resolve_to_region"]
        and lineage["resolved_survivor_count"] == common.EXPECTED_SURVIVOR_COUNT
        and flux["max_holonomy_error"] <= 1e-12
        and flux["max_curvature_error"] <= 1e-12
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
            "networkx": "nx.Graph resolves every survivor shell row through frozen class and region lineage",
            "sympy": "sp.Rational guards exact shell count, survivor total, and 2-4-4-4-2 shell signature",
        },
        "reads_peer_result": False,
        "lineage_graph_receipt": lineage,
        "jax_flux_receipt": flux,
        "sympy_guard": exact,
        "survivor_count": payload["counts"]["survivor_count"],
        "shell_count": payload["counts"]["occupied_shell_count"],
        "shell_occupation_signature": payload["connection_flux_attachment"]["shell_occupation_signature"],
        "leakage_status": payload["leakage_analysis"]["status"],
        "all_pass": all_pass,
        "TOOL_MANIFEST": {
            "networkx": {"tried": True, "used": True, "reason": "load-bearing lineage graph resolution"},
            "sympy": {"tried": True, "used": True, "reason": "load-bearing exact shell signature guard"},
            "jax": {"tried": True, "used": True, "reason": "supportive x64 vector recomputation"},
            "jax.numpy": {"tried": True, "used": True, "reason": "supportive h(eta)/F_eta_chi arrays"},
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
