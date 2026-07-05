#!/usr/bin/env python3
from __future__ import annotations

import hashlib, json, pathlib
from datetime import datetime, timezone

SIM_ID = "tower_g8_two_sheets_v0"
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
        errors.append(f"{payload.get('engine')}:classification_not_scratch_diagnostic")
    if payload.get("promotion_allowed") is not False:
        errors.append(f"{payload.get('engine')}:promotion_allowed_not_false")
    if payload.get("initial_state_count", 0) < 5:
        errors.append(f"{payload.get('engine')}:too_few_initial_states")
    return errors


def main() -> None:
    RESULTS.mkdir(parents=True, exist_ok=True)
    legs = {name: load(name) for name in ("julia", "jax", "pytorch")}
    lint_errors = [e for payload in legs.values() for e in lint_payload(payload)]
    left = {k: v["sheets"]["L"]["orientation_values"] for k, v in legs.items()}
    right = {k: v["sheets"]["R"]["orientation_values"] for k, v in legs.items()}
    max_diff = 0.0
    for values in (left, right):
        for i in range(5):
            nums = [values[e][i] for e in values]
            max_diff = max(max_diff, max(nums) - min(nums))
    controls = {name: payload["controls"] for name, payload in legs.items()}
    all_controls = all(c["H0_zero"]["sheets_indistinguishable"] and c["sign_flip_relabel"]["left_becomes_right"] and c["sign_flip_relabel"]["right_becomes_left"] and c["label_shuffle"]["multiset_preserved"] for c in controls.values())
    all_pass = all(p["all_pass"] for p in legs.values()) and not lint_errors and max_diff < 3.0e-4 and all_controls
    source = pathlib.Path(__file__).resolve()
    result = {
        "schema_version": "three_engine_sim_result_v1",
        "sim_id": SIM_ID,
        "classification": "scratch_diagnostic",
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "all_pass": all_pass,
        "created_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "claim_ceiling": "Rerunnable G8 two-sheet assembly only: H_L=+H0 vs H_R=-H0 precession orientation over five initial states; no promotion or downstream claim.",
        "canon_runtime": {"semantic_owner": "julia", "peer_reads": False},
        "engines": {name: {"all_pass": p["all_pass"], "result_path": str(RESULTS / f"{SIM_ID}_{name}_results.json"), "source_sha256": p["source_sha256"]} for name, p in legs.items()},
        "precession_invariants": {"L": left, "R": right, "orientation_rule": "sign(dot(cross(r,r_dot),n)) is + on L and - on R"},
        "admission_reason": legs["julia"]["admission_reason"],
        "jax_reconciliation": legs["julia"]["jax_reconciliation"],
        "controls": {
            "H0_zero": all(c["H0_zero"]["sheets_indistinguishable"] for c in controls.values()),
            "H0_zero_max_abs_rate": max(c["H0_zero"]["max_abs_rate"] for c in controls.values()),
            "sign_flip_relabel": all(c["sign_flip_relabel"]["left_becomes_right"] and c["sign_flip_relabel"]["right_becomes_left"] for c in controls.values()),
            "sign_flip_max_residual": max(c["sign_flip_relabel"]["max_residual_after_relabel"] for c in controls.values()),
            "label_shuffle": all(c["label_shuffle"]["multiset_preserved"] for c in controls.values()),
        },
        "parity": {"max_engine_divergence": max_diff, "tolerance": 3.0e-4, "check_agreement": max_diff < 3.0e-4},
        "lint": {"error_count": len(lint_errors), "errors": lint_errors},
        "TOOL_MANIFEST": {"python_json": {"tried": True, "used": True, "reason": "supportive three-engine receipt comparison and envelope write"}},
        "TOOL_INTEGRATION_DEPTH": {"python_json": "supportive"},
        "controller_source_path": str(source),
        "controller_source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
    }
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"all_pass": all_pass, "lint_errors": len(lint_errors), "max_engine_divergence": max_diff, "out": str(OUT)}, sort_keys=True))


if __name__ == "__main__":
    main()
