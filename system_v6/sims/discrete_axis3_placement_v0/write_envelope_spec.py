#!/usr/bin/env python3
"""Write the standard envelope-builder spec for discrete_axis3_placement_v0."""

from __future__ import annotations

import discrete_axis3_placement_v0_common as common


SPEC_PATH = common.SIM_DIR / f"{common.SIM_ID}_envelope_spec.json"


def load_lane(engine: str) -> dict:
    return common.load_json(common.RESULT_DIR / f"{common.SIM_ID}_{engine}_results.json")


def lane_spec(engine: str, lane: dict) -> dict:
    return {
        "source_path": lane["source_path"],
        "result_path": lane["result_path"],
        "packages_used": lane["packages_used"],
        "aligned_packages_load_bearing": lane["aligned_packages_load_bearing"],
        "package_observables": lane["package_observables"],
        "result_all_pass": lane["all_pass"],
        "computed_values": lane["computed_values"],
    }


def build_spec() -> dict:
    axis3 = common.build_axis3_object()
    lanes = {engine: lane_spec(engine, load_lane(engine)) for engine in ["julia", "jax", "pytorch"]}
    engine_values = {
        engine: {
            "stable_edge_count": lane["computed_values"]["stable_edge_count"],
            "changed_edge_count": lane["computed_values"]["changed_edge_count"],
            "fiber_count": lane["computed_values"]["fiber_count"],
            "base_count": lane["computed_values"]["base_count"],
        }
        for engine, lane in lanes.items()
    }
    all_numbers = [
        value
        for row in engine_values.values()
        for value in row.values()
    ]
    divergence = {
        "julia_authoritative": True,
        "engine_values": engine_values,
        "max_divergence": max(all_numbers) - min(all_numbers) if all_numbers else 0,
        "exact_counts_match": len({common.stable_json(row) for row in engine_values.values()}) == 1,
    }
    extra_fields = dict(axis3)
    extra_fields["all_pass"] = axis3["all_pass"] and all(load_lane(engine)["all_pass"] for engine in ["julia", "jax", "pytorch"])
    extra_fields["mode"] = common.ENGINE_MODE
    return {
        "sim_id": common.SIM_ID,
        "lanes": lanes,
        "mode": common.ENGINE_MODE,
        "classification": common.CLASSIFICATION,
        "promotion_allowed": common.PROMOTION_ALLOWED,
        "formal_admission_allowed": common.FORMAL_ADMISSION_ALLOWED,
        "claim_path_tools": ["Graphs", "Z3", "networkx", "torch.func", "torch_geometric", "sympy", "z3", "cvc5"],
        "crossover_proofs": axis3["crossover_proofs"],
        "divergence": divergence,
        "parent_lineage": {
            key: row["path"]
            for section in axis3["source_import_audit"].values()
            if isinstance(section, dict)
            for key, row in section.items()
            if isinstance(row, dict) and row.get("path")
        },
        "stability_pairs": [
            {"subtree": "pin_block", "hash": axis3["pin_block"]["pin_block_sha256"]},
            {
                "subtree": "placement_table",
                "hash": common.stable_sha256(axis3["placement_table"]),
            },
            {
                "subtree": "independence_rows_vs_axis0",
                "hash": common.stable_sha256(axis3["independence_rows_vs_axis0"]),
            },
        ],
        "extra_fields": extra_fields,
    }


def main() -> int:
    spec = build_spec()
    common.write_json(SPEC_PATH, spec)
    print(common.stable_json({"ok": True, "spec_path": common.rel(SPEC_PATH)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
