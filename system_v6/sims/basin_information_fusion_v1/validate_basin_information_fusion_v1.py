#!/usr/bin/env python3
"""Packet-local validator for basin_information_fusion_v1."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any


ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
SIM_ID = "basin_information_fusion_v1"
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_DIR = SIM_DIR / "results"
DEFAULT_RESULT = RESULT_DIR / f"{SIM_ID}_envelope_results.json"
VALIDATOR_RESULT = RESULT_DIR / f"{SIM_ID}_validator_results.json"
CHART_RELATIVE_TOKEN = "G1_CHART_RELATIVE_ORIGINAL_33_CELL_FINITE_STRUCTURE"


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def require(errors: list[str], condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


def as_dict(value: Any, errors: list[str], name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        errors.append(f"{name} must be an object")
        return {}
    return value


def as_list(value: Any, errors: list[str], name: str) -> list[Any]:
    if not isinstance(value, list):
        errors.append(f"{name} must be a list")
        return []
    return value


def log_close(left: float, right: float, tol: float = 1.0e-12) -> bool:
    return abs(float(left) - float(right)) <= tol


def g1_rows_carry_chart_label(value: Any) -> bool:
    """Every dict/list subtree that cites G1 must also carry the chart label."""
    if isinstance(value, dict):
        text_values = [str(v) for v in value.values() if isinstance(v, str)]
        cites_g1 = any("G1" in text for text in text_values)
        if cites_g1 and CHART_RELATIVE_TOKEN not in text_values and value.get("chart_relative_label") != CHART_RELATIVE_TOKEN:
            return False
        return all(g1_rows_carry_chart_label(child) for child in value.values())
    if isinstance(value, list):
        return all(g1_rows_carry_chart_label(child) for child in value)
    return True


def validate(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    require(errors, payload.get("schema_version") == "three_engine_sim_result_v1", "schema_version mismatch")
    require(errors, payload.get("sim_id") == SIM_ID, "sim_id mismatch")
    require(errors, payload.get("classification") == "scratch_diagnostic", "classification mismatch")
    require(errors, payload.get("promotion_allowed") is False, "promotion_allowed must be false")
    require(errors, payload.get("formal_admission_allowed") is False, "formal_admission_allowed must be false")
    require(errors, payload.get("all_pass") is True, "all_pass must be true")

    engines = as_dict(payload.get("engines"), errors, "engines")
    require(errors, set(engines) == {"julia", "jax", "pytorch"}, "engines must be julia, jax, pytorch")
    for name in ("julia", "jax", "pytorch"):
        engine = as_dict(engines.get(name), errors, f"engines.{name}")
        require(errors, engine.get("ran") is True, f"{name}.ran must be true")
        require(errors, engine.get("reads_peer_result") is False, f"{name}.reads_peer_result must be false")
        require(errors, bool(engine.get("aligned_packages_load_bearing")), f"{name} load-bearing package list empty")
        observables = as_dict(engine.get("package_observables"), errors, f"{name}.package_observables")
        for package in engine.get("aligned_packages_load_bearing", []):
            require(errors, isinstance(observables.get(package), str) and bool(observables.get(package).strip()), f"{name}.{package} observable missing")

    tool_intent = as_dict(payload.get("tool_intent"), errors, "tool_intent")
    require(errors, bool(tool_intent.get("claim_classes")), "tool_intent.claim_classes must be non-empty")
    engine_tool_intent = as_dict(tool_intent.get("engine_tool_intent"), errors, "tool_intent.engine_tool_intent")
    for name in ("julia", "jax", "pytorch"):
        require(errors, name in engine_tool_intent, f"tool_intent missing {name}")

    orbit_rows = as_list(payload.get("entropy_production_along_orbits"), errors, "entropy_production_along_orbits")
    require(errors, len(orbit_rows) == 7, "must emit one entropy orbit row for G0-G5 plus G3L/G3R")
    for row in orbit_rows:
        if not isinstance(row, dict):
            continue
        require(errors, row.get("actual_R_C_orbits") is True, f"{row.get('set_id')} must use actual R_C orbits")
        trajectory = as_list(row.get("trajectory"), errors, f"{row.get('set_id')}.trajectory")
        require(errors, len(trajectory) >= 2, f"{row.get('set_id')} needs per-step trajectory")
        for step in trajectory:
            if not isinstance(step, dict):
                continue
            for key in ("cell_support_counting_entropy", "communicating_class_counting_entropy"):
                typed = as_dict(step.get(key), errors, f"{row.get('set_id')}.{key}")
                require(errors, typed.get("type", "").startswith("counting_entropy_"), f"{row.get('set_id')}.{key} type missing")
                require(errors, "after_minus_before" in typed, f"{row.get('set_id')}.{key} missing per-step delta")

    record = as_dict(payload.get("record_retention_at_g1_merge"), errors, "record_retention_at_g1_merge")
    require(errors, record.get("chart_relative_label") == CHART_RELATIVE_TOKEN, "record row missing G1 chart-relative label")
    require(errors, len(as_list(record.get("syndrome_table"), errors, "record.syndrome_table")) == 33, "syndrome table must cover 33 orbits")
    record_modes = as_dict(record.get("readout_recoverability"), errors, "record.readout_recoverability")
    full = as_dict(record_modes.get("constructed_full_syndrome_record"), errors, "record.full")
    erased = as_dict(record_modes.get("erased_record_control"), errors, "record.erased")
    partial = as_dict(record_modes.get("partial_record_control"), errors, "record.partial")
    state_loss = float(record.get("state_only_syndrome_loss_nats", -1.0))
    require(errors, log_close(full.get("recoverable_counting_entropy_nats", -1.0), math.log(3)), "full record must retain log(3)")
    require(errors, log_close(full.get("conservation_defect_nats", -1.0), 0.0), "full record defect must be zero")
    require(errors, log_close(erased.get("recoverable_counting_entropy_nats", -1.0), 0.0), "erased record must retain zero")
    require(errors, erased.get("conservation_defect_nats", 0.0) > 0.0 and log_close(erased.get("conservation_defect_nats", -1.0), state_loss), "erased defect must be nonzero")
    partial_value = float(partial.get("recoverable_counting_entropy_nats", -1.0))
    require(errors, 0.0 < partial_value < math.log(3), "partial record must be strictly between erased and full")

    throughput = as_list(payload.get("per_class_throughput"), errors, "per_class_throughput")
    require(errors, len(throughput) == 17, "per terminal class throughput rows must cover all G0-G5 terminal classes")
    for row in throughput:
        if not isinstance(row, dict):
            continue
        absent = as_dict(row.get("absent_exit_proof"), errors, f"{row.get('row_id')}.absent_exit_proof")
        require(errors, absent.get("no_exit") is True, f"{row.get('row_id')} must carry no-exit proof")
        info = as_dict(row.get("throughput"), errors, f"{row.get('row_id')}.throughput")
        require(errors, info.get("type") == "finite_counting_support_throughput_nats", f"{row.get('row_id')} throughput type mismatch")
        require(errors, info.get("exactness") == "exact_finite_counting_support", f"{row.get('row_id')} exactness mismatch")

    flow = as_list(payload.get("basin_conditioned_flow"), errors, "basin_conditioned_flow")
    require(errors, len(flow) == 17, "basin-conditioned flow rows must cover all terminal basin rows")
    for row in flow:
        if not isinstance(row, dict):
            continue
        require(errors, row.get("conditioning_variable") == "must_basin_vs_may_only", f"{row.get('row_id')} conditioning variable mismatch")
        require(errors, row.get("probe_identity_discipline") == "a=a iff a~b under declared probe family", f"{row.get('row_id')} identity discipline missing")
        require(errors, "distinguishable_under_declared_probes" in row, f"{row.get('row_id')} distinguishability missing")

    controls = as_dict(payload.get("controls"), errors, "controls")
    require(errors, controls.get("erased_record_control", {}).get("flipped") is True, "erased-record control must flip")
    require(errors, controls.get("partial_record_control", {}).get("flipped") is True, "partial-record control must flip")
    require(errors, controls.get("shuffled_order_control", {}).get("production_trajectory_changed") is True, "shuffled-order control must change")
    require(errors, controls.get("similarity_only_control", {}).get("basin_conditioned_rows_fail") is True, "similarity-only control must fail basin rows")

    contract = as_dict(payload.get("binding_basin_packet_contract"), errors, "binding_basin_packet_contract")
    for key in ("finite_S", "Adm_C", "R_C", "trapping_test", "lyapunov_monotone_observable", "escape_tests", "basin_partition", "engine_dof_perturbation_test", "negative_controls"):
        require(errors, key in contract, f"binding contract missing {key}")
    sections = as_dict(payload.get("claim_sections"), errors, "claim_sections")
    for key in ("positive", "negative", "boundary"):
        require(errors, bool(sections.get(key)), f"{key} claim section missing")

    proofs = as_dict(payload.get("crossover_proofs"), errors, "crossover_proofs")
    for name in ("z3", "cvc5", "julia_z3"):
        proof = as_dict(proofs.get(name), errors, f"proofs.{name}")
        require(errors, proof.get("ran") is True, f"{name} did not run")
        require(errors, proof.get("load_bearing") is True, f"{name} not load-bearing")
        require(errors, proof.get("verdict") == "unsat", f"{name} identity must be unsat")
        require(errors, proof.get("erased_flip_verdict") == "sat", f"{name} erased flip must be sat")

    gates = as_dict(payload.get("build_gates"), errors, "build_gates")
    for gate in (
        "ceilings_exact",
        "all_engine_legs_pass",
        "record_constructed_packet_locally",
        "record_controls_flip",
        "shuffled_order_changes_trajectory",
        "similarity_only_guard_fails",
        "g1_chart_relative_labels_present",
        "three_engine_divergence_zero",
        "tool_intent_present",
        "one_to_one_tool_calls",
    ):
        require(errors, gates.get(gate) is True, f"build gate {gate} must be true")

    require(errors, g1_rows_carry_chart_label(payload.get("entropy_production_along_orbits")), "G1-citing orbit rows lack chart-relative label")
    require(errors, g1_rows_carry_chart_label(payload.get("record_retention_at_g1_merge")), "G1-citing record rows lack chart-relative label")
    return errors


def main() -> int:
    if not DEFAULT_RESULT.exists():
        result = {
            "ok": False,
            "errors": [f"missing result JSON: {rel(DEFAULT_RESULT)}"],
            "result_json": rel(DEFAULT_RESULT),
            "validator": rel(Path(__file__)),
        }
        VALIDATOR_RESULT.parent.mkdir(parents=True, exist_ok=True)
        VALIDATOR_RESULT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(json.dumps(result, indent=2, sort_keys=True))
        return 1
    payload = json.loads(DEFAULT_RESULT.read_text(encoding="utf-8"))
    errors = validate(payload)
    result = {
        "ok": not errors,
        "errors": errors,
        "result_json": rel(DEFAULT_RESULT),
        "validator": rel(Path(__file__)),
    }
    VALIDATOR_RESULT.parent.mkdir(parents=True, exist_ok=True)
    VALIDATOR_RESULT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
