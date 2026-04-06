#!/usr/bin/env python3
"""
qit_graph_engine_alignment_probe.py
==================================

Read-only alignment probe between the live QIT owner graph and the executable
geometric engine.

Purpose
-------
Make the graph stack useful for the current engine work by checking whether the
owner graph still matches the runtime engine's real topology and sequencing.

This probe does not mutate owner truth. It only reports alignment.
"""

from __future__ import annotations

import json
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from engine_core import GeometricEngine, LOOP_STAGE_ORDER, OPERATORS, TERRAINS


REPO_ROOT = Path(__file__).resolve().parents[2]
GRAPH_PATH = REPO_ROOT / "system_v4" / "a2_state" / "graphs" / "qit_engine_graph_v1.json"
RESULTS_PATH = REPO_ROOT / "system_v4" / "probes" / "a2_state" / "sim_results" / "qit_graph_engine_alignment_probe_results.json"


def load_graph() -> dict[str, Any]:
    return json.loads(GRAPH_PATH.read_text(encoding="utf-8"))


def summarize_owner_graph(graph: dict[str, Any]) -> dict[str, Any]:
    summary = graph.get("summary", {})
    nodes = graph.get("nodes", {})
    edges = graph.get("edges", [])
    return {
        "schema": graph.get("schema"),
        "summary": summary,
        "node_count": len(nodes),
        "edge_count": len(edges),
    }


def collect_graph_stage_map(graph: dict[str, Any]) -> dict[str, dict[str, Any]]:
    stages = {}
    for node in graph.get("nodes", {}).values():
        if node.get("node_type") == "MACRO_STAGE":
            key = f"{node['engine_type']}::{node['terrain']}"
            stages[key] = {
                "stage_index": node["stage_index"],
                "loop": node["loop"],
                "loop_order": node["loop_order"],
                "generator": node["generator"],
                "spinor_type": node["spinor_type"],
            }
    return stages


def collect_graph_step_sequences(graph: dict[str, Any]) -> dict[str, list[str]]:
    steps_by_stage: dict[str, dict[int, str]] = {}
    for node in graph.get("nodes", {}).values():
        if node.get("node_type") == "SUBCYCLE_STEP":
            stage_key = f"{node['engine_type']}::{node['terrain']}"
            steps_by_stage.setdefault(stage_key, {})[int(node["position_in_subcycle"])] = node["operator"]

    return {
        stage_key: [ops[pos] for pos in sorted(ops)]
        for stage_key, ops in steps_by_stage.items()
    }


def runtime_snapshot(engine_type: int) -> dict[str, Any]:
    engine = GeometricEngine(engine_type=engine_type)
    state = engine.init_state()
    final_state = engine.run_cycle(state)
    terrain_order = [TERRAINS[idx]["name"] for idx in LOOP_STAGE_ORDER[engine_type]]
    history_stage_prefixes = [entry["stage"].rsplit("_", 1)[0] for entry in final_state.history]
    unique_runtime_stage_order = []
    for prefix in history_stage_prefixes:
        if not unique_runtime_stage_order or unique_runtime_stage_order[-1] != prefix:
            unique_runtime_stage_order.append(prefix)

    return {
        "engine_type": engine_type,
        "history_length": len(final_state.history),
        "runtime_stage_order": unique_runtime_stage_order,
        "expected_stage_order": terrain_order,
        "history_operator_sequence_first_stage": [entry["op_name"] for entry in final_state.history[:4]],
    }


def main() -> int:
    os.makedirs(RESULTS_PATH.parent, exist_ok=True)

    graph = load_graph()
    owner = summarize_owner_graph(graph)
    graph_stage_map = collect_graph_stage_map(graph)
    graph_step_sequences = collect_graph_step_sequences(graph)

    runtime_t1 = runtime_snapshot(1)
    runtime_t2 = runtime_snapshot(2)

    expected_counts = {
        "ENGINE": 2,
        "MACRO_STAGE": 16,
        "SUBCYCLE_STEP": 64,
        "OPERATOR": 4,
        "TORUS": 3,
        "AXIS": 7,
    }
    owner_counts = owner["summary"].get("node_types", {})
    count_checks = {
        node_type: owner_counts.get(node_type) == expected
        for node_type, expected in expected_counts.items()
    }

    graph_stage_sequence_ok = all(
        runtime["runtime_stage_order"] == runtime["expected_stage_order"]
        for runtime in (runtime_t1, runtime_t2)
    )
    graph_operator_sequence_ok = all(
        seq == OPERATORS for seq in graph_step_sequences.values()
    ) and runtime_t1["history_operator_sequence_first_stage"] == OPERATORS and runtime_t2["history_operator_sequence_first_stage"] == OPERATORS

    stage_presence_ok = True
    for engine_type in ("type1", "type2"):
        for terrain in [t["name"] for t in TERRAINS]:
            if f"{engine_type}::{terrain}" not in graph_stage_map:
                stage_presence_ok = False

    overall_pass = all(count_checks.values()) and graph_stage_sequence_ok and graph_operator_sequence_ok and stage_presence_ok and owner["summary"].get("validation_errors") == []

    payload = {
        "schema": "QIT_GRAPH_ENGINE_ALIGNMENT_PROBE_v1",
        "generated_utc": datetime.now(UTC).isoformat(),
        "graph_path": str(GRAPH_PATH),
        "owner_graph": owner,
        "expected_counts": expected_counts,
        "count_checks": count_checks,
        "runtime_checks": {
            "stage_presence_ok": stage_presence_ok,
            "graph_stage_sequence_ok": graph_stage_sequence_ok,
            "graph_operator_sequence_ok": graph_operator_sequence_ok,
            "type1": runtime_t1,
            "type2": runtime_t2,
        },
        "verdict": {
            "result": "PASS" if overall_pass else "KILL",
            "read": (
                "The QIT owner graph is structurally aligned with the live engine topology and subcycle sequencing."
                if overall_pass
                else
                "The QIT owner graph has drifted from the live engine topology and needs reconciliation before it is trusted as a runtime substrate."
            ),
        },
    }

    RESULTS_PATH.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    print("=" * 72)
    print("QIT GRAPH ENGINE ALIGNMENT PROBE")
    print("=" * 72)
    print(f"  Owner graph schema: {owner['schema']}")
    print(f"  Node count: {owner['node_count']}")
    print(f"  Edge count: {owner['edge_count']}")
    print(f"  Stage presence ok: {stage_presence_ok}")
    print(f"  Stage sequence ok: {graph_stage_sequence_ok}")
    print(f"  Operator sequence ok: {graph_operator_sequence_ok}")
    print(f"  Verdict: {payload['verdict']['result']}")
    print(f"  Results saved: {RESULTS_PATH}")

    return 0 if overall_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
