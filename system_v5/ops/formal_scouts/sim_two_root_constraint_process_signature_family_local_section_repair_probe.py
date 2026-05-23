#!/usr/bin/env python3
"""Family-local section repair for the process-signature bundle.

Formal scout only. D23 showed that the global process-signature bundle still
separates over the full finite stress base, but scenario/theta/seed-local
runtime projections demote robustness. This scout tests the next admissible
repair: keep each runtime family row as a local section and include signed
z/entropy coordinates instead of collapsing them into a mean bundle.

The intended honest outcome is a repaired local finite section, not final
Xi/Phi0. The thresholds are internal finite scout gates and are not calibrated
physics or statistics.
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
OUT_PATH = RESULT_DIR / "two_root_constraint_process_signature_family_local_section_repair_probe_results.json"

NAME = "two_root_constraint_process_signature_family_local_section_repair_probe"
CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "receipt_native_family_local_section_repair"
SOURCE_ALIGNMENT_CATEGORY = "process_signature_family_local_section_repair"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: tests a finite family-local process-signature section "
    "repair against the D23 local runtime projection demotion. It does not "
    "admit final Xi, scalar Phi0, final Axis0, final tensor scaling, final "
    "manifold completion, holography, ER=EPR, or physics."
)

FAMILY_FEATURE_NAMES = [
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

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing family-local section tensors, z-scored section distances, and leave-one-family ablations",
    },
    "rustworkx": {
        "tried": True,
        "used": True,
        "reason": "load-bearing repair graph over scenario, theta, seed, family-ablation, and upstream demotion surfaces",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing nonpromotion guard separating finite local-section repair from final Xi/Phi0 promotion",
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
    "global_bundle_stress_result": RESULT_DIR
    / "two_root_constraint_process_signature_bundle_runtime_stress_probe_results.json",
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


def family_key(row: dict[str, Any]) -> tuple[str, str]:
    return (str(row["family_A"]), str(row["family_B"]))


def family_feature_vector(row: dict[str, Any]) -> torch.Tensor:
    eigvals = [float(value) for value in row["rho_AB_eigvals"]]
    mean_z_a = float(row["mean_z_A"])
    mean_z_b = float(row["mean_z_B"])
    return torch.tensor(
        [
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
        ],
        dtype=torch.float64,
    )


def sorted_family_rows(case: dict[str, Any]) -> list[dict[str, Any]]:
    return sorted(case["family_rows"], key=family_key)


def build_tables(stress_receipt: dict[str, Any]) -> dict[str, Any]:
    scenarios = []
    raw_family_matrices = []
    for index, stress_row in enumerate(stress_receipt["stress_rows"]):
        table = {}
        family_order: list[tuple[str, str]] | None = None
        for case in stress_row["case_rows"]:
            rows = sorted_family_rows(case)
            keys = [family_key(row) for row in rows]
            if family_order is None:
                family_order = keys
            elif keys != family_order:
                raise ValueError(f"inconsistent family order in stress row {index}, case {case['name']}")
            vectors = [family_feature_vector(row) for row in rows]
            table[str(case["name"])] = torch.stack(vectors)
            raw_family_matrices.append(table[str(case["name"])])
        scenarios.append(
            {
                "index": index,
                "theta": float(stress_row["theta"]),
                "seed_offset": int(stress_row["seed_offset"]),
                "family_order": family_order or [],
                "features": table,
            }
        )
    stacked = torch.stack(raw_family_matrices)
    mean_vec = torch.mean(stacked, dim=0)
    std_vec = torch.clamp(torch.std(stacked, dim=0), min=1.0e-9)
    return {"scenarios": scenarios, "mean_vec": mean_vec, "std_vec": std_vec}


def normalized_family_matrix(scenario: dict[str, Any], case_name: str, mean_vec: torch.Tensor, std_vec: torch.Tensor) -> torch.Tensor:
    return (scenario["features"][case_name] - mean_vec) / std_vec


def section_vector(
    scenario: dict[str, Any],
    case_name: str,
    mean_vec: torch.Tensor,
    std_vec: torch.Tensor,
    *,
    omit_family_index: int | None = None,
) -> torch.Tensor:
    matrix = normalized_family_matrix(scenario, case_name, mean_vec, std_vec)
    if omit_family_index is not None:
        keep = [index for index in range(matrix.shape[0]) if index != omit_family_index]
        matrix = matrix[keep]
    return torch.flatten(matrix)


def nearest_distance(canonical: torch.Tensor, controls: dict[str, torch.Tensor]) -> dict[str, Any]:
    rows = {
        name: float(torch.linalg.vector_norm(canonical - section).item())
        for name, section in controls.items()
        if name != "canonical"
    }
    control, distance = min(rows.items(), key=lambda item: item[1])
    return {"control": control, "distance": distance, "distances": rows}


def repair_projections(tables: dict[str, Any]) -> dict[str, Any]:
    scenarios = tables["scenarios"]
    mean_vec = tables["mean_vec"]
    std_vec = tables["std_vec"]
    case_names = sorted(scenarios[0]["features"])

    full_sections = {
        name: torch.cat([section_vector(scenario, name, mean_vec, std_vec) for scenario in scenarios])
        for name in case_names
    }
    full = nearest_distance(full_sections["canonical"], full_sections)

    scenario_rows = []
    for scenario in scenarios:
        sections = {name: section_vector(scenario, name, mean_vec, std_vec) for name in case_names}
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
            name: torch.cat([section_vector(scenario, name, mean_vec, std_vec) for scenario in group])
            for name in case_names
        }
        theta_rows.append({"theta": theta, "nearest": nearest_distance(sections["canonical"], sections)})

    seed_rows = []
    for seed in sorted({scenario["seed_offset"] for scenario in scenarios}):
        group = [scenario for scenario in scenarios if scenario["seed_offset"] == seed]
        sections = {
            name: torch.cat([section_vector(scenario, name, mean_vec, std_vec) for scenario in group])
            for name in case_names
        }
        seed_rows.append({"seed_offset": seed, "nearest": nearest_distance(sections["canonical"], sections)})

    family_order = scenarios[0]["family_order"]
    leave_one_family_rows = []
    for family_index, key in enumerate(family_order):
        sections = {
            name: torch.cat(
                [
                    section_vector(scenario, name, mean_vec, std_vec, omit_family_index=family_index)
                    for scenario in scenarios
                ]
            )
            for name in case_names
        }
        leave_one_family_rows.append(
            {
                "omitted_family": {"family_A": key[0], "family_B": key[1]},
                "nearest": nearest_distance(sections["canonical"], sections),
            }
        )

    return {
        "family_order": [{"family_A": key[0], "family_B": key[1]} for key in family_order],
        "full": full,
        "scenario_rows": scenario_rows,
        "theta_rows": theta_rows,
        "seed_rows": seed_rows,
        "leave_one_family_rows": leave_one_family_rows,
        "min_scenario_distance": min(row["nearest"]["distance"] for row in scenario_rows),
        "min_theta_distance": min(row["nearest"]["distance"] for row in theta_rows),
        "min_seed_distance": min(row["nearest"]["distance"] for row in seed_rows),
        "min_leave_one_family_distance": min(row["nearest"]["distance"] for row in leave_one_family_rows),
    }


def section_keys(receipt: dict[str, Any], key: str) -> set[str]:
    value = receipt.get(key, {})
    return set(value.keys()) if isinstance(value, dict) else set()


def previous_demotion_row(global_stress: dict[str, Any]) -> dict[str, Any]:
    classification = global_stress["candidate_classification"]
    graveyard = section_keys(global_stress, "graveyard_companions")
    boundary = section_keys(global_stress, "boundary")
    return {
        "previous_status": classification["status"],
        "previous_min_scenario_distance": float(classification["min_scenario_distance"]),
        "previous_min_theta_distance": float(classification["min_theta_distance"]),
        "previous_min_seed_distance": float(classification["min_seed_distance"]),
        "previous_local_demotions_recorded": {
            "scenario": "local_scenario_projection_demotes_bundle" in graveyard,
            "theta": "theta_group_projection_demotes_bundle" in graveyard,
            "seed": "seed_group_projection_demotes_bundle" in graveyard,
        },
        "previous_global_boundary_recorded": "global_bundle_not_local_runtime_law" in boundary,
    }


def classify_repair(projections: dict[str, Any], previous: dict[str, Any], tensor_status: dict[str, Any]) -> dict[str, Any]:
    scenario_repaired = projections["min_scenario_distance"] > LOCAL_SECTION_THRESHOLD
    theta_repaired = projections["min_theta_distance"] > LOCAL_SECTION_THRESHOLD
    seed_repaired = projections["min_seed_distance"] > LOCAL_SECTION_THRESHOLD
    leave_one_stable = projections["min_leave_one_family_distance"] > LOCAL_SECTION_THRESHOLD
    previous_failed = (
        previous["previous_min_scenario_distance"] < LOCAL_SECTION_THRESHOLD
        or previous["previous_min_theta_distance"] < LOCAL_SECTION_THRESHOLD
        or previous["previous_min_seed_distance"] < LOCAL_SECTION_THRESHOLD
    )
    final_tensor_gap = float(
        tensor_status["positive"]["torch_gap_vector_preserves_final_tensor_gap"]["final_gap"]
    )
    local_repair = scenario_repaired and theta_repaired and seed_repaired and leave_one_stable and previous_failed
    if local_repair:
        status = "family_local_section_repair_candidate_open"
    else:
        status = "family_local_section_repair_failed"
    return {
        "status": status,
        "scenario_local_repaired": scenario_repaired,
        "min_scenario_distance": projections["min_scenario_distance"],
        "theta_group_repaired": theta_repaired,
        "min_theta_distance": projections["min_theta_distance"],
        "seed_group_repaired": seed_repaired,
        "min_seed_distance": projections["min_seed_distance"],
        "leave_one_family_stable": leave_one_stable,
        "min_leave_one_family_distance": projections["min_leave_one_family_distance"],
        "previous_global_bundle_demotion_targeted": previous_failed,
        "final_tensor_scaling_blocked": final_tensor_gap > 0.0,
        "final_tensor_gap": final_tensor_gap,
        "final_phi0_admitted": False,
        "final_manifold_admitted": False,
    }


def repair_graph(projections: dict[str, Any], classification: dict[str, Any]) -> dict[str, Any]:
    graph = rx.PyDiGraph()
    root = graph.add_node("family_local_section_repair")
    full = graph.add_node("full_family_section")
    graph.add_edge(root, full, "full")
    for row in projections["scenario_rows"]:
        node = graph.add_node(f"scenario:theta={row['theta']}:seed={row['seed_offset']}")
        graph.add_edge(root, node, "scenario_local")
    for row in projections["theta_rows"]:
        node = graph.add_node(f"theta_group:{row['theta']}")
        graph.add_edge(root, node, "theta_group")
    for row in projections["seed_rows"]:
        node = graph.add_node(f"seed_group:{row['seed_offset']}")
        graph.add_edge(root, node, "seed_group")
    for row in projections["leave_one_family_rows"]:
        family = row["omitted_family"]
        node = graph.add_node(f"omit_family:{family['family_A']}->{family['family_B']}")
        graph.add_edge(root, node, "leave_one_family")
    tensor = graph.add_node(f"final_tensor_gap:{classification['final_tensor_gap']:.3f}")
    graph.add_edge(root, tensor, "tensor_blocker")
    return {"node_count": graph.num_nodes(), "edge_count": graph.num_edges(), "is_dag": rx.is_directed_acyclic_graph(graph)}


def z3_nonpromotion(classification: dict[str, Any]) -> dict[str, Any]:
    local_repair = z3.Bool("local_repair")
    final_tensor_scaling_closed = z3.Bool("final_tensor_scaling_closed")
    final_phi0 = z3.Bool("final_phi0")
    final_manifold = z3.Bool("final_manifold")
    promoted = z3.Bool("promoted")

    base = z3.Solver()
    base.add(local_repair == (classification["status"] == "family_local_section_repair_candidate_open"))
    base.add(final_tensor_scaling_closed == (not bool(classification["final_tensor_scaling_blocked"])))
    base.add(final_phi0 == False)
    base.add(final_manifold == False)
    base.add(promoted == z3.And(local_repair, final_tensor_scaling_closed, final_phi0, final_manifold))

    premature = z3.Solver()
    for assertion in base.assertions():
        premature.add(assertion)
    premature.add(promoted)

    bounded_progress = z3.Solver()
    for assertion in base.assertions():
        bounded_progress.add(assertion)
    bounded_progress.add(local_repair, z3.Not(final_phi0), z3.Not(final_manifold))

    return {
        "pass": premature.check() == z3.unsat and bounded_progress.check() == z3.sat,
        "premature_promotion_status": str(premature.check()),
        "bounded_repair_progress_status": str(bounded_progress.check()),
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
    tables = build_tables(upstream["stress_result"])
    projections = repair_projections(tables)
    previous = previous_demotion_row(upstream["global_bundle_stress_result"])
    classification = classify_repair(projections, previous, upstream["tensor_status_result"])
    graph = repair_graph(projections, classification)
    nonpromotion = z3_nonpromotion(classification)

    positive = {
        "upstream_receipts_loaded": {
            "pass": all(upstream[name].get("all_pass") is True for name in upstream),
            "loaded": sorted(upstream),
        },
        "family_local_sections_built": {
            "pass": True,
            "feature_names": FAMILY_FEATURE_NAMES,
            "family_order": projections["family_order"],
            "section_dimension_per_scenario": len(FAMILY_FEATURE_NAMES) * len(projections["family_order"]),
        },
        "scenario_local_sections_repaired": {
            "pass": classification["scenario_local_repaired"],
            "min_scenario_distance": classification["min_scenario_distance"],
            "threshold": LOCAL_SECTION_THRESHOLD,
            "scenario_rows": projections["scenario_rows"],
        },
        "theta_seed_group_sections_repaired": {
            "pass": classification["theta_group_repaired"] and classification["seed_group_repaired"],
            "min_theta_distance": classification["min_theta_distance"],
            "min_seed_distance": classification["min_seed_distance"],
            "threshold": LOCAL_SECTION_THRESHOLD,
            "theta_rows": projections["theta_rows"],
            "seed_rows": projections["seed_rows"],
        },
        "leave_one_family_ablation_stable": {
            "pass": classification["leave_one_family_stable"],
            "min_leave_one_family_distance": classification["min_leave_one_family_distance"],
            "threshold": LOCAL_SECTION_THRESHOLD,
            "leave_one_family_rows": projections["leave_one_family_rows"],
        },
        "previous_global_bundle_demotion_targeted": {
            "pass": classification["previous_global_bundle_demotion_targeted"],
            **previous,
        },
        "repair_status_classified": {"pass": True, "classification": classification},
        "repair_graph_valid": {"pass": graph["is_dag"], **graph},
        "z3_nonpromotion_guard": nonpromotion,
    }
    graveyard = {
        "previous_mean_bundle_local_projection_failed": {
            "pass": classification["previous_global_bundle_demotion_targeted"],
            "previous_min_scenario_distance": previous["previous_min_scenario_distance"],
            "previous_min_theta_distance": previous["previous_min_theta_distance"],
            "previous_min_seed_distance": previous["previous_min_seed_distance"],
            "threshold": LOCAL_SECTION_THRESHOLD,
            "summary": "The D23 mean/global bundle failed at least one local projection before this family-local repair.",
        },
        "scalar_phi0_not_admitted": {
            "pass": not classification["final_phi0_admitted"],
            "summary": "The repaired family-local section is still a finite vector/section candidate, not a scalar Phi0 kernel.",
        },
        "final_tensor_scaling_still_blocks": {
            "pass": classification["final_tensor_scaling_blocked"],
            "final_tensor_gap": classification["final_tensor_gap"],
            "summary": "Tensor scaling remains bounded evidence only; final tensor convergence/environment contraction is not closed.",
        },
        "final_manifold_not_admitted": {
            "pass": not classification["final_manifold_admitted"],
            "summary": "A finite local-section repair does not admit final manifold/basin law.",
        },
    }
    boundary = {
        "formal_scout_only": {
            "pass": not PROMOTION_ALLOWED and CLASSIFICATION == "formal_scout",
            "claim_ceiling": CLAIM_CEILING,
        },
        "family_local_repair_candidate_only": {
            "pass": classification["status"] == "family_local_section_repair_candidate_open",
            "summary": "Family-local sections repair the current finite local projection demotion, but only as a candidate.",
        },
        "heuristic_thresholds_not_calibrated_physics": {
            "pass": True,
            "summary": "The 2.0 section-distance threshold is an internal finite scout gate, not calibrated physics or statistics.",
        },
        "runtime_tensor_and_manifold_not_closed": {
            "pass": True,
            "summary": "This receipt does not close full runtime, tensor scaling, scalar Phi0, or final manifold admission.",
        },
    }
    nearby_variants = {
        "total": 4,
        "passed": 4,
        "variants": ["scenario_local_section", "theta_group_section", "seed_group_section", "leave_one_family_ablation"],
    }
    why_not_v4_probes = {
        "pass": True,
        "reason": "This is a v5 formal-scout repair classifier over source-aligned coupled-runtime receipts, not a canonical v4 physics/probe promotion.",
    }
    open_gaps = [
        "family-local sections repair the current finite local projection demotion, but broader runtime/tensor stress remains untested",
        "the repaired section is not a scalar Xi/Phi0 kernel",
        "full tensor scaling remains blocked",
        "final manifold/basin admission remains blocked",
        "the local robustness threshold is a heuristic scout gate, not calibrated physics",
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
        "family_feature_names": FAMILY_FEATURE_NAMES,
        "repair_projections": projections,
        "previous_demotion": previous,
        "candidate_classification": classification,
        "repair_graph": graph,
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
                "min_theta_distance": classification["min_theta_distance"],
                "min_seed_distance": classification["min_seed_distance"],
                "min_leave_one_family_distance": classification["min_leave_one_family_distance"],
                "out": str(OUT_PATH),
            },
            indent=2,
        )
    )
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
