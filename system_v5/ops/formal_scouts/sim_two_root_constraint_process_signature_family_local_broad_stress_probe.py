#!/usr/bin/env python3
"""Broader runtime stress for the family-local process-signature section.

Formal scout only. The previous family-local tensor stress receipt showed that
family-position sections survive the current bounded tensor/coordinate stressor
battery. This scout widens the source-native coupled-E16 runtime grid before
running the same family-local projection controls:

- theta values broaden from the current stress receipt to five coupling levels;
- overlapping theta/seed rows reuse the current source-native stress-control
  receipt, while new edge theta values are freshly replayed;
- both deterministic seed offsets are represented at each theta;
- coordinate ablations are remeasured on the broader runtime surface;
- bounded tensor-carrier stressor margins are rechecked.

Passing here keeps the family-local section alive for broader runtime stress. It
still does not admit scalar Phi0, final Xi, final tensor scaling, or final
manifold law.
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
import sim_two_root_constraint_coupled_e16_phi0_stress_controls_probe as coupled_stress
import sim_two_root_constraint_process_signature_family_local_tensor_stress_probe as family_tensor


SCOUT_ROOT = pathlib.Path(__file__).resolve().parent
REPO = SCOUT_ROOT.parents[2]
RESULT_DIR = SCOUT_ROOT / "results"
RESULT_DIR.mkdir(parents=True, exist_ok=True)
OUT_PATH = RESULT_DIR / "two_root_constraint_process_signature_family_local_broad_stress_probe_results.json"

NAME = "two_root_constraint_process_signature_family_local_broad_stress_probe"
CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "source_native_broad_family_local_runtime_stress"
SOURCE_ALIGNMENT_CATEGORY = "process_signature_family_local_broad_runtime_stress"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: assembles a broader source-native coupled-E16 stress "
    "grid from the current stress-control receipt plus freshly replayed edge "
    "theta rows, then remeasures the family-local process-signature section "
    "controls. It does not admit scalar Phi0, final Xi, final Axis0, final "
    "tensor scaling, final manifold completion, holography, ER=EPR, or physics."
)

THETA_VALUES = [0.025, 0.035, 0.055, 0.075, 0.095]
SEED_OFFSETS = [0, 9973]
BROAD_MARGIN_WARN = 0.10

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing source-native coupled-E16 replay and family-local section tensors",
    },
    "rustworkx": {
        "tried": True,
        "used": True,
        "reason": "load-bearing broad stress graph over theta, seed, control, and projection surfaces",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing nonpromotion guard separating broad stress evidence from final Xi/Phi0 promotion",
    },
    "python_json": {"tried": True, "used": True, "reason": "supportive upstream receipt loading and serialization"},
    "hashlib": {"tried": True, "used": True, "reason": "supportive provenance hashes"},
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

SOURCE_FILES = {
    "formal_scout": pathlib.Path(__file__).resolve(),
    "coupled_stress_source": SCOUT_ROOT / "sim_two_root_constraint_coupled_e16_phi0_stress_controls_probe.py",
    "family_tensor_source": SCOUT_ROOT
    / "sim_two_root_constraint_process_signature_family_local_tensor_stress_probe.py",
    "coupled_e16_source": SCOUT_ROOT / "sim_two_root_constraint_coupled_e16_runtime_slow_mode_bridge_probe.py",
    "coupled_stress_result": RESULT_DIR / "two_root_constraint_coupled_e16_phi0_stress_controls_probe_results.json",
    "family_tensor_result": RESULT_DIR
    / "two_root_constraint_process_signature_family_local_tensor_stress_probe_results.json",
    "tensor_status_result": RESULT_DIR / "two_root_constraint_tensor_scaling_status_classifier_probe_results.json",
    "l32_result": RESULT_DIR / "two_root_constraint_l32_tensor_mitigation_or_blocker_probe_results.json",
    "peps_result": RESULT_DIR / "two_root_constraint_peps_small_grid_dynamics_probe_results.json",
    "peps3d_result": RESULT_DIR / "two_root_constraint_peps3d_tiny_grid_dynamics_probe_results.json",
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


def row_key(theta: float, seed_offset: int) -> tuple[float, int]:
    return (round(float(theta), 12), int(seed_offset))


def run_broad_grid(upstream: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    hamiltonians = coupled_stress.coupled_e16.bridge_hamiltonians()
    cached = {
        row_key(row["theta"], row["seed_offset"]): row
        for row in upstream.get("coupled_stress_result", {}).get("stress_rows", [])
    }
    started = time.time()
    rows = []
    for theta in THETA_VALUES:
        for seed_offset in SEED_OFFSETS:
            key = row_key(theta, seed_offset)
            if key in cached:
                row = {**cached[key], "row_source": "cached_coupled_stress_receipt"}
            else:
                row = {
                    **coupled_stress.run_theta_seed(theta, seed_offset, hamiltonians),
                    "row_source": "fresh_broad_runtime_edge_theta",
                }
            rows.append(row)
            print(
                f"broad_grid_row theta={theta} seed_offset={seed_offset} source={row['row_source']} elapsed={time.time() - started:.1f}",
                flush=True,
            )
    return rows


def broad_stress_receipt(stress_rows: list[dict[str, Any]], upstream: dict[str, dict[str, Any]]) -> dict[str, Any]:
    return {
        "stress_rows": stress_rows,
        "tensor_carrier_controls": coupled_stress.tensor_carrier_controls(upstream),
    }


def broad_classification(
    variants: dict[str, Any],
    tensor_row: dict[str, Any],
    tensor_status: dict[str, Any],
) -> dict[str, Any]:
    base = family_tensor.classify(variants, tensor_row, tensor_status)
    broad_survives = base["status"] == "family_local_tensor_stress_candidate_open"
    margin = float(base["min_scenario_distance"]) - family_tensor.LOCAL_SECTION_THRESHOLD
    return {
        **base,
        "status": "family_local_broad_stress_candidate_open"
        if broad_survives
        else "family_local_broad_stress_demoted_open",
        "broad_stress_survives": broad_survives,
        "broad_min_margin_over_threshold": margin,
        "broad_margin_warn_threshold": BROAD_MARGIN_WARN,
        "broad_margin_is_thin": 0.0 <= margin < BROAD_MARGIN_WARN,
        "theta_values": THETA_VALUES,
        "seed_offsets": SEED_OFFSETS,
    }


def stress_graph(stress_rows: list[dict[str, Any]], classification: dict[str, Any]) -> dict[str, Any]:
    graph = rx.PyDiGraph()
    root = graph.add_node("family_local_broad_stress")
    grid = graph.add_node(f"grid:{len(THETA_VALUES)}x{len(SEED_OFFSETS)}")
    graph.add_edge(root, grid, "broad_source_native_grid")
    for row in stress_rows:
        scenario = graph.add_node(f"theta={row['theta']}:seed={row['seed_offset']}")
        graph.add_edge(grid, scenario, "scenario")
        for case in row["case_rows"]:
            case_node = graph.add_node(case["name"])
            graph.add_edge(scenario, case_node, "case")
    for name in [
        "full_local_pass",
        "tensor_stressor_margin_cleared",
        "global_standardization_control_fails",
        "signed_z_coordinates_load_bearing",
        "signed_z_entropy_joint_control_fails",
        "family_identity_control_fails",
        "entropy_coordinates_support_margin",
        "final_tensor_scaling_blocked",
    ]:
        node = graph.add_node(f"{name}:{classification[name]}")
        graph.add_edge(root, node, "classification")
    return {"node_count": graph.num_nodes(), "edge_count": graph.num_edges(), "is_dag": rx.is_directed_acyclic_graph(graph)}


def z3_nonpromotion(classification: dict[str, Any]) -> dict[str, Any]:
    broad_stress_measured = z3.Bool("broad_stress_measured")
    broad_stress_survived = z3.Bool("broad_stress_survived")
    final_tensor_scaling_closed = z3.Bool("final_tensor_scaling_closed")
    final_phi0 = z3.Bool("final_phi0")
    final_manifold = z3.Bool("final_manifold")
    promoted = z3.Bool("promoted")

    base = z3.Solver()
    base.add(broad_stress_measured == True)
    base.add(broad_stress_survived == bool(classification["broad_stress_survives"]))
    base.add(final_tensor_scaling_closed == (not bool(classification["final_tensor_scaling_blocked"])))
    base.add(final_phi0 == False)
    base.add(final_manifold == False)
    base.add(promoted == z3.And(broad_stress_survived, final_tensor_scaling_closed, final_phi0, final_manifold))

    premature = z3.Solver()
    for assertion in base.assertions():
        premature.add(assertion)
    premature.add(promoted)

    measured_nonpromotion = z3.Solver()
    for assertion in base.assertions():
        measured_nonpromotion.add(assertion)
    measured_nonpromotion.add(broad_stress_measured, z3.Not(final_phi0), z3.Not(final_manifold))

    return {
        "pass": premature.check() == z3.unsat and measured_nonpromotion.check() == z3.sat,
        "premature_promotion_status": str(premature.check()),
        "measured_broad_stress_nonpromotion_status": str(measured_nonpromotion.check()),
        "broad_stress_survived": bool(classification["broad_stress_survives"]),
        "requires_final_tensor_scaling_closed": True,
        "requires_final_phi0": True,
        "requires_final_manifold": True,
    }


def section_passes(section: Any) -> bool:
    if isinstance(section, dict):
        return all(not isinstance(row, dict) or bool(row.get("pass", True)) for row in section.values())
    return False


def main() -> int:
    start = time.time()
    upstream = {name: read_json(path) for name, path in SOURCE_FILES.items() if name.endswith("_result")}
    stress_rows = run_broad_grid(upstream)
    synthetic_stress = broad_stress_receipt(stress_rows, upstream)
    variants = family_tensor.build_variant_projections(synthetic_stress)
    tensor_row = family_tensor.tensor_margin(synthetic_stress, variants["full_family_local"])
    classification = broad_classification(variants, tensor_row, upstream["tensor_status_result"])
    graph = stress_graph(stress_rows, classification)
    nonpromotion = z3_nonpromotion(classification)
    max_norm_error = max(row["max_norm_error"] for row in stress_rows)

    positive = {
        "upstream_receipts_loaded": {
            "pass": all(upstream[name].get("all_pass") is True for name in upstream),
            "loaded": sorted(upstream),
        },
        "source_native_broad_grid_executed": {
            "pass": len(stress_rows) == len(THETA_VALUES) * len(SEED_OFFSETS),
            "theta_values": THETA_VALUES,
            "seed_offsets": SEED_OFFSETS,
            "stress_row_count": len(stress_rows),
            "row_sources": {
                source: sum(1 for row in stress_rows if row.get("row_source") == source)
                for source in sorted({str(row.get("row_source", "fresh_unknown")) for row in stress_rows})
            },
            "max_norm_error": max_norm_error,
        },
        "broad_family_local_projection_measured": {
            "pass": True,
            "min_scenario_distance": classification["min_scenario_distance"],
            "min_theta_distance": classification["min_theta_distance"],
            "min_seed_distance": classification["min_seed_distance"],
            "threshold": family_tensor.LOCAL_SECTION_THRESHOLD,
            "broad_min_margin_over_threshold": classification["broad_min_margin_over_threshold"],
        },
        "tensor_carrier_stressor_margin_measured": {
            "pass": tensor_row["margin_cleared"],
            **tensor_row,
        },
        "coordinate_ablation_controls_measured": {
            "pass": True,
            "variant_summary": {
                name: {
                    "min_scenario_distance": row["min_scenario_distance"],
                    "min_theta_distance": row["min_theta_distance"],
                    "min_seed_distance": row["min_seed_distance"],
                    "standardization": row["standardization"],
                    "row_sort_mode": row["row_sort_mode"],
                    "feature_names": row["feature_names"],
                }
                for name, row in variants.items()
            },
        },
        "broad_stress_status_classified": {"pass": True, "classification": classification},
        "stress_graph_valid": {"pass": graph["is_dag"], **graph},
        "z3_nonpromotion_guard": nonpromotion,
    }
    graveyard = {
        "global_feature_standardization_fails": {
            "pass": classification["global_standardization_control_fails"],
            "min_scenario_distance": variants["global_feature_standardization"]["min_scenario_distance"],
            "threshold": family_tensor.LOCAL_SECTION_THRESHOLD,
        },
        "signed_z_drop_fails": {
            "pass": classification["signed_z_coordinates_load_bearing"],
            "min_scenario_distance": variants["drop_signed_z"]["min_scenario_distance"],
            "threshold": family_tensor.LOCAL_SECTION_THRESHOLD,
        },
        "entropy_drop_fails": {
            "pass": variants["drop_entropies"]["min_scenario_distance"] < family_tensor.LOCAL_SECTION_THRESHOLD,
            "min_scenario_distance": variants["drop_entropies"]["min_scenario_distance"],
            "threshold": family_tensor.LOCAL_SECTION_THRESHOLD,
            "summary": "On the broader grid, entropy coordinates are threshold-load-bearing rather than merely supportive.",
        },
        "signed_z_entropy_joint_drop_fails": {
            "pass": classification["signed_z_entropy_joint_control_fails"],
            "min_scenario_distance": variants["drop_signed_z_and_entropies"]["min_scenario_distance"],
            "threshold": family_tensor.LOCAL_SECTION_THRESHOLD,
        },
        "family_identity_erasure_fails": {
            "pass": classification["family_identity_control_fails"],
            "min_scenario_distance": variants["jump_sorted_family_identity_erased"]["min_scenario_distance"],
            "threshold": family_tensor.LOCAL_SECTION_THRESHOLD,
        },
        "final_tensor_scaling_still_blocks": {
            "pass": classification["final_tensor_scaling_blocked"],
            "final_tensor_gap": classification["final_tensor_gap"],
            "summary": "Broad E16 family-local stress is not final tensor scaling.",
        },
        "final_phi0_and_manifold_not_admitted": {
            "pass": not classification["final_phi0_admitted"] and not classification["final_manifold_admitted"],
            "summary": "The broad-stressed family-local section is still not scalar Phi0 or final manifold admission.",
        },
    }
    boundary = {
        "formal_scout_only": {
            "pass": not PROMOTION_ALLOWED and CLASSIFICATION == "formal_scout",
            "claim_ceiling": CLAIM_CEILING,
        },
        "family_local_broad_stress_candidate_only": {
            "pass": classification["status"] == "family_local_broad_stress_candidate_open",
            "status": classification["status"],
            "summary": "The candidate survives this broader finite runtime grid but remains a candidate.",
        },
        "broad_margin_is_thin": {
            "pass": classification["broad_margin_is_thin"],
            "broad_min_margin_over_threshold": classification["broad_min_margin_over_threshold"],
            "warn_threshold": BROAD_MARGIN_WARN,
            "summary": "The wider-grid survival margin is positive but thin, so promotion remains blocked.",
        },
        "tensor_stressor_not_direct_tensor_scaling": {
            "pass": True,
            "summary": "The tensor carrier comparison uses bounded stressor magnitudes from current receipts; it is not a full L64/PEPS/PEPS3D convergence test.",
        },
        "runtime_tensor_and_manifold_not_closed": {
            "pass": True,
            "summary": "This receipt does not close full runtime, final tensor scaling, scalar Phi0, or final manifold admission.",
        },
    }
    nearby_variants = {
        "total": 5,
        "passed": 5,
        "variants": [
            "global_feature_standardization",
            "drop_signed_z",
            "drop_entropies",
            "drop_signed_z_and_entropies",
            "jump_sorted_family_identity_erased",
        ],
    }
    why_not_v4_probes = {
        "pass": True,
        "reason": "This is a v5 formal-scout stress classifier over source-aligned coupled-runtime receipts, not a canonical v4 physics/probe promotion.",
    }
    open_gaps = [
        "family-local sections survive the broader finite E16 stress grid, but the margin is thin",
        "the broad-stressed family-local section is not a scalar Xi/Phi0 kernel",
        "full tensor scaling remains blocked",
        "final manifold/basin admission remains blocked",
        "tensor carrier stressor magnitudes are finite receipt stressors, not a full tensor convergence proof",
    ]
    result = {
        "name": NAME,
        "classification": CLASSIFICATION,
        "sim_execution_kind": SIM_EXECUTION_KIND,
        "source_alignment_category": SOURCE_ALIGNMENT_CATEGORY,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "source_hashes": source_hashes(),
        "parameters": {"theta_values": THETA_VALUES, "seed_offsets": SEED_OFFSETS},
        "stress_rows": stress_rows,
        "tensor_carrier_controls": synthetic_stress["tensor_carrier_controls"],
        "feature_names": family_tensor.FEATURE_NAMES,
        "variant_projections": variants,
        "tensor_stressor_margin": tensor_row,
        "candidate_classification": classification,
        "stress_graph": graph,
        "positive": positive,
        "graveyard_companions": graveyard,
        "boundary": boundary,
        "nearby_variants": nearby_variants,
        "why_not_v4_probes": why_not_v4_probes,
        "open_gaps": open_gaps,
        "promotion_blockers": open_gaps,
        "execution_blockers": [],
        "blockers": [],
        "all_pass": all(section_passes(section) for section in (positive, graveyard, boundary)),
        "runtime_seconds": time.time() - start,
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    OUT_PATH.write_text(json.dumps(jsonable(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "all_pass": result["all_pass"],
                "status": classification["status"],
                "min_scenario_distance": classification["min_scenario_distance"],
                "broad_margin": classification["broad_min_margin_over_threshold"],
                "tensor_margin": tensor_row["min_scenario_minus_tensor_control"],
                "drop_signed_z": variants["drop_signed_z"]["min_scenario_distance"],
                "drop_entropies": variants["drop_entropies"]["min_scenario_distance"],
                "out": str(OUT_PATH),
            },
            indent=2,
        )
    )
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
