#!/usr/bin/env python3
"""Write the build_three_engine_envelope.py spec for manifold_super_sim_v0."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import manifold_super_sim_v0_common as common


SPEC_PATH = common.SIM_DIR / f"{common.SIM_ID}_envelope_spec.json"


def load_lane(engine: str) -> dict[str, Any]:
    path = common.RESULT_DIR / f"{common.SIM_ID}_{engine}_results.json"
    return common.load_json(path)


def lane_spec(engine: str, source: str, packages: list[str], load_bearing: list[str], observables: dict[str, str]) -> dict[str, Any]:
    result = load_lane(engine)
    return {
        "source_path": f"system_v6/sims/{common.SIM_ID}/{source}",
        "result_path": result["result_path"],
        "packages_used": packages,
        "aligned_packages_load_bearing": load_bearing,
        "package_observables": observables,
        "result_all_pass": result["all_pass"],
        "state_object_id": result.get("state_object_id"),
    }


def build_spec() -> dict[str, Any]:
    super_object = common.build_super_object(common.scipy_expm)
    artifact = common.write_trajectory_artifact(super_object)
    julia = load_lane("julia")
    jax = load_lane("jax")
    pytorch = load_lane("pytorch")
    all_lanes_pass = julia["all_pass"] and jax["all_pass"] and pytorch["all_pass"]
    extra = {
        "all_pass": super_object["all_pass"] and all_lanes_pass and artifact["sha_verified"],
        "state_object_id": super_object["state_object_id"],
        "family": super_object["family"],
        "substrate": super_object["substrate"],
        "source_import_audit": super_object["source_import_audit"],
        "parent_lineage": super_object["parent_lineage"],
        "layers": super_object["layers"],
        "weld_anchors": super_object["weld_anchors"],
        "kill_controls": super_object["kill_controls"],
        "TOOL_MANIFEST": common.TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": common.TOOL_INTEGRATION_DEPTH,
        "tool_intent": common.TOOL_INTENT,
        "trajectory_artifact": artifact,
        "claim_sections": super_object["claim_sections"],
        "allowed_claims": [
            "scratch diagnostic: one shared finite 33-cell object across L1-L5",
            "chart-relative finite basin partitions and controls",
            "typed entropy/information rows with explicit conventions",
        ],
        "disallowed_claims": [
            "formal admission",
            "invariant/frame-independent sub-basins",
            "axis/bridge/physics claims",
            "joint-engine/two-engine convention sweep claims",
        ],
        "ceiling": {
            "classification": common.CLASSIFICATION,
            "promotion_allowed": common.PROMOTION_ALLOWED,
            "formal_admission_allowed": common.FORMAL_ADMISSION_ALLOWED,
        },
        "capability_receipts": {
            "julia": julia.get("capability_receipts", []),
            "jax": jax.get("source_backing_probe", {}),
            "pytorch": pytorch.get("source_backing_probe", {}),
        },
        "validator_expected_commands": [
            "/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/manifold_super_sim_v0/validate_manifold_super_sim_v0.py",
            "/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py --require-pytorch --strict-source-backed --require-tool-intent system_v6/sims/manifold_super_sim_v0/results/manifold_super_sim_v0_envelope_results.json",
            "/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 -m pytest -q system_v6/sims/manifold_super_sim_v0/tests",
        ],
    }
    return {
        "sim_id": common.SIM_ID,
        "mode": "all_three_full_sims",
        "classification": common.CLASSIFICATION,
        "promotion_allowed": common.PROMOTION_ALLOWED,
        "formal_admission_allowed": common.FORMAL_ADMISSION_ALLOWED,
        "expected_lanes": ["julia", "jax", "pytorch"],
        "lanes": {
            "julia": lane_spec(
                "julia",
                "manifold_super_sim_v0_julia.jl",
                ["Graphs", "Z3", "LinearAlgebra", "JSON", "Dates", "SHA"],
                ["Graphs", "Z3"],
                {
                    "Graphs": "partition_rows.G0/G1 terminal_class_sizes from Graphs SCCs",
                    "Z3": "crossover_proofs.julia_z3 partition identity",
                },
            ),
            "jax": lane_spec(
                "jax",
                "manifold_super_sim_v0_jax.py",
                ["jax", "jax.numpy", "jax.scipy.linalg", "networkx", "sympy", "z3", "cvc5", "json", "pathlib"],
                ["networkx", "sympy", "z3", "cvc5"],
                {
                    "networkx": "source_backing_probe.networkx_component_count plus inherited finite graph recomputation",
                    "sympy": "source_backing_probe.sympy_exact_log and typed entropy expressions",
                    "z3": "crossover_proofs.z3 computed partition identity",
                    "cvc5": "crossover_proofs.cvc5 computed partition identity",
                },
            ),
            "pytorch": lane_spec(
                "pytorch",
                "manifold_super_sim_v0_pytorch.py",
                ["torch", "torch.func", "torch_geometric", "sympy", "z3", "cvc5", "json"],
                ["sympy", "z3", "cvc5"],
                {
                    "torch.func": "supportive source_backing_probe.torch_func_batched_shape only; torch_expm uses plain torch.matrix_exp",
                    "torch_geometric": "supportive source_backing_probe.torch_geometric_edge_count only; finite graph rows use shared Python common path",
                    "sympy": "source_backing_probe.sympy_exact_log and typed entropy expressions",
                    "z3": "crossover_proofs.z3 computed partition identity",
                    "cvc5": "crossover_proofs.cvc5 computed partition identity",
                },
            ),
        },
        "claim_path_tools": ["Graphs", "Z3", "networkx", "sympy", "z3", "cvc5"],
        "crossover_proofs": {
            "z3": super_object["crossover_proofs"]["z3"],
            "cvc5": super_object["crossover_proofs"]["cvc5"],
            "julia_z3": julia["crossover_proofs"]["julia_z3"],
        },
        "divergence": {
            "julia_authoritative": True,
            "engine_values": {
                "julia": 1.0 if julia["all_pass"] else 0.0,
                "jax": 1.0 if jax["all_pass"] else 0.0,
                "pytorch": 1.0 if pytorch["all_pass"] else 0.0,
            },
            "max_divergence": 0.0 if all_lanes_pass else 1.0,
            "tolerance": 0.0,
            "basis": "boolean all_pass agreement plus packet validator anchor equality",
        },
        "parent_lineage": {key: row["path"] for key, row in super_object["parent_lineage"]["consumed_inputs"].items()},
        "stability_pairs": [
            {"subtree": row["path"], "hash": row["sha256"]}
            for row in super_object["parent_lineage"]["consumed_inputs"].values()
            if row.get("sha256")
        ],
        "extra_fields": extra,
    }


def main() -> int:
    spec = build_spec()
    common.write_json(SPEC_PATH, spec)
    print(json.dumps({"ok": True, "spec_path": common.rel(SPEC_PATH)}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
