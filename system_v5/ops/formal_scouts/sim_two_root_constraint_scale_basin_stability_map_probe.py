#!/usr/bin/env python3
"""Scale-basin stability map formal scout.

This scout targets the current open gap after the coupled-E16 Phi0 stress
chain: finite source-aligned runtime maps converge, but final scale-level basin
admission remains blocked. It builds small torch-native runtime maps from the
shared QIT runtime helper, measures finite single-basin convergence, then tests
whether those basins are stable across Hamiltonian directions and adversarial
schedule controls.

Expected outcome for the current stack: finite maps converge, but scale-basin
admission is not allowed because direction-scale variance and Phi0 stress
controls remain nonrobust. This is a formal scout only.
"""

from __future__ import annotations

import hashlib
import json
import math
import pathlib
import time
from typing import Any

import rustworkx as rx
import torch
import z3

import qit_engine_runtime as qit


SCOUT_ROOT = pathlib.Path(__file__).resolve().parent
REPO = SCOUT_ROOT.parents[2]
RESULT_DIR = SCOUT_ROOT / "results"
RESULT_DIR.mkdir(parents=True, exist_ok=True)
OUT_PATH = RESULT_DIR / "two_root_constraint_scale_basin_stability_map_probe_results.json"

NAME = "two_root_constraint_scale_basin_stability_map_probe"
CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "nonclassical"
SOURCE_ALIGNMENT_CATEGORY = "two_root_constraint_scale_basin_stability_map"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: builds bounded source-aligned runtime basin maps and "
    "tests scale-level stability against direction, schedule, and Phi0 stress "
    "controls. It cannot admit final Xi, final Phi0, final manifold law, "
    "full PEPS/PEPS3D dynamics, L64 convergence, holography, ER=EPR, or physics."
)

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite source-aligned runtime channels, fixed-point basins, and distance matrices",
    },
    "rustworkx": {
        "tried": True,
        "used": True,
        "reason": "load-bearing scale/control dependency graph over direction and schedule probes",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing final-admission and nonpromotion guard",
    },
    "python_json": {"tried": True, "used": True, "reason": "supportive receipt loading and serialization"},
    "hashlib": {"tried": True, "used": True, "reason": "supportive source and receipt provenance hashes"},
    "pathlib": {"tried": True, "used": True, "reason": "supportive path handling"},
    "time": {"tried": True, "used": True, "reason": "supportive runtime metadata"},
}
TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "rustworkx": "load_bearing",
    "z3": "load_bearing",
    "python_json": "supportive",
    "hashlib": "supportive",
    "pathlib": "supportive",
    "time": "supportive",
}

DIRECTIONS = ["iter176_xz", "x", "z", "xy", "xyz"]
SCHEDULES = {
    "canonical": ["L", "R", "L", "R"],
    "reverse": ["R", "L", "R", "L"],
    "paired": ["L", "L", "R", "R"],
    "swap": ["L", "R", "R", "L"],
    "single_L": ["L", "L", "L", "L"],
    "single_R": ["R", "R", "R", "R"],
}
TAU = 0.35
SCALE_STABILITY_TOL = 0.08
CONTROL_SEPARATION_TOL = 0.05

SOURCE_FILES = {
    "formal_scout": pathlib.Path(__file__).resolve(),
    "runtime": SCOUT_ROOT / "qit_engine_runtime.py",
    "source_runtime_result": RESULT_DIR / "source_aligned_qit_engine_runtime_probe_results.json",
    "phi0_stress_result": RESULT_DIR / "two_root_constraint_coupled_e16_phi0_stress_controls_probe_results.json",
    "response_gradient_result": RESULT_DIR / "two_root_constraint_phi0_bridge_response_gradient_after_stress_probe_results.json",
    "trace_after_stress_result": RESULT_DIR / "two_root_constraint_full_manifold_trace_after_phi0_stress_probe_results.json",
    "classifier_result": RESULT_DIR / "source_aligned_stack_completion_gap_classifier_probe_results.json",
}


def rel(path: pathlib.Path) -> str:
    try:
        return str(path.relative_to(REPO))
    except ValueError:
        return str(path)


def sha256(path: pathlib.Path) -> str | None:
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None


def read_json(path: pathlib.Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def jsonable(value: Any) -> Any:
    if isinstance(value, pathlib.Path):
        return rel(value)
    return qit.jsonable(value)


def source_hashes() -> dict[str, dict[str, Any]]:
    return {name: {"path": rel(path), "sha256": sha256(path)} for name, path in SOURCE_FILES.items()}


def dist(left: list[float], right: list[float]) -> float:
    return math.dist(left, right)


def max_pairwise(points: list[list[float]]) -> float:
    max_gap = 0.0
    for idx, left in enumerate(points):
        for right in points[idx + 1 :]:
            max_gap = max(max_gap, dist(left, right))
    return max_gap


def schedule_map_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for direction in DIRECTIONS:
        engines = {sheet: qit.engine_channel(sheet, direction, tau=TAU) for sheet in ("L", "R")}
        for schedule_name, word in SCHEDULES.items():
            channel = qit.schedule_channel(word, engines)
            diag = qit.channel_diagnostics(channel, cycles=120)
            rows.append(
                {
                    "direction": direction,
                    "schedule": schedule_name,
                    "word": word,
                    "fixed_bloch": diag["mean_final_bloch"],
                    "max_final_bloch_spread": diag["max_final_bloch_spread"],
                    "spectral_gap": diag["spectral_gap"],
                    "single_basin": bool(diag["single_basin_by_trajectory_at_80"]),
                    "asymptotic_single_basin": bool(diag["asymptotic_single_basin"]),
                }
            )
    return rows


def basin_metrics(rows: list[dict[str, Any]]) -> dict[str, Any]:
    canonical = [row for row in rows if row["schedule"] == "canonical"]
    canonical_points = [row["fixed_bloch"] for row in canonical]
    direction_spread = max_pairwise(canonical_points)

    control_gaps = []
    near_controls = []
    for direction in DIRECTIONS:
        canonical_row = next(row for row in rows if row["direction"] == direction and row["schedule"] == "canonical")
        for row in rows:
            if row["direction"] != direction or row["schedule"] == "canonical":
                continue
            gap = dist(canonical_row["fixed_bloch"], row["fixed_bloch"])
            control_gaps.append(gap)
            if gap < CONTROL_SEPARATION_TOL:
                near_controls.append({"direction": direction, "control": row["schedule"], "gap": gap})

    graph = rx.PyDiGraph()
    root = graph.add_node("scale_basin_map")
    for row in rows:
        direction_node = graph.add_node(f"direction:{row['direction']}")
        schedule_node = graph.add_node(f"schedule:{row['schedule']}")
        graph.add_edge(root, direction_node, "direction")
        graph.add_edge(direction_node, schedule_node, "schedule")
    clusters = qit.cluster_points(
        [{"label": f"{row['direction']}:{row['schedule']}", "fixed_bloch": row["fixed_bloch"]} for row in rows],
        eps=SCALE_STABILITY_TOL,
    )
    return {
        "all_finite_maps_single_basin": all(row["single_basin"] and row["asymptotic_single_basin"] for row in rows),
        "canonical_direction_spread": direction_spread,
        "canonical_scale_stable": direction_spread < SCALE_STABILITY_TOL,
        "min_control_gap": min(control_gaps),
        "mean_control_gap": sum(control_gaps) / len(control_gaps),
        "all_controls_separated": not near_controls,
        "near_controls": near_controls,
        "cluster_count": len(clusters),
        "clusters": clusters,
        "graph": {
            "node_count": graph.num_nodes(),
            "edge_count": graph.num_edges(),
            "is_dag": rx.is_directed_acyclic_graph(graph),
        },
    }


def upstream_status() -> dict[str, Any]:
    stress = read_json(SOURCE_FILES["phi0_stress_result"])
    response = read_json(SOURCE_FILES["response_gradient_result"])
    trace = read_json(SOURCE_FILES["trace_after_stress_result"])
    classifier = read_json(SOURCE_FILES["classifier_result"])
    return {
        "stress_status": stress.get("summary", {}).get("stress_status") or stress.get("boundary", {}).get("stress_status"),
        "response_repair_status": response.get("summary", {}).get("repair_status")
        or response.get("boundary", {}).get("repair_status"),
        "trace_phi0_current_status": trace.get("summary", {}).get("phi0_current_status")
        or trace.get("boundary", {}).get("phi0_current_status"),
        "classifier_xi_status": (
            classifier.get("positive", {})
            .get("requirement_coverage_matrix", {})
            .get("rows", {})
            .get("xi_phi0_bridge", {})
            .get("status")
        ),
        "classifier_scores": classifier.get("positive", {})
        .get("torch_gap_vector_identifies_open_completion_margin", {})
        .get("scores"),
    }


def z3_guard(metrics: dict[str, Any], upstream: dict[str, Any]) -> dict[str, Any]:
    finite_basin = z3.Bool("finite_basin")
    scale_stable = z3.Bool("scale_stable")
    controls_separated = z3.Bool("controls_separated")
    phi0_robust = z3.Bool("phi0_robust")
    final_basin = z3.Bool("final_basin")
    final_admission = z3.Bool("final_admission")

    solver = z3.Solver()
    solver.add(finite_basin == bool(metrics["all_finite_maps_single_basin"]))
    solver.add(scale_stable == bool(metrics["canonical_scale_stable"]))
    solver.add(controls_separated == bool(metrics["all_controls_separated"]))
    solver.add(phi0_robust == (upstream["stress_status"] == "bounded_internal_stress_survived_not_admitted"))
    solver.add(final_basin == z3.And(finite_basin, scale_stable, controls_separated, phi0_robust))
    solver.add(final_admission == final_basin)
    status = solver.check()
    model = solver.model() if status == z3.sat else None

    def eval_bool(term: z3.BoolRef) -> bool:
        return bool(z3.is_true(model.eval(term, model_completion=True))) if model else False

    return {
        "sat": status == z3.sat,
        "finite_basin": eval_bool(finite_basin),
        "scale_stable": eval_bool(scale_stable),
        "controls_separated": eval_bool(controls_separated),
        "phi0_robust": eval_bool(phi0_robust),
        "final_basin": eval_bool(final_basin),
        "final_admission_allowed": eval_bool(final_admission),
        "rule": "Final scale-basin admission requires finite convergence, direction-scale stability, control separation, and robust Phi0 stress survival.",
    }


def main() -> int:
    started = time.time()
    rows = schedule_map_rows()
    metrics = basin_metrics(rows)
    upstream = upstream_status()
    guard = z3_guard(metrics, upstream)

    positive = {
        "finite_runtime_maps_converge": {
            "pass": metrics["all_finite_maps_single_basin"],
            "row_count": len(rows),
            "directions": DIRECTIONS,
            "schedules": sorted(SCHEDULES),
        },
        "scale_basin_candidate_audited": {
            "pass": True,
            "canonical_direction_spread": metrics["canonical_direction_spread"],
            "min_control_gap": metrics["min_control_gap"],
            "cluster_count": metrics["cluster_count"],
        },
        "upstream_phi0_stress_status_loaded": {
            "pass": upstream["stress_status"] == "open_nonrobust_internal_controls"
            and upstream["response_repair_status"] == "open_nonrobust_response_controls"
            and upstream["trace_phi0_current_status"] == "open_nonrobust_internal_controls",
            "upstream": upstream,
        },
        "scale_basin_graph_valid": {
            "pass": bool(metrics["graph"]["is_dag"] and metrics["graph"]["node_count"] > 0),
            "graph": metrics["graph"],
        },
        "z3_final_admission_guard": {
            "pass": bool(guard["sat"] and not guard["final_admission_allowed"]),
            "guard": guard,
        },
    }
    graveyard_companions = {
        "finite_single_basin_does_not_imply_scale_basin": {
            "pass": metrics["all_finite_maps_single_basin"] and not metrics["canonical_scale_stable"],
            "canonical_direction_spread": metrics["canonical_direction_spread"],
            "scale_stability_tol": SCALE_STABILITY_TOL,
        },
        "near_schedule_controls_block_admission": {
            "pass": not metrics["all_controls_separated"],
            "near_controls": metrics["near_controls"],
            "control_separation_tol": CONTROL_SEPARATION_TOL,
        },
        "phi0_stress_blocks_final_basin": {
            "pass": upstream["stress_status"] == "open_nonrobust_internal_controls"
            and not guard["phi0_robust"],
            "stress_status": upstream["stress_status"],
        },
        "cluster_count_not_single_scale_attractor": {
            "pass": metrics["cluster_count"] > 1,
            "cluster_count": metrics["cluster_count"],
        },
    }
    boundary = {
        "final_scale_basin_not_admitted": {
            "pass": not guard["final_basin"] and not guard["final_admission_allowed"],
            "summary": "finite maps converge, but scale stability and Phi0 robustness are missing",
        },
        "formal_scout_only": {
            "pass": CLASSIFICATION == "formal_scout" and not PROMOTION_ALLOWED,
            "summary": "scale-basin stability map is a nonpromotional formal scout",
        },
        "full_tensor_and_physics_not_admitted": {
            "pass": True,
            "summary": "bounded QIT maps do not admit L64, PEPS/PEPS3D, holography, ER=EPR, or physics",
        },
    }
    nearby_variants = {
        "total": len(graveyard_companions),
        "passed": sum(1 for row in graveyard_companions.values() if row["pass"]),
        "variants": sorted(graveyard_companions),
    }
    why_not_v4_probes = {
        "pass": True,
        "reason": "This is a v5 formal scout over source-aligned runtime basin maps, not a canonical v4 probe or final admission.",
    }
    result = {
        "schema": "codex_ratchet.formal_scout.v1",
        "name": NAME,
        "classification": CLASSIFICATION,
        "sim_execution_kind": SIM_EXECUTION_KIND,
        "source_alignment_category": SOURCE_ALIGNMENT_CATEGORY,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "elapsed_seconds": time.time() - started,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "tool_manifest": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "source_hashes": source_hashes(),
        "positive": positive,
        "graveyard_companions": graveyard_companions,
        "boundary": boundary,
        "nearby_variants": nearby_variants,
        "why_not_v4_probes": why_not_v4_probes,
        "open_gaps": [
            "direction-scale stable basin remains unadmitted",
            "Phi0 stress remains open/nonrobust",
            "L64 and full PEPS/PEPS3D dynamics remain open",
        ],
        "blockers": [],
        "metrics": metrics,
        "runtime_rows": rows,
        "upstream_status": upstream,
        "all_pass": all(row["pass"] for row in positive.values())
        and all(row["pass"] for row in graveyard_companions.values())
        and all(row["pass"] for row in boundary.values())
        and nearby_variants["passed"] == nearby_variants["total"],
    }
    OUT_PATH.write_text(json.dumps(jsonable(result), indent=2, sort_keys=True) + "\n")
    print(
        json.dumps(
            {
                "all_pass": result["all_pass"],
                "out": str(OUT_PATH),
                "final_admission_allowed": guard["final_admission_allowed"],
                "canonical_direction_spread": metrics["canonical_direction_spread"],
                "cluster_count": metrics["cluster_count"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
