#!/usr/bin/env python3
# object_id: discriminator_matrix_cross_row_consistency
# classification: scratch_diagnostic
# promotion_allowed: false
# formal_admission_allowed: false

from __future__ import annotations

import datetime as _dt
import hashlib
import json
from pathlib import Path
from typing import Any


classification = "scratch_diagnostic"
CLASSIFICATION = classification
promotion_allowed = False
PROMOTION_ALLOWED = promotion_allowed
formal_admission_allowed = False
FORMAL_ADMISSION_ALLOWED = formal_admission_allowed
SIM_EXECUTION_KIND = "scratch"

TOOL_MANIFEST = {
    "Python stdlib": {
        "tried": True,
        "used": True,
        "reason": "load-bearing JSON/source-hash audit over existing discriminator receipts; no numerical carrier compute is performed",
    },
    "result JSON receipts": {
        "tried": True,
        "used": True,
        "reason": "load-bearing evidence surface for reconciling matrix-level branch labels with stricter individual-row verdicts",
    },
    "JAX": {
        "tried": False,
        "used": False,
        "reason": "not relevant; this is a receipt-consistency audit, not a finite numerical carrier computation",
    },
    "Julia": {
        "tried": False,
        "used": False,
        "reason": "not relevant; peer Julia/JAX parity is read from existing receipts rather than recomputed here",
    },
    "numpy": {
        "tried": False,
        "used": False,
        "reason": "not relevant and not imported; this audit uses stdlib JSON only",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "Python stdlib": "load_bearing",
    "result JSON receipts": "load_bearing",
    "JAX": None,
    "Julia": None,
    "numpy": None,
}

OBJECT_ID = "discriminator_matrix_cross_row_consistency"
REPO = Path("/Users/joshuaeisenhart/Codex-Ratchet")
RESULTS = REPO / "system_v5" / "ops" / "formal_scouts" / "results"
RESULT_PATH = RESULTS / "discriminator_matrix_cross_row_consistency_results.json"

CLAIM_CEILING = (
    "Receipt-consistency audit only: reconciles matrix-level branch labels with stricter individual "
    "discriminator-row verdicts. No physics, M(C), Axis0, QIT-engine, SM, GR, alpha, gravity, "
    "chirality-doctrine, formal admission, or promotion."
)

BLOCKED_CONSUMERS = [
    "physics_admission",
    "M(C)_admission",
    "Axis0_admission",
    "QIT_engine_admission",
    "SM_recovery",
    "GR_recovery",
    "alpha_derivation",
    "gravity_derivation",
    "formal_admission",
    "promotion",
]

SOURCE_PATHS = {
    "matrix": RESULTS / "carrier_readout_discriminator_matrix_results.json",
    "associator_formal": RESULTS / "three_spinor_associator_lifted_bracketing_probe_results.json",
    "associator_harden": RESULTS / "disc_associator_harden_results.json",
    "charge": RESULTS / "disc_charge_ladder_results.json",
    "chirality": RESULTS / "disc_sigma_y_holonomy_results.json",
    "qit_source_native": RESULTS / "disc_qit_source_native_results.json",
    "gravity_knot": RESULTS / "disc_gravity_knot_results.json",
    "shell_capacity": RESULTS / "disc_shell_capacity_2n2_results.json",
    "hopf_lifted_density": RESULTS / "disc_hopf_lifted_vs_density_results.json",
    "spinor_minimality": RESULTS / "disc_spinor_carrier_minimality_results.json",
    "fine_structure": RESULTS / "mp4_fine_structure_explore_results.json",
}


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256_file(path: Path) -> str | None:
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None


def source_refs() -> dict[str, Any]:
    return {
        key: {"path": str(path), "exists": path.exists(), "sha256": sha256_file(path)}
        for key, path in SOURCE_PATHS.items()
    }


def summary(data: dict[str, Any]) -> dict[str, Any]:
    return data.get("result_summary") or data.get("summary") or {}


def verdict(data: dict[str, Any]) -> str | None:
    s = summary(data)
    for key in ("row_verdict", "layer_verdict", "realization_verdict", "branch_verdict"):
        if key in data:
            return str(data[key])
        if key in s:
            return str(s[key])
    return None


def matrix_rows(matrix: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {row["branch_id"]: row for row in matrix.get("rows", [])}


def row_record(
    branch_id: str,
    matrix_verdict: str | None,
    individual_path_key: str,
    individual: dict[str, Any],
    effective_ceiling: str,
    relation: str,
    reason: str,
) -> dict[str, Any]:
    s = summary(individual)
    return {
        "branch_id": branch_id,
        "matrix_verdict": matrix_verdict,
        "individual_result_key": individual_path_key,
        "individual_verdict": verdict(individual),
        "individual_all_pass": bool(individual.get("all_pass")),
        "individual_classification": individual.get("classification"),
        "promotion_allowed": bool(individual.get("promotion_allowed")),
        "formal_admission_allowed": bool(individual.get("formal_admission_allowed")),
        "effective_ceiling": effective_ceiling,
        "relation": relation,
        "reason": reason,
        "selected_flags": {
            key: s[key]
            for key in sorted(s)
            if key
            in {
                "G_derived",
                "charges_only_with_chosen_rep",
                "controls_also_produce_charges",
                "derived",
                "filling_order_2_8_8_derived",
                "fit_control_matches_137",
                "matches_137",
                "owner_carrier_load_bearing",
                "source_native",
                "survives_mutation",
                "underdetermined",
            }
        },
    }


def build_result() -> dict[str, Any]:
    missing = [key for key, path in SOURCE_PATHS.items() if not path.exists()]
    loaded = {key: read_json(path) for key, path in SOURCE_PATHS.items() if path.exists()}
    matrix = loaded.get("matrix", {})
    matrix_by_id = matrix_rows(matrix)

    rows: list[dict[str, Any]] = []

    assoc = loaded.get("associator_formal", {})
    rows.append(
        row_record(
            "associator_nonassociativity",
            matrix_by_id.get("associator_nonassociativity", {}).get("branch_verdict"),
            "associator_formal",
            assoc,
            "formal_scout_only_no_promotion",
            "compatible_but_fenced",
            "matrix and formal row agree that nonassociative lifted bracketing is the strongest carrier-specific row; ceiling remains formal scout / no promotion",
        )
    )

    charge = loaded.get("charge", {})
    rows.append(
        row_record(
            "charge_ladder_cl6",
            matrix_by_id.get("charge_ladder_cl6", {}).get("branch_verdict"),
            "charge",
            charge,
            "split_scope_carrier_support_but_physical_derivation_open",
            "split_scope_demote_physics_claim",
            "matrix checks presence of carrier-dependent ladder structure; individual row says physical charge derivation remains convention-bound",
        )
    )

    chirality = loaded.get("chirality", {})
    rows.append(
        row_record(
            "chirality_survival_type1_type2_weyl",
            matrix_by_id.get("chirality_survival_type1_type2_weyl", {}).get("branch_verdict"),
            "chirality",
            chirality,
            "scratch_supported_lifted_holonomy_only",
            "compatible_but_fenced",
            "sigma-y / 720-degree holonomy row now supports a lifted-carrier split, but no weak, SM, baryogenesis, or biology admission",
        )
    )

    gravity = loaded.get("gravity_knot", {})
    rows.append(
        row_record(
            "knot_mass_gravity",
            matrix_by_id.get("knot_mass_gravity", {}).get("branch_verdict"),
            "gravity_knot",
            gravity,
            "scratch_geometry_readout_not_gravity_derivation",
            "compatible_demoted",
            "matrix target-imprint warning and individual CONVENTION verdict agree that G is not derived and gravity is not admitted",
        )
    )

    shell = loaded.get("shell_capacity", {})
    rows.append(
        row_record(
            "shell_capacity_hopf_clifford",
            matrix_by_id.get("shell_capacity_hopf_clifford", {}).get("branch_verdict"),
            "shell_capacity",
            shell,
            "partial_capacity_not_chemistry",
            "split_scope_demote_full_claim",
            "matrix sees carrier support for shell capacity; individual row is only PARTIAL because filling order is not derived",
        )
    )

    qit = loaded.get("qit_source_native", {})
    rows.append(
        row_record(
            "qit_face_knot_readout",
            matrix_by_id.get("qit_face_knot_readout", {}).get("branch_verdict"),
            "qit_source_native",
            qit,
            "source_native_real_carrier_but_no_qit_admission",
            "split_scope_repair_needed",
            "older matrix key-list test calls target imprint, while the source-native individual row reports REAL_CARRIER; Claude should reconcile scope before using either label",
        )
    )

    fine = loaded.get("fine_structure", {})
    rows.append(
        row_record(
            "fine_structure_alpha",
            None,
            "fine_structure",
            fine,
            "graveyard_underdetermined_challenger_only",
            "external_to_matrix",
            "alpha row passes its hygiene/graveyard contract after AST import-guard repair, but matches_137=false and derived=false",
        )
    )

    hopf = loaded.get("hopf_lifted_density", {})
    rows.append(
        row_record(
            "hopf_lifted_vs_density",
            None,
            "hopf_lifted_density",
            hopf,
            "real_lifted_data_fence_only",
            "supplemental",
            "lifted Hopf/spinor data survives where density quotient loses phase/path/bracketing information",
        )
    )

    spinor = loaded.get("spinor_minimality", {})
    rows.append(
        row_record(
            "spinor_carrier_minimality",
            None,
            "spinor_minimality",
            spinor,
            "real_layer_but_realization_convention",
            "supplemental",
            "spinor double-cover witness is real, but quaternion tie blocks unique-carrier/canon language",
        )
    )

    split_scope = [row for row in rows if row["relation"].startswith("split_scope")]
    demoted = [row for row in rows if "demote" in row["relation"] or "graveyard" in row["effective_ceiling"]]
    compatible = [row for row in rows if row["relation"].startswith("compatible")]
    supplemental = [row for row in rows if row["relation"] == "supplemental"]
    unsafe_promotions = [
        row
        for row in rows
        if row["matrix_verdict"] == "REAL_SUPPORT"
        and row["individual_verdict"] in {"CONVENTION", "PARTIAL"}
        and not row["relation"].startswith("split_scope")
    ]
    source_all_pass = all(bool(data.get("all_pass")) for key, data in loaded.items() if key != "matrix")
    fence_pass = all(not row["promotion_allowed"] and not row["formal_admission_allowed"] for row in rows)
    all_pass = not missing and source_all_pass and fence_pass and not unsafe_promotions

    result = {
        "object_id": OBJECT_ID,
        "classification": classification,
        "promotion_allowed": promotion_allowed,
        "formal_admission_allowed": formal_admission_allowed,
        "generated_at": _dt.datetime.now(_dt.timezone.utc).isoformat(),
        "claim_ceiling": CLAIM_CEILING,
        "blocked_consumers": BLOCKED_CONSUMERS,
        "source_refs": source_refs(),
        "rows": rows,
        "missing_sources": missing,
        "unsafe_promotions": unsafe_promotions,
        "positive": {
            "source_files_present": {"pass": not missing, "missing": missing},
            "individual_rows_pass": {"pass": source_all_pass},
            "no_promotion_fence": {"pass": fence_pass},
            "matrix_overclaim_split_scopes_identified": {"pass": not unsafe_promotions, "unsafe_promotions": unsafe_promotions},
        },
        "result_summary": {
            "all_pass": all_pass,
            "rows": len(rows),
            "compatible_count": len(compatible),
            "split_scope_count": len(split_scope),
            "demoted_count": len(demoted),
            "supplemental_count": len(supplemental),
            "effective_high_value_spine": [
                "associator_nonassociativity=formal_scout_only_no_promotion",
                "hopf_lifted_vs_density=real_lifted_data_fence_only",
                "chirality_survival_type1_type2_weyl=scratch_supported_lifted_holonomy_only",
            ],
            "keep_demoted": [
                "fine_structure_alpha=graveyard_underdetermined_challenger_only",
                "knot_mass_gravity=scratch_geometry_readout_not_gravity_derivation",
                "charge_ladder_cl6=split_scope_carrier_support_but_physical_derivation_open",
                "shell_capacity_hopf_clifford=partial_capacity_not_chemistry",
            ],
            "claude_next_action": "repair/reconcile matrix scopes before any new broad sim: charge, qit, shell, and fine-structure rows must carry effective ceilings from this audit",
        },
        "all_pass": all_pass,
        "blockers": [] if all_pass else ["missing_sources_or_unsafe_matrix_promotion"],
    }
    return result


def main() -> None:
    result = build_result()
    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        "SCOUT_DONE "
        f"result={RESULT_PATH} "
        f"all_pass={str(result['all_pass']).lower()} "
        f"split_scope_count={result['result_summary']['split_scope_count']} "
        f"demoted_count={result['result_summary']['demoted_count']}"
    )
    if not result["all_pass"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
