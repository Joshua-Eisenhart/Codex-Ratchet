#!/usr/bin/env python3
"""Validate the gcm_qca_runner_2q_v1 packet."""

from __future__ import annotations

import json
from pathlib import Path
import sys
from typing import Any

from gcm_qca_runner_2q_v1_common import (
    BASE_REGISTRY_BODY_SHA256,
    CARVE_PREDICATE_TEXT_SHA256,
    CLAIM_CEILING,
    COORDINATES,
    ENVELOPE_PATH,
    GCM_2Q_OBJECT_ID,
    GCM_2Q_REGISTRY_BODY_SHA256,
    LINEAGE_FREE_NEGATIVE_PATH,
    REGISTRY_PATH,
    RESULT_PATH,
    SIM_DIR,
    SIM_ID,
    TOOL_INTEGRATION_DEPTH,
    TOOL_MANIFEST,
    VALIDATOR_RESULT_PATH,
    build_envelope,
    build_packet,
    builder_audit_boundary_errors,
    gcm_substrate_check,
    load_json,
    packet_hash_payload,
    rel,
    stable_sha256,
    write_json,
)


REQUIRED_FILES = [
    "build_card.md",
    "builder_self_assessment.md",
    "gcm_qca_runner_2q_v1.py",
    "gcm_qca_runner_2q_v1_common.py",
    "gcm_qca_runner_2q_v1_envelope.py",
    "validate_gcm_qca_runner_2q_v1.py",
    "tests/test_gcm_qca_runner_2q_v1.py",
]


def add(errors: list[str], code: str, detail: str) -> None:
    errors.append(f"{code}: {detail}")


def scrub_volatile(payload: dict[str, Any]) -> dict[str, Any]:
    out = json.loads(json.dumps(payload))
    out.pop("generated_at", None)
    out.pop("result_sha256", None)
    if "source_locks" in out and isinstance(out["source_locks"], dict):
        out["source_locks"].pop("2q_carve_result", None)
    return out


def rows_by_id(packet: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {row["rule_id"]: row for row in packet["qca_index_rows"]}


def validate_packet(packet: dict[str, Any], envelope: dict[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []

    for rel_path in REQUIRED_FILES:
        if not (SIM_DIR / rel_path).is_file():
            add(errors, "MISSING_FILE", rel_path)

    if packet.get("sim_id") != SIM_ID:
        add(errors, "SIM_ID", str(packet.get("sim_id")))
    if packet.get("classification") != "scratch_diagnostic":
        add(errors, "CLASSIFICATION", str(packet.get("classification")))
    if packet.get("claim_ceiling") != CLAIM_CEILING:
        add(errors, "CLAIM_CEILING", str(packet.get("claim_ceiling")))
    if packet.get("promotion_allowed") is not False or packet.get("formal_admission_allowed") is not False:
        add(errors, "PROMOTION_BOUNDARY", "promotion/formal admission must be false")
    if packet.get("carrier_and_pins_relative") is not True:
        add(errors, "CARRIER_BOUNDARY", "carrier_and_pins_relative must be true")
    if packet.get("coordinates") != COORDINATES:
        add(errors, "COORDINATES", str(packet.get("coordinates")))
    if packet.get("gcm_2q_object_id") != GCM_2Q_OBJECT_ID:
        add(errors, "GCM2Q_OBJECT_ID", str(packet.get("gcm_2q_object_id")))
    if packet.get("gcm_2q_registry_body_sha256") != GCM_2Q_REGISTRY_BODY_SHA256:
        add(errors, "GCM2Q_HASH", str(packet.get("gcm_2q_registry_body_sha256")))
    if packet.get("base_registry_body_sha256") != BASE_REGISTRY_BODY_SHA256:
        add(errors, "BASE_HASH", str(packet.get("base_registry_body_sha256")))
    if not packet.get("registry_dependency", {}).get("claims_conditional_on_audit_verdict"):
        add(errors, "AUDIT_CONDITION", "2Q dependency must be conditional on in-flight audit verdict")

    expected_hash = stable_sha256(packet_hash_payload(packet))
    if packet.get("result_sha256") != expected_hash:
        add(errors, "RESULT_HASH", f"expected={expected_hash} actual={packet.get('result_sha256')}")

    rebuilt = build_packet()
    if scrub_volatile(packet) != scrub_volatile(rebuilt):
        add(errors, "REBUILD_DRIFT", "stored packet differs from rebuilt nonvolatile payload")

    positive = gcm_substrate_check(packet, REGISTRY_PATH)
    if not positive["ok"]:
        add(errors, "SUBSTRATE_POSITIVE", json.dumps(positive, sort_keys=True))
    negative = gcm_substrate_check(load_json(LINEAGE_FREE_NEGATIVE_PATH), REGISTRY_PATH)
    if negative["ok"]:
        add(errors, "SUBSTRATE_NEGATIVE", "lineage-free negative unexpectedly passed")
    required_negative_codes = {
        "GCM_OBJECT_ID_MISMATCH",
        "GCM2Q_LINEAGE_REGISTRY_BODY_SHA256_MISMATCH",
        "GCM_LINEAGE_BASE_REGISTRY_BODY_SHA256_MISMATCH",
        "GCM_LINEAGE_CONSUMPTION_MISSING",
    }
    if not required_negative_codes.issubset(set(negative.get("error_codes", []))):
        add(errors, "SUBSTRATE_NEGATIVE_CODES", json.dumps(negative.get("error_codes", []), sort_keys=True))

    by_id = rows_by_id(packet)
    expected_indices = {
        "calibration_right_shift": (1, 2, "4/1", 16, 1),
        "calibration_left_shift": (-1, -2, "1/4", 1, 16),
        "nonchiral_onsite_index0": (0, 0, "1/1", 1, 1),
        "balanced_pair_swap_index0": (0, 0, "1/1", 16, 16),
        "engine_L_flux_IN_left_O1": (-1, -2, "1/4", 1, 16),
        "engine_R_flux_OUT_right_O1": (1, 2, "4/1", 16, 1),
        "gauge_inserted_R_engine": (1, 2, "4/1", 16, 1),
        "reflected_L_spatial_to_R": (1, 2, "4/1", 16, 1),
        "v0_constructor_swap_regression": (1, 2, "4/1", 16, 1),
    }
    for rule_id, (signed_local, signed_log2, ratio, right_rank, left_rank) in expected_indices.items():
        row = by_id.get(rule_id)
        if not row:
            add(errors, "MISSING_RULE_ROW", rule_id)
            continue
        if row.get("signed_log_local_dim_index") != signed_local:
            add(errors, "SIGNED_LOCAL_INDEX", f"{rule_id}: {row.get('signed_log_local_dim_index')}")
        if row.get("signed_log2_index") != signed_log2:
            add(errors, "SIGNED_LOG2_INDEX", f"{rule_id}: {row.get('signed_log2_index')}")
        if row.get("index_ratio") != ratio:
            add(errors, "INDEX_RATIO", f"{rule_id}: {row.get('index_ratio')}")
        if row.get("right_crossing_support_rank", {}).get("rank") != right_rank:
            add(errors, "RIGHT_RANK", f"{rule_id}: {row.get('right_crossing_support_rank', {}).get('rank')}")
        if row.get("left_crossing_support_rank", {}).get("rank") != left_rank:
            add(errors, "LEFT_RANK", f"{rule_id}: {row.get('left_crossing_support_rank', {}).get('rank')}")
        if row.get("metadata_flow_fields_present") is not False:
            add(errors, "METADATA_FLOW", rule_id)
        if row.get("unitarity_error_frobenius", 1.0) > 1.0e-8:
            add(errors, "UNITARITY", f"{rule_id}: {row.get('unitarity_error_frobenius')}")

    if not packet.get("chirality_row", {}).get("opposite"):
        add(errors, "CHIRALITY", "L/R indices are not opposite")
    if packet.get("quantization_check", {}).get("all_indices_integer") is not True:
        add(errors, "QUANTIZATION_INTEGER", "false")
    if packet.get("quantization_check", {}).get("all_signed_log2_multiples_of_site_qubits") is not True:
        add(errors, "QUANTIZATION_LOG2", "false")
    controls = packet.get("controls", {})
    for key in (
        "L_R_opposite",
        "reflected_L_flips_index_sign",
        "v0_constructor_regression_reproduces_R_index",
        "nonchiral_rule_index_zero",
        "balanced_swap_control_index_zero",
        "gauge_inserted_R_preserves_index",
    ):
        if controls.get(key) is not True:
            add(errors, "CONTROL", f"{key}={controls.get(key)}")
    mirror = packet.get("mirror_repair", {})
    if mirror.get("uses_brickwork_engine_for_reflection") is not False:
        add(errors, "MIRROR_CONSTRUCTOR_RECALL", str(mirror.get("uses_brickwork_engine_for_reflection")))
    if mirror.get("bare_reflected_L_equals_R") is not False:
        add(errors, "MIRROR_BARE_EXPECTATION", str(mirror.get("bare_reflected_L_equals_R")))
    if mirror.get("bare_reflected_L_vs_R_max_abs_diff", 0.0) <= 1.0e-8:
        add(errors, "MIRROR_BARE_DIFF", str(mirror.get("bare_reflected_L_vs_R_max_abs_diff")))
    if mirror.get("reflection_involution", {}).get("passes") is not True:
        add(errors, "MIRROR_INVOLUTION", str(mirror.get("reflection_involution")))
    if mirror.get("non_mirror_permutation_negative", {}).get("red_as_expected") is not True:
        add(errors, "NON_MIRROR_NEGATIVE", str(mirror.get("non_mirror_permutation_negative")))
    if mirror.get("v0_constructor_swap_regression", {}).get("verdict") != "BY_CONSTRUCTION":
        add(errors, "CONSTRUCTOR_REGRESSION_VERDICT", str(mirror.get("v0_constructor_swap_regression")))
    if mirror.get("v0_constructor_swap_regression", {}).get("equals_R") is not True:
        add(errors, "CONSTRUCTOR_REGRESSION", str(mirror.get("v0_constructor_swap_regression")))
    if mirror.get("dressed_conjugacy", {}).get("passes_tolerance") is not True:
        add(errors, "DRESSED_CONJUGACY", str(mirror.get("dressed_conjugacy")))
    if packet.get("chirality_row", {}).get("independent_reflection_reproduces_R_index") is not True:
        add(errors, "REFLECTED_INDEX", str(packet.get("chirality_row")))

    qca_boundary = packet.get("qca_boundary", {})
    if qca_boundary.get("finite_ring_nonzero_gnvw_claim") != "not_claimed":
        add(errors, "FINITE_RING_FENCE", str(qca_boundary.get("finite_ring_nonzero_gnvw_claim")))
    fence = qca_boundary.get("runtime_flux_family_fence", "")
    if "J_ent" not in fence or "J_cut" not in fence or "gated on 3Q" not in fence:
        add(errors, "3Q_FLUX_FENCE", fence)
    if packet.get("ring_locality_witness", {}).get("strict_light_cone_one_site_per_half_step") is not True:
        add(errors, "RING_LIGHT_CONE", "false")

    m_c_summary = packet.get("M_C_preservation_summary", {})
    if m_c_summary.get("all_rows_preserve_M_C") is not True:
        add(errors, "M_C_PRESERVATION", "false")
    if m_c_summary.get("predicate_text_sha256") != CARVE_PREDICATE_TEXT_SHA256:
        add(errors, "M_C_HASH", str(m_c_summary.get("predicate_text_sha256")))
    for row in packet.get("M_C_preservation_by_rule", []):
        if row.get("carve_predicate_text_sha256") != CARVE_PREDICATE_TEXT_SHA256:
            add(errors, "M_C_ROW_HASH", row.get("rule_id", "<missing>"))
        if row.get("preserves_M_C_at_2Q") is not True:
            add(errors, "M_C_ROW_BOOL", row.get("rule_id", "<missing>"))

    if packet.get("TOOL_MANIFEST") != TOOL_MANIFEST:
        add(errors, "TOOL_MANIFEST", "drift")
    if packet.get("TOOL_INTEGRATION_DEPTH") != TOOL_INTEGRATION_DEPTH:
        add(errors, "TOOL_DEPTH", "drift")
    for tool, depth in TOOL_INTEGRATION_DEPTH.items():
        if depth == "load_bearing" and packet.get("TOOL_MANIFEST", {}).get(tool, {}).get("role") != "load_bearing":
            add(errors, "TOOL_LOAD_BEARING", tool)

    if not packet.get("z3_index_contract", {}).get("contract_proved"):
        add(errors, "Z3_CONTRACT", str(packet.get("z3_index_contract")))
    if not packet.get("cvc5_index_contract", {}).get("contract_proved"):
        add(errors, "CVC5_CONTRACT", str(packet.get("cvc5_index_contract")))
    if not packet.get("z3_index_contract", {}).get("same_sign_mutation_killed"):
        add(errors, "Z3_MUTATION", str(packet.get("z3_index_contract")))
    if not packet.get("cvc5_index_contract", {}).get("same_sign_mutation_killed"):
        add(errors, "CVC5_MUTATION", str(packet.get("cvc5_index_contract")))

    g2a_errors = builder_audit_boundary_errors(packet.get("builder_audit_boundary", {}), SIM_DIR / "audit_verdict.md")
    if g2a_errors:
        add(errors, "BUILDER_G2A", json.dumps(g2a_errors, sort_keys=True))

    rebuilt_envelope = build_envelope(packet)
    stored_envelope = dict(envelope)
    stored_envelope.pop("generated_at", None)
    stored_envelope.pop("envelope_sha256", None)
    rebuilt_envelope.pop("generated_at", None)
    rebuilt_envelope.pop("envelope_sha256", None)
    if stored_envelope != rebuilt_envelope:
        add(errors, "ENVELOPE_DRIFT", "stored envelope differs from rebuilt nonvolatile payload")
    if envelope.get("all_pass") is not True:
        add(errors, "ENVELOPE_ALL_PASS", str(envelope.get("all_pass")))

    build_card = (SIM_DIR / "build_card.md").read_text(encoding="utf-8") if (SIM_DIR / "build_card.md").is_file() else ""
    for phrase in (
        "dynamics | integrated-onto-the-carve | 2Q",
        "scratch_diagnostic",
        "carrier-and-pins-relative",
        "J_ent",
        "J_cut",
        "gated on 3Q",
    ):
        if phrase not in build_card:
            add(errors, "BUILD_CARD_PHRASE", phrase)

    return {
        "ok": not errors,
        "errors": errors,
        "warnings": warnings,
        "result_path": rel(RESULT_PATH),
        "envelope_path": rel(ENVELOPE_PATH),
        "lineage_free_negative_path": rel(LINEAGE_FREE_NEGATIVE_PATH),
        "substrate_positive_ok": positive["ok"],
        "lineage_free_negative_red": not negative["ok"],
        "rule_count": len(packet.get("qca_index_rows", [])),
    }


def main() -> None:
    if not RESULT_PATH.is_file() or not ENVELOPE_PATH.is_file() or not LINEAGE_FREE_NEGATIVE_PATH.is_file():
        from gcm_qca_runner_2q_v1_common import write_envelope, write_result

        packet = write_result()
        write_envelope(packet)

    result = validate_packet(load_json(RESULT_PATH), load_json(ENVELOPE_PATH))
    write_json(VALIDATOR_RESULT_PATH, result)
    print(json.dumps(result, indent=2, sort_keys=True))
    raise SystemExit(0 if result["ok"] else 1)


if __name__ == "__main__":
    main()
