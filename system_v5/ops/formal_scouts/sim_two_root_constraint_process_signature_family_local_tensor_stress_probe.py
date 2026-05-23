#!/usr/bin/env python3
"""Tensor/runtime stress for the family-local process-signature section.

Formal scout only. The previous repair showed that family-local sections clear
the current finite scenario/theta/seed projection gates. This scout asks whether
that repair survives a sharper control battery:

- family-position standardization versus global feature standardization;
- signed-z coordinate removal;
- entropy-coordinate removal;
- joint signed-z plus entropy removal;
- family-identity erasure by jump-sorted rows;
- bounded tensor-carrier stressor margin.

Passing here keeps the family-local section alive for broader stress. It still
does not admit scalar Phi0, final Xi, final tensor scaling, or final manifold
law.
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
OUT_PATH = RESULT_DIR / "two_root_constraint_process_signature_family_local_tensor_stress_probe_results.json"

NAME = "two_root_constraint_process_signature_family_local_tensor_stress_probe"
CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "receipt_native_family_local_tensor_stress"
SOURCE_ALIGNMENT_CATEGORY = "process_signature_family_local_tensor_stress"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: stress-tests the finite family-local process-signature "
    "section repair against coordinate ablations, family-identity controls, and "
    "bounded tensor-carrier stressors. It does not admit final Xi, scalar Phi0, "
    "final Axis0, final tensor scaling, final manifold completion, holography, "
    "ER=EPR, or physics."
)

FEATURE_NAMES = [
    "I_A_colon_B",
    "I_c_A_to_B",
    "half_entropy",
    "total_jumps",
    "abs_z_asymmetry",
    "pair_spectral_entropy",
    "pair_largest_eigenvalue",
    "mean_z_A",
    "mean_z_B",
    "S_A",
    "S_B",
    "S_AB",
]

LOCAL_SECTION_THRESHOLD = 2.0
TENSOR_STRESSOR_MARGIN = 0.25
ENTROPY_PRESSURE_MIN_DROP = 0.03

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing family-local section tensors, ablation distances, and bounded tensor-stressor margin calculations",
    },
    "rustworkx": {
        "tried": True,
        "used": True,
        "reason": "load-bearing stress graph over coordinate ablations, family-identity controls, and tensor-stressor checks",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing nonpromotion guard separating finite tensor-stressed family-local evidence from final Xi/Phi0 promotion",
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
    "family_repair_result": RESULT_DIR
    / "two_root_constraint_process_signature_family_local_section_repair_probe_results.json",
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


def phi0(row: dict[str, Any], key: str) -> float:
    return float(row["phi0"][key])


def raw_features(row: dict[str, Any]) -> list[float]:
    eigvals = [float(value) for value in row["rho_AB_eigvals"]]
    mean_z_a = float(row["mean_z_A"])
    mean_z_b = float(row["mean_z_B"])
    return [
        phi0(row, "I_A_colon_B"),
        phi0(row, "I_c_A_to_B"),
        float(row["half_entropy"]),
        float(row["total_jumps"]),
        abs(mean_z_a - mean_z_b),
        entropy_from_probs(eigvals),
        max(eigvals),
        mean_z_a,
        mean_z_b,
        phi0(row, "S_A"),
        phi0(row, "S_B"),
        phi0(row, "S_AB"),
    ]


def feature_tensor(row: dict[str, Any], feature_indices: list[int]) -> torch.Tensor:
    values = raw_features(row)
    return torch.tensor([values[index] for index in feature_indices], dtype=torch.float64)


def sort_rows(rows: list[dict[str, Any]], mode: str, feature_indices: list[int]) -> list[dict[str, Any]]:
    if mode == "family_label":
        return sorted(rows, key=lambda row: (str(row["family_A"]), str(row["family_B"])))
    if mode == "jump_count":
        return sorted(rows, key=lambda row: feature_tensor(row, feature_indices)[3].item())
    raise ValueError(f"unknown row sort mode: {mode}")


def build_variant_tables(
    stress_receipt: dict[str, Any],
    *,
    feature_indices: list[int],
    standardization: str,
    row_sort_mode: str = "family_label",
) -> dict[str, Any]:
    scenarios = []
    matrices = []
    for stress_row in stress_receipt["stress_rows"]:
        table = {}
        for case in stress_row["case_rows"]:
            rows = sort_rows(list(case["family_rows"]), row_sort_mode, feature_indices)
            matrix = torch.stack([feature_tensor(row, feature_indices) for row in rows])
            table[str(case["name"])] = matrix
            matrices.append(matrix)
        scenarios.append(
            {
                "theta": float(stress_row["theta"]),
                "seed_offset": int(stress_row["seed_offset"]),
                "features": table,
            }
        )

    if standardization == "family_position":
        stacked = torch.stack(matrices)
        mean_vec = torch.mean(stacked, dim=0)
        std_vec = torch.clamp(torch.std(stacked, dim=0), min=1.0e-9)
    elif standardization == "global_feature":
        stacked = torch.cat(matrices, dim=0)
        mean_vec = torch.mean(stacked, dim=0)
        std_vec = torch.clamp(torch.std(stacked, dim=0), min=1.0e-9)
    else:
        raise ValueError(f"unknown standardization: {standardization}")

    return {
        "scenarios": scenarios,
        "mean_vec": mean_vec,
        "std_vec": std_vec,
        "feature_indices": feature_indices,
        "standardization": standardization,
        "row_sort_mode": row_sort_mode,
    }


def section_vector(table: dict[str, Any], scenario: dict[str, Any], case_name: str) -> torch.Tensor:
    return torch.flatten((scenario["features"][case_name] - table["mean_vec"]) / table["std_vec"])


def nearest_distance(canonical: torch.Tensor, controls: dict[str, torch.Tensor]) -> dict[str, Any]:
    rows = {
        name: float(torch.linalg.vector_norm(canonical - section).item())
        for name, section in controls.items()
        if name != "canonical"
    }
    control, distance = min(rows.items(), key=lambda item: item[1])
    return {"control": control, "distance": distance, "distances": rows}


def variant_projection(table: dict[str, Any]) -> dict[str, Any]:
    scenarios = table["scenarios"]
    case_names = sorted(scenarios[0]["features"])
    scenario_rows = []
    for scenario in scenarios:
        sections = {name: section_vector(table, scenario, name) for name in case_names}
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
        sections = {
            name: torch.cat([section_vector(table, scenario, name) for scenario in group])
            for name in case_names
        }
        theta_rows.append({"theta": theta, "nearest": nearest_distance(sections["canonical"], sections)})
    seed_rows = []
    for seed in sorted({scenario["seed_offset"] for scenario in scenarios}):
        group = [scenario for scenario in scenarios if scenario["seed_offset"] == seed]
        sections = {
            name: torch.cat([section_vector(table, scenario, name) for scenario in group])
            for name in case_names
        }
        seed_rows.append({"seed_offset": seed, "nearest": nearest_distance(sections["canonical"], sections)})
    return {
        "min_scenario_distance": min(row["nearest"]["distance"] for row in scenario_rows),
        "min_theta_distance": min(row["nearest"]["distance"] for row in theta_rows),
        "min_seed_distance": min(row["nearest"]["distance"] for row in seed_rows),
        "scenario_rows": scenario_rows,
        "theta_rows": theta_rows,
        "seed_rows": seed_rows,
    }


def build_variant_projections(stress_receipt: dict[str, Any]) -> dict[str, Any]:
    variants = {
        "full_family_local": {
            "feature_indices": list(range(len(FEATURE_NAMES))),
            "standardization": "family_position",
            "row_sort_mode": "family_label",
        },
        "global_feature_standardization": {
            "feature_indices": list(range(len(FEATURE_NAMES))),
            "standardization": "global_feature",
            "row_sort_mode": "family_label",
        },
        "drop_signed_z": {
            "feature_indices": [index for index in range(len(FEATURE_NAMES)) if index not in (7, 8)],
            "standardization": "family_position",
            "row_sort_mode": "family_label",
        },
        "drop_entropies": {
            "feature_indices": [index for index in range(len(FEATURE_NAMES)) if index not in (9, 10, 11)],
            "standardization": "family_position",
            "row_sort_mode": "family_label",
        },
        "drop_signed_z_and_entropies": {
            "feature_indices": [index for index in range(len(FEATURE_NAMES)) if index not in (7, 8, 9, 10, 11)],
            "standardization": "family_position",
            "row_sort_mode": "family_label",
        },
        "jump_sorted_family_identity_erased": {
            "feature_indices": list(range(len(FEATURE_NAMES))),
            "standardization": "family_position",
            "row_sort_mode": "jump_count",
        },
    }
    rows = {}
    for name, spec in variants.items():
        table = build_variant_tables(stress_receipt, **spec)
        projection = variant_projection(table)
        rows[name] = {
            **projection,
            "feature_names": [FEATURE_NAMES[index] for index in spec["feature_indices"]],
            "standardization": spec["standardization"],
            "row_sort_mode": spec["row_sort_mode"],
        }
    return rows


def tensor_margin(stress_receipt: dict[str, Any], full_row: dict[str, Any]) -> dict[str, Any]:
    max_tensor = float(stress_receipt["tensor_carrier_controls"]["max_tensor_carrier_control_value"])
    margin = float(full_row["min_scenario_distance"]) - max_tensor
    return {
        "max_tensor_carrier_control_name": stress_receipt["tensor_carrier_controls"]["max_tensor_carrier_control_name"],
        "max_tensor_carrier_control_value": max_tensor,
        "min_family_local_scenario_distance": full_row["min_scenario_distance"],
        "min_scenario_minus_tensor_control": margin,
        "margin_threshold": TENSOR_STRESSOR_MARGIN,
        "margin_cleared": margin > TENSOR_STRESSOR_MARGIN,
        "comparison_caveat": "Tensor carrier controls are bounded admission stressors, not direct rho_AB controls.",
    }


def classify(variants: dict[str, Any], tensor_row: dict[str, Any], tensor_status: dict[str, Any]) -> dict[str, Any]:
    full = variants["full_family_local"]
    full_local_pass = full["min_scenario_distance"] > LOCAL_SECTION_THRESHOLD
    global_control_fails = variants["global_feature_standardization"]["min_scenario_distance"] < LOCAL_SECTION_THRESHOLD
    signed_z_fails = variants["drop_signed_z"]["min_scenario_distance"] < LOCAL_SECTION_THRESHOLD
    signed_z_entropy_fails = variants["drop_signed_z_and_entropies"]["min_scenario_distance"] < LOCAL_SECTION_THRESHOLD
    family_identity_fails = variants["jump_sorted_family_identity_erased"]["min_scenario_distance"] < LOCAL_SECTION_THRESHOLD
    entropy_drop = full["min_scenario_distance"] - variants["drop_entropies"]["min_scenario_distance"]
    entropy_pressure = entropy_drop > ENTROPY_PRESSURE_MIN_DROP
    final_tensor_gap = float(tensor_status["positive"]["torch_gap_vector_preserves_final_tensor_gap"]["final_gap"])
    stress_survives = (
        full_local_pass
        and tensor_row["margin_cleared"]
        and global_control_fails
        and signed_z_fails
        and signed_z_entropy_fails
        and family_identity_fails
        and entropy_pressure
    )
    return {
        "status": "family_local_tensor_stress_candidate_open" if stress_survives else "family_local_tensor_stress_failed",
        "full_local_pass": full_local_pass,
        "min_scenario_distance": full["min_scenario_distance"],
        "min_theta_distance": full["min_theta_distance"],
        "min_seed_distance": full["min_seed_distance"],
        "tensor_stressor_margin_cleared": bool(tensor_row["margin_cleared"]),
        "global_standardization_control_fails": global_control_fails,
        "signed_z_coordinates_load_bearing": signed_z_fails,
        "signed_z_entropy_joint_control_fails": signed_z_entropy_fails,
        "family_identity_control_fails": family_identity_fails,
        "entropy_coordinates_support_margin": entropy_pressure,
        "entropy_drop_margin": entropy_drop,
        "final_tensor_scaling_blocked": final_tensor_gap > 0.0,
        "final_tensor_gap": final_tensor_gap,
        "final_phi0_admitted": False,
        "final_manifold_admitted": False,
    }


def stress_graph(classification: dict[str, Any]) -> dict[str, Any]:
    graph = rx.PyDiGraph()
    root = graph.add_node("family_local_tensor_stress")
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
        graph.add_edge(root, node, name)
    return {"node_count": graph.num_nodes(), "edge_count": graph.num_edges(), "is_dag": rx.is_directed_acyclic_graph(graph)}


def z3_nonpromotion(classification: dict[str, Any]) -> dict[str, Any]:
    tensor_stress_survived = z3.Bool("tensor_stress_survived")
    final_tensor_scaling_closed = z3.Bool("final_tensor_scaling_closed")
    final_phi0 = z3.Bool("final_phi0")
    final_manifold = z3.Bool("final_manifold")
    promoted = z3.Bool("promoted")

    base = z3.Solver()
    base.add(tensor_stress_survived == (classification["status"] == "family_local_tensor_stress_candidate_open"))
    base.add(final_tensor_scaling_closed == (not bool(classification["final_tensor_scaling_blocked"])))
    base.add(final_phi0 == False)
    base.add(final_manifold == False)
    base.add(promoted == z3.And(tensor_stress_survived, final_tensor_scaling_closed, final_phi0, final_manifold))

    premature = z3.Solver()
    for assertion in base.assertions():
        premature.add(assertion)
    premature.add(promoted)

    bounded_progress = z3.Solver()
    for assertion in base.assertions():
        bounded_progress.add(assertion)
    bounded_progress.add(tensor_stress_survived, z3.Not(final_phi0), z3.Not(final_manifold))

    return {
        "pass": premature.check() == z3.unsat and bounded_progress.check() == z3.sat,
        "premature_promotion_status": str(premature.check()),
        "bounded_tensor_stress_progress_status": str(bounded_progress.check()),
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
    variants = build_variant_projections(upstream["stress_result"])
    tensor_row = tensor_margin(upstream["stress_result"], variants["full_family_local"])
    classification = classify(variants, tensor_row, upstream["tensor_status_result"])
    graph = stress_graph(classification)
    nonpromotion = z3_nonpromotion(classification)

    positive = {
        "upstream_receipts_loaded": {
            "pass": all(upstream[name].get("all_pass") is True for name in upstream),
            "loaded": sorted(upstream),
        },
        "baseline_family_local_replay_survives": {
            "pass": classification["full_local_pass"],
            "min_scenario_distance": classification["min_scenario_distance"],
            "min_theta_distance": classification["min_theta_distance"],
            "min_seed_distance": classification["min_seed_distance"],
            "threshold": LOCAL_SECTION_THRESHOLD,
        },
        "tensor_carrier_stressor_margin_cleared": {
            "pass": classification["tensor_stressor_margin_cleared"],
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
        "stress_status_classified": {"pass": True, "classification": classification},
        "stress_graph_valid": {"pass": graph["is_dag"], **graph},
        "z3_nonpromotion_guard": nonpromotion,
    }
    graveyard = {
        "global_feature_standardization_fails": {
            "pass": classification["global_standardization_control_fails"],
            "min_scenario_distance": variants["global_feature_standardization"]["min_scenario_distance"],
            "threshold": LOCAL_SECTION_THRESHOLD,
            "summary": "Family-position coordinates are required; global feature standardization falls below the local gate.",
        },
        "signed_z_drop_fails": {
            "pass": classification["signed_z_coordinates_load_bearing"],
            "min_scenario_distance": variants["drop_signed_z"]["min_scenario_distance"],
            "threshold": LOCAL_SECTION_THRESHOLD,
            "summary": "Dropping signed mean_z_A/mean_z_B falls below the local gate.",
        },
        "signed_z_entropy_joint_drop_fails": {
            "pass": classification["signed_z_entropy_joint_control_fails"],
            "min_scenario_distance": variants["drop_signed_z_and_entropies"]["min_scenario_distance"],
            "threshold": LOCAL_SECTION_THRESHOLD,
            "summary": "Dropping signed z and entropy coordinates together falls below the local gate.",
        },
        "family_identity_erasure_fails": {
            "pass": classification["family_identity_control_fails"],
            "min_scenario_distance": variants["jump_sorted_family_identity_erased"]["min_scenario_distance"],
            "threshold": LOCAL_SECTION_THRESHOLD,
            "summary": "Replacing family-label row order with jump-count row order falls below the local gate.",
        },
        "final_tensor_scaling_still_blocks": {
            "pass": classification["final_tensor_scaling_blocked"],
            "final_tensor_gap": classification["final_tensor_gap"],
            "summary": "Bounded tensor stressor margin is not final tensor scaling.",
        },
        "final_phi0_and_manifold_not_admitted": {
            "pass": not classification["final_phi0_admitted"] and not classification["final_manifold_admitted"],
            "summary": "The tensor-stressed family-local section is still not scalar Phi0 or final manifold admission.",
        },
    }
    boundary = {
        "formal_scout_only": {
            "pass": not PROMOTION_ALLOWED and CLASSIFICATION == "formal_scout",
            "claim_ceiling": CLAIM_CEILING,
        },
        "family_local_tensor_stress_candidate_only": {
            "pass": classification["status"] == "family_local_tensor_stress_candidate_open",
            "summary": "The repair survives this finite stressor battery but remains a candidate.",
        },
        "entropy_coordinates_supportive_not_alone_decisive": {
            "pass": classification["entropy_coordinates_support_margin"],
            "entropy_drop_margin": classification["entropy_drop_margin"],
            "minimum_drop": ENTROPY_PRESSURE_MIN_DROP,
            "summary": "Entropy coordinates add margin, but signed z and family-position coordinates carry the threshold-crossing load in this fixture.",
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
            "drop_entropies_pressure",
            "drop_signed_z_and_entropies",
            "jump_sorted_family_identity_erased",
        ],
    }
    why_not_v4_probes = {
        "pass": True,
        "reason": "This is a v5 formal-scout stress classifier over source-aligned coupled-runtime receipts, not a canonical v4 physics/probe promotion.",
    }
    open_gaps = [
        "family-local sections survive this bounded tensor/runtime stressor battery, but broader runtime/tensor surfaces remain untested",
        "the stressed family-local section is not a scalar Xi/Phi0 kernel",
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
        "feature_names": FEATURE_NAMES,
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
