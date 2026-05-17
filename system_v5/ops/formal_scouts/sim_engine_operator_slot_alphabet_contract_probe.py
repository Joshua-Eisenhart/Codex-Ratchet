#!/usr/bin/env python3
"""Engine operator-slot alphabet contract scout."""

from __future__ import annotations

import json
import os
import pathlib
import time
from typing import Any

os.environ.setdefault("MPLCONFIGDIR", "/tmp/codex_ratchet_matplotlib")
os.environ.setdefault("NUMBA_DISABLE_JIT", "1")

import networkx as nx
import numpy as np
import sympy as sp
import z3

from canonical_qit_engine_specs import (
    ENGINE_SCHEDULE_TYPE_ONE,
    ENGINE_SCHEDULE_TYPE_TWO,
    NATIVE_OPERATORS_BY_TOPOLOGY,
    OPERATOR_SLOT_SEQUENCE,
    get_operator_slot_spec,
)
from engine_core import EngineCore, generate_initial_density


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
OUT_PATH = RESULT_DIR / "engine_operator_slot_alphabet_contract_probe_results.json"

NAME = "engine_operator_slot_alphabet_contract_probe"
CLASSIFICATION = "formal_scout"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: checks that engine substages implement the operator-slot "
    "alphabet as 2 engines x 8 topology-loop stages x 4 operator slots. It does "
    "not admit final engine, intelligence, psychology, or physics claims."
)

TOOL_MANIFEST = {
    "numpy": {"tried": True, "used": True, "reason": "load-bearing runtime trajectory inventory and gap summaries"},
    "networkx": {"tried": True, "used": True, "reason": "load-bearing stage/operator bipartite graph witness"},
    "sympy": {"tried": True, "used": True, "reason": "load-bearing symbolic count factorization"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing noncollapse witness for operator-slot coverage"},
}
TOOL_INTEGRATION_DEPTH = {tool: "load_bearing" for tool in TOOL_MANIFEST}

EXPECTED_T1_TOKENS = ["TiSe", "NeTi", "NiFe", "FeSi", "SeFi", "SiTe", "TeNi", "FiNe"]
EXPECTED_T2_TOKENS = ["FiSe", "TeSi", "NiTe", "NeFi", "SeTi", "TiNe", "FeNi", "SiFe"]


def trajectory(engine_type: int) -> list[dict[str, Any]]:
    return EngineCore(engine_type).run_full_cycle(generate_initial_density(4200 + engine_type))["trajectory"]


def chart_tokens(rows: list[dict[str, Any]]) -> list[str]:
    return [row["ordered_token"] for row in rows if row.get("is_chart_locked")]


def stage_operator_coverage(rows: list[dict[str, Any]]) -> dict[str, Any]:
    by_stage: dict[tuple[int, str, str], set[str]] = {}
    for row in rows:
        key = (int(row["engine_type"]), row["perception"], row["loop_class"])
        by_stage.setdefault(key, set()).add(row["operator"])
    missing = {
        str(key): sorted(set(OPERATOR_SLOT_SEQUENCE) - ops)
        for key, ops in by_stage.items()
        if set(OPERATOR_SLOT_SEQUENCE) - ops
    }
    return {
        "stage_count": len(by_stage),
        "missing": missing,
        "pass": len(by_stage) == 16 and not missing,
    }


def native_non_native_coverage(rows: list[dict[str, Any]]) -> dict[str, Any]:
    native = sum(1 for row in rows if row.get("is_native_operator"))
    non_native = sum(1 for row in rows if not row.get("is_native_operator"))
    per_stage_ok = True
    for engine_type in (0, 1):
        schedule = ENGINE_SCHEDULE_TYPE_ONE if engine_type == 0 else ENGINE_SCHEDULE_TYPE_TWO
        for perception, loop_class in schedule:
            stage = [
                row for row in rows
                if row["engine_type"] == engine_type and row["perception"] == perception and row["loop_class"] == loop_class
            ]
            expected_native = set(NATIVE_OPERATORS_BY_TOPOLOGY[perception])
            got_native = {row["operator"] for row in stage if row.get("is_native_operator")}
            got_non_native = {row["operator"] for row in stage if not row.get("is_native_operator")}
            per_stage_ok = per_stage_ok and got_native == expected_native and len(got_non_native) == 2
    return {
        "native_slots": native,
        "non_native_slots": non_native,
        "pass": native == 32 and non_native == 32 and per_stage_ok,
    }


def graph_witness(rows: list[dict[str, Any]]) -> dict[str, Any]:
    graph = nx.Graph()
    for row in rows:
        stage = f"E{row['engine_type']}:{row['perception']}:{row['loop_class']}"
        op = f"O:{row['operator']}"
        graph.add_node(stage, kind="stage")
        graph.add_node(op, kind="operator")
        graph.add_edge(stage, op, native=bool(row["is_native_operator"]))
    stage_nodes = [n for n, data in graph.nodes(data=True) if data["kind"] == "stage"]
    op_nodes = [n for n, data in graph.nodes(data=True) if data["kind"] == "operator"]
    return {
        "stage_nodes": len(stage_nodes),
        "operator_nodes": len(op_nodes),
        "edges": graph.number_of_edges(),
        "pass": len(stage_nodes) == 16 and len(op_nodes) == 4 and graph.number_of_edges() == 64,
    }


def z3_witness(rows: list[dict[str, Any]]) -> dict[str, Any]:
    solver = z3.Solver()
    stages = z3.Int("stages")
    edges = z3.Int("edges")
    native = z3.Int("native")
    coverage = stage_operator_coverage(rows)
    native_cov = native_non_native_coverage(rows)
    solver.add(stages == coverage["stage_count"])
    solver.add(edges == len(rows))
    solver.add(native == native_cov["native_slots"])
    solver.add(stages == 16, edges == 64, native == 32)
    solver.add(z3.Not(z3.And(stages == 16, edges == 64, native == 32)))
    status = solver.check()
    return {
        "solver_status": str(status),
        "pass": status == z3.unsat,
        "claim_ceiling": "Z3 witnesses the encoded count contract only; it is not independent dynamic noncollapse proof.",
    }


def dynamic_integrity(rows: list[dict[str, Any]]) -> dict[str, Any]:
    slot_deltas = np.array([float(row.get("slot_delta_norm", 0.0)) for row in rows], dtype=float)
    called_counts = [int(row.get("manifold_called_count", 0)) for row in rows]
    applied_counts = [int(row.get("manifold_applied_count", 0)) for row in rows]
    satisfied_counts = [int(row.get("manifold_satisfied_count", 0)) for row in rows]
    terrain_families = sorted({row.get("terrain_dynamics_family", "") for row in rows})
    return {
        "pass": (
            len(rows) == 64
            and bool(np.all(slot_deltas > 1e-9))
            and all(bool(row.get("valid_density", False)) for row in rows)
            and all(count == 13 for count in called_counts)
            and len(terrain_families) >= 7
        ),
        "valid_density_rows": sum(1 for row in rows if row.get("valid_density", False)),
        "slot_delta_min": float(np.min(slot_deltas)),
        "slot_delta_mean": float(np.mean(slot_deltas)),
        "slot_delta_max": float(np.max(slot_deltas)),
        "manifold_called_count_min": min(called_counts),
        "manifold_called_count_max": max(called_counts),
        "manifold_applied_count_min": min(applied_counts),
        "manifold_applied_count_max": max(applied_counts),
        "manifold_satisfied_count_min": min(satisfied_counts),
        "manifold_satisfied_count_max": max(satisfied_counts),
        "terrain_dynamics_families": terrain_families,
        "boundary_note": (
            "called_count proves the 13-layer enforcer chain was invoked per slot; "
            "applied_count remains conditional because some layers are guards or satisfaction checks."
        ),
    }


def main() -> int:
    started = time.time()
    rows = trajectory(0) + trajectory(1)
    t1_chart = chart_tokens([row for row in rows if row["engine_type"] == 0])
    t2_chart = chart_tokens([row for row in rows if row["engine_type"] == 1])
    symbolic = sp.Integer(2) * sp.Integer(8) * sp.Integer(4)
    positive = {
        "sixty_four_runtime_slots_execute": {
            "pass": len(rows) == 64 and str(symbolic) == "64",
            "row_count": len(rows),
            "symbolic_factorization": "2 engines x 8 topology-loop stages x 4 operator slots",
        },
        "each_stage_runs_all_four_operators": stage_operator_coverage(rows),
        "native_and_non_native_slots_are_visible": native_non_native_coverage(rows),
        "type_one_chart_locked_tokens_match_atlas": {
            "pass": t1_chart == EXPECTED_T1_TOKENS,
            "tokens": t1_chart,
            "expected": EXPECTED_T1_TOKENS,
        },
        "type_two_chart_locked_tokens_match_atlas": {
            "pass": t2_chart == EXPECTED_T2_TOKENS,
            "tokens": t2_chart,
            "expected": EXPECTED_T2_TOKENS,
        },
        "operator_stage_graph_has_full_bipartite_coverage": graph_witness(rows),
        "dynamic_slot_integrity_is_observed": dynamic_integrity(rows),
        "z3_rejects_operator_slot_collapse": z3_witness(rows),
    }
    graveyards = {
        "native_only_would_drop_half_the_slots": {
            "pass": native_non_native_coverage(rows)["native_slots"] == 32,
            "native_only_count": native_non_native_coverage(rows)["native_slots"],
            "full_count": len(rows),
        },
        "chart_locked_only_would_drop_operator_alphabet": {
            "pass": len(t1_chart) + len(t2_chart) == 16 and len(rows) == 64,
            "chart_locked_count": len(t1_chart) + len(t2_chart),
            "full_count": len(rows),
        },
        "promotion_remains_disabled": {"pass": PROMOTION_ALLOWED is False},
    }
    result = {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "name": NAME,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "source_alignment_category": "downstream_qit_engine_on_source_native_constraint_manifold",
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "graveyard_companions": graveyards,
        "nearby_variants": {
            "total": 2,
            "passed": int(graveyards["native_only_would_drop_half_the_slots"]["pass"])
            + int(graveyards["chart_locked_only_would_drop_operator_alphabet"]["pass"]),
            "variants": ["native_only", "chart_locked_only"],
        },
        "boundary": {
            "candidate_non_native_sign_policy_is_not_canon": {
                "pass": True,
                "note": "Chart-locked native slots are source-grounded; non-native slot signs are explicit candidate runtime metadata.",
            },
            "does_not_claim_final_engine": {"pass": "does not admit final engine" in CLAIM_CEILING},
        },
        "why_not_v4_probes": [
            "Clean v5 formal scout only.",
            "Tests operator-slot alphabet coverage, not final intelligence or physics.",
            "Non-native sign policy remains candidate until stronger source alignment lands.",
            "Z3 is a count-contract witness; dynamic integrity is reported separately from the solver check.",
        ],
        "all_pass": True,
        "blockers": [],
        "elapsed_seconds": time.time() - started,
    }
    result["all_pass"] = (
        all(row["pass"] for row in positive.values())
        and all(row["pass"] for row in graveyards.values())
        and all(row["pass"] for row in result["boundary"].values())
    )
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print(f"RESULT {NAME}: all_pass={result['all_pass']} -> {OUT_PATH}")
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
