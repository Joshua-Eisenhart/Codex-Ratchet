#!/usr/bin/env python3
"""Packet-local validator for round3_s6s7_heavy_discriminator_v0."""

from __future__ import annotations

import datetime as dt
import json
from pathlib import Path
from typing import Any


ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
SIM_ID = "round3_s6s7_heavy_discriminator_v0"
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_DIR = SIM_DIR / "results"
ENVELOPE = RESULT_DIR / f"{SIM_ID}_envelope_results.json"
JAX = RESULT_DIR / f"{SIM_ID}_jax_results.json"
JULIA = RESULT_DIR / f"{SIM_ID}_julia_results.json"
PYTORCH = RESULT_DIR / f"{SIM_ID}_pytorch_results.json"
VALIDATOR_RESULT = RESULT_DIR / f"{SIM_ID}_validator_results.json"

EXPECTED_VERDICTS = {
    "S67.R3.1_mobius_reflection_shifted": "excluded-by-lens-quotient-commensurability",
    "S67.R3.2_klein_double_twist": "excluded-by-cover-orbit-well-definedness-then-lens-row",
    "S67.R3.3_shear_torus": "excluded-by-lens-descent-and-S6-leakage-taxonomy",
    "S67.R3.4_cycle_with_one_chord": "excluded-by-bounded-word-cost-and-cycle-holonomy",
    "S67.R3.5_ladder_prism_graph": "excluded-by-locality-cost-plus-leakage-class-row",
}
EXPECTED_N = [8, 16, 32]


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def require(errors: list[str], condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


def verdict_map_from_table(rows: list[dict[str, Any]]) -> dict[str, str]:
    return {row["candidate"]: row["final_verdict"] for row in rows}


def verdict_map_from_lane(payload: dict[str, Any]) -> dict[str, str]:
    return {row["candidate"]: row["verdict"] for row in payload.get("candidate_verdicts", [])}


def main() -> int:
    errors: list[str] = []
    for path in [ENVELOPE, JAX, JULIA, PYTORCH, SIM_DIR / "build_card.md", SIM_DIR / "audit_verdict.md"]:
        require(errors, path.exists(), f"missing required file: {path.relative_to(ROOT)}")

    payload = load(ENVELOPE) if ENVELOPE.exists() else {}
    jax = load(JAX) if JAX.exists() else {}
    julia = load(JULIA) if JULIA.exists() else {}
    pytorch = load(PYTORCH) if PYTORCH.exists() else {}

    if payload:
        require(errors, payload.get("schema_version") == "three_engine_sim_result_v1", "schema_version mismatch")
        require(errors, payload.get("sim_id") == SIM_ID, "sim_id mismatch")
        require(errors, payload.get("classification") == "scratch_diagnostic", "classification must be scratch_diagnostic")
        require(errors, payload.get("promotion_allowed") is False, "promotion_allowed must be false")
        require(errors, payload.get("formal_admission_allowed") is False, "formal_admission_allowed must be false")
        require(errors, payload.get("all_pass") is True, "all_pass must be true")
        require(errors, payload.get("engine_contract", {}).get("mode") == "julia_canon_jax_with_pytorch_graph", "engine mode mismatch")
        require(errors, sorted(payload.get("engines", {})) == ["jax", "julia", "pytorch"], "all three engines must be present")

        gates = payload.get("build_gates", {})
        for gate in [
            "julia_lane_pass",
            "jax_lane_pass",
            "pytorch_lane_pass",
            "three_engine_verdicts_match",
            "expected_five_row_verdicts",
            "registry_commit_bound",
            "build_card_copied",
            "classification_ceiling",
            "explicit_mapping_certificate_present",
            "all_rows_swept_N_8_16_32",
            "z3_cvc5_agree",
            "julia_z3_agrees",
            "flip_controls_fire",
            "pytorch_graph_claim_scoped",
            "no_cosurvivors_minted",
            "no_size_relative_labels",
        ]:
            require(errors, gates.get(gate) is True, f"gate failed: {gate}")

        table = payload.get("final_verdict_table", [])
        require(errors, verdict_map_from_table(table) == EXPECTED_VERDICTS, "final verdict table mismatch")
        for row in table:
            require(errors, row.get("N_sweep") == EXPECTED_N, f"N sweep mismatch for {row.get('candidate')}")
            require(errors, row.get("separating_sizes") == EXPECTED_N, f"separating sizes mismatch for {row.get('candidate')}")
            require(errors, row.get("co_survivor") is False, f"co-survivor should not be minted for {row.get('candidate')}")
            require(errors, row.get("size_relative") is False, f"size-relative label should not appear for {row.get('candidate')}")
            require(errors, bool(row.get("citable_witness")), f"missing citable witness for {row.get('candidate')}")

        cert = payload.get("positive", {}).get("explicit_isomorphism_certificate", {})
        require(errors, cert.get("verdict") == "alias", "explicit certificate verdict must be alias")
        require(errors, cert.get("edge_by_edge_verified") is True, "explicit certificate must verify edge-by-edge")
        require(errors, len(cert.get("mapping_anchor_to_reparameterized", {})) == 8, "mapping certificate must cover 8 vertices")
        require(errors, cert.get("mapped_edge_set_sha256") == cert.get("target_edge_set_sha256"), "mapped and target edge hashes must match")

        proofs = payload.get("crossover_proofs", {})
        require(errors, proofs.get("z3", {}).get("verdict") == "unsat", "z3 proof must be unsat")
        require(errors, proofs.get("cvc5", {}).get("verdict") == "unsat", "cvc5 proof must be unsat")
        require(errors, proofs.get("julia_z3", {}).get("verdict") == "unsat", "julia_z3 proof must be unsat")
        require(errors, proofs.get("z3", {}).get("flip_control_verdict") == "sat", "z3 flip must be sat")
        require(errors, proofs.get("cvc5", {}).get("flip_control_verdict") == "sat", "cvc5 flip must be sat")
        require(errors, proofs.get("julia_z3", {}).get("flip_control_verdict") == "sat", "julia_z3 flip must be sat")

    for name, payload_lane in [("jax", jax), ("julia", julia), ("pytorch", pytorch)]:
        if payload_lane:
            require(errors, payload_lane.get("all_pass") is True, f"{name} lane all_pass false")
            require(errors, verdict_map_from_lane(payload_lane) == EXPECTED_VERDICTS, f"{name} verdict mismatch")
            require(errors, payload_lane.get("reads_peer_result") is False, f"{name} must not read peer result")

    result = {
        "ok": not errors,
        "validator_ok": not errors,
        "sim_id": SIM_ID,
        "result_json": str(ENVELOPE.relative_to(ROOT)),
        "errors": errors,
        "verdicts": verdict_map_from_table(payload.get("final_verdict_table", [])) if payload else {},
        "generated_at": dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    VALIDATOR_RESULT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
