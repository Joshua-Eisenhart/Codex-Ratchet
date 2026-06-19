#!/usr/bin/env python3
"""Packet-local validator for eng64_stage_fingerprint_ids_v0."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


SIM_ID = "eng64_stage_fingerprint_ids_v0"
ROOT = Path(__file__).resolve().parents[3]
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_DIR = SIM_DIR / "results"
RESULT = RESULT_DIR / f"{SIM_ID}_results.json"
VALIDATOR_RESULT = RESULT_DIR / f"{SIM_ID}_validator_results.json"

sys.path.insert(0, str(SIM_DIR))
import eng64_stage_fingerprint_ids_v0 as packet  # noqa: E402

sys.path.insert(0, str(ROOT / "scripts"))
from builder_audit_boundary import builder_audit_boundary_errors  # noqa: E402


REQUIRED_FILES = [
    "build_card.md",
    "builder_self_assessment.md",
    f"{SIM_ID}.py",
    f"validate_{SIM_ID}.py",
]


def require(errors: list[str], condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_files(errors: list[str]) -> None:
    for rel_path in REQUIRED_FILES:
        require(errors, (SIM_DIR / rel_path).is_file(), f"missing packet file: {rel_path}")
    card = (SIM_DIR / "build_card.md").read_text(encoding="utf-8")
    for needle in (
        SIM_ID,
        "STRICTLY ADDITIVE",
        "No git add/commit",
        "2b32714a0",
        "scratch_diagnostic",
        "Matrix64 behavior packet",
    ):
        require(errors, needle in card, f"build_card.md missing: {needle}")


def validate_payload(errors: list[str], obj: dict[str, Any]) -> None:
    require(errors, obj.get("schema_version") == packet.SCHEMA_VERSION, "schema_version mismatch")
    require(errors, obj.get("sim_id") == SIM_ID, "sim_id mismatch")
    require(errors, obj.get("classification") == "scratch_diagnostic", "classification must be scratch_diagnostic")
    require(errors, obj.get("promotion_allowed") is False, "promotion_allowed must be false")
    require(errors, obj.get("formal_admission_allowed") is False, "formal_admission_allowed must be false")
    require(errors, obj.get("claim_ceiling") == packet.CLAIM_CEILING, "claim_ceiling mismatch")
    require(errors, obj.get("all_pass") is True, "all_pass must be true")

    summary = obj.get("summary", {})
    require(errors, summary.get("stage_count") == 64, "stage_count must be 64")
    require(errors, summary.get("n_distinct_fresh_fingerprints") == 16, "fresh n_distinct must be 16")
    require(errors, summary.get("committed_eng64_n_distinct") == 16, "committed n_distinct must be 16")
    require(errors, summary.get("recovered_iching_reference_n_distinct_16") is True, "iching n_distinct recovery failed")

    definition = obj.get("fingerprint_definition", {})
    require(errors, definition.get("fp_tolerance") == packet.FP_TOL, "FP_TOL mismatch")
    require(errors, "source_stage_label" in definition.get("excluded_fields", []), "label exclusion missing")
    require(errors, "rounded_8_float_vector" in definition.get("label_free_fields", []), "label-free fingerprint field missing")

    rows = obj.get("stage_fingerprint_components", [])
    require(errors, len(rows) == 64, "must emit one row per stage")
    require(errors, sorted(row.get("stage") for row in rows) == list(range(64)), "stage rows must cover 0..63")
    require(errors, all(len(row.get("fingerprint", [])) == 8 for row in rows), "each fingerprint must have 8 floats")
    require(errors, all(row.get("fingerprint_id") == row.get("component_id") for row in rows), "fingerprint/component ID mismatch")
    require(errors, len({row.get("component_id") for row in rows}) == 16, "component IDs must have 16 distinct values")

    components = obj.get("components", [])
    require(errors, len(components) == 16, "component table must have 16 rows")
    flattened = sorted(stage for component in components for stage in component.get("stages", []))
    require(errors, flattened == list(range(64)), "component table must partition stages 0..63")

    controls = obj.get("controls", {})
    require(
        errors,
        controls.get("label_permutation_invariance", {}).get("fingerprint_ids_unchanged") is True,
        "label permutation invariance failed",
    )
    require(
        errors,
        controls.get("label_permutation_invariance", {}).get("label_field_used_in_fingerprint") is False,
        "label field leaked into fingerprint",
    )
    require(
        errors,
        controls.get("same_component_independent_recompute", {}).get("all_equal") is True,
        "same-component independent recompute failed",
    )
    require(
        errors,
        controls.get("collapse_graph_parity", {}).get("fresh_fingerprint_components_match_committed_collapse_graph") is True,
        "fresh components do not match committed collapse graph",
    )

    boundary = obj.get("claim_boundary", {})
    for key in (
        "scratch_diagnostic",
        "downstream_plumbing_only",
        "does_not_modify_eng_64_estate",
        "does_not_claim_64_behavior_iso",
        "does_not_claim_matrix64_behavior",
        "does_not_promote_eng_64",
        "no_qit_or_physics_admission",
    ):
        require(errors, boundary.get(key) is True, f"boundary missing/false: {key}")

    require(errors, obj.get("TOOL_MANIFEST") == packet.TOOL_MANIFEST, "TOOL_MANIFEST mismatch")
    require(errors, obj.get("TOOL_INTEGRATION_DEPTH") == packet.TOOL_INTEGRATION_DEPTH, "TOOL_INTEGRATION_DEPTH mismatch")
    require(errors, obj.get("builder_gates", {}).get("boundary_helper_fully_used") is True, "boundary helper not fully used")
    errors.extend(builder_audit_boundary_errors(obj, SIM_DIR / "audit_verdict.md"))


def main() -> int:
    errors: list[str] = []
    validate_files(errors)
    if RESULT.exists():
        validate_payload(errors, load(RESULT))
    else:
        errors.append(f"missing result: {RESULT.relative_to(ROOT).as_posix()}")
    output = {
        "ok": not errors,
        "errors": errors,
        "checked": {
            "result": RESULT.relative_to(ROOT).as_posix(),
            "required_files": REQUIRED_FILES,
        },
    }
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    VALIDATOR_RESULT.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(output, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
