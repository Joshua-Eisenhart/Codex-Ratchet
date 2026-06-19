#!/usr/bin/env python3
"""Packet-local validator for round3_s3_alias_pass_v0."""

from __future__ import annotations

import datetime as dt
import json
from pathlib import Path
from typing import Any


ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
SIM_ID = "round3_s3_alias_pass_v0"
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_DIR = SIM_DIR / "results"
ENVELOPE = RESULT_DIR / f"{SIM_ID}_envelope_results.json"
JAX = RESULT_DIR / f"{SIM_ID}_jax_results.json"
JULIA = RESULT_DIR / f"{SIM_ID}_julia_results.json"
VALIDATOR_RESULT = RESULT_DIR / f"{SIM_ID}_validator_results.json"

EXPECTED_VERDICTS = {
    "S3.R3.0_committed_pauli_xyz": "anchor",
    "S3.R3.1_mub_xyz_alias_probe": "alias",
    "S3.R3.2_sic_tetrahedron": "co-survivor-open",
    "S3.R3.3_noisy_pauli_ic__lambda_2_3": "excluded-by-projective-sharpness-and-N01-order-row",
    "S3.R3.3_noisy_pauli_ic__lambda_1_2": "excluded-by-projective-sharpness-and-N01-order-row",
    "S3.R3.4_z_refined_equatorial_trine": "excluded-by-z-coarsening-plus-six-state-separation",
    "S3.R3.5_rank4_random_null_fixed": "excluded-by-composite-IC-z-order-row",
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
        require(
            errors,
            payload.get("engine_contract", {}).get("mode") == "julia_canon_plus_jax_diagnostic",
            "engine mode must be honest two-engine symbolic mode",
        )
        omitted = payload.get("engine_contract", {}).get("omitted_lanes", {})
        require(errors, "pytorch" in omitted and "No graph" in omitted["pytorch"], "pytorch omission must be explicit")
        require(errors, "pytorch" not in payload.get("engines", {}), "pytorch engine must not be present")

        gates = payload.get("build_gates", {})
        for gate in [
            "julia_lane_pass",
            "jax_lane_pass",
            "julia_jax_verdicts_match",
            "registry_commit_bound",
            "build_card_copied",
            "classification_ceiling",
            "pytorch_honestly_omitted",
            "generic_validator_expected_without_require_pytorch",
            "z3_cvc5_agree",
            "flip_controls_fire",
            "mub_alias_not_counted_independent",
            "sic_preserved_not_merged",
            "no_heavy_local_s3_registry_rows",
        ]:
            require(errors, gates.get(gate) is True, f"gate failed: {gate}")

        require(errors, verdict_map_from_table(payload) == EXPECTED_VERDICTS, "candidate verdict table mismatch")
        phase2 = payload.get("phase2_queue", {})
        require(
            errors,
            phase2.get("light_symbolic_non_alias_representatives_remaining") == ["S3.R3.2_sic_tetrahedron"],
            "SIC must be the only non-alias open representative",
        )
        require(
            errors,
            phase2.get("known_co_survivors_not_heavy_queued") == ["S3.R3.2_sic_tetrahedron"],
            "SIC must be recorded as known co-survivor, not heavy queued",
        )
        require(
            errors,
            phase2.get("heavy_local_queued_by_registry_cost_class") == [],
            "S3 registry has no heavy-local cost rows",
        )
        controls = {row["id"]: row["verdict"] for row in payload.get("control_verdicts", [])}
        require(errors, controls.get("control.anchor_self") == "anchor", "anchor control mismatch")
        require(errors, controls.get("control.alias_reordered_pauli_xyz") == "alias", "alias control mismatch")
        require(
            errors,
            controls.get("control.far_z_only_round2_null") == "excluded-by-first-teeth-row-frame-rank-and-six-state-separation",
            "far control mismatch",
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
        require(errors, verdict_map_from_lane(jax) == EXPECTED_VERDICTS, "jax verdict mismatch")
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
