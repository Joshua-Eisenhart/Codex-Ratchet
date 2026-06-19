#!/usr/bin/env python3
"""Packet-local validator for gcm_ring_checkerboard_runner_v1."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import gcm_ring_checkerboard_runner_v1_common as common


sys.path.insert(0, str(common.ROOT / "scripts"))
from builder_audit_boundary import builder_audit_boundary_errors  # noqa: E402
from gcm_substrate_check import gcm_substrate_check  # noqa: E402


REQUIRED_PACKET_FILES = [
    "build_card.md",
    "builder_self_assessment.md",
    f"{common.SIM_ID}.py",
    f"{common.SIM_ID}_common.py",
    f"{common.SIM_ID}_envelope.py",
    f"validate_{common.SIM_ID}.py",
    f"tests/test_{common.SIM_ID}.py",
    f"results/{common.SIM_ID}_results.json",
    f"results/{common.SIM_ID}_envelope_results.json",
]


def require(errors: list[str], condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_packet_files(errors: list[str]) -> None:
    for rel_path in REQUIRED_PACKET_FILES:
        require(errors, (common.SIM_DIR / rel_path).is_file(), f"missing required packet file: {rel_path}")
    text = (common.SIM_DIR / "build_card.md").read_text(encoding="utf-8")
    for phrase in (
        common.SIM_ID,
        "G.2a",
        "scratch_diagnostic",
        "carrier-and-pins-relative",
        "layers 1-2 + 12 support",
        "integrated-onto-the-carve",
        "1Q",
        "gcm_object_id",
        "gcm_substrate_check",
        "lineage-free negative",
        "QCA/GNVW index row = named not run",
        "NO git add/commit",
        "strict ring-site light-cone",
        "dead-rule honest refusals",
    ):
        require(errors, phrase in text, f"build_card.md missing required phrase: {phrase}")


def validate_payload(payload: dict[str, Any], envelope: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    validate_packet_files(errors)
    rebuilt = common.build_packet()
    rebuilt_envelope = common.build_envelope()
    volatile = {"generated_at", "result_sha256", "substrate_enforcement"}
    for key, value in rebuilt.items():
        if key not in volatile:
            require(errors, payload.get(key) == value, f"payload drifted: {key}")
    envelope_volatile = {"result_sha256"}
    for key, value in rebuilt_envelope.items():
        if key not in envelope_volatile:
            require(errors, envelope.get(key) == value, f"envelope drifted: {key}")
    require(errors, payload.get("gcm_object_id") == common.EXPECTED_OBJECT_ID, "wrong gcm_object_id")
    require(
        errors,
        payload.get("registry_body_sha256") == common.EXPECTED_REGISTRY_BODY_SHA256,
        "wrong registry_body_sha256",
    )
    positive = gcm_substrate_check(payload, common.REGISTRY_PATH)
    negative = gcm_substrate_check(common.lineage_free_variant(payload), common.REGISTRY_PATH)
    require(errors, positive.get("ok") is True, f"positive gcm_substrate_check failed: {positive.get('errors')}")
    require(errors, negative.get("ok") is False, "lineage-free negative unexpectedly passed")
    require(
        errors,
        any("missing lineage consumption" in err or "gcm_object_id mismatch" in err for err in negative.get("errors", [])),
        "lineage-free negative did not fail for lineage/object reason",
    )
    support = payload.get("support_map", {})
    cells = support.get("cells", [])
    require(errors, len(cells) == 16, "support cell count mismatch")
    require(errors, len({cell["survivor_id"] for cell in cells}) == 16, "survivor IDs not unique")
    require(errors, len(support.get("carved_adjacency_edges", [])) == 24, "carved adjacency edge count mismatch")
    require(
        errors,
        support.get("presentation_equivalence_summary", {}).get("status") == "completed_for_frozen_object",
        "presentation equivalence summary not completed",
    )
    require(
        errors,
        len(support.get("presentation_equivalence_checks", [])) == 3
        and all(row.get("status") == "checked_on_frozen_object" for row in support.get("presentation_equivalence_checks", [])),
        "missing completed three-presentation equivalence checks",
    )
    dynamics = payload.get("dynamics", {})
    require(errors, dynamics.get("alternating_AB", {}).get("dynamic_admissibility", {}).get("preserves_M_C") is True, "alternating M(C) preservation failed")
    require(errors, dynamics.get("paired_nontrivial_AABB", {}).get("dynamic_admissibility", {}).get("preserves_M_C") is True, "paired M(C) preservation failed")
    require(errors, dynamics.get("paired_nontrivial_AABB", {}).get("moved_count", 0) > 0, "paired schedule is vacuous identity")
    require(errors, dynamics.get("paired_nontrivial_AABB", {}).get("periods", {}).get("spectrum") != [1], "paired schedule period remained identity")
    require(errors, dynamics.get("two_phase_two_loop_row", {}).get("periodicity_changed") is True, "periodicity row did not change")
    require(errors, dynamics.get("two_phase_two_loop_row", {}).get("v0_identity_tooth_applied") is True, "v0 identity tooth missing")
    require(
        errors,
        payload.get("ring_local_update", {}).get("strict_one_site_per_half_step_light_cone_pass") is True,
        "strict ring-site light-cone failed",
    )
    preservation = payload.get("M_C_preservation_rerun_by_rule", {})
    require(
        errors,
        set(preservation) == {"A_half_step", "B_half_step", "alternating_AB", "paired_nontrivial_AABB", "ring_local_AB"},
        "M(C) preservation rule set mismatch",
    )
    require(errors, all(row.get("preserves_M_C") is True for row in preservation.values()), "some rule failed M(C) preservation")
    require(
        errors,
        all(row.get("carve_predicate_text_sha256") == common.EXPECTED_CARVE_PREDICATE_SHA256 for row in preservation.values()),
        "carve predicate hash missing from M(C) preservation rows",
    )
    require(
        errors,
        all(row.get("moved_count", 0) > 0 for row in payload.get("orbit_nontriviality_by_rule", {}).values()),
        "some orbit nontriviality row is vacuous",
    )
    require(
        errors,
        payload.get("controls", {}).get("all_to_all", {}).get("carved_edge_subset") is False,
        "locality removal control did not break locality",
    )
    require(
        errors,
        payload.get("controls", {}).get("phase_merge", {}).get("periodicity_changed_vs_paired") is True,
        "phase merge control did not change periodicity",
    )
    require(errors, payload.get("dead_rule_honest_refusals", {}).get("v0_AABB_identity", {}).get("status") == "refused_dead_rule", "v0 dead-rule refusal missing")
    require(errors, payload.get("fences", {}).get("qca_gnvw_index_row") == "named_not_run_2Q_plus_ladder", "QCA/GNVW fence mismatch")
    require(errors, payload.get("TOOL_MANIFEST") == common.TOOL_MANIFEST, "TOOL_MANIFEST mismatch")
    require(errors, payload.get("TOOL_INTEGRATION_DEPTH") == common.TOOL_INTEGRATION_DEPTH, "TOOL_INTEGRATION_DEPTH mismatch")
    require(errors, payload.get("all_pass") is True, "payload all_pass false")
    require(errors, envelope.get("all_pass") is True, "envelope all_pass false")
    errors.extend(builder_audit_boundary_errors(envelope, common.SIM_DIR / "audit_verdict.md"))
    return errors


def main() -> int:
    payload = load(common.RESULT_PATH)
    envelope = load(common.ENVELOPE_PATH)
    errors = validate_payload(payload, envelope)
    result = {"ok": not errors, "result_json": common.rel(common.ENVELOPE_PATH), "errors": errors}
    common.write_json(common.VALIDATOR_RESULT_PATH, result)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
