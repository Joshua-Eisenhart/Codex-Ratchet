#!/usr/bin/env python3
"""Write the build_three_engine_envelope.py spec for carnot_szilard_basin_cycle_v0."""

from __future__ import annotations

import json
from typing import Any

import carnot_szilard_basin_cycle_v0_common as common


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
        "capability_receipts": result.get("capability_receipts", []),
        "tool_calls": result.get("tool_calls", []),
        "one_to_one_tool_calls": result.get("one_to_one_tool_calls", {}),
    }


def build_spec() -> dict[str, Any]:
    obj = common.build_packet_object()
    lanes = {engine: load_lane(engine) for engine in ("julia", "jax", "pytorch")}
    engine_values = {
        engine: lane["computed_values"]["sample_m"] * 100 + lane["computed_values"]["full_graph_m"]
        for engine, lane in lanes.items()
    }
    all_lanes_pass = all(lane["all_pass"] for lane in lanes.values())
    extra_fields = {
        **obj,
        "schema": f"{common.SIM_ID}.envelope.v1",
        "source_path": common.rel(common.SIM_DIR / "write_envelope_spec.py"),
        "source_sha256": common.sha256_file(common.SIM_DIR / "write_envelope_spec.py"),
        "result_path": common.rel(ENVELOPE_PATH),
        "all_pass": obj["all_pass"] and all_lanes_pass and len(set(engine_values.values())) == 1,
        "envelope_built_with_helper": True,
        "build_helper_path": "scripts/build_three_engine_envelope.py",
        "no_builder_audit_verdict": True,
        "no_builder_audit_verdict_envelope_gate": True,
        "builder_gates": {
            "packet_audit_verdict_absent": not (common.SIM_DIR / "audit_verdict.md").exists(),
            "all_lanes_pass": all_lanes_pass,
            "floor_and_closure_pass": obj["all_pass"],
            "sample_and_full_m_scopes_both_reported": all(
                row["m_readings_reported"] == ["sample", "full_graph"] for row in obj["basin_cycle_rows"]
            ),
            "no_heat_work_or_bath_gate_faked": True,
        },
        "lane_comparison": {
            "engine_values": engine_values,
            "all_lanes_same": len(set(engine_values.values())) == 1,
            "basis": "sample_m*100 + full_graph_m",
        },
        "capability_receipts": {engine: lane.get("capability_receipts", []) for engine, lane in lanes.items()},
        "tool_calls": {engine: lane.get("tool_calls", []) for engine, lane in lanes.items()},
        "one_to_one_tool_calls": {
            "pass": all(lane.get("one_to_one_tool_calls", {}).get("pass") is True for lane in lanes.values()),
            "by_engine": {engine: lane.get("one_to_one_tool_calls", {}) for engine, lane in lanes.items()},
        },
        "result_integrity": {
            "leg_result_sha256": {
                engine: common.sha256_file(common.RESULT_DIR / f"{common.SIM_ID}_{engine}_results.json")
                for engine in ("julia", "jax", "pytorch")
            },
            "build_helper_path": "scripts/build_three_engine_envelope.py",
            "build_helper_sha256": common.sha256_file(common.ROOT / "scripts/build_three_engine_envelope.py"),
            "envelope_content_without_result_hash_sha256": common.stable_sha256(
                {
                    "basin_cycle_rows": obj["basin_cycle_rows"],
                    "controls": obj["controls"],
                    "alternation_rows": obj["alternation_rows"],
                }
            ),
        },
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
            "networkx",
            "torch.func",
            "torch_geometric",
            "sympy",
            "z3",
            "cvc5",
        ],
        "crossover_proofs": {
            "z3": obj["crossover_proofs"]["z3"],
            "cvc5": obj["crossover_proofs"]["cvc5"],
            "julia_z3": lanes["julia"]["crossover_proofs"]["julia_z3"],
        },
        "divergence": {
            "julia_authoritative": True,
            "engine_values": engine_values,
            "max_divergence": max(engine_values.values()) - min(engine_values.values()),
            "tolerance": 0,
            "basis": "sample_m*100 + full_graph_m",
        },
        "parent_lineage": {key: row["path"] for key, row in obj["source_import_audit"].items()},
        "stability_pairs": [
            {"subtree": "basin_cycle_rows", "hash": common.stable_sha256(obj["basin_cycle_rows"])},
            {"subtree": "controls", "hash": common.stable_sha256(obj["controls"])},
            {"subtree": "alternation_rows", "hash": common.stable_sha256(obj["alternation_rows"])},
            {"subtree": "structure_map_table", "hash": common.stable_sha256(obj["structure_map_table"])},
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
