#!/usr/bin/env python3
"""Packet-local validator for axis0_contender_heavy_v0."""

from __future__ import annotations

import datetime as dt
import json
import sys
from pathlib import Path
from typing import Any


SIM_ID = "axis0_contender_heavy_v0"
ROOT = Path(__file__).resolve().parents[3]
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_DIR = SIM_DIR / "results"
ENVELOPE = RESULT_DIR / f"{SIM_ID}_envelope_results.json"
JAX = RESULT_DIR / f"{SIM_ID}_jax_results.json"
PYTORCH = RESULT_DIR / f"{SIM_ID}_pytorch_results.json"
JULIA = RESULT_DIR / f"{SIM_ID}_julia_results.json"
VALIDATOR_RESULT = RESULT_DIR / f"{SIM_ID}_validator_results.json"
AUDIT_VERDICT = SIM_DIR / "audit_verdict.md"

sys.path.insert(0, str(ROOT / "scripts"))
import validate_three_engine_sim_result as generic_validator  # noqa: E402
from builder_audit_boundary import builder_audit_boundary_errors  # noqa: E402


EXPECTED_VERDICTS = {
    "A0.CP.3_entropy_gradient_sign": "excluded-by-stability-class-mismatch",
    "A0.CP.4_pauli_participation_feedback_polarity": "excluded-by-stability-class-mismatch",
    "A0.CP.5_flux_direction_annular_or_edge_current": "excluded-by-distinction-boundary",
    "A0.CP.6_flux_continuity_n3_n4_current_sign": "excluded-by-distinction-boundary",
    "A0.CP.7_lyapunov_descent_direction": "excluded-by-functional-teeth-wrong-distinction",
    "A0.CP.8_hopfield_energy_gradient_sign": "excluded-by-retrieval-teeth-wrong-distinction",
    "A0.CP.9_holonomy_spectrum_sign": "excluded-by-holonomy-axis3-axis6-boundary",
}
EXPECTED_SENTENCE = "Axis-0 = the anchor alias class"


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def require(errors: list[str], condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


def verdict_map(payload: dict[str, Any]) -> dict[str, str]:
    return {row["candidate"]: row["final_verdict"] for row in payload.get("final_verdict_table", [])}


def final_table(payload: dict[str, Any]) -> list[dict[str, Any]]:
    return payload.get("final_verdict_table", [])


def validate_payload() -> tuple[list[str], dict[str, Any]]:
    errors: list[str] = []
    for path in [ENVELOPE, JAX, PYTORCH, JULIA, SIM_DIR / "build_card.md", SIM_DIR / "builder_self_assessment.md"]:
        require(errors, path.exists(), f"missing required file: {path.relative_to(ROOT)}")
    payload = load(ENVELOPE) if ENVELOPE.exists() else {}
    jax = load(JAX) if JAX.exists() else {}
    pytorch = load(PYTORCH) if PYTORCH.exists() else {}
    julia = load(JULIA) if JULIA.exists() else {}

    if payload:
        require(errors, payload.get("schema_version") == "three_engine_sim_result_v1", "schema_version mismatch")
        require(errors, payload.get("sim_id") == SIM_ID, "sim_id mismatch")
        require(errors, payload.get("classification") == "scratch_diagnostic", "classification must be scratch_diagnostic")
        require(errors, payload.get("promotion_allowed") is False, "promotion_allowed must be false")
        require(errors, payload.get("formal_admission_allowed") is False, "formal_admission_allowed must be false")
        require(errors, payload.get("all_pass") is True, "all_pass must be true")
        require(errors, payload.get("family_adjudication_sentence") == EXPECTED_SENTENCE, "adjudication sentence mismatch")
        require(errors, verdict_map(payload) == EXPECTED_VERDICTS, "final verdict table mismatch")
        require(errors, all(row.get("co_survivor") is False for row in final_table(payload)), "no co-survivor should be minted")
        require(errors, sorted(payload.get("engines", {})) == ["jax", "julia", "pytorch"], "all three engines must be present")

        generic_errors = generic_validator.validate(
            payload,
            require_pytorch=True,
            strict_source_backed=True,
            require_tool_intent=True,
        )
        errors.extend([f"generic validator: {error}" for error in generic_errors])
        errors.extend([f"builder boundary: {error}" for error in builder_audit_boundary_errors(payload, AUDIT_VERDICT)])

        gates = payload.get("build_gates", {})
        for gate in [
            "julia_lane_pass",
            "jax_lane_pass",
            "pytorch_lane_pass",
            "three_engine_final_tables_match",
            "registry_commit_bound",
            "doctrine_commit_bound",
            "sweep_audit_commit_bound",
            "build_card_copied",
            "builder_self_assessment_present",
            "classification_ceiling",
            "all_heavy_rows_excluded",
            "no_cosurvivors_minted",
            "family_adjudication_sentence",
            "z3_cvc5_agree",
            "julia_z3_agrees",
            "flip_controls_fire",
            "builder_audit_boundary_ok",
        ]:
            require(errors, gates.get(gate) is True, f"gate failed: {gate}")

        controls = {row["id"]: row["verdict"] for row in payload.get("control_verdicts", [])}
        require(errors, controls.get("control.anchor_self") == "alias-of-anchor", "anchor control mismatch")
        require(errors, controls.get("control.deliberate_alias") == "alias-of-anchor", "deliberate alias control mismatch")
        require(errors, controls.get("control.degree_only_baseline") == "excluded-by-degree-teeth-wrong-distinction", "degree control mismatch")
        require(errors, controls.get("control.constant_readout_erased", "").startswith("excluded-by"), "constant control mismatch")
        require(errors, controls.get("control.zero_readout_erased", "").startswith("excluded-by"), "zero control mismatch")

        light = {row["candidate"]: row["verdict"] for row in payload.get("light_regression_verdicts", [])}
        require(errors, light.get("A0.CP.1_unweighted_edge_gradient_count_balance", "").startswith("excluded-by"), "CP.1 regression mismatch")
        require(errors, light.get("A0.CP.2_incoming_vs_outgoing_gradient_current", "").startswith("excluded-by"), "CP.2 regression mismatch")
        require(errors, light.get("A0.CP.10_transition_graph_in_out_degree_imbalance", "").startswith("excluded-by"), "CP.10 regression mismatch")

        for row in payload.get("candidate_verdict_table", []):
            require(errors, len(row.get("sign_vector", [])) == 33, f"{row.get('candidate')} vector length mismatch")
            require(errors, row.get("teeth_run") is True, f"{row.get('candidate')} teeth not marked run")
            require(errors, row.get("adapter_status") == "computed_source_backed_33_cell_variants", f"{row.get('candidate')} adapter status mismatch")
            require(errors, bool(row.get("cell_level_disagreement_table") is not None), f"{row.get('candidate')} missing cell disagreement table")
            require(errors, "stability_class_comparison" in row, f"{row.get('candidate')} missing stability comparison")
            require(errors, "distinction_boundary_check" in row, f"{row.get('candidate')} missing boundary check")

    for name, lane in [("jax", jax), ("pytorch", pytorch), ("julia", julia)]:
        if lane:
            require(errors, lane.get("all_pass") is True, f"{name} lane all_pass false")
            require(errors, verdict_map(lane) == EXPECTED_VERDICTS, f"{name} verdict mismatch")
            require(errors, lane.get("reads_peer_result") is False, f"{name} must not read peer result")

    summary = {
        "payload": payload,
        "jax": jax,
        "pytorch": pytorch,
        "julia": julia,
    }
    return errors, summary


def main() -> int:
    errors, summary = validate_payload()
    result = {
        "ok": not errors,
        "validator_ok": not errors,
        "sim_id": SIM_ID,
        "result_json": str(ENVELOPE.relative_to(ROOT)),
        "errors": errors,
        "verdicts": verdict_map(summary["payload"]) if summary.get("payload") else {},
        "family_adjudication_sentence": summary.get("payload", {}).get("family_adjudication_sentence"),
        "generated_at": dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    VALIDATOR_RESULT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
