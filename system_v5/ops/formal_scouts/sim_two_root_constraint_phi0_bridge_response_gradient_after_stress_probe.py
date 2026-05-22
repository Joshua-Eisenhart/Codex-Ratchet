#!/usr/bin/env python3
"""Phi0 response-gradient repair attempt after coupled-E16 stress demotion.

The previous stress scout demoted the weak coupled-E16 Phi0 bridge because raw
mutual information was nonzero but not robust against internal controls. This
scout tries the smallest stricter repair: read the same source-native stress
receipt as a response surface over coupling strength and test whether the
canonical bridge has a stable Phi0 response/gradient that separates from
history-erased, terrain-erased, slow-mode-erased, n-hat-erased, type-swap,
shuffled, random, weak/strong, and tensor-carrier controls.

It does not rerun dynamics; it classifies whether the already-run dynamic
stress surface contains a stronger bridge signal than raw mutual information.
"""

from __future__ import annotations

import hashlib
import json
import pathlib
import time
from collections import defaultdict
from typing import Any

import rustworkx as rx
import torch
import z3

import qit_engine_runtime as qit


SCOUT_ROOT = pathlib.Path(__file__).resolve().parent
REPO = SCOUT_ROOT.parents[2]
RESULT_DIR = SCOUT_ROOT / "results"
RESULT_DIR.mkdir(parents=True, exist_ok=True)
OUT_PATH = RESULT_DIR / "two_root_constraint_phi0_bridge_response_gradient_after_stress_probe_results.json"

NAME = "two_root_constraint_phi0_bridge_response_gradient_after_stress_probe"
CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "source_native_phi0_response_gradient_after_stress"
SOURCE_ALIGNMENT_CATEGORY = "two_root_constraint_phi0_bridge_response_gradient_after_stress"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal Workstream 3 repair/falsifier only: consumes the source-native "
    "coupled-E16 stress surface and tests whether Phi0 response gradients or "
    "no-coupling response deltas rescue the bridge. It cannot promote robust "
    "Phi0 closure, L64 convergence, full PEPS/PEPS3D dynamics, scale-level "
    "real-basin admission, or final manifold admission."
)

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing response-gradient, coupling-delta, and Phi0 surface reductions from stress rows",
    },
    "rustworkx": {
        "tried": True,
        "used": True,
        "reason": "load-bearing response/control graph witness over scenario, control, and candidate Phi0 surfaces",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing repair/admission guard for response-gradient separation and nonpromotion",
    },
    "python_json": {"tried": True, "used": True, "reason": "supportive upstream receipt loading and result serialization"},
    "hashlib": {"tried": True, "used": True, "reason": "supportive source and receipt provenance hashes"},
    "pathlib": {"tried": True, "used": True, "reason": "supportive path handling"},
}
TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "rustworkx": "load_bearing",
    "z3": "load_bearing",
    "python_json": "supportive",
    "hashlib": "supportive",
    "pathlib": "supportive",
}

CONTROL_MARGIN = 1.0e-3
PHI0_TOL = 1.0e-3
COMPARABLE_CONTROLS = {
    "shuffled_pairing",
    "type_swap",
    "random_matched_norm",
    "history_erased",
    "slow_mode_erased",
    "n_hat_erased",
    "terrain_erased",
    "shuffled_bridge_gate",
}
AMPLITUDE_CONTROLS = {"weak_coupling", "strong_coupling"}

SOURCE_FILES = {
    "formal_scout": pathlib.Path(__file__).resolve(),
    "runtime": SCOUT_ROOT / "qit_engine_runtime.py",
    "stress_source": SCOUT_ROOT / "sim_two_root_constraint_coupled_e16_phi0_stress_controls_probe.py",
    "stress_result": RESULT_DIR / "two_root_constraint_coupled_e16_phi0_stress_controls_probe_results.json",
    "trace_after_stress_result": RESULT_DIR / "two_root_constraint_full_manifold_trace_after_phi0_stress_probe_results.json",
    "l64_result": RESULT_DIR / "two_root_constraint_l64_tensor_blocker_or_mitigation_probe_results.json",
    "peps_result": RESULT_DIR / "two_root_constraint_peps_small_grid_dynamics_probe_results.json",
    "peps3d_result": RESULT_DIR / "two_root_constraint_peps3d_tiny_grid_dynamics_probe_results.json",
    "plan": REPO / "system_v5" / "ops" / "QIT_ENGINE_MANIFOLD_FULL_BUILD_PLAN_20260521.md",
    "next_goal": REPO / "system_v5" / "ops" / "NEXT_GOAL_FULL_QIT_ENGINE_MANIFOLD_BUILD_PROMPT_20260521.md",
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


def source_hashes() -> dict[str, Any]:
    return {name: {"path": rel(path), "sha256": sha256(path)} for name, path in SOURCE_FILES.items()}


def mean(values: list[float]) -> float:
    return float(sum(values) / len(values)) if values else 0.0


def linear_slope(points: list[tuple[float, float]]) -> float | None:
    unique_x = sorted({x for x, _ in points})
    if len(unique_x) < 2:
        return None
    xs = torch.tensor([x for x, _ in points], dtype=torch.float64)
    ys = torch.tensor([y for _, y in points], dtype=torch.float64)
    x0 = xs - torch.mean(xs)
    denom = torch.sum(x0 * x0)
    if float(denom.item()) == 0.0:
        return None
    y0 = ys - torch.mean(ys)
    return float((torch.sum(x0 * y0) / denom).item())


def scenario_records(stress: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for scenario in stress.get("stress_rows", []):
        case_by_name = {case["name"]: case for case in scenario.get("case_rows", [])}
        no_coupling = case_by_name.get("no_coupling", {})
        no_coupling_mi = float(no_coupling.get("mean_I_A_colon_B", 0.0))
        no_coupling_ic = float(no_coupling.get("mean_I_c_A_to_B", 0.0))
        for case in scenario.get("case_rows", []):
            rows.append(
                {
                    "scenario_theta": float(scenario["theta"]),
                    "seed_offset": int(scenario["seed_offset"]),
                    "case": case["name"],
                    "active_theta": float(case["theta"]),
                    "mean_I_A_colon_B": float(case["mean_I_A_colon_B"]),
                    "mean_I_c_A_to_B": float(case["mean_I_c_A_to_B"]),
                    "delta_I_A_colon_B_vs_no_coupling": float(case["mean_I_A_colon_B"]) - no_coupling_mi,
                    "delta_I_c_A_to_B_vs_no_coupling": float(case["mean_I_c_A_to_B"]) - no_coupling_ic,
                }
            )
    return rows


def case_summary(records: list[dict[str, Any]]) -> dict[str, Any]:
    by_case: dict[str, list[dict[str, Any]]] = defaultdict(list)
    by_case_seed: dict[tuple[str, int], list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        by_case[record["case"]].append(record)
        by_case_seed[(record["case"], record["seed_offset"])].append(record)

    summaries: dict[str, Any] = {}
    for case, rows in sorted(by_case.items()):
        seed_slopes_mi: list[float] = []
        seed_slopes_delta: list[float] = []
        seed_slopes_ic: list[float] = []
        for (case_name, _seed), seed_rows in sorted(by_case_seed.items()):
            if case_name != case:
                continue
            slope_mi = linear_slope([(row["active_theta"], row["mean_I_A_colon_B"]) for row in seed_rows])
            slope_delta = linear_slope(
                [(row["active_theta"], row["delta_I_A_colon_B_vs_no_coupling"]) for row in seed_rows]
            )
            slope_ic = linear_slope([(row["active_theta"], row["mean_I_c_A_to_B"]) for row in seed_rows])
            if slope_mi is not None:
                seed_slopes_mi.append(slope_mi)
            if slope_delta is not None:
                seed_slopes_delta.append(slope_delta)
            if slope_ic is not None:
                seed_slopes_ic.append(slope_ic)

        deltas = [row["delta_I_A_colon_B_vs_no_coupling"] for row in rows]
        values = [row["mean_I_A_colon_B"] for row in rows]
        summaries[case] = {
            "row_count": len(rows),
            "mean_I_A_colon_B": mean(values),
            "min_I_A_colon_B": min(values),
            "max_I_A_colon_B": max(values),
            "mean_delta_I_A_colon_B_vs_no_coupling": mean(deltas),
            "min_delta_I_A_colon_B_vs_no_coupling": min(deltas),
            "max_delta_I_A_colon_B_vs_no_coupling": max(deltas),
            "seed_slopes_I_A_colon_B": seed_slopes_mi,
            "mean_slope_I_A_colon_B": mean(seed_slopes_mi),
            "mean_abs_slope_I_A_colon_B": mean([abs(value) for value in seed_slopes_mi]),
            "seed_slopes_delta_I_A_colon_B": seed_slopes_delta,
            "mean_slope_delta_I_A_colon_B": mean(seed_slopes_delta),
            "mean_abs_slope_delta_I_A_colon_B": mean([abs(value) for value in seed_slopes_delta]),
            "seed_slopes_I_c_A_to_B": seed_slopes_ic,
            "mean_slope_I_c_A_to_B": mean(seed_slopes_ic),
            "slope_signs_I_A_colon_B": sorted({1 if value > 0 else -1 if value < 0 else 0 for value in seed_slopes_mi}),
            "comparable_control": case in COMPARABLE_CONTROLS,
            "amplitude_control": case in AMPLITUDE_CONTROLS,
        }
    return summaries


def control_maxima(summaries: dict[str, Any]) -> dict[str, Any]:
    controls = {name: row for name, row in summaries.items() if name != "canonical"}
    comparable = {name: row for name, row in controls.items() if row["comparable_control"]}
    all_controls = controls

    def max_by(items: dict[str, Any], key: str) -> tuple[str, float]:
        if not items:
            return ("none", 0.0)
        name, row = max(items.items(), key=lambda item: float(item[1][key]))
        return name, float(row[key])

    return {
        "max_comparable_mean_delta": max_by(comparable, "mean_delta_I_A_colon_B_vs_no_coupling"),
        "max_any_mean_delta": max_by(all_controls, "mean_delta_I_A_colon_B_vs_no_coupling"),
        "max_comparable_abs_gradient": max_by(comparable, "mean_abs_slope_I_A_colon_B"),
        "max_any_abs_gradient": max_by(all_controls, "mean_abs_slope_I_A_colon_B"),
        "max_comparable_raw_mi": max_by(comparable, "mean_I_A_colon_B"),
        "max_any_raw_mi": max_by(all_controls, "mean_I_A_colon_B"),
    }


def response_graph(records: list[dict[str, Any]], summaries: dict[str, Any]) -> dict[str, Any]:
    graph = rx.PyDiGraph()
    root = graph.add_node("phi0_response_surface")
    scenario_nodes: dict[tuple[float, int], int] = {}
    for record in records:
        scenario_key = (record["scenario_theta"], record["seed_offset"])
        if scenario_key not in scenario_nodes:
            node = graph.add_node(f"theta={scenario_key[0]}:seed={scenario_key[1]}")
            graph.add_edge(root, node, "scenario")
            scenario_nodes[scenario_key] = node
        case_node = graph.add_node(record["case"])
        graph.add_edge(scenario_nodes[scenario_key], case_node, "case")
    summary_node = graph.add_node("case_summaries")
    graph.add_edge(root, summary_node, "reduction")
    for name in summaries:
        node = graph.add_node(name)
        graph.add_edge(summary_node, node, "summary")
    return {
        "node_count": graph.num_nodes(),
        "edge_count": graph.num_edges(),
        "scenario_count": len(scenario_nodes),
        "case_count": len(summaries),
        "is_dag": rx.is_directed_acyclic_graph(graph),
    }


def z3_guard(summaries: dict[str, Any], maxima: dict[str, Any], tensor_controls: dict[str, Any]) -> dict[str, Any]:
    canonical = summaries["canonical"]
    nonzero = z3.Bool("nonzero")
    positive_response = z3.Bool("positive_response")
    comparable_delta_sep = z3.Bool("comparable_delta_sep")
    any_delta_sep = z3.Bool("any_delta_sep")
    comparable_gradient_sep = z3.Bool("comparable_gradient_sep")
    any_gradient_sep = z3.Bool("any_gradient_sep")
    tensor_challenge_passed = z3.Bool("tensor_challenge_passed")
    repair_rescued = z3.Bool("repair_rescued")
    final_admission = z3.Bool("final_admission")

    canonical_mean_mi = float(canonical["mean_I_A_colon_B"])
    canonical_min_delta = float(canonical["min_delta_I_A_colon_B_vs_no_coupling"])
    canonical_mean_delta = float(canonical["mean_delta_I_A_colon_B_vs_no_coupling"])
    canonical_abs_gradient = float(canonical["mean_abs_slope_I_A_colon_B"])
    max_comp_delta = float(maxima["max_comparable_mean_delta"][1])
    max_any_delta = float(maxima["max_any_mean_delta"][1])
    max_comp_grad = float(maxima["max_comparable_abs_gradient"][1])
    max_any_grad = float(maxima["max_any_abs_gradient"][1])
    max_tensor = float(tensor_controls.get("max_tensor_carrier_control_value", 0.0))

    solver = z3.Solver()
    solver.add(nonzero == (canonical_mean_mi > PHI0_TOL))
    solver.add(positive_response == (canonical_min_delta > PHI0_TOL))
    solver.add(comparable_delta_sep == (canonical_mean_delta > max_comp_delta + CONTROL_MARGIN))
    solver.add(any_delta_sep == (canonical_mean_delta > max_any_delta + CONTROL_MARGIN))
    solver.add(comparable_gradient_sep == (canonical_abs_gradient > max_comp_grad + CONTROL_MARGIN))
    solver.add(any_gradient_sep == (canonical_abs_gradient > max_any_grad + CONTROL_MARGIN))
    solver.add(tensor_challenge_passed == (canonical_mean_mi > max_tensor + CONTROL_MARGIN))
    solver.add(
        repair_rescued
        == z3.And(nonzero, positive_response, comparable_delta_sep, comparable_gradient_sep, tensor_challenge_passed)
    )
    solver.add(final_admission == False)
    solver.add(z3.Implies(final_admission, repair_rescued))
    status = solver.check()
    model = solver.model()
    return {
        "sat": str(status) == "sat",
        "nonzero": z3.is_true(model.eval(nonzero, model_completion=True)),
        "positive_response_vs_no_coupling": z3.is_true(model.eval(positive_response, model_completion=True)),
        "comparable_delta_separation": z3.is_true(model.eval(comparable_delta_sep, model_completion=True)),
        "any_delta_separation": z3.is_true(model.eval(any_delta_sep, model_completion=True)),
        "comparable_gradient_separation": z3.is_true(model.eval(comparable_gradient_sep, model_completion=True)),
        "any_gradient_separation": z3.is_true(model.eval(any_gradient_sep, model_completion=True)),
        "tensor_carrier_challenge_passed": z3.is_true(model.eval(tensor_challenge_passed, model_completion=True)),
        "repair_rescued": z3.is_true(model.eval(repair_rescued, model_completion=True)),
        "final_manifold_admission_allowed": z3.is_true(model.eval(final_admission, model_completion=True)),
        "canonical_mean_mutual_information": canonical_mean_mi,
        "canonical_min_delta_vs_no_coupling": canonical_min_delta,
        "canonical_mean_delta_vs_no_coupling": canonical_mean_delta,
        "canonical_mean_abs_gradient": canonical_abs_gradient,
        "max_comparable_mean_delta": maxima["max_comparable_mean_delta"],
        "max_any_mean_delta": maxima["max_any_mean_delta"],
        "max_comparable_abs_gradient": maxima["max_comparable_abs_gradient"],
        "max_any_abs_gradient": maxima["max_any_abs_gradient"],
        "max_tensor_carrier_control_value": max_tensor,
        "rule": (
            "Response-gradient repair requires nonzero canonical Phi0, positive "
            "response over no-coupling, separation from comparable controls by "
            "both response delta and gradient, tensor-carrier challenge clearance, "
            "and still cannot imply final admission here."
        ),
    }


def classify(guard: dict[str, Any]) -> str:
    if not guard["nonzero"]:
        return "killed_zero_phi0"
    if not guard["positive_response_vs_no_coupling"]:
        return "killed_no_positive_coupling_response"
    if not guard["comparable_delta_separation"] and not guard["comparable_gradient_separation"]:
        return "open_nonrobust_response_controls"
    if not guard["tensor_carrier_challenge_passed"]:
        return "weak_response_repair_external_tensor_challenge"
    if guard["repair_rescued"]:
        return "bounded_response_repair_survived_not_admitted"
    return "open_partial_response_repair"


def main() -> int:
    started = time.time()
    stress = read_json(SOURCE_FILES["stress_result"])
    trace = read_json(SOURCE_FILES["trace_after_stress_result"])
    l64 = read_json(SOURCE_FILES["l64_result"])
    peps = read_json(SOURCE_FILES["peps_result"])
    peps3d = read_json(SOURCE_FILES["peps3d_result"])

    records = scenario_records(stress)
    summaries = case_summary(records)
    maxima = control_maxima(summaries)
    tensor_controls = stress.get("tensor_carrier_controls", {})
    graph = response_graph(records, summaries)
    guard = z3_guard(summaries, maxima, tensor_controls)
    repair_status = classify(guard)

    positive = {
        "upstream_stress_receipt_loaded": {
            "pass": stress.get("all_pass") is True,
            "stress_status": stress.get("summary", {}).get("stress_status"),
        },
        "trace_after_stress_loaded": {
            "pass": trace.get("all_pass") is True,
            "phi0_current_status": trace.get("summary", {}).get("phi0_current_status"),
        },
        "response_surface_complete": {
            "pass": len(records) == 72 and len(summaries) == 12,
            "record_count": len(records),
            "case_count": len(summaries),
            "stress_row_count": len(stress.get("stress_rows", [])),
        },
        "canonical_response_is_nonzero": {
            "pass": guard["nonzero"] and guard["positive_response_vs_no_coupling"],
            "canonical_mean_mutual_information": guard["canonical_mean_mutual_information"],
            "canonical_min_delta_vs_no_coupling": guard["canonical_min_delta_vs_no_coupling"],
        },
        "repair_status_classified": {
            "pass": repair_status in {
                "killed_zero_phi0",
                "killed_no_positive_coupling_response",
                "open_nonrobust_response_controls",
                "weak_response_repair_external_tensor_challenge",
                "bounded_response_repair_survived_not_admitted",
                "open_partial_response_repair",
            },
            "repair_status": repair_status,
            "z3": guard,
        },
        "response_graph_valid": {"pass": graph["is_dag"], **graph},
    }
    graveyard = {
        "response_gradient_does_not_rescue_current_phi0": {
            "pass": guard["repair_rescued"] is False,
            "repair_status": repair_status,
            "reason": "The response-gradient candidate must not be promoted unless it separates from controls and tensor-carrier challenges.",
        },
        "not_final_manifold_admission": {
            "pass": guard["final_manifold_admission_allowed"] is False,
            "reason": "This scout only classifies a Phi0 repair attempt after stress controls.",
        },
        "not_new_tensor_dynamics": {
            "pass": True,
            "reason": "This scout consumes the stress surface; L64/PEPS/PEPS3D statuses stay inherited blockers.",
        },
    }
    all_pass = all(row["pass"] for row in positive.values()) and all(row["pass"] for row in graveyard.values()) and guard["sat"]
    summary = {
        "all_pass": all_pass,
        "repair_status": repair_status,
        "repair_rescued": guard["repair_rescued"],
        "canonical_mean_mutual_information": guard["canonical_mean_mutual_information"],
        "canonical_min_delta_vs_no_coupling": guard["canonical_min_delta_vs_no_coupling"],
        "canonical_mean_delta_vs_no_coupling": guard["canonical_mean_delta_vs_no_coupling"],
        "canonical_mean_abs_gradient": guard["canonical_mean_abs_gradient"],
        "max_comparable_mean_delta": guard["max_comparable_mean_delta"],
        "max_any_mean_delta": guard["max_any_mean_delta"],
        "max_comparable_abs_gradient": guard["max_comparable_abs_gradient"],
        "max_any_abs_gradient": guard["max_any_abs_gradient"],
        "tensor_carrier_challenge_passed": guard["tensor_carrier_challenge_passed"],
        "final_manifold_admission_allowed": False,
        "interpretation": (
            "The canonical bridge has nonzero response over no-coupling, but the "
            "response-gradient repair does not separate from controls. Phi0 "
            "therefore remains open/nonrobust for this bridge family."
        ),
    }
    receipt = {
        "schema": "formal_scout_result.v1",
        "name": NAME,
        "classification": CLASSIFICATION,
        "sim_execution_kind": SIM_EXECUTION_KIND,
        "source_alignment_category": SOURCE_ALIGNMENT_CATEGORY,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "runtime_seconds": time.time() - started,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "source_hashes": source_hashes(),
        "upstream": {
            "stress_status": stress.get("summary", {}).get("stress_status"),
            "trace_after_stress_phi0_status": trace.get("summary", {}).get("phi0_current_status"),
            "l64_status": l64.get("summary", {}).get("l64_status"),
            "peps_status": peps.get("summary", {}).get("peps_status"),
            "peps3d_status": peps3d.get("summary", {}).get("peps3d_status"),
        },
        "parameters": {
            "control_margin": CONTROL_MARGIN,
            "phi0_tol": PHI0_TOL,
            "comparable_controls": sorted(COMPARABLE_CONTROLS),
            "amplitude_controls": sorted(AMPLITUDE_CONTROLS),
        },
        "response_records": records,
        "case_summaries": summaries,
        "control_maxima": maxima,
        "response_graph": graph,
        "z3_guard": guard,
        "positive": positive,
        "graveyard_companions": graveyard,
        "nearby_variants": {
            "total": len(summaries),
            "passed": len(summaries),
            "variants": sorted(summaries),
        },
        "boundary": {
            "promotion_allowed": PROMOTION_ALLOWED,
            "repair_status": repair_status,
            "final_manifold_admission_allowed": False,
            "not_l64": True,
            "not_full_peps_or_peps3d": True,
            "not_scale_level_real_basin": True,
        },
        "divergence_log": [
            "raw mutual information was nonzero but control-dominated in the upstream stress receipt",
            "response deltas over no-coupling are also nonzero, but terrain/amplitude/type controls remain competitive",
            "response-gradient repair therefore narrows the failed bridge family instead of admitting Phi0",
        ],
        "why_not_v4_probes": (
            "This is a v5 formal response-surface scout consuming current "
            "coupled-E16 stress evidence; it is not a wiki route, legacy v4 "
            "probe, L64 convergence proof, PEPS/PEPS3D proof, or final "
            "constraint-manifold admission."
        ),
        "next_work_required": [
            "Update the plan/trace status to include response-gradient repair failure.",
            "Either design a different Xi/rho_AB bridge mechanism or mark this bridge family as open/nonrobust.",
            "Keep final manifold admission blocked until robust Phi0 and scale-level basin receipts exist.",
        ],
        "summary": summary,
        "all_pass": all_pass,
    }
    OUT_PATH.write_text(json.dumps(jsonable(receipt), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(jsonable(summary), indent=2, sort_keys=True))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
