#!/usr/bin/env python3
"""Packet validator for ECD.01 order-programmability."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import ecd01_order_programmable_computer_v0_common as common


ENVELOPE = common.RESULT_DIR / f"{common.SIM_ID}_envelope_results.json"
VALIDATOR_RESULT = common.RESULT_DIR / f"{common.SIM_ID}_validator_results.json"

sys.path.insert(0, str(common.ROOT / "scripts"))
from builder_audit_boundary import builder_audit_boundary_errors  # noqa: E402
from validate_three_engine_sim_result import validate as validate_three_engine  # noqa: E402


REQUIRED_PACKET_FILES = [
    "build_card.md",
    f"{common.SIM_ID}_common.py",
    f"{common.SIM_ID}_julia.jl",
    f"{common.SIM_ID}_jax.py",
    f"{common.SIM_ID}_pytorch.py",
    f"{common.SIM_ID}_envelope.py",
    f"validate_{common.SIM_ID}.py",
    f"tests/test_{common.SIM_ID}.py",
]


def require(errors: list[str], condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_payload(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    rebuilt = common.build_order_programmability_object()
    for rel_path in REQUIRED_PACKET_FILES:
        require(errors, (common.SIM_DIR / rel_path).is_file(), f"missing packet file: {rel_path}")
    require(errors, payload.get("schema_version") == "three_engine_sim_result_v1", "schema version mismatch")
    require(errors, payload.get("sim_id") == common.SIM_ID, "sim id mismatch")
    require(errors, payload.get("classification") == common.CLASSIFICATION, "classification must be scratch_diagnostic")
    require(errors, payload.get("promotion_allowed") is False, "promotion_allowed must be false")
    require(errors, payload.get("formal_admission_allowed") is False, "formal_admission_allowed must be false")
    require(errors, payload.get("claim_ceiling") == common.CLAIM_CEILING, "claim ceiling mismatch")
    require(errors, payload.get("all_pass") is True, "all_pass must be true")
    require(errors, payload.get("registered_order_words") == common.REGISTERED_ORDER_WORDS, "registered order words changed")
    require(errors, payload.get("channel_hash_classes") == rebuilt["channel_hash_classes"], "channel hashes recompute mismatch")
    require(errors, payload.get("capability_metric") == rebuilt["capability_metric"], "capability metric recompute mismatch")
    require(errors, payload.get("channel_distinguishability_matrix") == rebuilt["channel_distinguishability_matrix"], "distance matrix recompute mismatch")
    metric = payload.get("capability_metric", {})
    require(errors, metric.get("qit_distinct_channel_count", 0) >= 3, "QIT distinct diversity too small")
    require(errors, metric.get("szilard_distinct_channel_count") == 1, "Szilard baseline must be single-class")
    require(errors, metric.get("qit_diversity_strictly_exceeds_szilard") is True, "Szilard baseline did not fail")
    controls = payload.get("controls", {})
    require(errors, controls.get("commuting_generator_engine", {}).get("capability_gone_without_N01") is True, "commuting control did not collapse")
    require(errors, controls.get("shuffled_labels", {}).get("same_distance_multiset_after_label_shuffle") is True, "shuffled-label control failed")
    for name, row in payload.get("smt_rows", {}).items():
        require(errors, row.get("verdict") == "unsat", f"{name} real SMT verdict must be unsat")
        require(errors, row.get("erased_flip_verdict") == "sat", f"{name} erased SMT verdict must be sat")
        require(errors, row.get("asserted_precomputed_boolean") is False, f"{name} must bind counts, not booleans")
    require(errors, payload.get("TOOL_MANIFEST") == common.TOOL_MANIFEST, "TOOL_MANIFEST mismatch")
    require(errors, payload.get("TOOL_INTEGRATION_DEPTH") == common.TOOL_INTEGRATION_DEPTH, "TOOL_INTEGRATION_DEPTH mismatch")
    errors.extend(builder_audit_boundary_errors(payload, common.SIM_DIR / "audit_verdict.md"))
    errors.extend(
        f"generic three-engine validator: {err}"
        for err in validate_three_engine(payload, require_pytorch=True, strict_source_backed=True, require_tool_intent=True)
    )
    for engine in ("julia", "jax", "pytorch"):
        lane = load(common.RESULT_DIR / f"{common.SIM_ID}_{engine}_results.json")
        require(errors, lane.get("all_pass") is True, f"{engine} lane all_pass false")
        require(errors, payload.get("engines", {}).get(engine, {}).get("all_pass") is True, f"{engine} envelope result false")
        require(errors, payload.get("engines", {}).get(engine, {}).get("reads_peer_result") is False, f"{engine} reads_peer_result must be false")
    require(errors, payload.get("divergence", {}).get("max_divergence") == 0, "engine channel hashes diverged")
    return errors


def main() -> int:
    payload = load(ENVELOPE)
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
