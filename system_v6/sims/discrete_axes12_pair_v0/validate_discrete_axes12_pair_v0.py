#!/usr/bin/env python3
"""Packet-local validator for discrete_axes12_pair_v0."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import discrete_axes12_pair_v0_common as common


ROOT = common.ROOT
SIM_DIR = common.SIM_DIR
RESULT_DIR = common.RESULT_DIR
ENVELOPE = RESULT_DIR / f"{common.SIM_ID}_envelope_results.json"
VALIDATOR_RESULT = RESULT_DIR / f"{common.SIM_ID}_validator_results.json"

sys.path.insert(0, str(ROOT / "scripts"))
from builder_audit_boundary import builder_audit_boundary_errors  # noqa: E402
from validate_three_engine_sim_result import validate as validate_three_engine  # noqa: E402


REQUIRED_PACKET_FILES = [
    "build_card.md",
    f"{common.SIM_ID}_common.py",
    f"{common.SIM_ID}_julia.jl",
    f"{common.SIM_ID}_jax.py",
    f"{common.SIM_ID}_pytorch.py",
    "write_envelope_spec.py",
    f"validate_{common.SIM_ID}.py",
    f"tests/test_{common.SIM_ID}.py",
]


def require(errors: list[str], condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_packet_files(errors: list[str]) -> None:
    for rel_path in REQUIRED_PACKET_FILES:
        require(errors, (SIM_DIR / rel_path).is_file(), f"missing required packet file: {rel_path}")
    text = (SIM_DIR / "build_card.md").read_text(encoding="utf-8") if (SIM_DIR / "build_card.md").exists() else ""
    require(errors, common.SIM_ID in text, "build_card.md missing packet id")
    require(errors, common.CLAIM_CEILING in text, "build_card.md missing claim ceiling")
    require(errors, common.STANDARDS_COMMIT in text, "build_card.md missing standards commit")
    require(errors, common.VEIN_COMMIT in text, "build_card.md missing vein commit")


def validate_ceiling(errors: list[str], payload: dict[str, Any]) -> None:
    require(errors, payload.get("schema_version") == "three_engine_sim_result_v1", "schema_version mismatch")
    require(errors, payload.get("sim_id") == common.SIM_ID, "sim_id mismatch")
    require(errors, payload.get("classification") == common.CLASSIFICATION, "classification must be scratch_diagnostic")
    require(errors, payload.get("promotion_allowed") is False, "promotion_allowed must be false")
    require(errors, payload.get("formal_admission_allowed") is False, "formal_admission_allowed must be false")
    require(errors, payload.get("claim_ceiling") == common.CLAIM_CEILING, "claim ceiling mismatch")
    require(errors, payload.get("standards_commit") == common.STANDARDS_COMMIT, "standards commit mismatch")
    require(errors, payload.get("freshness_tier") == "TIER-2", "freshness tier mismatch")
    require(errors, payload.get("all_pass") is True, "top-level all_pass must be true")
    for banned in (
        "axis admission",
        "Carnot thermodynamic-stroke identity",
        "Szilard-class proof",
        "bridge admission",
        "physics",
        "manifold admission",
    ):
        require(errors, banned in payload.get("disallowed_claims", []), f"missing disallowed claim: {banned}")


def validate_product_and_witnesses(errors: list[str], payload: dict[str, Any]) -> None:
    rebuilt = common.build_axes12_object()
    require(errors, payload.get("state_object_id") == rebuilt["state_object_id"], "state_object_id mismatch")
    carrier = payload.get("carrier", {})
    require(errors, carrier.get("state_count") == common.EXPECTED_STATE_COUNT, "carrier state_count must be 33")
    rows = payload.get("axis12_row_table", [])
    require(errors, len(rows) == common.EXPECTED_ROW_COUNT, "axis12 row table must have 10 rows")
    require(errors, common.stable_sha256(rows) == common.stable_sha256(rebuilt["axis12_row_table"]), "axis12 row table recompute mismatch")
    aliases = {row.get("product_alias") for row in rows}
    require(errors, {"Se", "Ni", "Ne", "Si"} <= aliases, "product aliases missing one or more perceiving classes")
    product = payload.get("joint_product_table", {})
    require(errors, product.get("proper_cptp|direct", {}).get("alias") == "Se", "Se product row mismatch")
    require(errors, product.get("proper_cptp|conjugated", {}).get("alias") == "Ni", "Ni product row mismatch")
    require(errors, product.get("unitary|direct", {}).get("alias") == "Ne", "Ne product row mismatch")
    require(errors, product.get("unitary|conjugated", {}).get("alias") == "Si", "Si product row mismatch")
    by_id = {row["row_id"]: row for row in rows}
    require(errors, by_id["Vortex:pure_hamiltonian"]["axis1_witnesses"]["kraus_rank"] == 1, "unitary calibration kraus rank failed")
    require(errors, by_id["Vortex:pure_hamiltonian"]["axis1_witnesses"]["purity_preserved"] is True, "unitary purity failed")
    require(errors, by_id["Pit"]["axis1_witnesses"]["trace_preserving"] is True, "Pit trace preservation failed")
    require(errors, by_id["Pit"]["axis1_witnesses"]["complete_positive"] is True, "Pit CP failed")
    require(errors, by_id["Pit"]["axis1_witnesses"]["unital"] is False, "Pit unital witness should be false")
    require(errors, by_id["Hill"]["axis2_witnesses"]["connection_K_norm"] > common.EPS, "Hill K_t nonzero failed")
    require(errors, payload.get("carnot_strokes_fence", {}).get("same_object_as_axis12_product") is False, "Carnot fence missing")


def validate_controls_independence_stability(errors: list[str], payload: dict[str, Any]) -> None:
    controls = payload.get("controls", {})
    for name, row in controls.items():
        require(errors, row.get("fired") is True, f"control did not fire: {name}")
    require(errors, controls.get("unitary_row_calibration", {}).get("fired") is True, "unitary control failed")
    require(errors, controls.get("manifestly_conjugated_nonzero_Kt", {}).get("connection_K_norm", 0.0) > common.EPS, "K_t control failed")
    require(errors, controls.get("product_degeneracy_forced_bits", {}).get("flagged") is True, "forced-bit degeneracy not flagged")
    require(errors, controls.get("shuffled_order", {}).get("label_only_reproduction_pass") is False, "shuffled label-only row passed")
    require(errors, controls.get("falsifier_reachability", {}).get("reachable") is True, "falsifier not reachable")

    stability = payload.get("stability_under_axis0_standard", {})
    require(errors, stability.get("neither_trivial_nor_frozen") is True, "stability must be neither trivial nor frozen")
    require(errors, stability.get("one_step", {}).get("stable_edges", 0) > 0, "stable edges missing")
    require(errors, stability.get("one_step", {}).get("changed_edges", 0) > 0, "changed edges missing")

    rows = {row.get("row_id"): row for row in payload.get("independence_rows_vs_axes0_4_5_6", [])}
    required = [
        "axis12_product_not_recoverable_from_axis0_response",
        "axis12_product_not_recoverable_from_axis4_composition",
        "axis12_product_not_recoverable_from_axis5_family",
        "axis12_product_not_recoverable_from_axis6_precedence",
        "identity_leak_report",
    ]
    for row_id in required:
        require(errors, row_id in rows, f"missing independence row: {row_id}")
        require(errors, rows.get(row_id, {}).get("pass") is True, f"independence row did not pass: {row_id}")
    leak = rows.get("identity_leak_report", {})
    require(errors, leak.get("identity_leak_detected") is True, "identity leak must be reported")
    require(errors, leak.get("identity_leak_excluded_best_accuracy", 1.0) < 1.0, "identity-excluded best predictor recovered target")
    require(errors, bool(leak.get("identity_leak_exclusion_rule")), "identity leak exclusion rule missing")


def validate_smt_tooling(errors: list[str], payload: dict[str, Any]) -> None:
    rows = payload.get("smt_rows", {})
    require(errors, set(rows) == {"z3", "cvc5"}, "SMT row set mismatch")
    for name, row in rows.items():
        require(errors, row.get("ran") is True and row.get("load_bearing") is True, f"{name} did not run load-bearing")
        require(errors, row.get("verdict") == "unsat", f"{name} verdict must be UNSAT")
        require(errors, row.get("erased_flip_verdict") == "sat", f"{name} erased flip must be SAT")
        require(errors, row.get("asserted_precomputed_boolean") is False, f"{name} must bind values, not booleans")
    require(errors, payload.get("TOOL_MANIFEST") == common.TOOL_MANIFEST, "TOOL_MANIFEST mismatch")
    require(errors, payload.get("TOOL_INTEGRATION_DEPTH") == common.TOOL_INTEGRATION_DEPTH, "TOOL_INTEGRATION_DEPTH mismatch")
    require(errors, payload.get("tool_intent") == common.TOOL_INTENT, "tool_intent mismatch")
    require(errors, payload.get("no_builder_audit_verdict") is True, "no_builder_audit_verdict must be true")
    require(errors, payload.get("no_builder_audit_verdict_envelope_gate") is True, "no_builder_audit_verdict_envelope_gate must be true")
    require(errors, payload.get("builder_gates", {}).get("packet_audit_verdict_absent") is True, "audit verdict absent gate failed")
    errors.extend(builder_audit_boundary_errors(payload, SIM_DIR / "audit_verdict.md"))
    for engine in ("julia", "jax", "pytorch"):
        lane = load(RESULT_DIR / f"{common.SIM_ID}_{engine}_results.json")
        require(errors, lane.get("all_pass") is True, f"{engine} lane all_pass false")
        require(errors, payload.get("engines", {}).get(engine, {}).get("result_all_pass") is True, f"{engine} envelope result_all_pass false")
        require(errors, payload.get("engines", {}).get(engine, {}).get("reads_peer_result") is False, f"{engine} reads_peer_result must be false")
    require(errors, payload.get("lane_comparison", {}).get("all_lanes_same_counts") is True, "lane count comparison mismatch")


def validate_payload(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    validate_packet_files(errors)
    validate_ceiling(errors, payload)
    validate_product_and_witnesses(errors, payload)
    validate_controls_independence_stability(errors, payload)
    validate_smt_tooling(errors, payload)
    generic_errors = validate_three_engine(
        payload,
        require_pytorch=True,
        strict_source_backed=True,
        require_tool_intent=True,
    )
    errors.extend(f"generic three-engine validator: {err}" for err in generic_errors)
    return errors


def main() -> int:
    payload = load(ENVELOPE)
    errors = validate_payload(payload)
    result = {"ok": not errors, "result_json": common.rel(ENVELOPE), "errors": errors}
    common.write_json(VALIDATOR_RESULT, result)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
