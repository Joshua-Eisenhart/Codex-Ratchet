#!/usr/bin/env python3
"""Write the build_three_engine_envelope.py spec for manifold_family_c_integrated_v0."""

from __future__ import annotations

import json
from typing import Any

import manifold_family_c_integrated_v0_common as common


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
    family_c = common.build_family_c_object()
    artifact = common.write_trajectory_artifact(family_c)
    julia = load_lane("julia")
    jax = load_lane("jax")
    pytorch = load_lane("pytorch")
    all_lanes_pass = julia["all_pass"] and jax["all_pass"] and pytorch["all_pass"]
    extra = {
        "all_pass": family_c["all_pass"] and all_lanes_pass and artifact["sha_verified"],
        "ceiling": common.CLASSIFICATION,
        "state_object_id": family_c["integrated_state_object"]["state_object_id"],
        "family": family_c["family"],
        "live_rungs": family_c["live_rungs"],
        "n5_behavior_continuation_claimed": family_c["n5_behavior_continuation_claimed"],
        "behavior_class_growth_claimed": family_c["behavior_class_growth_claimed"],
        "raw_stage_lifted_rows_used": family_c["raw_stage_lifted_rows_used"],
        "shell_support_consumption": family_c["shell_support_consumption"],
        "floor_anchor": family_c["floor_anchor"],
        "boundary_stress_context": family_c["boundary_stress_context"],
        "integrated_state_object": family_c["integrated_state_object"],
        "source_import_audit": family_c["source_import_audit"],
        "surviving_mechanics": family_c["surviving_mechanics"],
        "integration_controls": family_c["integration_controls"],
        "unified_run_consistency_matrix": family_c["unified_run_consistency_matrix"],
        "trajectory_artifact": artifact,
        "TOOL_MANIFEST": common.TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": common.TOOL_INTEGRATION_DEPTH,
        "tool_intent": common.TOOL_INTENT,
        "allowed_claims": family_c["allowed_claims"],
        "disallowed_claims": family_c["disallowed_claims"],
        "out_of_scope": family_c["out_of_scope"],
        "carried_boundaries": family_c["carried_boundaries"],
        "no_builder_audit_verdict": True,
        "packet_audit_verdict_absent": True,
        "file_disjoint_packet": True,
        "engine_scope_notes": {
            "julia": "independently recomputes finite n3/n4 rung graph and live-rung count identity with Graphs/Z3",
            "jax": "uses package-backed graph/exact/SMT probes plus common Family C object builder",
            "pytorch": "uses torch.func/torch_geometric/SMT probes plus common Family C object builder",
        },
        "validator_expected_commands": [
            "/opt/homebrew/bin/julia --startup-file=no --project=/Users/joshuaeisenhart/Codex-Ratchet/system_v5/julia_carrier system_v6/sims/manifold_family_c_integrated_v0/manifold_family_c_integrated_v0_julia.jl",
            "/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/manifold_family_c_integrated_v0/manifold_family_c_integrated_v0_jax.py",
            "/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/manifold_family_c_integrated_v0/manifold_family_c_integrated_v0_pytorch.py",
            "/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/manifold_family_c_integrated_v0/write_envelope_spec.py",
            "/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/build_three_engine_envelope.py system_v6/sims/manifold_family_c_integrated_v0/manifold_family_c_integrated_v0_envelope_spec.json > system_v6/sims/manifold_family_c_integrated_v0/results/manifold_family_c_integrated_v0_envelope_results.json",
            "/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/manifold_family_c_integrated_v0/validate_manifold_family_c_integrated_v0.py",
            "/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py --require-pytorch --strict-source-backed --require-tool-intent system_v6/sims/manifold_family_c_integrated_v0/results/manifold_family_c_integrated_v0_envelope_results.json",
            "/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 -m pytest -q system_v6/sims/manifold_family_c_integrated_v0/tests",
        ],
    }
    return {
        "sim_id": common.SIM_ID,
        "mode": common.ENGINE_MODE,
        "classification": common.CLASSIFICATION,
        "promotion_allowed": common.PROMOTION_ALLOWED,
        "formal_admission_allowed": common.FORMAL_ADMISSION_ALLOWED,
        "expected_lanes": ["julia", "jax", "pytorch"],
        "lanes": {"julia": lane_spec("julia"), "jax": lane_spec("jax"), "pytorch": lane_spec("pytorch")},
        "claim_path_tools": ["Graphs", "Z3", "networkx", "sympy", "z3", "cvc5", "torch.func", "torch_geometric"],
        "crossover_proofs": {
            "z3": family_c["crossover_proofs"]["z3"],
            "cvc5": family_c["crossover_proofs"]["cvc5"],
            "julia_z3": julia["crossover_proofs"]["julia_z3"],
        },
        "divergence": {
            "julia_authoritative": True,
            "engine_values": {"julia": 1.0 if julia["all_pass"] else 0.0, "jax": 1.0 if jax["all_pass"] else 0.0, "pytorch": 1.0 if pytorch["all_pass"] else 0.0},
            "max_divergence": 0.0 if all_lanes_pass else 1.0,
            "tolerance": 0.0,
            "basis": "boolean all_pass agreement plus packet-local validator; all three lanes source-backed but only scratch diagnostic",
        },
        "parent_lineage": {key: row["path"] for key, row in family_c["source_import_audit"]["parent_hash_pins"].items()},
        "stability_pairs": [
            {"subtree": row["path"], "hash": row["sha256"]}
            for row in family_c["source_import_audit"]["parent_hash_pins"].values()
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
