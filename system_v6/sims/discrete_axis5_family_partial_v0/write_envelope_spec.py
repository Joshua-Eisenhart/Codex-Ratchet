#!/usr/bin/env python3
"""Write the build_three_engine_envelope.py spec for discrete_axis5_family_partial_v0."""

from __future__ import annotations

import json
from typing import Any

import discrete_axis5_family_partial_v0_common as common


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
    axis5_object = common.build_axis5_object()
    julia = load_lane("julia")
    jax = load_lane("jax")
    pytorch = load_lane("pytorch")
    engine_values = {
        name: {
            "dephasing_gradient_side": lane["computed_values"]["dephasing_gradient_side"],
            "unitary_hamiltonian_side": lane["computed_values"]["unitary_hamiltonian_side"],
            "boundary": lane["computed_values"]["boundary"],
            "table_rows": lane["computed_values"]["table_rows"],
        }
        for name, lane in {"julia": julia, "jax": jax, "pytorch": pytorch}.items()
    }
    table_rows = [row["table_rows"] for row in engine_values.values()]
    all_lanes_pass = julia["all_pass"] and jax["all_pass"] and pytorch["all_pass"]
    extra_fields = {
        **axis5_object,
        "schema": f"{common.SIM_ID}.envelope.v1",
        "source_path": common.rel(common.SIM_DIR / "write_envelope_spec.py"),
        "source_sha256": common.sha256_file(common.SIM_DIR / "write_envelope_spec.py"),
        "result_path": common.rel(ENVELOPE_PATH),
        "all_pass": axis5_object["all_pass"] and all_lanes_pass,
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
        "claim_path_tools": ["build_three_engine_envelope", "Z3", "z3", "cvc5", "torch.func"],
        "crossover_proofs": {
            "z3": axis5_object["crossover_proofs"]["z3"],
            "cvc5": axis5_object["crossover_proofs"]["cvc5"],
            "julia_z3": {
                "ran": True,
                "load_bearing": True,
                "verdict": julia["source_backing_probe"]["z3_family_count_erasure"],
                "claim": "Julia Z3 family-count erasure agrees with Python SMT rows",
            },
        },
        "divergence": {
            "julia_authoritative": True,
            "engine_values": {name: row["table_rows"] for name, row in engine_values.items()},
            "engine_count_rows": engine_values,
            "max_divergence": max(table_rows) - min(table_rows),
            "tolerance": 0,
            "basis": "table-row and family-count agreement across three lanes",
        },
        "parent_lineage": {
            key: row["path"]
            for key, row in axis5_object["source_import_audit"]["parent_hash_pins"].items()
        },
        "stability_pairs": [
            {"subtree": "axis5_family_table", "hash": common.stable_sha256(axis5_object["axis5_family_table"])},
            {
                "subtree": "independence_rows_vs_axes0_6",
                "hash": common.stable_sha256(axis5_object["independence_rows_vs_axes0_6"]),
            },
            {"subtree": "substage_product_rows", "hash": common.stable_sha256(axis5_object["substage_product_rows"])},
            {"subtree": "controls", "hash": common.stable_sha256(axis5_object["controls"])},
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
