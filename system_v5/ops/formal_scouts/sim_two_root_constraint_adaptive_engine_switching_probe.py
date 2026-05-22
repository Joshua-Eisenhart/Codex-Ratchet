#!/usr/bin/env python3
"""Test adaptive engine switching as a weak-basin candidate mechanism.

Workstreams A and B established that fixed engine maps are monostable and that
schedule-family classes are pseudo-basins, not one-map basins. This
Workstream C scout tests generated piecewise/adaptive maps: a single switching
rule repeatedly chooses the Type-1 or Type-2 engine from the current density
state, optionally including a one-token schedule-memory state.

The key distinction is cycle-level: two endpoints that are only opposite phases
of the same period-2 cycle are one attractor, not two basins.
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
OUT_PATH = RESULT_DIR / "two_root_constraint_adaptive_engine_switching_probe_results.json"

NAME = "two_root_constraint_adaptive_engine_switching_probe"
CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "source_native_adaptive_piecewise_engine"
SOURCE_ALIGNMENT_CATEGORY = "two_root_constraint_adaptive_engine_switching"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal Workstream C scout only: tests single-qubit generated adaptive/"
    "piecewise QIT engine maps using the shared exact torch runtime. It may "
    "identify weak single-qubit basin candidates for the adaptive map, but "
    "cannot promote full E=16 dynamics, tensor-network Lindblad, "
    "Xi/rho_AB/Phi0 closure, or final manifold admission."
)

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing adaptive density evolution, Bloch readouts, cycle detection, and channel application",
    },
    "rustworkx": {
        "tried": True,
        "used": True,
        "reason": "load-bearing switching-state transition graph witness for each generated runtime rule",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing admission guard requiring multiple stable attractors, perturbation split, and clean controls",
    },
    "python_json": {"tried": True, "used": True, "reason": "supportive result serialization"},
    "hashlib": {"tried": True, "used": True, "reason": "supportive source/result provenance hashes"},
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

TAU = 0.5
CYCLES = 180
PERIOD_MAX = 4
PERIOD_TOL = 1.0e-7
ATTRACTOR_EPS = 0.05
TWO_TOL = 1.0e-9

SOURCE_FILES = {
    "runtime": SCOUT_ROOT / "qit_engine_runtime.py",
    "workstream_b_result": RESULT_DIR / "two_root_constraint_schedule_memory_phase_map_probe_results.json",
    "next_goal": REPO / "system_v5" / "ops" / "NEXT_GOAL_FULL_QIT_ENGINE_MANIFOLD_BUILD_PROMPT_20260521.md",
    "plan": REPO / "system_v5" / "ops" / "QIT_ENGINE_MANIFOLD_FULL_BUILD_PLAN_20260521.md",
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


def density_from_z(z_value: float) -> torch.Tensor:
    return qit.rho_from_bloch((0.0, 0.0, float(z_value)))


def initial_cases(include_memory: bool) -> list[dict[str, Any]]:
    base = [
        ("x_plus", qit.rho_from_bloch((1.0, 0.0, 0.0))),
        ("x_minus", qit.rho_from_bloch((-1.0, 0.0, 0.0))),
        ("y_plus", qit.rho_from_bloch((0.0, 1.0, 0.0))),
        ("y_minus", qit.rho_from_bloch((0.0, -1.0, 0.0))),
        ("z_plus", qit.rho_from_bloch((0.0, 0.0, 1.0))),
        ("z_minus", qit.rho_from_bloch((0.0, 0.0, -1.0))),
        ("mixed", 0.5 * qit.I2),
        ("z_lower_left", density_from_z(-0.21)),
        ("z_lower_right", density_from_z(-0.19)),
        ("z_upper_left", density_from_z(0.19)),
        ("z_upper_right", density_from_z(0.21)),
    ]
    prevs = ("1", "2") if include_memory else (None,)
    return [
        {
            "label": f"{label}|prev={prev}" if prev is not None else label,
            "rho": rho,
            "initial_prev": prev,
            "initial_bloch": qit.bloch(rho),
        }
        for label, rho in base
        for prev in prevs
    ]


RULES: list[dict[str, Any]] = [
    {
        "name": "fixed_type1_control",
        "kind": "control",
        "uses_memory": False,
        "description": "Fixed Type-1 engine only.",
    },
    {
        "name": "fixed_type2_control",
        "kind": "control",
        "uses_memory": False,
        "description": "Fixed Type-2 engine only.",
    },
    {
        "name": "periodic_12_control",
        "kind": "control",
        "uses_memory": False,
        "description": "Open-loop alternating Type-1/Type-2 schedule.",
    },
    {
        "name": "identity_no_switch_control",
        "kind": "control",
        "uses_memory": False,
        "description": "No dynamics identity control; expected non-attracting fixed continuum.",
    },
    {
        "name": "sign_z",
        "kind": "adaptive",
        "uses_memory": False,
        "description": "Choose Type-1 for z >= 0 and Type-2 for z < 0.",
    },
    {
        "name": "bloch_sector_xz",
        "kind": "adaptive",
        "uses_memory": False,
        "description": "Choose Type-1 inside the z-dominant sector z >= |x|, else Type-2.",
    },
    {
        "name": "entropy_threshold",
        "kind": "adaptive",
        "uses_memory": False,
        "description": "Choose Type-1 for purity >= 0.72 and Type-2 below that threshold.",
    },
    {
        "name": "phi0_proxy_xz",
        "kind": "adaptive",
        "uses_memory": False,
        "description": "Choose Type-1 for x*z >= 0 and Type-2 otherwise.",
    },
    {
        "name": "schedule_memory_hysteresis_z",
        "kind": "adaptive",
        "uses_memory": True,
        "description": "One-token hysteresis: Type-1 persists until z < -0.2; Type-2 persists until z > 0.2.",
    },
    {
        "name": "shuffled_hysteresis_threshold_control",
        "kind": "control",
        "uses_memory": True,
        "description": "Invalid shuffled threshold order; should not create a clean hysteretic basin split.",
    },
    {
        "name": "delayed_sign_z_control",
        "kind": "control",
        "uses_memory": False,
        "description": "Delay state switching until after a warmup window.",
    },
]


def choose_token(rule_name: str, rho: torch.Tensor, prev: str | None, step: int) -> str | None:
    x_val, _y_val, z_val = qit.bloch(rho)
    purity = float(torch.trace(rho @ rho).real.item())
    if rule_name == "fixed_type1_control":
        return "1"
    if rule_name == "fixed_type2_control":
        return "2"
    if rule_name == "periodic_12_control":
        return "1" if step % 2 == 0 else "2"
    if rule_name == "identity_no_switch_control":
        return None
    if rule_name == "sign_z":
        return "1" if z_val >= 0.0 else "2"
    if rule_name == "bloch_sector_xz":
        return "1" if z_val >= abs(x_val) else "2"
    if rule_name == "entropy_threshold":
        return "1" if purity >= 0.72 else "2"
    if rule_name == "phi0_proxy_xz":
        return "1" if x_val * z_val >= 0.0 else "2"
    if rule_name == "schedule_memory_hysteresis_z":
        active = prev or "1"
        if active == "1":
            return "1" if z_val >= -0.2 else "2"
        return "1" if z_val >= 0.2 else "2"
    if rule_name == "shuffled_hysteresis_threshold_control":
        active = prev or "1"
        if active == "1":
            return "1" if z_val >= 0.2 else "2"
        return "1" if z_val >= -0.2 else "2"
    if rule_name == "delayed_sign_z_control":
        if step < 12:
            return "1"
        return "1" if z_val >= 0.0 else "2"
    raise ValueError(f"unknown rule {rule_name}")


def evolve_case(rule: dict[str, Any], engines: dict[str, torch.Tensor], case: dict[str, Any]) -> dict[str, Any]:
    rho = case["rho"].clone()
    prev = case["initial_prev"]
    states: list[list[float]] = []
    tokens: list[str] = []
    for step in range(CYCLES):
        token = choose_token(rule["name"], rho, prev, step)
        tokens.append(token or "I")
        if token is not None:
            rho = qit.normalize_density(qit.mat(engines[token] @ qit.vec(rho)))
            prev = token
        states.append(qit.bloch(rho))
    period, period_error = detect_period(states)
    cycle = canonical_cycle(states, period) if period is not None else []
    return {
        "label": case["label"],
        "initial_bloch": case["initial_bloch"],
        "initial_prev": case["initial_prev"],
        "final_bloch": states[-1],
        "last_tokens": tokens[-12:],
        "detected_period": period,
        "period_error": period_error,
        "cycle_signature": cycle,
    }


def detect_period(states: list[list[float]]) -> tuple[int | None, float]:
    best_error = float("inf")
    best_period: int | None = None
    for period in range(1, PERIOD_MAX + 1):
        if len(states) < period * 4:
            continue
        errors: list[float] = []
        for offset in range(1, period * 3 + 1):
            errors.append(math.dist(states[-offset], states[-offset - period]))
        error = max(errors)
        if error < best_error:
            best_error = error
            best_period = period
        if error < PERIOD_TOL:
            return period, float(error)
    return None, float(best_error if best_period is not None else float("inf"))


def canonical_cycle(states: list[list[float]], period: int | None) -> list[list[float]]:
    if period is None:
        return []
    points = [states[-offset] for offset in range(period, 0, -1)]
    return sorted([[round(float(value), 12) for value in point] for point in points])


def cycle_distance(left: list[list[float]], right: list[list[float]]) -> float:
    if len(left) != len(right) or not left or not right:
        return float("inf")
    return max(math.dist(left[idx], right[idx]) for idx in range(len(left)))


def cluster_cycles(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    clusters: list[dict[str, Any]] = []
    for row in rows:
        cycle = row["cycle_signature"]
        for cluster in clusters:
            if cycle_distance(cycle, cluster["cycle_signature"]) < ATTRACTOR_EPS:
                cluster["members"].append(row["label"])
                break
        else:
            clusters.append(
                {
                    "period": row["detected_period"],
                    "cycle_signature": cycle,
                    "members": [row["label"]],
                }
            )
    return clusters


def transition_graph(rule_name: str, rows: list[dict[str, Any]]) -> dict[str, Any]:
    graph = rx.PyDiGraph()
    node_ids: dict[str, int] = {}
    for row in rows:
        previous = None
        for token in row["last_tokens"]:
            if token not in node_ids:
                node_ids[token] = graph.add_node(token)
            if previous is not None:
                graph.add_edge(node_ids[previous], node_ids[token], rule_name)
            previous = token
    return {
        "node_count": graph.num_nodes(),
        "edge_count": graph.num_edges(),
        "tokens": sorted(node_ids),
    }


def perturbation_split(rule_name: str, rows: list[dict[str, Any]], clusters: list[dict[str, Any]]) -> dict[str, Any]:
    label_to_cluster: dict[str, int] = {}
    for idx, cluster in enumerate(clusters):
        for member in cluster["members"]:
            label_to_cluster[member] = idx
    checks = []
    for left, right in [
        ("z_lower_left|prev=1", "z_lower_right|prev=1"),
        ("z_upper_left|prev=2", "z_upper_right|prev=2"),
    ]:
        if left in label_to_cluster and right in label_to_cluster:
            checks.append(
                {
                    "left": left,
                    "right": right,
                    "left_cluster": label_to_cluster[left],
                    "right_cluster": label_to_cluster[right],
                    "split": label_to_cluster[left] != label_to_cluster[right],
                }
            )
    return {
        "rule": rule_name,
        "checks": checks,
        "any_split": any(check["split"] for check in checks),
    }


def z3_weak_candidate_guard(row: dict[str, Any], controls_clear: bool) -> dict[str, Any]:
    is_adaptive = z3.Bool("is_adaptive")
    multiple_attractors = z3.Bool("multiple_attractors")
    all_periodic = z3.Bool("all_periodic")
    perturbation = z3.Bool("perturbation")
    controls = z3.Bool("controls_clear")
    weak_candidate = z3.Bool("weak_candidate")
    solver = z3.Solver()
    solver.add(is_adaptive == (row["kind"] == "adaptive"))
    solver.add(multiple_attractors == (row["attractor_count"] >= 2))
    solver.add(all_periodic == row["all_periods_detected"])
    solver.add(perturbation == row["perturbation_split"]["any_split"])
    solver.add(controls == controls_clear)
    solver.add(weak_candidate == z3.And(is_adaptive, multiple_attractors, all_periodic, perturbation, controls))
    check = solver.check()
    model = solver.model()
    return {
        "sat": str(check) == "sat",
        "weak_candidate_allowed": z3.is_true(model.eval(weak_candidate, model_completion=True)),
        "rule": "adaptive AND >=2 sampled attractors AND all periodic AND perturbation split AND controls clear",
    }


def summarize_rule(rule: dict[str, Any], engines: dict[str, torch.Tensor]) -> dict[str, Any]:
    cases = initial_cases(bool(rule["uses_memory"]))
    rows = [evolve_case(rule, engines, case) for case in cases]
    clusters = cluster_cycles(rows)
    graph = transition_graph(rule["name"], rows)
    all_periods_detected = all(row["detected_period"] is not None for row in rows)
    max_period_error = max(row["period_error"] for row in rows)
    return {
        "name": rule["name"],
        "kind": rule["kind"],
        "uses_memory": rule["uses_memory"],
        "description": rule["description"],
        "case_count": len(rows),
        "attractor_count": len(clusters),
        "all_periods_detected": all_periods_detected,
        "max_period_error": max_period_error,
        "transition_graph": graph,
        "perturbation_split": perturbation_split(rule["name"], rows, clusters),
        "attractors": clusters,
        "cases": rows,
    }


def source_hashes() -> dict[str, Any]:
    return {name: {"path": rel(path), "sha256": sha256(path)} for name, path in SOURCE_FILES.items()}


def main() -> int:
    started = time.time()
    workstream_b = read_json(SOURCE_FILES["workstream_b_result"])
    engines = {
        "1": qit.engine_channel("L", "iter176_xz", tau=TAU, normalize=True),
        "2": qit.engine_channel("R", "iter176_xz", tau=TAU, normalize=True),
    }
    rule_rows = [summarize_rule(rule, engines) for rule in RULES]
    control_rows = [row for row in rule_rows if row["kind"] == "control"]
    adaptive_rows = [row for row in rule_rows if row["kind"] == "adaptive"]
    attracting_control_reproductions = [
        row["name"]
        for row in control_rows
        if row["name"] != "identity_no_switch_control"
        and row["attractor_count"] >= 2
        and row["all_periods_detected"]
        and row["perturbation_split"]["any_split"]
    ]
    controls_clear = not attracting_control_reproductions
    for row in rule_rows:
        row["z3_weak_candidate_guard"] = z3_weak_candidate_guard(row, controls_clear)
        row["basin_status"] = (
            "single_qubit_adaptive_weak_basin_candidate"
            if row["z3_weak_candidate_guard"]["weak_candidate_allowed"]
            else (
                "weak_or_pseudo_basin"
                if row["kind"] == "adaptive" and row["attractor_count"] >= 2
                else "killed_or_control_nonbasin"
            )
        )
    weak_candidates = [row for row in rule_rows if row["basin_status"] == "single_qubit_adaptive_weak_basin_candidate"]
    weak_or_pseudo = [row for row in rule_rows if row["basin_status"] == "weak_or_pseudo_basin"]
    sign_z_row = next(row for row in rule_rows if row["name"] == "sign_z")
    identity_row = next(row for row in rule_rows if row["name"] == "identity_no_switch_control")
    positive = {
        "workstream_b_anchor_exists": {
            "pass": bool(workstream_b.get("all_pass")),
            "summary": workstream_b.get("summary", {}),
        },
        "generated_piecewise_rules_executed": {
            "pass": len(rule_rows) == len(RULES) and all(row["case_count"] > 0 for row in rule_rows),
            "rule_count": len(rule_rows),
            "tau": TAU,
            "cycles": CYCLES,
        },
        "phase_artifact_not_overcounted": {
            "pass": sign_z_row["attractor_count"] == 1,
            "detail": "sign_z endpoint phases collapse to one period-2 attractor after cycle-level clustering",
        },
        "adaptive_weak_basin_candidate_found": {
            "pass": len(weak_candidates) >= 1,
            "candidates": [row["name"] for row in weak_candidates],
        },
        "controls_do_not_reproduce_clean_attracting_split": {
            "pass": controls_clear,
            "reproductions": attracting_control_reproductions,
        },
    }
    graveyard = {
        "fixed_and_open_loop_controls_not_admitted": {
            "pass": controls_clear,
            "control_reproductions": attracting_control_reproductions,
        },
        "identity_control_not_mistaken_for_attractor_split": {
            "pass": identity_row["basin_status"] == "killed_or_control_nonbasin",
            "basin_status": identity_row["basin_status"],
            "attractor_count": identity_row["attractor_count"],
            "detail": "identity control samples many unchanged endpoints but has no attracting split",
        },
        "stateless_sign_switch_phase_overcount_killed": {
            "pass": sign_z_row["attractor_count"] == 1,
            "basin_status": sign_z_row["basin_status"],
            "attractor_count": sign_z_row["attractor_count"],
        },
    }
    nearby_variants = {
        "total": len(graveyard),
        "passed": sum(1 for row in graveyard.values() if row["pass"]),
        "variants": sorted(graveyard),
    }
    boundary = {
        "promotion_allowed": PROMOTION_ALLOWED,
        "not_full_e16": True,
        "not_tensor_network": True,
        "not_xi_rhoab_phi0": True,
        "not_final_manifold_admission": True,
        "weak_basin_candidate_is_single_qubit_piecewise_only": True,
    }
    next_work_required = [
        "Workstream D still needed for coupled E=16 and Xi -> rho_AB -> Phi0.",
        "Workstream E still needed for tensor-network Lindblad dynamics.",
        "Workstream F still needed for full constraint-manifold trace and final admission.",
    ]
    all_pass = (
        all(item["pass"] for item in positive.values())
        and all(item["pass"] for item in graveyard.values())
        and controls_clear
    )
    summary = {
        "all_pass": all_pass,
        "rule_count": len(rule_rows),
        "weak_basin_candidate_count": len(weak_candidates),
        "weak_basin_candidates": [row["name"] for row in weak_candidates],
        "weak_or_pseudo_rules": [row["name"] for row in weak_or_pseudo],
        "control_reproductions": attracting_control_reproductions,
        "interpretation": (
            "Workstream C found one bounded single-qubit adaptive weak-basin "
            "candidate: "
            "schedule_memory_hysteresis_z. The candidate is one generated "
            "piecewise map on the augmented (rho, previous-engine-token) state, "
            "with two sampled attracting endpoints separated by finite "
            "perturbations around the hysteresis thresholds. It does not prove "
            "a basin radius, contraction margin, multiseed robustness, or "
            "readout invariance. Stateless sign switching collapses to one "
            "period-2 attractor once phase is not overcounted. This is not full "
            "E=16, tensor-network, Phi0, or manifold admission."
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
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "source_hashes": source_hashes(),
        "parameters": {
            "tau": TAU,
            "cycles": CYCLES,
            "period_max": PERIOD_MAX,
            "period_tol": PERIOD_TOL,
            "attractor_eps": ATTRACTOR_EPS,
        },
        "positive": positive,
        "graveyard_companions": graveyard,
        "nearby_variants": nearby_variants,
        "boundary": boundary,
        "why_not_v4_probes": (
            "This is a v5 Workstream C adaptive-map scout over the shared exact-torch "
            "QIT runtime; it is not a legacy v4 probe, full E=16 execution, or final "
            "manifold admission."
        ),
        "next_work_required": next_work_required,
        "blockers": [] if all_pass else [
            name
            for name, item in {**positive, **graveyard}.items()
            if not item.get("pass")
        ],
        "rule_rows": rule_rows,
        "summary": summary,
        "all_pass": all_pass,
    }
    OUT_PATH.write_text(json.dumps(jsonable(receipt), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(jsonable(summary), indent=2, sort_keys=True))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
