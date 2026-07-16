#!/usr/bin/env python3
"""Write the build_three_engine_envelope.py spec for manifold_super_sim_v2_weld."""

from __future__ import annotations

import json
from typing import Any

import manifold_super_sim_v2_weld_common as common


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
    weld_object = common.build_weld_object()
    artifact = common.write_trajectory_artifact(weld_object)
    julia = load_lane("julia")
    jax = load_lane("jax")
    pytorch = load_lane("pytorch")
    all_lanes_pass = julia["all_pass"] and jax["all_pass"] and pytorch["all_pass"]
    extra_fields: dict[str, Any] = {
        "schema": f"{common.SIM_ID}.envelope.v1",
        "source_path": common.rel(common.SIM_DIR / "write_envelope_spec.py"),
        "source_sha256": common.sha256_file(common.SIM_DIR / "write_envelope_spec.py"),
        "result_path": common.rel(ENVELOPE_PATH),
        "all_pass": weld_object["all_pass"] and all_lanes_pass and artifact["sha_verified"],
        "state_object_id": weld_object["state_object_id"],
        "family_state_objects": weld_object["family_state_objects"],
        "source_import_audit": weld_object["source_import_audit"],
        "parent_anchor_checks": weld_object["parent_anchor_checks"],
        "declared_weld_map": weld_object["declared_weld_map"],
        "weld_row_table": weld_object["weld_row_table"],
        "cross_family_controls": weld_object["cross_family_controls"],
        "weld_smt_rows": weld_object["weld_smt_rows"],
        "trajectory_artifact": artifact,
        "backend_contract_decision": weld_object["backend_contract_decision"],
        "TOOL_MANIFEST": common.TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": common.TOOL_INTEGRATION_DEPTH,
        "TOOL_INTENT_MATRIX": weld_object["TOOL_INTENT_MATRIX"],
        "tool_intent": common.TOOL_INTENT,
        "builder_gates": weld_object["builder_gates"],
        "no_builder_audit_verdict": weld_object["builder_gates"]["no_builder_audit_verdict"],
        "no_builder_audit_verdict_envelope_gate": weld_object["builder_gates"]["no_builder_audit_verdict_envelope_gate"],
        "envelope_built_with_helper": True,
        "build_helper_path": "scripts/build_three_engine_envelope.py",
        "claim_sections": weld_object["claim_sections"],
        "allowed_claims": weld_object["allowed_claims"],
        "disallowed_claims": weld_object["disallowed_claims"],
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
            "/opt/homebrew/bin/julia --startup-file=no --project=/Users/joshuaeisenhart/Codex-Ratchet/system_v5/julia_carrier system_v6/sims/manifold_super_sim_v2_weld/manifold_super_sim_v2_weld_julia.jl",
            "/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/manifold_super_sim_v2_weld/manifold_super_sim_v2_weld_jax.py",
            "/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/manifold_super_sim_v2_weld/manifold_super_sim_v2_weld_pytorch.py",
            "/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/manifold_super_sim_v2_weld/write_envelope_spec.py",
            "/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/build_three_engine_envelope.py system_v6/sims/manifold_super_sim_v2_weld/manifold_super_sim_v2_weld_envelope_spec.json > system_v6/sims/manifold_super_sim_v2_weld/results/manifold_super_sim_v2_weld_envelope_results.json",
            "/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/manifold_super_sim_v2_weld/validate_manifold_super_sim_v2_weld.py",
            "/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py --require-pytorch --strict-source-backed --require-tool-intent system_v6/sims/manifold_super_sim_v2_weld/results/manifold_super_sim_v2_weld_envelope_results.json",
            "/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 -m pytest -q system_v6/sims/manifold_super_sim_v2_weld/tests",
        ],
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
            "z3": weld_object["weld_smt_rows"]["z3_weld_relation"],
            "cvc5": weld_object["weld_smt_rows"]["cvc5_weld_relation"],
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
            "basis": "boolean lane all_pass agreement plus v2 packet validator anchor equality; full-object backend mode is honest shared-common scope",
        },
        "parent_lineage": {
            key: row["path"]
            for key, row in weld_object["source_import_audit"]["parent_hash_pins"].items()
        },
        "stability_pairs": [
            {
                "subtree": "family_state_objects.A.anchor_values",
                "hash": weld_object["parent_anchor_checks"]["family_a_recomputed_anchor_signature"],
            },
            {
                "subtree": "family_state_objects.B.anchor_values",
                "hash": weld_object["parent_anchor_checks"]["family_b_recomputed_anchor_signature"],
            },
            {
                "subtree": "declared_weld_map",
                "hash": common.stable_sha256(weld_object["declared_weld_map"]),
            },
            {
                "subtree": "weld_row_table",
                "hash": common.signature_rows(weld_object["weld_row_table"]),
            },
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
