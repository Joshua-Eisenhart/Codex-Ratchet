#!/usr/bin/env python3
"""Write the build_three_engine_envelope.py spec for discrete_axis6_precedence_v0."""

from __future__ import annotations

import json
from typing import Any

import discrete_axis6_precedence_v0_common as common


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
        "state_object_id": result.get("state_object_id"),
        "engine_mode": result.get("engine_mode", common.ENGINE_MODE),
        "capability_receipts": result.get("capability_receipts", []),
        "tool_calls": result.get("tool_calls", []),
    }


def build_spec() -> dict[str, Any]:
    axis6_object = common.build_axis6_object()
    julia = load_lane("julia")
    jax = load_lane("jax")
    pytorch = load_lane("pytorch")
    engine_values = {
        name: {
            "positive": lane["computed_values"]["positive"],
            "negative": lane["computed_values"]["negative"],
            "neutral": lane["computed_values"]["neutral"],
            "nonneutral": lane["computed_values"]["nonneutral"],
            "stable_edge_count": lane["computed_values"]["stable_edge_count"],
            "changed_edge_count": lane["computed_values"]["changed_edge_count"],
        }
        for name, lane in {"julia": julia, "jax": jax, "pytorch": pytorch}.items()
    }
    nonneutral_values = [row["nonneutral"] for row in engine_values.values()]
    all_lanes_pass = julia["all_pass"] and jax["all_pass"] and pytorch["all_pass"]
    extra_fields = {
        **axis6_object,
        "schema": f"{common.SIM_ID}.envelope.v1",
        "source_path": common.rel(common.SIM_DIR / "write_envelope_spec.py"),
        "source_sha256": common.sha256_file(common.SIM_DIR / "write_envelope_spec.py"),
        "result_path": common.rel(ENVELOPE_PATH),
        "all_pass": axis6_object["all_pass"] and all_lanes_pass,
        "lane_comparison": {
            "engine_values": engine_values,
            "all_lanes_same_counts": len({common.stable_json(row) for row in engine_values.values()}) == 1,
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
    rehomed_builder_fields = {
        key: extra_fields.pop(key)
        for key in (
            "classification",
            "crossover_proofs",
            "formal_admission_allowed",
            "promotion_allowed",
            "sim_id",
        )
        if key in extra_fields
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
            "z3": axis6_object["crossover_proofs"]["z3"],
            "cvc5": axis6_object["crossover_proofs"]["cvc5"],
            "julia_z3": julia["crossover_proofs"]["julia_z3"],
        },
        "divergence": {
            "julia_authoritative": True,
            "engine_values": {name: row["nonneutral"] for name, row in engine_values.items()},
            "engine_count_rows": engine_values,
            "max_divergence": max(nonneutral_values) - min(nonneutral_values),
            "tolerance": 0,
            "basis": "nonneutral precedence count and detailed positive/negative/neutral/stability count agreement across three lanes",
        },
        "parent_lineage": {
            key: row["path"]
            for key, row in axis6_object["source_import_audit"]["parent_hash_pins"].items()
        },
        "stability_pairs": [
            {"subtree": "precedence_table", "hash": common.stable_sha256(axis6_object["precedence_table"])},
            {"subtree": "independence_rows_vs_axis0", "hash": common.stable_sha256(axis6_object["independence_rows_vs_axis0"])},
            {"subtree": "b0_b6_prediction", "hash": common.stable_sha256(axis6_object["b0_b6_prediction"])},
            {"subtree": "controls", "hash": common.stable_sha256(axis6_object["controls"])},
        ],
        **rehomed_builder_fields,
        "extra_fields": extra_fields,
    }


def main() -> int:
    spec = build_spec()
    common.write_json(SPEC_PATH, spec)
    print(json.dumps({"ok": True, "spec_path": common.rel(SPEC_PATH)}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
