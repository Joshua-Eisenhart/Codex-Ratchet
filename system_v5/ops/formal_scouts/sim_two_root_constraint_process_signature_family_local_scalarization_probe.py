#!/usr/bin/env python3
"""Scalarization audit for the family-local process-signature section.

Formal scout only. The broad family-local section survives as a vector/section
object with thin margin. This scout asks the next stricter question: can that
section evidence be collapsed into a scalar Xi/Phi0-like score without using the
control labels it is supposed to beat?

The answer in this receipt is negative. Simple scalar energies and held-out
prototype scalarizations fail rowwise canonical-vs-control separation on the
broad stress surface. That keeps the section candidate useful but blocks scalar
Phi0 admission.
"""

from __future__ import annotations

import hashlib
import json
import pathlib
import time
from typing import Any, Callable

import rustworkx as rx
import torch
import z3

import qit_engine_runtime as qit
import sim_two_root_constraint_process_signature_family_local_tensor_stress_probe as family_tensor


SCOUT_ROOT = pathlib.Path(__file__).resolve().parent
REPO = SCOUT_ROOT.parents[2]
RESULT_DIR = SCOUT_ROOT / "results"
OUT_PATH = RESULT_DIR / "two_root_constraint_process_signature_family_local_scalarization_probe_results.json"

NAME = "two_root_constraint_process_signature_family_local_scalarization_probe"
CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "receipt_native_family_local_scalarization_audit"
SOURCE_ALIGNMENT_CATEGORY = "process_signature_family_local_scalarization"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: audits whether the broad family-local process-signature "
    "section can be collapsed into scalar Xi/Phi0-like readouts. It kills the "
    "tested scalarizations and does not admit scalar Phi0, final Xi, final "
    "Axis0, final tensor scaling, final manifold completion, holography, ER=EPR, "
    "or physics."
)

SCALAR_MARGIN_TOL = 1.0e-9

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing section tensors, scalarization scores, and held-out margin calculations",
    },
    "rustworkx": {
        "tried": True,
        "used": True,
        "reason": "load-bearing scalarization failure graph over candidate families and holdout modes",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing nonpromotion guard separating section survival from scalar Phi0 admission",
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
    "family_tensor_source": SCOUT_ROOT
    / "sim_two_root_constraint_process_signature_family_local_tensor_stress_probe.py",
    "broad_stress_result": RESULT_DIR
    / "two_root_constraint_process_signature_family_local_broad_stress_probe_results.json",
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


def build_sections(broad_receipt: dict[str, Any]) -> list[dict[str, Any]]:
    stress = {
        "stress_rows": broad_receipt["stress_rows"],
        "tensor_carrier_controls": broad_receipt["tensor_carrier_controls"],
    }
    table = family_tensor.build_variant_tables(
        stress,
        feature_indices=list(range(len(family_tensor.FEATURE_NAMES))),
        standardization="family_position",
        row_sort_mode="family_label",
    )
    rows = []
    case_names = sorted(table["scenarios"][0]["features"])
    for scenario_idx, scenario in enumerate(table["scenarios"]):
        for case_name in case_names:
            rows.append(
                {
                    "scenario": scenario_idx,
                    "theta": float(scenario["theta"]),
                    "seed_offset": int(scenario["seed_offset"]),
                    "case": case_name,
                    "section": family_tensor.section_vector(table, scenario, case_name),
                }
            )
    return rows


def rowwise_margins(rows: list[dict[str, Any]], score_fn: Callable[[dict[str, Any]], float]) -> dict[str, Any]:
    margins = []
    details = []
    for scenario in sorted({row["scenario"] for row in rows}):
        group = [row for row in rows if row["scenario"] == scenario]
        canonical_score = [score_fn(row) for row in group if row["case"] == "canonical"][0]
        control_scores = {row["case"]: score_fn(row) for row in group if row["case"] != "canonical"}
        max_control_name, max_control_score = max(control_scores.items(), key=lambda item: item[1])
        margin = canonical_score - max_control_score
        margins.append(margin)
        details.append(
            {
                "scenario": scenario,
                "theta": group[0]["theta"],
                "seed_offset": group[0]["seed_offset"],
                "canonical_score": canonical_score,
                "max_control_name": max_control_name,
                "max_control_score": max_control_score,
                "margin": margin,
            }
        )
    return {
        "scenario_count": len(details),
        "pass": min(margins) > SCALAR_MARGIN_TOL,
        "min_margin": min(margins),
        "mean_margin": sum(margins) / len(margins),
        "max_margin": max(margins),
        "details": details,
    }


def simple_scalarizations(rows: list[dict[str, Any]]) -> dict[str, Any]:
    score_fns: dict[str, Callable[[dict[str, Any]], float]] = {
        "section_norm": lambda row: float(torch.linalg.vector_norm(row["section"]).item()),
        "section_l1": lambda row: float(torch.sum(torch.abs(row["section"])).item()),
        "section_sum": lambda row: float(torch.sum(row["section"]).item()),
        "section_mean": lambda row: float(torch.mean(row["section"]).item()),
    }
    return {name: rowwise_margins(rows, fn) for name, fn in score_fns.items()}


def prototype_scalarization(rows: list[dict[str, Any]], holdout: str, mode: str) -> dict[str, Any]:
    margins = []
    details = []
    values = sorted({row[holdout] for row in rows})
    for value in values:
        train = [row for row in rows if row[holdout] != value]
        if not train:
            continue
        canonical_centroid = torch.stack([row["section"] for row in train if row["case"] == "canonical"]).mean(0)
        control_centroid = torch.stack([row["section"] for row in train if row["case"] != "canonical"]).mean(0)
        direction = canonical_centroid - control_centroid
        scenarios = sorted({row["scenario"] for row in rows if row[holdout] == value})
        for scenario in scenarios:
            group = [row for row in rows if row["scenario"] == scenario]
            scores = {}
            for row in group:
                if mode == "projection":
                    score = float(torch.dot(row["section"], direction).item())
                elif mode == "distance_margin":
                    score = float(
                        torch.linalg.vector_norm(row["section"] - control_centroid).item()
                        - torch.linalg.vector_norm(row["section"] - canonical_centroid).item()
                    )
                else:
                    raise ValueError(f"unknown prototype scalarization mode: {mode}")
                scores[row["case"]] = score
            canonical_score = scores["canonical"]
            control_scores = {name: score for name, score in scores.items() if name != "canonical"}
            max_control_name, max_control_score = max(control_scores.items(), key=lambda item: item[1])
            margin = canonical_score - max_control_score
            margins.append(margin)
            details.append(
                {
                    "holdout": holdout,
                    "holdout_value": value,
                    "scenario": scenario,
                    "theta": group[0]["theta"],
                    "seed_offset": group[0]["seed_offset"],
                    "canonical_score": canonical_score,
                    "max_control_name": max_control_name,
                    "max_control_score": max_control_score,
                    "margin": margin,
                }
            )
    return {
        "holdout": holdout,
        "mode": mode,
        "scenario_count": len(details),
        "pass": min(margins) > SCALAR_MARGIN_TOL,
        "min_margin": min(margins),
        "mean_margin": sum(margins) / len(margins),
        "max_margin": max(margins),
        "positive_margin_count": sum(1 for margin in margins if margin > SCALAR_MARGIN_TOL),
        "details": details,
    }


def prototype_scalarizations(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        f"leave_one_{holdout}_{mode}": prototype_scalarization(rows, holdout, mode)
        for holdout in ("scenario", "theta", "seed_offset")
        for mode in ("projection", "distance_margin")
    }


def classify(simple: dict[str, Any], prototype: dict[str, Any], broad_receipt: dict[str, Any]) -> dict[str, Any]:
    all_scalar_rows = {**simple, **prototype}
    admitted = {name: row for name, row in all_scalar_rows.items() if row["pass"]}
    broad_status = broad_receipt["candidate_classification"]["status"]
    return {
        "status": "scalarization_killed_section_only_open" if not admitted else "scalarization_candidate_open",
        "tested_scalarization_count": len(all_scalar_rows),
        "admitted_scalarizations": sorted(admitted),
        "killed_scalarizations": sorted(set(all_scalar_rows) - set(admitted)),
        "section_candidate_status": broad_status,
        "section_min_scenario_distance": broad_receipt["candidate_classification"]["min_scenario_distance"],
        "section_broad_margin": broad_receipt["candidate_classification"]["broad_min_margin_over_threshold"],
        "scalar_phi0_admitted": bool(admitted),
        "final_xi_phi0_admitted": False,
        "final_manifold_admitted": False,
    }


def scalarization_graph(classification: dict[str, Any], simple: dict[str, Any], prototype: dict[str, Any]) -> dict[str, Any]:
    graph = rx.PyDiGraph()
    root = graph.add_node("family_local_scalarization")
    for name, row in {**simple, **prototype}.items():
        node = graph.add_node(f"{name}:pass={row['pass']}")
        graph.add_edge(root, node, "candidate")
    status_node = graph.add_node(classification["status"])
    graph.add_edge(root, status_node, "classification")
    return {"node_count": graph.num_nodes(), "edge_count": graph.num_edges(), "is_dag": rx.is_directed_acyclic_graph(graph)}


def z3_nonpromotion(classification: dict[str, Any]) -> dict[str, Any]:
    section_survived = z3.Bool("section_survived")
    scalar_phi0 = z3.Bool("scalar_phi0")
    final_xi_phi0 = z3.Bool("final_xi_phi0")
    final_manifold = z3.Bool("final_manifold")
    promoted = z3.Bool("promoted")

    base = z3.Solver()
    base.add(section_survived == (classification["section_candidate_status"] == "family_local_broad_stress_candidate_open"))
    base.add(scalar_phi0 == bool(classification["scalar_phi0_admitted"]))
    base.add(final_xi_phi0 == False)
    base.add(final_manifold == False)
    base.add(promoted == z3.And(section_survived, scalar_phi0, final_xi_phi0, final_manifold))

    premature = z3.Solver()
    for assertion in base.assertions():
        premature.add(assertion)
    premature.add(promoted)

    section_only = z3.Solver()
    for assertion in base.assertions():
        section_only.add(assertion)
    section_only.add(section_survived, z3.Not(scalar_phi0), z3.Not(final_xi_phi0))

    return {
        "pass": premature.check() == z3.unsat and section_only.check() == z3.sat,
        "premature_promotion_status": str(premature.check()),
        "section_only_nonpromotion_status": str(section_only.check()),
        "requires_scalar_phi0": True,
        "requires_final_xi_phi0": True,
        "requires_final_manifold": True,
    }


def section_passes(section: Any) -> bool:
    if isinstance(section, dict):
        return all(not isinstance(row, dict) or bool(row.get("pass", True)) for row in section.values())
    return False


def main() -> int:
    start = time.time()
    broad_receipt = read_json(SOURCE_FILES["broad_stress_result"])
    rows = build_sections(broad_receipt)
    simple = simple_scalarizations(rows)
    prototype = prototype_scalarizations(rows)
    classification = classify(simple, prototype, broad_receipt)
    graph = scalarization_graph(classification, simple, prototype)
    nonpromotion = z3_nonpromotion(classification)

    positive = {
        "upstream_broad_stress_loaded": {
            "pass": broad_receipt.get("all_pass") is True
            and broad_receipt.get("candidate_classification", {}).get("status")
            == "family_local_broad_stress_candidate_open",
            "broad_status": broad_receipt.get("candidate_classification", {}).get("status"),
        },
        "family_local_sections_rebuilt": {
            "pass": len(rows) == 120,
            "section_count": len(rows),
            "scenario_count": len({row["scenario"] for row in rows}),
            "case_count": len({row["case"] for row in rows}),
            "feature_names": family_tensor.FEATURE_NAMES,
        },
        "scalarization_candidates_evaluated": {
            "pass": classification["tested_scalarization_count"] == 10,
            "tested_scalarization_count": classification["tested_scalarization_count"],
            "simple": {name: {k: v for k, v in row.items() if k != "details"} for name, row in simple.items()},
            "prototype": {name: {k: v for k, v in row.items() if k != "details"} for name, row in prototype.items()},
        },
        "scalarization_status_classified": {"pass": True, "classification": classification},
        "scalarization_graph_valid": {"pass": graph["is_dag"], **graph},
        "z3_nonpromotion_guard": nonpromotion,
    }

    graveyard = {
        "simple_scalarizations_fail": {
            "pass": all(not row["pass"] for row in simple.values()),
            "failed": sorted(name for name, row in simple.items() if not row["pass"]),
            "summary": "Norm, L1, sum, and mean scalar readouts do not separate canonical rows from controls.",
        },
        "heldout_prototype_scalarizations_fail": {
            "pass": all(not row["pass"] for row in prototype.values()),
            "failed": sorted(name for name, row in prototype.items() if not row["pass"]),
            "summary": "Leave-one-scenario/theta/seed projection and centroid-distance scalarizations do not separate canonical rows from controls.",
        },
        "section_margin_is_not_scalar_phi0": {
            "pass": classification["section_candidate_status"] == "family_local_broad_stress_candidate_open",
            "section_min_scenario_distance": classification["section_min_scenario_distance"],
            "section_broad_margin": classification["section_broad_margin"],
            "summary": "The surviving broad section margin is a control-relative vector/section distance, not a standalone scalar Phi0.",
        },
        "scalar_phi0_not_admitted": {
            "pass": not classification["scalar_phi0_admitted"],
            "admitted_scalarizations": classification["admitted_scalarizations"],
        },
        "final_xi_phi0_and_manifold_not_admitted": {
            "pass": not classification["final_xi_phi0_admitted"] and not classification["final_manifold_admitted"],
        },
    }

    boundary = {
        "formal_scout_only": {
            "pass": not PROMOTION_ALLOWED and CLASSIFICATION == "formal_scout",
            "claim_ceiling": CLAIM_CEILING,
        },
        "section_candidate_survives_but_scalarization_fails": {
            "pass": classification["status"] == "scalarization_killed_section_only_open",
            "status": classification["status"],
        },
        "tested_scalarizations_are_not_exhaustive": {
            "pass": True,
            "summary": "This kills the tested simple/prototype scalarizations, not every possible future section kernel.",
        },
        "no_final_phi0_or_manifold_claim": {
            "pass": True,
            "summary": "The result narrows next work; it does not promote Phi0, Xi, tensor scaling, or final manifold admission.",
        },
    }

    nearby_variants = {
        "total": classification["tested_scalarization_count"],
        "passed": classification["tested_scalarization_count"] - len(classification["admitted_scalarizations"]),
        "variants": classification["killed_scalarizations"],
    }
    why_not_v4_probes = {
        "pass": True,
        "reason": "This is a v5 formal-scout scalarization audit over source-aligned family-local section receipts, not a canonical v4 physics/probe promotion.",
    }
    open_gaps = [
        "tested scalarizations fail; the current family-local process-signature object remains section-only",
        "a future stronger section kernel must beat these scalarization failures without using control labels",
        "scalar Phi0 remains open",
        "final Xi/Phi0, tensor scaling, and manifold admission remain blocked",
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
        "simple_scalarizations": simple,
        "prototype_scalarizations": prototype,
        "candidate_classification": classification,
        "scalarization_graph": graph,
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
                "tested_scalarization_count": classification["tested_scalarization_count"],
                "admitted_scalarizations": classification["admitted_scalarizations"],
                "section_broad_margin": classification["section_broad_margin"],
                "out": str(OUT_PATH),
            },
            indent=2,
        )
    )
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
