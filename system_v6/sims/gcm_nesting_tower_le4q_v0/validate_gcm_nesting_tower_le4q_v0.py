#!/usr/bin/env python3
"""Packet-local validator for gcm_nesting_tower_le4q_v0."""

from __future__ import annotations

import json
from typing import Any

import gcm_nesting_tower_le4q_v0_common as common


REQUIRED_FILES = [
    common.SIM_DIR / "build_card.md",
    common.SIM_DIR / "builder_self_assessment.md",
    common.SIM_DIR / f"{common.SIM_ID}_common.py",
    common.SIM_DIR / f"validate_{common.SIM_ID}.py",
    common.RESULT_PATH,
]


def require(errors: list[str], condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


def validate_packet(packet: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for path in REQUIRED_FILES:
        require(errors, path.exists(), f"missing required file: {common.rel(path)}")
    require(errors, packet.get("classification") == common.CLASSIFICATION, "classification mismatch")
    require(errors, packet.get("claim_ceiling") == common.CLAIM_CEILING, "claim ceiling mismatch")
    require(errors, packet.get("promotion_allowed") is False, "promotion_allowed must be false")
    require(errors, packet.get("formal_admission_allowed") is False, "formal_admission_allowed must be false")
    require(errors, packet.get("axis_declaration") == common.AXIS_DECLARATION, "axis declaration mismatch")
    require(errors, packet["relation_boundary"]["strict_separation"] is True, "exact/probe separation flag missing")

    counts = packet["counts"]
    require(errors, counts["four_q_survivor_count"] == common.EXPECTED_4Q_SURVIVOR_COUNT, "4Q survivor count mismatch")
    require(errors, counts["four_q_cut_count"] == common.EXPECTED_4Q_CUT_COUNT, "4Q cut count mismatch")
    require(
        errors,
        counts["stored_reduced_matrix_pair_count"] == common.EXPECTED_4Q_STORED_MATRIX_PAIR_COUNT,
        "stored matrix pair count mismatch",
    )
    require(
        errors,
        counts["exact_all_cut_compatible_4q_count"] + counts["exact_all_cut_orphan_4q_count"]
        == common.EXPECTED_4Q_SURVIVOR_COUNT,
        "exact partition mismatch",
    )
    require(
        errors,
        counts["probe_all_cut_compatible_4q_count"] + counts["probe_all_cut_orphan_4q_count"]
        == common.EXPECTED_4Q_SURVIVOR_COUNT,
        "probe partition mismatch",
    )
    require(
        errors,
        counts["probe_all_cut_compatible_family_count"] >= counts["exact_all_cut_compatible_family_count"],
        "probe multiplicity below exact multiplicity",
    )

    root = packet["root_axiom_verdict_at_4q"]
    require(errors, root["le4_exact_all_cut_count"] == counts["exact_all_cut_compatible_4q_count"], "root exact count drift")
    require(errors, root["le4_probe_all_cut_count"] == counts["probe_all_cut_compatible_4q_count"], "root probe count drift")
    require(
        errors,
        root["root_axiom_verdict_at_4q"] in {"HOLDS", "STRENGTHENS", "BREAKS"},
        "root verdict enum mismatch",
    )

    controls = packet["controls"]
    require(
        errors,
        all(controls["positive_partition_checks"].values()),
        f"positive partition checks failed: {controls['positive_partition_checks']}",
    )
    require(errors, controls["negative_scrambled_source_cut"]["red"] is True, "scrambled source-cut negative not red")
    require(errors, all(controls["boundary_tests"].values()), f"boundary tests failed: {controls['boundary_tests']}")

    substrates = packet["substrate_checks"]
    require(errors, substrates["all_positive_ok"] is True, "substrate positive failed")
    require(errors, substrates["negatives_red"] is True, "substrate negative did not turn red")
    require(errors, packet["crossover_proofs"]["z3"]["verdict"] == "unsat", "z3 count proof did not return unsat")
    require(errors, packet["crossover_proofs"]["cvc5"]["verdict"] == "unsat", "cvc5 count proof did not return unsat")

    depth = packet["TOOL_INTEGRATION_DEPTH"]
    require(
        errors,
        any(tool != "numpy" and value == "load_bearing" for tool, value in depth.items()),
        "missing load-bearing non-numeric tool",
    )
    for tool, entry in packet["TOOL_MANIFEST"].items():
        require(errors, bool(entry.get("reason")), f"empty tool manifest reason: {tool}")
    return errors


def main() -> int:
    packet = common.load_json(common.RESULT_PATH)
    errors = validate_packet(packet)
    result = {"ok": not errors, "errors": errors, "result_path": common.rel(common.RESULT_PATH)}
    common.write_json(common.VALIDATOR_RESULT_PATH, result)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
