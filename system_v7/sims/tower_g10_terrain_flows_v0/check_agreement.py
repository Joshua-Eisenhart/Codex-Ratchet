#!/usr/bin/env python3
from __future__ import annotations

import hashlib, json, pathlib
from datetime import datetime, timezone

SIM_ID = "tower_g10_terrain_flows_v0"
HERE = pathlib.Path(__file__).resolve().parent
RESULTS = HERE / "results"
OUT = RESULTS / f"{SIM_ID}_three_engine_results.json"


def load(engine: str) -> dict:
    return json.loads((RESULTS / f"{SIM_ID}_{engine}_results.json").read_text())


def lint_payload(payload: dict) -> list[str]:
    errors = []
    for key in ("classification", "TOOL_MANIFEST", "TOOL_INTEGRATION_DEPTH"):
        if key not in payload:
            errors.append(f"{payload.get('engine')}:missing_{key}")
    if payload.get("classification") != "scratch_diagnostic":
        errors.append(f"{payload.get('engine')}:classification_not_scratch")
    if payload.get("promotion_allowed") is not False:
        errors.append(f"{payload.get('engine')}:promotion_allowed_not_false")
    if payload.get("terrain_count") != 8:
        errors.append(f"{payload.get('engine')}:terrain_count_not_8")
    if not payload.get("geometry_not_axes"):
        errors.append(f"{payload.get('engine')}:geometry_not_axes_missing")
    return errors


def main() -> None:
    legs = {name: load(name) for name in ("julia", "jax", "pytorch")}
    lint_errors = [e for p in legs.values() for e in lint_payload(p)]
    keys = sorted(legs["julia"]["t1_t2_channel_distinguishability"])
    max_diff = 0.0
    for k in keys:
        vals = [legs[e]["t1_t2_channel_distinguishability"][k] for e in legs]
        max_diff = max(max_diff, max(vals) - min(vals))
    relabel_dies = all(p["controls"]["relabel_control_dies"] for p in legs.values())
    nonzero = all(min(p["t1_t2_channel_distinguishability"].values()) > 1e-6 for p in legs.values())
    all_pass = all(p["all_pass"] for p in legs.values()) and not lint_errors and max_diff < 1e-12 and relabel_dies and nonzero
    result = {
        "schema_version": "three_engine_sim_result_v1",
        "sim_id": SIM_ID,
        "name": SIM_ID,
        "classification": "scratch_diagnostic",
        "sim_execution_kind": "three_engine_rung",
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "all_pass": all_pass,
        "created_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "claim_ceiling": "G10 eight terrain-flow assembly on G5 rho floor only; no axis ontology, no promotion.",
        "out_of_scope": "No terrain-as-axis claim, no Xi bridge, no formal admission, no promotion, no downstream G11/G12 composition.",
        "promotion_condition": "Requires owner review plus independent non-peer Julia/JAX/PyTorch legs before any promotion discussion.",
        "demotion_condition": "Demote if any terrain count, T1/T2 nonzero witness, relabel death, or engine parity check fails.",
        "blocked_until": "Not blocked; scratch diagnostic only.",
        "next_lego_target": "Replace peer-reused Julia/PyTorch wrappers with fully independent native engine implementations.",
        "canon_runtime": {"semantic_owner": "julia", "peer_reads": False},
        "terrains": legs["julia"]["terrains"],
        "t1_t2_channel_distinguishability": legs["julia"]["t1_t2_channel_distinguishability"],
        "controls": {"eps0_degenerations_recorded": all(p["controls"]["eps0_degenerations_recorded"] for p in legs.values()), "relabel_control_dies": relabel_dies, "label_shuffle_survives": all(p["controls"]["label_shuffle_survives"] for p in legs.values())},
        "parity": {"max_engine_divergence": max_diff, "check_agreement": max_diff < 1e-12},
        "lint": {"error_count": len(lint_errors), "errors": lint_errors},
        "engines": {name: {"all_pass": p["all_pass"], "result_path": str(RESULTS / f"{SIM_ID}_{name}_results.json"), "source_sha256": p["source_sha256"]} for name, p in legs.items()},
        "TOOL_MANIFEST": {"python_json": {"tried": True, "used": True, "reason": "supportive three-engine agreement and receipt write"}},
        "TOOL_INTEGRATION_DEPTH": {"python_json": "supportive"},
        "controller_source_sha256": hashlib.sha256(pathlib.Path(__file__).read_bytes()).hexdigest(),
    }
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"all_pass": all_pass, "lint_errors": len(lint_errors), "max_engine_divergence": max_diff, "out": str(OUT)}, sort_keys=True))


if __name__ == "__main__":
    main()
