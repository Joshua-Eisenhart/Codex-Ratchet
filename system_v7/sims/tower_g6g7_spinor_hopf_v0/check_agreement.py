#!/usr/bin/env python3
"""Three-engine agreement checker for tower_g6g7_spinor_hopf_v0."""

from __future__ import annotations

import hashlib
import json
import pathlib
from datetime import datetime, timezone

SIM_ID = "tower_g6g7_spinor_hopf_v0"
HERE = pathlib.Path(__file__).resolve().parent
RESULT_DIR = HERE / "results"
OUT_PATH = RESULT_DIR / f"{SIM_ID}_three_engine_results.json"
ENGINES = ("julia", "jax", "pytorch")
TOL = 1.0e-9

classification = "scratch_diagnostic"
promotion_allowed = False
formal_admission_allowed = False
TOOL_MANIFEST = {"python_json": {"tried": True, "used": True, "reason": "supportive envelope readback from completed engine receipts"}}
TOOL_INTEGRATION_DEPTH = {"python_json": "supportive"}


def load(engine: str) -> dict:
    return json.loads((RESULT_DIR / f"{SIM_ID}_{engine}_results.json").read_text(encoding="utf-8"))


def max_divergence(legs: dict[str, dict]) -> tuple[float, str]:
    worst = 0.0
    worst_key = ""
    keys = legs["julia"]["shared_scalars"].keys()
    for key in keys:
        vals = [float(legs[e]["shared_scalars"][key]) for e in ENGINES]
        diff = max(vals) - min(vals)
        if diff > worst:
            worst = diff
            worst_key = key
    return worst, worst_key


def lint_failures(legs: dict[str, dict]) -> list[str]:
    failures = []
    for engine, payload in legs.items():
        if payload.get("classification") != "scratch_diagnostic":
            failures.append(f"{engine}: classification")
        if payload.get("promotion_allowed") is not False:
            failures.append(f"{engine}: promotion_allowed")
        if payload.get("formal_admission_allowed") is not False:
            failures.append(f"{engine}: formal_admission_allowed")
        if not payload.get("TOOL_MANIFEST"):
            failures.append(f"{engine}: TOOL_MANIFEST")
        if not payload.get("TOOL_INTEGRATION_DEPTH"):
            failures.append(f"{engine}: TOOL_INTEGRATION_DEPTH")
        if payload.get("reads_peer_result") is not False:
            failures.append(f"{engine}: reads_peer_result")
    return failures


def main() -> int:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    legs = {engine: load(engine) for engine in ENGINES}
    max_diff, worst_key = max_divergence(legs)
    lint = lint_failures(legs)
    controls = {
        "rho_only_control_fails_to_separate_720_all_engines": all(legs[e]["controls"]["rho_only_control_fails_to_separate_720"] for e in ENGINES),
        "flat_plain_s2_control_kills_connection_witness_all_engines": all(legs[e]["controls"]["flat_plain_s2_control_kills_connection_witness"] for e in ENGINES),
        "label_shuffle_preserves_density_all_engines": all(legs[e]["controls"]["label_shuffle_preserves_density"] for e in ENGINES),
    }
    all_pass = all(legs[e]["all_pass"] is True for e in ENGINES) and max_diff < TOL and not lint and all(controls.values())
    source_path = str(pathlib.Path(__file__).resolve())
    result = {
        "schema_version": "three_engine_sim_result_v1",
        "sim_id": SIM_ID,
        "classification": classification,
        "promotion_allowed": promotion_allowed,
        "formal_admission_allowed": formal_admission_allowed,
        "all_pass": all_pass,
        "created_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "claim": "One rerunnable G6/G7 rung: rho-first spinor lift with 720-degree witness plus Hopf torus/connection holonomy witness.",
        "claim_ceiling": "scratch_diagnostic G6/G7 envelope only; no formal admission, tower promotion, bridge, Axis, or physics claim.",
        "engine_contract": {"mode": "all_three_full_sims", "lanes": list(ENGINES), "controller_reads_engine_results_after_lanes": True},
        "canon_runtime": {"semantic_owner": "julia", "consumer_policy": "three independent local calculations; JSON receipts compared only by controller"},
        "engines": {e: {"ran": True, "source_path": legs[e]["source_path"], "source_sha256": legs[e]["source_sha256"], "result_path": str(RESULT_DIR / f"{SIM_ID}_{e}_results.json"), "packages_used": legs[e]["packages_used"]} for e in ENGINES},
        "witness_values": {
            "spinor_separation_2pi": {e: legs[e]["witnesses"]["spinor_separation_2pi"] for e in ENGINES},
            "spinor_separation_4pi": {e: legs[e]["witnesses"]["spinor_separation_4pi"] for e in ENGINES},
            "rho_path_residual_identical_readouts": {e: legs[e]["witnesses"]["rho_path_residual_identical_readouts"] for e in ENGINES},
            "holonomy_2pi_class": {e: legs[e]["witnesses"]["holonomy_2pi_class"] for e in ENGINES},
            "holonomy_4pi_class": {e: legs[e]["witnesses"]["holonomy_4pi_class"] for e in ENGINES},
            "hopf_eta_rows": legs["julia"]["hopf_connection"]["eta_rows"],
        },
        "controls": controls,
        "parity": {"agreement_ok": max_diff < TOL, "max_divergence": max_diff, "worst_key": worst_key, "engines": list(ENGINES)},
        "lint": {"failures": lint, "failure_count": len(lint)},
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "controller_source_path": source_path,
        "controller_source_sha256": hashlib.sha256(pathlib.Path(source_path).read_bytes()).hexdigest(),
        "engine_result_paths": {e: str(RESULT_DIR / f"{SIM_ID}_{e}_results.json") for e in ENGINES},
    }
    OUT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"all_pass": all_pass, "parity_max_diff": max_diff, "lint_failures": len(lint), "out": str(OUT_PATH)}, sort_keys=True))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
