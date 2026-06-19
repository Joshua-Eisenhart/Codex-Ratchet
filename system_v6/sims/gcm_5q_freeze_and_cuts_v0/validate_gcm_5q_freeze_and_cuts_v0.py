#!/usr/bin/env python3
"""Packet-local validator for gcm_5q_freeze_and_cuts_v0."""

from __future__ import annotations

import copy
import json
import sys
from pathlib import Path
from typing import Any

import gcm_5q_freeze_and_cuts_v0_common as common


SIM_DIR = common.SIM_DIR
RESULT = common.RESULT_PATH
REGISTRY = common.REGISTRY_PATH
VALIDATOR_RESULT = common.VALIDATOR_RESULT_PATH

sys.path.insert(0, str(common.ROOT / "scripts"))
from gcm_substrate_check import gcm_substrate_check  # noqa: E402


REQUIRED_PACKET_FILES = [
    "build_card.md",
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


def without_runtime_fields(payload: dict[str, Any]) -> dict[str, Any]:
    clone = copy.deepcopy(payload)
    clone.pop("generated_at", None)
    clone.pop("result_sha256", None)
    clone.pop("file_size_guard", None)
    clone.pop("builder_gates", None)
    clone.pop("all_pass", None)
    controls = clone.get("controls")
    if isinstance(controls, dict):
        controls.pop("substrate_positive", None)
        controls.pop("substrate_negatives", None)
    return clone


def validate_packet_files(errors: list[str]) -> None:
    for rel_path in REQUIRED_PACKET_FILES:
        require(errors, (SIM_DIR / rel_path).is_file(), f"missing required packet file: {rel_path}")
    text = (SIM_DIR / "build_card.md").read_text(encoding="utf-8") if (SIM_DIR / "build_card.md").exists() else ""
    for required in (
        common.SIM_ID,
        "5Q freeze/registry",
        "Cl(10)",
        "1024",
        "547",
        "9",
        "15",
        "cut_state_available=true",
        "hash-per-(survivor,cut)",
        "sample full reduced matrices",
        "scratch_diagnostic",
        "NO git add/commit",
    ):
        require(errors, required in text, f"build_card.md missing {required}")


def validate_registry(errors: list[str], registry: dict[str, Any]) -> None:
    rebuilt = common.build_5q_registry(load(common.FIVE_Q_CARVE_RESULT), load(common.FOUR_Q_FREEZE_REGISTRY))
    require(errors, registry == rebuilt, "5Q registry drift against source rebuild")
    require(errors, registry.get("schema") == common.REGISTRY_SCHEMA, "registry schema mismatch")
    require(errors, registry.get("gcm_object_id") == common.EXPECTED_1Q_OBJECT_ID, "1Q object id mismatch")
    require(errors, registry.get("gcm_2q_object_id") == common.EXPECTED_2Q_OBJECT_ID, "2Q object id mismatch")
    require(errors, registry.get("gcm_3q_object_id") == common.EXPECTED_3Q_OBJECT_ID, "3Q object id mismatch")
    require(errors, registry.get("gcm_4q_object_id") == common.EXPECTED_4Q_OBJECT_ID, "4Q object id mismatch")
    require(errors, isinstance(registry.get("gcm_5q_object_id"), str) and registry["gcm_5q_object_id"].startswith("gcm5qobj_"), "bad gcm_5q_object_id")
    frozen = registry.get("frozen_5q_registry", {})
    survivors = frozen.get("survivors", [])
    classes = frozen.get("quotient_classes", [])
    regions = frozen.get("candidate_regions", [])
    require(errors, len(survivors) == common.EXPECTED_5Q_SURVIVOR_COUNT, "5Q survivor count mismatch")
    require(errors, len(classes) == common.EXPECTED_5Q_CLASS_COUNT, "5Q class count mismatch")
    require(errors, len(regions) == common.EXPECTED_5Q_REGION_COUNT, "5Q candidate region count mismatch")
    require(errors, len({row["gcm_5q_survivor_id"] for row in survivors}) == len(survivors), "5Q survivor IDs not unique")
    require(errors, len({row["gcm_5q_quotient_class_id"] for row in classes}) == len(classes), "5Q class IDs not unique")
    require(errors, len({row["gcm_5q_candidate_region_id"] for row in regions}) == len(regions), "5Q region IDs not unique")
    counts = registry.get("counts", {})
    require(errors, counts.get("survivor_count") == common.EXPECTED_5Q_SURVIVOR_COUNT, "registry survivor count mismatch")
    require(errors, counts.get("killed_count") == common.EXPECTED_5Q_KILLED_COUNT, "registry killed count mismatch")
    require(errors, counts.get("product_lift_survivor_count") == common.EXPECTED_5Q_PRODUCT_LIFT_COUNT, "registry product-lift count mismatch")


def validate_packet(errors: list[str], packet: dict[str, Any], registry: dict[str, Any]) -> None:
    rebuilt = common.build_packet(write=False)
    require(errors, without_runtime_fields(packet) == without_runtime_fields(rebuilt), "packet drift against source rebuild")
    require(errors, packet.get("schema_version") == common.SCHEMA, "packet schema mismatch")
    require(errors, packet.get("classification") == common.CLASSIFICATION, "classification mismatch")
    require(errors, packet.get("promotion_allowed") is False, "promotion_allowed must be false")
    require(errors, packet.get("formal_admission_allowed") is False, "formal_admission_allowed must be false")
    require(errors, packet.get("cut_state_available") is True, "cut_state_available must be true")
    require(errors, packet.get("lean_storage_policy", {}).get("full_all_survivor_cut_matrices_stored") is False, "full all-survivor matrices must not be stored")
    evidence = packet.get("cut_state_available_evidence", {})
    require(errors, evidence.get("hash_pair_count") == common.EXPECTED_5Q_SURVIVOR_COUNT * 15, "hash pair count mismatch")
    require(errors, evidence.get("sample_candidate_count") == len(common.SAMPLE_LABELS), "sample candidate count mismatch")
    require(errors, evidence.get("sample_cut_pair_count") == len(common.SAMPLE_LABELS) * 15, "sample cut pair count mismatch")
    rows = packet.get("cut_tables", {}).get("survivor_cut_hash_rows", [])
    require(errors, len(rows) == common.EXPECTED_5Q_SURVIVOR_COUNT, "survivor hash row count mismatch")
    for row in rows[:5] + rows[-5:]:
        require(errors, row.get("cut_state_available") is True, f"cut state flag missing for {row.get('candidate_label')}")
        require(errors, row.get("full_reduced_matrices_stored") is False, f"full matrices leaked into {row.get('candidate_label')}")
        require(errors, set(row.get("cuts", {})) == set(common.CUTS), f"missing cuts for {row.get('candidate_label')}")
        for cut in row.get("cuts", {}).values():
            require(errors, "rho_left_hash" in cut and "rho_right_hash" in cut, "missing reduced-state hashes")
            require(errors, "rho_left" not in cut and "rho_right" not in cut, "full reduced matrix stored in hash row")
    sample = packet.get("cut_tables", {}).get("sample_cut_matrix_pairs", [])
    require(errors, [row.get("candidate_label") for row in sample] == common.SAMPLE_LABELS, "sample labels mismatch")
    require(errors, packet.get("controls", {}).get("sample_recompute", {}).get("sample_recompute_pass") is True, "sample recompute failed")
    require(errors, packet.get("controls", {}).get("mutation_sensitivity", {}).get("mutation_detected") is True, "mutation sensitivity failed")
    helper = gcm_substrate_check({"sim_id": common.SIM_ID, "classification": common.CLASSIFICATION, "gcm_lineage": packet["gcm_lineage"]}, common.FOUR_Q_FREEZE_REGISTRY)
    require(errors, helper.get("ok") is True, "live 4Q substrate helper check failed")
    negative = gcm_substrate_check(load(common.LINEAGE_FREE_NEGATIVE_PATH), common.FOUR_Q_FREEZE_REGISTRY)
    require(errors, negative.get("ok") is False and bool(negative.get("error_codes")), "live lineage-free negative did not fail")
    require(errors, packet.get("TOOL_MANIFEST") == common.TOOL_MANIFEST, "TOOL_MANIFEST mismatch")
    require(errors, packet.get("TOOL_INTEGRATION_DEPTH") == common.TOOL_INTEGRATION_DEPTH, "TOOL_INTEGRATION_DEPTH mismatch")
    guard = common.file_size_guard()
    require(errors, guard.get("all_files_under_50mb") is True, "live file-size guard failed")
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
    for err in common.validate_payload(packet, require_file_size=True):
        if err == "audit_verdict.md exists but its header does not declare an independent/fresh audit":
            continue
        errors.append(err)
    return errors


def main() -> int:
    errors = validate_payload()
    result = {"ok": not errors, "result_json": common.rel(RESULT), "registry_json": common.rel(REGISTRY), "errors": errors}
    common.write_json(VALIDATOR_RESULT, result)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
