#!/usr/bin/env python3
"""Validate geo_s9_alternative_connections_v0."""

from __future__ import annotations

import datetime as dt
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
SIM_ID = "geo_s9_alternative_connections_v0"
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_DIR = SIM_DIR / "results"
ENVELOPE = RESULT_DIR / f"{SIM_ID}_envelope_results.json"
JULIA = RESULT_DIR / f"{SIM_ID}_julia_results.json"
VALIDATOR_RESULT = RESULT_DIR / f"{SIM_ID}_validator_results.json"

sys.path.insert(0, str(ROOT))
from scripts.builder_audit_boundary import builder_audit_boundary_errors  # noqa: E402


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def require(errors: list[str], condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


def main() -> int:
    errors: list[str] = []
    require(errors, ENVELOPE.exists(), f"missing envelope: {ENVELOPE}")
    require(errors, JULIA.exists(), f"missing julia result: {JULIA}")
    payload = load(ENVELOPE) if ENVELOPE.exists() else {}
    julia = load(JULIA) if JULIA.exists() else {}
    text = json.dumps(payload, sort_keys=True).lower()

    if payload:
        require(errors, payload.get("schema_version") == "three_engine_sim_result_v1", "schema_version mismatch")
        require(errors, payload.get("sim_id") == SIM_ID, "sim_id mismatch")
        require(errors, payload.get("classification") == "scratch_diagnostic", "classification must be scratch_diagnostic")
        require(errors, payload.get("promotion_allowed") is False, "promotion_allowed must be false")
        require(errors, payload.get("formal_admission_allowed") is False, "formal_admission_allowed must be false")
        require(errors, payload.get("all_pass") is True, "all_pass must be true")
        errors.extend(builder_audit_boundary_errors(payload, SIM_DIR / "audit_verdict.md"))
        banned_word = "fix" + "ture"
        require(errors, banned_word not in text, "forbidden setup wording present")

        lineage = payload.get("parent_lineage", {})
        for parent in [
            "stack_uniqueness_map_8f4fef471",
            "geo_s2_connection_flux_foliation_v0",
            "geo_s9_quaternionic_hopf_stack_v0",
            "geo_s9_quat_path_ordered_transport_v0",
            "ratchet_s2_two_shell_flux_v0",
        ]:
            require(errors, parent in lineage, f"missing parent lineage: {parent}")
            require(errors, bool(lineage.get(parent, {}).get("envelope_sha256")), f"missing parent hash: {parent}")

        matrix = payload.get("survival_matrix", {})
        require(
            errors,
            set(matrix) == {
                "committed_hopf",
                "A_flat_dphi",
                "B_half_cos",
                "C_same_c1_non_hopf_density",
                "D_random_nonperiodic",
            },
            "survival matrix coverage mismatch",
        )
        require(errors, matrix.get("committed_hopf", {}).get("full_battery_match") is True, "committed control must pass")
        require(errors, matrix.get("A_flat_dphi", {}).get("first_failure_row") == "curvature_anchor", "flat must first fail curvature")
        require(errors, matrix.get("A_flat_dphi", {}).get("chern_number_c1_anchor") is False, "flat must fail c1")
        require(errors, matrix.get("B_half_cos", {}).get("holonomy_spectrum_anchor") is False, "half-cos holonomy control must fire")
        require(errors, matrix.get("B_half_cos", {}).get("chern_number_c1_anchor") is False, "half-cos must fail c1")
        require(errors, matrix.get("C_same_c1_non_hopf_density", {}).get("chern_number_c1_anchor") is True, "C must survive c1")
        require(errors, matrix.get("C_same_c1_non_hopf_density", {}).get("holonomy_spectrum_anchor") is False, "C must fail holonomy")
        require(errors, matrix.get("C_same_c1_non_hopf_density", {}).get("gauge_equivalent_to_committed") is False, "C must be genuine")
        require(errors, matrix.get("D_random_nonperiodic", {}).get("first_failure_row") == "smoothness_periodicity_validity", "random one-form must fail validity")

        answer = payload.get("structural_answer", {})
        require(errors, answer.get("full_battery_survivors") == [], "no alternative should survive full battery")
        require(
            errors,
            answer.get("topological_c1_co_survivors") == ["C_same_c1_non_hopf_density"],
            "C must be the only topological c1 co-survivor",
        )
        require(errors, answer.get("topological_rows") == ["chern_number_c1"], "topological row split mismatch")

        gates = payload.get("build_gates", {})
        for gate in [
            "classification_ceiling",
            "file_disjoint_packet",
            "parent_lineage_hash_bound",
            "committed_control_reproduces_all_anchors",
            "flat_connection_dies_curvature_chern",
            "rescaled_connection_holonomy_control_fires",
            "same_flux_candidate_c1_survives",
            "same_flux_candidate_geometric_rows_die",
            "random_one_form_dies_validity",
            "no_alternative_full_battery_survivor",
            "topological_cosurvivor_present",
            "z3_cvc5_agree",
            "erased_flip_controls_fire",
            "julia_leg_loaded",
            "julia_reads_no_peer_result",
            "julia_values_match_python",
            "one_to_one_tool_calls",
            "no_audit_verdict_written",
        ]:
            require(errors, gates.get(gate) is True, f"gate failed: {gate}")

        calls = payload.get("tool_calls", [])
        require(errors, [call.get("tool") for call in calls] == ["sympy", "z3", "cvc5", "Z3"], "tool call order mismatch")
        require(errors, all(call.get("load_bearing") is True for call in calls), "all claim-path tool calls must be load-bearing")

        proofs = payload.get("smt_proofs", {})
        for key in ["z3", "cvc5", "julia_z3"]:
            proof = proofs.get(key, {})
            require(errors, proof.get("ran") is True, f"{key} did not run")
            require(errors, proof.get("load_bearing") is True, f"{key} not load-bearing")
            require(errors, proof.get("real_verdict") == "unsat", f"{key} real verdict must be unsat")
            require(errors, proof.get("erased_flip_verdict") == "sat", f"{key} erased verdict must be sat")
            require(errors, proof.get("asserted_precomputed_boolean") is False, f"{key} must bind measured values")

        divergence = payload.get("divergence", {})
        require(errors, divergence.get("julia_authoritative") is True, "julia_authoritative must be true")
        require(errors, divergence.get("max_divergence") == 0.0, "max divergence must be zero")

    if julia:
        require(errors, julia.get("all_pass") is True, "julia all_pass must be true")
        require(errors, julia.get("reads_peer_result") is False, "julia reads_peer_result must be false")

    result = {
        "ok": not errors,
        "validator_ok": not errors,
        "declared_mode": payload.get("mode") if payload else None,
        "declared_modes_ok": (payload.get("mode") == "RATCHETED") if payload else False,
        "sim_id": SIM_ID,
        "result_json": str(ENVELOPE.relative_to(ROOT)),
        "errors": errors,
        "generated_at": dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    VALIDATOR_RESULT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
