#!/usr/bin/env python3
"""Packet-local validator for qit_bidirectional_science_type1_type2_v0."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from qit_bidirectional_science_type1_type2_v0_common import (
    BLOCKED_CONSUMERS,
    OBJECT_CARD,
    RESULTS,
    SIM_DIR,
    SIM_ID,
    V43_VALIDATION,
    read_json,
    rel,
    sha256_file,
)

MAIN = RESULTS / f"{SIM_ID}_results.json"
ENVELOPE = RESULTS / f"{SIM_ID}_envelope_results.json"


def require(errors: list[str], condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


def validate_main(payload: dict[str, Any], errors: list[str]) -> None:
    require(errors, payload.get("classification") == "scratch_diagnostic", "main classification mismatch")
    require(errors, payload.get("promotion_allowed") is False, "main promotion_allowed must be false")
    require(errors, payload.get("formal_admission_allowed") is False, "main formal_admission_allowed must be false")
    require(errors, payload.get("all_pass") is True, "main all_pass must be true")
    core = payload["core_measurement"]
    require(errors, core["comparison"]["trial_count"] == 40, "must run 40 paired method trials")
    require(errors, core["type1"]["nominal"]["trial_count"] == 20, "Type-1 must run 20 trials")
    require(errors, core["type2"]["nominal"]["trial_count"] == 20, "Type-2 must run 20 trials")
    require(errors, core["type1"]["nominal"]["accuracy"] == 1.0, "Type-1 nominal accuracy must be 1.0")
    require(errors, core["type1"]["controls"]["wrong_candidate"]["accepted_rate"] <= 0.25, "Type-1 wrong candidate above chance")
    require(errors, core["type2"]["nominal"]["accuracy"] >= 0.85, "Type-2 nominal below gate")
    require(errors, core["type2"]["controls"]["bag_erased"]["accuracy"] <= 0.25, "Type-2 bag control above chance")
    require(errors, core["type2"]["controls"]["view_erased"]["accuracy"] <= 0.25, "Type-2 view-erased control above chance")
    counts = core["comparison"]["unique_win_table"]["counts"]
    require(errors, counts == {"shared_fail": 0, "shared_win": 18, "type1_only": 2, "type2_only": 0}, "unique-win table drift")
    require(errors, all(payload["gates"].values()), "main gates must all pass")
    proofs = payload["crossover_proofs"]
    require(errors, proofs["z3"]["verdict"] == "unsat", "main z3 verdict must be unsat")
    require(errors, proofs["cvc5"]["verdict"] == "unsat", "main cvc5 verdict must be unsat")
    require(errors, set(BLOCKED_CONSUMERS) <= set(payload.get("blocked_consumers", [])), "main blocked consumers incomplete")


def validate_envelope(payload: dict[str, Any], errors: list[str]) -> None:
    require(errors, payload.get("schema_version") == "three_engine_sim_result_v1", "envelope schema mismatch")
    require(errors, payload.get("all_pass") is True, "envelope all_pass must be true")
    require(errors, payload.get("promotion_allowed") is False, "envelope promotion_allowed must be false")
    require(errors, payload.get("formal_admission_allowed") is False, "envelope formal_admission_allowed must be false")
    require(errors, bool(payload.get("tool_intent", {}).get("claim_classes")), "tool_intent.claim_classes required")
    engines = payload.get("engines", {})
    require(errors, set(engines) == {"julia", "jax", "pytorch"}, "envelope must include julia/jax/pytorch")
    for name, record in engines.items():
        require(errors, record.get("ran") is True, f"{name} did not run")
        require(errors, record.get("all_pass") is True, f"{name} all_pass must be true")
        require(errors, record.get("reads_peer_result") is False, f"{name} reads_peer_result must be false")
        require(errors, bool(record.get("aligned_packages_load_bearing")), f"{name} aligned load-bearing missing")
        source = Path(record["source_path"])
        if not source.is_absolute():
            source = SIM_DIR.parents[2] / source
        require(errors, source.exists(), f"{name} source missing")
        if source.exists():
            require(errors, sha256_file(source) == record["source_sha256"], f"{name} source hash drift")
    require(errors, payload["divergence"]["max_divergence"] == 0.0, "object-count divergence must be zero")
    require(errors, payload["divergence"]["trial_max_divergence"] == 0.0, "trial-count divergence must be zero")
    require(errors, payload["divergence"]["trial_values"] == {"jax": 40.0, "julia": 40.0, "pytorch": 40.0}, "trial values drift")
    require(errors, payload["crossover_proofs"]["z3"]["verdict"] == "unsat", "envelope z3 verdict must be unsat")
    require(errors, payload["crossover_proofs"]["cvc5"]["verdict"] == "unsat", "envelope cvc5 verdict must be unsat")
    require(errors, payload["crossover_proofs"]["julia_z3"]["verdict"] == "unsat", "envelope julia_z3 verdict must be unsat")
    require(errors, OBJECT_CARD.exists(), "v4.3 object card missing")
    require(errors, V43_VALIDATION.exists(), "v4.3 validation missing")
    require(errors, read_json(V43_VALIDATION).get("ok") is True, "v4.3 validation must be ok")
    lev = payload["lev_host_consumer_contract"]
    for key in ("graph_mutation_allowed", "compositor_apply_allowed", "mesh_projection_allowed", "source_boundary_mutated"):
        require(errors, lev.get(key) is False, f"Lev host {key} must be false")
    require(errors, set(BLOCKED_CONSUMERS) <= set(payload.get("blocked_consumers", [])), "envelope blocked consumers incomplete")


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
