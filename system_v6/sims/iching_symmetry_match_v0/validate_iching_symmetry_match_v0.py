#!/usr/bin/env python3
"""Packet-local validator for iching_symmetry_match_v0."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


SIM_ID = "iching_symmetry_match_v0"
ROOT = Path(__file__).resolve().parents[3]
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_DIR = SIM_DIR / "results"
RESULT = RESULT_DIR / f"{SIM_ID}_results.json"
VALIDATOR_RESULT = RESULT_DIR / f"{SIM_ID}_validator_results.json"

sys.path.insert(0, str(SIM_DIR))
import iching_symmetry_match_v0 as packet  # noqa: E402

sys.path.insert(0, str(ROOT / "scripts"))
from builder_audit_boundary import builder_audit_boundary_errors  # noqa: E402


REQUIRED_FILES = [
    "build_card.md",
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
        "No git add/commit",
        "No King Wen order claim exists",
        "boundary helper",
        "scratch_diagnostic",
    ):
        require(errors, needle in card, f"build_card.md missing: {needle}")


def validate_payload(errors: list[str], obj: dict[str, Any]) -> None:
    require(errors, obj.get("schema_version") == packet.SCHEMA_VERSION, "schema_version mismatch")
    require(errors, obj.get("sim_id") == SIM_ID, "sim_id mismatch")
    require(errors, obj.get("classification") == "scratch_diagnostic", "classification must be scratch_diagnostic")
    require(errors, obj.get("promotion_allowed") is False, "promotion_allowed must be false")
    require(errors, obj.get("formal_admission_allowed") is False, "formal_admission_allowed must be false")
    require(errors, obj.get("claim_ceiling") == packet.CLAIM_CEILING, "claim ceiling mismatch")
    require(errors, obj.get("all_pass") is True, "all_pass must be true")

    objects = obj.get("objects", {})
    require(errors, objects.get("hexagram_state_count") == 64, "hexagram state count must be 64")
    require(errors, objects.get("engine_axis_state_count") == 64, "engine state count must be 64")
    require(errors, objects.get("axis0_excluded_from_lines") is True, "Axis0 must be excluded")
    require(errors, obj.get("candidate_map", {}).get("line_to_axis") == {str(k): f"Axis{v}" for k, v in packet.LINE_TO_AXIS.items()}, "line-axis map mismatch")

    checks = obj.get("checks", {})
    for key in (
        "line_flip_homomorphism",
        "complement_homomorphism",
        "gray_vs_binary_order_distinguished",
        "king_wen_vs_gray_distinguished",
        "random_labeling_control",
        "axis0_as_line_control",
    ):
        require(errors, checks.get(key) is True, f"required check failed: {key}")

    group = obj.get("group_check", {})
    require(errors, group.get("address_level_isomorphism") is True, "address-level group iso failed")
    require(errors, group.get("hex_group_size") == group.get("engine_group_size"), "group sizes differ")
    require(
        errors,
        group.get("hex_group_size") == 256 and group.get("engine_group_size") == 256,
        "address group size must remain 256; complement is redundant inside the six flip subgroup",
    )
    require(errors, group.get("conjugated_hex_group_equals_engine_group") is True, "conjugated groups differ")

    hom = obj.get("homomorphism_rows", {})
    for line, axis in packet.LINE_TO_AXIS.items():
        row = hom.get(f"flip_line_{line}", {})
        require(errors, row.get("pass") is True, f"flip line {line} homomorphism failed")
        require(errors, row.get("engine_generator") == f"flip_Axis{axis}", f"flip line {line} maps to wrong axis")
    for key in ("complement", "vertical_rotation", "trigram_swap"):
        require(errors, hom.get(key, {}).get("pass") is True, f"{key} homomorphism failed")

    surfaces = obj.get("engine_surface_results", {})
    eng64 = surfaces.get("eng_64_runtime", {})
    require(errors, eng64.get("address_level_match") == "pass", "eng_64 address match must pass")
    require(errors, eng64.get("behavior_level_match") == "quotient_partial", "eng_64 behavior match must stay quotient_partial")
    require(errors, eng64.get("n_distinct_under_current_fingerprint") == 16, "eng_64 n_distinct must be 16")
    behavior_rows = eng64.get("generator_behavior_rows", {})
    require(errors, behavior_rows.get("flip_line_5", {}).get("status") == "quotient_symmetry", "line5/Axis1 quotient symmetry missing")
    require(errors, behavior_rows.get("flip_line_6", {}).get("status") == "quotient_symmetry", "line6/Axis2 quotient symmetry missing")
    require(errors, behavior_rows.get("flip_line_1", {}).get("status") == "homomorphism_only", "line1/Axis6 should not preserve current quotient")

    matrix64 = surfaces.get("matrix64_chart", {})
    require(errors, matrix64.get("address_level_match") == "pass", "Matrix64 address match must pass")
    require(
        errors,
        matrix64.get("behavior_level_match") == "not_run_until_matrix64_behavior_packet_exists",
        "Matrix64 behavior must remain not-run",
    )
    require(errors, matrix64.get("matrix64_completion_claim") is False, "Matrix64 completion must not be claimed")

    controls = obj.get("controls", {})
    random_rows = controls.get("random_64_relabeling", {}).get("rows", [])
    require(errors, len(random_rows) >= 3, "random relabeling controls missing")
    require(errors, all(row.get("perfect_match") is False for row in random_rows), "a random relabeling matched perfectly")
    require(
        errors,
        all(row.get("passed_pairs", row.get("total_pairs", 1)) / row.get("total_pairs", 1) <= 0.10 for row in random_rows),
        "a random relabeling exceeded the bounded exact-agreement threshold",
    )
    orders = controls.get("order_controls", {})
    require(errors, orders.get("gray_code_single_line_cycle", {}).get("all_steps_hamming_1") is True, "Gray single-line cycle failed")
    require(errors, orders.get("ordinary_binary_count", {}).get("all_steps_hamming_1") is False, "binary count should fail single-line cycle")
    require(errors, orders.get("king_wen_sequence", {}).get("all_steps_hamming_1") is False, "King Wen should fail Hamming-1 path")
    require(
        errors,
        orders.get("king_wen_sequence", {}).get("engine_order_claim") == "not_claimed_comparator_only",
        "King Wen engine order claim leaked",
    )
    require(errors, controls.get("axis0_as_seventh_line", {}).get("verdict") == "fail_by_scope_dimension", "Axis0 control did not fail by dimension")

    boundary = obj.get("claim_boundary", {})
    for key in (
        "structure_only",
        "no_divination_or_meaning_claims",
        "not_qit_admission",
        "not_matrix64_completion",
        "not_axis0_closure",
        "not_physics_admission",
        "symbolic_witnesses_weaker_than_math_anchors",
    ):
        require(errors, boundary.get(key) is True, f"boundary missing/false: {key}")
    require(errors, boundary.get("king_wen_engine_order_claim") is False, "King Wen claim boundary failed")

    require(errors, obj.get("TOOL_MANIFEST") == packet.TOOL_MANIFEST, "TOOL_MANIFEST mismatch")
    require(errors, obj.get("TOOL_INTEGRATION_DEPTH") == packet.TOOL_INTEGRATION_DEPTH, "TOOL_INTEGRATION_DEPTH mismatch")
    require(errors, obj.get("builder_gates", {}).get("boundary_helper_fully_used") is True, "boundary helper not fully used")
    errors.extend(builder_audit_boundary_errors(obj, SIM_DIR / "audit_verdict.md"))


def main() -> int:
    errors: list[str] = []
    validate_files(errors)
    if RESULT.exists():
        obj = load(RESULT)
        validate_payload(errors, obj)
    else:
        errors.append(f"missing result: {RESULT.relative_to(ROOT).as_posix()}")
    output = {
        "ok": not errors,
        "errors": errors,
        "checked": {
            "result": RESULT.relative_to(ROOT).as_posix(),
            "packet": SIM_DIR.relative_to(ROOT).as_posix(),
        },
    }
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    VALIDATOR_RESULT.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(output, indent=2, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
