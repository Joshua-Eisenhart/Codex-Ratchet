#!/usr/bin/env python3
"""Cross-leg agreement check (separate verification step). Confirms the EXACT
leg (explicit Python-set operations), the JAX leg (boolean mask over the full
enumeration), and the Julia leg (native integer bitmask survivor sets) landed on
the same load-bearing invariant: at N in {5,6,7}, running_mean_threshold
noncommutes under the running survivor set, commutes under the fixed reference,
and the negative controls are confluent. Exit 0 iff they agree. This script does
NOT recompute the physics.
"""

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SIM_ID = "survivor_set_running_mean_threshold_noncommutation_v0"
LEGS = ("exact", "jax", "julia")
THREE_LEG_INTEGER_KEYS = [
    "pair_count",
    "running_mean_threshold_running_X_noncommute",
    "running_mean_threshold_fixed_reference_noncommute",
    "floor_mean_threshold_running_X_noncommute",
    "ensemble_consistency_noncommute",
]
EXACT_JULIA_INTEGER_KEYS = [
    "config_count",
    "window_count",
    "competitive_exclusion_noncommute",
    "minority_frustration_noncommute",
]
FLOAT_KEYS = []


def main():
    base = os.path.join(HERE, "results", f"{SIM_ID}_")
    legs = {}
    failures = []
    for e in LEGS:
        path = base + e + "_results.json"
        if not os.path.exists(path):
            failures.append(f"{e}: missing result file {os.path.basename(path)}")
            continue
        with open(path) as f:
            legs[e] = json.load(f)

    if set(legs) != set(LEGS):
        report = {
            "schema": "codex_ratchet.agreement_result.v1",
            "sim_id": SIM_ID,
            "engines_present": sorted(legs),
            "three_legs_agree": False,
            "agreement_ok": False,
            "observables_match": {"integer": "diff", "float_max": None},
            "failures": failures,
            "classification": "scratch_diagnostic",
            "promotion_allowed": False,
        }
        out = os.path.join(HERE, "results", f"{SIM_ID}_agreement_results.json")
        with open(out, "w") as f:
            json.dump(report, f, indent=2)
        print(json.dumps(report, indent=2))
        print(f"\nAGREEMENT CHECK FAILED ({len(failures)} issue(s))", file=sys.stderr)
        sys.exit(1)

    styles = {e: legs[e]["computation_style"] for e in legs}
    if len(set(styles.values())) != len(legs):
        failures.append(f"legs do not have distinct computation styles: {styles}")
    for e, r in legs.items():
        if r.get("reads_peer_result") is not False:
            failures.append(f"{e}: reads_peer_result is not False")

    max_float_diff = 0.0
    for n in ("5", "6", "7"):
        rows = {e: legs[e]["per_N"][n] for e in LEGS}
        for k in THREE_LEG_INTEGER_KEYS:
            vals = {e: rows[e].get(k) for e in LEGS}
            if len(set(vals.values())) != 1:
                failures.append(f"N={n} {k}: {vals}")
        for k in EXACT_JULIA_INTEGER_KEYS:
            vals = {e: rows[e].get(k) for e in ("exact", "julia")}
            if len(set(vals.values())) != 1:
                failures.append(f"N={n} {k}: {vals}")
        for k in FLOAT_KEYS:
            vals = {e: float(rows[e][k]) for e in LEGS}
            local = max(abs(v - vals["exact"]) for v in vals.values())
            max_float_diff = max(max_float_diff, local)
            if local > 1e-10:
                failures.append(f"N={n} {k}: max diff {local} > 1e-10 values={vals}")
        # the load-bearing facts themselves
        ex = rows["exact"]
        if not ex["running_mean_threshold_running_X_noncommute"] > 0:
            failures.append(f"N={n}: no order-dependence (running-X noncommute == 0)")
        if ex["running_mean_threshold_fixed_reference_noncommute"] != 0:
            failures.append(f"N={n}: isolator broken (fixed-reference noncommute != 0)")
        if ex["floor_mean_threshold_running_X_noncommute"] != 0:
            failures.append(f"N={n}: floor-mean negative control broken")
        if ex["ensemble_consistency_noncommute"] != 0:
            failures.append(f"N={n}: ensemble-consistency negative control broken")
        if ex["competitive_exclusion_noncommute"] != 0:
            failures.append(f"N={n}: competitive-exclusion negative control broken")
        if ex["minority_frustration_noncommute"] != 0:
            failures.append(f"N={n}: minority-frustration negative control broken")

    # ceilings honest
    for e, r in legs.items():
        if r["classification"] != "scratch_diagnostic":
            failures.append(f"{e}: classification != scratch_diagnostic")
        if r["promotion_allowed"] is not False:
            failures.append(f"{e}: promotion_allowed not False")

    integer_match = "exact" if not failures else "diff"
    report = {
        "schema": "codex_ratchet.agreement_result.v1",
        "sim_id": SIM_ID,
        "engines_present": list(LEGS),
        "computation_styles": styles,
        "per_N_running_X_noncommute": {n: legs["exact"]["per_N"][n]["running_mean_threshold_running_X_noncommute"] for n in ("5", "6", "7")},
        "per_N_fixed_reference_noncommute": {n: legs["exact"]["per_N"][n]["running_mean_threshold_fixed_reference_noncommute"] for n in ("5", "6", "7")},
        "two_legs_agree": len([
            f for f in failures if "julia" not in f and "competitive" not in f and "minority" not in f
        ]) == 0,
        "three_legs_agree": len(failures) == 0,
        "agreement_ok": len(failures) == 0,
        "observables_match": {"integer": integer_match, "float_max": max_float_diff},
        "failures": failures,
        "classification": "scratch_diagnostic",
        "promotion_allowed": False,
        "formal_admission_allowed": False,
    }
    out = os.path.join(HERE, "results", f"{SIM_ID}_agreement_results.json")
    with open(out, "w") as f:
        json.dump(report, f, indent=2)
    print(json.dumps(report, indent=2))
    if failures:
        print(f"\nAGREEMENT CHECK FAILED ({len(failures)} issue(s))", file=sys.stderr)
        sys.exit(1)
    print("\nAGREEMENT CHECK OK: exact, jax, and julia legs agree on the order-dependence invariant.")


if __name__ == "__main__":
    main()
