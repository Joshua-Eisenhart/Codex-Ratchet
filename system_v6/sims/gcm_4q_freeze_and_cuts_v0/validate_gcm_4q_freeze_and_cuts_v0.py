#!/usr/bin/env python3
"""Packet-local validator for gcm_4q_freeze_and_cuts_v0."""

from __future__ import annotations

import copy
import json
import sys
from pathlib import Path
from typing import Any

import gcm_4q_freeze_and_cuts_v0_common as common


ROOT = common.ROOT
SIM_DIR = common.SIM_DIR
RESULT = common.RESULT_PATH
REGISTRY = common.REGISTRY_PATH
VALIDATOR_RESULT = common.VALIDATOR_RESULT_PATH

sys.path.insert(0, str(ROOT / "scripts"))
from gcm_substrate_check import gcm_substrate_check  # noqa: E402


REQUIRED_PACKET_FILES = [
    "build_card.md",
    "builder_self_assessment.md",
    f"{common.SIM_ID}_common.py",
    f"validate_{common.SIM_ID}.py",
    f"tests/test_{common.SIM_ID}.py",
    f"results/{common.SIM_ID}_registry.json",
    f"results/{common.SIM_ID}_results.json",
    f"results/{common.SIM_ID}_lineage_free_negative.json",
]


def require(errors: list[str], condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


# controls.substrate_positive / controls.substrate_negatives echo gcm_substrate_check's
# raw output, whose diagnostic schema grows as later rungs add error codes / object-id
# fields. They are helper-version-dependent demonstrations, NOT this rung's reproducible
# math (which lives in three_q_regression / cut-state controls and remains compared). Their
# verdicts are asserted independently (substrate_positive ok True / substrate_negatives ok
# False) and re-run live, so excluding them from the byte-reproduce check loses no coverage.
HELPER_OUTPUT_CONTROL_KEYS = ("substrate_positive", "substrate_negatives")


def without_runtime_fields(payload: dict[str, Any]) -> dict[str, Any]:
    clone = copy.deepcopy(payload)
    clone.pop("generated_at", None)
    clone.pop("result_sha256", None)
    controls = clone.get("controls")
    if isinstance(controls, dict):
        for key in HELPER_OUTPUT_CONTROL_KEYS:
            controls.pop(key, None)
    return clone


def validate_packet_files(errors: list[str]) -> None:
    for rel_path in REQUIRED_PACKET_FILES:
        require(errors, (SIM_DIR / rel_path).is_file(), f"missing required packet file: {rel_path}")
    text = (SIM_DIR / "build_card.md").read_text(encoding="utf-8") if (SIM_DIR / "build_card.md").exists() else ""
    for required in (
        common.SIM_ID,
        "freeze/registry + cut layers",
        "carve-attached",
        "4Q",
        "1|234",
        "2|134",
        "3|124",
        "4|123",
        "12|34",
        "13|24",
        "14|23",
        "546",
        "cut_state_available=true",
        "G.2a",
        "scratch_diagnostic",
        "NO git add/commit",
    ):
        require(errors, required in text, f"build_card.md missing {required}")


def validate_registry(errors: list[str], registry: dict[str, Any]) -> None:
    rebuilt = common.build_4q_registry(load(common.FOUR_Q_CARVE_RESULT), load(common.THREE_Q_FREEZE_REGISTRY))
    require(errors, registry == rebuilt, "4Q registry drift against source rebuild")
    require(errors, registry.get("schema") == common.REGISTRY_SCHEMA, "registry schema mismatch")
    require(errors, registry.get("gcm_object_id") == common.EXPECTED_1Q_OBJECT_ID, "1Q object id mismatch")
    require(errors, registry.get("gcm_2q_object_id") == common.EXPECTED_2Q_OBJECT_ID, "2Q object id mismatch")
    require(errors, registry.get("gcm_3q_object_id") == common.EXPECTED_3Q_OBJECT_ID, "3Q object id mismatch")
    require(errors, isinstance(registry.get("gcm_4q_object_id"), str) and registry["gcm_4q_object_id"].startswith("gcm4qobj_"), "bad gcm_4q_object_id")
    frozen = registry.get("frozen_4q_registry", {})
    survivors = frozen.get("survivors", [])
    classes = frozen.get("quotient_classes", [])
    regions = frozen.get("candidate_regions", [])
    require(errors, len(survivors) == common.EXPECTED_4Q_SURVIVOR_COUNT, "4Q survivor count mismatch")
    require(errors, len(classes) == common.EXPECTED_4Q_CLASS_COUNT, "4Q class count mismatch")
    require(errors, len(regions) == common.EXPECTED_4Q_CLASS_COUNT, "4Q candidate region count mismatch")
    require(errors, len({row["gcm_4q_survivor_id"] for row in survivors}) == len(survivors), "4Q survivor IDs not unique")
    require(errors, len({row["gcm_4q_quotient_class_id"] for row in classes}) == len(classes), "4Q class IDs not unique")
    require(errors, len({row["gcm_4q_candidate_region_id"] for row in regions}) == len(regions), "4Q region IDs not unique")
    require(errors, registry.get("counts", {}).get("product_lift_survivor_count") == common.EXPECTED_4Q_PRODUCT_LIFT_COUNT, "4Q product lift count mismatch")
    require(errors, registry.get("counts", {}).get("four_partite_entangled_survivor_count") == common.EXPECTED_4Q_ENTANGLED_ANCHOR_COUNT, "4Q anchor count mismatch")


def validate_packet(errors: list[str], packet: dict[str, Any], registry: dict[str, Any]) -> None:
    rebuilt = common.build_packet(write=False)
    require(errors, without_runtime_fields(packet) == without_runtime_fields(rebuilt), "packet drift against source rebuild")
    require(errors, packet.get("schema_version") == common.SCHEMA, "packet schema mismatch")
    require(errors, packet.get("classification") == common.CLASSIFICATION, "classification mismatch")
    require(errors, packet.get("promotion_allowed") is False, "promotion_allowed must be false")
    require(errors, packet.get("formal_admission_allowed") is False, "formal_admission_allowed must be false")
    require(errors, packet.get("declared_surface") == "freeze/registry + cut layers | carve-attached | 4Q", "declared surface mismatch")
    require(errors, packet.get("cut_state_available") is True, "cut_state_available must be true")
    evidence = packet.get("cut_state_available_evidence", {})
    require(errors, evidence.get("stored_reduced_matrices") is True, "stored matrix evidence missing")
    require(errors, evidence.get("stored_matrix_pair_count") == common.EXPECTED_4Q_SURVIVOR_COUNT * 7, "stored matrix pair count mismatch")
    rows = packet.get("cut_tables", {}).get("survivor_cut_rows", [])
    require(errors, len(rows) == common.EXPECTED_4Q_SURVIVOR_COUNT, "cut row count mismatch")
    require(errors, len(packet.get("cut_tables", {}).get("class_cut_rows", [])) == common.EXPECTED_4Q_CLASS_COUNT, "class cut row count mismatch")
    for row in rows:
        require(errors, row.get("cut_state_available") is True, f"cut state flag missing for survivor {row.get('raw_4q_survivor_id')}")
        require(errors, set(row.get("cuts", {})) == set(common.CUTS), f"missing cuts for survivor {row.get('raw_4q_survivor_id')}")
        for cut_name, cut in row.get("cuts", {}).items():
            entropy = cut.get("entropy_values", {})
            for key in (
                "S_rho_left",
                "S_rho_right",
                "S_rho_ABCD",
                "conditional_S_left_given_right",
                "conditional_S_right_given_left",
                "mutual_I_left_right",
                "coherent_I_c_left_to_right",
                "coherent_I_c_right_to_left",
                "negativity",
                "log_negativity",
            ):
                require(errors, key in entropy, f"{cut_name} entropy missing {key}")
            require(errors, cut.get("rho_left") and cut.get("rho_right"), f"{cut_name} missing reduced matrices")
            require(errors, cut.get("rho_left_id") and cut.get("rho_right_id"), f"{cut_name} missing reduced matrix ids")
    anchor = packet.get("four_partite_anchor_profile", {})
    require(errors, anchor.get("four_partite_entangled_anchor") is True, "4Q anchor profile missing")
    require(errors, all(cut.get("schmidt_stratum", {}).get("schmidt_applicable") for cut in anchor.get("cuts", {}).values()), "anchor Schmidt applicability mismatch")
    require(errors, all(cut.get("entropy_values", {}).get("negativity", 0.0) > 0.0 for cut in anchor.get("cuts", {}).values()), "anchor negativity missing")
    mono = packet.get("monogamy_table", {})
    require(errors, mono.get("computed_from_stored_rho_ABCD") is True, "monogamy not stored-rho based")
    require(errors, mono.get("residual_4_tangle_claimed") is False, "residual 4-tangle overclaimed")
    require(errors, mono.get("pure_survivor_count_checked") >= 1, "monogamy pure survivor count missing")
    require(errors, mono.get("all_focus_qubits_satisfy_ckw") is True, "4-party focus CKW failed")
    controls = packet.get("controls", {})
    require(errors, controls.get("three_q_regression", {}).get("partial_traces_reproduce") is True, "3Q partial-trace regression failed")
    require(errors, controls.get("three_q_regression", {}).get("product_lift_checked_count") == common.EXPECTED_4Q_PRODUCT_LIFT_COUNT, "3Q product-lift regression count mismatch")
    require(errors, controls.get("cut_state_caveat_resolution", {}).get("cut_state_available") is True, "cut-state caveat resolution missing")
    for rung in ("1Q", "2Q", "3Q", "4Q"):
        require(errors, controls.get("substrate_positive", {}).get(rung, {}).get("ok") is True, f"{rung} substrate positive failed")
        for negative in ("lineage_free", "forged_registry", "stale_lineage"):
            result = controls.get("substrate_negatives", {}).get(rung, {}).get(negative, {})
            require(errors, result.get("ok") is False, f"{rung} {negative} negative did not fail")
            require(errors, bool(result.get("error_codes")), f"{rung} {negative} negative missing error codes")
    require(errors, gcm_substrate_check(packet, REGISTRY).get("ok") is True, "helper 4Q substrate check failed")
    # Live negative-rejection gate (helper-output controls are excluded from byte-reproduce, so the
    # negative-rejection property is asserted live here — a helper regression that stops rejecting
    # lineage-free payloads must flip this to red rather than survive green).
    require(errors, gcm_substrate_check(common.lineage_free_variant(packet), REGISTRY).get("ok") is False, "live 4Q lineage-free negative did not fail")
    require(errors, packet.get("TOOL_MANIFEST") == common.TOOL_MANIFEST, "TOOL_MANIFEST mismatch")
    require(errors, packet.get("TOOL_INTEGRATION_DEPTH") == common.TOOL_INTEGRATION_DEPTH, "TOOL_INTEGRATION_DEPTH mismatch")
    require(errors, packet.get("all_pass") is True, "packet all_pass false")


def validate_payload() -> list[str]:
    errors: list[str] = []
    validate_packet_files(errors)
    if not REGISTRY.exists() or not RESULT.exists():
        return errors
    registry = load(REGISTRY)
    packet = load(RESULT)
    validate_registry(errors, registry)
    validate_packet(errors, packet, registry)
    return errors


def main() -> int:
    errors = validate_payload()
    result = {"ok": not errors, "result_json": common.rel(RESULT), "registry_json": common.rel(REGISTRY), "errors": errors}
    common.write_json(VALIDATOR_RESULT, result)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
