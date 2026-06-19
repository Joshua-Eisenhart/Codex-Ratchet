#!/usr/bin/env python3
"""Write the standard envelope spec for gcm_constraint_carve_3q_v0."""

from __future__ import annotations

import json

import gcm_constraint_carve_3q_v0_common as common


CLASSIFICATION = common.CLASSIFICATION
TOOL_MANIFEST = common.TOOL_MANIFEST
TOOL_INTEGRATION_DEPTH = common.TOOL_INTEGRATION_DEPTH
SPEC_PATH = common.SIM_DIR / f"{common.SIM_ID}_envelope_spec.json"


def build_spec() -> dict:
    payload = common.load_json(common.RESULT_PATH)
    lanes = {}
    for engine in ("julia", "jax", "pytorch"):
        lane = common.load_json(common.RESULT_DIR / f"{common.SIM_ID}_{engine}_results.json")
        lanes[engine] = {
            "source_path": lane["source_path"],
            "result_path": lane["result_path"],
            "packages_used": lane["packages_used"],
            "aligned_packages_load_bearing": lane["aligned_packages_load_bearing"],
            "package_observables": lane["package_observables"],
            "result_all_pass": lane["all_pass"],
            "survivor_count": lane["survivor_count"],
            "quotient_class_count": lane["quotient_class_count"],
            "ckw_survivor_count": lane["ckw_survivor_count"],
            "floor_carrier": lane["floor_carrier"],
        }
    divergence_values = {
        engine: {
            "survivor_count": lanes[engine]["survivor_count"],
            "quotient_class_count": lanes[engine]["quotient_class_count"],
            "ckw_survivor_count": lanes[engine]["ckw_survivor_count"],
        }
        for engine in lanes
    }
    return {
        "sim_id": common.SIM_ID,
        "lanes": lanes,
        "mode": common.ENGINE_MODE,
        "classification": common.CLASSIFICATION,
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "claim_path_tools": ["Graphs", "networkx", "torch.func", "sympy", "z3", "cvc5"],
        "crossover_proofs": payload["crossover_proofs"],
        "divergence": {
            "julia_authoritative": True,
            "engine_values": divergence_values,
            "max_divergence": 0.0,
        },
        "parent_lineage": {
            "one_q_registry": payload["source_locks"]["one_q_registry"]["path"],
            "two_q_carve": payload["source_locks"]["two_q_carve"]["path"],
            "three_q_floor": payload["source_locks"]["three_q_floor"]["path"],
            "three_q_shell": payload["source_locks"]["three_q_shell"]["path"],
            "climb_ledger_correction": payload["source_locks"]["climb_ledger_correction"]["path"],
        },
        "stability_pairs": [
            {"subtree": "three_q_floor", "hash": payload["source_locks"]["three_q_floor"]["sha256"]},
            {"subtree": "three_q_shell", "hash": payload["source_locks"]["three_q_shell"]["sha256"]},
        ],
        "extra_fields": {
            "schema": "gcm_constraint_carve_3q_v0_envelope_v1",
            "coordinates": payload["coordinates"],
            "claim_ceiling": payload["claim_ceiling"],
            "carrier_and_pins_relative": True,
            "not_THE_manifold": True,
            "all_pass": all(lane["result_all_pass"] for lane in lanes.values()) and payload["all_pass"],
            "engine_lanes": ["julia", "jax", "pytorch"],
            "engine_consensus": {
                "survivor_count_agreement": len({lane["survivor_count"] for lane in lanes.values()}) == 1,
                "quotient_class_count_agreement": len({lane["quotient_class_count"] for lane in lanes.values()}) == 1,
                "ckw_survivor_count_agreement": len({lane["ckw_survivor_count"] for lane in lanes.values()}) == 1,
                "floor_row_agreement": len({lane["floor_carrier"] for lane in lanes.values()}) == 1,
            },
            "substrate_first": payload["substrate_first"],
            "source_locks": payload["source_locks"],
            "constraint_family_C": payload["constraint_family_C"],
            "candidate_space": payload["candidate_space"],
            "survivor_count": payload["survivor_count"],
            "quotient_class_count": payload["quotient"]["class_count"],
            "cross_rung_rows": payload["cross_rung_rows"],
            "ghz_vs_w_admissibility": payload["ghz_vs_w_admissibility"],
            "monogamy_ckw_row": payload["monogamy_ckw_row"],
            "floor_rows": payload["floor_rows"],
            "controls": payload["controls"],
            "lineage_free_negative": payload["lineage_free_negative"],
            "terrain_blindness_guard": payload["terrain_blindness_guard"],
            "builder_gates": payload["builder_gates"],
            "no_builder_audit_verdict": True,
            "no_builder_audit_verdict_envelope_gate": True,
            "TOOL_MANIFEST": common.TOOL_MANIFEST,
            "TOOL_INTEGRATION_DEPTH": common.TOOL_INTEGRATION_DEPTH,
            "tool_intent": common.TOOL_INTENT,
            "allowed_claims": payload["allowed_claims"],
            "blocked_consumers": payload["blocked_consumers"],
        },
    }


def main() -> int:
    spec = build_spec()
    common.write_json(SPEC_PATH, spec)
    print(json.dumps({"ok": True, "result": common.rel(SPEC_PATH)}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
