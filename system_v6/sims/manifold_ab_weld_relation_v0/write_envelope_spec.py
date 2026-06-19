#!/usr/bin/env python3
"""Write the build_three_engine_envelope.py spec for manifold_ab_weld_relation_v0."""

from __future__ import annotations

import json
from typing import Any

import manifold_ab_weld_relation_v0_common as common


SPEC_PATH = common.SIM_DIR / f"{common.SIM_ID}_envelope_spec.json"
ENVELOPE_PATH = common.RESULT_DIR / f"{common.SIM_ID}_envelope_results.json"
CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
TOOL_MANIFEST = {
    "build_three_engine_envelope": {
        "tried": True,
        "used": True,
        "reason": "standard three-engine envelope helper for this packet",
    },
}
TOOL_INTEGRATION_DEPTH = {
    "build_three_engine_envelope": "load_bearing",
}


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
    relation_object = common.build_relation_object()
    artifact = common.write_trajectory_artifact(relation_object)
    julia = load_lane("julia")
    jax = load_lane("jax")
    pytorch = load_lane("pytorch")
    all_lanes_pass = julia["all_pass"] and jax["all_pass"] and pytorch["all_pass"]
    all_pass = relation_object["all_pass"] and all_lanes_pass and artifact["sha_verified"]
    extra_fields: dict[str, Any] = {
        "schema": f"{common.SIM_ID}.envelope.v1",
        "source_path": common.rel(common.SIM_DIR / "write_envelope_spec.py"),
        "source_sha256": common.sha256_file(common.SIM_DIR / "write_envelope_spec.py"),
        "result_path": common.rel(ENVELOPE_PATH),
        "all_pass": all_pass,
        "state_object_id": relation_object["state_object_id"],
        "source_import_audit": relation_object["source_import_audit"],
        "pinned_state_objects": relation_object["pinned_state_objects"],
        "parent_anchor_checks": relation_object["parent_anchor_checks"],
        "coordinate_map": relation_object["coordinate_map"],
        "coordinate_map_signature_sha256": relation_object["coordinate_map_signature_sha256"],
        "weld_only_rows": relation_object["weld_only_rows"],
        "weld_only_rows_signature_sha256": relation_object["weld_only_rows_signature_sha256"],
        "nonrecoverability_table": relation_object["nonrecoverability_table"],
        "nonrecoverability_signature_sha256": relation_object["nonrecoverability_signature_sha256"],
        "cross_family_controls": relation_object["cross_family_controls"],
        "weld_relation_smt": relation_object["weld_relation_smt"],
        "family_c_fence": relation_object["family_c_fence"],
        "trajectory_artifact": artifact,
        "backend_contract_decision": relation_object["backend_contract_decision"],
        "TOOL_MANIFEST": common.TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": common.TOOL_INTEGRATION_DEPTH,
        "TOOL_INTENT_MATRIX": relation_object["TOOL_INTENT_MATRIX"],
        "tool_intent": common.TOOL_INTENT,
        "builder_gates": relation_object["builder_gates"],
        "no_builder_audit_verdict": relation_object["builder_gates"]["no_builder_audit_verdict"],
        "no_builder_audit_verdict_envelope_gate": relation_object["builder_gates"]["no_builder_audit_verdict_envelope_gate"],
        "builder_surface_no_audit_verdict": relation_object["builder_gates"]["builder_surface_no_audit_verdict"],
        "envelope_built_with_helper": True,
        "build_helper_path": "scripts/build_three_engine_envelope.py",
        "claim_sections": relation_object["claim_sections"],
        "allowed_claims": relation_object["allowed_claims"],
        "disallowed_claims": relation_object["disallowed_claims"],
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
            "JULIA_LOAD_PATH=@:@stdlib /opt/homebrew/bin/julia --startup-file=no --project=/Users/joshuaeisenhart/Codex-Ratchet/system_v5/julia_carrier system_v6/sims/manifold_ab_weld_relation_v0/manifold_ab_weld_relation_v0_julia.jl",
            "/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/manifold_ab_weld_relation_v0/manifold_ab_weld_relation_v0_jax.py",
            "/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/manifold_ab_weld_relation_v0/manifold_ab_weld_relation_v0_pytorch.py",
            "/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/manifold_ab_weld_relation_v0/write_envelope_spec.py",
            "/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/build_three_engine_envelope.py system_v6/sims/manifold_ab_weld_relation_v0/manifold_ab_weld_relation_v0_envelope_spec.json > system_v6/sims/manifold_ab_weld_relation_v0/results/manifold_ab_weld_relation_v0_envelope_results.json",
            "/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py --require-pytorch --strict-source-backed --require-tool-intent system_v6/sims/manifold_ab_weld_relation_v0/results/manifold_ab_weld_relation_v0_envelope_results.json",
            "/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/manifold_ab_weld_relation_v0/validate_manifold_ab_weld_relation_v0.py",
            "PYTHONDONTWRITEBYTECODE=1 /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 -m pytest -q -p no:cacheprovider system_v6/sims/manifold_ab_weld_relation_v0/tests",
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
            "z3": relation_object["weld_relation_smt"]["z3_weld_relation_sum"],
            "cvc5": relation_object["weld_relation_smt"]["cvc5_weld_relation_sum"],
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
            "basis": "boolean all_pass agreement plus exact A=3, B=8, W=11 relation witness across lanes",
        },
        "parent_lineage": {
            "family_a_envelope": common.SOURCE_PINS["family_a_envelope"]["path"],
            "family_b_envelope": common.SOURCE_PINS["family_b_envelope"]["path"],
            "v2_weld_context": common.SOURCE_PINS["v2_weld_envelope"]["path"],
            "family_c_fence": common.SOURCE_PINS["family_c_envelope"]["path"],
        },
        "stability_pairs": [
            {
                "subtree": "pinned_state_objects.A.anchor_values",
                "hash": relation_object["parent_anchor_checks"]["family_a_anchor_signature"],
            },
            {
                "subtree": "pinned_state_objects.B.anchor_values",
                "hash": relation_object["parent_anchor_checks"]["family_b_anchor_signature"],
            },
            {
                "subtree": "coordinate_map",
                "hash": relation_object["coordinate_map_signature_sha256"],
            },
            {
                "subtree": "weld_only_rows",
                "hash": relation_object["weld_only_rows_signature_sha256"],
            },
            {
                "subtree": "nonrecoverability_table",
                "hash": relation_object["nonrecoverability_signature_sha256"],
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
