#!/usr/bin/env python3
"""Packet-local validator for qit_projection_battery_v0."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from qit_projection_battery_v0_common import RESULTS, SIM_DIR, SIM_ID, V1_ENVELOPE, VIEW_MASKS, read_json, rel, sha256_file


MAIN = RESULTS / f"{SIM_ID}_results.json"
ENVELOPE = RESULTS / f"{SIM_ID}_envelope_results.json"
EXPECTED_BLOCKED = {
    "QIT_engine_admission",
    "Axis0",
    "FEP",
    "Xi/Phi0",
    "physics",
    "Lev_mesh_runtime",
    "production_perception",
    "production_ontology",
    "MMM_driver",
    "mesh_visible_projection",
}
BANNED_IDENTITY_INDICES = {5, 6}


def require(errors: list[str], condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


def validate_main(payload: dict[str, Any], errors: list[str]) -> None:
    require(errors, payload.get("classification") == "scratch_diagnostic", "main classification must be scratch_diagnostic")
    require(errors, payload.get("promotion_allowed") is False, "main promotion_allowed must be false")
    require(errors, payload.get("formal_admission_allowed") is False, "main formal_admission_allowed must be false")
    for key in (
        "host_consumed",
        "live_lev_consumed",
        "release_admission_allowed",
        "graph_mutation_allowed",
        "mesh_projection_allowed",
    ):
        require(errors, payload.get(key) is False, f"main {key} must be false")
    require(errors, payload.get("all_pass") is True, "main all_pass must be true")
    policy = payload["projection_policy"]
    require(errors, policy["direct_identity_leakage_excluded"] is True, "direct identity leakage must be excluded")
    used = {idx for mask in VIEW_MASKS.values() for idx in mask}
    require(errors, not (used & BANNED_IDENTITY_INDICES), "nominal masks must exclude loop/engine_type indices")
    core = payload["core_measurement"]
    require(errors, core["nominal"]["object_count"] == 4, "object_count must be 4")
    require(errors, core["nominal"]["view_count"] == 5, "view_count must be 5")
    require(errors, core["nominal"]["mean_heldout_accuracy"] >= 0.85, "nominal mean accuracy below gate")
    require(errors, core["controls"]["bag_erased"]["mean_heldout_accuracy"] <= 0.25, "bag erased control above chance")
    require(errors, core["controls"]["view_erased"]["mean_heldout_accuracy"] <= 0.25, "view erased control above chance")
    require(errors, all(core["gates"].values()), "core gates must all pass")
    require(errors, all(payload["gates"].values()), "main gates must all pass")
    require(errors, len(core["object_cards"]) == 4, "must emit four projection object cards")
    for card in core["object_cards"]:
        require(errors, bool(card.get("survivor_hash")), f"{card.get('object_id')}: survivor hash missing")
        require(errors, len(card.get("projection_hashes", {})) == 5, f"{card.get('object_id')}: projection hashes incomplete")
        require(errors, len(card.get("anti_hashes", {})) >= 2, f"{card.get('object_id')}: anti hashes incomplete")
    proofs = payload["crossover_proofs"]
    require(errors, proofs["z3"]["verdict"] == "unsat", "main z3 full gate must be unsat")
    require(errors, proofs["cvc5"]["verdict"] == "unsat", "main cvc5 full gate must be unsat")
    require(errors, proofs["z3"]["erased_control_verdict"] == "sat", "main z3 erased control must be sat")
    require(errors, proofs["cvc5"]["erased_control_verdict"] == "sat", "main cvc5 erased control must be sat")
    require(errors, EXPECTED_BLOCKED <= set(payload.get("blocked_consumers", [])), "main blocked_consumers incomplete")


def validate_envelope(payload: dict[str, Any], errors: list[str]) -> None:
    require(errors, payload.get("schema_version") == "three_engine_sim_result_v1", "envelope schema mismatch")
    require(errors, payload.get("classification") == "scratch_diagnostic", "envelope classification mismatch")
    require(errors, payload.get("promotion_allowed") is False, "envelope promotion_allowed must be false")
    require(errors, payload.get("formal_admission_allowed") is False, "envelope formal_admission_allowed must be false")
    require(errors, payload.get("all_pass") is True, "envelope all_pass must be true")
    for key in (
        "host_consumed",
        "live_lev_consumed",
        "release_admission_allowed",
        "graph_mutation_allowed",
        "mesh_projection_allowed",
    ):
        require(errors, payload.get(key) is False, f"envelope {key} must be false")
    engines = payload.get("engines", {})
    require(errors, set(engines) == {"julia", "jax", "pytorch"}, "envelope must include julia, jax, pytorch")
    for name, record in engines.items():
        require(errors, record.get("ran") is True, f"{name} did not run")
        require(errors, record.get("all_pass") is True, f"{name} all_pass must be true")
        require(errors, record.get("reads_peer_result") is False, f"{name} reads_peer_result must be false")
        require(errors, bool(record.get("packages_used")), f"{name} packages_used missing")
        require(errors, bool(record.get("aligned_packages_load_bearing")), f"{name} aligned load-bearing missing")
        source = Path(record["source_path"])
        if not source.is_absolute():
            source = SIM_DIR.parents[2] / source
        require(errors, source.exists(), f"{name} source path missing")
        if source.exists():
            require(errors, sha256_file(source) == record["source_sha256"], f"{name} source hash drift")
    divergence = payload["divergence"]
    require(errors, divergence["max_divergence"] == 0.0, "engine object-count divergence must be zero")
    require(errors, divergence["view_max_divergence"] == 0.0, "engine view-count divergence must be zero")
    require(errors, payload["crossover_proofs"]["z3"]["verdict"] == "unsat", "envelope z3 verdict must be unsat")
    require(errors, payload["crossover_proofs"]["cvc5"]["verdict"] == "unsat", "envelope cvc5 verdict must be unsat")
    require(errors, payload["crossover_proofs"]["julia_z3"]["verdict"] == "unsat", "envelope julia_z3 verdict must be unsat")
    require(errors, EXPECTED_BLOCKED <= set(payload.get("blocked_consumers", [])), "envelope blocked_consumers incomplete")
    lev = payload["lev_host_consumer_contract"]
    for key in ("graph_mutation_allowed", "compositor_apply_allowed", "mesh_projection_allowed", "source_boundary_mutated"):
        require(errors, lev.get(key) is False, f"Lev host contract {key} must be false")
    require(errors, V1_ENVELOPE.exists(), "parent v1 envelope must exist")


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
