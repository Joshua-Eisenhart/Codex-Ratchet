#!/usr/bin/env python3
"""JAX/Python lane for gcm_geometry_attach_v0."""

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

import gcm_geometry_attach_v0_common as common


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
        graph.add_edge(row["survivor_id"], row["spinor_id"], relation="survivor_to_spinor")
        graph.add_edge(row["quotient_class_id"], row["rho_id"], relation="class_to_rho")
        graph.add_edge(row["rho_id"], row["shell_id"], relation="rho_to_shell")
    survivor_ids = payload["gcm_lineage"]["survivor_ids"]
    resolved = [
        bool(
            nx.has_path(graph, sid, row["candidate_region_id"])
            and nx.has_path(graph, sid, row["shell_id"])
        )
        for sid, row in zip(survivor_ids, payload["gcm_lineage"]["object_maps"], strict=True)
    ]
    return {
        "node_count": graph.number_of_nodes(),
        "edge_count": graph.number_of_edges(),
        "component_count": nx.number_connected_components(graph),
        "all_survivors_resolve_to_region_and_shell": all(resolved),
        "survivor_path_count": len(resolved),
    }


def jax_spinor_receipt(payload: dict[str, Any]) -> dict[str, Any]:
    rows = payload["attachment_map"]["survivor_spinor_maps"]
    spinors = jnp.array([[row["psi_C2"][0]["re"], row["psi_C2"][1]["re"]] for row in rows], dtype=jnp.float64)

    def hopf(v: jax.Array) -> jax.Array:
        alpha, beta = v[0], v[1]
        return jnp.array([2.0 * alpha * beta, 0.0, alpha * alpha - beta * beta], dtype=jnp.float64)

    norms = jnp.sum(spinors * spinors, axis=1)
    hopf_rows = jax.vmap(hopf)(spinors)
    hopf_norms = jnp.sum(hopf_rows * hopf_rows, axis=1)
    return {
        "spinor_shape": list(spinors.shape),
        "max_spinor_norm_error": float(jax.device_get(jnp.max(jnp.abs(norms - 1.0)))),
        "max_hopf_norm_error": float(jax.device_get(jnp.max(jnp.abs(hopf_norms - 1.0)))),
        "unique_hopf_rows": int(jnp.unique(jnp.round(hopf_rows, 12), axis=0).shape[0]),
        "x64_enabled": bool(jax.config.jax_enable_x64),
    }


def sympy_guard(payload: dict[str, Any]) -> dict[str, Any]:
    counts = payload["counts"]
    shells = payload["attachment_map"]["shell_occupancy"]["counts_by_T_eta"]
    shell_total = sum(sp.Rational(value, 1) for value in shells.values())
    return {
        "survivors": str(sp.Rational(counts["survivor_count"], 1)),
        "density_classes": str(sp.Rational(counts["density_quotient_unique_count"], 1)),
        "shells": str(sp.Rational(counts["occupied_shell_count"], 1)),
        "shell_total": str(shell_total),
        "pass": bool(
            sp.Rational(counts["survivor_count"], 1) == common.EXPECTED_SURVIVOR_COUNT
            and sp.Rational(counts["density_quotient_unique_count"], 1) == common.EXPECTED_QUOTIENT_CLASS_COUNT
            and sp.Rational(counts["occupied_shell_count"], 1) == common.EXPECTED_SHELL_COUNT
            and shell_total == common.EXPECTED_SURVIVOR_COUNT
        ),
    }


def build_result() -> dict[str, Any]:
    payload = common.build_packet()
    lineage = lineage_graph_receipt(payload)
    spinors = jax_spinor_receipt(payload)
    exact = sympy_guard(payload)
    all_pass = bool(
        payload["all_pass"]
        and lineage["all_survivors_resolve_to_region_and_shell"]
        and lineage["survivor_path_count"] == common.EXPECTED_SURVIVOR_COUNT
        and spinors["max_spinor_norm_error"] <= 1e-12
        and spinors["max_hopf_norm_error"] <= 1e-12
        and spinors["unique_hopf_rows"] == common.EXPECTED_QUOTIENT_CLASS_COUNT
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
            "networkx": "nx.Graph lineage paths survivor->class->region and survivor->rho->shell",
            "sympy": "sp.Rational exact survivor/density-class/shell count guard",
        },
        "reads_peer_result": False,
        "lineage_graph_receipt": lineage,
        "jax_spinor_receipt": spinors,
        "sympy_guard": exact,
        "survivor_count": payload["counts"]["survivor_count"],
        "density_quotient_unique_count": payload["counts"]["density_quotient_unique_count"],
        "shell_count": payload["counts"]["occupied_shell_count"],
        "class_structure_survives_density_quotient": payload["attachment_map"]["class_structure_survives_density_quotient"],
        "all_pass": all_pass,
        "TOOL_MANIFEST": {
            "networkx": {"tried": True, "used": True, "reason": "load-bearing lineage graph resolution"},
            "sympy": {"tried": True, "used": True, "reason": "load-bearing exact count guard"},
            "jax": {"tried": True, "used": True, "reason": "supportive x64 vector materialization"},
            "jax.numpy": {"tried": True, "used": True, "reason": "supportive spinor/Hopf vector checks"},
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
