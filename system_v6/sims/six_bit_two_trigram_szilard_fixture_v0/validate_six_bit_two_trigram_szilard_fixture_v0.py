#!/usr/bin/env python3
"""Packet-local validator for six_bit_two_trigram_szilard_fixture_v0."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
SIM_ID = "six_bit_two_trigram_szilard_fixture_v0"
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT = SIM_DIR / "results" / f"{SIM_ID}_results.json"
ENVELOPE_RESULT = SIM_DIR / "results" / f"{SIM_ID}_envelope_results.json"


def require(errors: list[str], condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


def frac(value: dict[str, Any]) -> tuple[int, int]:
    return int(value["num"]), int(value["den"])


def main() -> int:
    errors: list[str] = []
    if not RESULT.exists():
        errors.append(f"missing result: {RESULT.relative_to(ROOT)}")
        print(json.dumps({"ok": False, "errors": errors}, indent=2))
        return 1
    if not ENVELOPE_RESULT.exists():
        errors.append(f"missing envelope result: {ENVELOPE_RESULT.relative_to(ROOT)}")
        print(json.dumps({"ok": False, "errors": errors}, indent=2))
        return 1

    payload = json.loads(RESULT.read_text(encoding="utf-8"))
    envelope = json.loads(ENVELOPE_RESULT.read_text(encoding="utf-8"))
    require(errors, payload.get("schema_version") == f"{SIM_ID}_result_v1", "schema_version mismatch")
    require(errors, payload.get("sim_id") == SIM_ID, "sim_id mismatch")
    require(errors, payload.get("classification") == "scratch_diagnostic", "classification must stay scratch_diagnostic")
    require(errors, payload.get("row_classification") == "classical_baseline", "row classification must be classical_baseline")
    require(errors, payload.get("promotion_allowed") is False, "promotion_allowed must be false")
    require(errors, payload.get("formal_admission_allowed") is False, "formal_admission_allowed must be false")
    require(errors, payload.get("all_pass") is True, "all_pass must be true")

    boundary = payload.get("claim_boundary", {})
    for key in ("engine_carrier_fixture_only", "no_physics_bridge", "no_64_claims", "not_qit_admission", "not_axis_admission"):
        require(errors, boundary.get(key) is True, f"boundary missing/false: {key}")

    carrier = payload.get("carrier_summary", {})
    require(errors, carrier.get("state_count") == 64, "carrier state_count must be 64")
    require(errors, carrier.get("bit_count") == 6, "carrier bit_count must be 6")
    require(errors, carrier.get("pair_count") == 64, "trigram pair_count must be 64")
    require(errors, carrier.get("lower_trigram_values") == list(range(8)), "lower trigram values must be 0..7")
    require(errors, carrier.get("upper_trigram_values") == list(range(8)), "upper trigram values must be 0..7")

    costs = payload.get("record_costs", {})
    require(errors, frac(costs["unstructured_6bit_state_record"]["bits"]) == (6, 1), "unstructured record must cost 6 bits")
    require(errors, frac(costs["two_trigram_full_pair_record"]["bits"]) == (6, 1), "two-trigram full record must cost 6 bits")
    effect = costs["effect_of_3_plus_3_split"]
    require(errors, frac(effect["full_state_delta_bits"]) == (0, 1), "3+3 split full-state delta must be zero")
    require(
        errors,
        effect["full_state_verdict"] == "no_change_for_uniform_full_state_record",
        "full-state split verdict mismatch",
    )
    require(errors, frac(costs["lower_trigram_only_record"]["bits"]) == (3, 1), "lower trigram-only record must cost 3 bits")
    require(errors, frac(costs["upper_trigram_only_record"]["bits"]) == (3, 1), "upper trigram-only record must cost 3 bits")
    require(errors, frac(costs["parity_pair_record"]["bits"]) == (2, 1), "parity-pair record must cost 2 bits")

    ledger = payload.get("per_cycle_ledger", {})
    for row_id in ("unstructured_6bit_state_record", "two_trigram_full_pair_record"):
        row = ledger[row_id]
        require(errors, frac(row["record_bits"]) == (6, 1), f"{row_id} record_bits must be 6")
        require(errors, frac(row["erase_cost_ln2_coeff"]) == (6, 1), f"{row_id} erase cost must be 6 ln2")
        require(errors, frac(row["net_paid_cycle_ln2_coeff"]) == (0, 1), f"{row_id} net paid cycle must balance")

    controls = ledger["wrong_order_controls"]
    require(errors, controls["canonical_measure_feedback_erase"]["verdict"] == "sat", "canonical order must be sat")
    require(errors, controls["feedback_before_measure"]["verdict"] == "unsat", "feedback-before-measure must be unsat")
    require(errors, controls["erase_before_feedback"]["verdict"] == "unsat", "erase-before-feedback must be unsat")
    require(errors, frac(controls["no_measurement_control"]["work_credit_ln2_coeff"]) == (0, 1), "no-measurement work credit must be zero")

    require(errors, "TOOL_MANIFEST" in payload, "TOOL_MANIFEST missing")
    require(errors, "TOOL_INTEGRATION_DEPTH" in payload, "TOOL_INTEGRATION_DEPTH missing")
    require(errors, payload["TOOL_INTEGRATION_DEPTH"].get("python_fractions") == "load_bearing", "python_fractions must be load_bearing")
    require(errors, bool(payload.get("divergence_log")), "classical baseline divergence_log must be non-empty")
    require(errors, "physics bridge" in payload.get("blocked_claims", []), "physics bridge must be blocked")

    require(errors, envelope.get("schema_version") == "three_engine_sim_result_v1", "envelope schema_version mismatch")
    require(errors, envelope.get("sim_id") == SIM_ID, "envelope sim_id mismatch")
    require(errors, envelope.get("classification") == "scratch_diagnostic", "envelope classification must stay scratch_diagnostic")
    require(errors, envelope.get("promotion_allowed") is False, "envelope promotion_allowed must be false")
    require(errors, envelope.get("formal_admission_allowed") is False, "envelope formal_admission_allowed must be false")
    require(errors, envelope.get("all_pass") is True, "envelope all_pass must be true")
    require(
        errors,
        envelope.get("mode") == "julia_canon_plus_jax_diagnostic_pytorch_omitted",
        "envelope mode must declare honest two-lane plus omitted PyTorch mode",
    )
    require(
        errors,
        envelope.get("build_helper_path") == "scripts/build_three_engine_envelope.py",
        "envelope must name canonical build helper",
    )
    engine_contract = envelope.get("engine_contract", {})
    require(errors, sorted(engine_contract.get("lanes", [])) == ["jax", "julia"], "envelope lanes must be jax+julia")
    require(errors, "pytorch" in engine_contract.get("omitted_lanes", {}), "envelope must honestly omit PyTorch")
    require(errors, set(envelope.get("engines", {})) == {"julia", "jax"}, "envelope engines must be julia+jax only")
    boundary = envelope.get("boundary", {})
    for key in ("no_physics_bridge", "no_64_claims", "not_qit_admission", "not_axis_admission", "not_matrix64_completion"):
        require(errors, boundary.get(key) is True, f"envelope boundary missing/false: {key}")
    require(errors, envelope.get("result_values_unchanged") is True, "envelope must declare unchanged values")
    parity = envelope.get("engine_value_parity", {})
    require(errors, bool(parity), "envelope parity section missing")
    for engine in ("julia", "jax"):
        checks = parity.get(engine, {})
        require(errors, bool(checks), f"{engine} parity checks missing")
        require(errors, all(checks.values()), f"{engine} parity checks must all pass")
    intent = envelope.get("TOOL_INTENT_MATRIX", {})
    require(errors, "build_three_engine_envelope" in intent, "TOOL_INTENT_MATRIX missing envelope builder")
    require(errors, intent.get("pytorch", {}).get("mode") == "omitted", "TOOL_INTENT_MATRIX must declare PyTorch omitted")

    if errors:
        print(json.dumps({"ok": False, "errors": errors}, indent=2))
        return 1
    print(
        json.dumps(
            {
                "ok": True,
                "result_json": str(RESULT.relative_to(ROOT)),
                "envelope_json": str(ENVELOPE_RESULT.relative_to(ROOT)),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
