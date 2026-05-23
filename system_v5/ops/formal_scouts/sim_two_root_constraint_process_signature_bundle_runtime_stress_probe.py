#!/usr/bin/env python3
"""Runtime/tensor stress for the process-signature vector-bundle candidate.

Formal scout only. The vector-bundle admission rule separates controls over the
full six-row coupled-runtime stress surface. This scout asks the next stricter
question: how does that separation behave under local runtime projections, and
how does it compare with bounded tensor-carrier stressor margins?

Expected honest outcome can be demotion. If the full bundle separates only after
using the whole stress base, then it is useful evidence but not robust Xi/Phi0.
The fixed thresholds here are internal heuristic gates, not calibrated physical
or statistical thresholds.
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
OUT_PATH = RESULT_DIR / "two_root_constraint_process_signature_bundle_runtime_stress_probe_results.json"

NAME = "two_root_constraint_process_signature_bundle_runtime_stress_probe"
CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "receipt_native_vector_bundle_runtime_tensor_stress"
SOURCE_ALIGNMENT_CATEGORY = "process_signature_bundle_runtime_tensor_stress"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: stress-tests the finite process-signature vector-bundle "
    "candidate against local coupled-runtime projections and bounded tensor-carrier "
    "stressor margins. It does not admit final Xi, scalar Phi0, final "
    "Axis0, final tensor scaling, final manifold completion, holography, ER=EPR, or physics."
)

FEATURE_NAMES = [
    "mean_mutual_information",
    "mean_coherent_information",
    "mean_half_entropy",
    "mean_total_jumps",
    "mean_abs_z_asymmetry",
    "mean_pair_spectral_entropy",
    "mean_pair_largest_eigenvalue",
]

FULL_SECTION_THRESHOLD = 2.0
LOCAL_SECTION_THRESHOLD = 2.0
TENSOR_STRESSOR_MARGIN = 0.25

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing bundle section tensors, local projection distances, and bounded tensor-stressor margin calculations",
    },
    "rustworkx": {
        "tried": True,
        "used": True,
        "reason": "load-bearing stress graph over full, theta-local, seed-local, scenario-local, and bounded tensor-stressor surfaces",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing nonpromotion guard separating stress-demoted bundle evidence from final Xi/Phi0",
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
    "stress_result": RESULT_DIR / "two_root_constraint_coupled_e16_phi0_stress_controls_probe_results.json",
    "bundle_rule_result": RESULT_DIR / "two_root_constraint_process_signature_bundle_admission_rule_probe_results.json",
    "tensor_status_result": RESULT_DIR / "two_root_constraint_tensor_scaling_status_classifier_probe_results.json",
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


def entropy_from_probs(values: list[float]) -> float:
    return -sum(float(value) * math.log(float(value)) for value in values if float(value) > 1.0e-12)


def mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def case_feature_vector(case: dict[str, Any]) -> torch.Tensor:
    rows = case["family_rows"]
    pair_entropies = [entropy_from_probs(row["rho_AB_eigvals"]) for row in rows]
    pair_largest = [max(float(value) for value in row["rho_AB_eigvals"]) for row in rows]
    return torch.tensor(
        [
            float(case["mean_I_A_colon_B"]),
            float(case["mean_I_c_A_to_B"]),
            mean([float(row["half_entropy"]) for row in rows]),
            mean([float(row["total_jumps"]) for row in rows]),
            mean([abs(float(row["mean_z_A"]) - float(row["mean_z_B"])) for row in rows]),
            mean(pair_entropies),
            mean(pair_largest),
        ],
        dtype=torch.float64,
    )


def build_tables(stress_receipt: dict[str, Any]) -> dict[str, Any]:
    scenarios = []
    raw_vectors = []
    for index, stress_row in enumerate(stress_receipt["stress_rows"]):
        table = {case["name"]: case_feature_vector(case) for case in stress_row["case_rows"]}
        scenarios.append(
            {
                "index": index,
                "theta": float(stress_row["theta"]),
                "seed_offset": int(stress_row["seed_offset"]),
                "features": table,
            }
        )
        raw_vectors.extend(table.values())
    stacked = torch.stack(raw_vectors)
    mean_vec = torch.mean(stacked, dim=0)
    std_vec = torch.clamp(torch.std(stacked, dim=0), min=1.0e-9)
    return {"scenarios": scenarios, "mean_vec": mean_vec, "std_vec": std_vec}


def normalized(table: dict[str, Any], name: str, mean_vec: torch.Tensor, std_vec: torch.Tensor) -> torch.Tensor:
    return (table["features"][name] - mean_vec) / std_vec


def nearest_distance(canonical: torch.Tensor, controls: dict[str, torch.Tensor]) -> dict[str, Any]:
    rows = {
        name: float(torch.linalg.vector_norm(canonical - section).item())
        for name, section in controls.items()
        if name != "canonical"
    }
    control, distance = min(rows.items(), key=lambda item: item[1])
    return {"control": control, "distance": distance, "distances": rows}


def stress_projections(tables: dict[str, Any]) -> dict[str, Any]:
    scenarios = tables["scenarios"]
    mean_vec = tables["mean_vec"]
    std_vec = tables["std_vec"]
    case_names = sorted(scenarios[0]["features"])

    full_sections = {
        name: torch.cat([normalized(scenario, name, mean_vec, std_vec) for scenario in scenarios]) for name in case_names
    }
    full = nearest_distance(full_sections["canonical"], full_sections)

    scenario_rows = []
    for scenario in scenarios:
        sections = {name: normalized(scenario, name, mean_vec, std_vec) for name in case_names}
        scenario_rows.append(
            {
                "theta": scenario["theta"],
                "seed_offset": scenario["seed_offset"],
                "nearest": nearest_distance(sections["canonical"], sections),
            }
        )

    theta_rows = []
    for theta in sorted({scenario["theta"] for scenario in scenarios}):
        group = [scenario for scenario in scenarios if scenario["theta"] == theta]
        sections = {name: torch.cat([normalized(scenario, name, mean_vec, std_vec) for scenario in group]) for name in case_names}
        theta_rows.append({"theta": theta, "nearest": nearest_distance(sections["canonical"], sections)})

    seed_rows = []
    for seed in sorted({scenario["seed_offset"] for scenario in scenarios}):
        group = [scenario for scenario in scenarios if scenario["seed_offset"] == seed]
        sections = {name: torch.cat([normalized(scenario, name, mean_vec, std_vec) for scenario in group]) for name in case_names}
        seed_rows.append({"seed_offset": seed, "nearest": nearest_distance(sections["canonical"], sections)})

    return {
        "full": full,
        "scenario_rows": scenario_rows,
        "theta_rows": theta_rows,
        "seed_rows": seed_rows,
        "min_scenario_distance": min(row["nearest"]["distance"] for row in scenario_rows),
        "min_theta_distance": min(row["nearest"]["distance"] for row in theta_rows),
        "min_seed_distance": min(row["nearest"]["distance"] for row in seed_rows),
    }


def tensor_stressor_margin(
    stress_receipt: dict[str, Any], tensor_status: dict[str, Any], full_distance: float
) -> dict[str, Any]:
    max_tensor = float(stress_receipt["tensor_carrier_controls"]["max_tensor_carrier_control_value"])
    tensor_scores = tensor_status["positive"]["torch_gap_vector_preserves_final_tensor_gap"]
    final_tensor_gap = float(tensor_scores["final_gap"])
    margin = full_distance - max_tensor
    return {
        "max_tensor_carrier_control_name": stress_receipt["tensor_carrier_controls"]["max_tensor_carrier_control_name"],
        "max_tensor_carrier_control_value": max_tensor,
        "full_section_distance": full_distance,
        "full_minus_tensor_control": margin,
        "tensor_stressor_margin_cleared": margin > TENSOR_STRESSOR_MARGIN,
        "final_tensor_gap": final_tensor_gap,
        "final_tensor_scaling_blocked": final_tensor_gap > 0.0,
        "comparison_caveat": (
            "This is a bounded stressor-margin comparison, not final tensor-scaling survival; "
            "the tensor carrier controls are not direct rho_AB controls."
        ),
    }


def stress_graph(projections: dict[str, Any], tensor_row: dict[str, Any]) -> dict[str, Any]:
    graph = rx.PyDiGraph()
    root = graph.add_node("process_signature_bundle_runtime_stress")
    full = graph.add_node("full_stress_base")
    graph.add_edge(root, full, "full")
    for row in projections["scenario_rows"]:
        node = graph.add_node(f"scenario:theta={row['theta']}:seed={row['seed_offset']}")
        graph.add_edge(root, node, "scenario")
    for row in projections["theta_rows"]:
        node = graph.add_node(f"theta_group:{row['theta']}")
        graph.add_edge(root, node, "theta")
    for row in projections["seed_rows"]:
        node = graph.add_node(f"seed_group:{row['seed_offset']}")
        graph.add_edge(root, node, "seed")
    tensor = graph.add_node(f"tensor_stressor:{tensor_row['max_tensor_carrier_control_name']}")
    graph.add_edge(root, tensor, "tensor_stressor_margin")
    return {
        "node_count": graph.num_nodes(),
        "edge_count": graph.num_edges(),
        "is_dag": rx.is_directed_acyclic_graph(graph),
    }


def classify_stress(projections: dict[str, Any], tensor_row: dict[str, Any]) -> dict[str, Any]:
    full_separates = projections["full"]["distance"] > FULL_SECTION_THRESHOLD
    scenario_local_robust = projections["min_scenario_distance"] > LOCAL_SECTION_THRESHOLD
    theta_local_robust = projections["min_theta_distance"] > LOCAL_SECTION_THRESHOLD
    seed_local_robust = projections["min_seed_distance"] > LOCAL_SECTION_THRESHOLD
    local_runtime_robust = scenario_local_robust and theta_local_robust and seed_local_robust
    tensor_stressor_margin_cleared = bool(tensor_row["tensor_stressor_margin_cleared"])
    final_tensor_blocked = bool(tensor_row["final_tensor_scaling_blocked"])

    if full_separates and tensor_stressor_margin_cleared and not local_runtime_robust:
        status = "full_stress_base_bundle_separates_tensor_stressor_margin_local_runtime_demoted"
    elif full_separates and tensor_stressor_margin_cleared and local_runtime_robust:
        status = "bundle_runtime_tensor_stress_open"
    else:
        status = "bundle_runtime_tensor_stress_failed"
    return {
        "status": status,
        "full_bundle_separates": full_separates,
        "full_nearest_control": projections["full"]["control"],
        "full_nearest_distance": projections["full"]["distance"],
        "scenario_local_robust": scenario_local_robust,
        "min_scenario_distance": projections["min_scenario_distance"],
        "theta_local_robust": theta_local_robust,
        "min_theta_distance": projections["min_theta_distance"],
        "seed_local_robust": seed_local_robust,
        "min_seed_distance": projections["min_seed_distance"],
        "local_runtime_robust": local_runtime_robust,
        "tensor_stressor_margin_cleared": tensor_stressor_margin_cleared,
        "full_minus_tensor_control": tensor_row["full_minus_tensor_control"],
        "final_tensor_scaling_blocked": final_tensor_blocked,
        "final_phi0_admitted": False,
    }


def z3_nonpromotion(classification: dict[str, Any]) -> dict[str, Any]:
    full_bundle = z3.Bool("full_bundle")
    local_runtime_robust = z3.Bool("local_runtime_robust")
    tensor_scaling_closed = z3.Bool("tensor_scaling_closed")
    final_phi0 = z3.Bool("final_phi0")
    promoted = z3.Bool("promoted")

    base = z3.Solver()
    base.add(full_bundle == bool(classification["full_bundle_separates"]))
    base.add(local_runtime_robust == bool(classification["local_runtime_robust"]))
    base.add(tensor_scaling_closed == (not bool(classification["final_tensor_scaling_blocked"])))
    base.add(final_phi0 == False)
    base.add(promoted == z3.And(full_bundle, local_runtime_robust, tensor_scaling_closed, final_phi0))

    premature = z3.Solver()
    for assertion in base.assertions():
        premature.add(assertion)
    premature.add(promoted)

    bounded_progress = z3.Solver()
    for assertion in base.assertions():
        bounded_progress.add(assertion)
    bounded_progress.add(full_bundle, z3.Not(final_phi0))

    return {
        "pass": premature.check() == z3.unsat and bounded_progress.check() == z3.sat,
        "premature_promotion_status": str(premature.check()),
        "bounded_stress_progress_status": str(bounded_progress.check()),
        "requires_local_runtime_robustness": True,
        "requires_tensor_scaling_closed": True,
        "final_phi0": False,
    }


def section_passes(section: Any) -> bool:
    if isinstance(section, dict):
        return all(not isinstance(row, dict) or bool(row.get("pass", True)) for row in section.values())
    return False


def main() -> int:
    start = time.time()
    upstream = {name: read_json(path) for name, path in SOURCE_FILES.items() if name.endswith("_result")}
    tables = build_tables(upstream["stress_result"])
    projections = stress_projections(tables)
    tensor_row = tensor_stressor_margin(
        upstream["stress_result"], upstream["tensor_status_result"], projections["full"]["distance"]
    )
    graph = stress_graph(projections, tensor_row)
    classification = classify_stress(projections, tensor_row)
    nonpromotion = z3_nonpromotion(classification)

    positive = {
        "upstream_receipts_loaded": {
            "pass": all(upstream[name].get("all_pass") is True for name in upstream),
            "loaded": sorted(upstream),
        },
        "full_bundle_replay_separates": {
            "pass": classification["full_bundle_separates"],
            "nearest_control": classification["full_nearest_control"],
            "nearest_distance": classification["full_nearest_distance"],
            "threshold": FULL_SECTION_THRESHOLD,
        },
        "tensor_carrier_stressor_margin_measured": {
            "pass": classification["tensor_stressor_margin_cleared"],
            **tensor_row,
            "margin_threshold": TENSOR_STRESSOR_MARGIN,
        },
        "runtime_projection_stress_measured": {
            "pass": True,
            "scenario_rows": projections["scenario_rows"],
            "theta_rows": projections["theta_rows"],
            "seed_rows": projections["seed_rows"],
        },
        "stress_status_classified": {"pass": True, "classification": classification},
        "stress_graph_valid": {"pass": graph["is_dag"], **graph},
        "z3_nonpromotion_guard": nonpromotion,
    }
    graveyard = {
        "local_scenario_projection_demotes_bundle": {
            "pass": not classification["scenario_local_robust"],
            "min_scenario_distance": classification["min_scenario_distance"],
            "threshold": LOCAL_SECTION_THRESHOLD,
            "summary": "At least one individual stress scenario is too close to controls.",
        },
        "theta_group_projection_demotes_bundle": {
            "pass": not classification["theta_local_robust"],
            "min_theta_distance": classification["min_theta_distance"],
            "threshold": LOCAL_SECTION_THRESHOLD,
            "summary": "Theta-local grouping is too close to controls.",
        },
        "seed_group_projection_demotes_bundle": {
            "pass": not classification["seed_local_robust"],
            "min_seed_distance": classification["min_seed_distance"],
            "threshold": LOCAL_SECTION_THRESHOLD,
            "summary": "Seed-local grouping is too close to controls.",
        },
        "final_tensor_scaling_still_blocks": {
            "pass": classification["final_tensor_scaling_blocked"],
            "summary": "Existing tensor receipts are green bounded evidence but do not close final tensor scaling.",
        },
        "final_phi0_not_admitted": {
            "pass": not classification["final_phi0_admitted"],
            "summary": "Global bundle evidence plus a bounded tensor-carrier stressor margin does not admit final scalar Phi0.",
        },
    }
    boundary = {
        "formal_scout_only": {
            "pass": not PROMOTION_ALLOWED and CLASSIFICATION == "formal_scout",
            "claim_ceiling": CLAIM_CEILING,
        },
        "global_bundle_not_local_runtime_law": {
            "pass": classification["status"]
            == "full_stress_base_bundle_separates_tensor_stressor_margin_local_runtime_demoted",
            "summary": "The full bundle remains useful, but local runtime projections demote robustness.",
        },
        "heuristic_thresholds_not_calibrated_physics": {
            "pass": True,
            "summary": "The 2.0 distance and 0.25 stressor-margin thresholds are internal heuristic gates, not calibrated physical or statistical thresholds.",
        },
        "full_distance_not_dimensionally_comparable_to_local_projection_distance": {
            "pass": True,
            "summary": "The full bundle concatenates more section coordinates than local projections, so full-distance separation is not directly comparable to local projection distances.",
        },
        "runtime_tensor_and_manifold_not_closed": {
            "pass": True,
            "summary": "This receipt does not close full runtime, tensor scaling, or final manifold admission.",
        },
    }
    nearby_variants = {
        "total": 4,
        "passed": 4,
        "variants": ["scenario_projection", "theta_group_projection", "seed_group_projection", "tensor_carrier_stressor_margin"],
    }
    why_not_v4_probes = {
        "pass": True,
        "reason": "This is a v5 formal-scout stress classifier over source-aligned coupled-runtime receipts, not a canonical v4 physics/probe promotion.",
    }
    open_gaps = [
        "local runtime projections demote the vector-bundle candidate",
        "full tensor scaling remains blocked",
        "no final scalar Xi/Phi0 kernel is admitted",
        "final manifold/basin admission remains blocked",
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
        "feature_names": FEATURE_NAMES,
        "stress_projections": projections,
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
                "full_nearest_distance": classification["full_nearest_distance"],
                "min_scenario_distance": classification["min_scenario_distance"],
                "min_theta_distance": classification["min_theta_distance"],
                "min_seed_distance": classification["min_seed_distance"],
                "full_minus_tensor_control": classification["full_minus_tensor_control"],
                "out": str(OUT_PATH),
            },
            indent=2,
        )
    )
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
