#!/usr/bin/env python3
"""Validate geo_s67_alternative_topologies_v0."""

from __future__ import annotations

import datetime as dt
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
SIM_ID = "geo_s67_alternative_topologies_v0"
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_DIR = SIM_DIR / "results"
ENVELOPE = RESULT_DIR / f"{SIM_ID}_envelope_results.json"
JULIA = RESULT_DIR / f"{SIM_ID}_julia_results.json"
VALIDATOR_RESULT = RESULT_DIR / f"{SIM_ID}_validator_results.json"

sys.path.insert(0, str(ROOT))
from scripts.builder_audit_boundary import builder_audit_boundary_errors  # noqa: E402
FORBIDDEN = ROOT / "system_v6/sims/geo_s3_alternative_probe_families_v0"


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
        require(errors, FORBIDDEN.exists(), "forbidden active lane path missing; cannot prove untouched boundary")
        banned_word = "fix" + "ture"
        require(errors, banned_word not in text, "forbidden setup wording present")

        lineage = payload.get("parent_lineage", {})
        for parent in [
            "geo_s7_discrete_refinement_v0",
            "geo_s6_s7_mode_sweep_v0",
            "ring_checkerboard_support_graph_probe",
            "engine_stage_word_cost_discriminator_v0",
        ]:
            require(errors, parent in lineage, f"missing parent lineage: {parent}")
            require(errors, bool(lineage.get(parent, {}).get("result_sha256")), f"missing parent hash: {parent}")
        require(errors, lineage.get("engine_stage_word_cost_discriminator_v0", {}).get("commit", "").startswith("123b8e7d8"), "cost parent commit missing")

        matrix = payload.get("survival_matrix", {})
        require(errors, set(matrix) == {"A_path", "B_star", "C_complete", "mobius_grid"}, "survival matrix coverage mismatch")
        require(errors, matrix.get("A_path", {}).get("first_failure_row") == "closed_holonomy", "path must fail closed holonomy")
        require(errors, matrix.get("C_complete", {}).get("first_failure_row") == "locality_cost", "complete graph must fail cost row")
        require(errors, matrix.get("C_complete", {}).get("locality_cost", {}).get("observed_cost_profile", [])[-1] == 64, "complete cost 64 control missing")
        require(errors, matrix.get("mobius_grid", {}).get("first_failure_row") == "lens_quotient_commensurability", "Mobius row must report computed lens failure")
        require(errors, payload.get("structural_answer", {}).get("full_battery_survivors") == [], "no alternative should survive full battery")

        gates = payload.get("build_gates", {})
        for gate in [
            "classification_ceiling",
            "file_disjoint_packet",
            "parent_lineage_hash_bound",
            "committed_ring_grid_anchor_loaded",
            "complete_graph_cost_control_fires",
            "path_closed_holonomy_killed",
            "mobius_twist_computed",
            "smt_agreement",
            "erased_flip_controls_fire",
            "julia_leg_loaded",
            "julia_python_graph_hash_match",
            "one_to_one_tool_calls",
        ]:
            require(errors, gates.get(gate) is True, f"gate failed: {gate}")

        calls = payload.get("tool_calls", [])
        require(errors, sorted(call.get("tool") for call in calls) == sorted(payload.get("claim_path_tools", [])), "one-to-one tool call mismatch")
        require(errors, all(call.get("load_bearing") is True for call in calls), "all top-level tool calls must be load-bearing")

        proofs = payload.get("crossover_proofs", {})
        for key in ["z3", "cvc5", "julia_z3"]:
            proof = proofs.get(key, {})
            require(errors, proof.get("ran") is True, f"{key} did not run")
            require(errors, proof.get("load_bearing") is True, f"{key} not load-bearing")
            require(errors, proof.get("verdict") == "unsat", f"{key} verdict must be unsat")
            require(errors, proof.get("erased_flip_detected") is True, f"{key} erased flip must fire")
            require(errors, proof.get("asserted_precomputed_boolean") is False, f"{key} must not assert a precomputed boolean")

        divergence = payload.get("divergence", {})
        require(errors, divergence.get("julia_authoritative") is True, "julia_authoritative must be true")
        require(errors, divergence.get("max_divergence") == 0.0, "max_divergence must be zero")

    if julia:
        require(errors, julia.get("all_pass") is True, "julia all_pass must be true")
        require(errors, julia.get("reads_peer_result") is False, "julia reads_peer_result must be false")

    result = {
        "ok": not errors,
        "validator_ok": not errors,
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
