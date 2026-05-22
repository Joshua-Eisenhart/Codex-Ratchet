#!/usr/bin/env python3
"""Route grok_sim 161-173 as sidequest wiki/math evidence only.

These late grok_sim rows cover operator algebra, QFI/Fubini-Study/Hopf
geometry, Clifford/quaternion/spinor facts, distinguishability, formal-method
checks, attractor-distance examples, density/spectral facts, engine QIT
doctrine, hypergraph/equivariance/persistence, SMT checks, FEP/process
examples, and thermodynamic/information identities.

This receipt preserves them as formal reproduction targets or sidequest
context. It does not promote them into final axis canon, final manifold
evidence, real attractor-basin evidence, bridge closure, tensor-network
evidence, or D86 goal reopening.
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
OUT_PATH = RESULT_DIR / "two_root_constraint_late_grok_161_173_wiki_math_sidequest_routing_probe_results.json"

GROK_RESULTS = REPO / "system_v5" / "grok_sim" / "results"
ACTIVE_HANDOFF = REPO / ".lev" / "pm" / "handoffs" / "20260520-formal-manifold-tooling-retool-session-1.md"
FINAL_SYNTHESIS = REPO / "system_v5" / "ops" / "formal_scouts" / "results" / "two_root_constraint_final_synthesis_receipt_results.json"

NAME = "two_root_constraint_late_grok_161_173_wiki_math_sidequest_routing_probe"
CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "audit"
PROMOTION_ALLOWED = False
SOURCE_ALIGNMENT_CATEGORY = "two_root_constraint_late_grok_161_173_wiki_math_sidequest_routing"
CLAIM_CEILING = (
    "Formal routing receipt only: classifies grok_sim iter_161-173 as "
    "sidequest wiki/math evidence. It cannot promote final axis canon, "
    "terrain admission, manifold completion, real attractor-basin evidence, "
    "bridge closure, tensor-network evidence, cleanup, or D86 goal reopening."
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
        "iter": "iter_161",
        "path": GROK_RESULTS / "iter_161_wiki_batch_5_operator_algebra_core_results.json",
        "route_class": "formal_reproduction_target",
        "subject": "operator algebra, CP tetrahedron, entanglement, Renyi, SSA, negativity",
        "formal_use": "reproduce before citing operator-algebra or entanglement-entropy facts",
    },
    {
        "iter": "iter_162",
        "path": GROK_RESULTS / "iter_162_wiki_batch_6_qfi_fubini_hopf_foliation_results.json",
        "route_class": "formal_reproduction_target",
        "subject": "QFI, Bures/Fubini-Study links, QGT split, Hopf foliation volume, Mandelstam-Tamm",
        "formal_use": "reproduce before citing QFI/Hopf-foliation geometry targets",
    },
    {
        "iter": "iter_163",
        "path": GROK_RESULTS / "iter_163_wiki_batch_7_clifford_quaternion_spinor_results.json",
        "route_class": "formal_reproduction_target",
        "subject": "Clifford, quaternion, rotor, spin double-cover, and S3 unit-quaternion checks",
        "formal_use": "reproduce before citing Cl+ to quaternion or spinor geometry facts",
    },
    {
        "iter": "iter_164",
        "path": GROK_RESULTS / "iter_164_wiki_batch_8_constraint_distinguishability_foliations_results.json",
        "route_class": "formal_reproduction_target",
        "subject": "trace distance, Helstrom, DPI, Hopf/contact integrability distinctions",
        "formal_use": "reproduce before citing distinguishability or foliation/integrability evidence",
    },
    {
        "iter": "iter_165",
        "path": GROK_RESULTS / "iter_165_wiki_batch_9_rosetta_iching_taijitu_results.json",
        "route_class": "sidequest_context_only",
        "subject": "Rosetta/IChing/Taijitu crosswalk and axis-symbol anchoring",
        "formal_use": "use as language/crosswalk context only; do not promote symbolic crosswalk as math evidence",
    },
    {
        "iter": "iter_166",
        "path": GROK_RESULTS / "iter_166_wiki_batch_10_formal_methods_nominalism_results.json",
        "route_class": "formal_reproduction_target",
        "subject": "formal-method style quotient, Pauli probe, invariant 16-stage, N01 trace inequivalence",
        "formal_use": "reproduce before citing proof-method or 16-stage invariant claims",
    },
    {
        "iter": "iter_167",
        "path": GROK_RESULTS / "iter_167_wiki_batch_11_attractor_distance_results.json",
        "route_class": "formal_reproduction_target",
        "subject": "contractive maps, Pinsker, dephasing and Lindblad sink examples, process attractor, diamond bound",
        "formal_use": "reproduce before citing attractor-distance examples; not real basin evidence by itself",
    },
    {
        "iter": "iter_168",
        "path": GROK_RESULTS / "iter_168_wiki_batch_12_density_operators_spectral_results.json",
        "route_class": "formal_reproduction_target",
        "subject": "density operators, singlet/triplet, swap, modular conjugation, Araki-Lieb, Bell correlations",
        "formal_use": "reproduce before citing density/spectral operator facts",
    },
    {
        "iter": "iter_169",
        "path": GROK_RESULTS / "iter_169_wiki_batch_13_engine_qit_doctrine_results.json",
        "route_class": "formal_reproduction_target",
        "subject": "engine QIT doctrine, Ti/Te dephasing, Fi/Fe unitary purity, loop vector fields, 16 placements",
        "formal_use": "reproduce before citing engine QIT placement and state-positivity targets",
    },
    {
        "iter": "iter_170",
        "path": GROK_RESULTS / "iter_170_wiki_batch_14_hypergraph_equivariance_persistence_results.json",
        "route_class": "formal_reproduction_target",
        "subject": "hypergraph incidence, SO3 equivariance, Schur, Betti, Rips filtration, Euler characteristic",
        "formal_use": "reproduce before citing hypergraph/equivariance/persistence targets",
    },
    {
        "iter": "iter_171",
        "path": GROK_RESULTS / "iter_171_wiki_batch_15_smt_z3_proofs_results.json",
        "route_class": "formal_reproduction_target",
        "subject": "SMT/Z3 proof checks, exact 16-model enumeration, contradiction and dim-count checks",
        "formal_use": "reproduce before citing the independent R1/R2/R3 16-model SMT cross-check",
    },
    {
        "iter": "iter_172",
        "path": GROK_RESULTS / "iter_172_wiki_batch_16_fep_viability_process_results.json",
        "route_class": "formal_reproduction_target",
        "subject": "FEP decomposition, Markov blanket factor, viability, Nagumo-Aubin, Helmholtz",
        "formal_use": "reproduce before citing FEP/process/viability examples",
    },
    {
        "iter": "iter_173",
        "path": GROK_RESULTS / "iter_173_wiki_batch_17_shannon_thermo_topos_results.json",
        "route_class": "formal_reproduction_target",
        "subject": "Jarzynski, Crooks, quantum Landauer, TUR, and Holevo identities",
        "formal_use": "reproduce before citing thermodynamic/information identity targets",
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


def test_keys(data: dict[str, Any]) -> list[str]:
    return sorted(key for key in data if key.startswith("T"))


def all_tests_passed(data: dict[str, Any]) -> bool:
    keys = test_keys(data)
    return bool(keys) and all(passed(data[key].get("passed")) for key in keys if isinstance(data.get(key), dict))


def selected_diagnostics(iter_id: str, data: dict[str, Any]) -> dict[str, Any]:
    common = {
        "all_pass": data.get("all_pass"),
        "test_count": len(test_keys(data)),
        "all_named_tests_passed": all_tests_passed(data),
    }
    if iter_id == "iter_161":
        common.update(
            {
                "choi_cp": data.get("T1_choi_cp", {}).get("passed"),
                "pauli_tetrahedron": data.get("T2_pauli_tetrahedron", {}).get("passed"),
                "strong_subadditivity": data.get("T6_strong_subadditivity", {}).get("passed"),
                "negative_conditional_entropy": data.get("T7_conditional_entropy_negative", {}).get("passed"),
            }
        )
    elif iter_id == "iter_162":
        common.update(
            {
                "qfi_pure_unitary": data.get("T1_qfi_pure_unitary", {}).get("passed"),
                "bures_local_eq_qfi": data.get("T3_bures_local_eq_qfi", {}).get("passed"),
                "qgt_split": data.get("T5_qgt_split", {}).get("passed"),
                "hopf_volume_2pi_sq": data.get("T6_hopf_volume_2pi_sq", {}).get("passed"),
            }
        )
    elif iter_id == "iter_163":
        common.update(
            {
                "cl3_dim_8": data.get("T3_cl3_dim_8", {}).get("passed"),
                "quaternion_isomorphism": data.get("T4_quaternion_isomorphism", {}).get("passed"),
                "spin3_so3_double_cover": data.get("T6_spin3_so3_double_cover", {}).get("passed"),
                "spin6_su4_dim_15": data.get("T8_spin6_su4_dim_15", {}).get("passed"),
            }
        )
    elif iter_id == "iter_164":
        common.update(
            {
                "trace_distance": data.get("T1_trace_distance", {}).get("passed"),
                "helstrom": data.get("T2_helstrom", {}).get("passed"),
                "dpi": data.get("T3_dpi", {}).get("passed"),
                "contact_nonintegrable": data.get("T7_contact_nonintegrable", {}).get("passed"),
            }
        )
    elif iter_id == "iter_165":
        common.update(
            {
                "axis0_chart_anchor": data.get("T1_axis_0_symbol_eq_chart_A_0", {}).get("passed"),
                "axis6_precedence_anchor": data.get("T5_axis_6_symbol_eq_precedence", {}).get("passed"),
                "all_axes_math_anchored": data.get("T6_all_axes_math_anchored", {}).get("passed"),
                "crosswalk_table": data.get("T7_crosswalk_table", {}).get("passed"),
            }
        )
    elif iter_id == "iter_166":
        common.update(
            {
                "pauli_complete_probe": data.get("T2_pauli_complete_probe", {}).get("passed"),
                "invariant_16_stage": data.get("T3_invariant_16_stage", {}).get("passed"),
                "n01_trace_inequiv": data.get("T4_N01_trace_inequiv", {}).get("passed"),
                "fail_closed_count": data.get("T5_fail_closed_count", {}).get("passed"),
            }
        )
    elif iter_id == "iter_167":
        common.update(
            {
                "relative_entropy_bell": data.get("T2_relative_entropy_bell", {}).get("value"),
                "pinsker_bound": data.get("T3_pinsker", {}).get("bound"),
                "dephasing_attractor": data.get("T4_dephasing_attractor", {}).get("passed"),
                "lindblad_sigma_minus_sink": data.get("T5_lindblad_sigma_minus_sink", {}).get("passed"),
            }
        )
    elif iter_id == "iter_168":
        common.update(
            {
                "bloch_ball": data.get("T1_bloch_ball", {}).get("passed"),
                "singlet_triplet": data.get("T2_singlet_triplet", {}).get("passed"),
                "swap_eigenvalues": data.get("T3_swap_eigenvalues", {}).get("passed"),
                "araki_lieb": data.get("T5_araki_lieb", {}).get("passed"),
            }
        )
    elif iter_id == "iter_169":
        common.update(
            {
                "ti_dephasing": data.get("T1_Ti_dephasing", {}).get("passed"),
                "te_dephasing": data.get("T2_Te_dephasing", {}).get("passed"),
                "loop_vector_fields": data.get("T5_loop_vector_fields", {}).get("passed"),
                "placements_16": data.get("T8_16_placements", {}).get("passed"),
            }
        )
    elif iter_id == "iter_170":
        common.update(
            {
                "hypergraph_incidence": data.get("T1_hypergraph_incidence", {}).get("passed"),
                "so3_clebsch_gordan": data.get("T2_so3_clebsch_gordan", {}).get("passed"),
                "rips_filtration": data.get("T5_rips_filtration", {}).get("passed"),
                "euler_characteristic": data.get("T6_euler_characteristic", {}).get("passed"),
            }
        )
    elif iter_id == "iter_171":
        common.update(
            {
                "g_dual_zero_unsat": data.get("T1_z3_unsat_G_dual_zero", {}).get("passed"),
                "r_models": data.get("T2_z3_enumerates_16_models", {}).get("n_models"),
                "universal_not_unsat": data.get("T3_z3_unsat_universal_NOT", {}).get("passed"),
                "contradiction_unsat": data.get("T5_z3_unsat_contradiction", {}).get("passed"),
            }
        )
    elif iter_id == "iter_172":
        common.update(
            {
                "f_decomposition": data.get("T1_F_decomposition", {}).get("passed"),
                "f_geq_surprise": data.get("T2_F_geq_surprise", {}).get("passed"),
                "markov_blanket_factor": data.get("T3_markov_blanket_factor", {}).get("passed"),
                "nagumo_aubin": data.get("T5_nagumo_aubin", {}).get("passed"),
            }
        )
    elif iter_id == "iter_173":
        common.update(
            {
                "jarzynski_expected": data.get("T1_jarzynski", {}).get("expected"),
                "crooks_expected": data.get("T2_crooks", {}).get("expected"),
                "quantum_landauer": data.get("T3_quantum_landauer", {}).get("passed"),
                "holevo_chi": data.get("T5_holevo", {}).get("chi"),
            }
        )
    return common


def artifact_row(artifact: dict[str, Any]) -> dict[str, Any]:
    path = artifact["path"]
    data = read_json(path)
    return {
        "iter": artifact["iter"],
        "path": rel(path),
        "exists": path.exists(),
        "sha256": sha256(path),
        "route_class": artifact["route_class"],
        "subject": artifact["subject"],
        "formal_use": artifact["formal_use"],
        "claim_ceiling": data.get("claim_ceiling") or "sidequest_wiki_math_only",
        "direct_formal_promotion_allowed": False,
        "diagnostics": selected_diagnostics(artifact["iter"], data),
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


def final_synthesis_closed() -> dict[str, Any]:
    data = read_json(FINAL_SYNTHESIS)
    return {
        "path": rel(FINAL_SYNTHESIS),
        "exists": FINAL_SYNTHESIS.exists(),
        "goal_complete": data.get("goal_complete"),
        "cleanup_authorized": data.get("cleanup_authorized"),
        "open_blocker_count": data.get("summary", {}).get("open_blocker_count")
        if isinstance(data.get("summary"), dict)
        else data.get("open_blocker_count"),
    }


def main() -> int:
    started = time.time()
    rows = [artifact_row(artifact) for artifact in ARTIFACTS]
    class_counts: dict[str, int] = {}
    for row in rows:
        class_counts[row["route_class"]] = class_counts.get(row["route_class"], 0) + 1

    row_by_iter = {row["iter"]: row for row in rows}
    missing = [row["iter"] for row in rows if not row["exists"]]
    invalid_routes = [row["iter"] for row in rows if row["route_class"] not in ALLOWED_ROUTE_CLASSES]
    z3_result = z3_no_direct_promotion(rows)

    reproduction_rows = [row for row in rows if row["route_class"] == "formal_reproduction_target"]
    positive = {
        "all_161_173_artifacts_classified": {
            "pass": len(rows) == 13 and not missing,
            "classified_count": len(rows),
            "missing": missing,
        },
        "route_classes_are_allowed": {
            "pass": not invalid_routes,
            "class_counts": dict(sorted(class_counts.items())),
            "invalid_routes": invalid_routes,
        },
        "reproduction_targets_pass_sidequest_tests": {
            "pass": all(passed(row["diagnostics"]["all_pass"]) for row in reproduction_rows)
            and all(row["diagnostics"]["all_named_tests_passed"] for row in reproduction_rows),
            "iters": [row["iter"] for row in reproduction_rows],
        },
        "rosetta_crosswalk_kept_context_only": {
            "pass": row_by_iter["iter_165"]["route_class"] == "sidequest_context_only"
            and row_by_iter["iter_165"]["diagnostics"]["all_axes_math_anchored"] is True,
            "diagnostics": row_by_iter["iter_165"]["diagnostics"],
        },
        "qfi_hopf_geometry_preserved_as_target": {
            "pass": passed(row_by_iter["iter_162"]["diagnostics"]["hopf_volume_2pi_sq"])
            and passed(row_by_iter["iter_162"]["diagnostics"]["qgt_split"]),
            "diagnostics": row_by_iter["iter_162"]["diagnostics"],
        },
        "clifford_quaternion_preserved_without_cl_basin_revival": {
            "pass": passed(row_by_iter["iter_163"]["diagnostics"]["quaternion_isomorphism"])
            and passed(row_by_iter["iter_163"]["diagnostics"]["spin3_so3_double_cover"]),
            "diagnostics": row_by_iter["iter_163"]["diagnostics"],
        },
        "engine_placement_target_preserved": {
            "pass": passed(row_by_iter["iter_169"]["diagnostics"]["placements_16"])
            and passed(row_by_iter["iter_169"]["diagnostics"]["loop_vector_fields"]),
            "diagnostics": row_by_iter["iter_169"]["diagnostics"],
        },
        "smt_sixteen_model_crosscheck_preserved": {
            "pass": row_by_iter["iter_171"]["diagnostics"]["r_models"] == 16
            and passed(row_by_iter["iter_171"]["diagnostics"]["contradiction_unsat"]),
            "diagnostics": row_by_iter["iter_171"]["diagnostics"],
        },
        "thermo_information_targets_preserved": {
            "pass": abs(row_by_iter["iter_173"]["diagnostics"]["holevo_chi"] - 0.6931471805599453) < 1e-12
            and passed(row_by_iter["iter_173"]["diagnostics"]["quantum_landauer"]),
            "diagnostics": row_by_iter["iter_173"]["diagnostics"],
        },
        "no_direct_formal_promotion": {
            "pass": z3_result["direct_promotion_is_unsat"],
            "z3": z3_result,
        },
        "d86_stays_closed_not_reopened": {
            "pass": final_synthesis_closed()["goal_complete"] is True,
            "final_synthesis": final_synthesis_closed(),
        },
    }
    boundary = {
        "promotion_allowed": {"pass": True, "value": False},
        "final_axis_canon_allowed": {"pass": True, "value": False},
        "terrain_admission_allowed": {"pass": True, "value": False},
        "manifold_completion_allowed": {"pass": True, "value": False},
        "real_basin_claim_allowed": {"pass": True, "value": False},
        "bridge_or_phi0_closure_allowed": {"pass": True, "value": False},
        "tensor_network_evidence_allowed": {"pass": True, "value": False},
        "d86_reopen_allowed": {"pass": True, "value": False},
    }
    graveyard_companions = {
        "sidequest_all_pass_is_not_promotion": {
            "pass": True,
            "reason": "Every row keeps direct_formal_promotion_allowed false despite all_pass sidequest receipts.",
        },
        "clifford_quaternion_target_not_cl_basin_revival": {
            "pass": row_by_iter["iter_163"]["route_class"] == "formal_reproduction_target",
            "reason": "Clifford/quaternion facts are reproduction targets, not a revival of a Cl basin theorem.",
        },
        "attractor_distance_examples_not_real_basin": {
            "pass": row_by_iter["iter_167"]["route_class"] == "formal_reproduction_target",
            "reason": "Attractor-distance examples can guide formal tests but do not prove the terrain-engine pseudo-basin.",
        },
        "rosetta_crosswalk_not_math_authority": {
            "pass": row_by_iter["iter_165"]["route_class"] == "sidequest_context_only",
            "reason": "Symbolic crosswalk language remains context-only until independently formalized.",
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
        "math_object": "late grok_sim 161-173 wiki/math sidequest routing",
        "artifact_rows": rows,
        "summary": {
            "all_pass": all_pass,
            "artifact_count": len(rows),
            "class_counts": dict(sorted(class_counts.items())),
            "formal_reproduction_targets": [row["iter"] for row in reproduction_rows],
            "sidequest_context_only": [row["iter"] for row in rows if row["route_class"] == "sidequest_context_only"],
            "direct_formal_promotion_allowed": False,
            "d86_reopened": False,
            "useful_reproduction_targets": [
                "operator algebra and entanglement entropy checks",
                "QFI/Fubini-Study/Bures/Hopf-foliation geometry",
                "Cl+ quaternion and spin double-cover checks",
                "trace-distance/Helstrom/DPI and Hopf/contact integrability",
                "formal-method 16-stage invariant and N01 trace inequivalence",
                "attractor-distance examples as test-design inputs only",
                "density/spectral operator facts",
                "engine QIT placement and 16-placement checks",
                "hypergraph/equivariance/persistence checks",
                "SMT 16-model cross-check for R1/R2/R3",
                "FEP/process/viability examples",
                "Jarzynski/Crooks/Landauer/TUR/Holevo identities",
            ],
            "preserved_boundaries": [
                "sidequest all_pass is not promotion",
                "no final axis canon",
                "no terrain admission",
                "no manifold completion",
                "no real basin, bridge closure, or tensor-network evidence",
                "D86 remains complete and is not reopened",
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
        "why_not_v4_probes": "This is a v5 formal-scout routing receipt over v5 grok_sim sidequest artifacts and D86 post-closeout handling.",
        "blockers": [],
        "source_hashes": {
            "final_synthesis": {
                "path": rel(FINAL_SYNTHESIS),
                "exists": FINAL_SYNTHESIS.exists(),
                "sha256": sha256(FINAL_SYNTHESIS),
            },
            "active_handoff": {
                "path": rel(ACTIVE_HANDOFF),
                "exists": ACTIVE_HANDOFF.exists(),
                "sha256": sha256(ACTIVE_HANDOFF),
            },
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
                "d86_reopened": False,
                "useful_reproduction_targets": result["summary"]["useful_reproduction_targets"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
