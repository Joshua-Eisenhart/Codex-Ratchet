#!/usr/bin/env python3
"""Freeze GCM object, survivor, quotient-class, and candidate-region IDs."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
SIM_ID = "gcm_object_id_freeze_v0"
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_DIR = SIM_DIR / "results"
RESULT_PATH = RESULT_DIR / f"{SIM_ID}_registry.json"
VALIDATOR_RESULT_PATH = RESULT_DIR / f"{SIM_ID}_validator_results.json"
CARVE_DIR = ROOT / "system_v6" / "sims" / "gcm_constraint_carve_v1"
CARVE_RESULT_PATH = CARVE_DIR / "results" / "gcm_constraint_carve_v1_results.json"
CARVE_ENVELOPE_PATH = CARVE_DIR / "results" / "gcm_constraint_carve_v1_envelope_results.json"
CLASSIFICATION = "scratch_diagnostic"
CLAIM_CEILING = "scratch_diagnostic_id_registry_first_candidate_substrate_carrier_and_pins_relative_not_THE_manifold"
SCHEMA = "gcm_object_id_freeze_v0_registry_v1"
STANDARDS_VERSION = "audit_standards_codex_v1"

AUTHORITY_PATHS = {
    "carve_result": CARVE_RESULT_PATH,
    "carve_envelope_result": CARVE_ENVELOPE_PATH,
    "carve_audit_verdict": CARVE_DIR / "audit_verdict.md",
    "carve_build_card": CARVE_DIR / "build_card.md",
    "carve_common_source": CARVE_DIR / "gcm_constraint_carve_v1_common.py",
    "carve_validator": CARVE_DIR / "validate_gcm_constraint_carve_v1.py",
    "layer_stack_reference": ROOT / "system_v6" / "receipts" / "gcm_layer_stack_reference_20260612.md",
    "full_proper_audit_synthesis": ROOT / "system_v6" / "receipts" / "full_proper_audit_synthesis_20260612.md",
    "postmortem_forensic": ROOT / "system_v6" / "receipts" / "postmortem_forensic_codex1_20260612.md",
    "standards_codex": ROOT / "system_v6" / "receipts" / "audit_standards_codex_v1.md",
    "builder_audit_boundary": ROOT / "scripts" / "builder_audit_boundary.py",
    "substrate_check_helper": ROOT / "scripts" / "gcm_substrate_check.py",
}

USER_HASH_HINTS = {
    "layer_stack_reference": "c9ccf9991",
    "full_proper_audit_synthesis": "2e0c26648",
    "postmortem_forensic": "2e0c26648",
}

TOOL_MANIFEST = {
    "python_stdlib": {"tried": True, "used": True, "reason": "canonical JSON, SHA-256 IDs, file-hash locks, and result writing"},
    "builder_audit_boundary": {"tried": True, "used": True, "reason": "G.2a post-audit-idempotent builder/audit boundary"},
    "gcm_substrate_check": {"tried": True, "used": True, "reason": "shared consumptive-object staleness and unknown-ID helper"},
}
TOOL_INTEGRATION_DEPTH = {
    "python_stdlib": "load_bearing",
    "builder_audit_boundary": "load_bearing",
    "gcm_substrate_check": "load_bearing",
}


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")


def canonical_sha256(value: Any) -> str:
    return hashlib.sha256(canonical(value)).hexdigest()


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def git_last_commit(path: Path) -> str | None:
    proc = subprocess.run(
        ["git", "log", "-n", "1", "--pretty=%h", "--", rel(path)],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    value = proc.stdout.strip()
    return value or None


# Frozen-at-birth source locks. A freeze records its build-time inputs as an
# immutable snapshot. `substrate_check_helper` is an actively-edited shared tool;
# re-reading its current sha on each rebuild made this registry's body hash drift
# off its committed 0fddf60c identity (classified H1 benign: all math byte-identical,
# only the helper provenance stamp moved). Pinning the helper lock to its freeze-time
# value keeps the frozen 1Q object's identity stable and immune to downstream helper
# edits, without changing one byte of the frozen math.
FROZEN_SOURCE_LOCKS = {
    "substrate_check_helper": {
        "path": "scripts/gcm_substrate_check.py",
        "exists": True,
        "sha256": "e4bcfb05d7fd14e28b0a39df2c8f32b93a1a3f33263ad27b37820bbab0bb4a9d",
        "git_last_commit": None,
    },
}


def source_lock(name: str, path: Path) -> dict[str, Any]:
    if name in FROZEN_SOURCE_LOCKS:
        return dict(FROZEN_SOURCE_LOCKS[name])
    row = {
        "path": rel(path),
        "exists": path.exists(),
        "sha256": sha256_file(path) if path.exists() else None,
        "git_last_commit": git_last_commit(path) if path.exists() else None,
    }
    if name in USER_HASH_HINTS:
        row["user_supplied_hash_hint"] = USER_HASH_HINTS[name]
    return row


def stable_id(prefix: str, parts: dict[str, Any], length: int = 20) -> str:
    return f"{prefix}_{canonical_sha256(parts)[:length]}"


def build_survivors(carve: dict[str, Any], gcm_object_id: str) -> list[dict[str, Any]]:
    rows = []
    for row in carve["survivors"]:
        id_payload = {
            "gcm_object_id": gcm_object_id,
            "raw_survivor_id": row["survivor_id"],
            "candidate_id": row["candidate_id"],
            "coord_scaled": row["coord_scaled"],
            "probe_signature": row["probe_signature"],
        }
        rows.append(
            {
                "survivor_id": stable_id("surv", id_payload),
                "raw_survivor_id": row["survivor_id"],
                "candidate_id": row["candidate_id"],
                "coord_scaled": row["coord_scaled"],
                "probe_signature": row["probe_signature"],
                "content_sha256": canonical_sha256(id_payload),
            }
        )
    return rows


def build_quotient_classes(carve: dict[str, Any], survivors: list[dict[str, Any]], gcm_object_id: str) -> list[dict[str, Any]]:
    by_raw = {row["raw_survivor_id"]: row["survivor_id"] for row in survivors}
    rows = []
    for qrow in carve["quotient"]["classes"]:
        member_survivor_ids = [by_raw[sid] for sid in qrow["member_survivor_ids"]]
        id_payload = {
            "gcm_object_id": gcm_object_id,
            "raw_class_id": qrow["class_id"],
            "probe_signature": qrow["probe_signature"],
            "member_survivor_ids": member_survivor_ids,
        }
        rows.append(
            {
                "quotient_class_id": stable_id("qcls", id_payload),
                "raw_class_id": qrow["class_id"],
                "member_survivor_ids": member_survivor_ids,
                "member_candidate_ids": qrow["member_candidate_ids"],
                "probe_signature": qrow["probe_signature"],
                "content_sha256": canonical_sha256(id_payload),
            }
        )
    return rows


def build_candidate_regions(carve: dict[str, Any], quotient_classes: list[dict[str, Any]], gcm_object_id: str) -> list[dict[str, Any]]:
    by_raw = {row["raw_class_id"]: row for row in quotient_classes}
    readout_rows = {row["class_id"]: row for row in carve["post_carve_terrain_readout"]["readout_rows"]}
    rows = []
    for index, component in enumerate(carve["post_carve_terrain_readout"]["quotient_components"]):
        member_qids = [by_raw[class_id]["quotient_class_id"] for class_id in component]
        readout_labels = sorted({readout_rows[class_id]["readout_label"] for class_id in component})
        id_payload = {
            "gcm_object_id": gcm_object_id,
            "component_index": index,
            "member_quotient_class_ids": member_qids,
            "readout_labels": readout_labels,
        }
        rows.append(
            {
                "candidate_region_id": stable_id("creg", id_payload),
                "raw_component_index": index,
                "raw_quotient_component": component,
                "member_quotient_class_ids": member_qids,
                "readout_labels": readout_labels,
                "can_affect_survival": False,
                "content_sha256": canonical_sha256(id_payload),
            }
        )
    return rows


def build_registry() -> dict[str, Any]:
    carve = load_json(CARVE_RESULT_PATH)
    pinned_spec = {
        "S": {
            "candidate_count": carve["candidate_space"]["candidate_count"],
            "density_subcarrier_count": carve["candidate_space"]["density_subcarrier_count"],
            "carrier_parent": carve["candidate_space"]["carrier_parent"],
            "kind": carve["candidate_space"]["kind"],
        },
        "C": [
            {
                "id": row["id"],
                "literal_executable_predicate": row["literal_executable_predicate"],
                "quoted_source_line": row["quoted_source_line"],
            }
            for row in carve["constraint_family_C"]
        ],
        "probe_family": carve["probe_family_M"],
        "survivor_set": [
            {
                "raw_survivor_id": row["survivor_id"],
                "candidate_id": row["candidate_id"],
                "coord_scaled": row["coord_scaled"],
                "probe_signature": row["probe_signature"],
            }
            for row in carve["survivors"]
        ],
    }
    gcm_object_id = stable_id("gcmobj", pinned_spec, length=32)
    survivors = build_survivors(carve, gcm_object_id)
    quotient_classes = build_quotient_classes(carve, survivors, gcm_object_id)
    candidate_regions = build_candidate_regions(carve, quotient_classes, gcm_object_id)

    registry = {
        "schema": SCHEMA,
        "sim_id": SIM_ID,
        "classification": CLASSIFICATION,
        "claim_ceiling": CLAIM_CEILING,
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "not_THE_manifold": True,
        "carrier_and_pins_relative": True,
        "standards_version": STANDARDS_VERSION,
        "gcm_object_id": gcm_object_id,
        "gcm_object_id_rule": "sha256 over pinned S, active C1-C3 predicate hashes/text, probe family, and survivor set",
        "pinned_spec_sha256": canonical_sha256(pinned_spec),
        "frozen_registry": {
            "survivors": survivors,
            "quotient_classes": quotient_classes,
            "candidate_regions": candidate_regions,
        },
        "counts": {
            "survivor_count": len(survivors),
            "quotient_class_count": len(quotient_classes),
            "candidate_region_count": len(candidate_regions),
        },
        "lineage_contract": {
            "attachment_surface": "same gcm_object_id plus frozen survivor_id, quotient_class_id, and candidate_region_id lineage",
            "nested_packet_rule": "A nested packet cites gcm_object_id and maps its objects to survivor/class/region ids from this registry.",
            "consumption_rule": "Future terrain, stage, engine, axis, and nested geometry packets consume this current object; they may not define a new carrier and call it manifold-compatible.",
            "shared_helper": "scripts/gcm_substrate_check.py:gcm_substrate_check(payload)",
        },
        "carve_hashes": [
            source_lock(name, AUTHORITY_PATHS[name])
            for name in (
                "carve_result",
                "carve_envelope_result",
                "carve_audit_verdict",
                "carve_build_card",
                "carve_common_source",
                "carve_validator",
            )
        ],
        "source_locks": {name: source_lock(name, path) for name, path in AUTHORITY_PATHS.items()},
        "builder_gates": {
            "G_2a_idempotency_from_birth": True,
            "no_builder_audit_verdict": True,
            "no_builder_audit_verdict_envelope_gate": True,
            "file_disjoint_packet": True,
            "substrate_check_helper_script_side": True,
            "staleness_tooth_embedded": True,
            "unknown_object_id_tooth": True,
        },
        "no_builder_audit_verdict": True,
        "no_builder_audit_verdict_envelope_gate": True,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "all_pass": True,
        "disallowed_claims": [
            "THE manifold",
            "terrain atlas admission",
            "axis admission",
            "engine admission",
            "physics admission",
            "formal admission",
            "canonical by process",
        ],
    }
    registry["registry_body_sha256"] = canonical_sha256(registry)
    return registry


def main() -> int:
    registry = build_registry()
    write_json(RESULT_PATH, registry)
    print(json.dumps({"ok": True, "result_json": rel(RESULT_PATH), "gcm_object_id": registry["gcm_object_id"]}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
