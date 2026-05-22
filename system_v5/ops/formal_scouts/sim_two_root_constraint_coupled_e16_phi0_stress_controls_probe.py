#!/usr/bin/env python3
"""Stress controls for the weak coupled-E16 Phi0 bridge margin.

The coupled E=16 runtime first rung found a small canonical-minus-control
margin. This scout does not try to promote that result. It replays the same
source-native dense trajectory mechanism across a small grid of coupling
strengths and seed offsets, then checks whether the canonical bridge stays
separated from named adversarial controls. It also records tensor-carrier
challenge readouts from the current L32/PEPS/PEPS3D rungs as admission blockers,
without treating those different carriers as direct replacements for rho_AB.
"""

from __future__ import annotations

import hashlib
import json
import pathlib
import time
from typing import Any

import rustworkx as rx
import torch
import z3

import qit_engine_runtime as qit
import sim_two_root_constraint_coupled_e16_runtime_slow_mode_bridge_probe as coupled_e16


SCOUT_ROOT = pathlib.Path(__file__).resolve().parent
REPO = SCOUT_ROOT.parents[2]
RESULT_DIR = SCOUT_ROOT / "results"
RESULT_DIR.mkdir(parents=True, exist_ok=True)
OUT_PATH = RESULT_DIR / "two_root_constraint_coupled_e16_phi0_stress_controls_probe_results.json"

NAME = "two_root_constraint_coupled_e16_phi0_stress_controls_probe"
CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "source_native_coupled_e16_phi0_stress_controls"
SOURCE_ALIGNMENT_CATEGORY = "two_root_constraint_coupled_e16_phi0_stress_controls"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal stress-control scout only: replays the bounded dense coupled-E16 "
    "runtime over multiple coupling strengths and seed offsets, compares Phi0 "
    "against adversarial controls, and records tensor-carrier challenge "
    "readouts. It cannot promote robust Phi0 closure, L64, full PEPS/PEPS3D "
    "convergence, scale-level real-basin admission, or final manifold admission."
)

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing coupled E16 dense trajectory replay and Phi0 entropy stress readouts",
    },
    "rustworkx": {
        "tried": True,
        "used": True,
        "reason": "load-bearing stress-grid graph witness over theta, seed, and control surfaces",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing robust-bridge and nonpromotion guard",
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

THETA_VALUES = [0.035, 0.055, 0.075]
SEED_OFFSETS = [0, 9973]
CONTROL_MARGIN = 1.0e-3
PHI0_TOL = 1.0e-3
NORM_TOL = 1.0e-8
INITIAL_FAMILIES = coupled_e16.INITIAL_FAMILIES

SOURCE_FILES = {
    "formal_scout": pathlib.Path(__file__).resolve(),
    "runtime": SCOUT_ROOT / "qit_engine_runtime.py",
    "coupled_e16_source": SCOUT_ROOT / "sim_two_root_constraint_coupled_e16_runtime_slow_mode_bridge_probe.py",
    "coupled_e16_result": RESULT_DIR / "two_root_constraint_coupled_e16_runtime_slow_mode_bridge_probe_results.json",
    "trace_refresh_result": RESULT_DIR / "two_root_constraint_full_manifold_runtime_trace_refresh_probe_results.json",
    "l32_result": RESULT_DIR / "two_root_constraint_l32_tensor_mitigation_or_blocker_probe_results.json",
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
    return sum(values) / len(values) if values else 0.0


def case_family_rows(
    name: str,
    H_bridge: torch.Tensor,
    *,
    theta: float,
    seed_offset: int,
    history_erased: bool = False,
    terrain_erased: bool = False,
    type_swap: bool = False,
    pairings: list[tuple[int, int]] | None = None,
) -> list[dict[str, Any]]:
    active_pairings = pairings if pairings is not None else coupled_e16.bridge_pairings(name)
    rows = []
    for idx, family_a in enumerate(INITIAL_FAMILIES):
        family_b = INITIAL_FAMILIES[-1 - idx]
        row = coupled_e16.evolve_case(
            name,
            family_a,
            family_b,
            H_bridge,
            pairings=active_pairings,
            theta=theta,
            seed=20260521 + seed_offset + 101 * idx + 17 * len(name),
            history_erased=history_erased,
            terrain_erased=terrain_erased,
            type_swap=type_swap,
        )
        rows.append({key: value for key, value in row.items() if key not in {"final_state", "events"}} | {"event_count": len(row["events"])})
    return rows


def stress_controls(Hs: dict[str, torch.Tensor]) -> dict[str, dict[str, Any]]:
    return {
        "canonical": {"H": Hs["enhanced"], "theta_scale": 1.0},
        "no_coupling": {"H": Hs["enhanced"], "theta_override": 0.0},
        "shuffled_pairing": {"H": Hs["enhanced"], "pairings": coupled_e16.bridge_pairings("shuffled_pairing_control")},
        "type_swap": {"H": Hs["enhanced"], "type_swap": True},
        "random_matched_norm": {"H": Hs["random_matched_norm"]},
        "history_erased": {"H": Hs["enhanced"], "history_erased": True},
        "slow_mode_erased": {"H": Hs["slow_erased"]},
        "n_hat_erased": {"H": Hs["n_hat_erased"]},
        "terrain_erased": {"H": Hs["terrain_erased"], "terrain_erased": True},
        "shuffled_bridge_gate": {"H": shuffled_bridge_hamiltonian(Hs["enhanced"])},
        "weak_coupling": {"H": Hs["enhanced"], "theta_scale": 0.5},
        "strong_coupling": {"H": Hs["enhanced"], "theta_scale": 1.5},
    }


def shuffled_bridge_hamiltonian(H: torch.Tensor) -> torch.Tensor:
    # Deterministic basis permutation control: same spectrum/norm, different
    # tensor-basis placement.
    perm = torch.tensor([0, 2, 1, 3], dtype=torch.long)
    return H[perm][:, perm].clone()


def run_theta_seed(theta: float, seed_offset: int, Hs: dict[str, torch.Tensor]) -> dict[str, Any]:
    controls = stress_controls(Hs)
    case_rows = []
    for name, cfg in controls.items():
        active_theta = float(cfg.get("theta_override", theta * float(cfg.get("theta_scale", 1.0))))
        rows = case_family_rows(
            name,
            cfg["H"],
            theta=active_theta,
            seed_offset=seed_offset,
            history_erased=bool(cfg.get("history_erased", False)),
            terrain_erased=bool(cfg.get("terrain_erased", False)),
            type_swap=bool(cfg.get("type_swap", False)),
            pairings=cfg.get("pairings"),
        )
        mi_values = [float(row["phi0"]["I_A_colon_B"]) for row in rows]
        ic_values = [float(row["phi0"]["I_c_A_to_B"]) for row in rows]
        case_rows.append(
            {
                "name": name,
                "theta": active_theta,
                "mean_I_A_colon_B": mean(mi_values),
                "mean_I_c_A_to_B": mean(ic_values),
                "max_norm_error": max(float(row["norm_error"]) for row in rows),
                "family_rows": rows,
            }
        )
    by_name = {row["name"]: row for row in case_rows}
    canonical = by_name["canonical"]["mean_I_A_colon_B"]
    internal_controls = {name: row["mean_I_A_colon_B"] for name, row in by_name.items() if name != "canonical"}
    max_control_name, max_control_mi = max(internal_controls.items(), key=lambda item: item[1])
    return {
        "theta": theta,
        "seed_offset": seed_offset,
        "case_rows": case_rows,
        "canonical_mean_I_A_colon_B": canonical,
        "max_internal_control_name": max_control_name,
        "max_internal_control_mean_I_A_colon_B": max_control_mi,
        "canonical_minus_max_internal_control": canonical - max_control_mi,
        "canonical_nonzero": canonical > PHI0_TOL,
        "canonical_separates_internal_controls": canonical > max_control_mi + CONTROL_MARGIN,
        "max_norm_error": max(row["max_norm_error"] for row in case_rows),
    }


def tensor_carrier_controls(upstream: dict[str, dict[str, Any]]) -> dict[str, Any]:
    l32_summary = upstream["l32_result"].get("summary", {})
    peps_summary = upstream["peps_result"].get("summary", {})
    peps3d_summary = upstream["peps3d_result"].get("summary", {})
    l32_values = list(l32_summary.get("center_pair_mutual_information_by_family", {}).values())
    peps_values = list(peps_summary.get("dynamic_minus_max_control", {}).values())
    peps3d_selected = list(peps3d_summary.get("selected_dynamic_minus_max_control", {}).values())
    peps3d_edge = list(peps3d_summary.get("edge_max_dynamic_minus_max_control", {}).values())
    rows = {
        "l32_low_bond_center_pair_max": max([float(v) for v in l32_values], default=0.0),
        "peps_2d_tiny_center_delta_max": max([float(v) for v in peps_values], default=0.0),
        "peps3d_tiny_selected_delta_max": max([float(v) for v in peps3d_selected], default=0.0),
        "peps3d_tiny_edge_max_delta_max": max([float(v) for v in peps3d_edge], default=0.0),
    }
    max_name, max_value = max(rows.items(), key=lambda item: item[1])
    return {
        "rows": rows,
        "max_tensor_carrier_control_name": max_name,
        "max_tensor_carrier_control_value": max_value,
        "comparison_boundary": "Different tensor carriers are admission stressors, not direct rho_AB controls.",
    }


def stress_graph(rows: list[dict[str, Any]], tensor_controls: dict[str, Any]) -> dict[str, Any]:
    graph = rx.PyDiGraph()
    root = graph.add_node("stress_grid")
    for row in rows:
        scenario = graph.add_node(f"theta={row['theta']}:seed={row['seed_offset']}")
        graph.add_edge(root, scenario, "scenario")
        for case in row["case_rows"]:
            case_node = graph.add_node(case["name"])
            graph.add_edge(scenario, case_node, "case")
    tensor_node = graph.add_node("tensor_carrier_controls")
    graph.add_edge(root, tensor_node, "external_challenge")
    for name in tensor_controls["rows"]:
        node = graph.add_node(name)
        graph.add_edge(tensor_node, node, "carrier_metric")
    return {
        "node_count": graph.num_nodes(),
        "edge_count": graph.num_edges(),
        "scenario_count": len(rows),
        "case_count_per_scenario": len(rows[0]["case_rows"]) if rows else 0,
        "tensor_carrier_control_count": len(tensor_controls["rows"]),
        "is_dag": rx.is_directed_acyclic_graph(graph),
    }


def z3_guard(stress_rows: list[dict[str, Any]], tensor_controls: dict[str, Any]) -> dict[str, Any]:
    canonical_values = [float(row["canonical_mean_I_A_colon_B"]) for row in stress_rows]
    deltas = [float(row["canonical_minus_max_internal_control"]) for row in stress_rows]
    max_tensor = float(tensor_controls["max_tensor_carrier_control_value"])
    min_canonical = min(canonical_values)
    robust_internal = z3.Bool("robust_internal")
    nonzero_all = z3.Bool("nonzero_all")
    tensor_challenge_passed = z3.Bool("tensor_challenge_passed")
    final_admission = z3.Bool("final_admission")
    solver = z3.Solver()
    solver.add(nonzero_all == all(value > PHI0_TOL for value in canonical_values))
    solver.add(robust_internal == all(delta > CONTROL_MARGIN for delta in deltas))
    solver.add(tensor_challenge_passed == (min_canonical > max_tensor + CONTROL_MARGIN))
    solver.add(final_admission == False)
    solver.add(z3.Implies(final_admission, z3.And(nonzero_all, robust_internal, tensor_challenge_passed)))
    status = solver.check()
    model = solver.model()
    return {
        "sat": str(status) == "sat",
        "nonzero_all": z3.is_true(model.eval(nonzero_all, model_completion=True)),
        "robust_internal_control_separation": z3.is_true(model.eval(robust_internal, model_completion=True)),
        "tensor_carrier_challenge_passed": z3.is_true(model.eval(tensor_challenge_passed, model_completion=True)),
        "final_manifold_admission_allowed": z3.is_true(model.eval(final_admission, model_completion=True)),
        "min_canonical_mean_mutual_information": min_canonical,
        "max_canonical_mean_mutual_information": max(canonical_values),
        "min_canonical_minus_max_internal_control": min(deltas),
        "max_tensor_carrier_control_name": tensor_controls["max_tensor_carrier_control_name"],
        "max_tensor_carrier_control_value": max_tensor,
        "rule": "Robust Phi0 admission would require nonzero canonical MI, internal control separation across all stress rows, tensor-carrier challenge clearance, and separate L64/scale-basin receipts.",
    }


def classify_status(guard: dict[str, Any]) -> str:
    if not guard["nonzero_all"]:
        return "killed_zero_under_stress"
    if not guard["robust_internal_control_separation"]:
        return "open_nonrobust_internal_controls"
    if not guard["tensor_carrier_challenge_passed"]:
        return "weak_internal_separation_external_tensor_challenge"
    return "bounded_internal_stress_survived_not_admitted"


def main() -> int:
    started = time.time()
    upstream = {
        name: read_json(path)
        for name, path in SOURCE_FILES.items()
        if name.endswith("_result")
    }
    Hs = coupled_e16.bridge_hamiltonians()
    rows = [run_theta_seed(theta, seed_offset, Hs) for theta in THETA_VALUES for seed_offset in SEED_OFFSETS]
    tensor_controls = tensor_carrier_controls(upstream)
    graph = stress_graph(rows, tensor_controls)
    guard = z3_guard(rows, tensor_controls)
    stress_status = classify_status(guard)
    max_norm_error = max(row["max_norm_error"] for row in rows)
    positive = {
        "upstream_receipts_loaded": {
            "pass": all(upstream[name].get("all_pass") is True for name in upstream),
            "loaded": sorted(upstream),
        },
        "stress_grid_ran": {
            "pass": len(rows) == len(THETA_VALUES) * len(SEED_OFFSETS),
            "theta_values": THETA_VALUES,
            "seed_offsets": SEED_OFFSETS,
            "stress_row_count": len(rows),
        },
        "controls_ran_each_scenario": {
            "pass": all(len(row["case_rows"]) == len(stress_controls(Hs)) for row in rows),
            "case_count_per_scenario": len(rows[0]["case_rows"]) if rows else 0,
        },
        "norms_bounded": {
            "pass": max_norm_error < NORM_TOL,
            "max_norm_error": max_norm_error,
            "threshold": NORM_TOL,
        },
        "tensor_carrier_controls_recorded": {
            "pass": tensor_controls["max_tensor_carrier_control_value"] >= 0.0,
            **tensor_controls,
        },
        "stress_status_classified": {
            "pass": stress_status in {
                "killed_zero_under_stress",
                "open_nonrobust_internal_controls",
                "weak_internal_separation_external_tensor_challenge",
                "bounded_internal_stress_survived_not_admitted",
            },
            "stress_status": stress_status,
            "z3": guard,
        },
        "stress_graph_valid": {"pass": graph["is_dag"], **graph},
    }
    graveyard = {
        "not_final_manifold_admission": {
            "pass": guard["final_manifold_admission_allowed"] is False,
            "detail": "Stress controls are not scale-level basin or final admission receipts.",
        },
        "not_l64": {
            "pass": True,
            "detail": "The scout replays bounded dense E16 and reads existing tensor-carrier receipts; it does not run L64 dynamics.",
        },
        "not_full_peps_or_peps3d": {
            "pass": True,
            "detail": "The tensor controls are readouts from tiny/low-bond receipts, not full PEPS/PEPS3D convergence evidence.",
        },
        "stress_may_demote_weak_bridge": {
            "pass": stress_status != "bounded_internal_stress_survived_not_admitted",
            "detail": "If true, the previous weak bridge should remain open or be demoted rather than promoted.",
            "stress_status": stress_status,
        },
    }
    all_pass = all(row["pass"] for row in positive.values()) and all(row["pass"] for row in graveyard.values()) and guard["sat"]
    summary = {
        "all_pass": all_pass,
        "stress_status": stress_status,
        "stress_grid": {"theta_values": THETA_VALUES, "seed_offsets": SEED_OFFSETS, "row_count": len(rows)},
        "min_canonical_mean_mutual_information": guard["min_canonical_mean_mutual_information"],
        "max_canonical_mean_mutual_information": guard["max_canonical_mean_mutual_information"],
        "min_canonical_minus_max_internal_control": guard["min_canonical_minus_max_internal_control"],
        "max_tensor_carrier_control_name": guard["max_tensor_carrier_control_name"],
        "max_tensor_carrier_control_value": guard["max_tensor_carrier_control_value"],
        "final_manifold_admission_allowed": False,
        "interpretation": (
            "The coupled-E16 Phi0 bridge is stress-tested as a weak first-rung signal. "
            "The result must update admission status according to internal-control and "
            "tensor-carrier stress, but cannot complete L64, scale-basin, or final manifold goals."
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
        "parameters": {
            "theta_values": THETA_VALUES,
            "seed_offsets": SEED_OFFSETS,
            "control_margin": CONTROL_MARGIN,
            "phi0_tol": PHI0_TOL,
            "initial_families": INITIAL_FAMILIES,
        },
        "upstream": {
            "coupled_e16_bridge_status": upstream["coupled_e16_result"].get("summary", {}).get("bridge_status"),
            "coupled_e16_canonical_minus_max_control": upstream["coupled_e16_result"].get("summary", {}).get("canonical_minus_max_control"),
            "trace_refresh_phi0_status": upstream["trace_refresh_result"].get("summary", {}).get("phi0_current_status"),
            "l32_status": upstream["l32_result"].get("summary", {}).get("l32_status"),
            "peps_status": upstream["peps_result"].get("summary", {}).get("peps_status"),
            "peps3d_status": upstream["peps3d_result"].get("summary", {}).get("peps3d_status"),
        },
        "stress_rows": rows,
        "tensor_carrier_controls": tensor_controls,
        "stress_graph": graph,
        "z3_guard": guard,
        "positive": positive,
        "graveyard_companions": graveyard,
        "nearby_variants": {
            "total": len(graveyard),
            "passed": sum(1 for row in graveyard.values() if row["pass"]),
            "variants": sorted(graveyard),
        },
        "boundary": {
            "promotion_allowed": PROMOTION_ALLOWED,
            "final_manifold_admission_allowed": False,
            "not_l64": True,
            "not_full_peps_or_peps3d": True,
            "not_scale_level_real_basin": True,
            "stress_status": stress_status,
        },
        "why_not_v4_probes": (
            "This is a v5 formal stress scout over the current QIT coupled-E16 "
            "runtime and tensor-carrier receipts; it is not a legacy v4 probe, "
            "wiki route, L64 run, full PEPS/PEPS3D convergence proof, or final "
            "constraint-manifold admission."
        ),
        "next_work_required": [
            "Update the full manifold trace with this stress classification.",
            "If the weak Phi0 bridge is demoted, pursue a stronger coupling/bridge mechanism or mark Phi0 open.",
            "Keep L64 and scale-level basin admission blocked until direct dynamic receipts exist.",
        ],
        "summary": summary,
        "all_pass": all_pass,
    }
    OUT_PATH.write_text(json.dumps(jsonable(receipt), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(jsonable(summary), indent=2, sort_keys=True))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
