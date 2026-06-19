#!/usr/bin/env python3
"""Cross-leg agreement check (separate verification step). Confirms the EXACT
leg (explicit Python-set operations) and the JAX leg (boolean mask over the full
enumeration) -- two distinct representations -- landed on the same load-bearing
invariant: at N in {5,6,7}, running_mean_threshold noncommutes under the running
survivor set, commutes under the fixed reference, and ensemble_consistency is
confluent. Exit 0 iff they agree. This script does NOT recompute the physics.
"""

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SIM_ID = "survivor_set_running_mean_threshold_noncommutation_v0"


def main():
    base = os.path.join(HERE, "results", f"{SIM_ID}_")
    legs = {e: json.load(open(base + e + "_results.json")) for e in ("exact", "jax")}

    failures = []

    styles = {e: legs[e]["computation_style"] for e in legs}
    if len(set(styles.values())) != len(legs):
        failures.append(f"legs do not have distinct computation styles: {styles}")
    for e, r in legs.items():
        if r.get("reads_peer_result") is not False:
            failures.append(f"{e}: reads_peer_result is not False")

    for n in ("5", "6", "7"):
        ex = legs["exact"]["per_N"][n]
        jx = legs["jax"]["per_N"][n]
        keys = [
            "running_mean_threshold_running_X_noncommute",
            "running_mean_threshold_fixed_reference_noncommute",
            "ensemble_consistency_noncommute",
        ]
        for k in keys:
            if ex[k] != jx[k]:
                failures.append(f"N={n} {k}: exact={ex[k]} jax={jx[k]}")
        # the load-bearing facts themselves
        if not ex["running_mean_threshold_running_X_noncommute"] > 0:
            failures.append(f"N={n}: no order-dependence (running-X noncommute == 0)")
        if ex["running_mean_threshold_fixed_reference_noncommute"] != 0:
            failures.append(f"N={n}: isolator broken (fixed-reference noncommute != 0)")

    # ceilings honest
    for e, r in legs.items():
        if r["classification"] != "scratch_diagnostic":
            failures.append(f"{e}: classification != scratch_diagnostic")
        if r["promotion_allowed"] is not False:
            failures.append(f"{e}: promotion_allowed not False")

    report = {
        "sim_id": SIM_ID,
        "computation_styles": styles,
        "per_N_running_X_noncommute": {n: legs["exact"]["per_N"][n]["running_mean_threshold_running_X_noncommute"] for n in ("5", "6", "7")},
        "per_N_fixed_reference_noncommute": {n: legs["exact"]["per_N"][n]["running_mean_threshold_fixed_reference_noncommute"] for n in ("5", "6", "7")},
        "two_legs_agree": len(failures) == 0,
        "failures": failures,
        "classification": "scratch_diagnostic",
        "promotion_allowed": False,
    }
    out = os.path.join(HERE, "results", f"{SIM_ID}_agreement_results.json")
    with open(out, "w") as f:
        json.dump(report, f, indent=2)
    print(json.dumps(report, indent=2))
    if failures:
        print(f"\nAGREEMENT CHECK FAILED ({len(failures)} issue(s))", file=sys.stderr)
        sys.exit(1)
    print("\nAGREEMENT CHECK OK: exact and jax legs agree on the order-dependence invariant.")


if __name__ == "__main__":
    main()
