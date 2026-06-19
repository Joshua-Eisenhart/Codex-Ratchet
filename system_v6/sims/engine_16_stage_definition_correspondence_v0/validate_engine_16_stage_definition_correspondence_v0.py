#!/usr/bin/env python3
"""Packet-local validator for engine_16_stage_definition_correspondence_v0."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import engine_16_stage_definition_correspondence_v0_boundary as boundary
import engine_16_stage_definition_correspondence_v0_common as common


ROOT = common.ROOT
SIM_DIR = common.SIM_DIR
RESULT_DIR = common.RESULT_DIR
RESULT = common.RESULT_PATH
ENVELOPE = RESULT_DIR / f"{common.SIM_ID}_envelope_results.json"
VALIDATOR_RESULT = RESULT_DIR / f"{common.SIM_ID}_validator_results.json"

sys.path.insert(0, str(ROOT / "scripts"))
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
        "Owner challenge",
        "G.2a idempotency-from-birth",
        "G7 Definition Pin",
        "classification=scratch_diagnostic",
        "NO git add/commit",
        "R_x/D_z",
        "Either correspondence outcome is valid",
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
    require(errors, len(payload.get("base_operator_rows", [])) == 4, "must emit four base operator rows")
    rows = payload.get("defined_stage_rows", [])
    require(errors, len(rows) == 16, "must emit 16 defined stage rows")
    require(errors, all(len(row.get("matrix_bloch_3x3", [])) == 3 for row in rows), "missing 3x3 matrices")
    require(errors, all(len(row.get("matrix_affine_4x4", [])) == 4 for row in rows), "missing 4x4 channels")
    require(errors, all("geometry" in row for row in rows), "missing geometry rows")
    require(errors, all(len(row.get("fingerprint", [])) == 8 for row in rows), "each fingerprint must have 8 floats")
    require(errors, len(payload.get("discovered_components", [])) == 16, "discovered component count mismatch")
    corr = payload.get("correspondence", {})
    require(errors, corr.get("defined_component_count") == payload.get("summary", {}).get("defined_distinct_component_count"), "defined count drift")
    require(errors, len(corr.get("match_matrix_16x16", [])) == 16, "match matrix row count mismatch")
    require(errors, all(len(row) == 16 for row in corr.get("match_matrix_16x16", [])), "match matrix col count mismatch")
    require(errors, corr.get("result") in {"MATCH", "MISMATCH"}, "correspondence result must be explicit")
    neq = payload.get("non_equivalence_matrix", {})
    require(errors, len(neq.get("alias_distinct_matrix_16x16", [])) == 16, "non-equivalence row count mismatch")
    controls = payload.get("controls", {})
    require(errors, controls.get("identity_stages", {}).get("n_distinct") == 1, "identity control failed")
    require(errors, controls.get("erase_order_polarity", {}).get("n_distinct", 99) <= 8, "order-erased control failed")
    require(errors, controls.get("erase_chirality", {}).get("all_lr_pairs_merge") is True, "chirality control failed")
    require(errors, controls.get("scramble_operator_assignments", {}).get("does_not_improve_correspondence") is True, "scramble control failed")
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
