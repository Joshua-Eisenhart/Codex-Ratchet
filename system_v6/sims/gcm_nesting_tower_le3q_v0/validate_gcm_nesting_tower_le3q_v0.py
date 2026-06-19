#!/usr/bin/env python3
"""Validate gcm_nesting_tower_le3q_v0 local packet outputs."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from gcm_nesting_tower_le3q_v0_common import (
    ENVELOPE_PATH,
    EXPECTED_3Q_PRODUCT_LIFT_COUNT,
    EXPECTED_3Q_SURVIVOR_COUNT,
    EXPECTED_3Q_TRIPARTITE_ENTANGLED_COUNT,
    LE2_REGRESSION_EXPECTED_COUNTS,
    RESULT_DIR,
    RESULT_PATH,
    SIM_DIR,
    SIM_ID,
    VALIDATOR_RESULT_PATH,
    load_json,
    rel,
    write_json,
)

SCRIPTS_DIR = Path(__file__).resolve().parents[3] / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from builder_audit_boundary import builder_audit_boundary_errors  # noqa: E402
from validate_three_engine_sim_result import validate as validate_three_engine  # noqa: E402


REQUIRED_FILES = [
    SIM_DIR / "build_card.md",
    SIM_DIR / "builder_self_assessment.md",
    SIM_DIR / f"{SIM_ID}_common.py",
    SIM_DIR / f"{SIM_ID}_boundary.py",
    SIM_DIR / f"{SIM_ID}_julia.jl",
    SIM_DIR / f"{SIM_ID}_jax.py",
    SIM_DIR / f"{SIM_ID}_pytorch.py",
    SIM_DIR / "write_envelope_spec.py",
    SIM_DIR / f"validate_{SIM_ID}.py",
    RESULT_PATH,
    ENVELOPE_PATH,
    RESULT_DIR / f"{SIM_ID}_julia_results.json",
    RESULT_DIR / f"{SIM_ID}_jax_results.json",
    RESULT_DIR / f"{SIM_ID}_pytorch_results.json",
]


def require(condition: bool, errors: list[str], message: str) -> None:
    if not condition:
        errors.append(message)


def validate_packet(packet: dict[str, Any], envelope: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for path in REQUIRED_FILES:
        require(path.exists(), errors, f"missing required file: {rel(path)}")

    require(packet.get("classification") == "scratch_diagnostic", errors, "classification must be scratch_diagnostic")
    require(packet.get("promotion_allowed") is False, errors, "promotion_allowed must be false")
    require(packet.get("formal_admission_allowed") is False, errors, "formal_admission_allowed must be false")
    require(packet.get("claim_ceiling") == "scratch_diagnostic_le3q_tower_carrier_and_pins_relative", errors, "claim ceiling mismatch")
    require(
        packet.get("axis_declaration") == {"axis": "nesting/tower", "limit_object": "inverse-limit", "rung": "<=3Q"},
        errors,
        "axis declaration mismatch",
    )

    counts = packet["counts"]
    require(counts["three_q_survivor_count"] == EXPECTED_3Q_SURVIVOR_COUNT, errors, "3Q survivor count mismatch")
    require(counts["product_lift_3q_count"] == EXPECTED_3Q_PRODUCT_LIFT_COUNT, errors, "product lift count mismatch")
    require(
        counts["tripartite_entangled_anchor_count"] == EXPECTED_3Q_TRIPARTITE_ENTANGLED_COUNT,
        errors,
        "tripartite entangled anchor count mismatch",
    )
    require(
        counts["exact_all_cut_compatible_3q_count"] + counts["exact_all_cut_orphan_3q_count"]
        == EXPECTED_3Q_SURVIVOR_COUNT,
        errors,
        "exact all-cut partition mismatch",
    )
    require(
        counts["probe_all_cut_compatible_3q_count"] + counts["probe_all_cut_orphan_3q_count"]
        == EXPECTED_3Q_SURVIVOR_COUNT,
        errors,
        "probe all-cut partition mismatch",
    )
    require(
        counts["product_lift_probe_family_count"] + counts["tripartite_entangled_probe_family_count"]
        == counts["probe_all_cut_compatible_family_count"],
        errors,
        "probe family product/entangled partition mismatch",
    )

    for row in packet["object_maps"]:
        require(set(row["cut_relations"]) == {"A|BC", "B|AC", "C|AB"}, errors, f"missing cut row for survivor {row['survivor_id']}")
        for cut, cut_row in row["cut_relations"].items():
            require(cut_row["partial_trace_tested"] is True, errors, f"partial trace not marked tested: {row['survivor_id']} {cut}")

    source_checks = packet["source_authority_checks"]
    require(all(source_checks.values()), errors, f"authority commit check failed: {source_checks}")

    substrates = packet["substrate_checks"]
    require(substrates["all_positive_ok"] is True, errors, "hardened helper positive checks failed")
    require(substrates["negatives_red"] is True, errors, "hardened helper negative did not turn red")
    require(substrates["three_q_parent_source_check"]["commit_matches_authority"] is True, errors, "3Q parent commit mismatch")
    require(
        substrates["three_q_parent_source_check"]["state_artifacted_survivors_by_content_id"] is True,
        errors,
        "3Q parent survivor content-id artifact check failed",
    )

    le2 = packet["controls"]["le2_regression"]
    require(le2["all_counts_reproduced"] is True, errors, "le2 regression counts were not reproduced")
    for key, expected in LE2_REGRESSION_EXPECTED_COUNTS.items():
        require(le2["observed_counts"].get(key) == expected, errors, f"le2 regression mismatch: {key}")
    require(packet["controls"]["scrambled_pairing"]["red"] is True, errors, "scrambled-pairing negative did not turn red")
    require(
        packet["controls"]["product_baseline"]["product_lift_count"] == EXPECTED_3Q_PRODUCT_LIFT_COUNT,
        errors,
        "product baseline count mismatch",
    )

    root = packet["root_axiom_question_at_3q"]
    require(isinstance(root["exact_tower_stays_product_trivial"], bool), errors, "root exact answer missing bool")
    require(isinstance(root["probe_quotient_admits_tripartite_entangled_anchor"], bool), errors, "root probe answer missing bool")

    require(envelope["divergence"]["max_divergence"] == 0, errors, "engine divergence is nonzero")
    errors.extend(
        validate_three_engine(
            envelope,
            require_pytorch=True,
            strict_source_backed=True,
            require_tool_intent=True,
        )
    )
    errors.extend(builder_audit_boundary_errors(envelope, SIM_DIR / "audit_verdict.md"))
    return errors


def main() -> int:
    packet = load_json(RESULT_PATH)
    envelope = load_json(ENVELOPE_PATH)
    errors = validate_packet(packet, envelope)
    result = {"ok": not errors, "errors": errors, "result_path": rel(RESULT_PATH), "envelope_path": rel(ENVELOPE_PATH)}
    write_json(VALIDATOR_RESULT_PATH, result)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
