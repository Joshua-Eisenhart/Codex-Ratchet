#!/usr/bin/env python3
"""Packet validator for manifold_family_b_integrated_v0."""

from __future__ import annotations

import json
import math
from typing import Any

import manifold_family_b_integrated_v0_common as common


ENVELOPE = common.RESULT_DIR / f"{common.SIM_ID}_envelope_results.json"
VALIDATOR_RESULT = common.RESULT_DIR / f"{common.SIM_ID}_validator_results.json"

EXPECTED_PARENT_CAVEATS = {
    "ratchet_deep_chain_v0:G1_COMPOSITE_GROUP_NOT_EARNED",
    "ratchet_deep_chain_v0:G2_SECOND_Z2_ACTION_UNSPECIFIED",
    "compression_flow_radiated_record_v0:F1_REGISTER_BASIS_SEMANTICS_UNDERPINNED",
    "compression_flow_radiated_record_v0:F2_SMT_ROW_SET_NOT_PAYLOAD_HASH_PROOF",
    "z4_syndrome_record_v0:CAVEAT_JULIA_RECORD_COUNTS_LITERAL",
    "z4_syndrome_record_v0:CAVEAT_SMT_BINDS_COEFFICIENTS_NOT_RAW_TABLES",
    "manifold_entropy_ledger_v0:CAVEAT_SIGNED_LENS_DELTA_LABEL",
    "manifold_unified_run_v0:CAVEAT_Q4_PARENT_RIGIDITY",
}


def require(errors: list[str], condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


def has_key_prefix(value: Any, prefix: str) -> bool:
    if isinstance(value, dict):
        return any(str(key).startswith(prefix) or has_key_prefix(item, prefix) for key, item in value.items())
    if isinstance(value, list):
        return any(has_key_prefix(item, prefix) for item in value)
    return False


def load_lane(engine: str) -> dict[str, Any]:
    return common.load_json(common.RESULT_DIR / f"{common.SIM_ID}_{engine}_results.json")


def validate_hash_lock_surfaces(errors: list[str], payload: dict[str, Any]) -> None:
    source_audit = payload.get("source_import_audit", {})
    pins = source_audit.get("parent_hash_pins", {})
    require(errors, isinstance(pins, dict) and bool(pins), "parent_hash_pins must be a non-empty mapping")
    for key, row in pins.items():
        path = str(row.get("path", ""))
        require(errors, path.endswith(".json"), f"parent_hash_pins.{key} must point at JSON")
        require(errors, "/results/" in path or path.startswith("system_v6/sims/") and "/results/" in f"/{path}", f"parent_hash_pins.{key} must be a result surface")
        require(errors, "audit_verdict" not in path, f"parent_hash_pins.{key} must not lock audit verdicts")
        require(errors, bool(row.get("sha256")), f"parent_hash_pins.{key} missing sha256")
    context = source_audit.get("audit_verdict_citation_context_hashes", {})
    require(errors, isinstance(context, dict) and bool(context), "audit verdict locks must be separate citation context")
    for key, row in context.items():
        path = str(row.get("path", ""))
        require(errors, path.endswith("audit_verdict.md"), f"audit verdict citation context path unexpected for {key}")


def validate_layers(errors: list[str], layers: dict[str, Any]) -> None:
    expected_layers = ["B1_RATCHET_CHAIN", "B2_COMPRESSION_RECORD", "B3_CONSERVATION_ACCOUNTS", "B4_TYPED_LEDGER"]
    require(errors, sorted(layers) == expected_layers, "layer map must contain B1-B4 only")
    b1_pin = layers.get("B1_RATCHET_CHAIN", {}).get("pinned_ratchet_row_ledger", {})
    require(errors, b1_pin.get("source_json_pointer") == "/ratchet_sequence/per_step_ledger/rows", "B1 must consume ratchet parent row ledger")
    require(errors, bool(b1_pin.get("pin_block_sha256")), "B1 pin block missing sha")
    require(errors, len(b1_pin.get("derived_pin_rows", [])) == 7, "B1 pin block must derive seven parent rows")
    require(errors, not has_key_prefix(layers.get("B2_COMPRESSION_RECORD", {}), "axis0_"), "B2 emitted an axis0_* field")
    b3_citation = common.rel(common.PARENT_RESULTS["z4_syndrome_record_v0"])
    for layer_name, layer in layers.items():
        require(errors, bool(layer.get("row_signature_sha256")), f"{layer_name} missing row signature")
        for row in layer.get("reduced_rows", []):
            caveats = set(row.get("parent_caveats", []))
            require(errors, EXPECTED_PARENT_CAVEATS <= caveats, f"{layer_name}.{row.get('row_id')} did not preserve expected caveats")
            require(errors, row.get("claim_ceiling") == common.CLASSIFICATION, f"{layer_name}.{row.get('row_id')} wrong claim ceiling")
            require(errors, row.get("row_step_class") in {"STEP_DEPENDENT", "CARRIED"}, f"{layer_name}.{row.get('row_id')} missing trajectory row class")
            if layer_name == "B3_CONSERVATION_ACCOUNTS":
                require(errors, row.get("co_citation") == b3_citation, f"{row.get('row_id')} missing row-local z4 co-citation")
                require(
                    errors,
                    row.get("state_plus_record_convention_label") == "finite_counting_state_plus_record",
                    f"{row.get('row_id')} missing state-plus-record convention label",
                )
    ledger = layers.get("B4_TYPED_LEDGER", {}).get("typed_consistency_matrix", {})
    require(errors, ledger.get("all_rows_typed") is True, "typed ledger rows must be typed")
    require(errors, ledger.get("forbidden_cross_type_sum_found") is False, "typed ledger detected forbidden cross-type sum")
    require(errors, ledger.get("signed_lens_delta_label_caveat_carried") is True, "signed lens delta caveat not carried")


def validate_anchors(errors: list[str], anchors: dict[str, Any]) -> None:
    deep = anchors.get("deep_chain", {})
    require(errors, deep.get("pass") is True, "deep-chain anchor failed")
    require(errors, deep.get("final_denominator") == 16, "deep-chain denominator mismatch")
    require(errors, deep.get("final_volume_exact") == "pi**2/4", "deep-chain exact volume mismatch")
    require(errors, math.isclose(deep.get("final_volume_float", -1.0), math.pi**2 / 4.0, abs_tol=1.0e-15), "deep-chain float volume mismatch")
    require(errors, deep.get("entropy_deltas_exact") == ["-log(4)", "-log(2)", "-log(2)"], "deep-chain entropy delta mismatch")
    require(errors, deep.get("composite_order") == 8, "deep-chain composite order mismatch")

    compression = anchors.get("compression_flow", {})
    require(errors, compression.get("pass") is True, "compression-flow anchor failed")
    require(errors, compression.get("initial_size") == 384, "compression initial size mismatch")
    require(errors, compression.get("total_emitted_rows") == 288, "compression emitted count mismatch")
    require(errors, compression.get("P_T_size") == 96, "compression survivor count mismatch")
    require(errors, compression.get("max_conservation_defect") == 0, "compression conservation defect nonzero")
    require(errors, compression.get("computed_hash_chain_heads") == compression.get("expected_hash_chain_heads"), "compression hash-chain heads mismatch parent")

    conservation = anchors.get("conservation", {})
    require(errors, conservation.get("pass") is True, "conservation anchor failed")
    require(errors, math.isclose(conservation.get("state_loss_nats", -1.0), math.log(4), abs_tol=1.0e-15), "conservation loss mismatch")
    require(errors, math.isclose(conservation.get("record_retained_nats", -1.0), math.log(4), abs_tol=1.0e-15), "conservation record mismatch")
    require(errors, math.isclose(conservation.get("defect_nats", -1.0), 0.0, abs_tol=1.0e-15), "conservation defect mismatch")

    smt = anchors.get("SMT_rows", {})
    require(errors, bool(smt), "SMT rows missing")
    for name, row in smt.items():
        require(errors, row.get("ran") is True and row.get("load_bearing") is True, f"{name} did not run load-bearing")
        require(errors, row.get("verdict") == "unsat", f"{name} identity must be UNSAT")
        require(errors, row.get("erased_flip_verdict") == "sat", f"{name} erased/perturbed flip must be SAT")
        require(errors, row.get("asserted_precomputed_boolean") is False, f"{name} must bind computed values, not booleans")


def validate_controls(errors: list[str], controls: dict[str, Any]) -> None:
    for key in ["stale_import_control", "order_shuffled_N01", "erased_record", "quotient_erased", "similarity_only_root_off_guard"]:
        require(errors, controls.get(key, {}).get("fires") is True, f"{key} did not fire")
    decorative = controls.get("decorative_layer_detector", {})
    require(errors, sorted(decorative) == ["B1_RATCHET_CHAIN", "B2_COMPRESSION_RECORD", "B3_CONSERVATION_ACCOUNTS", "B4_TYPED_LEDGER"], "decorative detector coverage mismatch")
    for key, row in decorative.items():
        require(errors, row.get("fires") is True, f"decorative detector failed for {key}")
        require(errors, row.get("baseline_row_signature") != row.get("perturbed_row_signature"), f"decorative detector did not change signature for {key}")
    stale = controls.get("stale_import_control", {})
    require(
        errors,
        stale.get("pin_mutation_surface") == "B1.pinned_ratchet_row_ledger.derived_pin_rows[1].factor",
        "stale-import control must mutate the B1 pin path directly",
    )
    require(errors, stale.get("baseline_b1_pin_block_sha256") != stale.get("mutated_b1_pin_block_sha256"), "B1 pin mutation did not change pin block sha")


def validate_trajectory(errors: list[str], payload: dict[str, Any]) -> None:
    artifact = payload.get("trajectory_artifact", {})
    artifact_path = common.ROOT / artifact.get("path", "")
    sha_path = common.ROOT / artifact.get("sha_path", "")
    require(errors, artifact.get("sha_verified") is True, "trajectory artifact was not sha verified")
    require(errors, artifact_path.exists(), "trajectory artifact file missing")
    require(errors, sha_path.exists(), "trajectory artifact sha sidecar missing")
    if artifact_path.exists() and sha_path.exists():
        stored_payload = common.load_json(artifact_path)
        content_digest = common.content_sha256_without_self(stored_payload)
        file_digest = common.sha256_file(artifact_path)
        sidecar = sha_path.read_text(encoding="utf-8").split()[0]
        require(errors, content_digest == stored_payload.get("content_sha256") == artifact.get("content_sha256"), "trajectory artifact content sha mismatch")
        require(errors, file_digest == sidecar == artifact.get("artifact_file_sha256"), "trajectory artifact file sha mismatch")
        state_ids = {row.get("state_object_id") for row in stored_payload.get("step_rows", [])}
        classes = {row.get("row_step_class") for row in stored_payload.get("step_rows", [])}
        require(errors, state_ids == {payload.get("state_object_id")}, "trajectory artifact must use one state_object_id")
        require(errors, {"STEP_DEPENDENT", "CARRIED"} <= classes, "trajectory artifact needs step-dependent and carried rows")
        require(errors, all(row.get("sha_verified") is True for row in stored_payload.get("step_rows", [])), "trajectory row sha verification failed")
        for row in stored_payload.get("step_rows", []):
            require(errors, bool(row.get("trajectory_step_id")), "trajectory row missing trajectory_step_id")
            require(errors, bool(row.get("row_step_lineage_id")), "trajectory row missing row_step_lineage_id")
            require(errors, bool(row.get("row_step_class_why")), "trajectory row missing row_step_class_why")


def validate_payload(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    family_b_object = common.build_family_b_object()
    require(errors, payload.get("schema_version") == "three_engine_sim_result_v1", "schema_version mismatch")
    require(errors, payload.get("sim_id") == common.SIM_ID, "sim_id mismatch")
    require(errors, payload.get("mode") == common.ENGINE_MODE, "engine mode must be honest shared-common scope")
    require(errors, payload.get("classification") == common.CLASSIFICATION, "classification must be scratch_diagnostic")
    require(errors, payload.get("promotion_allowed") is False, "promotion_allowed must be false")
    require(errors, payload.get("formal_admission_allowed") is False, "formal_admission_allowed must be false")
    require(errors, payload.get("all_pass") is True, "top-level all_pass must be true")
    require(errors, payload.get("state_object_id") == family_b_object["state_object_id"], "state_object_id mismatch")
    require(errors, payload.get("family_a_rows_used") is False, "Family A rows are fenced out")
    require(errors, payload.get("two_engine_rows_used") is False, "two-engine rows are fenced out")
    substrate = payload.get("substrate", {})
    require(errors, substrate.get("final_denominator") == 16, "substrate denominator mismatch")
    require(errors, substrate.get("mct_carrier_row_count") == 384, "substrate MCT row count mismatch")
    require(errors, payload.get("source_import_audit", {}).get("raw_parent_computation_imported") is False, "raw parent computation must not be imported")

    validate_hash_lock_surfaces(errors, payload)
    validate_layers(errors, payload.get("layers", {}))
    validate_anchors(errors, payload.get("weld_anchors", {}))
    validate_controls(errors, payload.get("kill_controls", {}))
    validate_trajectory(errors, payload)

    require(errors, family_b_object["all_pass"] is True, f"fresh Family B object failed: {family_b_object['failures']}")
    expected_tools = {"Graphs", "Z3", "networkx", "torch.func", "torch_geometric", "sympy", "z3", "cvc5"}
    require(errors, expected_tools <= set(payload.get("claim_path_tools", [])), "claim path tools missing expected package-backed tools")
    require(errors, payload.get("TOOL_MANIFEST") == common.TOOL_MANIFEST, "TOOL_MANIFEST mismatch")
    require(errors, payload.get("TOOL_INTEGRATION_DEPTH") == common.TOOL_INTEGRATION_DEPTH, "TOOL_INTEGRATION_DEPTH mismatch")
    require(errors, payload.get("tool_intent") == common.TOOL_INTENT, "tool_intent mismatch")
    for section in ["positive", "negative", "boundary"]:
        require(errors, bool(payload.get("claim_sections", {}).get(section)), f"claim_sections.{section} missing")
    for engine in ["julia", "jax", "pytorch"]:
        lane = load_lane(engine)
        require(errors, lane.get("all_pass") is True, f"{engine} lane all_pass false")
        require(errors, payload.get("engines", {}).get(engine, {}).get("result_all_pass") is True, f"{engine} envelope result_all_pass false")
        require(errors, payload.get("engines", {}).get(engine, {}).get("reads_peer_result") is False, f"{engine} reads_peer_result must be false")
    return errors


def main() -> int:
    payload = common.load_json(ENVELOPE)
    errors = validate_payload(payload)
    result = {
        "ok": not errors,
        "result_json": common.rel(ENVELOPE),
        "errors": errors,
    }
    common.write_json(VALIDATOR_RESULT, result)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
