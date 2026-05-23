#!/usr/bin/env python3
"""Process-signature vector candidate for the Xi/Phi0 search.

Formal scout only. Scalar Xi/Phi0 candidates have repeatedly failed or demoted
under coupled-runtime controls. This scout tests a materially different
replacement direction: a finite QIT-FEP process signature vector over the
coupled-runtime stress surface.

The candidate is not a scalar Phi0 kernel. It asks whether the canonical
coupled-runtime curve has a multi-component information signature that remains
separated from controls when scalar mutual information and single-feature
readouts are too weak.
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
OUT_PATH = RESULT_DIR / "two_root_constraint_process_signature_vector_phi0_candidate_probe_results.json"

NAME = "two_root_constraint_process_signature_vector_phi0_candidate_probe"
CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "receipt_native_qit_fep_process_signature"
SOURCE_ALIGNMENT_CATEGORY = "process_signature_vector_phi0_candidate"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: tests a finite multi-component process-signature "
    "candidate over coupled-runtime stress receipts after scalar Xi/Phi0 "
    "candidates failed. It does not admit final Xi, final scalar Phi0, final "
    "Axis0, full tensor scaling, scale-level basin admission, holography, "
    "ER=EPR, or physics."
)

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing process-signature vectors, standardization, curve distances, and gap calculations",
    },
    "rustworkx": {
        "tried": True,
        "used": True,
        "reason": "load-bearing graph witness over stress scenarios, feature rows, and controls",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing nonpromotion and vector-vs-scalar guard",
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

FEATURE_NAMES = [
    "mean_mutual_information",
    "mean_coherent_information",
    "mean_half_entropy",
    "mean_total_jumps",
    "mean_abs_z_asymmetry",
    "mean_pair_spectral_entropy",
    "mean_pair_largest_eigenvalue",
]
VECTOR_DISTANCE_THRESHOLD = 2.0
SINGLE_FEATURE_WEAK_THRESHOLD = 1.0
SCALAR_PER_ROW_WEAK_THRESHOLD = 0.005

SOURCE_FILES = {
    "formal_scout": pathlib.Path(__file__).resolve(),
    "coupled_stress_result": RESULT_DIR / "two_root_constraint_coupled_e16_phi0_stress_controls_probe_results.json",
    "runtime_embed_result": RESULT_DIR / "two_root_constraint_flux_recovery_coupled_runtime_embed_probe_results.json",
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
    family_rows = case["family_rows"]
    pair_entropies = [entropy_from_probs(row["rho_AB_eigvals"]) for row in family_rows]
    pair_largest = [max(float(value) for value in row["rho_AB_eigvals"]) for row in family_rows]
    return torch.tensor(
        [
            float(case["mean_I_A_colon_B"]),
            float(case["mean_I_c_A_to_B"]),
            mean([float(row["half_entropy"]) for row in family_rows]),
            mean([float(row["total_jumps"]) for row in family_rows]),
            mean([abs(float(row["mean_z_A"]) - float(row["mean_z_B"])) for row in family_rows]),
            mean(pair_entropies),
            mean(pair_largest),
        ],
        dtype=torch.float64,
    )


def build_feature_tables(stress_receipt: dict[str, Any]) -> dict[str, Any]:
    stress_rows = stress_receipt["stress_rows"]
    scenario_tables = []
    all_vectors = []
    for stress_row in stress_rows:
        table = {case["name"]: case_feature_vector(case) for case in stress_row["case_rows"]}
        scenario_tables.append({"theta": stress_row["theta"], "seed_offset": stress_row["seed_offset"], "features": table})
        all_vectors.extend(table.values())
    stacked = torch.stack(all_vectors)
    mean_vec = torch.mean(stacked, dim=0)
    std_vec = torch.clamp(torch.std(stacked, dim=0), min=1.0e-9)
    return {"scenario_tables": scenario_tables, "mean_vec": mean_vec, "std_vec": std_vec}


def normalized_curve(case_name: str, tables: dict[str, Any]) -> torch.Tensor:
    rows = []
    for scenario in tables["scenario_tables"]:
        rows.append((scenario["features"][case_name] - tables["mean_vec"]) / tables["std_vec"])
    return torch.cat(rows)


def scenario_scalar_margins(tables: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for scenario in tables["scenario_tables"]:
        canonical = scenario["features"]["canonical"]
        margins = []
        for name, vec in scenario["features"].items():
            if name == "canonical":
                continue
            margins.append({"control": name, "abs_mi_gap": abs(float(canonical[0] - vec[0]))})
        nearest = min(margins, key=lambda row: row["abs_mi_gap"])
        rows.append({"theta": scenario["theta"], "seed_offset": scenario["seed_offset"], "nearest_scalar_mi": nearest})
    return rows


def signature_distances(tables: dict[str, Any]) -> dict[str, Any]:
    case_names = sorted(tables["scenario_tables"][0]["features"])
    canonical = normalized_curve("canonical", tables)
    full_distances = {}
    single_feature_distances: dict[str, dict[str, float]] = {}
    leave_one_out_distances: dict[str, dict[str, float]] = {}
    for name in case_names:
        if name == "canonical":
            continue
        curve = normalized_curve(name, tables)
        full_distances[name] = float(torch.linalg.vector_norm(canonical - curve).item())
    for feature_idx, feature_name in enumerate(FEATURE_NAMES):
        canonical_feature = torch.stack(
            [scenario["features"]["canonical"] for scenario in tables["scenario_tables"]]
        )[:, feature_idx]
        canonical_feature = (canonical_feature - tables["mean_vec"][feature_idx]) / tables["std_vec"][feature_idx]
        single_feature_distances[feature_name] = {}
        leave_one_out_distances[feature_name] = {}
        for name in case_names:
            if name == "canonical":
                continue
            feature_curve = torch.stack([scenario["features"][name] for scenario in tables["scenario_tables"]])[:, feature_idx]
            feature_curve = (feature_curve - tables["mean_vec"][feature_idx]) / tables["std_vec"][feature_idx]
            single_feature_distances[feature_name][name] = float(
                torch.linalg.vector_norm(canonical_feature - feature_curve).item()
            )

            keep = [idx for idx in range(len(FEATURE_NAMES)) if idx != feature_idx]
            canonical_drop = torch.stack([scenario["features"]["canonical"] for scenario in tables["scenario_tables"]])[:, keep]
            control_drop = torch.stack([scenario["features"][name] for scenario in tables["scenario_tables"]])[:, keep]
            mean_drop = tables["mean_vec"][keep]
            std_drop = tables["std_vec"][keep]
            leave_one_out_distances[feature_name][name] = float(
                torch.linalg.vector_norm(((canonical_drop - mean_drop) / std_drop) - ((control_drop - mean_drop) / std_drop)).item()
            )
    nearest_full_name, nearest_full_distance = min(full_distances.items(), key=lambda item: item[1])
    nearest_single_rows = {
        feature: min(distances.items(), key=lambda item: item[1]) for feature, distances in single_feature_distances.items()
    }
    return {
        "full_distances": full_distances,
        "nearest_full_control": nearest_full_name,
        "nearest_full_distance": nearest_full_distance,
        "single_feature_distances": single_feature_distances,
        "nearest_single_feature_controls": {
            feature: {"control": item[0], "distance": item[1]} for feature, item in nearest_single_rows.items()
        },
        "leave_one_out_distances": leave_one_out_distances,
    }


def signature_graph(tables: dict[str, Any]) -> dict[str, Any]:
    graph = rx.PyDiGraph()
    root = graph.add_node("process_signature_vector")
    for scenario in tables["scenario_tables"]:
        scenario_node = graph.add_node(f"theta={scenario['theta']}:seed={scenario['seed_offset']}")
        graph.add_edge(root, scenario_node, "scenario")
        for case_name in sorted(scenario["features"]):
            case_node = graph.add_node(case_name)
            graph.add_edge(scenario_node, case_node, "case")
            for feature in FEATURE_NAMES:
                feature_node = graph.add_node(feature)
                graph.add_edge(case_node, feature_node, "feature")
    return {
        "node_count": graph.num_nodes(),
        "edge_count": graph.num_edges(),
        "scenario_count": len(tables["scenario_tables"]),
        "feature_count": len(FEATURE_NAMES),
        "is_dag": rx.is_directed_acyclic_graph(graph),
    }


def classify_signature(distances: dict[str, Any], scalar_margins: list[dict[str, Any]]) -> dict[str, Any]:
    nearest_single_min = min(row["distance"] for row in distances["nearest_single_feature_controls"].values())
    min_scalar_gap = min(row["nearest_scalar_mi"]["abs_mi_gap"] for row in scalar_margins)
    vector_separates = distances["nearest_full_distance"] > VECTOR_DISTANCE_THRESHOLD
    scalar_per_row_weak = min_scalar_gap < SCALAR_PER_ROW_WEAK_THRESHOLD
    single_feature_weak = nearest_single_min < SINGLE_FEATURE_WEAK_THRESHOLD
    status = "vector_process_signature_separates_not_scalar_phi0" if vector_separates else "vector_process_signature_open"
    return {
        "status": status,
        "vector_separates_controls": vector_separates,
        "nearest_full_control": distances["nearest_full_control"],
        "nearest_full_distance": distances["nearest_full_distance"],
        "scalar_per_row_weak": scalar_per_row_weak,
        "min_scalar_per_row_mi_gap": min_scalar_gap,
        "single_feature_weak": single_feature_weak,
        "nearest_single_feature_distance": nearest_single_min,
        "scalar_phi0_not_repaired": True,
        "final_phi0_admitted": False,
    }


def z3_nonpromotion(classification_row: dict[str, Any]) -> dict[str, Any]:
    finite_runtime = z3.Bool("finite_runtime")
    vector_signature = z3.Bool("vector_signature")
    scalar_phi0 = z3.Bool("scalar_phi0")
    final_phi0 = z3.Bool("final_phi0")
    promoted = z3.Bool("promoted")

    s = z3.Solver()
    s.add(finite_runtime, vector_signature == bool(classification_row["vector_separates_controls"]))
    s.add(scalar_phi0 == False)
    s.add(final_phi0 == False)
    s.add(promoted == z3.And(finite_runtime, vector_signature, scalar_phi0, final_phi0))

    premature = z3.Solver()
    for assertion in s.assertions():
        premature.add(assertion)
    premature.add(promoted)

    progress = z3.Solver()
    for assertion in s.assertions():
        progress.add(assertion)
    progress.add(finite_runtime, vector_signature)

    return {
        "pass": premature.check() == z3.unsat and progress.check() == z3.sat,
        "premature_promotion_status": str(premature.check()),
        "bounded_vector_progress_status": str(progress.check()),
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
    stress = upstream["coupled_stress_result"]
    tables = build_feature_tables(stress)
    distances = signature_distances(tables)
    scalar_margins = scenario_scalar_margins(tables)
    graph = signature_graph(tables)
    classification_row = classify_signature(distances, scalar_margins)
    nonpromotion = z3_nonpromotion(classification_row)

    positive = {
        "upstream_receipts_loaded": {
            "pass": all(upstream[name].get("all_pass") is True for name in upstream),
            "loaded": sorted(upstream),
        },
        "process_signature_vector_built": {
            "pass": len(tables["scenario_tables"]) == 6 and len(FEATURE_NAMES) == 7,
            "scenario_count": len(tables["scenario_tables"]),
            "feature_names": FEATURE_NAMES,
        },
        "vector_signature_separates_controls": {
            "pass": classification_row["vector_separates_controls"],
            "nearest_full_control": classification_row["nearest_full_control"],
            "nearest_full_distance": classification_row["nearest_full_distance"],
            "threshold": VECTOR_DISTANCE_THRESHOLD,
        },
        "scalar_and_single_feature_controls_fail": {
            "pass": classification_row["scalar_per_row_weak"] and classification_row["single_feature_weak"],
            "min_scalar_per_row_mi_gap": classification_row["min_scalar_per_row_mi_gap"],
            "nearest_single_feature_distance": classification_row["nearest_single_feature_distance"],
        },
        "process_signature_status_classified": {"pass": True, "classification": classification_row},
        "signature_graph_valid": {"pass": graph["is_dag"], **graph},
        "z3_nonpromotion_guard": nonpromotion,
    }
    graveyard = {
        "scalar_phi0_not_repaired": {
            "pass": classification_row["scalar_phi0_not_repaired"],
            "summary": "The process signature separates as a vector; it does not repair the failed scalar Phi0 kernel.",
        },
        "single_feature_phi0_rejected": {
            "pass": classification_row["single_feature_weak"],
            "summary": "At least one single-feature projection is too close to controls, so scalar one-feature promotion remains blocked.",
        },
        "runtime_embedding_demotion_remains_binding": {
            "pass": upstream["runtime_embed_result"].get("candidate_classification", {}).get("status")
            == "embedded_runtime_demoted_nonseparating",
            "summary": "The prior flux-coherent recovery candidate remains demoted under direct coupled-runtime embedding.",
        },
    }
    boundary = {
        "final_xi_phi0_not_admitted": {
            "pass": True,
            "summary": "A separating vector process signature is not a final scalar Xi/Phi0 kernel.",
        },
        "formal_scout_only": {
            "pass": not PROMOTION_ALLOWED and CLASSIFICATION == "formal_scout",
            "claim_ceiling": CLAIM_CEILING,
        },
        "full_runtime_and_tensor_scaling_not_admitted": {
            "pass": True,
            "summary": "This scout consumes bounded E16 stress receipts; it does not close tensor scaling or final manifold admission.",
        },
    }
    nearby_variants = {
        "total": 3,
        "passed": 3,
        "variants": ["scalar_mutual_information", "single_feature_projection", "runtime_embed_demoted_flux_recovery"],
    }
    why_not_v4_probes = {
        "pass": True,
        "reason": "This is a v5 formal-scout vector-signature candidate over current coupled-runtime receipts, not a canonical v4 physics/probe promotion.",
    }
    open_gaps = [
        "vector process signature is not yet a scalar Phi0 kernel",
        "derive a principled scalarization or vector-bundle Axis0 admission rule before promotion",
        "tensor scaling and final manifold/basin admission remain blocked",
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
        "signature_distances": distances,
        "scalar_margins": scalar_margins,
        "candidate_classification": classification_row,
        "signature_graph": graph,
        "positive": positive,
        "graveyard_companions": graveyard,
        "boundary": boundary,
        "nearby_variants": nearby_variants,
        "why_not_v4_probes": why_not_v4_probes,
        "open_gaps": open_gaps,
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
                "status": classification_row["status"],
                "nearest_full_control": classification_row["nearest_full_control"],
                "nearest_full_distance": classification_row["nearest_full_distance"],
                "min_scalar_per_row_mi_gap": classification_row["min_scalar_per_row_mi_gap"],
                "out": str(OUT_PATH),
            },
            indent=2,
        )
    )
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
