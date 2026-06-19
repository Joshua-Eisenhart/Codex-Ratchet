#!/usr/bin/env python3
"""Packet validator for manifold_super_sim_v0."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

import manifold_super_sim_v0_common as common


ENVELOPE = common.RESULT_DIR / f"{common.SIM_ID}_envelope_results.json"
VALIDATOR_RESULT = common.RESULT_DIR / f"{common.SIM_ID}_validator_results.json"


def require(errors: list[str], condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


def load_lane(engine: str) -> dict[str, Any]:
    return common.load_json(common.RESULT_DIR / f"{common.SIM_ID}_{engine}_results.json")


def validate_payload(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    super_object = common.build_super_object(common.scipy_expm)
    require(errors, payload.get("schema_version") == "three_engine_sim_result_v1", "schema_version mismatch")
    require(errors, payload.get("sim_id") == common.SIM_ID, "sim_id mismatch")
    require(errors, payload.get("classification") == common.CLASSIFICATION, "classification must be scratch_diagnostic")
    require(errors, payload.get("promotion_allowed") is False, "promotion_allowed must be false")
    require(errors, payload.get("formal_admission_allowed") is False, "formal_admission_allowed must be false")
    require(errors, payload.get("all_pass") is True, "top-level all_pass must be true")
    require(errors, payload.get("state_object_id") == super_object["state_object_id"], "state_object_id mismatch")
    require(errors, payload.get("substrate", {}).get("state_count") == 33, "substrate state_count must be 33")
    require(errors, payload.get("substrate", {}).get("raw_transition_graphs_persisted") is False, "raw transition graphs must not be persisted")
    require(errors, payload.get("source_import_audit", {}).get("stale_imports") == [], "stale imports must be empty")
    require(errors, payload.get("source_import_audit", {}).get("raw_transition_graphs_imported") is False, "raw graphs must not be imported")

    anchors = payload.get("weld_anchors", {})
    require(errors, anchors.get("G0_transition_graph_sha256", {}).get("computed") == common.EXPECTED_G0_SHA, "G0 SHA anchor mismatch")
    require(errors, anchors.get("G1_partition", {}).get("terminal_class_sizes") == [1, 14, 18], "G1 partition mismatch")
    require(errors, anchors.get("G1_partition", {}).get("may_equals_must") is True, "G1 may/must mismatch")
    require(errors, anchors.get("rotated_chart", {}).get("rotated_terminal_class_count") == 2, "rotated chart terminal count mismatch")
    require(errors, anchors.get("rotated_chart", {}).get("refined_terminal_counts") == {"2x": 3, "3x": 3}, "refinement persistence mismatch")
    require(errors, math.isclose(anchors.get("D_z_information", {}).get("holevo_nats", -1), common.EXPECTED_DZ_HOLEVO, abs_tol=1.0e-15), "D_z Holevo mismatch")
    require(errors, math.isclose(anchors.get("D_z_information", {}).get("killed_nats", -1), common.EXPECTED_DZ_KILLED, abs_tol=1.0e-15), "D_z killed mismatch")
    require(errors, math.isclose(anchors.get("stage_word_endpoint", {}).get("word_output_information_nats", -1), common.EXPECTED_STAGE_ENDPOINT, abs_tol=1.0e-15), "stage endpoint mismatch")
    require(errors, all(row.get("pass") is True for row in anchors.values()), "not every weld anchor passed")

    controls = payload.get("kill_controls", {})
    for key in ["stale_import_control", "order_shuffled_N01", "root_off_similarity_only_guard", "quotient_erased"]:
        require(errors, controls.get(key, {}).get("fires") is True, f"{key} did not fire")
    decorative = controls.get("decorative_layer_detector", {})
    require(errors, sorted(decorative) == ["L1_BASIN", "L2_CHART", "L3_INFORMATION", "L4_FUSION", "L5_LEDGER"], "decorative layer detector coverage mismatch")
    for key, row in decorative.items():
        require(errors, row.get("fires") is True, f"decorative detector failed for {key}")

    layers = payload.get("layers", {})
    require(errors, sorted(layers) == ["L1_BASIN", "L2_CHART", "L3_INFORMATION", "L4_FUSION", "L5_LEDGER"], "layer map must contain L1-L5")
    require(errors, layers.get("L1_BASIN", {}).get("raw_transition_graphs_persisted") is False, "L1 must not persist raw graphs")
    ledger = layers.get("L5_LEDGER", {}).get("typed_consistency_matrix", {})
    require(errors, ledger.get("all_rows_typed") is True, "ledger rows must be typed")
    require(errors, ledger.get("cross_type_accounts_have_conventions") is True, "cross-type accounts need conventions")
    require(errors, ledger.get("forbidden_cross_type_sum_found") is False, "forbidden cross-type sum detected")

    smt = payload.get("crossover_proofs", {})
    require(errors, smt.get("z3", {}).get("verdict") == "unsat", "z3 verdict must be unsat")
    require(errors, smt.get("z3", {}).get("erased_flip_verdict") == "sat", "z3 erased flip must be sat")
    require(errors, smt.get("cvc5", {}).get("verdict") == "unsat", "cvc5 verdict must be unsat")
    require(errors, smt.get("cvc5", {}).get("erased_flip_verdict") == "sat", "cvc5 erased flip must be sat")

    for engine in ["julia", "jax", "pytorch"]:
        lane = load_lane(engine)
        require(errors, lane.get("all_pass") is True, f"{engine} lane all_pass false")
        require(errors, payload.get("engines", {}).get(engine, {}).get("result_all_pass") is True, f"{engine} envelope result_all_pass false")

    artifact = payload.get("trajectory_artifact", {})
    artifact_path = common.ROOT / artifact.get("path", "")
    sha_path = common.ROOT / artifact.get("sha_path", "")
    require(errors, artifact.get("sha_verified") is True, "trajectory artifact was not sha verified")
    require(errors, artifact_path.exists(), "trajectory artifact file missing")
    require(errors, sha_path.exists(), "trajectory artifact sha sidecar missing")
    if artifact_path.exists() and sha_path.exists():
        stored_payload = common.load_json(artifact_path)
        digest = common.stable_sha256(stored_payload)
        sidecar = sha_path.read_text(encoding="utf-8").split()[0]
        require(errors, digest == sidecar == artifact.get("payload_sha256"), "trajectory artifact sha mismatch")

    require(errors, super_object["all_pass"] is True, f"fresh super object failed: {super_object['failures']}")
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

