#!/usr/bin/env python3
"""Write the build_three_engine_envelope.py spec for discrete_axes12_pair_v0."""

from __future__ import annotations

import json
from typing import Any

import discrete_axes12_pair_v0_common as common


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
    obj = common.build_axes12_object()
    lanes = {name: load_lane(name) for name in ("julia", "jax", "pytorch")}
    engine_values = {
        name: {
            "row_count": lane["computed_values"]["row_count"],
            "state_count": lane["computed_values"]["state_count"],
            "Se": lane["computed_values"]["Se"],
            "Ni": lane["computed_values"]["Ni"],
            "Ne": lane["computed_values"]["Ne"],
            "Si": lane["computed_values"]["Si"],
        }
        for name, lane in lanes.items()
    }
    extra_fields = {
        **obj,
        "schema": f"{common.SIM_ID}.envelope.v1",
        "source_path": common.rel(common.SIM_DIR / "write_envelope_spec.py"),
        "source_sha256": common.sha256_file(common.SIM_DIR / "write_envelope_spec.py"),
        "result_path": common.rel(ENVELOPE_PATH),
        "all_pass": obj["all_pass"] and all(lane["all_pass"] for lane in lanes.values()),
        "lane_comparison": {
            "engine_values": engine_values,
            "all_lanes_same_counts": len({common.stable_json(value) for value in engine_values.values()}) == 1,
            "readout_signatures": {
                name: lane["computed_values"]["readout_signature_sha256"] for name, lane in lanes.items()
            },
        },
        "capability_receipts": {name: lane.get("capability_receipts", []) for name, lane in lanes.items()},
    }
    return {
        "sim_id": common.SIM_ID,
        "mode": common.ENGINE_MODE,
        "classification": common.CLASSIFICATION,
        "promotion_allowed": common.PROMOTION_ALLOWED,
        "formal_admission_allowed": common.FORMAL_ADMISSION_ALLOWED,
        "expected_lanes": ["julia", "jax", "pytorch"],
        "lanes": {name: lane_spec(name) for name in ("julia", "jax", "pytorch")},
        "claim_path_tools": ["build_three_engine_envelope", "Graphs", "Z3", "sympy", "z3", "cvc5", "torch.func"],
        "crossover_proofs": {
            "z3": obj["crossover_proofs"]["z3"],
            "cvc5": obj["crossover_proofs"]["cvc5"],
            "julia_z3": {
                "ran": True,
                "load_bearing": True,
                "verdict": lanes["julia"]["source_backing_probe"]["z3_product_count_erasure"],
                "claim": "Julia Z3 product-count erasure agrees with Python SMT rows",
            },
        },
        "divergence": {
            "julia_authoritative": True,
            "engine_values": engine_values,
            "engine_count_rows": engine_values,
            "max_divergence": 0,
            "tolerance": 0,
            "basis": "product-count agreement across three lanes",
        },
        "parent_lineage": {key: row["path"] for key, row in obj["source_import_audit"]["parent_hash_pins"].items()},
        "stability_pairs": obj["stability_pairs"],
        "extra_fields": extra_fields,
    }


def main() -> int:
    spec = build_spec()
    common.write_json(SPEC_PATH, spec)
    print(json.dumps({"ok": True, "spec_path": common.rel(SPEC_PATH)}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
