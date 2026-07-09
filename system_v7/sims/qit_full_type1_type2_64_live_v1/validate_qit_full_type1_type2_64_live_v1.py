#!/usr/bin/env python3
"""Packet-local validator for qit_full_type1_type2_64_live_v1."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from qit_full_type1_type2_64_live_v1_common import RESULTS, SIM_ID, read_json, rel


MAIN = RESULTS / f"{SIM_ID}_results.json"
ENVELOPE = RESULTS / f"{SIM_ID}_envelope_results.json"


def require(errors: list[str], condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


def validate_main(payload: dict[str, Any], errors: list[str]) -> None:
    summary = payload["matrix64_schedule"]
    require(errors, payload.get("classification") == "scratch_diagnostic", "main classification must be scratch_diagnostic")
    require(errors, payload.get("promotion_allowed") is False, "main promotion_allowed must be false")
    require(errors, payload.get("formal_admission_allowed") is False, "main formal_admission_allowed must be false")
    require(errors, summary["slot_count"] == 64, "slot_count must be 64")
    require(errors, summary["macro_stage_count"] == 16, "macro_stage_count must be 16")
    require(errors, summary["substage_count_per_macro"] == 4, "substage_count_per_macro must be 4")
    require(errors, summary["type1_slots"] == 32, "type1_slots must be 32")
    require(errors, summary["type2_slots"] == 32, "type2_slots must be 32")
    require(errors, summary["chart_locked_slots"] == 16, "chart_locked_slots must be 16")
    require(errors, summary["runtime_probe_slots"] == 48, "runtime_probe_slots must be 48")
    formation = payload["core_measurement"]["ordered_object_formation"]
    require(errors, formation["ordered_accuracy"] == 1.0, "ordered object formation must be perfect in finite scout")
    require(errors, formation["min_entropy_drop_bits"] > 0, "entropy drop must be positive")
    require(errors, formation["all_entropy_gradients_monotone"], "entropy gradients must be monotone nonincreasing")
    controls = payload["core_measurement"]["negative_controls"]
    require(errors, controls["bag_topology"]["unique_signature_count"] == 1, "bag topology control must collapse all objects")
    require(errors, controls["first_static"]["unique_signature_count"] == 1, "first static control must collapse all objects")
    cards = payload["core_measurement"]["object_cards"]
    require(errors, len(cards) == formation["object_count"], "object card count must equal object count")
    for card in cards:
        require(errors, bool(card.get("survivor_hash")), f"{card.get('object_id')}: survivor hash missing")
        require(errors, len(card.get("anti_hashes", {})) >= 4, f"{card.get('object_id')}: anti hashes incomplete")
    proofs = payload["crossover_proofs"]
    require(errors, proofs["z3"]["verdict"] == "unsat", "main z3 full gate must be unsat")
    require(errors, proofs["cvc5"]["verdict"] == "unsat", "main cvc5 full gate must be unsat")
    require(errors, proofs["z3"]["erased_control_verdict"] == "sat", "main z3 erased control must be sat")
    require(errors, proofs["cvc5"]["erased_control_verdict"] == "sat", "main cvc5 erased control must be sat")


def validate_envelope(payload: dict[str, Any], errors: list[str]) -> None:
    require(errors, payload.get("schema_version") == "three_engine_sim_result_v1", "envelope schema mismatch")
    require(errors, payload.get("classification") == "scratch_diagnostic", "envelope classification mismatch")
    require(errors, payload.get("promotion_allowed") is False, "envelope promotion_allowed must be false")
    require(errors, payload.get("formal_admission_allowed") is False, "envelope formal_admission_allowed must be false")
    require(errors, payload.get("host_consumed") is False, "envelope host_consumed must be false")
    require(errors, payload.get("live_lev_consumed") is False, "envelope live_lev_consumed must be false")
    require(errors, payload.get("release_admission_allowed") is False, "envelope release_admission_allowed must be false")
    require(errors, payload.get("graph_mutation_allowed") is False, "envelope graph_mutation_allowed must be false")
    require(errors, payload.get("mesh_projection_allowed") is False, "envelope mesh_projection_allowed must be false")
    require(errors, payload.get("evidence_grade") == "scratch_diagnostic_measurement", "envelope evidence_grade mismatch")
    engines = payload.get("engines", {})
    require(errors, set(engines) == {"julia", "jax", "pytorch"}, "envelope must include julia, jax, pytorch")
    for name, record in engines.items():
        require(errors, record.get("ran") is True, f"{name} did not run")
        require(errors, record.get("reads_peer_result") is False, f"{name} reads_peer_result must be false")
        require(errors, bool(record.get("packages_used")), f"{name} packages_used missing")
        require(errors, bool(record.get("aligned_packages_load_bearing")), f"{name} aligned load-bearing missing")
    require(errors, payload["divergence"]["max_divergence"] == 0.0, "engine survivor object count divergence must be zero")
    require(errors, payload["crossover_proofs"]["z3"]["verdict"] == "unsat", "envelope z3 verdict must be unsat")
    require(errors, payload["crossover_proofs"]["cvc5"]["verdict"] == "unsat", "envelope cvc5 verdict must be unsat")
    require(errors, bool(payload.get("blocked_consumers")), "blocked_consumers must be present")
    lev_contract = payload.get("lev_host_consumer_contract", {})
    require(errors, isinstance(lev_contract, dict), "lev_host_consumer_contract must be present")
    if isinstance(lev_contract, dict):
        require(errors, lev_contract.get("truth_state") == "proposed", "lev truth_state must be proposed")
        require(errors, lev_contract.get("evidence_kind") == "measurement", "lev evidence_kind must be measurement")
        require(
            errors,
            lev_contract.get("decision_ceiling") == "accepted_as_evidence_only",
            "lev decision_ceiling must be accepted_as_evidence_only",
        )
        for key in (
            "graph_mutation_allowed",
            "compositor_apply_allowed",
            "mesh_projection_allowed",
            "source_boundary_mutated",
            "cr_object_id_is_lev_entity_id",
        ):
            require(errors, lev_contract.get(key) is False, f"lev {key} must be false")


def main() -> int:
    errors: list[str] = []
    if not MAIN.exists():
        errors.append(f"missing {rel(MAIN)}")
    if not ENVELOPE.exists():
        errors.append(f"missing {rel(ENVELOPE)}")
    if not errors:
        validate_main(read_json(MAIN), errors)
        validate_envelope(read_json(ENVELOPE), errors)
    ok = not errors
    print(json.dumps({"ok": ok, "errors": errors, "main": rel(MAIN), "envelope": rel(ENVELOPE)}, indent=2, sort_keys=True))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
