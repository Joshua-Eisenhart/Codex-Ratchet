#!/usr/bin/env python3
"""Agreement check for finite_distinguishability_quotient_forced_or_installed_carrier_v0.

This is a separate adjudicator. It reads the three engine result JSONs and exits
0 iff the shared invariants, controls, SMT flip, minima, and ceilings agree.
"""

import json
import os
import sys
from datetime import datetime, timezone

SIM_ID = "finite_distinguishability_quotient_forced_or_installed_carrier_v0"
HERE = os.path.dirname(os.path.abspath(__file__))
ENGINES = ("julia", "jax", "pytorch")
VERDICTS = {"forced", "installed", "plural_incomparable", "inconclusive"}


def norm_classes(classes):
    return sorted(sorted(c) for c in classes)


def load_leg(engine):
    with open(os.path.join(HERE, "results", f"{SIM_ID}_{engine}_results.json")) as f:
        return json.load(f)


def final_verdict(survivors, mins, pre, controls_ok, smt):
    if not controls_ok:
        return "inconclusive", "at least one required control failed"
    smt_ok = (
        smt.get("z3_full") == "unsat"
        and smt.get("z3_erased") == "sat"
        and smt.get("cvc5_full") == "unsat"
        and smt.get("cvc5_erased") == "sat"
        and smt.get("real_vs_erased_flip_confirmed") is True
    )
    real_ok = smt.get("z3_real_operator_full") == "sat" and smt.get("cvc5_real_operator_full") == "sat"
    if not smt_ok or not real_ok:
        return "inconclusive", "SMT flip or real-operator sufficiency did not behave"
    if len(mins) >= 2 and all(not pre[a][b] and not pre[b][a] for a in mins for b in mins if a != b):
        return "plural_incomparable", "minimal survivor set contains pairwise-incomparable structures"
    if "C4" in survivors and any(c != "C4" and pre[c]["C4"] and not pre["C4"][c] for c in survivors):
        return "installed", "full SMT UNSAT forces noncommuting updates, erased SMT SAT isolates N01, real-operator SAT blocks complex-forced, and Min(Surv) has a stricter weaker survivor below C4"
    if "C4" in survivors:
        return "forced", "no strictly weaker survivor below C4"
    return "inconclusive", "C4 did not survive or survivor set is empty"


def main():
    legs = {engine: load_leg(engine) for engine in ENGINES}
    failures = []

    styles = {engine: legs[engine].get("computation_style") for engine in ENGINES}
    if len(set(styles.values())) != 3:
        failures.append(f"engine legs do not have 3 distinct computation styles: {styles}")

    hashes = {engine: legs[engine].get("source_sha256") for engine in ENGINES}
    if len(set(hashes.values())) != 1:
        failures.append(f"source_sha256 does not agree as spec hash: {hashes}")

    for engine, result in legs.items():
        if result.get("reads_peer_result") is not False:
            failures.append(f"{engine}: reads_peer_result is not false")
        if result.get("classification") != "scratch_diagnostic":
            failures.append(f"{engine}: classification is not scratch_diagnostic")
        if result.get("promotion_allowed") is not False:
            failures.append(f"{engine}: promotion_allowed is not false")
        if result.get("formal_admission_allowed") is not False:
            failures.append(f"{engine}: formal_admission_allowed is not false")
        if result.get("does_not_self_upgrade") is not True:
            failures.append(f"{engine}: does_not_self_upgrade is not true")
        if "F01" not in result.get("lineage", {}) or "N01" not in result.get("lineage", {}):
            failures.append(f"{engine}: F01/N01 lineage missing")
        if result.get("computed_verdict") not in VERDICTS:
            failures.append(f"{engine}: computed_verdict outside allowed set")

    q_full = {engine: norm_classes(legs[engine]["quotient_classes_full"]) for engine in ENGINES}
    q_erased = {engine: norm_classes(legs[engine]["quotient_classes_erased"]) for engine in ENGINES}
    if len({json.dumps(v, sort_keys=True) for v in q_full.values()}) != 1:
        failures.append(f"full quotient classes disagree: {q_full}")
    if len({json.dumps(v, sort_keys=True) for v in q_erased.values()}) != 1:
        failures.append(f"erased quotient classes disagree: {q_erased}")
    if not legs["julia"]["quotient_class_count_erased"] < legs["julia"]["quotient_class_count_full"]:
        failures.append("probe erase did not strictly reduce quotient class count")

    survival = {engine: legs[engine]["per_structure_survival"] for engine in ENGINES}
    if len({json.dumps(v, sort_keys=True) for v in survival.values()}) != 1:
        failures.append("per-structure survival tables disagree")

    preorders = {engine: legs[engine]["preorder_matrix"] for engine in ENGINES}
    if len({json.dumps(v, sort_keys=True) for v in preorders.values()}) != 1:
        failures.append("preorder matrices disagree")

    surv_sets = {engine: legs[engine]["Surv"] for engine in ENGINES}
    min_sets = {engine: legs[engine]["MinSurv"] for engine in ENGINES}
    if len({json.dumps(v, sort_keys=True) for v in surv_sets.values()}) != 1:
        failures.append(f"Surv disagree: {surv_sets}")
    if len({json.dumps(v, sort_keys=True) for v in min_sets.values()}) != 1:
        failures.append(f"MinSurv disagree: {min_sets}")

    controls = {engine: legs[engine]["controls"] for engine in ENGINES}
    if len({json.dumps(v, sort_keys=True) for v in controls.values()}) != 1:
        failures.append("controls disagree")
    controls_ok = all(row.get("passed") is True for row in legs["julia"]["controls"].values())
    if not controls_ok:
        failures.append(f"not all controls passed: {legs['julia']['controls']}")

    if legs["julia"]["element_noncommutation_witness"].get("exists") is not True:
        failures.append("active element noncommutation witness missing")
    if legs["julia"]["commuting_control_element_witness"].get("exists") is not False:
        failures.append("commuting control has a noncommutation witness")

    smt = legs["jax"].get("smt_flip", {})
    if not (
        smt.get("z3_full") == "unsat"
        and smt.get("z3_erased") == "sat"
        and smt.get("cvc5_full") == "unsat"
        and smt.get("cvc5_erased") == "sat"
        and smt.get("real_vs_erased_flip_confirmed") is True
    ):
        failures.append(f"SMT flip wrong: {smt}")
    if not (smt.get("z3_real_operator_full") == "sat" and smt.get("cvc5_real_operator_full") == "sat"):
        failures.append(f"real-operator sufficiency SMT wrong: {smt}")

    verdict_value, verdict_reason = final_verdict(legs["julia"]["Surv"], legs["julia"]["MinSurv"], legs["julia"]["preorder_matrix"], controls_ok, smt)
    if verdict_value != "installed":
        failures.append(f"final verdict was {verdict_value}, expected installed for this measured fixture")

    report = {
        "schema": "codex_ratchet.agreement_result.v1",
        "sim_id": SIM_ID,
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "classification": "scratch_diagnostic",
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "does_not_self_upgrade": True,
        "reads_peer_result": False,
        "source_sha256": legs["julia"]["source_sha256"],
        "computation_styles": styles,
        "quotient_classes_full": q_full["julia"],
        "quotient_classes_erased": q_erased["julia"],
        "quotient_class_count_full": legs["julia"]["quotient_class_count_full"],
        "quotient_class_count_erased": legs["julia"]["quotient_class_count_erased"],
        "per_structure_survival": legs["julia"]["per_structure_survival"],
        "preorder_definition": legs["julia"]["preorder_definition"],
        "preorder_matrix": legs["julia"]["preorder_matrix"],
        "Surv": legs["julia"]["Surv"],
        "MinSurv": legs["julia"]["MinSurv"],
        "controls": legs["julia"]["controls"],
        "smt_flip": smt,
        "computed_verdict": verdict_value,
        "computed_verdict_reason": verdict_reason,
        "all_three_agree": len(failures) == 0,
        "failures": failures,
        "lineage": legs["julia"]["lineage"],
    }
    out = os.path.join(HERE, "results", f"{SIM_ID}_agreement_results.json")
    with open(out, "w") as f:
        json.dump(report, f, indent=2)
    print(json.dumps(report, indent=2))
    if failures:
        print(f"\nAGREEMENT CHECK FAILED ({len(failures)} issue(s))", file=sys.stderr)
        sys.exit(1)
    print(f"\nAGREEMENT CHECK OK: final computed verdict = {verdict_value}")


if __name__ == "__main__":
    main()
