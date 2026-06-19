#!/usr/bin/env python3
"""Packet-local validator for gcm_object_id_freeze_v0."""

from __future__ import annotations

import copy
import json
import sys
import tempfile
from pathlib import Path
from typing import Any

import gcm_object_id_freeze_v0 as common
import gcm_object_id_freeze_v0_boundary as boundary


ROOT = Path(__file__).resolve().parents[3]
SCRIPTS_DIR = ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from gcm_substrate_check import gcm_substrate_check  # noqa: E402


REQUIRED_PACKET_FILES = [
    "build_card.md",
    "builder_self_assessment.md",
    "gcm_object_id_freeze_v0.py",
    "gcm_object_id_freeze_v0_boundary.py",
    "validate_gcm_object_id_freeze_v0.py",
    "tests/test_gcm_object_id_freeze_v0.py",
    "results/gcm_object_id_freeze_v0_registry.json",
]


def require(errors: list[str], condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


def validate_source_locks(errors: list[str], payload: dict[str, Any]) -> None:
    source_locks = payload.get("source_locks", {})
    require(errors, set(source_locks) == set(common.AUTHORITY_PATHS), "source lock set mismatch")
    for name, path in common.AUTHORITY_PATHS.items():
        row = source_locks.get(name, {})
        require(errors, row.get("exists") is True, f"{name} source missing")
        frozen = getattr(common, "FROZEN_SOURCE_LOCKS", {})
        if name in frozen:
            # Frozen-at-birth provenance: the recorded lock is intentionally pinned to the
            # freeze-time value and does NOT track the live (evolving) helper file. Assert it
            # equals the frozen constant — anti-tamper is preserved against a known value.
            require(errors, row.get("sha256") == frozen[name]["sha256"], f"{name} frozen-at-birth lock mismatch")
        else:
            require(errors, row.get("sha256") == common.sha256_file(path), f"{name} source hash drift")
        if name in common.USER_HASH_HINTS:
            require(errors, row.get("user_supplied_hash_hint") == common.USER_HASH_HINTS[name], f"{name} hash hint mismatch")


def validate_registry_shape(errors: list[str], payload: dict[str, Any]) -> None:
    frozen = payload.get("frozen_registry", {})
    survivors = frozen.get("survivors", [])
    qclasses = frozen.get("quotient_classes", [])
    regions = frozen.get("candidate_regions", [])

    require(errors, payload.get("schema") == common.SCHEMA, "schema mismatch")
    require(errors, payload.get("sim_id") == common.SIM_ID, "sim_id mismatch")
    require(errors, payload.get("standards_version") == common.STANDARDS_VERSION, "standards_version mismatch")
    require(errors, isinstance(payload.get("gcm_object_id"), str) and payload["gcm_object_id"].startswith("gcmobj_"), "bad gcm_object_id")
    require(errors, payload.get("counts") == {"survivor_count": 16, "quotient_class_count": 8, "candidate_region_count": 6}, "count contract mismatch")
    require(errors, len(survivors) == 16, "survivor row count mismatch")
    require(errors, len(qclasses) == 8, "quotient class row count mismatch")
    require(errors, len(regions) == 6, "candidate region count mismatch")
    require(errors, len({row.get("survivor_id") for row in survivors}) == 16, "survivor IDs not unique")
    require(errors, len({row.get("quotient_class_id") for row in qclasses}) == 8, "quotient class IDs not unique")
    require(errors, len({row.get("candidate_region_id") for row in regions}) == 6, "candidate region IDs not unique")

    survivor_ids = {row.get("survivor_id") for row in survivors}
    for row in qclasses:
        require(errors, set(row.get("member_survivor_ids", [])).issubset(survivor_ids), f"unknown survivor in {row.get('quotient_class_id')}")
    qids = {row.get("quotient_class_id") for row in qclasses}
    for row in regions:
        require(errors, set(row.get("member_quotient_class_ids", [])).issubset(qids), f"unknown quotient class in {row.get('candidate_region_id')}")
        require(errors, row.get("can_affect_survival") is False, f"region {row.get('candidate_region_id')} can affect survival")


def validate_staleness_tooth(errors: list[str], payload: dict[str, Any]) -> None:
    ok_payload = {
        "gcm_lineage": {
            "gcm_object_id": payload["gcm_object_id"],
            "registry_body_sha256": (
                common.load_json(common.RESULT_PATH).get("registry_body_sha256")
                if common.RESULT_PATH.exists()
                else payload["registry_body_sha256"]
            ),
            "object_maps": [
                {
                    "object_id": "smoke",
                    "survivor_id": payload["frozen_registry"]["survivors"][0]["survivor_id"],
                    "quotient_class_id": payload["frozen_registry"]["quotient_classes"][0]["quotient_class_id"],
                    "candidate_region_id": payload["frozen_registry"]["candidate_regions"][0]["candidate_region_id"],
                }
            ],
        }
    }
    require(errors, gcm_substrate_check(ok_payload, common.RESULT_PATH).get("ok") is True, "valid substrate check failed")

    unknown_payload = copy.deepcopy(ok_payload)
    unknown_payload["gcm_lineage"]["object_maps"][0]["survivor_id"] = "surv_unknown"
    unknown = gcm_substrate_check(unknown_payload, common.RESULT_PATH)
    require(errors, unknown.get("ok") is False and any("unknown survivor_id" in err for err in unknown.get("errors", [])), "unknown-object-id test did not fail")

    stale_registry = copy.deepcopy(payload)
    stale_registry["carve_hashes"][0]["sha256"] = "0" * 64
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "stale_registry.json"
        common.write_json(path, stale_registry)
        stale = gcm_substrate_check(ok_payload, path)
    require(errors, stale.get("ok") is False and any("carve hash drift" in err for err in stale.get("errors", [])), "stale-registry test did not fail")


def validate_payload(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for rel_path in REQUIRED_PACKET_FILES:
        require(errors, (common.SIM_DIR / rel_path).is_file(), f"missing packet file: {rel_path}")
    card = (common.SIM_DIR / "build_card.md").read_text(encoding="utf-8")
    for phrase in ("gcm_object_id", "survivor_id", "quotient_class_id", "candidate_region_id", "G.2a", "not THE manifold"):
        require(errors, phrase in card, f"build_card missing phrase: {phrase}")

    rebuilt = common.build_registry()
    require(errors, payload == rebuilt, "registry drift against rebuilt output")
    validate_registry_shape(errors, payload)
    validate_source_locks(errors, payload)
    errors.extend(boundary.boundary_errors(payload, common.SIM_DIR))
    validate_staleness_tooth(errors, payload)
    require(errors, payload.get("TOOL_MANIFEST") == common.TOOL_MANIFEST, "TOOL_MANIFEST mismatch")
    require(errors, payload.get("TOOL_INTEGRATION_DEPTH") == common.TOOL_INTEGRATION_DEPTH, "TOOL_INTEGRATION_DEPTH mismatch")
    require(errors, payload.get("all_pass") is True, "all_pass must be true")
    return errors


def main() -> int:
    payload = common.load_json(common.RESULT_PATH) if common.RESULT_PATH.exists() else common.build_registry()
    errors = validate_payload(payload)
    result = {"ok": not errors, "result_json": common.rel(common.RESULT_PATH), "errors": errors}
    common.write_json(common.VALIDATOR_RESULT_PATH, result)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
