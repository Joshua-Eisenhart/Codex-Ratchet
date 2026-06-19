#!/usr/bin/env python3
"""Packet-local validator for round3_s5_heavy_discriminator_v0."""

from __future__ import annotations

import datetime as dt
import json
from pathlib import Path
from typing import Any


ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
SIM_ID = "round3_s5_heavy_discriminator_v0"
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_DIR = SIM_DIR / "results"
ENVELOPE = RESULT_DIR / f"{SIM_ID}_envelope_results.json"
JAX = RESULT_DIR / f"{SIM_ID}_jax_results.json"
JULIA = RESULT_DIR / f"{SIM_ID}_julia_results.json"
PYTORCH = RESULT_DIR / f"{SIM_ID}_pytorch_results.json"
VALIDATOR_RESULT = RESULT_DIR / f"{SIM_ID}_validator_results.json"

EXPECTED_VERDICTS = {
    "S5.R3.1_alpha_mix_rotation_contraction__alpha_1_4": "excluded-by-mirror-structure-and-N01-full-signature",
    "S5.R3.1_alpha_mix_rotation_contraction__alpha_1_2": "excluded-by-mirror-structure-and-N01-full-signature",
    "S5.R3.1_alpha_mix_rotation_contraction__alpha_3_4": "excluded-by-mirror-structure-and-N01-full-signature",
    "S5.R3.2_committed_coeff_epsilon__plus_1_20": "excluded-by-fixed-point-basin-and-N01-gap",
    "S5.R3.2_committed_coeff_epsilon__minus_1_20": "excluded-by-fixed-point-basin-and-N01-gap",
    "S5.R3.3_nonunital_weak_shift__plus_1_20": "excluded-by-validity-fixed-point-and-quotient-row",
    "S5.R3.3_nonunital_weak_shift__minus_1_20": "excluded-by-validity-fixed-point-and-quotient-row",
    "S5.R3.5_basin_preserving_null": "excluded-by-time-flow-N01-row-after-quotient-survival",
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
    for path in [ENVELOPE, JAX, JULIA, PYTORCH, SIM_DIR / "build_card.md"]:
        require(errors, path.exists(), f"missing required file: {path.relative_to(ROOT)}")

    envelope = load(ENVELOPE) if ENVELOPE.exists() else {}
    jax = load(JAX) if JAX.exists() else {}
    julia = load(JULIA) if JULIA.exists() else {}
    pytorch = load(PYTORCH) if PYTORCH.exists() else {}

    if envelope:
        require(errors, envelope.get("schema_version") == "three_engine_sim_result_v1", "schema_version mismatch")
        require(errors, envelope.get("sim_id") == SIM_ID, "sim_id mismatch")
        require(errors, envelope.get("classification") == "scratch_diagnostic", "classification mismatch")
        require(errors, envelope.get("promotion_allowed") is False, "promotion_allowed must be false")
        require(errors, envelope.get("formal_admission_allowed") is False, "formal_admission_allowed must be false")
        require(errors, envelope.get("all_pass") is True, "all_pass must be true")
        require(errors, envelope.get("engine_contract", {}).get("mode") == "julia_canon_jax_with_pytorch_graph", "engine mode mismatch")
        require(errors, set(envelope.get("engines", {})) == {"julia", "jax", "pytorch"}, "expected all three engine records")
        require(errors, verdict_map_from_table(envelope) == EXPECTED_VERDICTS, "candidate verdict table mismatch")
        for row in envelope.get("candidate_verdict_table", []):
            n01 = row.get("n01_full_signature_comparison", {})
            require(errors, n01.get("operator") == "Fi_R_x", f"missing N01 operator for {row.get('candidate')}")
            require(errors, len(n01.get("rows", {})) == 8, f"missing complete N01 rows for {row.get('candidate')}")
            require(errors, n01.get("first_difference", {}).get("field") is not None, f"missing N01 first difference for {row.get('candidate')}")
        require(errors, envelope.get("negative", {}).get("known_cosurvivors_minted") == [], "must not mint co-survivors")
        gates = envelope.get("build_gates", {})
        for gate in [
            "julia_lane_pass",
            "jax_lane_pass",
            "pytorch_lane_pass",
            "three_engine_verdicts_match",
            "expected_eight_row_verdicts",
            "registry_commit_bound",
            "build_card_copied",
            "classification_ceiling",
            "z3_cvc5_agree",
            "julia_z3_agrees",
            "flip_controls_fire",
            "pytorch_graph_rows_scoped",
            "chart_relative_graph_rows",
            "no_cosurvivors_minted",
        ]:
            require(errors, gates.get(gate) is True, f"gate failed: {gate}")
        proofs = envelope.get("crossover_proofs", {})
        require(errors, proofs.get("z3", {}).get("verdict") == "unsat", "z3 proof must be unsat")
        require(errors, proofs.get("cvc5", {}).get("verdict") == "unsat", "cvc5 proof must be unsat")
        require(errors, proofs.get("julia_z3", {}).get("verdict") == "unsat", "julia_z3 proof must be unsat")
        require(errors, proofs.get("z3", {}).get("flip_control_verdict") == "sat", "z3 flip must be sat")
        require(errors, proofs.get("cvc5", {}).get("flip_control_verdict") == "sat", "cvc5 flip must be sat")
        require(errors, proofs.get("julia_z3", {}).get("flip_control_verdict") == "sat", "julia_z3 flip must be sat")
        graph_rows = envelope.get("basin_graph_rows", {})
        require(errors, graph_rows, "basin graph rows missing")
        require(errors, all(row.get("state_count") == 33 for row in graph_rows.values()), "basin graph rows must use 33 cells")

    for name, payload in [("jax", jax), ("julia", julia), ("pytorch", pytorch)]:
        if payload:
            require(errors, payload.get("all_pass") is True, f"{name} all_pass false")
            require(errors, payload.get("reads_peer_result") is False, f"{name} must not read peer result")
            require(errors, verdict_map(payload) == EXPECTED_VERDICTS, f"{name} verdict mismatch")
            require(errors, payload.get("classification") == "scratch_diagnostic", f"{name} classification mismatch")
            require(errors, payload.get("promotion_allowed") is False, f"{name} promotion_allowed mismatch")
            if name in {"jax", "pytorch"}:
                for row in payload.get("candidate_verdicts", []):
                    n01 = row.get("n01_full_signature_comparison", {})
                    require(errors, len(n01.get("rows", {})) == 8, f"{name} missing complete N01 rows for {row.get('candidate')}")

    result = {
        "ok": not errors,
        "validator_ok": not errors,
        "sim_id": SIM_ID,
        "result_json": str(ENVELOPE.relative_to(ROOT)),
        "errors": errors,
        "verdicts": verdict_map_from_table(envelope) if envelope else {},
        "generated_at": dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    VALIDATOR_RESULT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
