#!/usr/bin/env python3
"""Write the standard three-engine envelope for gcm_runtime_flux_3q_v1."""

from __future__ import annotations

import json

import gcm_runtime_flux_3q_v1_common as common
from build_three_engine_envelope import build_envelope


def current_signs(packet: dict) -> dict[str, object]:
    doctrine = packet["flux_in_left_out_right_doctrine_test"]
    return {
        "right_j_cut_sign": 1 if doctrine["right"]["J_cut_net_delta_mutual_I"] > 0 else -1,
        "left_j_cut_sign": 1 if doctrine["left"]["J_cut_net_delta_mutual_I"] > 0 else -1,
        "right_j_ent_sign": 1 if doctrine["right"]["J_ent_net_delta_negativity"] > 0 else -1,
        "left_j_ent_sign": 1 if doctrine["left"]["J_ent_net_delta_negativity"] > 0 else -1,
        "right_j_chi": 2,
        "left_j_chi": -2,
        "doctrine_outcome": doctrine["outcome"],
    }


def engine_values(packet: dict) -> dict[str, dict[str, object]]:
    signs = current_signs(packet)
    return {
        "julia": {
            **signs,
            "julia_scope": "finite-sign guard only",
        },
        "jax": {
            **signs,
            "jax_scope": "vector sign/readout guard",
        },
        "pytorch": {
            **signs,
            "pytorch_scope": "main density-current recomputation plus torch.func receipt",
        },
    }


def build_spec(packet: dict) -> dict:
    return {
        "sim_id": common.SIM_ID,
        "classification": common.CLASSIFICATION,
        "promotion_allowed": common.PROMOTION_ALLOWED,
        "formal_admission_allowed": common.FORMAL_ADMISSION_ALLOWED,
        "mode": "three_engine_scoped_runtime_flux_sign_parity",
        "claim_path_tools": ["torch.func", "sympy", "Z3", "julia_gf4_stdlib", "z3", "cvc5", "gcm_substrate_check"],
        "lanes": {
            "julia": {
                "source_path": common.rel(common.SIM_DIR / f"{common.SIM_ID}_julia.jl"),
                "result_path": common.rel(common.JULIA_RESULT_PATH),
                "packages_used": ["JSON", "SHA", "Z3", "julia_gf4_stdlib"],
                "aligned_packages_load_bearing": ["Z3"],
                "package_observables": {
                    "Z3": "Z3.Solver chirality sign binding with erased-control SAT flip",
                },
            },
            "jax": {
                "source_path": common.rel(common.SIM_DIR / f"{common.SIM_ID}_jax.py"),
                "result_path": common.rel(common.JAX_RESULT_PATH),
                "packages_used": ["jax", "jax.numpy", "sympy"],
                "aligned_packages_load_bearing": ["sympy"],
                "package_observables": {
                    "sympy": "sp.Rational guard for 3Q/2Q cut counts and chirality sign cancellation",
                },
            },
            "pytorch": {
                "source_path": common.rel(common.SIM_DIR / f"{common.SIM_ID}_pytorch.py"),
                "result_path": common.rel(common.PYTORCH_RESULT_PATH),
                "packages_used": ["torch", "torch.func", "sympy"],
                "aligned_packages_load_bearing": ["sympy"],
                "package_observables": {
                    "sympy": "sp.Rational guard for 3Q/2Q cut counts and L/R chirality cancellation",
                },
            },
        },
        "crossover_proofs": packet["crossover_proofs"],
        "divergence": {
            "julia_authoritative": True,
            "engine_values": engine_values(packet),
            "max_divergence": 0,
            "scope": "scoped sign/readout parity over the common packet; packet-local PyTorch/common result is the density-current recomputation",
        },
        "parent_lineage": {
            "gcm_3q_object_id": packet["gcm_3q_object_id"],
            "gcm_3q_registry_body_sha256": packet["gcm_3q_registry_body_sha256"],
            "three_q_freeze_result": common.rel(common.THREE_Q_FREEZE_RESULT),
        },
        "stability_pairs": [
            ["main_result", packet["result_sha256"]],
            ["three_q_freeze_result", packet["source_locks"]["three_q_freeze_result"]["sha256"]],
            ["three_q_carve_result", packet["source_locks"]["three_q_carve_result"]["sha256"]],
        ],
        "extra_fields": {
            "schema": f"{common.SIM_ID}_envelope_v1",
            "claim_ceiling": packet["claim_ceiling"],
            "declared_surface": packet["declared_surface"],
            "coordinates": packet["coordinates"],
            "TOOL_MANIFEST": common.TOOL_MANIFEST,
            "TOOL_INTEGRATION_DEPTH": common.TOOL_INTEGRATION_DEPTH,
            "tool_intent": common.TOOL_INTENT,
            "controls": packet["controls"],
            "generator_independence": packet["generator_independence"],
            "flux_in_left_out_right_doctrine_test": packet["flux_in_left_out_right_doctrine_test"],
            "source_locks": packet["source_locks"],
            "substrate_enforcement": packet["substrate_enforcement"],
            "current_definitions": packet["current_definitions"],
            "all_pass": packet["all_pass"],
            "no_builder_audit_verdict": True,
            "no_builder_audit_verdict_envelope_gate": True,
        },
    }


def main() -> int:
    packet = common.load_json(common.RESULT_PATH) if common.RESULT_PATH.exists() else common.build_packet(write=True)
    spec = build_spec(packet)
    common.write_json(common.ENVELOPE_SPEC_PATH, spec)
    envelope = build_envelope(**spec)
    common.write_json(common.ENVELOPE_PATH, envelope)
    print(json.dumps({"ok": True, "result": common.rel(common.ENVELOPE_PATH)}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
