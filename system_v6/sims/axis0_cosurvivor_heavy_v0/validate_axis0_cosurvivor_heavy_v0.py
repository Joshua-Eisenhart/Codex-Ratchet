#!/usr/bin/env python3
"""Packet-local validator for axis0_cosurvivor_heavy_v0."""

from __future__ import annotations

import datetime as dt
import json
import sys
from pathlib import Path
from typing import Any


SIM_ID = "axis0_cosurvivor_heavy_v0"
ROOT = Path(__file__).resolve().parents[3]
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_DIR = SIM_DIR / "results"
ENVELOPE = RESULT_DIR / f"{SIM_ID}_envelope_results.json"
JAX = RESULT_DIR / f"{SIM_ID}_jax_results.json"
PYTORCH = RESULT_DIR / f"{SIM_ID}_pytorch_results.json"
JULIA = RESULT_DIR / f"{SIM_ID}_julia_results.json"
VALIDATOR_RESULT = RESULT_DIR / f"{SIM_ID}_validator_results.json"

sys.path.insert(0, str(ROOT / "scripts"))
import validate_three_engine_sim_result as generic_validator  # noqa: E402


EXPECTED_VERDICTS = {
    "A0.CP.11": "excluded-by-stability-class-mismatch",
    "A0.CP.14": "excluded-by-stability-class-mismatch",
}
EXPECTED_SENTENCE = "Axis-0 = the anchor alias class"


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def require(errors: list[str], condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


def verdict_map(payload: dict[str, Any]) -> dict[str, str]:
    return {row["candidate"]: row["final_verdict"] for row in payload.get("final_verdict_table", [])}


def validate_payload() -> tuple[list[str], dict[str, Any]]:
    errors: list[str] = []
    for path in [
        ENVELOPE,
        JAX,
        PYTORCH,
        JULIA,
        SIM_DIR / "build_card.md",
        SIM_DIR / "builder_self_assessment.md",
    ]:
        require(errors, path.exists(), f"missing required file: {path.relative_to(ROOT)}")
    payload = load(ENVELOPE) if ENVELOPE.exists() else {}
    lanes = {name: load(path) if path.exists() else {} for name, path in [("jax", JAX), ("pytorch", PYTORCH), ("julia", JULIA)]}

    if payload:
        require(errors, payload.get("schema_version") == "three_engine_sim_result_v1", "schema_version mismatch")
        require(errors, payload.get("sim_id") == SIM_ID, "sim_id mismatch")
        require(errors, payload.get("classification") == "scratch_diagnostic", "classification must be scratch_diagnostic")
        require(errors, payload.get("promotion_allowed") is False, "promotion_allowed must be false")
        require(errors, payload.get("formal_admission_allowed") is False, "formal_admission_allowed must be false")
        require(errors, payload.get("all_pass") is True, "all_pass must be true")
        require(errors, verdict_map(payload) == EXPECTED_VERDICTS, "final verdict table mismatch")
        require(errors, payload.get("family_adjudication_sentence") == EXPECTED_SENTENCE, "family sentence mismatch")
        require(errors, sorted(payload.get("engines", {})) == ["jax", "julia", "pytorch"], "all three engines must be present")
        require(errors, all(row.get("co_survivor") is False for row in payload["final_verdict_table"]), "no co-survivor should be minted")
        for row in payload.get("candidate_verdict_table", []):
            require(errors, len(row.get("sign_vector", [])) == 33, f"{row.get('candidate')} vector length mismatch")
            require(errors, len(row.get("cell_level_disagreement_table", [])) == 33, f"{row.get('candidate')} disagreement table must include all cells")
            require(errors, "stability_class_comparison" in row, f"{row.get('candidate')} missing stability comparison")
            require(errors, "multi_step_stability_extension" in row, f"{row.get('candidate')} missing multi-step stability")
            require(errors, "distinction_boundary_check" in row, f"{row.get('candidate')} missing boundary check")
            require(errors, row.get("distinction_boundary_check", {}).get("reads_axis0_feedback_distinction") is True, f"{row.get('candidate')} boundary should pass")
            require(errors, row.get("stability_class_comparison", {}).get("matches_anchor_profile") is False, f"{row.get('candidate')} should fail stability")
        controls = {row.get("id"): row.get("verdict") for row in payload.get("control_verdicts", [])}
        require(errors, controls.get("control.anchor_self") == "alias-of-anchor", "anchor control mismatch")
        require(errors, controls.get("control.deliberate_alias") == "alias-of-anchor", "alias control mismatch")
        for cid in [
            "A0.CP.1_unweighted_edge_gradient_count_balance",
            "A0.CP.2_incoming_vs_outgoing_gradient_current",
            "A0.CP.10_transition_graph_in_out_degree_imbalance",
        ]:
            require(errors, any(row.get("candidate") == cid and row.get("still_excluded") is True for row in payload.get("control_verdicts", [])), f"{cid} not preserved excluded")
        generic_errors = generic_validator.validate(payload, require_pytorch=True)
        errors.extend([f"generic validator: {error}" for error in generic_errors])

    for name, lane in lanes.items():
        if lane:
            require(errors, lane.get("all_pass") is True, f"{name} lane all_pass false")
            require(errors, verdict_map(lane) == EXPECTED_VERDICTS, f"{name} verdict mismatch")
            require(errors, lane.get("reads_peer_result") is False, f"{name} must not read peer result")
    return errors, {"payload": payload, **lanes}


def main() -> int:
    errors, summary = validate_payload()
    result = {
        "ok": not errors,
        "validator_ok": not errors,
        "sim_id": SIM_ID,
        "result_json": str(ENVELOPE.relative_to(ROOT)),
        "errors": errors,
        "verdicts": verdict_map(summary["payload"]) if summary.get("payload") else {},
        "family_adjudication_sentence": summary.get("payload", {}).get("family_adjudication_sentence"),
        "generated_at": dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    VALIDATOR_RESULT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
