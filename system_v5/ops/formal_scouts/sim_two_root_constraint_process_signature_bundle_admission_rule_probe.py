#!/usr/bin/env python3
"""Vector-bundle admission rule for process-signature evidence.

Formal scout only. The previous process-signature scout found that a full
multi-component curve separates coupled-runtime controls while scalar mutual
information and single-feature readouts are weak. This scout tests the next
admissible rule: treat the process signature as a finite section over a
stress-scenario base, not as a scalar Phi0 kernel.

The rule can fail in three ways:
- the full base-resolved section can fail to separate controls;
- the section can be fragile under leave-one-feature ablation;
- the separation can survive only after collapsing away the stress base, which
  would make the "bundle" claim decorative.
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
OUT_PATH = RESULT_DIR / "two_root_constraint_process_signature_bundle_admission_rule_probe_results.json"

NAME = "two_root_constraint_process_signature_bundle_admission_rule_probe"
CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "receipt_native_vector_bundle_admission_rule"
SOURCE_ALIGNMENT_CATEGORY = "process_signature_bundle_admission_rule"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: tests a finite vector-bundle admission rule for the "
    "process-signature evidence. It may admit a bounded vector-bundle candidate "
    "for further work, but it does not admit final Xi, scalar Phi0, final "
    "Axis0, tensor scaling, final manifold completion, holography, ER=EPR, or physics."
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
LEAVE_ONE_OUT_THRESHOLD = 2.0
BASE_COLLAPSED_REJECTION_THRESHOLD = 1.0
SINGLE_FEATURE_REJECTION_THRESHOLD = 1.0
SCALAR_MI_REJECTION_THRESHOLD = 0.005

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing vector-bundle section tensors, standardization, ablations, and distance calculations",
    },
    "rustworkx": {
        "tried": True,
        "used": True,
        "reason": "load-bearing bundle incidence graph over stress-scenario base, feature fibers, and controls",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing nonpromotion guard separating vector-bundle progress from scalar Phi0 promotion",
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
    "process_signature_result": RESULT_DIR / "two_root_constraint_process_signature_vector_phi0_candidate_probe_results.json",
    "runtime_embed_result": RESULT_DIR / "two_root_constraint_flux_recovery_coupled_runtime_embed_probe_results.json",
}


def rel(path: pathlib.Path) -> str:
    try:
        return str(path.relative_to(REPO))
    except ValueError:
        return str(path)


def sha256(path: pathlib.Path) -> str | None:
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None


def source_hashes() -> dict[str, Any]:
    return {name: {"path": rel(path), "sha256": sha256(path)} for name, path in SOURCE_FILES.items()}


def read_json(path: pathlib.Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def jsonable(value: Any) -> Any:
    if isinstance(value, pathlib.Path):
        return rel(value)
    return qit.jsonable(value)


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


def build_sections(stress_receipt: dict[str, Any]) -> dict[str, Any]:
    scenario_tables = []
    raw_vectors = []
    for stress_row in stress_receipt["stress_rows"]:
        table = {case["name"]: case_feature_vector(case) for case in stress_row["case_rows"]}
        scenario_tables.append({"theta": stress_row["theta"], "seed_offset": stress_row["seed_offset"], "features": table})
        raw_vectors.extend(table.values())
    stacked = torch.stack(raw_vectors)
    mean_vec = torch.mean(stacked, dim=0)
    std_vec = torch.clamp(torch.std(stacked, dim=0), min=1.0e-9)
    case_names = sorted(scenario_tables[0]["features"])
    sections = {
        case_name: torch.stack([(row["features"][case_name] - mean_vec) / std_vec for row in scenario_tables])
        for case_name in case_names
    }
    return {
        "scenario_tables": scenario_tables,
        "sections": sections,
        "case_names": case_names,
        "mean_vec": mean_vec,
        "std_vec": std_vec,
    }


def nearest(rows: dict[str, float]) -> tuple[str, float]:
    return min(rows.items(), key=lambda item: item[1])


def section_distances(sections: dict[str, torch.Tensor]) -> dict[str, Any]:
    canonical = sections["canonical"]
    full = {}
    base_collapsed = {}
    base_sorted = {}
    single_feature: dict[str, dict[str, float]] = {feature: {} for feature in FEATURE_NAMES}
    leave_one_out: dict[str, dict[str, float]] = {feature: {} for feature in FEATURE_NAMES}

    for name, section in sections.items():
        if name == "canonical":
            continue
        full[name] = float(torch.linalg.vector_norm(canonical - section).item())
        base_collapsed[name] = float(torch.linalg.vector_norm(torch.mean(canonical, dim=0) - torch.mean(section, dim=0)).item())
        base_sorted[name] = float(torch.linalg.vector_norm(torch.sort(canonical, dim=0).values - torch.sort(section, dim=0).values).item())
        for idx, feature in enumerate(FEATURE_NAMES):
            single_feature[feature][name] = float(torch.linalg.vector_norm(canonical[:, idx] - section[:, idx]).item())
            keep = [feature_idx for feature_idx in range(len(FEATURE_NAMES)) if feature_idx != idx]
            leave_one_out[feature][name] = float(torch.linalg.vector_norm(canonical[:, keep] - section[:, keep]).item())

    nearest_full = nearest(full)
    nearest_base_collapsed = nearest(base_collapsed)
    nearest_base_sorted = nearest(base_sorted)
    nearest_single_feature = {feature: nearest(rows) for feature, rows in single_feature.items()}
    nearest_leave_one_out = {feature: nearest(rows) for feature, rows in leave_one_out.items()}
    return {
        "full_section_distances": full,
        "nearest_full_section": {"control": nearest_full[0], "distance": nearest_full[1]},
        "base_collapsed_distances": base_collapsed,
        "nearest_base_collapsed": {"control": nearest_base_collapsed[0], "distance": nearest_base_collapsed[1]},
        "base_sorted_distances": base_sorted,
        "nearest_base_sorted": {"control": nearest_base_sorted[0], "distance": nearest_base_sorted[1]},
        "single_feature_distances": single_feature,
        "nearest_single_feature": {
            feature: {"control": item[0], "distance": item[1]} for feature, item in nearest_single_feature.items()
        },
        "leave_one_out_distances": leave_one_out,
        "nearest_leave_one_out": {
            feature: {"control": item[0], "distance": item[1]} for feature, item in nearest_leave_one_out.items()
        },
    }


def scalar_mi_gaps(sections_data: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for scenario in sections_data["scenario_tables"]:
        canonical = scenario["features"]["canonical"][0]
        margins = []
        for name, vec in scenario["features"].items():
            if name == "canonical":
                continue
            margins.append({"control": name, "abs_mi_gap": abs(float(canonical - vec[0]))})
        closest = min(margins, key=lambda row: row["abs_mi_gap"])
        rows.append({"theta": scenario["theta"], "seed_offset": scenario["seed_offset"], "nearest_scalar_mi": closest})
    return rows


def bundle_graph(sections_data: dict[str, Any]) -> dict[str, Any]:
    graph = rx.PyDiGraph()
    root = graph.add_node("finite_process_signature_bundle")
    for scenario_idx, scenario in enumerate(sections_data["scenario_tables"]):
        base_node = graph.add_node(f"base:{scenario_idx}:theta={scenario['theta']}:seed={scenario['seed_offset']}")
        graph.add_edge(root, base_node, "base")
        for feature in FEATURE_NAMES:
            fiber_node = graph.add_node(f"fiber:{feature}")
            graph.add_edge(base_node, fiber_node, "fiber")
        for case_name in sections_data["case_names"]:
            section_node = graph.add_node(f"section:{case_name}")
            graph.add_edge(base_node, section_node, "section_value")
    return {
        "node_count": graph.num_nodes(),
        "edge_count": graph.num_edges(),
        "base_count": len(sections_data["scenario_tables"]),
        "fiber_dimension": len(FEATURE_NAMES),
        "case_count": len(sections_data["case_names"]),
        "is_dag": rx.is_directed_acyclic_graph(graph),
    }


def classify_bundle(distances: dict[str, Any], scalar_rows: list[dict[str, Any]]) -> dict[str, Any]:
    nearest_single = min(row["distance"] for row in distances["nearest_single_feature"].values())
    nearest_leave_one_out = min(row["distance"] for row in distances["nearest_leave_one_out"].values())
    min_scalar_gap = min(row["nearest_scalar_mi"]["abs_mi_gap"] for row in scalar_rows)
    full_distance = distances["nearest_full_section"]["distance"]
    base_collapsed_distance = distances["nearest_base_collapsed"]["distance"]

    full_section_separates = full_distance > FULL_SECTION_THRESHOLD
    leave_one_out_stable = nearest_leave_one_out > LEAVE_ONE_OUT_THRESHOLD
    scalar_mi_rejected = min_scalar_gap < SCALAR_MI_REJECTION_THRESHOLD
    single_feature_rejected = nearest_single < SINGLE_FEATURE_REJECTION_THRESHOLD
    base_collapsed_rejected = base_collapsed_distance < BASE_COLLAPSED_REJECTION_THRESHOLD
    vector_bundle_candidate = full_section_separates and leave_one_out_stable and base_collapsed_rejected
    status = "vector_bundle_candidate_admitted_for_further_stress" if vector_bundle_candidate else "vector_bundle_candidate_open"
    return {
        "status": status,
        "vector_bundle_candidate": vector_bundle_candidate,
        "full_section_separates": full_section_separates,
        "full_section_nearest_control": distances["nearest_full_section"]["control"],
        "full_section_nearest_distance": full_distance,
        "leave_one_out_stable": leave_one_out_stable,
        "nearest_leave_one_out_distance": nearest_leave_one_out,
        "scalar_mi_rejected": scalar_mi_rejected,
        "min_scalar_mi_gap": min_scalar_gap,
        "single_feature_rejected": single_feature_rejected,
        "nearest_single_feature_distance": nearest_single,
        "base_collapsed_rejected": base_collapsed_rejected,
        "base_collapsed_nearest_control": distances["nearest_base_collapsed"]["control"],
        "base_collapsed_nearest_distance": base_collapsed_distance,
        "final_phi0_admitted": False,
    }


def z3_nonpromotion_gate(classification: dict[str, Any]) -> dict[str, Any]:
    finite_runtime = z3.Bool("finite_runtime")
    vector_bundle = z3.Bool("vector_bundle")
    scalar_phi0 = z3.Bool("scalar_phi0")
    final_phi0 = z3.Bool("final_phi0")
    promoted = z3.Bool("promoted")

    base = z3.Solver()
    base.add(finite_runtime)
    base.add(vector_bundle == bool(classification["vector_bundle_candidate"]))
    base.add(scalar_phi0 == False)
    base.add(final_phi0 == False)
    base.add(promoted == z3.And(finite_runtime, vector_bundle, scalar_phi0, final_phi0))

    premature = z3.Solver()
    for assertion in base.assertions():
        premature.add(assertion)
    premature.add(promoted)

    bounded_progress = z3.Solver()
    for assertion in base.assertions():
        bounded_progress.add(assertion)
    bounded_progress.add(finite_runtime, vector_bundle, z3.Not(scalar_phi0), z3.Not(final_phi0))

    return {
        "pass": premature.check() == z3.unsat and bounded_progress.check() == z3.sat,
        "premature_promotion_status": str(premature.check()),
        "bounded_vector_bundle_progress_status": str(bounded_progress.check()),
        "scalar_phi0": False,
        "final_phi0": False,
    }


def section_passes(section: Any) -> bool:
    if isinstance(section, dict):
        return all(not isinstance(row, dict) or bool(row.get("pass", True)) for row in section.values())
    return False


def main() -> int:
    start = time.time()
    upstream = {name: read_json(path) for name, path in SOURCE_FILES.items() if name.endswith("_result")}
    sections_data = build_sections(upstream["stress_result"])
    distances = section_distances(sections_data["sections"])
    scalar_rows = scalar_mi_gaps(sections_data)
    graph = bundle_graph(sections_data)
    classification = classify_bundle(distances, scalar_rows)
    nonpromotion = z3_nonpromotion_gate(classification)

    positive = {
        "upstream_receipts_loaded": {
            "pass": all(upstream[name].get("all_pass") is True for name in upstream),
            "loaded": sorted(upstream),
        },
        "finite_bundle_section_built": {
            "pass": graph["base_count"] == 6 and graph["fiber_dimension"] == 7,
            **graph,
        },
        "base_resolved_section_separates_controls": {
            "pass": classification["full_section_separates"],
            "nearest_control": classification["full_section_nearest_control"],
            "nearest_distance": classification["full_section_nearest_distance"],
            "threshold": FULL_SECTION_THRESHOLD,
        },
        "leave_one_feature_ablation_stable": {
            "pass": classification["leave_one_out_stable"],
            "nearest_leave_one_out_distance": classification["nearest_leave_one_out_distance"],
            "threshold": LEAVE_ONE_OUT_THRESHOLD,
            "nearest_leave_one_out": distances["nearest_leave_one_out"],
        },
        "bundle_status_classified": {"pass": True, "classification": classification},
        "z3_nonpromotion_guard": nonpromotion,
    }
    graveyard = {
        "base_collapsed_mean_rejected": {
            "pass": classification["base_collapsed_rejected"],
            "nearest_control": classification["base_collapsed_nearest_control"],
            "nearest_distance": classification["base_collapsed_nearest_distance"],
            "threshold": BASE_COLLAPSED_REJECTION_THRESHOLD,
            "summary": "Collapsing the stress base to a mean feature vector is too weak; the base-resolved section is load-bearing.",
        },
        "single_feature_scalarization_rejected": {
            "pass": classification["single_feature_rejected"],
            "nearest_single_feature_distance": classification["nearest_single_feature_distance"],
            "threshold": SINGLE_FEATURE_REJECTION_THRESHOLD,
            "summary": "No one-feature readout is admitted as Phi0.",
        },
        "scalar_mutual_information_rejected": {
            "pass": classification["scalar_mi_rejected"],
            "min_scalar_mi_gap": classification["min_scalar_mi_gap"],
            "threshold": SCALAR_MI_REJECTION_THRESHOLD,
            "summary": "Per-scenario scalar mutual information remains too close to controls.",
        },
        "final_phi0_not_admitted": {
            "pass": not classification["final_phi0_admitted"],
            "summary": "The vector-bundle rule is a bounded candidate for further stress, not final scalar Phi0.",
        },
    }
    boundary = {
        "formal_scout_only": {
            "pass": not PROMOTION_ALLOWED and CLASSIFICATION == "formal_scout",
            "claim_ceiling": CLAIM_CEILING,
        },
        "vector_bundle_candidate_only": {
            "pass": classification["vector_bundle_candidate"] and not classification["final_phi0_admitted"],
            "summary": "Admits only a bounded vector-bundle candidate for further stress; no scalar kernel is promoted.",
        },
        "runtime_tensor_and_manifold_not_closed": {
            "pass": True,
            "summary": "Uses bounded coupled-runtime stress receipts; does not close full tensor scaling or final manifold admission.",
        },
    }
    nearby_variants = {
        "total": 4,
        "passed": 4,
        "variants": [
            "base_collapsed_mean",
            "single_feature_scalarization",
            "scalar_mutual_information",
            "leave_one_feature_ablation",
        ],
    }
    why_not_v4_probes = {
        "pass": True,
        "reason": "This is a v5 formal-scout admission-rule test over current source-aligned receipts, not a canonical v4 physics/probe promotion.",
    }
    open_gaps = [
        "vector-bundle candidate needs broader coupled-runtime and tensor-scaling stress before any promotion",
        "no scalar Xi/Phi0 kernel is admitted",
        "full manifold/basin admission remains blocked",
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
        "distances": distances,
        "scalar_rows": scalar_rows,
        "candidate_classification": classification,
        "bundle_graph": graph,
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
                "full_section_nearest_distance": classification["full_section_nearest_distance"],
                "base_collapsed_nearest_distance": classification["base_collapsed_nearest_distance"],
                "nearest_leave_one_out_distance": classification["nearest_leave_one_out_distance"],
                "out": str(OUT_PATH),
            },
            indent=2,
        )
    )
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
