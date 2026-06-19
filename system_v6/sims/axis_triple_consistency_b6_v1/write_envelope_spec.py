#!/usr/bin/env python3
"""Write the build_three_engine_envelope.py spec for axis_triple_consistency_b6_v1."""

from __future__ import annotations

import json
from typing import Any

import axis_triple_consistency_b6_v1_common as common


SPEC_PATH = common.SIM_DIR / f"{common.SIM_ID}_envelope_spec.json"
ENVELOPE_PATH = common.RESULT_DIR / f"{common.SIM_ID}_envelope_results.json"


def load_lane(engine: str) -> dict[str, Any]:
    return common.load_json(common.RESULT_DIR / f"{common.SIM_ID}_{engine}_results.json")


def lane_spec(engine: str) -> dict[str, Any]:
    result = load_lane(engine)
    return {
        "source_path": result["source_path"],
        "result_path": result["result_path"],
        "packages_used": result["packages_used"],
        "aligned_packages_load_bearing": result["aligned_packages_load_bearing"],
        "package_observables": result["package_observables"],
        "result_all_pass": result["all_pass"],
        "engine_mode": result.get("engine_mode", common.ENGINE_MODE),
        "computed_values": result.get("computed_values", {}),
        "per_row_sign_vector_sha256": result.get("per_row_sign_vector_sha256"),
        "panel_anchor_checks": result.get("panel_anchor_checks", []),
        "capability_receipts": result.get("capability_receipts", []),
        "tool_calls": result.get("tool_calls", []),
        "source_backing_probe": result.get("source_backing_probe", {}),
    }


def build_spec() -> dict[str, Any]:
    obj = common.build_axis_triple_object()
    lanes = {engine: load_lane(engine) for engine in ("julia", "jax", "pytorch")}
    expected_values = common.engine_computed_values(obj)
    engine_values = {engine: lane.get("computed_values", {}) for engine, lane in lanes.items()}
    value_keys = [
        "shared_carrier_status",
        "sample_total",
        "agreement_count",
        "violation_count",
        "nonneutral_total",
        "nonneutral_agreement_count",
        "faithful_33_cell_placement_possible",
        "panel_pass_count",
        "sign_vector_sha256",
    ]
    engine_values_match = all(
        engine_values[engine].get(key) == expected_values[key]
        for engine in engine_values
        for key in value_keys
    )
    all_lanes_pass = all(lane.get("all_pass") for lane in lanes.values())
    per_lane_hashes = {
        engine: lanes[engine].get("per_row_sign_vector_sha256") for engine in ("julia", "jax", "pytorch")
    }
    extra_fields: dict[str, Any] = {
        "schema": f"{common.SIM_ID}.envelope.v1",
        "source_path": common.rel(common.SIM_DIR / "write_envelope_spec.py"),
        "source_sha256": common.sha256_file(common.SIM_DIR / "write_envelope_spec.py"),
        "result_path": common.rel(ENVELOPE_PATH),
        "all_pass": obj["all_pass"] and all_lanes_pass and engine_values_match,
        "state_object_id": obj["state_object_id"],
        "claim_ceiling": common.CLAIM_CEILING,
        "source_import_audit": obj["source_import_audit"],
        "shared_carrier_decision": obj["shared_carrier_decision"],
        "carrier_faithfulness_audit": obj["carrier_faithfulness_audit"],
        "sign_convention_ledger": obj["sign_convention_ledger"],
        "consistency_table": obj["consistency_table"],
        "consistency_summary": obj["consistency_summary"],
        "violation_rows": obj["violation_rows"],
        "sign_vector_sha256": obj["sign_vector_sha256"],
        "per_lane_sign_vector_hashes": per_lane_hashes,
        "panel_anchor_checks": obj["panel_anchor_checks"],
        "controls": obj["controls"],
        "v0_hopf_transplant_regression": obj["v0_hopf_transplant_regression"],
        "smt_rows": obj["smt_rows"],
        "reading_A_adjudication": obj["reading_A_adjudication"],
        "TOOL_MANIFEST": common.TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": common.TOOL_INTEGRATION_DEPTH,
        "TOOL_INTENT_MATRIX": obj["TOOL_INTENT_MATRIX"],
        "tool_intent": common.TOOL_INTENT,
        "builder_gates": obj["builder_gates"],
        "no_builder_audit_verdict": obj["no_builder_audit_verdict"],
        "no_builder_audit_verdict_envelope_gate": obj["no_builder_audit_verdict_envelope_gate"],
        "envelope_built_with_helper": True,
        "build_helper_path": "scripts/build_three_engine_envelope.py",
        "claim_sections": obj["claim_sections"],
        "allowed_claims": obj["allowed_claims"],
        "disallowed_claims": obj["disallowed_claims"],
        "blocked_consumers": obj["blocked_consumers"],
        "divergence_log": obj["divergence_log"],
        "ceiling": {
            "classification": common.CLASSIFICATION,
            "claim_ceiling": common.CLAIM_CEILING,
            "promotion_allowed": common.PROMOTION_ALLOWED,
            "formal_admission_allowed": common.FORMAL_ADMISSION_ALLOWED,
        },
        "engine_count_comparison": {
            "expected_values": expected_values,
            "engine_values": engine_values,
            "engine_values_match": engine_values_match,
        },
        "capability_receipts": {
            engine: lanes[engine].get("capability_receipts", []) for engine in ("julia", "jax", "pytorch")
        },
        "validator_expected_commands": common.validator_expected_commands(),
    }
    return {
        "sim_id": common.SIM_ID,
        "mode": common.ENGINE_MODE,
        "classification": common.CLASSIFICATION,
        "promotion_allowed": common.PROMOTION_ALLOWED,
        "formal_admission_allowed": common.FORMAL_ADMISSION_ALLOWED,
        "expected_lanes": ["julia", "jax", "pytorch"],
        "lanes": {engine: lane_spec(engine) for engine in ("julia", "jax", "pytorch")},
        "claim_path_tools": [
            "build_three_engine_envelope",
            "Graphs",
            "Z3",
            "networkx",
            "sympy",
            "z3",
            "cvc5",
            "torch.func",
            "torch_geometric",
        ],
        "crossover_proofs": {
            "z3": obj["smt_rows"]["z3"],
            "cvc5": obj["smt_rows"]["cvc5"],
            "julia_z3": lanes["julia"]["crossover_proofs"]["julia_z3"],
        },
        "divergence": {
            "julia_authoritative": True,
            "engine_values": {
                engine: 1.0 if lanes[engine].get("all_pass") and engine_values_match else 0.0
                for engine in ("julia", "jax", "pytorch")
            },
            "max_divergence": 0.0 if all_lanes_pass and engine_values_match else 1.0,
            "tolerance": 0.0,
            "basis": "exact shared-carrier blocker status, count rows, and per-row sign-vector hash equality across Julia/JAX/PyTorch",
        },
        "parent_lineage": {
            key: row["path"] for key, row in obj["source_import_audit"]["parent_hash_pins"].items()
        },
        "stability_pairs": [
            {"subtree": "consistency_table", "hash": common.stable_sha256(obj["consistency_table"])},
            {"subtree": "violation_rows", "hash": common.stable_sha256(obj["violation_rows"])},
            {"subtree": "controls", "hash": common.stable_sha256(obj["controls"])},
            {"subtree": "carrier_faithfulness_audit", "hash": common.stable_sha256(obj["carrier_faithfulness_audit"])},
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
