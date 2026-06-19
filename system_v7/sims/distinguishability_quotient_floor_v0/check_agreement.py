#!/usr/bin/env python3
"""Cross-leg agreement check (separate verification step, not part of any leg's
own computation). Reads the three result JSONs and confirms they agree on the
shared invariant: the quotient class sets, the quotient counts, the probe
expectations (to 1e-9), the SMT real-vs-erased flip, and the autograd identity.

This script does NOT recompute the physics; it only adjudicates that three
INDEPENDENT computations landed on the same invariant. Exit 0 iff agreement.
"""

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SIM_ID = "distinguishability_quotient_floor_v0"


def norm(classes):
    return sorted(sorted(c) for c in classes)


def main():
    base = os.path.join(HERE, "results", f"{SIM_ID}_")
    legs = {e: json.load(open(base + e + "_results.json")) for e in ("julia", "jax", "pytorch")}

    failures = []

    # distinct computation styles
    styles = {e: legs[e]["computation_style"] for e in legs}
    if len(set(styles.values())) != 3:
        failures.append(f"engine legs do not have 3 distinct computation styles: {styles}")

    # no leg reads a peer result
    for e, r in legs.items():
        if r.get("reads_peer_result") is not False:
            failures.append(f"{e}: reads_peer_result is not False")

    # quotient agreement
    qf = {e: norm(r["quotient_classes_full"]) for e, r in legs.items()}
    qe = {e: norm(r["quotient_classes_erased"]) for e, r in legs.items()}
    if len({str(v) for v in qf.values()}) != 1:
        failures.append(f"full quotient classes disagree: {qf}")
    if len({str(v) for v in qe.values()}) != 1:
        failures.append(f"erased quotient classes disagree: {qe}")

    # the flip itself: full has more classes than erased
    cf = legs["julia"]["quotient_class_count_full"]
    ce = legs["julia"]["quotient_class_count_erased"]
    if not cf > ce:
        failures.append(f"no quotient flip: full={cf} erased={ce} (expected full > erased)")

    # expectation agreement to 1e-9
    for e in ("jax", "pytorch"):
        for lab in legs["julia"]["state_labels"]:
            for a, b in zip(legs["julia"]["probe_expectations_full"][lab], legs[e]["probe_expectations_full"][lab]):
                if abs(a - b) > 1e-9:
                    failures.append(f"expectation mismatch julia vs {e} at {lab}: {a} != {b}")

    # SMT flip
    smt = legs["jax"]["smt_flip"]
    if not (smt["z3_full_M"] == "sat" and smt["z3_erased_M"] == "unsat"):
        failures.append(f"z3 flip wrong: full={smt['z3_full_M']} erased={smt['z3_erased_M']}")
    if not (smt["cvc5_full_M"] == "sat" and smt["cvc5_erased_M"] == "unsat"):
        failures.append(f"cvc5 flip wrong: full={smt['cvc5_full_M']} erased={smt['cvc5_erased_M']}")
    if not smt["real_vs_erased_flip_confirmed"]:
        failures.append("real_vs_erased_flip_confirmed is False")

    # autograd identity
    if not legs["pytorch"]["autograd_receipt"]["jacobian_is_identity_selection"]:
        failures.append("autograd jacobian is not the identity selection")

    # ceilings honest
    for e, r in legs.items():
        if r["classification"] != "scratch_diagnostic":
            failures.append(f"{e}: classification != scratch_diagnostic")
        if r["promotion_allowed"] is not False or r["formal_admission_allowed"] is not False:
            failures.append(f"{e}: ceilings not fenced")

    report = {
        "sim_id": SIM_ID,
        "computation_styles": styles,
        "quotient_classes_full": qf["julia"],
        "quotient_classes_erased": qe["julia"],
        "quotient_count_full": cf,
        "quotient_count_erased": ce,
        "smt_flip": {
            "z3": [smt["z3_full_M"], smt["z3_erased_M"]],
            "cvc5": [smt["cvc5_full_M"], smt["cvc5_erased_M"]],
            "confirmed": smt["real_vs_erased_flip_confirmed"],
        },
        "autograd_identity_ok": legs["pytorch"]["autograd_receipt"]["jacobian_is_identity_selection"],
        "all_three_agree": len(failures) == 0,
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
    print("\nAGREEMENT CHECK OK: three independent legs agree on the invariant.")


if __name__ == "__main__":
    main()
