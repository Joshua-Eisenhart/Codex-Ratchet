#!/usr/bin/env python3
"""Write the three-engine envelope for gcm_nested_geometry_delta_3q_v0."""

from __future__ import annotations

import json

from gcm_nested_geometry_delta_3q_v0_common import (
    CLAIM_CEILING,
    CLASSIFICATION,
    ENVELOPE_PATH,
    ENVELOPE_SCHEMA,
    FORMAL_ADMISSION_ALLOWED,
    PROMOTION_ALLOWED,
    RESULT_DIR,
    RESULT_PATH,
    SIM_ID,
    TOOL_INTENT,
    engine_claim_values,
    load_json,
    rel,
    source_lock,
    stable_sha256,
    write_json,
)


JULIA_RESULT_PATH = RESULT_DIR / f"{SIM_ID}_julia_results.json"
JAX_RESULT_PATH = RESULT_DIR / f"{SIM_ID}_jax_results.json"
PYTORCH_RESULT_PATH = RESULT_DIR / f"{SIM_ID}_pytorch_results.json"


def engine_record(result: dict[str, object]) -> dict[str, object]:
    return {
        "ran": result["ran"],
        "source_path": result["source_path"],
        "source_sha256": source_lock(RESULT_PATH.parents[1] / str(result["source_path"]).split("/")[-1], "engine source").get("sha256"),
        "result_path": result["result_path"],
        "reads_peer_result": result["reads_peer_result"],
        "packages_used": result["packages_used"],
        "aligned_packages_load_bearing": result["aligned_packages_load_bearing"],
        "aligned_packages_supportive": result.get("aligned_packages_supportive", []),
        "engine_role": result.get("engine_role"),
        "claim_path_depth": result.get("claim_path_depth"),
        "engine_independence_ceiling": result.get("engine_independence_ceiling"),
        "package_observables": result["package_observables"],
    }


def normalize_claim_values(result: dict[str, object]) -> dict[str, int]:
    raw = result["claim_values"]
    assert isinstance(raw, dict)
    keys = (
        "main_delta_l1_scaled",
        "same_input_null_delta_l1_scaled",
        "same_input_stable_delta_l1_scaled",
        "alternate_pin_delta_l1_scaled",
        "alternate_probe_delta_l1_scaled",
        "main_free_count",
        "main_nested_count",
        "alternate_pin_nested_count",
    )
    return {key: int(raw[key]) for key in keys}


def max_divergence(values: dict[str, dict[str, int]]) -> int:
    max_div = 0
    keys = next(iter(values.values())).keys()
    for key in keys:
        observed = [int(row[key]) for row in values.values()]
        max_div = max(max_div, max(observed) - min(observed))
    return max_div


def main() -> int:
    main_result = load_json(RESULT_PATH)
    julia = load_json(JULIA_RESULT_PATH)
    jax = load_json(JAX_RESULT_PATH)
    pytorch = load_json(PYTORCH_RESULT_PATH)
    expected_values = engine_claim_values(main_result)
    engine_values = {
        "julia": normalize_claim_values(julia),
        "jax": normalize_claim_values(jax),
        "pytorch": normalize_claim_values(pytorch),
    }
    envelope = {
        "schema": ENVELOPE_SCHEMA,
        "schema_version": "three_engine_sim_result_v1",
        "sim_id": SIM_ID,
        "result_path": rel(RESULT_PATH),
        "result_sha256": stable_sha256(main_result),
        "classification": CLASSIFICATION,
        "claim_ceiling": CLAIM_CEILING,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "engine_contract": {
            "mode": main_result["engine_mode"],
            "lanes": ["julia", "python_packet", "jax", "pytorch"],
            "audit_order": ["combined_envelope", "python_packet", "julia_local", "jax_supportive", "pytorch_supportive"],
            "independence_ceiling": main_result["engine_role_ceiling"]["ceiling"],
        },
        "engine_role_ceiling": main_result["engine_role_ceiling"],
        "layer_declaration": main_result["layer_declaration"],
        "axis_declaration": main_result["axis_declaration"],
        "claim_path_tools": ["Graphs", "python_packet_geometry", "gcm_substrate_check", "gcm_nested_schema_check"],
        "engines": {
            "julia": engine_record(julia),
            "jax": engine_record(jax),
            "pytorch": engine_record(pytorch),
        },
        "crossover_proofs": main_result["crossover_proofs"],
        "divergence": {
            "julia_authoritative": True,
            "expected_values_from_main_packet": expected_values,
            "engine_values": engine_values,
            "max_divergence": max_divergence(engine_values),
        },
        "geometry_delta_from_free": main_result["geometry_delta_from_free"],
        "flip_control_runs": main_result["flip_control_runs"],
        "same_input_stability_control": main_result["same_input_stability_control"],
        "exact_relation_status": main_result["exact_relation_status"],
        "probe_relation_status": main_result["probe_relation_status"],
        "extension_fiber_size": main_result["extension_fiber_size"],
        "cut_state_available": main_result["cut_state_available"],
        "blocked_consumer_enforced": main_result["blocked_consumer_enforced"],
        "what_would_flip": main_result["what_would_flip"],
        "negative_control_status": main_result["negative_control_status"],
        "cross_pin_stability": main_result["cross_pin_stability"],
        "cross_probe_stability": main_result["cross_probe_stability"],
        "geometry_delta_stability_class": main_result["geometry_delta_stability_class"],
        "forward_transport_status": main_result["forward_transport_status"],
        "backward_admissibility_status": main_result["backward_admissibility_status"],
        "counts": main_result["counts"],
        "controls": main_result["controls"],
        "substrate_checks": main_result["substrate_checks"],
        "TOOL_MANIFEST": main_result["TOOL_MANIFEST"],
        "TOOL_INTEGRATION_DEPTH": main_result["TOOL_INTEGRATION_DEPTH"],
        "tool_intent": TOOL_INTENT,
        "build_boundary": main_result["build_boundary"],
        "divergence_log": main_result["classical_baseline"]["divergence_log"],
        "no_builder_audit_verdict": True,
    }
    write_json(ENVELOPE_PATH, envelope)
    print(json.dumps({"ok": True, "envelope_path": rel(ENVELOPE_PATH), "max_divergence": envelope["divergence"]["max_divergence"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
