#!/usr/bin/env python3
"""Write the standard three-engine envelope for ECD.04."""

from __future__ import annotations

import json
import sys
from typing import Any

import ecd04_record_conditioned_navigation_v0_common as common


sys.path.insert(0, str(common.ROOT / "scripts"))
from build_three_engine_envelope import build_envelope  # noqa: E402


def load_lane(engine: str) -> dict[str, Any]:
    return common.load_json(common.RESULT_DIR / f"{common.SIM_ID}_{engine}_results.json")


def lane_spec(engine: str) -> dict[str, Any]:
    lane = load_lane(engine)
    return {
        "source_path": lane["source_path"],
        "result_path": lane["result_path"],
        "packages_used": lane["packages_used"],
        "aligned_packages_load_bearing": lane["aligned_packages_load_bearing"],
        "package_observables": lane["package_observables"],
        "result_all_pass": lane["all_pass"],
        "engine_mode": lane["engine_mode"],
        "capability_receipts": lane.get("capability_receipts", []),
        "tool_calls": lane.get("tool_calls", []),
        "one_to_one_tool_calls": lane.get("one_to_one_tool_calls", {}),
    }


def build_result() -> dict[str, Any]:
    base = common.load_json(common.RESULT_PATH) if common.RESULT_PATH.exists() else common.build_navigation_object()
    lanes = {engine: load_lane(engine) for engine in ("julia", "jax", "pytorch")}
    engine_values = {
        "julia": lanes["julia"]["computed_values"]["margin_scaled"],
        "jax": lanes["jax"]["computed_values"]["margin_scaled"],
        "pytorch": lanes["pytorch"]["computed_values"]["margin_scaled"],
    }
    all_lanes_pass = all(lane["all_pass"] for lane in lanes.values())
    extra_fields = {
        **base,
        "schema": f"{common.SIM_ID}.envelope.v1",
        "source_path": common.rel(common.SIM_DIR / f"{common.SIM_ID}_envelope.py"),
        "source_sha256": common.sha256_file(common.SIM_DIR / f"{common.SIM_ID}_envelope.py"),
        "result_path": common.rel(common.ENVELOPE_PATH),
        "all_pass": base["all_pass"] and all_lanes_pass and len(set(engine_values.values())) == 1,
        "envelope_built_with_helper": True,
        "build_helper_path": "scripts/build_three_engine_envelope.py",
        "no_builder_audit_verdict_envelope_gate": True,
        "builder_gates": {
            "g2a_boundary_helper_from_birth": True,
            "validator_delegates_to_builder_audit_boundary": True,
            "all_lanes_pass": all_lanes_pass,
            "information_parity_row_first": True,
            "basin_nontriviality_row_first": True,
            "packet_audit_verdict_absent": not (common.SIM_DIR / "audit_verdict.md").exists(),
        },
        "lane_comparison": {
            "engine_values": engine_values,
            "all_lanes_same_margin": len(set(engine_values.values())) == 1,
            "basis": "baseline_minus_qit_success_weighted_record_cost_scaled",
        },
        "capability_receipts": {engine: lanes[engine].get("capability_receipts", []) for engine in lanes},
        "tool_calls": {engine: lanes[engine].get("tool_calls", []) for engine in lanes},
        "one_to_one_tool_calls": {
            "pass": all(lanes[engine].get("one_to_one_tool_calls", {}).get("pass") is True for engine in lanes),
            "by_engine": {engine: lanes[engine].get("one_to_one_tool_calls", {}) for engine in lanes},
        },
        "result_integrity": {
            "base_result_sha256": common.sha256_file(common.RESULT_PATH),
            "lane_result_sha256": {
                engine: common.sha256_file(common.RESULT_DIR / f"{common.SIM_ID}_{engine}_results.json")
                for engine in lanes
            },
            "envelope_content_without_result_hash_sha256": common.stable_sha256(
                {
                    "witness_gates": base["witness_gates"],
                    "qit_side": base["qit_side"],
                    "baseline_side": base["baseline_side"],
                    "controls": base["controls"],
                    "discriminator": base["discriminator"],
                }
            ),
        },
    }
    return build_envelope(
        sim_id=common.SIM_ID,
        mode=common.ENGINE_MODE,
        classification=common.CLASSIFICATION,
        promotion_allowed=False,
        formal_admission_allowed=False,
        expected_lanes=["julia", "jax", "pytorch"],
        lanes={engine: lane_spec(engine) for engine in ("julia", "jax", "pytorch")},
        claim_path_tools=["Graphs", "Z3", "networkx", "torch.func", "torch_geometric", "sympy", "z3", "cvc5"],
        crossover_proofs={
            "z3": base["crossover_proofs"]["z3"],
            "cvc5": base["crossover_proofs"]["cvc5"],
            "julia_z3": lanes["julia"]["crossover_proofs"]["julia_z3"],
        },
        divergence={
            "julia_authoritative": True,
            "engine_values": engine_values,
            "max_divergence": max(engine_values.values()) - min(engine_values.values()),
            "tolerance": 0,
            "basis": "baseline_minus_qit_success_weighted_record_cost_scaled",
        },
        parent_lineage={name: row["path"] for name, row in base["source_locks"].items() if row.get("exists")},
        stability_pairs=[
            {"subtree": "shared_environment", "hash": common.stable_sha256(base["shared_environment"])},
            {"subtree": "qit_side", "hash": common.stable_sha256(base["qit_side"])},
            {"subtree": "baseline_side", "hash": common.stable_sha256(base["baseline_side"])},
            {"subtree": "controls", "hash": common.stable_sha256(base["controls"])},
        ],
        extra_fields=extra_fields,
    )


def main() -> int:
    envelope = build_result()
    common.write_json(common.ENVELOPE_PATH, envelope)
    print(
        json.dumps(
            {
                "ok": envelope["all_pass"],
                "result": common.rel(common.ENVELOPE_PATH),
                "verdict": envelope["discriminator"]["verdict"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if envelope["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
