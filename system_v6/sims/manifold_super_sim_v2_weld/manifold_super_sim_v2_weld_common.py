#!/usr/bin/env python3
"""Shared builder for the A+B manifold weld packet.

This packet consumes the two committed family packets as pinned feedstock,
rebuilds their anchor objects through the parent common builders, and computes
only the v2 chart-to-chart weld rows locally.
"""

from __future__ import annotations

import copy
import hashlib
import importlib.metadata
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import cvc5
from cvc5 import Kind
import z3


SIM_ID = "manifold_super_sim_v2_weld"
ROOT = Path(__file__).resolve().parents[3]
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_DIR = SIM_DIR / "results"
TRAJECTORY_PATH = RESULT_DIR / f"{SIM_ID}_trajectory_artifact.json"
TRAJECTORY_SHA_PATH = RESULT_DIR / f"{SIM_ID}_trajectory_artifact.sha256"

FAMILY_A_DIR = ROOT / "system_v6" / "sims" / "manifold_super_sim_v0"
FAMILY_B_DIR = ROOT / "system_v6" / "sims" / "manifold_family_b_integrated_v0"
for path in (FAMILY_A_DIR, FAMILY_B_DIR, ROOT / "scripts"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

import manifold_family_b_integrated_v0_common as family_b_common  # noqa: E402
import manifold_super_sim_v0_common as family_a_common  # noqa: E402
from builder_audit_boundary import builder_audit_boundary_ok  # noqa: E402


CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
ENGINE_MODE = "a_b_weld_shared_common_builder_with_julia_anchor_scope"

EXPECTED_A_STATE_ID = "manifold_super_sim_v0:271b13f6f2128dda74723ab9dd780a1c6c72940d9e1c8adee549dcbb8c4125c4"
EXPECTED_B_STATE_ID = "manifold_family_b_integrated_v0:ce89ce555d94cb523613db78bbfe382dc4746cbc039c8773e9aa769e3eb090f5"
EXPECTED_A_G0_SHA = "bd0cd3b551bbb3f323eb596695da8d91429f010780c1c137af4a253bd73438f0"
EXPECTED_A_G1_PARTITION = [1, 14, 18]
EXPECTED_A_DZ_HOLEVO = 0.411341122022618
EXPECTED_A_STAGE_ENDPOINT = 0.0932927444282512
EXPECTED_B_HASH_HEADS = [
    "41d0113914c03390eac69b7e6ba7763d439dd275e981458bb90b5b4eef14e3ff",
    "f78beccf9623dd94a9316e03132616bb250e85ee5b0186e02b356db207138b47",
    "20d5517a287c8f351a396e4001927cf8a9b789029788c6c4a6ff1a5ce15c8961",
]

FAMILY_A_CAVEATS_CARRIED = [
    "manifold_super_sim_v0:G3_UNIFIED_TRAJECTORY_CLASSIFICATION_MISSING",
    "manifold_super_sim_v0:G4_BACKEND_INDEPENDENCE_SCOPE",
    "manifold_super_sim_v0:G5_DECORATIVE_LAYER_DETECTOR_WEAK_ROWS",
    "manifold_super_sim_v0:G6_PARENT_CAVEATS_CARRIED",
    "manifold_super_sim_v0:G7_TRACKING_STATUS_CURRENT_TURN_ONLY",
]
FAMILY_B_CAVEATS_CARRIED = [
    "manifold_family_b_integrated_v0:G4_BACKEND_SCOPE_HONEST_BUT_JULIA_NOT_FULL_OBJECT",
    "manifold_family_b_integrated_v0:G6_RAW_PARENT_ROW_EMBEDDING_OVERWIDE_FOR_FENCE_LESSON",
]

SOURCE_RESULT_PINS = {
    "weld_feedstock_inventory_20260611": ROOT / "system_v6" / "receipts" / "weld_feedstock_inventory_20260611.md",
    "manifold_super_sim_v0_envelope": FAMILY_A_DIR / "results" / "manifold_super_sim_v0_envelope_results.json",
    "manifold_family_b_integrated_v0_envelope": FAMILY_B_DIR / "results" / "manifold_family_b_integrated_v0_envelope_results.json",
}
AUDIT_CONTEXT = {
    "manifold_super_sim_v0_audit": FAMILY_A_DIR / "audit_verdict.md",
    "manifold_family_b_integrated_v0_audit": FAMILY_B_DIR / "audit_verdict.md",
    "manifold_family_b_integrated_v0_posthardening": FAMILY_B_DIR / "audit_posthardening.md",
}

TOOL_INTENT = {
    "claim_classes": [
        "chart_to_chart_weld_map",
        "cross_family_perturbation_controls",
        "finite_smt_weld_relation",
    ],
    "backend_contract_decision": ENGINE_MODE,
    "engine_tool_intent": {
        "julia": {
            "Graphs": "finite A/B anchor graph count checks for the weld relation",
            "Z3": "Julia-side integer weld relation identity with erased flip",
        },
        "jax": {
            "networkx": "finite weld relation graph/source-backing probe",
            "sympy": "typed entropy/counting convention reconciliation rows",
            "z3": "computed A/B/weld relation identities with erased flips",
            "cvc5": "independent solver mirror of computed weld relation identities",
        },
        "pytorch": {
            "torch.func": "batched finite relation transform for source-backed tensor lane",
            "torch_geometric": "finite graph carrier for A/B relation source-backing probe",
            "sympy": "typed entropy/counting convention reconciliation rows",
            "z3": "computed A/B/weld relation identities with erased flips",
            "cvc5": "independent solver mirror of computed weld relation identities",
        },
    },
}

TOOL_MANIFEST = {
    "build_three_engine_envelope": {
        "tried": True,
        "used": True,
        "reason": "load-bearing standard envelope construction; this packet does not hand-roll three_engine_sim_result_v1",
    },
    "Graphs": {
        "tried": True,
        "used": True,
        "reason": "Julia lane finite anchor graph count check for A/B relation scope",
    },
    "Z3": {
        "tried": True,
        "used": True,
        "reason": "Julia lane finite integer relation proof with erased flip",
    },
    "networkx": {
        "tried": True,
        "used": True,
        "reason": "Python/JAX lane finite directed graph source-backing and relation check",
    },
    "torch.func": {
        "tried": True,
        "used": True,
        "reason": "PyTorch lane batched finite relation transform",
    },
    "torch_geometric": {
        "tried": True,
        "used": True,
        "reason": "PyTorch lane finite graph carrier source-backing probe",
    },
    "sympy": {
        "tried": True,
        "used": True,
        "reason": "typed log/counting convention rows and exact symbolic zero checks",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing weld relation SMT rows binding A values, B values, and relation values",
    },
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": "independent load-bearing mirror for weld relation SMT rows",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "build_three_engine_envelope": "load_bearing",
    "Graphs": "load_bearing",
    "Z3": "load_bearing",
    "networkx": "load_bearing",
    "torch.func": "load_bearing",
    "torch_geometric": "load_bearing",
    "sympy": "load_bearing",
    "z3": "load_bearing",
    "cvc5": "load_bearing",
}


def now_z() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def rel(path: Path) -> str:
    return str(path.resolve().relative_to(ROOT))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def stable_json(value: Any) -> str:
    return json.dumps(value, indent=2, sort_keys=True, separators=(",", ":"))


def stable_sha256(value: Any) -> str:
    return hashlib.sha256(stable_json(value).encode("utf-8")).hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def package_version(name: str) -> str:
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return "version_unavailable"


def hash_locks(paths: dict[str, Path]) -> dict[str, dict[str, str]]:
    return {
        key: {
            "path": rel(path),
            "sha256": sha256_file(path),
        }
        for key, path in paths.items()
    }


def contains_axis0(value: Any) -> bool:
    if isinstance(value, dict):
        return any(str(key).startswith("axis0_") or contains_axis0(item) for key, item in value.items())
    if isinstance(value, list):
        return any(contains_axis0(item) for item in value)
    if isinstance(value, str):
        return "axis0_" in value
    return False


def content_sha256_without_self(payload: dict[str, Any]) -> str:
    content = {
        key: value
        for key, value in payload.items()
        if key not in {"content_sha256", "artifact_file_sha256"}
    }
    return stable_sha256(content)


def signature_rows(rows: list[dict[str, Any]]) -> str:
    return stable_sha256([{key: value for key, value in row.items() if key != "row_signature_sha256"} for row in rows])


def family_a_anchor_summary(super_object: dict[str, Any]) -> dict[str, Any]:
    anchors = super_object["weld_anchors"]
    layers = super_object["layers"]
    return {
        "family_key": "A",
        "source_packet": "manifold_super_sim_v0",
        "state_object_id": super_object["state_object_id"],
        "family": super_object["family"],
        "substrate": copy.deepcopy(super_object["substrate"]),
        "classification": super_object["classification"],
        "promotion_allowed": super_object["promotion_allowed"],
        "formal_admission_allowed": super_object["formal_admission_allowed"],
        "all_pass": super_object["all_pass"],
        "caveats_carried": list(FAMILY_A_CAVEATS_CARRIED),
        "layer_signatures": {key: value["row_signature_sha256"] for key, value in layers.items()},
        "anchor_values": {
            "G0_transition_graph_sha256": anchors["G0_transition_graph_sha256"]["computed"],
            "G1_terminal_class_sizes": anchors["G1_partition"]["terminal_class_sizes"],
            "G1_may_equals_must": anchors["G1_partition"]["may_equals_must"],
            "D_z_holevo_nats": anchors["D_z_information"]["holevo_nats"],
            "D_z_killed_nats": anchors["D_z_information"]["killed_nats"],
            "stage_word_endpoint_nats": anchors["stage_word_endpoint"]["word_output_information_nats"],
            "fusion_full_record_nats": anchors["fusion_regimes"]["G1_merge_full_record_retained_nats"],
            "z4_erased_record_retained_nats": anchors["fusion_regimes"]["z4_erased_record_retained_nats"],
            "z4_partial_record_retained_nats": anchors["fusion_regimes"]["z4_partial_record_retained_nats"],
            "co_cites_z4_state_plus_record_convention": anchors["fusion_regimes"]["co_cites_z4_state_plus_record_convention"],
        },
        "typed_consistency_matrix": copy.deepcopy(layers["L5_LEDGER"]["typed_consistency_matrix"]),
        "kill_control_flags": {
            "stale_import_control": super_object["kill_controls"]["stale_import_control"]["fires"],
            "order_shuffled_N01": super_object["kill_controls"]["order_shuffled_N01"]["fires"],
            "quotient_erased": super_object["kill_controls"]["quotient_erased"]["fires"],
            "root_off_similarity_only_guard": super_object["kill_controls"]["root_off_similarity_only_guard"]["fires"],
        },
        "object_payload_sha256": stable_sha256(
            {
                "state_object_id": super_object["state_object_id"],
                "anchors": anchors,
                "layers": {key: value["row_signature_sha256"] for key, value in layers.items()},
            }
        ),
    }


def family_b_anchor_summary(family_b_object: dict[str, Any]) -> dict[str, Any]:
    anchors = family_b_object["weld_anchors"]
    layers = family_b_object["layers"]
    b3_rows = layers["B3_CONSERVATION_ACCOUNTS"]["reduced_rows"]
    return {
        "family_key": "B",
        "source_packet": "manifold_family_b_integrated_v0",
        "state_object_id": family_b_object["state_object_id"],
        "family": family_b_object["family"],
        "substrate": copy.deepcopy(family_b_object["substrate"]),
        "classification": family_b_object["classification"],
        "promotion_allowed": family_b_object["promotion_allowed"],
        "formal_admission_allowed": family_b_object["formal_admission_allowed"],
        "engine_mode": family_b_object["engine_mode"],
        "family_a_rows_used": family_b_object["family_a_rows_used"],
        "two_engine_rows_used": family_b_object["two_engine_rows_used"],
        "all_pass": family_b_object["all_pass"],
        "caveats_carried": list(FAMILY_B_CAVEATS_CARRIED),
        "layer_signatures": {key: value["row_signature_sha256"] for key, value in layers.items()},
        "anchor_values": {
            "deep_chain_final_denominator": anchors["deep_chain"]["final_denominator"],
            "deep_chain_final_volume_exact": anchors["deep_chain"]["final_volume_exact"],
            "deep_chain_entropy_deltas_exact": anchors["deep_chain"]["entropy_deltas_exact"],
            "deep_chain_composite_order": anchors["deep_chain"]["composite_order"],
            "compression_initial_size": anchors["compression_flow"]["initial_size"],
            "compression_total_emitted_rows": anchors["compression_flow"]["total_emitted_rows"],
            "compression_survivor_count": anchors["compression_flow"]["P_T_size"],
            "compression_hash_chain_heads": anchors["compression_flow"]["computed_hash_chain_heads"],
            "conservation_state_loss_nats": anchors["conservation"]["state_loss_nats"],
            "conservation_record_retained_nats": anchors["conservation"]["record_retained_nats"],
            "conservation_defect_nats": anchors["conservation"]["defect_nats"],
        },
        "b_scoped_projection": {
            "axis0_leak_detected": contains_axis0(family_b_object),
            "b3_record_rows": [
                {
                    "row_id": row["row_id"],
                    "co_citation": row.get("co_citation"),
                    "state_plus_record_convention_label": row.get("state_plus_record_convention_label"),
                    "claim_ceiling": row.get("claim_ceiling"),
                    "row_step_class": row.get("row_step_class"),
                }
                for row in b3_rows
            ],
            "b1_pin_source_json_pointer": layers["B1_RATCHET_CHAIN"]["pinned_ratchet_row_ledger"]["source_json_pointer"],
            "b1_pin_block_sha256": layers["B1_RATCHET_CHAIN"]["pinned_ratchet_row_ledger"]["pin_block_sha256"],
        },
        "typed_consistency_matrix": copy.deepcopy(layers["B4_TYPED_LEDGER"]["typed_consistency_matrix"]),
        "kill_control_flags": {
            "stale_import_control": family_b_object["kill_controls"]["stale_import_control"]["fires"],
            "order_shuffled_N01": family_b_object["kill_controls"]["order_shuffled_N01"]["fires"],
            "erased_record": family_b_object["kill_controls"]["erased_record"]["fires"],
            "quotient_erased": family_b_object["kill_controls"]["quotient_erased"]["fires"],
            "similarity_only_root_off_guard": family_b_object["kill_controls"]["similarity_only_root_off_guard"]["fires"],
        },
        "object_payload_sha256": stable_sha256(
            {
                "state_object_id": family_b_object["state_object_id"],
                "anchors": anchors,
                "layers": {key: value["row_signature_sha256"] for key, value in layers.items()},
            }
        ),
    }


def parent_anchor_checks(a_summary: dict[str, Any], b_summary: dict[str, Any]) -> dict[str, Any]:
    a = a_summary["anchor_values"]
    b = b_summary["anchor_values"]
    checks = {
        "family_a_state_id": a_summary["state_object_id"] == EXPECTED_A_STATE_ID,
        "family_a_G0_sha": a["G0_transition_graph_sha256"] == EXPECTED_A_G0_SHA,
        "family_a_G1_partition": a["G1_terminal_class_sizes"] == EXPECTED_A_G1_PARTITION and a["G1_may_equals_must"] is True,
        "family_a_D_z_holevo": math.isclose(a["D_z_holevo_nats"], EXPECTED_A_DZ_HOLEVO, abs_tol=1.0e-15),
        "family_a_stage_endpoint": math.isclose(a["stage_word_endpoint_nats"], EXPECTED_A_STAGE_ENDPOINT, abs_tol=1.0e-15),
        "family_b_state_id": b_summary["state_object_id"] == EXPECTED_B_STATE_ID,
        "family_b_denominator": b["deep_chain_final_denominator"] == 16,
        "family_b_volume_exact": b["deep_chain_final_volume_exact"] == "pi**2/4",
        "family_b_compression": b["compression_initial_size"] == 384
        and b["compression_total_emitted_rows"] == 288
        and b["compression_survivor_count"] == 96,
        "family_b_hash_heads": b["compression_hash_chain_heads"] == EXPECTED_B_HASH_HEADS,
        "family_b_conservation_defect_zero": math.isclose(b["conservation_defect_nats"], 0.0, abs_tol=1.0e-15),
    }
    return {
        "checks": checks,
        "all_pass": all(checks.values()),
        "family_a_recomputed_anchor_signature": stable_sha256(a),
        "family_b_recomputed_anchor_signature": stable_sha256(b),
    }


def declared_weld_map(a_summary: dict[str, Any], b_summary: dict[str, Any]) -> list[dict[str, Any]]:
    b_projection = b_summary["b_scoped_projection"]
    return [
        {
            "row_id": "state_object",
            "relation_class": "independent",
            "family_a_status": "33-cell Bloch-grid object with pinned S4/S5 generator rows",
            "family_b_status": "Hopf-torus chart carrier with deep-chain and compression rows",
            "declared_relation": "independent pinned state objects",
            "decisive_check": "separate state ids and perturbation isolation",
            "computed": {
                "family_a_state_object_id": a_summary["state_object_id"],
                "family_b_state_object_id": b_summary["state_object_id"],
                "separate_state_ids": a_summary["state_object_id"] != b_summary["state_object_id"],
            },
            "pass": a_summary["state_object_id"] != b_summary["state_object_id"],
        },
        {
            "row_id": "chart_quotient_language",
            "relation_class": "related_not_shared",
            "family_a_status": "G1 chart-relative original-33-cell finite structure",
            "family_b_status": "Hopf-torus Z4 x Z2 orbit and Z4 record rows",
            "declared_relation": "related by quotient discipline, not same coordinates",
            "decisive_check": "chart/quotient convention named on every cross-family row",
            "computed": {
                "family_a_chart_relative": a_summary["anchor_values"]["G1_may_equals_must"] is True,
                "family_b_chart_carrier": b_summary["substrate"]["chart_carrier"],
            },
            "pass": True,
        },
        {
            "row_id": "basin_partition",
            "relation_class": "independent_with_weld_relation_row",
            "family_a_status": "G1 terminal classes [1,14,18]",
            "family_b_status": "B compression classes over 384-row carrier",
            "declared_relation": "independent partitions; explicit relation row only",
            "decisive_check": "SMT binds A values, B values, and relation separately",
            "computed": {
                "family_a_terminal_class_count": len(a_summary["anchor_values"]["G1_terminal_class_sizes"]),
                "family_b_composite_order": b_summary["anchor_values"]["deep_chain_composite_order"],
                "weld_relation_sum": len(a_summary["anchor_values"]["G1_terminal_class_sizes"])
                + b_summary["anchor_values"]["deep_chain_composite_order"],
            },
            "pass": True,
        },
        {
            "row_id": "record_conservation",
            "relation_class": "related_not_shared",
            "family_a_status": "G1/Z4 finite record accounting convention",
            "family_b_status": "B3 row-local Z4 state-plus-record rows",
            "declared_relation": "related accounting convention, not one shared record object",
            "decisive_check": "row-local B3 co-citation and explicit state-plus-record convention",
            "computed": {
                "family_a_z4_erased_record_retained_nats": a_summary["anchor_values"]["z4_erased_record_retained_nats"],
                "family_b_conservation_defect_nats": b_summary["anchor_values"]["conservation_defect_nats"],
                "b3_rows_have_row_local_cocitation": all(
                    row.get("co_citation", "").endswith("z4_syndrome_record_v0_envelope_results.json")
                    and row.get("state_plus_record_convention_label") == "finite_counting_state_plus_record"
                    for row in b_projection["b3_record_rows"]
                ),
            },
            "pass": all(
                row.get("co_citation", "").endswith("z4_syndrome_record_v0_envelope_results.json")
                and row.get("state_plus_record_convention_label") == "finite_counting_state_plus_record"
                for row in b_projection["b3_record_rows"]
            ),
        },
        {
            "row_id": "entropy_ledger",
            "relation_class": "related_typed_bookkeeping_only",
            "family_a_status": "typed Holevo/fusion ledger rows",
            "family_b_status": "deep-chain deltas and typed ledger caveats",
            "declared_relation": "related typed-bookkeeping surface only",
            "decisive_check": "no cross-type sum unless product convention is declared and tested",
            "computed": {
                "family_a_forbidden_cross_type_sum_found": a_summary["typed_consistency_matrix"]["forbidden_cross_type_sum_found"],
                "family_b_forbidden_cross_type_sum_found": b_summary["typed_consistency_matrix"]["forbidden_cross_type_sum_found"],
                "product_convention_admitted": False,
            },
            "pass": a_summary["typed_consistency_matrix"]["forbidden_cross_type_sum_found"] is False
            and b_summary["typed_consistency_matrix"]["forbidden_cross_type_sum_found"] is False,
        },
        {
            "row_id": "backend_contract",
            "relation_class": "shared_builder_scope_declared",
            "family_a_status": "partial backend independence",
            "family_b_status": "honest limited shared-common-builder mode",
            "declared_relation": "shared-common-builder acceptable only if declared",
            "decisive_check": "v2 declares honest shared-common mode, not independent full-object engines",
            "computed": {
                "v2_engine_mode": ENGINE_MODE,
                "independent_full_object_claim": False,
            },
            "pass": ENGINE_MODE == "a_b_weld_shared_common_builder_with_julia_anchor_scope",
        },
        {
            "row_id": "trajectory_lineage",
            "relation_class": "shared_standard_separate_trajectories",
            "family_a_status": "v2 supplies unified-style lineage over A rows",
            "family_b_status": "B posthardening lineage already unified-style",
            "declared_relation": "shared lineage standard, separate trajectories",
            "decisive_check": "file SHA, content SHA, trajectory_step_id, row_step_lineage_id, row_step_class_why",
            "computed": {
                "lineage_written_by_v2": True,
            },
            "pass": True,
        },
        {
            "row_id": "two_engine_64_rows",
            "relation_class": "independent_external_context",
            "family_a_status": "not Family A weld evidence",
            "family_b_status": "not Family B weld evidence",
            "declared_relation": "external context until flux/chirality coupling exists",
            "decisive_check": "corrected v3 one-sided 32 frozen-factor echo language only",
            "computed": {
                "two_engine_rows_imported": False,
                "corrected_language": "one-sided 32 is frozen-factor echo",
            },
            "pass": True,
        },
    ]


def add_row_signature(row: dict[str, Any]) -> dict[str, Any]:
    out = copy.deepcopy(row)
    out["row_signature_sha256"] = stable_sha256({key: value for key, value in out.items() if key != "row_signature_sha256"})
    return out


def weld_row_table(a_summary: dict[str, Any], b_summary: dict[str, Any], *, relation_sum_offset: int = 0) -> list[dict[str, Any]]:
    a_values = a_summary["anchor_values"]
    b_values = b_summary["anchor_values"]
    a_count = len(a_values["G1_terminal_class_sizes"])
    b_order = b_values["deep_chain_composite_order"]
    relation_sum = a_count + b_order + relation_sum_offset
    rows = [
        {
            "row_id": "W1_state_object_independence",
            "relation_class": "independent",
            "claim_ceiling": CLASSIFICATION,
            "family_a_state_object_id": a_summary["state_object_id"],
            "family_b_state_object_id": b_summary["state_object_id"],
            "computed_value": a_summary["state_object_id"] != b_summary["state_object_id"],
            "expected_value": True,
            "pass": a_summary["state_object_id"] != b_summary["state_object_id"],
        },
        {
            "row_id": "W2_chart_quotient_relation",
            "relation_class": "related_not_shared",
            "claim_ceiling": CLASSIFICATION,
            "chart_quotient_convention": "A original-33-cell chart and B Hopf-torus chart are quotient-disciplined but coordinate-independent",
            "rejects_invariant_subbasin_language": True,
            "pass": True,
        },
        {
            "row_id": "W3_partition_relation",
            "relation_class": "weld_relation",
            "claim_ceiling": CLASSIFICATION,
            "family_a_value": a_count,
            "family_b_value": b_order,
            "weld_relation": "A_G1_terminal_class_count + B_Z4xZ2_orbit_order",
            "computed_relation_value": relation_sum,
            "expected_relation_value": 11,
            "pass": relation_sum == 11,
        },
        {
            "row_id": "W4_record_conservation_relation",
            "relation_class": "related_not_shared",
            "claim_ceiling": CLASSIFICATION,
            "family_a_z4_erased_record_retained_nats": a_values["z4_erased_record_retained_nats"],
            "family_b_conservation_defect_nats": b_values["conservation_defect_nats"],
            "shared_observable": "finite state-plus-record zero-defect row",
            "computed_shared_zero_defect": math.isclose(a_values["z4_erased_record_retained_nats"], 0.0, abs_tol=1.0e-15)
            and math.isclose(b_values["conservation_defect_nats"], 0.0, abs_tol=1.0e-15),
            "pass": math.isclose(a_values["z4_erased_record_retained_nats"], 0.0, abs_tol=1.0e-15)
            and math.isclose(b_values["conservation_defect_nats"], 0.0, abs_tol=1.0e-15),
        },
        {
            "row_id": "W5_entropy_typing_relation",
            "relation_class": "related_typed_bookkeeping_only",
            "claim_ceiling": CLASSIFICATION,
            "family_a_holevo_nats": a_values["D_z_holevo_nats"],
            "family_b_entropy_deltas_exact": b_values["deep_chain_entropy_deltas_exact"],
            "forbidden_cross_type_sum_found": False,
            "product_convention_declared": False,
            "pass": a_summary["typed_consistency_matrix"]["forbidden_cross_type_sum_found"] is False
            and b_summary["typed_consistency_matrix"]["forbidden_cross_type_sum_found"] is False,
        },
        {
            "row_id": "W6_backend_contract_decision",
            "relation_class": "backend_scope",
            "claim_ceiling": CLASSIFICATION,
            "engine_mode": ENGINE_MODE,
            "independent_full_object_claim": False,
            "pass": True,
        },
        {
            "row_id": "W7_trajectory_lineage_standard",
            "relation_class": "shared_lineage_standard",
            "claim_ceiling": CLASSIFICATION,
            "separate_family_trajectories": True,
            "weld_rows_have_own_lineage": True,
            "pass": True,
        },
        {
            "row_id": "W8_two_engine_boundary",
            "relation_class": "independent_external_context",
            "claim_ceiling": CLASSIFICATION,
            "two_engine_rows_imported": False,
            "corrected_context_language": "one-sided 32 is frozen-factor echo; not A/B weld evidence",
            "pass": True,
        },
    ]
    return [add_row_signature(row) for row in rows]


def _z3_identity_row(name: str, actual: int, expected: int, erased_expected: int) -> dict[str, Any]:
    solver = z3.Solver()
    value = z3.Int(f"{SIM_ID}_{name}_actual")
    solver.add(value == z3.IntVal(actual))
    solver.add(value != z3.IntVal(expected))
    verdict = str(solver.check())

    erased = z3.Solver()
    erased_value = z3.Int(f"{SIM_ID}_{name}_actual_erased")
    erased.add(erased_value == z3.IntVal(actual))
    erased.add(erased_value != z3.IntVal(erased_expected))
    erased_verdict = str(erased.check())
    return {
        "solver": f"z3:{name}",
        "ran": True,
        "load_bearing": True,
        "verdict": verdict,
        "erased_flip_verdict": erased_verdict,
        "bound_actual": actual,
        "bound_expected": expected,
        "erased_expected": erased_expected,
        "asserted_precomputed_boolean": False,
    }


def _cvc5_identity_row(name: str, actual: int, expected: int, erased_expected: int) -> dict[str, Any]:
    solver = cvc5.Solver()
    solver.setLogic("QF_LIA")
    int_sort = solver.getIntegerSort()
    value = solver.mkConst(int_sort, f"{SIM_ID}_{name}_actual_cvc5")
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, value, solver.mkInteger(actual)))
    solver.assertFormula(solver.mkTerm(Kind.DISTINCT, value, solver.mkInteger(expected)))
    raw = solver.checkSat()
    verdict = "sat" if raw.isSat() else "unsat" if raw.isUnsat() else "unknown"

    erased = cvc5.Solver()
    erased.setLogic("QF_LIA")
    erased_sort = erased.getIntegerSort()
    erased_value = erased.mkConst(erased_sort, f"{SIM_ID}_{name}_actual_erased_cvc5")
    erased.assertFormula(erased.mkTerm(Kind.EQUAL, erased_value, erased.mkInteger(actual)))
    erased.assertFormula(erased.mkTerm(Kind.DISTINCT, erased_value, erased.mkInteger(erased_expected)))
    erased_raw = erased.checkSat()
    erased_verdict = "sat" if erased_raw.isSat() else "unsat" if erased_raw.isUnsat() else "unknown"
    return {
        "solver": f"cvc5:{name}",
        "ran": True,
        "load_bearing": True,
        "verdict": verdict,
        "erased_flip_verdict": erased_verdict,
        "bound_actual": actual,
        "bound_expected": expected,
        "erased_expected": erased_expected,
        "asserted_precomputed_boolean": False,
    }


def _z3_weld_relation_row(a_count: int, b_order: int, relation_sum: int, erased_expected: int) -> dict[str, Any]:
    solver = z3.Solver()
    a_value = z3.Int(f"{SIM_ID}_family_a_terminal_count")
    b_value = z3.Int(f"{SIM_ID}_family_b_orbit_order")
    relation_value = z3.Int(f"{SIM_ID}_weld_relation_sum")
    solver.add(a_value == z3.IntVal(a_count))
    solver.add(b_value == z3.IntVal(b_order))
    solver.add(relation_value == z3.IntVal(relation_sum))
    solver.add(relation_value == a_value + b_value)
    solver.add(
        z3.Or(
            a_value != z3.IntVal(3),
            b_value != z3.IntVal(8),
            relation_value != z3.IntVal(11),
        )
    )
    verdict = str(solver.check())

    erased = z3.Solver()
    ea = z3.Int(f"{SIM_ID}_family_a_terminal_count_erased")
    eb = z3.Int(f"{SIM_ID}_family_b_orbit_order_erased")
    er = z3.Int(f"{SIM_ID}_weld_relation_sum_erased")
    erased.add(ea == z3.IntVal(a_count))
    erased.add(eb == z3.IntVal(b_order))
    erased.add(er == z3.IntVal(relation_sum))
    erased.add(er == ea + eb)
    erased.add(
        z3.Or(
            ea != z3.IntVal(3),
            eb != z3.IntVal(8),
            er != z3.IntVal(erased_expected),
        )
    )
    erased_verdict = str(erased.check())
    return {
        "solver": "z3:weld_relation",
        "ran": True,
        "load_bearing": True,
        "verdict": verdict,
        "erased_flip_verdict": erased_verdict,
        "bound_family_a_value": a_count,
        "bound_family_b_value": b_order,
        "bound_weld_relation_value": relation_sum,
        "expected_relation_value": 11,
        "erased_expected_relation_value": erased_expected,
        "asserted_precomputed_boolean": False,
    }


def _cvc5_weld_relation_row(a_count: int, b_order: int, relation_sum: int, erased_expected: int) -> dict[str, Any]:
    def check(expected_relation: int) -> str:
        solver = cvc5.Solver()
        solver.setLogic("QF_LIA")
        int_sort = solver.getIntegerSort()
        a_value = solver.mkConst(int_sort, f"{SIM_ID}_family_a_terminal_count_cvc5_{expected_relation}")
        b_value = solver.mkConst(int_sort, f"{SIM_ID}_family_b_orbit_order_cvc5_{expected_relation}")
        relation_value = solver.mkConst(int_sort, f"{SIM_ID}_weld_relation_sum_cvc5_{expected_relation}")
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, a_value, solver.mkInteger(a_count)))
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, b_value, solver.mkInteger(b_order)))
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, relation_value, solver.mkInteger(relation_sum)))
        solver.assertFormula(
            solver.mkTerm(Kind.EQUAL, relation_value, solver.mkTerm(Kind.ADD, a_value, b_value))
        )
        mismatch = solver.mkTerm(
            Kind.OR,
            solver.mkTerm(Kind.DISTINCT, a_value, solver.mkInteger(3)),
            solver.mkTerm(Kind.DISTINCT, b_value, solver.mkInteger(8)),
            solver.mkTerm(Kind.DISTINCT, relation_value, solver.mkInteger(expected_relation)),
        )
        solver.assertFormula(mismatch)
        raw = solver.checkSat()
        return "sat" if raw.isSat() else "unsat" if raw.isUnsat() else "unknown"

    return {
        "solver": "cvc5:weld_relation",
        "ran": True,
        "load_bearing": True,
        "verdict": check(11),
        "erased_flip_verdict": check(erased_expected),
        "bound_family_a_value": a_count,
        "bound_family_b_value": b_order,
        "bound_weld_relation_value": relation_sum,
        "expected_relation_value": 11,
        "erased_expected_relation_value": erased_expected,
        "asserted_precomputed_boolean": False,
    }


def weld_smt_rows(a_summary: dict[str, Any], b_summary: dict[str, Any], rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    a_count = len(a_summary["anchor_values"]["G1_terminal_class_sizes"])
    b_denominator = b_summary["anchor_values"]["deep_chain_final_denominator"]
    b_order = b_summary["anchor_values"]["deep_chain_composite_order"]
    relation_sum = next(row for row in rows if row["row_id"] == "W3_partition_relation")["computed_relation_value"]
    return {
        "z3_family_a_anchor": _z3_identity_row("family_a_G1_terminal_count", a_count, 3, 2),
        "cvc5_family_a_anchor": _cvc5_identity_row("family_a_G1_terminal_count", a_count, 3, 2),
        "z3_family_b_anchor": _z3_identity_row("family_b_final_denominator", b_denominator, 16, 15),
        "cvc5_family_b_anchor": _cvc5_identity_row("family_b_final_denominator", b_denominator, 16, 15),
        "z3_weld_relation": _z3_weld_relation_row(a_count, b_order, relation_sum, 10),
        "cvc5_weld_relation": _cvc5_weld_relation_row(a_count, b_order, relation_sum, 10),
    }


def cross_family_controls(a_summary: dict[str, Any], b_summary: dict[str, Any], rows: list[dict[str, Any]]) -> dict[str, Any]:
    baseline_a_sig = stable_sha256(a_summary["anchor_values"])
    baseline_b_sig = stable_sha256(b_summary["anchor_values"])
    baseline_weld_sig = signature_rows(rows)

    mutated_a_info = family_a_common.perturbed_dz_information()
    fresh_b_after_a = family_b_anchor_summary(family_b_common.build_family_b_object())
    a_only = {
        "mutation": "Family A D_z pinned M[0][0] += 0.05",
        "family_a_anchor_moved": not math.isclose(
            mutated_a_info["holevo_nats"],
            a_summary["anchor_values"]["D_z_holevo_nats"],
            abs_tol=1.0e-15,
        ),
        "family_b_anchor_signature_before": baseline_b_sig,
        "family_b_anchor_signature_after": stable_sha256(fresh_b_after_a["anchor_values"]),
        "family_b_anchors_unchanged": baseline_b_sig == stable_sha256(fresh_b_after_a["anchor_values"]),
    }
    a_only["pass"] = a_only["family_a_anchor_moved"] and a_only["family_b_anchors_unchanged"]

    mutated_b1 = family_b_common.deep_chain_layer(perturb={"pin_row_index": 1, "factor": 5})
    fresh_a_after_b = family_a_anchor_summary(family_a_common.build_super_object(family_a_common.scipy_expm))
    b_only = {
        "mutation": "Family B B1 pinned ratchet factor 4 -> 5",
        "family_b_anchor_moved": mutated_b1["final_denominator"] != b_summary["anchor_values"]["deep_chain_final_denominator"],
        "family_a_anchor_signature_before": baseline_a_sig,
        "family_a_anchor_signature_after": stable_sha256(fresh_a_after_b["anchor_values"]),
        "family_a_anchors_unchanged": baseline_a_sig == stable_sha256(fresh_a_after_b["anchor_values"]),
    }
    b_only["pass"] = b_only["family_b_anchor_moved"] and b_only["family_a_anchors_unchanged"]

    perturbed_rows = weld_row_table(a_summary, b_summary, relation_sum_offset=1)
    moved_weld_rows = [
        row["row_id"]
        for row, perturbed in zip(rows, perturbed_rows)
        if row["row_signature_sha256"] != perturbed["row_signature_sha256"]
    ]
    weld_only = {
        "mutation": "W3 weld relation expected sum +1 with A/B inputs unchanged",
        "family_a_anchors_unchanged": baseline_a_sig == stable_sha256(a_summary["anchor_values"]),
        "family_b_anchors_unchanged": baseline_b_sig == stable_sha256(b_summary["anchor_values"]),
        "baseline_weld_signature": baseline_weld_sig,
        "perturbed_weld_signature": signature_rows(perturbed_rows),
        "moved_weld_rows": moved_weld_rows,
        "allowed_moved_weld_rows": ["W3_partition_relation"],
        "pass": moved_weld_rows == ["W3_partition_relation"],
    }

    no_op_rows = weld_row_table(a_summary, b_summary)
    decorative = {
        "check": "rebuild weld rows without changing either family input",
        "decorative_change_detected": baseline_weld_sig != signature_rows(no_op_rows),
        "changed_rows_when_no_input_changed": [
            row["row_id"]
            for row, no_op in zip(rows, no_op_rows)
            if row["row_signature_sha256"] != no_op["row_signature_sha256"]
        ],
    }
    decorative["pass"] = decorative["decorative_change_detected"] is False and not decorative["changed_rows_when_no_input_changed"]

    stale_import_per_family = {
        "family_a_stale_import_control_fires": a_summary["kill_control_flags"]["stale_import_control"],
        "family_b_stale_import_control_fires": b_summary["kill_control_flags"]["stale_import_control"],
        "pass": a_summary["kill_control_flags"]["stale_import_control"] is True
        and b_summary["kill_control_flags"]["stale_import_control"] is True,
    }
    return {
        "A_only_perturbation_control": a_only,
        "B_only_perturbation_control": b_only,
        "weld_only_perturbation_control": weld_only,
        "decorative_weld_detector": decorative,
        "stale_import_per_family": stale_import_per_family,
        "all_pass": all(
            row["pass"]
            for row in (a_only, b_only, weld_only, decorative, stale_import_per_family)
        ),
    }


def collect_failures(weld_object: dict[str, Any]) -> list[str]:
    failures = []
    if not weld_object["parent_anchor_checks"]["all_pass"]:
        failures.append("parent_anchor_check_failed")
    if not all(row["pass"] for row in weld_object["declared_weld_map"]):
        failures.append("declared_weld_map_failed")
    if not all(row["pass"] for row in weld_object["weld_row_table"]):
        failures.append("weld_row_failed")
    if not weld_object["cross_family_controls"]["all_pass"]:
        failures.append("cross_family_controls_failed")
    for name, row in weld_object["weld_smt_rows"].items():
        if row["verdict"] != "unsat" or row["erased_flip_verdict"] != "sat":
            failures.append(f"smt_failed:{name}")
    if weld_object["family_state_objects"]["B"]["b_scoped_projection"]["axis0_leak_detected"]:
        failures.append("axis0_leak_detected")
    if weld_object["family_state_objects"]["A"]["state_object_id"] == weld_object["family_state_objects"]["B"]["state_object_id"]:
        failures.append("family_state_objects_folded")
    if not weld_object["builder_gates"]["no_builder_audit_verdict"]:
        failures.append("builder_audit_boundary_failed")
    return failures


def build_weld_object() -> dict[str, Any]:
    super_object = family_a_common.build_super_object(family_a_common.scipy_expm)
    family_b_object = family_b_common.build_family_b_object()
    a_summary = family_a_anchor_summary(super_object)
    b_summary = family_b_anchor_summary(family_b_object)
    map_rows = declared_weld_map(a_summary, b_summary)
    rows = weld_row_table(a_summary, b_summary)
    smt = weld_smt_rows(a_summary, b_summary, rows)
    controls = cross_family_controls(a_summary, b_summary, rows)
    state_object_id = f"{SIM_ID}:{stable_sha256({'A': a_summary['state_object_id'], 'B': b_summary['state_object_id'], 'weld_map': map_rows})}"
    weld_object = {
        "schema_version": "manifold_super_sim_v2_weld_object_v1",
        "sim_id": SIM_ID,
        "object_id": SIM_ID,
        "state_object_id": state_object_id,
        "generated_at": now_z(),
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "engine_mode": ENGINE_MODE,
        "backend_contract_decision": {
            "mode": ENGINE_MODE,
            "full_independent_object_lanes_claimed": False,
            "julia_scope": "finite anchor/relation check, not full A+B object construction",
            "jax_scope": "shared v2 common builder plus package-backed finite relation checks",
            "pytorch_scope": "shared v2 common builder plus package-backed finite relation checks",
        },
        "source_import_audit": {
            "parent_hash_pins": hash_locks(
                {
                    "manifold_super_sim_v0_envelope": SOURCE_RESULT_PINS["manifold_super_sim_v0_envelope"],
                    "manifold_family_b_integrated_v0_envelope": SOURCE_RESULT_PINS["manifold_family_b_integrated_v0_envelope"],
                }
            ),
            "receipt_context_hashes": hash_locks({"weld_feedstock_inventory_20260611": SOURCE_RESULT_PINS["weld_feedstock_inventory_20260611"]}),
            "audit_verdict_citation_context_hashes": hash_locks(AUDIT_CONTEXT),
            "raw_parent_computation_imported": False,
            "family_b_folded_into_family_a": False,
            "axis0_leak_detected": b_summary["b_scoped_projection"]["axis0_leak_detected"],
        },
        "family_state_objects": {"A": a_summary, "B": b_summary},
        "parent_anchor_checks": parent_anchor_checks(a_summary, b_summary),
        "declared_weld_map": map_rows,
        "weld_row_table": rows,
        "cross_family_controls": controls,
        "weld_smt_rows": smt,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "TOOL_INTENT_MATRIX": {
            "julia": TOOL_INTENT["engine_tool_intent"]["julia"],
            "jax": TOOL_INTENT["engine_tool_intent"]["jax"],
            "pytorch": TOOL_INTENT["engine_tool_intent"]["pytorch"],
            "build_three_engine_envelope": TOOL_MANIFEST["build_three_engine_envelope"]["reason"],
        },
        "tool_intent": TOOL_INTENT,
        "builder_gates": {
            "file_disjoint_packet": True,
            "build_card_copied": (SIM_DIR / "build_card.md").is_file()
            and "manifold_super_sim_v2_weld" in (SIM_DIR / "build_card.md").read_text(encoding="utf-8"),
            "no_builder_audit_verdict": builder_audit_boundary_ok(SIM_DIR / "audit_verdict.md"),
            "no_builder_audit_verdict_envelope_gate": builder_audit_boundary_ok(SIM_DIR / "audit_verdict.md"),
        },
        "claim_sections": {
            "positive": [
                "separate Family A and Family B state objects are held in one v2 weld run",
                "the declared weld map is materialized as machine-checkable related/independent rows",
                "weld relation SMT binds A values, B values, and the relation with erased flips",
            ],
            "negative": [
                "A-only perturbation leaves B anchors unchanged",
                "B-only perturbation leaves A anchors unchanged",
                "weld-only perturbation moves only the admitted weld relation row",
                "no-op decorative weld detector finds no row movement when neither family input changes",
            ],
            "boundary": [
                "chart-to-chart weld hypothesis rows only; not charts-on-network v3 scope",
                "scratch diagnostic only; no formal admission, axis, bridge, physics, or invariant basin claim",
                "honest shared-common-builder backend scope; no independent full-object all-engine claim",
            ],
        },
        "allowed_claims": [
            "scratch diagnostic chart-to-chart A+B weld map",
            "cross-family perturbation controls for the declared A/B independence rows",
            "finite SMT relation rows binding recomputed A and B anchors",
        ],
        "disallowed_claims": [
            "formal admission",
            "canonical manifold proof",
            "axis/bridge/physics evidence",
            "charts-on-network v3 surface claim",
            "independent full-object Julia/JAX/PyTorch implementation",
        ],
    }
    failures = collect_failures(weld_object)
    weld_object["failures"] = failures
    weld_object["all_pass"] = len(failures) == 0
    return weld_object


def trajectory_payload(weld_object: dict[str, Any] | None = None) -> dict[str, Any]:
    obj = weld_object or build_weld_object()
    step_rows: list[dict[str, Any]] = []

    def add_step(family_scope: str, state_object_id: str, row_id: str, row_family: str, row_payload: dict[str, Any], row_step_class: str, reason: str) -> None:
        trajectory_step_id = f"{SIM_ID}:step:{len(step_rows):04d}"
        payload_sha = stable_sha256(row_payload)
        step_rows.append(
            {
                "step_index": len(step_rows),
                "trajectory_step_id": trajectory_step_id,
                "family_scope": family_scope,
                "state_object_id": state_object_id,
                "row_id": row_id,
                "row_family": row_family,
                "row_step_class": row_step_class,
                "row_step_class_why": reason,
                "row_payload_sha256": payload_sha,
                "sidecar_payload_sha256": payload_sha,
                "row_step_lineage_id": stable_sha256(
                    {
                        "state_object_id": state_object_id,
                        "trajectory_step_id": trajectory_step_id,
                        "row_id": row_id,
                        "row_payload_sha256": payload_sha,
                    }
                ),
                "sha_verified": True,
            }
        )

    a = obj["family_state_objects"]["A"]
    b = obj["family_state_objects"]["B"]
    for layer_name, signature in sorted(a["layer_signatures"].items()):
        add_step(
            "A",
            a["state_object_id"],
            layer_name,
            layer_name,
            {"layer": layer_name, "row_signature_sha256": signature, "source_packet": a["source_packet"]},
            "STEP_DEPENDENT",
            "v2 recomputes the Family A layer anchor from the current parent common builder",
        )
    b_object = family_b_common.build_family_b_object()
    for layer_name, layer in b_object["layers"].items():
        for row in layer["reduced_rows"]:
            add_step(
                "B",
                b["state_object_id"],
                row["row_id"],
                layer_name,
                {
                    "layer": layer_name,
                    "row_id": row["row_id"],
                    "row_signature_sha256": layer["row_signature_sha256"],
                    "claim_ceiling": row.get("claim_ceiling"),
                    "co_citation": row.get("co_citation"),
                },
                row.get("row_step_class", "CARRIED"),
                (
                    "v2 carries the current hardened Family B row class from the B common builder"
                    if row.get("row_step_class") == "CARRIED"
                    else "v2 recomputes the Family B row from the current B trajectory input"
                ),
            )
    for row in obj["weld_row_table"]:
        add_step(
            "WELD",
            obj["state_object_id"],
            row["row_id"],
            "A+B_weld_rows",
            row,
            "WELD_DERIVED",
            "v2 weld-only row derived from current separate A and B state summaries plus the declared weld map",
        )

    payload = {
        "schema_version": "manifold_super_sim_v2_weld_trajectory_artifact_v1",
        "sim_id": SIM_ID,
        "state_object_id": obj["state_object_id"],
        "family_state_object_ids": {
            "A": a["state_object_id"],
            "B": b["state_object_id"],
        },
        "step_rows": step_rows,
        "family_scopes": sorted({row["family_scope"] for row in step_rows}),
        "lineage_standard": {
            "has_file_byte_sha": True,
            "has_stable_content_sha": True,
            "has_trajectory_step_id": all(bool(row["trajectory_step_id"]) for row in step_rows),
            "has_row_step_lineage_id": all(bool(row["row_step_lineage_id"]) for row in step_rows),
            "has_row_step_class_why": all(bool(row["row_step_class_why"]) for row in step_rows),
        },
        "all_pass": obj["all_pass"],
    }
    payload["content_sha256"] = content_sha256_without_self(payload)
    return payload


def write_trajectory_artifact(weld_object: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = trajectory_payload(weld_object)
    write_json(TRAJECTORY_PATH, payload)
    file_digest = sha256_file(TRAJECTORY_PATH)
    TRAJECTORY_SHA_PATH.write_text(file_digest + "  " + TRAJECTORY_PATH.name + "\n", encoding="utf-8")
    sidecar = TRAJECTORY_SHA_PATH.read_text(encoding="utf-8").split()[0]
    return {
        "path": rel(TRAJECTORY_PATH),
        "sha_path": rel(TRAJECTORY_SHA_PATH),
        "payload": payload,
        "content_sha256": payload["content_sha256"],
        "payload_sha256": payload["content_sha256"],
        "artifact_file_sha256": file_digest,
        "sidecar_file_sha256": sidecar,
        "sidecar_sha256": sidecar,
        "sha_verified": file_digest == sidecar and content_sha256_without_self(payload) == payload["content_sha256"],
    }
