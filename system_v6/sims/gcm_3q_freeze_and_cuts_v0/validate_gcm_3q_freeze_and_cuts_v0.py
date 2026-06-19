#!/usr/bin/env python3
"""Packet-local validator for gcm_3q_freeze_and_cuts_v0."""

from __future__ import annotations

import copy
import json
import sys
from pathlib import Path
from typing import Any

import gcm_3q_freeze_and_cuts_v0_common as common


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
# math (which lives in two_q_regression / cut-state controls and remains compared). Their
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
        "3Q",
        "A|BC",
        "B|AC",
        "C|AB",
        "545",
        "CKW",
        "G.2a",
        "scratch_diagnostic",
        "runtime flux is blocked",
        "NO git add/commit",
    ):
        require(errors, required in text, f"build_card.md missing {required}")


def validate_registry(errors: list[str], registry: dict[str, Any]) -> None:
    rebuilt = common.build_3q_registry(load(common.THREE_Q_CARVE_RESULT), load(common.TWO_Q_FREEZE_REGISTRY))
    require(errors, registry == rebuilt, "3Q registry drift against source rebuild")
    require(errors, registry.get("schema") == common.REGISTRY_SCHEMA, "registry schema mismatch")
    require(errors, registry.get("gcm_object_id") == common.EXPECTED_1Q_OBJECT_ID, "1Q object id mismatch")
    require(errors, registry.get("gcm_2q_object_id") == common.EXPECTED_2Q_OBJECT_ID, "2Q object id mismatch")
    require(errors, isinstance(registry.get("gcm_3q_object_id"), str) and registry["gcm_3q_object_id"].startswith("gcm3qobj_"), "bad gcm_3q_object_id")
    frozen = registry.get("frozen_3q_registry", {})
    survivors = frozen.get("survivors", [])
    classes = frozen.get("quotient_classes", [])
    regions = frozen.get("candidate_regions", [])
    require(errors, len(survivors) == common.EXPECTED_3Q_SURVIVOR_COUNT, "3Q survivor count mismatch")
    require(errors, len(classes) == common.EXPECTED_3Q_CLASS_COUNT, "3Q class count mismatch")
    require(errors, len(regions) >= 1, "3Q candidate regions missing")
    require(errors, len({row["gcm_3q_survivor_id"] for row in survivors}) == len(survivors), "3Q survivor IDs not unique")
    require(errors, len({row["gcm_3q_quotient_class_id"] for row in classes}) == len(classes), "3Q class IDs not unique")
    require(errors, len({row["gcm_3q_candidate_region_id"] for row in regions}) == len(regions), "3Q region IDs not unique")
    require(errors, registry.get("counts", {}).get("product_lift_survivor_count") == common.EXPECTED_3Q_PRODUCT_LIFT_COUNT, "3Q product lift count mismatch")
    require(errors, registry.get("counts", {}).get("tripartite_entangled_survivor_count") == common.EXPECTED_3Q_TRIPARTITE_ANCHOR_COUNT, "3Q anchor count mismatch")


def validate_packet(errors: list[str], packet: dict[str, Any], registry: dict[str, Any]) -> None:
    rebuilt = common.build_packet(write=False)
    require(errors, without_runtime_fields(packet) == without_runtime_fields(rebuilt), "packet drift against source rebuild")
    require(errors, packet.get("schema_version") == common.SCHEMA, "packet schema mismatch")
    require(errors, packet.get("classification") == common.CLASSIFICATION, "classification mismatch")
    require(errors, packet.get("promotion_allowed") is False, "promotion_allowed must be false")
    require(errors, packet.get("formal_admission_allowed") is False, "formal_admission_allowed must be false")
    require(errors, packet.get("runtime_flux_blocked") is True, "runtime flux must be blocked")
    require(errors, packet.get("declared_surface") == "freeze/registry + cut layers | carve-attached | 3Q", "declared surface mismatch")
    rows = packet.get("cut_tables", {}).get("survivor_cut_rows", [])
    require(errors, len(rows) == common.EXPECTED_3Q_SURVIVOR_COUNT, "cut row count mismatch")
    require(errors, len(packet.get("cut_tables", {}).get("class_cut_rows", [])) == common.EXPECTED_3Q_CLASS_COUNT, "class cut row count mismatch")
    for row in rows:
        require(errors, set(row.get("cuts", {})) == set(common.CUTS), f"missing cuts for survivor {row.get('raw_3q_survivor_id')}")
        for cut_name, cut in row.get("cuts", {}).items():
            entropy = cut.get("entropy_values", {})
            for key in (
                "S_rho_left",
                "S_rho_right",
                "S_rho_ABC",
                "conditional_S_left_given_right",
                "conditional_S_right_given_left",
                "mutual_I_left_right",
                "coherent_I_c_left_to_right",
                "coherent_I_c_right_to_left",
                "negativity",
            ):
                require(errors, key in entropy, f"{cut_name} entropy missing {key}")
            require(errors, cut.get("rho_left") and cut.get("rho_right"), f"{cut_name} missing reduced matrices")
    anchor = packet.get("tripartite_only_anchor_profile", {})
    require(errors, anchor.get("tripartite_entangled_anchor") is True, "tripartite anchor profile missing")
    require(errors, all(cut.get("schmidt_stratum", {}).get("schmidt_rank") == 2 for cut in anchor.get("cuts", {}).values()), "anchor Schmidt rank mismatch")
    ckw = packet.get("monogamy_table", {})
    require(errors, ckw.get("computed_from_stored_rho_ABC") is True, "CKW not stored-rho based")
    require(errors, ckw.get("entangled_survivor_count_checked") == common.EXPECTED_3Q_TRIPARTITE_ANCHOR_COUNT, "CKW entangled count mismatch")
    require(errors, ckw.get("all_party_cuts_satisfy_ckw") is True, "CKW failed")
    controls = packet.get("controls", {})
    require(errors, controls.get("two_q_regression", {}).get("partial_traces_reproduce") is True, "2Q partial-trace regression failed")
    require(errors, controls.get("two_q_regression", {}).get("product_lift_checked_count") == common.EXPECTED_3Q_PRODUCT_LIFT_COUNT, "2Q product-lift regression count mismatch")
    require(errors, controls.get("two_q_regression", {}).get("full_rho_AB_reproduced_product_rows") == 528, "2Q full product-row regression count mismatch")
    require(errors, controls.get("two_q_regression", {}).get("full_rho_AB_correlation_not_claimed_rows") == 16, "2Q entangled correlation boundary count mismatch")
    for rung in ("1Q", "2Q", "3Q"):
        require(errors, controls.get("substrate_positive", {}).get(rung, {}).get("ok") is True, f"{rung} substrate positive failed")
        for negative in ("lineage_free", "forged_registry", "stale_lineage"):
            result = controls.get("substrate_negatives", {}).get(rung, {}).get(negative, {})
            require(errors, result.get("ok") is False, f"{rung} {negative} negative did not fail")
            require(errors, bool(result.get("error_codes")), f"{rung} {negative} negative missing error codes")
    require(errors, gcm_substrate_check(packet, REGISTRY).get("ok") is True, "helper 3Q substrate check failed")
    # Live negative-rejection gate (helper-output controls are excluded from byte-reproduce, so the
    # negative-rejection property is asserted live here — a helper regression that stops rejecting
    # lineage-free payloads must flip this to red rather than survive green).
    require(errors, gcm_substrate_check(common.lineage_free_variant(packet), REGISTRY).get("ok") is False, "live 3Q lineage-free negative did not fail")
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
