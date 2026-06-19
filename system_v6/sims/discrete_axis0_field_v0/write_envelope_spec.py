#!/usr/bin/env python3
"""Write the build_three_engine_envelope.py spec for discrete_axis0_field_v0."""

from __future__ import annotations

import json
from typing import Any

import discrete_axis0_field_v0_common as common


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
        "state_object_id": result.get("state_object_id"),
        "engine_mode": result.get("engine_mode", common.ENGINE_MODE),
        "capability_receipts": result.get("capability_receipts", []),
        "tool_calls": result.get("tool_calls", []),
    }


def build_spec() -> dict[str, Any]:
    axis0_object = common.build_axis0_object()
    julia = load_lane("julia")
    jax = load_lane("jax")
    pytorch = load_lane("pytorch")
    stable_values = {
        "julia": julia["computed_values"]["stable_edge_count"],
        "jax": jax["computed_values"]["stable_edge_count"],
        "pytorch": pytorch["computed_values"]["stable_edge_count"],
    }
    all_lanes_pass = julia["all_pass"] and jax["all_pass"] and pytorch["all_pass"]
    extra_fields = {
        **axis0_object,
        "schema": f"{common.SIM_ID}.envelope.v1",
        "source_path": common.rel(common.SIM_DIR / "write_envelope_spec.py"),
        "source_sha256": common.sha256_file(common.SIM_DIR / "write_envelope_spec.py"),
        "result_path": common.rel(ENVELOPE_PATH),
        "all_pass": axis0_object["all_pass"] and all_lanes_pass,
        "lane_comparison": {
            "stable_edge_counts": stable_values,
            "all_lanes_same_stable_count": len(set(stable_values.values())) == 1,
            "readout_signatures": {
                "julia": julia["computed_values"]["readout_signature_sha256"],
                "jax": jax["computed_values"]["readout_signature_sha256"],
                "pytorch": pytorch["computed_values"]["readout_signature_sha256"],
            },
        },
        "capability_receipts": {
            "julia": julia.get("capability_receipts", []),
            "jax": jax.get("capability_receipts", []),
            "pytorch": pytorch.get("capability_receipts", []),
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
            "z3": axis0_object["crossover_proofs"]["z3"],
            "cvc5": axis0_object["crossover_proofs"]["cvc5"],
            "julia_z3": julia["crossover_proofs"]["julia_z3"],
        },
        "divergence": {
            "julia_authoritative": True,
            "engine_values": stable_values,
            "max_divergence": max(stable_values.values()) - min(stable_values.values()),
            "tolerance": 0,
            "basis": "stable_edge_count agreement for the exact readout candidate across three lanes",
        },
        "parent_lineage": {
            key: row["path"]
            for key, row in axis0_object["source_import_audit"]["parent_hash_pins"].items()
        },
        "stability_pairs": [
            {"subtree": "readout_table", "hash": common.stable_sha256(axis0_object["readout_table"])},
            {"subtree": "gradient_table", "hash": common.stable_sha256(axis0_object["gradient_table"])},
            {
                "subtree": "three_polarities_independence",
                "hash": common.stable_sha256(axis0_object["three_polarities_independence"]),
            },
            {"subtree": "controls", "hash": common.stable_sha256(axis0_object["controls"])},
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
