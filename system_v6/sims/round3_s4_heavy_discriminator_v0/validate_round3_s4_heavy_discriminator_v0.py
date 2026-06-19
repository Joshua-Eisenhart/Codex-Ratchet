#!/usr/bin/env python3
"""Packet-local validator for round3_s4_heavy_discriminator_v0."""

from __future__ import annotations

import datetime as dt
import json
from pathlib import Path
from typing import Any


ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
SIM_ID = "round3_s4_heavy_discriminator_v0"
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_DIR = SIM_DIR / "results"
ENVELOPE = RESULT_DIR / f"{SIM_ID}_envelope_results.json"
JAX = RESULT_DIR / f"{SIM_ID}_jax_results.json"
JULIA = RESULT_DIR / f"{SIM_ID}_julia_results.json"
VALIDATOR_RESULT = RESULT_DIR / f"{SIM_ID}_validator_results.json"

EXPECTED_VERDICTS = {
    "S4.R3.1_z_amplitude_damping_pair": "excluded-by-N01-commutator-and-fixed-axis-rows",
    "S4.R3.2_x_amplitude_damping_pair": "excluded-under-pinned-parent-z-probe-convention-by-z-probe-quotient-descent-mortality",
    "S4.R3.3_dephase_rotate_hybrid": "excluded-by-shell-preservation-leakage",
    "S4.R3.5_weak_nonunital_pauli_channel": "excluded-by-Choi-positivity-and-fixed-axis",
}


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def require(errors: list[str], condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


def verdict_map(payload: dict[str, Any]) -> dict[str, str]:
    return {row["candidate"]: row["verdict"] for row in payload.get("candidate_verdicts", [])}


def verdict_map_from_table(payload: dict[str, Any]) -> dict[str, str]:
    return {row["candidate"]: row["verdict"] for row in payload.get("candidate_verdict_table", [])}


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
        require(errors, payload.get("classification") == "scratch_diagnostic", "classification mismatch")
        require(errors, payload.get("promotion_allowed") is False, "promotion_allowed must be false")
        require(errors, payload.get("formal_admission_allowed") is False, "formal_admission_allowed must be false")
        require(errors, payload.get("all_pass") is True, "all_pass must be true")
        require(errors, payload.get("engine_contract", {}).get("mode") == "julia_canon_jax_workhorse", "engine mode mismatch")
        require(errors, "pytorch" not in payload.get("engines", {}), "pytorch must be honestly omitted")
        require(errors, verdict_map_from_table(payload) == EXPECTED_VERDICTS, "candidate verdict table mismatch")
        gates = payload.get("build_gates", {})
        for gate in [
            "julia_lane_pass",
            "jax_lane_pass",
            "julia_jax_verdicts_match",
            "expected_four_row_verdicts",
            "registry_commit_bound",
            "build_card_copied",
            "classification_ceiling",
            "z3_cvc5_agree",
            "julia_z3_agrees",
            "flip_controls_annotated",
            "julia_flip_control_fires",
            "r3_5_choi_negative_seen",
            "r3_2_pin_relative_recorded",
            "pytorch_honestly_omitted",
        ]:
            require(errors, gates.get(gate) is True, f"gate failed: {gate}")
        proofs = payload.get("crossover_proofs", {})
        require(errors, proofs.get("z3", {}).get("verdict") == "unsat", "z3 must be unsat")
        require(errors, proofs.get("cvc5", {}).get("verdict") == "unsat", "cvc5 must be unsat")
        require(errors, proofs.get("julia_z3", {}).get("verdict") == "unsat", "julia_z3 must be unsat")
        require(errors, proofs.get("z3", {}).get("flip_control_verdict") == "tautological_flip", "z3 flip must be annotated tautological_flip")
        require(errors, proofs.get("cvc5", {}).get("flip_control_verdict") == "tautological_flip", "cvc5 flip must be annotated tautological_flip")
        require(errors, proofs.get("julia_z3", {}).get("flip_control_verdict") == "sat", "julia_z3 flip must be sat")

    if jax:
        require(errors, jax.get("all_pass") is True, "jax all_pass false")
        require(errors, verdict_map(jax) == EXPECTED_VERDICTS, "jax verdict mismatch")
        require(errors, jax.get("reads_peer_result") is False, "jax peer read")
    if julia:
        require(errors, julia.get("all_pass") is True, "julia all_pass false")
        require(errors, verdict_map(julia) == EXPECTED_VERDICTS, "julia verdict mismatch")
        require(errors, julia.get("reads_peer_result") is False, "julia peer read")

    result = {
        "ok": not errors,
        "validator_ok": not errors,
        "sim_id": SIM_ID,
        "result_json": str(ENVELOPE.relative_to(ROOT)),
        "errors": errors,
        "verdicts": verdict_map_from_table(payload) if payload else {},
        "generated_at": dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    VALIDATOR_RESULT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
