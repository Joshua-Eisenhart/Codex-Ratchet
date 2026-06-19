#!/usr/bin/env python3
"""Packet-local validator for axis0_contender_sweep_v0."""

from __future__ import annotations

import datetime as dt
import json
import sys
from pathlib import Path
from typing import Any


SIM_ID = "axis0_contender_sweep_v0"
ROOT = Path(__file__).resolve().parents[3]
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_DIR = SIM_DIR / "results"
ENVELOPE = RESULT_DIR / f"{SIM_ID}_envelope_results.json"
JAX = RESULT_DIR / f"{SIM_ID}_jax_results.json"
JULIA = RESULT_DIR / f"{SIM_ID}_julia_results.json"
VALIDATOR_RESULT = RESULT_DIR / f"{SIM_ID}_validator_results.json"

sys.path.insert(0, str(ROOT / "scripts"))
import validate_three_engine_sim_result as generic_validator  # noqa: E402


EXPECTED_VERDICTS = {
    "A0.CP.0_committed_signed_outgoing_gradient_flux": "alias-of-anchor",
    "A0.CP.1_unweighted_edge_gradient_count_balance": "excluded-by-Hamming-disagreement-from-committed-sign-vector",
    "A0.CP.2_incoming_vs_outgoing_gradient_current": "excluded-by-source-sink-imbalance",
    "A0.CP.3_entropy_gradient_sign": "co-survivor-open",
    "A0.CP.4_pauli_participation_feedback_polarity": "co-survivor-open",
    "A0.CP.5_flux_direction_annular_or_edge_current": "co-survivor-open",
    "A0.CP.6_flux_continuity_n3_n4_current_sign": "co-survivor-open",
    "A0.CP.7_lyapunov_descent_direction": "co-survivor-open",
    "A0.CP.8_hopfield_energy_gradient_sign": "co-survivor-open",
    "A0.CP.9_holonomy_spectrum_sign": "co-survivor-open",
    "A0.CP.10_transition_graph_in_out_degree_imbalance": "excluded-by-degree-teeth-wrong-distinction",
}


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def require(errors: list[str], condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


def verdict_map_from_table(payload: dict[str, Any]) -> dict[str, str]:
    return {row["candidate"]: row["verdict"] for row in payload.get("candidate_verdict_table", [])}


def verdict_map_from_lane(payload: dict[str, Any]) -> dict[str, str]:
    return {row["id"]: row["verdict"] for row in payload.get("candidate_verdicts", [])}


def main() -> int:
    errors: list[str] = []
    for path in [ENVELOPE, JAX, JULIA, SIM_DIR / "build_card.md"]:
        require(errors, path.exists(), f"missing required file: {path.relative_to(ROOT)}")

    payload = load(ENVELOPE) if ENVELOPE.exists() else {}
    jax = load(JAX) if JAX.exists() else {}
    julia = load(JULIA) if JULIA.exists() else {}

    if payload:
        require(errors, payload.get("schema_version") == "three_engine_sim_result_v1", "schema_version mismatch")
        require(errors, payload.get("sim_id") == SIM_ID, "sim_id mismatch")
        require(errors, payload.get("classification") == "scratch_diagnostic", "classification must be scratch_diagnostic")
        require(errors, payload.get("promotion_allowed") is False, "promotion_allowed must be false")
        require(errors, payload.get("formal_admission_allowed") is False, "formal_admission_allowed must be false")
        require(errors, payload.get("all_pass") is True, "all_pass must be true")
        require(errors, payload.get("envelope_built_with_helper") is True, "helper-built envelope flag missing")
        require(errors, payload.get("build_helper_path") == "scripts/build_three_engine_envelope.py", "helper path mismatch")
        require(errors, "pytorch" not in payload.get("engines", {}), "pytorch lane must be omitted")
        omitted = payload.get("engine_contract", {}).get("omitted_lanes", {})
        require(errors, "pytorch" in omitted and "No tensor" in omitted["pytorch"], "pytorch omission text missing")

        generic_errors = generic_validator.validate(payload, require_pytorch=False)
        errors.extend([f"generic validator: {error}" for error in generic_errors])

        gates = payload.get("build_gates", {})
        for gate in [
            "julia_lane_pass",
            "jax_lane_pass",
            "julia_jax_verdicts_match",
            "registry_commit_bound",
            "registry_candidate_list_matches_committed",
            "registry_annotation_drift_recorded",
            "build_card_copied",
            "classification_ceiling",
            "pytorch_honestly_omitted",
            "z3_cvc5_agree",
            "flip_controls_fire",
            "heavy_rows_open_queued",
            "no_extra_candidates_added_after_results",
        ]:
            require(errors, gates.get(gate) is True, f"gate failed: {gate}")

        require(errors, verdict_map_from_table(payload) == EXPECTED_VERDICTS, "candidate verdict table mismatch")
        counts = payload.get("counts", {})
        require(errors, counts.get("registered_candidate_count") == 11, "registered count mismatch")
        require(errors, counts.get("light_symbolic_registered_count") == 4, "light-symbolic count mismatch")
        require(errors, counts.get("heavy_queued_count") == 7, "heavy queue count mismatch")
        require(errors, counts.get("extra_candidates_added_after_results") == 0, "post-hoc candidate count mismatch")
        phase2 = payload.get("phase2_queue", {})
        require(errors, len(phase2.get("heavy_local_queued_by_registry_cost_class", [])) == 7, "heavy queue missing rows")
        controls = {row["id"]: row["verdict"] for row in payload.get("control_verdicts", [])}
        require(errors, controls.get("control.anchor_self") == "alias-of-anchor", "anchor control mismatch")
        require(
            errors,
            controls.get("control.sign_flipped_monotone_reparameterized_anchor") == "alias-of-anchor",
            "alias control mismatch",
        )
        require(
            errors,
            controls.get("control.axis6_style_order_readout") == "not-axis0-contender-by-distinction-boundary",
            "different-distinction control mismatch",
        )
        proofs = payload.get("crossover_proofs", {})
        require(errors, proofs.get("z3", {}).get("verdict") == "unsat", "z3 positive proof must be unsat")
        require(errors, proofs.get("cvc5", {}).get("verdict") == "unsat", "cvc5 positive proof must be unsat")
        require(errors, proofs.get("z3", {}).get("flip_control_verdict") == "sat", "z3 flip must be sat")
        require(errors, proofs.get("cvc5", {}).get("flip_control_verdict") == "sat", "cvc5 flip must be sat")
        require(errors, proofs.get("julia_z3", {}).get("verdict") == "unsat", "julia_z3 positive proof must be unsat")
        require(errors, proofs.get("julia_z3", {}).get("flip_control_verdict") == "sat", "julia_z3 flip must be sat")

    if jax:
        require(errors, jax.get("all_pass") is True, "jax lane all_pass false")
        require(errors, verdict_map_from_table(jax) == EXPECTED_VERDICTS, "jax verdict mismatch")
        require(errors, jax.get("reads_peer_result") is False, "jax must not read peer result")
    if julia:
        require(errors, julia.get("all_pass") is True, "julia lane all_pass false")
        require(errors, verdict_map_from_lane(julia) == EXPECTED_VERDICTS, "julia verdict mismatch")
        require(errors, julia.get("reads_peer_result") is False, "julia must not read peer result")

    result = {
        "ok": not errors,
        "validator_ok": not errors,
        "sim_id": SIM_ID,
        "result_json": str(ENVELOPE.relative_to(ROOT)),
        "errors": errors,
        "verdicts": verdict_map_from_table(payload) if payload else {},
        "phase2_queue": payload.get("phase2_queue") if payload else {},
        "generated_at": dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    VALIDATOR_RESULT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
