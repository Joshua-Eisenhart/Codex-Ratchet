#!/usr/bin/env python3
"""Write the build_three_engine_envelope.py spec for manifold_family_b_integrated_v0."""

from __future__ import annotations

import json
from typing import Any

import manifold_family_b_integrated_v0_common as common


SPEC_PATH = common.SIM_DIR / f"{common.SIM_ID}_envelope_spec.json"


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
    }


def build_spec() -> dict[str, Any]:
    family_b_object = common.build_family_b_object()
    artifact = common.write_trajectory_artifact(family_b_object)
    julia = load_lane("julia")
    jax = load_lane("jax")
    pytorch = load_lane("pytorch")
    all_lanes_pass = julia["all_pass"] and jax["all_pass"] and pytorch["all_pass"]
    extra = {
        "all_pass": family_b_object["all_pass"] and all_lanes_pass and artifact["sha_verified"],
        "state_object_id": family_b_object["state_object_id"],
        "family": family_b_object["family"],
        "family_a_rows_used": family_b_object["family_a_rows_used"],
        "two_engine_rows_used": family_b_object["two_engine_rows_used"],
        "substrate": family_b_object["substrate"],
        "engine_mode": common.ENGINE_MODE,
        "engine_scope_notes": {
            "julia": "independently recomputes Z4xZ2 orbit graph and MCT compression cardinality counts with Graphs/Z3",
            "jax": "uses package-backed finite graph/SMT probes plus shared Python common builder for the full B1-B4 object",
            "pytorch": "uses package-backed tensor/graph/SMT probes plus shared Python common builder for the full B1-B4 object",
        },
        "source_import_audit": family_b_object["source_import_audit"],
        "parent_lineage": family_b_object["parent_lineage"],
        "layers": family_b_object["layers"],
        "weld_anchors": family_b_object["weld_anchors"],
        "kill_controls": family_b_object["kill_controls"],
        "TOOL_MANIFEST": common.TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": common.TOOL_INTEGRATION_DEPTH,
        "tool_intent": common.TOOL_INTENT,
        "trajectory_artifact": artifact,
        "claim_sections": family_b_object["claim_sections"],
        "allowed_claims": family_b_object["allowed_claims"],
        "disallowed_claims": family_b_object["disallowed_claims"],
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
            "/opt/homebrew/bin/julia --startup-file=no --project=/Users/joshuaeisenhart/Codex-Ratchet/system_v5/julia_carrier system_v6/sims/manifold_family_b_integrated_v0/manifold_family_b_integrated_v0_julia.jl",
            "/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/manifold_family_b_integrated_v0/manifold_family_b_integrated_v0_jax.py",
            "/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/manifold_family_b_integrated_v0/manifold_family_b_integrated_v0_pytorch.py",
            "/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/manifold_family_b_integrated_v0/write_envelope_spec.py",
            "/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/build_three_engine_envelope.py system_v6/sims/manifold_family_b_integrated_v0/manifold_family_b_integrated_v0_envelope_spec.json > system_v6/sims/manifold_family_b_integrated_v0/results/manifold_family_b_integrated_v0_envelope_results.json",
            "/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/manifold_family_b_integrated_v0/validate_manifold_family_b_integrated_v0.py",
            "/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py --require-pytorch --strict-source-backed --require-tool-intent system_v6/sims/manifold_family_b_integrated_v0/results/manifold_family_b_integrated_v0_envelope_results.json",
            "/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 -m pytest -q system_v6/sims/manifold_family_b_integrated_v0/tests",
        ],
    }
    rehomed_builder_fields = {
        key: extra.pop(key)
        for key in (
            "parent_lineage",
        )
        if key in extra
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
        "claim_path_tools": ["Graphs", "Z3", "networkx", "sympy", "z3", "cvc5", "torch.func", "torch_geometric"],
        "crossover_proofs": {
            "z3": family_b_object["crossover_proofs"]["z3"],
            "cvc5": family_b_object["crossover_proofs"]["cvc5"],
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
            "basis": "boolean all_pass agreement plus packet validator anchor equality; backend mode is honest shared-common scope",
        },
        "parent_lineage": {key: row["path"] for key, row in family_b_object["parent_lineage"]["consumed_inputs"].items()},
        "stability_pairs": [
            {"subtree": row["path"], "hash": row["sha256"]}
            for row in family_b_object["parent_lineage"]["consumed_inputs"].values()
            if row.get("sha256")
        ],
        **rehomed_builder_fields,
        "extra_fields": extra,
    }


def main() -> int:
    spec = build_spec()
    common.write_json(SPEC_PATH, spec)
    print(json.dumps({"ok": True, "spec_path": common.rel(SPEC_PATH)}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
