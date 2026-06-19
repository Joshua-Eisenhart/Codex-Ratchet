#!/usr/bin/env python3
"""Packet-local validator for matrix64_behavior_match_v0."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


SIM_ID = "matrix64_behavior_match_v0"
ROOT = Path(__file__).resolve().parents[3]
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_DIR = SIM_DIR / "results"
RESULT = RESULT_DIR / f"{SIM_ID}_results.json"
VALIDATOR_RESULT = RESULT_DIR / f"{SIM_ID}_validator_results.json"

sys.path.insert(0, str(SIM_DIR))
import matrix64_behavior_match_v0 as packet  # noqa: E402

sys.path.insert(0, str(ROOT / "scripts"))
from builder_audit_boundary import builder_audit_boundary_errors  # noqa: E402


REQUIRED_FILES = [
    "build_card.md",
    "builder_self_assessment.md",
    f"{SIM_ID}.py",
    f"validate_{SIM_ID}.py",
    f"test_{SIM_ID}.py",
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
        "No git add/commit",
        "STRICTLY ADDITIVE",
        "G.2a",
        "builder_audit_boundary.py",
        "scratch_diagnostic",
        "realization-relative",
        "King-Wen",
        "2b32714a0",
        "fab7b2253",
        "23cfa5536",
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

    objects = obj.get("objects", {})
    require(errors, objects.get("stage_count") == 64, "stage_count must be 64")
    require(errors, objects.get("component_count") == 16, "component_count must be 16")
    require(errors, objects.get("component_size_histogram") == {"4": 16}, "component histogram must be 16 components of size 4")

    rows = obj.get("generator_descent_rows", [])
    require(errors, len(rows) == 9, "must emit 9 generator descent rows")
    by_name = {row.get("generator"): row for row in rows}
    expected_names = {
        "flip_line_1",
        "flip_line_2",
        "flip_line_3",
        "flip_line_4",
        "flip_line_5",
        "flip_line_6",
        "complement",
        "vertical_rotation",
        "trigram_swap",
    }
    require(errors, set(by_name) == expected_names, "generator names mismatch")
    for name in [f"flip_line_{line}" for line in range(1, 7)] + ["complement"]:
        require(errors, by_name.get(name, {}).get("descends") is True, f"{name} must descend")
        require(errors, by_name.get(name, {}).get("breaking_component_count") == 0, f"{name} must not break components")
    for name in ("vertical_rotation", "trigram_swap"):
        row = by_name.get(name, {})
        require(errors, row.get("descends") is False, f"{name} must not descend")
        require(errors, row.get("breaking_component_count") == 16, f"{name} must break all 16 components")
        require(errors, len(row.get("breaking_components", [])) == 16, f"{name} must list all breaking components")
    require(errors, by_name.get("flip_line_5", {}).get("pointwise_preserves_components") is True, "flip_line_5 pointwise check failed")
    require(errors, by_name.get("flip_line_6", {}).get("pointwise_preserves_components") is True, "flip_line_6 pointwise check failed")
    for name in ("flip_line_1", "flip_line_2", "flip_line_3", "flip_line_4", "complement"):
        require(errors, by_name.get(name, {}).get("pointwise_preserves_components") is False, f"{name} should move components nontrivially")

    audit_rows = obj.get("audit_check_rows", [])
    require(errors, len(audit_rows) == 9, "audit_check_rows must have 9 rows")
    require(errors, all(row.get("pointwise_check_matches_audit") is True for row in audit_rows), "audit pointwise check mismatch")

    subgroup = obj.get("subgroup", {})
    require(errors, subgroup.get("full_address_group_size") == 256, "full address group size must be 256")
    require(errors, subgroup.get("descending_subgroup_size") == 64, "descending subgroup size must be 64")
    require(errors, subgroup.get("proper_subgroup") is True, "descending subgroup must be proper")
    require(errors, len(subgroup.get("descending_elements", [])) == 64, "must list 64 descending elements")

    summary = obj.get("summary", {})
    require(errors, summary.get("result") == "proper_subgroup_descends", "summary result mismatch")
    require(errors, summary.get("breaking_generators") == ["vertical_rotation", "trigram_swap"], "breaking generator summary mismatch")
    require(errors, summary.get("proper_subgroup_descends") is True, "proper subgroup summary missing")

    controls = obj.get("controls", {})
    require(
        errors,
        controls.get("identity_descends_trivially", {}).get("descends") is True,
        "identity must descend",
    )
    require(
        errors,
        controls.get("identity_descends_trivially", {}).get("breaking_component_count") == 0,
        "identity must not break components",
    )
    require(
        errors,
        controls.get("random_stage_to_component_relabeling", {}).get("breaks_descent_table") is True,
        "random relabeling control must break descent",
    )
    require(
        errors,
        controls.get("deliberately_coarsened_quotient", {}).get("descent_table_changed") is True,
        "coarsened quotient must change descent table",
    )

    boundary = obj.get("claim_boundary", {})
    for key in (
        "scratch_diagnostic",
        "realization_relative_behavioral_symmetry_table_only",
        "pinned_realization_only",
        "does_not_claim_matrix64_general",
        "does_not_claim_64_behavior_iso",
        "does_not_claim_matrix64_completion",
        "king_wen_comparator_only",
        "does_not_promote_eng_64",
        "not_qit_admission",
        "not_physics_admission",
        "not_bridge_or_axis_closure",
    ):
        require(errors, boundary.get(key) is True, f"claim boundary missing/false: {key}")

    require(errors, obj.get("TOOL_MANIFEST") == packet.TOOL_MANIFEST, "TOOL_MANIFEST mismatch")
    require(errors, obj.get("TOOL_INTEGRATION_DEPTH") == packet.TOOL_INTEGRATION_DEPTH, "TOOL_INTEGRATION_DEPTH mismatch")
    gates = obj.get("builder_gates", {})
    require(errors, gates.get("boundary_helper_fully_used") is True, "boundary helper not fully used")
    require(errors, gates.get("g2a_boundary_helper_from_birth") is True, "G.2a from-birth gate missing")
    require(errors, gates.get("no_hard_audit_absence_assertion") is True, "hard audit absence assertion must be absent")
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
