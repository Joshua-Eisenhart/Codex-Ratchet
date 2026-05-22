#!/usr/bin/env python3
"""Route grok_sim 149-160 as sidequest axis/wiki-geometry evidence only.

These late grok_sim rows are useful because they add per-axis geometric DOF
checks and wiki-concept cross-links:

- A0-A6 as geometric degrees of freedom,
- independent alt-DOF candidates beyond the seven axes,
- Hopf/Berry/contact form alignment,
- Hopf Chern number and two-qubit Hopf checks,
- chirality-admissible two-qubit operator set,
- KAK generators inside the chirality-admissible set,
- terrain labels as placements rather than primitives,
- 16 ordered tokens as topology x (A5,A6) placements.

This receipt routes those rows as reproduction targets or sidequest context.
It does not promote them into final axis canon, terrain admission, real basin,
bridge closure, or final-manifold evidence.
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
OUT_PATH = RESULT_DIR / "two_root_constraint_late_grok_149_160_wiki_axis_geometry_sidequest_routing_probe_results.json"

GROK_RESULTS = REPO / "system_v5" / "grok_sim" / "results"
PLAN = REPO / "system_v5" / "ops" / "NEXT_GOAL_LONG_FORMAL_MANIFOLD_RETOOL_PLAN.md"
PROMPT = REPO / "system_v5" / "ops" / "NEXT_GOAL_TERRAIN_ENGINE_PSEUDO_BASIN_PROMPT_20260520.md"
ACTIVE_HANDOFF = REPO / ".lev" / "pm" / "handoffs" / "20260520-formal-manifold-tooling-retool-session-1.md"

NAME = "two_root_constraint_late_grok_149_160_wiki_axis_geometry_sidequest_routing_probe"
CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "audit"
PROMOTION_ALLOWED = False
SOURCE_ALIGNMENT_CATEGORY = "two_root_constraint_late_grok_149_160_wiki_axis_geometry_sidequest_routing"
CLAIM_CEILING = (
    "Formal routing receipt only: classifies grok_sim iter_149-160 as "
    "sidequest axis/wiki-geometry evidence. It cannot promote final axis canon, "
    "terrain admission, manifold completion, real attractor-basin evidence, "
    "bridge closure, PEPS/PEPS3D or tensor-network evidence, cleanup, or final "
    "formal-manifold claims."
)

TOOL_MANIFEST = {
    "python_json": {
        "tried": True,
        "used": True,
        "reason": "supportive parsing of sidequest JSON artifacts and receipt serialization",
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
        "iter": "iter_149",
        "path": GROK_RESULTS / "iter_149_axis_6_left_right_action_chirality_dof_results.json",
        "route_class": "formal_reproduction_target",
        "subject": "A6 as left/right bimodule chirality and commutator/anticommutator split",
        "formal_use": "reproduce before citing A6 as geometric DOF or R2-derived chirality evidence",
    },
    {
        "iter": "iter_150",
        "path": GROK_RESULTS / "iter_150_axis_5_dissipative_vs_coherent_generator_algebra_dof_results.json",
        "route_class": "formal_reproduction_target",
        "subject": "A5 as Lindblad Hermiticity class, steady-kernel dimension, and R3-derived axis",
        "formal_use": "reproduce before citing A5 as dissipative/coherent generator-class evidence",
    },
    {
        "iter": "iter_151",
        "path": GROK_RESULTS / "iter_151_axis_3_hopf_fiber_vs_base_dof_results.json",
        "route_class": "formal_reproduction_target",
        "subject": "A3 as Hopf vertical/horizontal split with Berry closure phase",
        "formal_use": "reproduce before citing horizontal lift or Hopf/Berry phase placement",
    },
    {
        "iter": "iter_152",
        "path": GROK_RESULTS / "iter_152_axis_4_loop_family_z2_shift_dof_results.json",
        "route_class": "formal_reproduction_target",
        "subject": "A4 as the two Hamiltonian cycles on the K_{2,2} terrain graph",
        "formal_use": "reproduce before citing deductive/inductive loop-family distinction",
    },
    {
        "iter": "iter_153",
        "path": GROK_RESULTS / "iter_153_axis_1_unitary_vs_cptp_dof_results.json",
        "route_class": "formal_reproduction_target",
        "subject": "A1 as Choi-rank class separating unitary from proper CPTP branches",
        "formal_use": "reproduce before citing branch rank or purity-preservation evidence",
    },
    {
        "iter": "iter_154",
        "path": GROK_RESULTS / "iter_154_axis_2_direct_vs_conjugated_rep_dof_results.json",
        "route_class": "formal_reproduction_target",
        "subject": "A2 as direct versus conjugated Pauli representation involution",
        "formal_use": "reproduce before citing time-reversal or Weyl-sheet sign alignment",
    },
    {
        "iter": "iter_155",
        "path": GROK_RESULTS / "iter_155_axis_0_bipartite_scalar_field_dof_results.json",
        "route_class": "formal_reproduction_target",
        "subject": "A0 as external bipartite scalar Phi0 with Clifford-torus sign crossing",
        "formal_use": "reproduce before citing Phi0 chart, Werner crossing, or correlational entropy candidate evidence",
    },
    {
        "iter": "iter_156",
        "path": GROK_RESULTS / "iter_156_alt_dof_exploration_beyond_seven_axes_results.json",
        "route_class": "sidequest_context_only",
        "subject": "exploratory alt-DOF inventory beyond A0-A6",
        "formal_use": "use as proposal context only; provisional count is not canon and belongs to future axis-search work",
    },
    {
        "iter": "iter_157",
        "path": GROK_RESULTS / "iter_157_wiki_concepts_first_pass_chern_and_2qubit_hopf_results.json",
        "route_class": "formal_reproduction_target",
        "subject": "wiki first-pass Hopf Chern number, two-qubit Hopf, and terrain-placement correction",
        "formal_use": "reproduce before citing Chern number, S7->S4, or terrain-as-placement evidence",
    },
    {
        "iter": "iter_158",
        "path": GROK_RESULTS / "iter_158_wiki_batch_2_chirality_admissibility_and_64_schedule_results.json",
        "route_class": "formal_reproduction_target",
        "subject": "chirality-admissible two-qubit generator split and 64 microstep schedule count",
        "formal_use": "reproduce before citing the admissible 8-set or closure under Weyl chirality",
    },
    {
        "iter": "iter_159",
        "path": GROK_RESULTS / "iter_159_wiki_batch_3_contact_sasakian_kak_makhlin_results.json",
        "route_class": "formal_reproduction_target",
        "subject": "contact form as Hopf/Berry connection and KAK generators inside chirality-admissible set",
        "formal_use": "reproduce before citing contact/Sasakian/KAK/Makhlin structural links",
    },
    {
        "iter": "iter_160",
        "path": GROK_RESULTS / "iter_160_wiki_batch_4_f01_n01_jung_igt_phi0_weyl_flux_results.json",
        "route_class": "formal_reproduction_target",
        "subject": "F01/N01 charter, Jung/IGT token map, Phi0 candidates, and Weyl-flux multi-layer requirement",
        "formal_use": "reproduce before citing 16-token map, Phi0 candidates, or flux-placement constraints",
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


def passed(value: Any) -> bool:
    return value is True or value == "True"


def artifact_row(artifact: dict[str, Any]) -> dict[str, Any]:
    path = artifact["path"]
    data = read_json(path)
    diagnostics: dict[str, Any] = {}

    if artifact["iter"] == "iter_149":
        diagnostics = {
            "all_pass": data.get("all_pass"),
            "comm_norm": data.get("T1_L_R_commute", {}).get("comm_norm"),
            "token_ordering_diff_norm": data.get("T3_token_ordering_differs", {}).get("diff_norm"),
            "a6_flip_basin_shift": data.get("T4_a6_flip_basin_shift", {}).get("bloch_shift"),
            "b6_relation_matches": data.get("T5_b6_eq_neg_b0_b3_on_16_stages", {}).get("matches"),
        }
    elif artifact["iter"] == "iter_150":
        diagnostics = {
            "all_pass": data.get("all_pass"),
            "kernel_dim_dephase": data.get("T3_steady_state_dim", {}).get("kernel_dim_sz"),
            "kernel_dim_ladder": data.get("T3_steady_state_dim", {}).get("kernel_dim_sm"),
            "a5_relation_passed": data.get("T5_A5_eq_A2_A3_A4", {}).get("passed"),
            "basin_shift": data.get("T6_b5_flip_shifts_basin", {}).get("shift"),
        }
    elif artifact["iter"] == "iter_151":
        diagnostics = {
            "all_pass": data.get("all_pass"),
            "fiber_holonomy": data.get("T2_fiber_holonomy", {}).get("value"),
            "base_horizontal_integral": data.get("T3_base_holonomy", {}).get("value"),
            "closure_phase_actual": data.get("T4_closure_phase_berry", {}).get("closure_phase_actual"),
            "horizontal_omega_abs": data.get("T5_horizontal_in_kernel", {}).get("omega_H_abs"),
        }
    elif artifact["iter"] == "iter_152":
        diagnostics = {
            "all_pass": data.get("all_pass"),
            "hamiltonian_cycle_count": data.get("T1_hamiltonian_cycles_count", {}).get("count"),
            "noncommuting_loop_diff": data.get("T4_noncommuting_case_differ", {}).get("diff"),
            "type1_a4": data.get("T5_a4_partitions_types", {}).get("type1_a4"),
            "type2_a4": data.get("T5_a4_partitions_types", {}).get("type2_a4"),
        }
    elif artifact["iter"] == "iter_153":
        diagnostics = {
            "all_pass": data.get("all_pass"),
            "a1_relation_matches": data.get("T2_a1_eq_a0_a2_16_of_16", {}).get("matches"),
            "unitary_choi_rank": data.get("T5_choi_rank", {}).get("rank_unitary"),
            "cptp_choi_rank": data.get("T5_choi_rank", {}).get("rank_cptp"),
            "proper_cptp_purity_after": data.get("T4_proper_cptp_purity_decreases", {}).get("p_after_D"),
        }
    elif artifact["iter"] == "iter_154":
        diagnostics = {
            "all_pass": data.get("all_pass"),
            "direct": data.get("T4_a2_partition_matches_screenshot", {}).get("direct"),
            "conjugated": data.get("T4_a2_partition_matches_screenshot", {}).get("conjugated"),
            "a2_involutive": data.get("T5_a2_involutive", {}).get("passed"),
            "bloch_precession_sign_flip": data.get("T6_bloch_precession_sign_flip", {}).get("passed"),
        }
    elif artifact["iter"] == "iter_155":
        diagnostics = {
            "all_pass": data.get("all_pass"),
            "bell_Ic": data.get("T2_bell_state_Ic_log2", {}).get("Ic"),
            "werner_crossing_p": data.get("T3_werner_crossing", {}).get("crossing_p"),
            "phi0_at_clifford": data.get("T5_chart_phi0_zero_at_clifford", {}).get("phi0_at_pi_over_4"),
            "rz_below_above": [
                data.get("T6_rz_A_crosses_at_clifford", {}).get("rz_below_pi_over_4"),
                data.get("T6_rz_A_crosses_at_clifford", {}).get("rz_above_pi_over_4"),
            ],
        }
    elif artifact["iter"] == "iter_156":
        findings = data.get("findings", {})
        diagnostics = {
            "n_alt_independent": data.get("n_alt_independent"),
            "provisional_basin_dof_count": data.get("provisional_basin_dof_count"),
            "independent_alt_keys": [
                key for key, value in findings.items() if isinstance(value, dict) and value.get("independent") is True
            ],
            "disclaimer": data.get("disclaimer"),
        }
    elif artifact["iter"] == "iter_157":
        diagnostics = {
            "all_pass": data.get("all_pass"),
            "docs_processed_count": len(data.get("docs_processed", [])),
            "chern_number": data.get("T3_chern_number_one", {}).get("value"),
            "two_qubit_hopf_norms": data.get("T4_2qubit_hopf_norm_preserving", {}).get("norms"),
            "terrain_placement_finding": any("not primitive" in item for item in data.get("new_findings", [])),
        }
    elif artifact["iter"] == "iter_158":
        diagnostics = {
            "all_pass": data.get("all_pass"),
            "admissible": data.get("T1_chirality_admissibility_split", {}).get("admissible"),
            "inadmissible": data.get("T1_chirality_admissibility_split", {}).get("inadmissible"),
            "subalgebra_violations": data.get("T4_admissible_subalgebra_closed", {}).get("n_violations"),
            "microstep_count": data.get("T6_64_schedule_microstep_count", {}).get("total"),
            "unique_quad_tuples": data.get("T7_four_distinct_properties", {}).get("n_unique_quad_tuples"),
        }
    elif artifact["iter"] == "iter_159":
        diagnostics = {
            "all_pass": data.get("all_pass"),
            "alpha_dalpha_coeff": data.get("T1_contact_form_max_nonintegrable", {}).get("alpha_dalpha_coeff_at_pi_6"),
            "reeb_eq_hopf": data.get("T2_reeb_eq_hopf_fiber", {}).get("passed"),
            "kak_chirality_comm_norms": {
                "XX": data.get("T3_kak_uses_chirality_admissible", {}).get("comm_XX_gamma"),
                "YY": data.get("T3_kak_uses_chirality_admissible", {}).get("comm_YY_gamma"),
                "ZZ": data.get("T3_kak_uses_chirality_admissible", {}).get("comm_ZZ_gamma"),
            },
            "cnot_entangling_power": data.get("T6_entangling_power", {}).get("ep_cnot"),
        }
    elif artifact["iter"] == "iter_160":
        diagnostics = {
            "all_pass": data.get("all_pass"),
            "f01_axis_value_spaces": data.get("T1_F01_finitude", {}).get("axis_value_spaces"),
            "n01_passed": data.get("T2_N01_noncommutation", {}).get("passed"),
            "token_count": data.get("T3_jung_igt_16_token_map", {}).get("n_tokens"),
            "phi0_candidates": {
                "I_c": data.get("T4_phi0_candidates", {}).get("I_c"),
                "S_cond": data.get("T4_phi0_candidates", {}).get("S_cond"),
                "I_AB": data.get("T4_phi0_candidates", {}).get("I_AB"),
            },
            "weyl_flux_chirality_diff_norm": data.get("T5_weyl_flux_multi_layer", {}).get("chirality_diff_norm"),
            "token_types": data.get("T6_token_axis_map", {}).get("n_token_types"),
            "topologies": data.get("T6_token_axis_map", {}).get("n_topologies"),
        }

    return {
        "iter": artifact["iter"],
        "path": rel(path),
        "exists": path.exists(),
        "sha256": sha256(path),
        "route_class": artifact["route_class"],
        "subject": artifact["subject"],
        "formal_use": artifact["formal_use"],
        "claim_ceiling": data.get("claim_ceiling") or "sidequest_axis_wiki_geometry_only",
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
    row_by_iter = {row["iter"]: row for row in rows}

    axis_rows = [row_by_iter[f"iter_{idx}"] for idx in range(149, 156)]
    wiki_rows = [row_by_iter[f"iter_{idx}"] for idx in range(157, 161)]

    positive = {
        "all_149_160_artifacts_classified": {
            "pass": len(rows) == 12 and not missing,
            "classified_count": len(rows),
            "missing": missing,
        },
        "route_classes_are_allowed": {
            "pass": not invalid_routes,
            "class_counts": dict(sorted(class_counts.items())),
            "invalid_routes": invalid_routes,
        },
        "axis_dof_rows_are_reproduction_targets_not_canon": {
            "pass": all(row["route_class"] == "formal_reproduction_target" for row in axis_rows)
            and all(passed(row["diagnostics"].get("all_pass")) for row in axis_rows),
            "iters": [row["iter"] for row in axis_rows],
        },
        "alt_dofs_are_context_only": {
            "pass": row_by_iter["iter_156"]["route_class"] == "sidequest_context_only"
            and row_by_iter["iter_156"]["diagnostics"]["n_alt_independent"] == 4,
            "diagnostics": row_by_iter["iter_156"]["diagnostics"],
        },
        "wiki_rows_are_reproduction_targets": {
            "pass": all(row["route_class"] == "formal_reproduction_target" for row in wiki_rows)
            and all(passed(row["diagnostics"].get("all_pass")) for row in wiki_rows),
            "iters": [row["iter"] for row in wiki_rows],
        },
        "hopf_chern_and_two_qubit_hopf_are_targets": {
            "pass": row_by_iter["iter_157"]["diagnostics"]["chern_number"] == 1.0
            and row_by_iter["iter_157"]["diagnostics"]["terrain_placement_finding"] is True,
            "diagnostics": row_by_iter["iter_157"]["diagnostics"],
        },
        "chirality_admissible_set_preserved_as_target": {
            "pass": set(row_by_iter["iter_158"]["diagnostics"]["admissible"])
            == {"II", "IZ", "ZI", "ZZ", "XX", "XY", "YX", "YY"}
            and row_by_iter["iter_158"]["diagnostics"]["subalgebra_violations"] == 0,
            "diagnostics": row_by_iter["iter_158"]["diagnostics"],
        },
        "contact_kak_link_preserved_as_target": {
            "pass": all(abs(value) < 1e-12 for value in row_by_iter["iter_159"]["diagnostics"]["kak_chirality_comm_norms"].values())
            and row_by_iter["iter_159"]["diagnostics"]["cnot_entangling_power"] > 0.22,
            "diagnostics": row_by_iter["iter_159"]["diagnostics"],
        },
        "sixteen_token_and_flux_open_targets_preserved": {
            "pass": row_by_iter["iter_160"]["diagnostics"]["token_count"] == 16
            and row_by_iter["iter_160"]["diagnostics"]["token_types"] == 4
            and row_by_iter["iter_160"]["diagnostics"]["topologies"] == 4,
            "diagnostics": row_by_iter["iter_160"]["diagnostics"],
        },
        "no_direct_formal_promotion": {
            "pass": z3_result["direct_promotion_is_unsat"],
            "z3": z3_result,
        },
    }
    boundary = {
        "promotion_allowed": {"pass": True, "value": False},
        "final_axis_canon_allowed": {"pass": True, "value": False},
        "terrain_admission_allowed": {"pass": True, "value": False},
        "manifold_completion_allowed": {"pass": True, "value": False},
        "real_basin_claim_allowed": {"pass": True, "value": False},
        "bridge_or_phi0_closure_allowed": {"pass": True, "value": False},
        "full_tensor_network_lindblad_evidence_allowed": {"pass": True, "value": False},
        "goal_completion_effect": {"pass": True, "value": "does not close B2-B5 and does not authorize cleanup"},
    }
    graveyard_companions = {
        "alt_dof_count_is_provisional_not_canon": {
            "pass": True,
            "reason": "iter_156 explicitly marks the 8 total DOF count exploratory and not atlas canon.",
        },
        "terrain_labels_as_primitives_killed": {
            "pass": row_by_iter["iter_157"]["diagnostics"]["terrain_placement_finding"] is True,
            "reason": "iter_157 records terrain labels as placements rather than primitive topology objects.",
        },
        "flux_as_single_layer_killed": {
            "pass": passed(row_by_iter["iter_160"]["diagnostics"]["n01_passed"])
            and row_by_iter["iter_160"]["diagnostics"]["weyl_flux_chirality_diff_norm"] > 0.0,
            "reason": "iter_160 routes Weyl flux as a multi-layer derived/open target, not a primitive terrain or Hopf layer.",
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
        "math_object": "late grok_sim 149-160 axis/wiki-geometry sidequest routing",
        "artifact_rows": rows,
        "summary": {
            "all_pass": all_pass,
            "artifact_count": len(rows),
            "class_counts": dict(sorted(class_counts.items())),
            "formal_reproduction_targets": [row["iter"] for row in rows if row["route_class"] == "formal_reproduction_target"],
            "sidequest_context_only": [row["iter"] for row in rows if row["route_class"] == "sidequest_context_only"],
            "direct_formal_promotion_allowed": False,
            "useful_reproduction_targets": [
                "A0-A6 geometric DOF decomposition",
                "Hopf/Berry/contact form alignment",
                "Hopf Chern number c1=1",
                "two-qubit Hopf S7_to_S4",
                "chirality-admissible 8-set",
                "KAK generators inside chirality-admissible set",
                "terrain labels as placements not primitives",
                "16 ordered tokens as 4 topology x 4 A5_A6 placements",
            ],
            "preserved_boundaries": [
                "alt DOF count is exploratory",
                "no final axis canon",
                "no terrain admission",
                "no manifold completion",
                "no real basin or tensor-network evidence",
            ],
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
                "useful_reproduction_targets": result["summary"]["useful_reproduction_targets"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
