#!/usr/bin/env python3
"""Validate ratchet_s6_terrain_operator_shell_v0 result shape and gates."""

from __future__ import annotations

import datetime as dt
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
SIM_ID = "ratchet_s6_terrain_operator_shell_v0"
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
DEFAULT_RESULT = SIM_DIR / "results" / f"{SIM_ID}_envelope_results.json"
VALIDATOR_RESULT = SIM_DIR / "results" / f"{SIM_ID}_validator_results.json"

EXPECTED_PARENTS = {
    "ratchet_s1_single_shell_pilot_v0",
    "geo_disintegration_machinery_v0",
    "geo_s5_terrain_flows_v0",
    "geo_s4_operator_stage_v0",
    "geo_s2_s5_mode_sweep_v0",
}


def rel(path: Path) -> str:
    if not path.is_absolute():
        path = ROOT / path
    return str(path.relative_to(ROOT))


def require(condition: bool, errors: list[str], message: str) -> None:
    if not condition:
        errors.append(message)


def as_dict(value: Any, name: str, errors: list[str]) -> dict[str, Any]:
    if not isinstance(value, dict):
        errors.append(f"{name} must be an object")
        return {}
    return value


def validate(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    require(payload.get("schema_version") == "three_engine_sim_result_v1", errors, "schema_version mismatch")
    require(payload.get("mode") == "RATCHETED", errors, "mode must be RATCHETED")
    require(payload.get("engine_contract", {}).get("mode") == "RATCHETED", errors, "engine_contract.mode must be RATCHETED")
    require(payload.get("classification") == "scratch_diagnostic", errors, "classification must be scratch_diagnostic")
    require(payload.get("promotion_allowed") is False, errors, "promotion_allowed must be false")
    require(payload.get("formal_admission_allowed") is False, errors, "formal_admission_allowed must be false")
    require(payload.get("all_pass") is True, errors, "all_pass must be true")

    parents = as_dict(payload.get("parent_lineage"), "parent_lineage", errors)
    require(set(parents) == EXPECTED_PARENTS, errors, "parent_lineage must contain only the five allowed parent packets")
    for name in EXPECTED_PARENTS:
        parent = as_dict(parents.get(name), f"parent_lineage.{name}", errors)
        require(bool(parent.get("committed_tree")), errors, f"{name} committed_tree missing")
        require(bool(parent.get("envelope_sha256")), errors, f"{name} envelope_sha256 missing")
        require(bool(parent.get("top_source_sha256")), errors, f"{name} top_source_sha256 missing")

    fences = as_dict(payload.get("scope_fences"), "scope_fences", errors)
    require(fences.get("single_shell_only") is True, errors, "single_shell_only fence missing")
    require(fences.get("nested_multi_shell_conditioning") is False, errors, "nested_multi_shell_conditioning must be false")
    require(fences.get("nested_fences_do_not_bind_here") is True, errors, "nested nonbinding fence must be stated")

    sequence = as_dict(payload.get("ratchet_sequence"), "ratchet_sequence", errors)
    step1 = as_dict(sequence.get("step1_condition_shell"), "ratchet_sequence.step1_condition_shell", errors)
    require(step1.get("conditioned_object") == "T_pi/6", errors, "step1 must condition T_pi/6")
    require(step1.get("state_family", {}).get("z") == "1/2", errors, "conditioned shell z must be 1/2")
    step2 = as_dict(sequence.get("step2_terrain"), "ratchet_sequence.step2_terrain", errors)
    terrain = as_dict(step2.get("terrain_generator"), "terrain_generator", errors)
    require(terrain.get("id") == "Se_Funnel_L", errors, "terrain id must be Se_Funnel_L")
    require(terrain.get("ab_sha256") == "25f78fc755e37729771e46eef26f6d80358dbcee06891917e2ebe82dcee5128a", errors, "Se_Funnel_L A,b hash mismatch")
    require(terrain.get("z_dot") == "-sqrt(2)*cos(theta + pi/4)/5 - 2/5", errors, "terrain z_dot mismatch")
    require(terrain.get("shell_average_leakage") == "-2/5", errors, "terrain average leakage mismatch")
    require(terrain.get("s6_class_name_applied") == "cross_shell_with_leave_foliation", errors, "terrain classification mismatch")
    fixed = as_dict(step2.get("fixed_points"), "fixed_points", errors)
    require(fixed.get("survives_conditioning") is False, errors, "unconstrained fixed point must be excluded")
    require(fixed.get("induced_leaf_fixed_points") == [], errors, "induced leaf fixed points must be empty")

    step3 = as_dict(sequence.get("step3_operator_order"), "ratchet_sequence.step3_operator_order", errors)
    gap = as_dict(step3.get("order_gap"), "order_gap", errors)
    require(gap.get("norm_squared") == "4/25", errors, "order gap norm must be 4/25")
    require(gap.get("nonzero_for_all_theta") is True, errors, "order gap must be nonzero for all theta")
    require(gap.get("witness_theta0") == ["0", "0", "-2/5"], errors, "theta0 witness mismatch")
    control = as_dict(step3.get("commuting_control"), "commuting_control", errors)
    require(control.get("gap_killed") is True, errors, "commuting control must kill gap")
    require(control.get("norm_squared") == "0", errors, "commuting control norm must be zero")

    signatures = as_dict(payload.get("ratchet_signatures"), "ratchet_signatures", errors)
    require(signatures.get("narrowing", {}).get("computed") is True, errors, "narrowing must be computed")
    require(signatures.get("alteration", {}).get("altered") is True, errors, "alteration must be computed")
    path_specificity = as_dict(signatures.get("path_specificity"), "ratchet_signatures.path_specificity", errors)
    require(path_specificity.get("load_bearing_row", {}).get("nonzero_gap") is True, errors, "path nonzero gap row missing")
    require(path_specificity.get("load_bearing_row", {}).get("commuting_control_kills_gap") is True, errors, "path commuting kill row missing")

    controls = as_dict(payload.get("controls"), "controls", errors)
    require(controls.get("nothing_excluded", {}).get("byte_exact") is True, errors, "nothing-excluded control must be byte-exact")
    require(controls.get("wrong_leaf", {}).get("control_fired") is True, errors, "wrong-leaf control must fire")
    require(controls.get("naive_conditioning_failure_refired", {}).get("pass") is True, errors, "naive-conditioning control must fire")
    quotient = controls.get("quotient_survival_parent_row", {})
    require(quotient.get("off_diagonal_distinguishable_count") == 56, errors, "quotient survival distinguishable count must be 56")
    require(quotient.get("off_diagonal_pair_count") == 56, errors, "quotient survival pair count must be 56")
    require(quotient.get("collapsed_pairs") == [], errors, "quotient survival collapsed_pairs must be empty")

    proofs = as_dict(payload.get("crossover_proofs"), "crossover_proofs", errors)
    for solver in ("z3", "cvc5"):
        row = as_dict(proofs.get(solver), f"crossover_proofs.{solver}", errors)
        require(row.get("ran") is True, errors, f"{solver} must run")
        require(row.get("load_bearing") is True, errors, f"{solver} must be load-bearing")
        require(row.get("verdict") == "unsat", errors, f"{solver} positive verdict must be unsat")
        require(row.get("erased_flip_verdict") == "sat", errors, f"{solver} erased flip must be sat")
        require(row.get("commuting_control_verdict") == "unsat", errors, f"{solver} commuting control verdict must be unsat")
    julia_z3 = as_dict(proofs.get("julia_z3"), "crossover_proofs.julia_z3", errors)
    require(julia_z3.get("verdict") == "unsat", errors, "julia_z3 positive verdict must be unsat")
    require(julia_z3.get("erased_flip_verdict") == "sat", errors, "julia_z3 erased flip must be sat")

    calls = payload.get("tool_calls")
    require(isinstance(calls, list) and len(calls) == 4, errors, "tool_calls must contain exactly four rows")
    if isinstance(calls, list):
        require([call.get("tool") for call in calls] == ["sympy", "z3", "cvc5", "Z3"], errors, "tool call order mismatch")
        require(all(call.get("load_bearing") is True for call in calls), errors, "all tool calls must be load-bearing")
    require(payload.get("claim_path_tools") == ["sympy", "z3", "cvc5", "Z3"], errors, "claim_path_tools mismatch")

    gates = as_dict(payload.get("build_gates"), "build_gates", errors)
    for gate in (
        "mode_declared_ratcheted",
        "single_shell_only",
        "nested_fences_stated_not_binding",
        "parents_are_only_allowed_packets",
        "parent_lineage_hashes_present",
        "terrain_ab_hash_cited",
        "quotient_survival_56_56_cited",
        "nonzero_order_gap",
        "commuting_control_kills_gap",
        "smt_positive_and_erased_flip",
        "smt_commuting_control_zero",
        "julia_result_loaded",
        "julia_source_hash_matches",
        "julia_reads_no_peer_result",
        "julia_engine_values_match_python_exact_rows",
        "julia_z3_load_bearing",
        "julia_z3_positive_and_erased_flip",
        "one_to_one_tool_calls",
    ):
        require(gates.get(gate) is True, errors, f"gate {gate} must be true")

    divergence = as_dict(payload.get("divergence"), "divergence", errors)
    require(divergence.get("julia_authoritative") is True, errors, "divergence.julia_authoritative must be true")
    require(divergence.get("max_divergence") == 0.0, errors, "max_divergence must be 0.0")
    engine_values = as_dict(divergence.get("engine_values"), "divergence.engine_values", errors)
    require(set(engine_values) == {"julia", "jax"}, errors, "engine_values must contain julia and jax")
    if set(engine_values) == {"julia", "jax"}:
        require(engine_values["julia"] == engine_values["jax"], errors, "julia and jax engine values must match")

    return errors


def main(argv: list[str]) -> int:
    result_path = Path(argv[1]) if len(argv) > 1 else DEFAULT_RESULT
    if not result_path.is_absolute():
        result_path = ROOT / result_path
    payload = json.loads(result_path.read_text(encoding="utf-8"))
    errors = validate(payload)
    out = {
        "ok": not errors,
        "result_json": rel(result_path),
        "validator": rel(Path(__file__)),
        "validated_mode": payload.get("mode"),
        "errors": errors,
        "generated_at": dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }
    VALIDATOR_RESULT.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(out, indent=2, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
