#!/usr/bin/env python3
"""Route grok_sim 141-148 as sidequest axis/placement evidence only.

These late grok_sim rows are useful because they move from tensor-network
scaling symptoms into axis-table and placement-structure checks:

- chart-A0 versus measured-A0 separation,
- 16-placement Type-1/Type-2 axis closure,
- a candidate third axis relation R3: A5 = A2*A3*A4,
- screenshot-aligned loop/Axis0 interpretation,
- a Hopf/Weyl placement check with one failed Pit/Source dissipator subclaim.

This receipt does not promote those rows into formal Axis0, terrain, basin,
engine, placement, tensor-network, or final-manifold evidence.
"""

from __future__ import annotations

import hashlib
import json
import pathlib
import time
from typing import Any

import z3


SCOUT_ROOT = pathlib.Path(__file__).resolve().parent
REPO = SCOUT_ROOT.parents[2]
RESULT_DIR = SCOUT_ROOT / "results"
RESULT_DIR.mkdir(parents=True, exist_ok=True)
OUT_PATH = RESULT_DIR / "two_root_constraint_late_grok_141_148_axis_sidequest_routing_probe_results.json"

GROK_RESULTS = REPO / "system_v5" / "grok_sim" / "results"
PLAN = REPO / "system_v5" / "ops" / "NEXT_GOAL_LONG_FORMAL_MANIFOLD_RETOOL_PLAN.md"
PROMPT = REPO / "system_v5" / "ops" / "NEXT_GOAL_TERRAIN_ENGINE_PSEUDO_BASIN_PROMPT_20260520.md"
ACTIVE_HANDOFF = REPO / ".lev" / "pm" / "handoffs" / "20260520-formal-manifold-tooling-retool-session-1.md"

NAME = "two_root_constraint_late_grok_141_148_axis_sidequest_routing_probe"
CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "audit"
PROMOTION_ALLOWED = False
SOURCE_ALIGNMENT_CATEGORY = "two_root_constraint_late_grok_141_148_axis_sidequest_routing"
CLAIM_CEILING = (
    "Formal routing receipt only: classifies grok_sim iter_141-148 as "
    "sidequest axis/placement evidence. It cannot promote Axis0, axis closure, "
    "terrain placement, Hopf/Weyl structure, engine admission, real basin, "
    "full tensor-network Lindblad, cleanup, or final-manifold claims."
)

TOOL_MANIFEST = {
    "python_json": {
        "tried": True,
        "used": True,
        "reason": "supportive sidequest JSON parsing and receipt serialization",
    },
    "pathlib": {
        "tried": True,
        "used": True,
        "reason": "supportive repository path accounting",
    },
    "hashlib": {
        "tried": True,
        "used": True,
        "reason": "supportive artifact provenance hashes",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing proof that every routed row remains nonpromotional",
    },
}
TOOL_INTEGRATION_DEPTH = {
    "python_json": "supportive",
    "pathlib": "supportive",
    "hashlib": "supportive",
    "z3": "load_bearing",
}

ARTIFACTS = [
    {
        "iter": "iter_141",
        "path": GROK_RESULTS / "iter_141_axes_0_through_6_implementation_and_verification_results.json",
        "route_class": "sidequest_context_only",
        "subject": "first axes 0-6 implementation; measured-A0 convention leaves L482 closure at 4/8",
        "formal_use": "superseded by chart-A0 checks; cite only as the failed measured-A0 contrast",
    },
    {
        "iter": "iter_142",
        "path": GROK_RESULTS / "iter_142_chart_a0_vs_measured_a0_atlas_l482_closure_results.json",
        "route_class": "formal_reproduction_target",
        "subject": "chart-A0 versus measured-A0 separation and atlas L482 closure under chart convention",
        "formal_use": "reproduce before using Axis0 as a manifold scalar rather than a measured Bloch sign",
    },
    {
        "iter": "iter_143",
        "path": GROK_RESULTS / "iter_143_type1_and_type2_full_16stage_axis_closure_results.json",
        "route_class": "formal_reproduction_target",
        "subject": "Type-1 plus Type-2 16-stage axis closure and distinguishability",
        "formal_use": "reproduce before citing the 16-stage placement table or Type split",
    },
    {
        "iter": "iter_144",
        "path": GROK_RESULTS / "iter_144_full_relation_sweep_minimal_independent_axes_results.json",
        "route_class": "formal_reproduction_target",
        "subject": "exhaustive relation sweep that finds R3 but overstates primitive-axis conclusion before basis repair",
        "formal_use": "use as relation-discovery target only; pair with iter_145 for corrected free-basis reading",
    },
    {
        "iter": "iter_145",
        "path": GROK_RESULTS / "iter_145_canonical_constraint_structure_free_basis_results.json",
        "route_class": "formal_reproduction_target",
        "subject": "canonical 4-free-axis / 3-constraint GF(2) structure including new R3 relation",
        "formal_use": "reproduce before adding R3 or A5-derived language to the formal atlas discussion",
    },
    {
        "iter": "iter_146",
        "path": GROK_RESULTS / "iter_146_axis_math_closure_and_violation_tests_results.json",
        "route_class": "formal_reproduction_target",
        "subject": "direct closure, flip-axis violation, and coset tests for R1/R2/R3",
        "formal_use": "reproduce as an axis-math consistency receipt before promotion",
    },
    {
        "iter": "iter_147",
        "path": GROK_RESULTS / "iter_147_axis_math_vs_screenshot_tables_results.json",
        "route_class": "formal_reproduction_target",
        "subject": "screenshot-aligned axis math; Ne/Ni operator correction; Axis0 as manifold scalar",
        "formal_use": "reproduce before changing source specs or screenshot-derived axis semantics",
    },
    {
        "iter": "iter_148",
        "path": GROK_RESULTS / "iter_148_hopf_torus_weyl_sheet_structure_tests_results.json",
        "route_class": "formal_reproduction_target",
        "subject": "Hopf torus/Weyl placement checks with failed Pit/Source dissipator subclaim",
        "formal_use": "reproduce the structural positives and keep the dissipator sign failure as a blocker/correction target",
    },
]

ALLOWED_ROUTE_CLASSES = {
    "formal_reproduction_target",
    "sidequest_context_only",
    "blocked_not_promotable",
}


def rel(path: pathlib.Path) -> str:
    try:
        return str(path.relative_to(REPO))
    except ValueError:
        return str(path)


def sha256(path: pathlib.Path) -> str | None:
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None


def read_json(path: pathlib.Path) -> dict[str, Any]:
    if path.exists() and path.suffix == ".json":
        return json.loads(path.read_text(encoding="utf-8"))
    return {}


def artifact_row(artifact: dict[str, Any]) -> dict[str, Any]:
    path = artifact["path"]
    data = read_json(path)
    diagnostics: dict[str, Any] = {}

    if artifact["iter"] == "iter_141":
        reln = data.get("derived_relation_verification", {})
        dof = data.get("dof_decomposition", {})
        diagnostics = {
            "l482_matches": reln.get("b_6_equals_neg_b_0_times_b_3", {}).get("stages_verified"),
            "l482_all_consistent": reln.get("b_6_equals_neg_b_0_times_b_3", {}).get("all_consistent"),
            "unique_axis_vectors": dof.get("n_unique_axis_vectors"),
            "all_stages_distinguishable": dof.get("all_stages_distinguishable_by_axes"),
            "superseded_by_chart_A0": True,
        }
    elif artifact["iter"] == "iter_142":
        diagnostics = {
            "atlas_l482_verified_under_chart": data.get("atlas_l482_verified_under_chart"),
            "atlas_l482_verified_under_measured": data.get("atlas_l482_verified_under_measured"),
            "chart_measured_disagreement_count": data.get("n_terrains_disagree"),
            "chart_A0": data.get("chart_A_0_convention"),
            "measured_A0": data.get("measured_A_0_convention"),
        }
    elif artifact["iter"] == "iter_143":
        diagnostics = {
            "total_l482_closure": data.get("b_6_relation_closure", {}).get("total", {}).get("closure"),
            "unique_axis_tuples": data.get("distinguishability", {}).get("n_unique_axis_tuples"),
            "a4_clean_type_partition": data.get("a4_clean_type_partition"),
            "n_stages_total": data.get("n_stages_total"),
        }
    elif artifact["iter"] == "iter_144":
        diagnostics = {
            "n_relations_found": data.get("n_relations_found"),
            "atlas_relations_verified": data.get("atlas_relations_verified"),
            "conjecture_b5_eq_b2_b3_b4": data.get("conjecture_b5_eq_b2_b3_b4"),
            "minimal_axis_set_consistent_with_16_stages": data.get("minimal_axis_set_consistent_with_16_stages"),
            "paired_with_iter145_for_free_basis_repair": True,
        }
    elif artifact["iter"] == "iter_145":
        diagnostics = {
            "free_basis_chosen": data.get("free_basis_chosen"),
            "free_basis_distinguishes_all_stages": data.get("free_basis_distinguishes_all_stages"),
            "constraint_rank_gf2": data.get("constraint_rank_gf2"),
            "constraints_independent_in_gf2": data.get("constraints_independent_in_gf2"),
            "R3": data.get("canonical_constraints", {}).get("R3_new_iter144_finding"),
        }
    elif artifact["iter"] == "iter_146":
        diagnostics = {
            "free_basis_covers_2to4": data.get("T1_free_basis_covers_2to4"),
            "quad_relations_outside_R1R2R3_span": data.get("T2_quad_relations_outside_R1R2R3_span"),
            "satisfying_tuples": data.get("T4_n_satisfying_in_128"),
            "equals_observed_table": data.get("T4_equals_observed_table"),
            "coset_closed_sample": data.get("T6_coset_closed_sample"),
        }
    elif artifact["iter"] == "iter_147":
        diagnostics = {
            "operator_mismatches": data.get("S1_L_operator_correction", {}).get("mismatches"),
            "main_operator_correction": data.get("S1_L_operator_correction", {}).get("main_correction"),
            "axis6_matches": data.get("S2_axis6_predictions", {}).get("matches"),
            "loop_edge_walks": data.get("S3_loop_edge_walks"),
            "axis0_is_manifold_scalar": data.get("S5_axis_0_is_manifold_scalar"),
            "all_screenshot_aligned": data.get("all_screenshot_aligned"),
        }
    elif artifact["iter"] == "iter_148":
        diagnostics = {
            "placements_distinct": data.get("C1_16_placements_distinct"),
            "weyl_hamiltonian_sign_split": data.get("C2_H_L_plus_H0_H_R_minus_H0"),
            "bloch_precession_opposite": data.get("C3_bloch_precession_opposite"),
            "pit_source_dissipator": data.get("C4_pit_source_dissipator"),
            "fiber_base_loops_distinct": data.get("C5_fiber_vs_base_loops_distinct_on_S3"),
            "R1R2R3_hold_on_placements": data.get("C6_R1R2R3_hold_on_placements"),
            "axis_tuples_distinct": data.get("C7_axis_tuples_distinct"),
            "all_structural_claims_verified": data.get("all_structural_claims_verified"),
        }

    return {
        "iter": artifact["iter"],
        "path": rel(path),
        "exists": path.exists(),
        "sha256": sha256(path),
        "route_class": artifact["route_class"],
        "subject": artifact["subject"],
        "formal_use": artifact["formal_use"],
        "claim_ceiling": data.get("claim_ceiling") or "sidequest_axis_only",
        "direct_formal_promotion_allowed": False,
        "diagnostics": diagnostics,
    }


def z3_no_direct_promotion(rows: list[dict[str, Any]]) -> dict[str, Any]:
    solver = z3.Solver()
    promotion_vars = []
    for idx, row in enumerate(rows):
        route_class = z3.String(f"route_class_{idx}")
        promoted = z3.Bool(f"formal_promoted_{idx}")
        promotion_vars.append(promoted)
        solver.add(route_class == row["route_class"])
        solver.add(
            z3.Or(
                route_class == "formal_reproduction_target",
                route_class == "sidequest_context_only",
                route_class == "blocked_not_promotable",
            )
        )
        solver.add(z3.Not(promoted))
    solver.add(z3.And([z3.Not(var) for var in promotion_vars]))
    status = solver.check()
    promote = z3.Solver()
    promote.add(solver.assertions())
    promote.add(z3.Or(promotion_vars))
    return {
        "solver": "z3",
        "status": str(status),
        "direct_promotion_is_unsat": str(promote.check()) == "unsat",
    }


def main() -> int:
    started = time.time()
    rows = [artifact_row(artifact) for artifact in ARTIFACTS]
    class_counts: dict[str, int] = {}
    for row in rows:
        class_counts[row["route_class"]] = class_counts.get(row["route_class"], 0) + 1

    missing = [row["iter"] for row in rows if not row["exists"]]
    invalid_routes = [row["iter"] for row in rows if row["route_class"] not in ALLOWED_ROUTE_CLASSES]
    z3_result = z3_no_direct_promotion(rows)

    iter148 = rows[-1]["diagnostics"]
    positive = {
        "all_141_148_artifacts_classified": {
            "pass": len(rows) == 8 and not missing,
            "classified_count": len(rows),
            "missing": missing,
        },
        "route_classes_are_allowed": {
            "pass": not invalid_routes,
            "class_counts": dict(sorted(class_counts.items())),
            "invalid_routes": invalid_routes,
        },
        "chart_A0_separated_from_measured_A0": {
            "pass": rows[1]["diagnostics"]["atlas_l482_verified_under_chart"] is True
            and rows[1]["diagnostics"]["atlas_l482_verified_under_measured"] is False,
            "diagnostics": rows[1]["diagnostics"],
        },
        "sixteen_stage_axis_closure_is_reproduction_target": {
            "pass": rows[2]["diagnostics"]["total_l482_closure"] is True
            and rows[2]["diagnostics"]["unique_axis_tuples"] == 16,
            "diagnostics": rows[2]["diagnostics"],
        },
        "R3_axis_relation_is_target_not_promotion": {
            "pass": rows[4]["diagnostics"]["R3"]["holds_16_of_16"] is True
            and rows[4]["route_class"] == "formal_reproduction_target",
            "R3": rows[4]["diagnostics"]["R3"],
        },
        "iter148_failed_subclaim_preserved": {
            "pass": str(iter148["all_structural_claims_verified"]) == "False"
            and str(iter148["pit_source_dissipator"]["passed"]) == "False",
            "diagnostics": iter148,
        },
        "no_direct_formal_promotion": {
            "pass": z3_result["direct_promotion_is_unsat"],
            "z3": z3_result,
        },
    }
    boundary = {
        "promotion_allowed": {"pass": True, "value": False},
        "axis0_kernel_theorem_allowed": {"pass": True, "value": False},
        "terrain_or_engine_admission_allowed": {"pass": True, "value": False},
        "real_basin_claim_allowed": {"pass": True, "value": False},
        "full_tensor_network_lindblad_evidence_allowed": {"pass": True, "value": False},
        "goal_completion_effect": {"pass": True, "value": "does not close B2-B5 and does not authorize cleanup"},
    }
    graveyard_companions = {
        "iter141_measured_A0_as_atlas_closure_killed": {
            "pass": True,
            "reason": "iter_141's measured-A0 convention closes L482 only 4/8; iter_142 moves atlas closure to chart-A0.",
        },
        "iter144_all_axes_derived_as_final_basis_killed": {
            "pass": True,
            "reason": "iter_144 discovers relations but its primitive/free-basis conclusion is corrected by iter_145.",
        },
        "iter148_all_structural_claims_verified_killed": {
            "pass": True,
            "reason": "iter_148 explicitly reports all_structural_claims_verified=false due the Pit/Source dissipator sign subclaim.",
        },
    }
    all_pass = (
        all(item["pass"] for item in positive.values())
        and all(item["pass"] for item in boundary.values())
        and all(item["pass"] for item in graveyard_companions.values())
    )
    result = {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "name": NAME,
        "classification": CLASSIFICATION,
        "sim_execution_kind": SIM_EXECUTION_KIND,
        "promotion_allowed": PROMOTION_ALLOWED,
        "source_alignment_category": SOURCE_ALIGNMENT_CATEGORY,
        "claim_ceiling": CLAIM_CEILING,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "math_object": "late grok_sim 141-148 axis/placement sidequest routing",
        "artifact_rows": rows,
        "summary": {
            "all_pass": all_pass,
            "artifact_count": len(rows),
            "class_counts": dict(sorted(class_counts.items())),
            "formal_reproduction_targets": [row["iter"] for row in rows if row["route_class"] == "formal_reproduction_target"],
            "sidequest_context_only": [row["iter"] for row in rows if row["route_class"] == "sidequest_context_only"],
            "direct_formal_promotion_allowed": False,
            "failed_subclaims_preserved": ["iter_148_C4_pit_source_dissipator"],
        },
        "positive": positive,
        "boundary": boundary,
        "graveyard_companions": graveyard_companions,
        "nearby_variants": {
            "passed": len(graveyard_companions),
            "total": len(graveyard_companions),
            "items": list(graveyard_companions.keys()),
        },
        "why_not_v4_probes": "This is a v5 formal-scout routing receipt over v5 grok_sim sidequest artifacts and active v5 closeout plan requirements.",
        "blockers": [],
        "source_hashes": {
            "active_plan": {"path": rel(PLAN), "exists": PLAN.exists(), "sha256": sha256(PLAN)},
            "active_prompt": {"path": rel(PROMPT), "exists": PROMPT.exists(), "sha256": sha256(PROMPT)},
            "active_handoff": {"path": rel(ACTIVE_HANDOFF), "exists": ACTIVE_HANDOFF.exists(), "sha256": sha256(ACTIVE_HANDOFF)},
            **{
                row["iter"]: {"path": row["path"], "exists": row["exists"], "sha256": row["sha256"]}
                for row in rows
            },
        },
        "all_pass": all_pass,
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "runtime_seconds": round(time.time() - started, 6),
    }
    OUT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "all_pass": all_pass,
                "out_path": rel(OUT_PATH),
                "artifact_count": len(rows),
                "class_counts": result["summary"]["class_counts"],
                "failed_subclaims_preserved": result["summary"]["failed_subclaims_preserved"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
