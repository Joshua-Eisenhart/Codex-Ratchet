#!/usr/bin/env python3
"""Write the build_three_engine_envelope.py spec for basin_dof_perturb_and_read_v0."""

from __future__ import annotations

import json
from typing import Any

import basin_dof_perturb_and_read_v0_common as common


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
    julia = load_lane("julia")
    jax = load_lane("jax")
    pytorch = load_lane("pytorch")
    count_values = {
        "julia": julia["computed_values"]["return_dof_count"] * 100
        + julia["computed_values"]["boundary_dof_count"] * 10
        + julia["computed_values"]["scrambling_dof_count"],
        "jax": jax["computed_values"]["return_dof_count"] * 100
        + jax["computed_values"]["boundary_dof_count"] * 10
        + jax["computed_values"]["scrambling_dof_count"],
        "pytorch": pytorch["computed_values"]["return_dof_count"] * 100
        + pytorch["computed_values"]["boundary_dof_count"] * 10
        + pytorch["computed_values"]["scrambling_dof_count"],
    }
    all_lanes_pass = julia["all_pass"] and jax["all_pass"] and pytorch["all_pass"]
    extra_fields = {
        **obj,
        "schema": f"{common.SIM_ID}.envelope.v1",
        "source_path": common.rel(common.SIM_DIR / "write_envelope_spec.py"),
        "source_sha256": common.sha256_file(common.SIM_DIR / "write_envelope_spec.py"),
        "result_path": common.rel(ENVELOPE_PATH),
        "all_pass": obj["all_pass"] and all_lanes_pass and len(set(count_values.values())) == 1,
        "lane_comparison": {
            "classification_count_values": count_values,
            "all_lanes_same_classification_counts": len(set(count_values.values())) == 1,
            "return_boundary_counts": {
                "julia": {
                    "return": julia["computed_values"]["return_dof_count"],
                    "boundary": julia["computed_values"]["boundary_dof_count"],
                    "scrambling": julia["computed_values"]["scrambling_dof_count"],
                },
                "jax": {
                    "return": jax["computed_values"]["return_dof_count"],
                    "boundary": jax["computed_values"]["boundary_dof_count"],
                    "scrambling": jax["computed_values"]["scrambling_dof_count"],
                },
                "pytorch": {
                    "return": pytorch["computed_values"]["return_dof_count"],
                    "boundary": pytorch["computed_values"]["boundary_dof_count"],
                    "scrambling": pytorch["computed_values"]["scrambling_dof_count"],
                },
            },
        },
        "capability_receipts": {
            "julia": julia.get("capability_receipts", []),
            "jax": jax.get("capability_receipts", []),
            "pytorch": pytorch.get("capability_receipts", []),
        },
        "tool_calls": {
            "julia": julia.get("tool_calls", []),
            "jax": jax.get("tool_calls", []),
            "pytorch": pytorch.get("tool_calls", []),
        },
        "one_to_one_tool_calls": {
            "pass": all(leg.get("one_to_one_tool_calls", {}).get("pass") is True for leg in (julia, jax, pytorch)),
            "by_engine": {
                "julia": julia.get("one_to_one_tool_calls", {}),
                "jax": jax.get("one_to_one_tool_calls", {}),
                "pytorch": pytorch.get("one_to_one_tool_calls", {}),
            },
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
                    "dof_classification_table": obj["dof_classification_table"],
                    "controls": obj["controls"],
                    "summary": obj["result_summary"],
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
            "julia_z3": julia["crossover_proofs"]["julia_z3"],
        },
        "divergence": {
            "julia_authoritative": True,
            "engine_values": count_values,
            "max_divergence": max(count_values.values()) - min(count_values.values()),
            "tolerance": 0,
            "basis": "classification count code return*100 + boundary*10 + scrambling",
        },
        "parent_lineage": {
            key: row["path"]
            for key, row in obj["source_import_audit"]["authority_and_parents"].items()
        },
        "stability_pairs": [
            {"subtree": "dof_classification_table", "hash": common.stable_sha256(obj["dof_classification_table"])},
            {"subtree": "controls", "hash": common.stable_sha256(obj["controls"])},
            {"subtree": "axis0_readout_rebuild", "hash": common.stable_sha256(obj["axis0_readout_rebuild"])},
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
