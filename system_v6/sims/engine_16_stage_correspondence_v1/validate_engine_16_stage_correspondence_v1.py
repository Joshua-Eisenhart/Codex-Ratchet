#!/usr/bin/env python3
"""Packet-local validator for engine_16_stage_correspondence_v1."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import engine_16_stage_correspondence_v1_boundary as boundary
import engine_16_stage_correspondence_v1_common as common


ROOT = common.ROOT
SIM_DIR = common.SIM_DIR
RESULT_DIR = common.RESULT_DIR
RESULT = common.RESULT_PATH
ENVELOPE = RESULT_DIR / f"{common.SIM_ID}_envelope_results.json"
VALIDATOR_RESULT = RESULT_DIR / f"{common.SIM_ID}_validator_results.json"

sys.path.insert(0, str(ROOT / "scripts"))
from gcm_substrate_check import gcm_substrate_check  # noqa: E402
from validate_three_engine_sim_result import validate as validate_three_engine  # noqa: E402


REQUIRED_FILES = [
    "build_card.md",
    "builder_self_assessment.md",
    f"{common.SIM_ID}_common.py",
    f"{common.SIM_ID}_boundary.py",
    f"{common.SIM_ID}.py",
    f"{common.SIM_ID}_jax.py",
    f"{common.SIM_ID}_pytorch.py",
    f"{common.SIM_ID}_julia.jl",
    f"{common.SIM_ID}_envelope.py",
    f"validate_{common.SIM_ID}.py",
    f"tests/test_{common.SIM_ID}.py",
]


def require(errors: list[str], condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_files(errors: list[str]) -> None:
    for rel_path in REQUIRED_FILES:
        require(errors, (SIM_DIR / rel_path).is_file(), f"missing required file: {rel_path}")
    text = (SIM_DIR / "build_card.md").read_text(encoding="utf-8")
    for phrase in (
        common.SIM_ID,
        "G.2a idempotency-from-birth",
        "G7 Definition Pin",
        "classification: `scratch_diagnostic`",
        "NO git add/commit",
        "Ti <-> D_z",
        "Either correspondence outcome is the result",
        "gcmobj_a40e54e13cec01466c9d675028b3574b",
    ):
        require(errors, phrase in text, f"build_card.md missing: {phrase}")


def validate_packet_payload(errors: list[str], payload: dict[str, Any]) -> None:
    require(errors, payload.get("schema") == common.SCHEMA, "schema mismatch")
    require(errors, payload.get("sim_id") == common.SIM_ID, "sim_id mismatch")
    require(errors, payload.get("all_pass") is True, "all_pass must be true")
    require(errors, payload.get("definition_phase_pinned_before_correspondence") is True, "definitions not pinned first")
    require(errors, payload.get("classification") == common.CLASSIFICATION, "classification mismatch")
    require(errors, payload.get("claim_ceiling") == common.CLAIM_CEILING, "claim ceiling mismatch")
    require(errors, payload.get("promotion_allowed") is False, "promotion_allowed must be false")
    require(errors, payload.get("formal_admission_allowed") is False, "formal_admission_allowed must be false")
    require(errors, payload.get("layer_declaration", {}).get("layer") == "15 ordered compositions", "layer declaration mismatch")
    require(errors, len(payload.get("terrain_flow_rows", [])) == 4, "must emit four terrain flow rows")
    require(errors, len(payload.get("base_operator_rows", [])) == 4, "must emit four base operator rows")
    require(errors, [row["stage_token"] for row in common.STAGE_TABLE] == payload.get("definition_rule", {}).get("stage_table_verbatim_tokens"), "stage table token drift")
    rows = payload.get("defined_stage_rows", [])
    require(errors, len(rows) == 16, "must emit 16 defined stage rows")
    require(errors, [row["authority_stage_token"] for row in rows] == [row["stage_token"] for row in common.STAGE_TABLE], "defined rows not in owner-table order")
    require(errors, all(len(row.get("matrix_bloch_3x3", [])) == 3 for row in rows), "missing 3x3 matrices")
    require(errors, all(len(row.get("translation_bloch_3", [])) == 3 for row in rows), "missing translations")
    require(errors, all(len(row.get("matrix_affine_4x4", [])) == 4 for row in rows), "missing 4x4 channels")
    require(errors, all("geometry" in row for row in rows), "missing geometry rows")
    require(errors, all(len(row.get("fingerprint", [])) == 8 for row in rows), "each fingerprint must have 8 floats")
    require(errors, all(str(row.get("component_id", "")).startswith("eng64_fp_") for row in rows), "component IDs must be eng64 hashes")
    require(errors, len(payload.get("discovered_components", [])) == 16, "discovered component count mismatch")
    corr = payload.get("correspondence", {})
    require(errors, corr.get("defined_component_count") == payload.get("summary", {}).get("defined_distinct_component_count"), "defined count drift")
    require(errors, corr.get("verdict") in {"full_bijection", "partial", "0-match_again"}, "bad correspondence verdict")
    require(errors, len(corr.get("match_matrix_16x16", [])) == 16, "match matrix row count mismatch")
    require(errors, all(len(row) == 16 for row in corr.get("match_matrix_16x16", [])), "match matrix col count mismatch")
    require(errors, corr.get("result") in {"MATCH", "MISMATCH"}, "correspondence result must be explicit")
    if corr.get("verdict") == "partial":
        require(errors, bool(corr.get("failing_pairings")), "partial verdict must name failing pairings")
    neq = payload.get("non_equivalence_matrix", {})
    require(errors, len(neq.get("alias_distinct_matrix_16x16", [])) == 16, "non-equivalence row count mismatch")
    controls = payload.get("controls", {})
    require(errors, controls.get("order_erasure", {}).get("collapsed_toward_8") is True, "order-erasure control failed")
    require(
        errors,
        controls.get("pairing_scramble", {}).get("wrong_pairing_scores_worse") is True
        or controls.get("pairing_scramble", {}).get("pairing_convention_doing_nothing") is True,
        "pairing-scramble control failed",
    )
    require(errors, controls.get("label_permutation_invariance", {}).get("fingerprint_ids_unchanged") is True, "label-permutation control failed")
    require(errors, controls.get("commuting_pair_honest_null_rule", {}).get("reported_all_commuting_pairs") is True, "commuting-pair control failed")
    require(errors, payload.get("substrate_check", {}).get("ok") is True, "substrate check must pass")
    require(errors, payload.get("lineage_free_negative_control", {}).get("ok") is False, "lineage-free negative must fail red")
    require(errors, gcm_substrate_check(payload).get("ok") is True, "helper substrate check over payload failed")
    require(errors, payload.get("gcm_lineage", {}).get("gcm_object_id") == boundary.EXPECTED_GCM_OBJECT_ID, "GCM object id mismatch")
    require(errors, payload.get("TOOL_MANIFEST") == common.TOOL_MANIFEST, "TOOL_MANIFEST mismatch")
    require(errors, payload.get("TOOL_INTEGRATION_DEPTH") == common.TOOL_INTEGRATION_DEPTH, "TOOL_INTEGRATION_DEPTH mismatch")
    require(errors, payload.get("tool_intent") == common.TOOL_INTENT, "tool_intent mismatch")
    errors.extend(boundary.boundary_errors(payload, SIM_DIR))


def validate_envelope(errors: list[str], payload: dict[str, Any]) -> None:
    require(errors, payload.get("schema_version") == "three_engine_sim_result_v1", "envelope schema_version mismatch")
    require(errors, payload.get("schema") == f"{common.SIM_ID}_envelope_v1", "packet envelope schema mismatch")
    require(errors, payload.get("sim_id") == common.SIM_ID, "envelope sim_id mismatch")
    require(errors, payload.get("all_pass") is True, "envelope all_pass must be true")
    require(errors, set(payload.get("engines", {})) == {"julia", "jax", "pytorch"}, "engine set mismatch")
    consensus = payload.get("engine_consensus", {})
    for key in ("stage_count_agreement", "defined_distinct_count_agreement", "python_lane_match_matrix_hash_agreement"):
        require(errors, consensus.get(key) is True, f"engine consensus failed: {key}")
    for engine in ("julia", "jax", "pytorch"):
        lane = load(RESULT_DIR / f"{common.SIM_ID}_{engine}_results.json")
        require(errors, lane.get("all_pass") is True, f"{engine} lane all_pass false")
        require(errors, payload.get("engines", {}).get(engine, {}).get("result_all_pass") is True, f"{engine} envelope result_all_pass false")
        require(errors, payload.get("engines", {}).get(engine, {}).get("reads_peer_result") is False, f"{engine} reads peer result")
    errors.extend(boundary.boundary_errors(payload, SIM_DIR))
    require(errors, gcm_substrate_check(payload).get("ok") is True, "helper substrate check over envelope failed")
    generic = validate_three_engine(
        payload,
        require_pytorch=True,
        strict_source_backed=True,
        require_tool_intent=True,
    )
    errors.extend(f"generic three-engine validator: {err}" for err in generic)


def main() -> int:
    errors: list[str] = []
    validate_files(errors)
    if RESULT.exists():
        validate_packet_payload(errors, load(RESULT))
    else:
        errors.append(f"missing result: {common.rel(RESULT)}")
    if ENVELOPE.exists():
        validate_envelope(errors, load(ENVELOPE))
    else:
        errors.append(f"missing envelope: {common.rel(ENVELOPE)}")
    output = {"ok": not errors, "errors": errors, "result_json": common.rel(ENVELOPE)}
    common.write_json(VALIDATOR_RESULT, output)
    print(json.dumps(output, indent=2, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
