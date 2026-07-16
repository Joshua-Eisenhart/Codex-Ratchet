#!/usr/bin/env python3
"""Write the build_three_engine_envelope.py spec for axis_triple_consistency_b6_v0."""

from __future__ import annotations

import json
from typing import Any

import axis_triple_consistency_b6_v0_common as common


SPEC_PATH = common.SIM_DIR / f"{common.SIM_ID}_envelope_spec.json"
ENVELOPE_PATH = common.RESULT_DIR / f"{common.SIM_ID}_envelope_results.json"


def load_lane(engine: str) -> dict[str, Any]:
    return common.load_json(common.RESULT_DIR / f"{common.SIM_ID}_{engine}_results.json")


def lane_spec(engine: str) -> dict[str, Any]:
    result = load_lane(engine)
    return {
        "source_path": result["source_path"],
        "result_path": result["result_path"],
        "reads_peer_result": False,
        "packages_used": result["packages_used"],
        "aligned_packages_load_bearing": result["aligned_packages_load_bearing"],
        "package_observables": result["package_observables"],
        "result_all_pass": result["all_pass"],
        "engine_mode": result.get("engine_mode", common.ENGINE_MODE),
        "computed_values": result.get("computed_values", {}),
        "panel_point_checks": result.get("panel_point_checks", []),
        "capability_receipts": result.get("capability_receipts", []),
        "tool_calls": result.get("tool_calls", []),
    }


def build_spec() -> dict[str, Any]:
    obj = common.build_axis_triple_object()
    lanes = {engine: load_lane(engine) for engine in ("julia", "jax", "pytorch")}
    all_lanes_pass = all(lane["all_pass"] for lane in lanes.values())
    expected_values = common.engine_computed_values(obj)
    engine_values = {engine: lane.get("computed_values", {}) for engine, lane in lanes.items()}
    count_rows_match = all(
        engine_values[engine].get(key) == expected_values[key]
        for engine in engine_values
        for key in ("sample_total", "agreement_count", "violation_count", "nonneutral_total", "nonneutral_agreement_count")
    )
    extra_fields: dict[str, Any] = {
        "schema": f"{common.SIM_ID}.envelope.v1",
        "source_path": common.rel(common.SIM_DIR / "write_envelope_spec.py"),
        "source_sha256": common.sha256_file(common.SIM_DIR / "write_envelope_spec.py"),
        "result_path": common.rel(ENVELOPE_PATH),
        "all_pass": obj["all_pass"] and all_lanes_pass and count_rows_match,
        "state_object_id": obj["state_object_id"],
        "claim_ceiling": common.CLAIM_CEILING,
        "source_import_audit": obj["source_import_audit"],
        "pinned_pair": obj["pinned_pair"],
        "carrier_decision": obj["carrier_decision"],
        "consistency_table": obj["consistency_table"],
        "consistency_summary": obj["consistency_summary"],
        "violation_rows": obj["violation_rows"],
        "panel_point_checks": obj["panel_point_checks"],
        "controls": obj["controls"],
        "smt_rows": obj["smt_rows"],
        "independence_reminder_row": obj["independence_reminder_row"],
        "TOOL_MANIFEST": common.TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": common.TOOL_INTEGRATION_DEPTH,
        "TOOL_INTENT_MATRIX": obj["TOOL_INTENT_MATRIX"],
        "tool_intent": common.TOOL_INTENT,
        "builder_gates": obj["builder_gates"],
        "no_builder_audit_verdict": obj["builder_gates"]["no_builder_audit_verdict"],
        "no_builder_audit_verdict_envelope_gate": obj["builder_gates"]["no_builder_audit_verdict_envelope_gate"],
        "envelope_built_with_helper": True,
        "build_helper_path": "scripts/build_three_engine_envelope.py",
        "claim_sections": obj["claim_sections"],
        "allowed_claims": obj["allowed_claims"],
        "disallowed_claims": obj["disallowed_claims"],
        "ceiling": {
            "classification": common.CLASSIFICATION,
            "claim_ceiling": common.CLAIM_CEILING,
            "promotion_allowed": common.PROMOTION_ALLOWED,
            "formal_admission_allowed": common.FORMAL_ADMISSION_ALLOWED,
        },
        "engine_count_comparison": {
            "expected_values": expected_values,
            "engine_values": engine_values,
            "count_rows_match": count_rows_match,
        },
        "capability_receipts": {
            "julia": lanes["julia"].get("capability_receipts", []),
            "jax": lanes["jax"].get("source_backing_probe", {}),
            "pytorch": lanes["pytorch"].get("source_backing_probe", {}),
        },
        "validator_expected_commands": [
            "JULIA_LOAD_PATH=@:@stdlib /opt/homebrew/bin/julia --startup-file=no --project=/Users/joshuaeisenhart/Codex-Ratchet/system_v5/julia_carrier system_v6/sims/axis_triple_consistency_b6_v0/axis_triple_consistency_b6_v0_julia.jl",
            "/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/axis_triple_consistency_b6_v0/axis_triple_consistency_b6_v0_jax.py",
            "/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/axis_triple_consistency_b6_v0/axis_triple_consistency_b6_v0_pytorch.py",
            "/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/axis_triple_consistency_b6_v0/write_envelope_spec.py",
            "/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/build_three_engine_envelope.py system_v6/sims/axis_triple_consistency_b6_v0/axis_triple_consistency_b6_v0_envelope_spec.json > system_v6/sims/axis_triple_consistency_b6_v0/results/axis_triple_consistency_b6_v0_envelope_results.json",
            "/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/axis_triple_consistency_b6_v0/validate_axis_triple_consistency_b6_v0.py",
            "/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py --require-pytorch --strict-source-backed --require-tool-intent system_v6/sims/axis_triple_consistency_b6_v0/results/axis_triple_consistency_b6_v0_envelope_results.json",
            "/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 -m pytest -q system_v6/sims/axis_triple_consistency_b6_v0/tests",
        ],
    }
    return {
        "sim_id": common.SIM_ID,
        "mode": common.ENGINE_MODE,
        "classification": common.CLASSIFICATION,
        "promotion_allowed": common.PROMOTION_ALLOWED,
        "formal_admission_allowed": common.FORMAL_ADMISSION_ALLOWED,
        "expected_lanes": ["julia", "jax", "pytorch"],
        "lanes": {
            "julia": lane_spec("julia"),
            "jax": lane_spec("jax"),
            "pytorch": lane_spec("pytorch"),
        },
        "claim_path_tools": [
            "build_three_engine_envelope",
            "Graphs",
            "Z3",
            "sympy",
            "z3",
            "cvc5",
            "torch.func",
            "torch_geometric",
        ],
        "crossover_proofs": {
            "z3": obj["smt_rows"]["z3_computed_table"],
            "cvc5": obj["smt_rows"]["cvc5_computed_table"],
            "julia_z3": lanes["julia"]["crossover_proofs"]["julia_z3"],
        },
        "divergence": {
            "julia_authoritative": True,
            "engine_values": {
                "julia": 1.0 if lanes["julia"]["all_pass"] and count_rows_match else 0.0,
                "jax": 1.0 if lanes["jax"]["all_pass"] and count_rows_match else 0.0,
                "pytorch": 1.0 if lanes["pytorch"]["all_pass"] and count_rows_match else 0.0,
            },
            "max_divergence": 0.0 if all_lanes_pass and count_rows_match else 1.0,
            "tolerance": 0.0,
            "basis": "boolean all_pass agreement plus exact table-count equality across Julia/JAX/PyTorch lanes",
        },
        "parent_lineage": {
            key: row["path"]
            for key, row in obj["source_import_audit"]["parent_hash_pins"].items()
        },
        "stability_pairs": [
            {"subtree": "consistency_table", "hash": common.stable_sha256(obj["consistency_table"])},
            {"subtree": "violation_rows", "hash": common.stable_sha256(obj["violation_rows"])},
            {"subtree": "panel_point_checks", "hash": common.stable_sha256(obj["panel_point_checks"])},
            {"subtree": "controls", "hash": common.stable_sha256(obj["controls"])},
        ],
        "extra_fields": extra_fields,
    }


def main() -> int:
    spec = build_spec()
    common.write_json(SPEC_PATH, spec)
    print(json.dumps({"ok": True, "spec_path": common.rel(SPEC_PATH)}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
