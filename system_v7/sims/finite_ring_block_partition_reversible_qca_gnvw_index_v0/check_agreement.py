#!/usr/bin/env python3
"""Cross-leg agreement adjudicator for the finite-ring QCA GNVW diagnostic.

This script is the only file that reads peer result JSONs. It exits 0 iff the
three independent legs agree on every rule's index and required control gates.
"""

import json
import math
import os
import sys

SIM_ID = "finite_ring_block_partition_reversible_qca_gnvw_index_v0"
HERE = os.path.dirname(os.path.abspath(__file__))
RULES = [
    "left_shift",
    "right_shift",
    "identity",
    "finite_depth_local_circuit",
    "non_shift_partitioned",
]
SHIFT_BY_K = [1, 2, 3]


def sign(x):
    return 1 if x > 0 else -1 if x < 0 else 0


def main():
    base = os.path.join(HERE, "results", f"{SIM_ID}_")
    legs = {engine: json.load(open(base + engine + "_results.json")) for engine in ("julia", "jax", "pytorch")}
    failures = []

    styles = {engine: legs[engine]["computation_style"] for engine in legs}
    if len(set(styles.values())) != 3:
        failures.append(f"not three distinct computation_style values: {styles}")

    for engine, result in legs.items():
        if result.get("schema") != "codex_ratchet.engine_leg_result.v1":
            failures.append(f"{engine}: bad schema")
        if result.get("sim_id") != SIM_ID:
            failures.append(f"{engine}: wrong sim_id")
        if result.get("reads_peer_result") is not False:
            failures.append(f"{engine}: reads_peer_result is not false")
        if result.get("classification") != "scratch_diagnostic":
            failures.append(f"{engine}: classification not scratch_diagnostic")
        if result.get("promotion_allowed") is not False or result.get("formal_admission_allowed") is not False:
            failures.append(f"{engine}: promotion/formal ceilings not fenced")
        if result.get("does_not_self_upgrade") is not True:
            failures.append(f"{engine}: does_not_self_upgrade not true")
        if result.get("index_operator_equals_reversibility_operator") is not True:
            failures.append(f"{engine}: index/reversibility operator identity flag not true")
        bonds = result.get("operator_bonds", {})
        if bonds.get("odd_bonds") != [[1, 2], [3, 4], [5, 6], [7, 0]] and bonds.get("odd_bonds") != [(1, 2), (3, 4), (5, 6), (7, 0)]:
            failures.append(f"{engine}: odd_bonds are not the true periodic ring bonds")

    reference = legs["julia"]["gnvw_index_values"]
    for engine in ("jax", "pytorch"):
        for rule in RULES:
            a = reference[rule]["index_log_value"]
            b = legs[engine]["gnvw_index_values"][rule]["index_log_value"]
            if abs(a - b) > 1e-12:
                failures.append(f"{engine}: {rule} index_log_value mismatch {b} vs julia {a}")
            au = reference[rule]["index_units_log_d"]
            bu = legs[engine]["gnvw_index_values"][rule]["index_units_log_d"]
            if abs(au - bu) > 1e-12:
                failures.append(f"{engine}: {rule} index_units_log_d mismatch {bu} vs julia {au}")

    for engine in ("julia", "jax", "pytorch"):
        shift_by_k = legs[engine].get("shift_by_k_index_values", {})
        for k in SHIFT_BY_K:
            r_actual = shift_by_k.get("right_shift", {}).get(str(k), {}).get("index_units_log_d")
            l_actual = shift_by_k.get("left_shift", {}).get(str(k), {}).get("index_units_log_d")
            if r_actual is None or abs(r_actual - k) > 1e-12:
                failures.append(f"{engine}: right_shift k={k} expected {k}, got {r_actual}")
            if l_actual is None or abs(l_actual + k) > 1e-12:
                failures.append(f"{engine}: left_shift k={k} expected {-k}, got {l_actual}")

    left = reference["left_shift"]["index_units_log_d"]
    right = reference["right_shift"]["index_units_log_d"]
    if not (sign(left) == -sign(right) and sign(left) != 0 and sign(right) != 0):
        failures.append(f"left/right sign opposition failed: left={left}, right={right}")
    if abs(reference["identity"]["index_units_log_d"]) > 1e-12:
        failures.append("identity index is not zero")
    if abs(reference["finite_depth_local_circuit"]["index_units_log_d"]) > 1e-12:
        failures.append("finite_depth_local_circuit index is not zero")

    smt = legs["jax"].get("smt_chirality_flip", {})
    if smt.get("status") != "supportive_demoted":
        failures.append(f"jax SMT status must be supportive_demoted, got {smt.get('status')}")
    if "z3" in legs["jax"].get("aligned_packages_load_bearing", []) or "cvc5" in legs["jax"].get("aligned_packages_load_bearing", []):
        failures.append("jax z3/cvc5 must not be aligned load-bearing after SMT demotion")
    depth = legs["jax"].get("TOOL_INTEGRATION_DEPTH", {})
    if depth.get("z3") != "supportive" or depth.get("cvc5") != "supportive":
        failures.append("jax z3/cvc5 TOOL_INTEGRATION_DEPTH must be supportive")
    if "jax" not in legs["jax"].get("aligned_packages_load_bearing", []):
        failures.append("jax must remain load-bearing for batched index computation")

    if legs["pytorch"].get("reversibility_ok") is not True:
        failures.append("pytorch dense reversibility_ok is not true")
    if legs["pytorch"].get("autograd_receipt", {}).get("autograd_gradient_ok") is not True:
        failures.append("pytorch autograd gradient receipt failed")

    report = {
        "schema": "codex_ratchet.engine_agreement_result.v1",
        "sim_id": SIM_ID,
        "classification": "scratch_diagnostic",
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "computation_styles": styles,
        "gnvw_index_units_log_d": {rule: reference[rule]["index_units_log_d"] for rule in RULES},
        "gnvw_index_log_values": {rule: reference[rule]["index_log_value"] for rule in RULES},
        "shift_by_k_index_units_log_d": legs["julia"].get("shift_by_k_index_values", {}),
        "left_right_sign_opposition": sign(left) == -sign(right) and sign(left) != 0,
        "identity_zero": abs(reference["identity"]["index_units_log_d"]) <= 1e-12,
        "finite_depth_local_circuit_zero": abs(reference["finite_depth_local_circuit"]["index_units_log_d"]) <= 1e-12,
        "jax_smt_status": smt,
        "index_operator_equals_reversibility_operator": all(legs[e].get("index_operator_equals_reversibility_operator") is True for e in legs),
        "pytorch_reversibility_ok": legs["pytorch"].get("reversibility_ok"),
        "all_three_agree": len(failures) == 0,
        "failures": failures,
    }
    out = os.path.join(HERE, "results", f"{SIM_ID}_agreement_results.json")
    with open(out, "w") as f:
        json.dump(report, f, indent=2)
    print(json.dumps(report, indent=2))
    if failures:
        print(f"\nAGREEMENT CHECK FAILED ({len(failures)} issue(s))", file=sys.stderr)
        sys.exit(1)
    print("\nAGREEMENT CHECK OK: all three legs agree on the support-algebra GNVW index controls.")


if __name__ == "__main__":
    main()
