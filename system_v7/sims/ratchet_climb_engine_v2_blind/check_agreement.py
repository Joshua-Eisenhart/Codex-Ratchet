#!/usr/bin/env python3
"""Agreement envelope for ratchet_climb_engine_v2_blind."""

from __future__ import annotations

import json
from pathlib import Path

import ratchet_climb_core as core

classification = "scratch_diagnostic"
promotion_allowed = False
formal_admission_allowed = False
TOOL_MANIFEST = {"python_stdlib": {"tried": True, "used": True, "reason": "supportive parity comparison and envelope emission"}}
TOOL_INTEGRATION_DEPTH = {"python_stdlib": "supportive"}


def load(name: str) -> dict:
    return core.load_json(core.RESULTS / f"ratchet_climb_engine_v2_blind_{name}_results.json")


def main() -> int:
    results = {name: load(name) for name in ("numpy", "jax", "julia")}
    failures = []
    frontiers = {name: row["frontier_by_variant"] for name, row in results.items()}
    if len({json.dumps(v, sort_keys=True) for v in frontiers.values()}) != 1:
        failures.append(f"frontier mismatch: {frontiers}")
    for name, row in results.items():
        if row.get("classification") != "scratch_diagnostic" or row.get("promotion_allowed") is not False:
            failures.append(f"{name}: classification/promotion contract failed")
        if row.get("capstone_status") != "DRAFT_UNAUDITED" or row.get("all_pass") is not True:
            failures.append(f"{name}: capstone/all_pass failed")
    canonical = results["numpy"]["frontier_by_variant"]
    facts_used = {run["variant_id"]: run["blinded_selector"]["facts_used"] for run in results["numpy"]["run_results"]}
    envelope = {
        "schema_version": "three_engine_sim_result_v1",
        "sim_id": core.SIM_ID,
        "engine": "agreement_envelope",
        "generated_at": core.now_iso(),
        "classification": "scratch_diagnostic",
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "capstone_status": "DRAFT_UNAUDITED",
        "all_pass": not failures,
        "frontier_by_variant": canonical,
        "any_blinded_search_reached_beyond_rung4": any(v > 4 for v in canonical.values()),
        "facts_values_used_for_lifts": facts_used,
        "engine_frontiers": frontiers,
        "failures": failures,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "divergence_log": ["agreement envelope only; see per-engine native derivations"],
    }
    out = core.RESULTS / "ratchet_climb_engine_v2_blind_three_engine_results.json"
    core.write_json(out, envelope)
    print(json.dumps({"all_pass": envelope["all_pass"], "frontier_by_variant": canonical}, sort_keys=True))
    return 0 if envelope["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
