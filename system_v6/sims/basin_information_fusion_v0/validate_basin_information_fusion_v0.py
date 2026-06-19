#!/usr/bin/env python3
"""Packet-local validator for basin_information_fusion_v0."""

from __future__ import annotations

import json
import sys
import math
from pathlib import Path
from typing import Any


ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
SIM_ID = "basin_information_fusion_v0"
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_DIR = SIM_DIR / "results"
DEFAULT_RESULT = RESULT_DIR / f"{SIM_ID}_envelope_results.json"
VALIDATOR_RESULT = RESULT_DIR / f"{SIM_ID}_validator_results.json"

sys.path.insert(0, str(ROOT))
from scripts.builder_audit_boundary import builder_audit_boundary_errors  # noqa: E402


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def require(errors: list[str], condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


def as_dict(value: Any, errors: list[str], name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        errors.append(f"{name} must be an object")
        return {}
    return value


def validate(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    require(errors, payload.get("schema_version") == "three_engine_sim_result_v1", "schema_version mismatch")
    require(errors, payload.get("sim_id") == SIM_ID, "sim_id mismatch")
    require(errors, payload.get("classification") == "scratch_diagnostic", "classification mismatch")
    require(errors, payload.get("promotion_allowed") is False, "promotion_allowed must be false")
    require(errors, payload.get("formal_admission_allowed") is False, "formal_admission_allowed must be false")
    require(errors, payload.get("all_pass") is True, "all_pass must be true")

    engines = as_dict(payload.get("engines"), errors, "engines")
    require(errors, set(engines) == {"julia", "jax"}, "engines must be exactly julia and jax")
    omitted = payload.get("engine_contract", {}).get("omitted_lanes", {})
    require(errors, "pytorch" in omitted, "pytorch omission must be explicit")
    for name in ("julia", "jax"):
        engine = as_dict(engines.get(name), errors, f"engines.{name}")
        require(errors, engine.get("ran") is True, f"{name}.ran must be true")
        require(errors, engine.get("reads_peer_result") is False, f"{name}.reads_peer_result must be false")
        require(errors, engine.get("reads_parent_results") is True, f"{name}.reads_parent_results must be true")
        require(errors, bool(engine.get("aligned_packages_load_bearing")), f"{name}.aligned load-bearing tools missing")

    table = payload.get("fusion_table", [])
    require(errors, isinstance(table, list) and len(table) == 7, "fusion_table must have seven transition rows")
    by_id = {row.get("transition_id"): row for row in table if isinstance(row, dict)}
    required = {"G0_to_G1", "G1_to_G2", "G2_to_G3L", "G2_to_G3R", "G2_to_G4", "G2_to_G5", "G2_to_G2_null"}
    require(errors, set(by_id) == required, "fusion transition ids drift")
    if "G0_to_G1" in by_id:
        row = by_id["G0_to_G1"]
        require(errors, row["support_count_delta"]["after_minus_before"] == 0, "G0->G1 support delta must be zero")
        require(errors, row["class_count_delta"]["before"] == 1 and row["class_count_delta"]["after"] == 3, "G0->G1 must split 1->3")
        delta = row["entropy_type_delta"]["counting_entropy_log_class_count"]["after_minus_before"]
        require(errors, abs(delta - math.log(3)) < 1e-12, "G0->G1 counting entropy delta must be log(3)")
    if "G1_to_G2" in by_id:
        row = by_id["G1_to_G2"]
        require(errors, row["class_count_delta"]["before"] == 3 and row["class_count_delta"]["after"] == 1, "G1->G2 must re-merge 3->1")
        require(errors, abs(row["entropy_type_delta"]["counting_entropy_log_class_count"]["after_minus_before"] + math.log(3)) < 1e-12, "G1->G2 must lose log(3)")
    if "G2_to_G2_null" in by_id:
        row = by_id["G2_to_G2_null"]
        require(errors, row["support_count_delta"]["after_minus_before"] == 0, "null support delta nonzero")
        require(errors, row["class_count_delta"]["after_minus_before"] == 0, "null class delta nonzero")
        require(errors, row["entropy_type_delta"]["counting_entropy_log_class_count"]["after_minus_before"] == 0.0, "null counting entropy delta nonzero")
    for tid in ("G2_to_G3L", "G2_to_G3R", "G2_to_G4", "G2_to_G5"):
        if tid in by_id:
            require(errors, "responsible_generator" in by_id[tid], f"{tid} missing responsible generator")
            require(errors, "flux_current_delta" in by_id[tid], f"{tid} missing flux/current delta")

    synth = as_dict(payload.get("synthesis_row"), errors, "synthesis_row")
    answer = as_dict(synth.get("owner_question_basin_level_answer"), errors, "synthesis.owner_question")
    require(errors, abs(answer.get("partition_refinement_information_nats", 0.0) - math.log(3)) < 1e-12, "owner answer must quantify log(3)")
    remerge = as_dict(synth.get("g2_remerge_conservation"), errors, "synthesis.g2_remerge")
    require(errors, remerge.get("holds") is True, "G2 re-merge conservation must hold")
    require(errors, remerge.get("identity_defect") == 0.0, "G2 re-merge identity defect must be zero")

    controls = as_dict(payload.get("controls"), errors, "controls")
    require(errors, controls.get("partition_anchors_byte_exact", {}).get("g0_anchor_byte_exact") is True, "byte-exact partition anchor failed")
    require(errors, controls.get("type_mixing_control", {}).get("deliberate_cross_type_sum_flagged") is True, "type-mixing control must be flagged")
    require(errors, controls.get("null_transition", {}).get("all_deltas_zero") is True, "null transition control failed")

    proofs = as_dict(payload.get("crossover_proofs"), errors, "crossover_proofs")
    for name in ("z3", "cvc5", "julia_z3"):
        proof = as_dict(proofs.get(name), errors, f"proofs.{name}")
        require(errors, proof.get("ran") is True, f"{name} did not run")
        require(errors, proof.get("load_bearing") is True, f"{name} not load-bearing")
        require(errors, proof.get("verdict") == "unsat", f"{name} identity must be unsat")
        require(errors, proof.get("erased_flip_verdict") == "sat", f"{name} erased flip must be sat")

    require(errors, payload.get("claim_path_tools") == ["Graphs", "Z3", "networkx", "sympy", "z3", "cvc5"], "claim_path_tools drift")
    require(errors, isinstance(payload.get("tool_calls"), list) and len(payload["tool_calls"]) == 6, "six tool calls required")
    gates = as_dict(payload.get("build_gates"), errors, "build_gates")
    for gate in (
        "ceilings_exact",
        "g0_g1_information_gain_log3",
        "g2_remerge_conserves_counting_information",
        "partition_anchors_byte_exact",
        "type_mixing_control_fired",
        "null_transition_zero",
        "proofs_load_bearing",
        "divergence_zero",
        "one_to_one_tool_calls",
        "capability_receipts_present",
        "no_audit_verdict_written",
    ):
        require(errors, gates.get(gate) is True, f"build gate {gate} must be true")
    return errors


def main() -> int:
    payload = json.loads(DEFAULT_RESULT.read_text(encoding="utf-8"))
    errors = validate(payload)
    errors.extend(builder_audit_boundary_errors(payload, SIM_DIR / "audit_verdict.md"))
    result = {
        "ok": not errors,
        "errors": errors,
        "result_json": rel(DEFAULT_RESULT),
        "validator": rel(Path(__file__)),
    }
    VALIDATOR_RESULT.parent.mkdir(parents=True, exist_ok=True)
    VALIDATOR_RESULT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
