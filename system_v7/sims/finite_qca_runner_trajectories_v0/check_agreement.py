#!/usr/bin/env python3
"""Agreement adjudicator for finite_qca_runner_trajectories_v0."""

from __future__ import annotations

import json
from pathlib import Path

SIM_ID = "finite_qca_runner_trajectories_v0"
ROOT = Path(__file__).resolve().parent
RESULTS = ROOT / "results"
OUT = RESULTS / f"{SIM_ID}_agreement_results.json"
RULES = ["identity", "right_shift", "left_shift", "finite_depth_local_circuit"]
LEGS = {
    "exact": RESULTS / f"{SIM_ID}_exact_results.json",
    "jax": RESULTS / f"{SIM_ID}_jax_results.json",
}
EXPECTED_INDEX = {
    "identity": 0,
    "right_shift": 1,
    "left_shift": -1,
    "finite_depth_local_circuit": 0,
}


def main() -> int:
    failures = []
    legs = {}
    for name, path in LEGS.items():
        if not path.exists():
            failures.append(f"{name}: missing {path.name}")
            continue
        legs[name] = json.loads(path.read_text())

    for name, result in legs.items():
        if result.get("schema") != "codex_ratchet.sim_result.v1":
            failures.append(f"{name}: bad schema {result.get('schema')}")
        if result.get("sim_id") != SIM_ID:
            failures.append(f"{name}: wrong sim_id {result.get('sim_id')}")
        if result.get("classification") != "scratch_diagnostic":
            failures.append(f"{name}: classification not scratch_diagnostic")
        if result.get("promotion_allowed") is not False or result.get("formal_admission_allowed") is not False:
            failures.append(f"{name}: promotion/formal ceilings not fenced")
        if result.get("reads_peer_result") is not False:
            failures.append(f"{name}: reads_peer_result not false")
        if result.get("all_tests_pass") is not True or result.get("all_controls_pass") is not True:
            failures.append(f"{name}: tests/controls did not pass")

    if set(legs) == {"exact", "jax"}:
        exact = legs["exact"]
        jax = legs["jax"]
        if exact.get("gnvw_index_units_log_q") != jax.get("gnvw_index_units_log_q"):
            failures.append(
                f"indices disagree: exact={exact.get('gnvw_index_units_log_q')} jax={jax.get('gnvw_index_units_log_q')}"
            )
        for rule, expected in EXPECTED_INDEX.items():
            ex_rule = exact["rules"][rule]
            jx_rule = jax["rules"][rule]
            ex_idx = ex_rule["support_index"]["index_units_log_q"]
            jx_idx = jx_rule["support_index"]["index_units_log_q"]
            if ex_idx != expected or jx_idx != expected:
                failures.append(f"{rule}: expected index {expected}, exact={ex_idx}, jax={jx_idx}")
            for key in [
                "left_cut_source_conjugated_support",
                "right_cut_source_conjugated_support",
                "right_restricted_row_from_source_2",
                "left_restricted_row_from_source_3",
            ]:
                a = ex_rule["support_index"][key]
                b = jx_rule["support_index"][key]
                if a != b:
                    failures.append(f"{rule}: support key {key} disagrees exact={a} jax={b}")
            if ex_rule["finite_transition_graph"]["cycle_length_histogram"] != jx_rule["finite_transition_graph"]["cycle_length_histogram"]:
                failures.append(f"{rule}: cycle histogram disagrees")
            if ex_rule["reversibility"]["reversibility_ok"] is not True or jx_rule["reversibility"]["reversibility_ok"] is not True:
                failures.append(f"{rule}: reversibility not proven in both legs")

    agreement_ok = not failures and set(legs) == {"exact", "jax"}
    if set(legs) != {"exact", "jax"}:
        failures.append(f"engines present {sorted(legs)}; expected ['exact', 'jax']")

    result = {
        "schema": "codex_ratchet.agreement_result.v1",
        "sim_id": SIM_ID,
        "classification": "scratch_diagnostic",
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "agreement_ok": agreement_ok,
        "engines_present": sorted(legs),
        "gnvw_index_units_log_q": legs.get("exact", {}).get("gnvw_index_units_log_q", {}),
        "equivalence_relation_checked": "tau ~_support tau' iff ind_q(tau)=r_R-r_L from conjugated support across cut 2|3 is equal",
        "load_bearing_discriminators": {
            "identity_index_zero": agreement_ok and legs["exact"]["gnvw_index_units_log_q"]["identity"] == 0,
            "right_shift_index_plus_one": agreement_ok and legs["exact"]["gnvw_index_units_log_q"]["right_shift"] == 1,
            "left_shift_index_minus_one": agreement_ok and legs["exact"]["gnvw_index_units_log_q"]["left_shift"] == -1,
            "finite_depth_local_circuit_index_zero": agreement_ok and legs["exact"]["gnvw_index_units_log_q"]["finite_depth_local_circuit"] == 0,
            "explicit_inverse_reversibility_all_rules": agreement_ok and all(
                legs["exact"]["rules"][rule]["reversibility"]["reversibility_ok"]
                and legs["jax"]["rules"][rule]["reversibility"]["reversibility_ok"]
                for rule in RULES
            ),
        } if set(legs) == {"exact", "jax"} else {},
        "failures": failures,
        "honest_scope": {
            "earns": "two-leg local agreement that the finite support-flow index is derived from conjugated operator support and passes 0/+1/-1/0 controls",
            "does_not_earn": "formal infinite GNVW classification or promotion beyond scratch_diagnostic",
        },
    }
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"agreement_ok": agreement_ok, "engines": sorted(legs), "indices": result["gnvw_index_units_log_q"], "failures": failures}, indent=2))
    return 0 if agreement_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
