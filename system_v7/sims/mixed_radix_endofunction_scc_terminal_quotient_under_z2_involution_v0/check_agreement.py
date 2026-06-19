#!/usr/bin/env python3
"""Cross-leg agreement check for the mixed-radix endofunction sim."""

from __future__ import annotations

import json
import os
import sys

SIM_ID = "mixed_radix_endofunction_scc_terminal_quotient_under_z2_involution_v0"
HERE = os.path.dirname(os.path.abspath(__file__))


def norm_classes(value):
    return sorted(sorted(int(x) for x in row) for row in value)


def main() -> int:
    base = os.path.join(HERE, "results", f"{SIM_ID}_")
    legs = {name: json.load(open(base + name + "_results.json", encoding="utf-8")) for name in ("julia", "jax", "pytorch")}
    failures = []
    styles = {name: leg["computation_style"] for name, leg in legs.items()}
    if len(set(styles.values())) != 3:
        failures.append(f"computation_style values are not distinct: {styles}")
    for name, leg in legs.items():
        if leg.get("reads_peer_result") is not False:
            failures.append(f"{name}: reads_peer_result is not false")
        if leg.get("classification") != "scratch_diagnostic":
            failures.append(f"{name}: classification is not scratch_diagnostic")
        if leg.get("promotion_allowed") is not False or leg.get("formal_admission_allowed") is not False:
            failures.append(f"{name}: ceilings are not fenced")
        if leg.get("does_not_self_upgrade") is not True:
            failures.append(f"{name}: does_not_self_upgrade is not true")

    orientations = ["map_plus", "map_minus"]
    for orientation in orientations:
        counts = {name: legs[name]["terminal_scc_count"][orientation] for name in legs}
        sizes = {name: sorted(legs[name]["terminal_scc_sizes"][orientation]) for name in legs}
        scc_counts = {name: legs[name]["scc_count"][orientation] for name in legs}
        if len(set(counts.values())) != 1:
            failures.append(f"{orientation}: terminal_scc_count disagreement: {counts}")
        if len({json.dumps(v) for v in sizes.values()}) != 1:
            failures.append(f"{orientation}: terminal_scc_sizes disagreement: {sizes}")
        if len(set(scc_counts.values())) != 1:
            failures.append(f"{orientation}: scc_count disagreement: {scc_counts}")
        class_rows = {name: norm_classes(legs[name]["scc_classes"][orientation]) for name in legs}
        if len({json.dumps(v) for v in class_rows.values()}) != 1:
            failures.append(f"{orientation}: scc_classes disagreement")
        quotient_rows = {name: norm_classes(legs[name]["quotient_classes"][orientation]) for name in legs}
        if len({json.dumps(v) for v in quotient_rows.values()}) != 1:
            failures.append(f"{orientation}: quotient_classes disagreement")

    expected_equivariance = {
        "conserved_control": True,
        "parity_flipping_law": False,
        "reference_toggle_law": True
    }
    for name, leg in legs.items():
        for orientation in orientations:
            observed = leg["involution_is_equivariant"][orientation]
            for law, expected in expected_equivariance.items():
                if observed.get(law) is not expected:
                    failures.append(f"{name}/{orientation}/{law}: equivariance {observed.get(law)} != {expected}")

    smt = legs["jax"].get("smt_equivariance_flip", {})
    if smt.get("z3_equivariant_map") != "unsat":
        failures.append(f"z3 equivariant verdict wrong: {smt.get('z3_equivariant_map')}")
    if smt.get("z3_nonequivariant_map") != "sat":
        failures.append(f"z3 nonequivariant verdict wrong: {smt.get('z3_nonequivariant_map')}")
    if smt.get("cvc5_equivariant_map") != "unsat":
        failures.append(f"cvc5 equivariant verdict wrong: {smt.get('cvc5_equivariant_map')}")
    if smt.get("cvc5_nonequivariant_map") != "sat":
        failures.append(f"cvc5 nonequivariant verdict wrong: {smt.get('cvc5_nonequivariant_map')}")
    if smt.get("real_structural_flip_confirmed") is not True:
        failures.append("real_structural_flip_confirmed is not true")
    for orientation in orientations:
        row = smt.get("per_orientation", {}).get(orientation, {})
        if not (
            row.get("z3_equivariant_map") == "unsat"
            and row.get("z3_nonequivariant_map") == "sat"
            and row.get("cvc5_equivariant_map") == "unsat"
            and row.get("cvc5_nonequivariant_map") == "sat"
        ):
            failures.append(f"{orientation}: SMT per-orientation flip missing or wrong: {row}")

    report = {
        "sim_id": SIM_ID,
        "computation_styles": styles,
        "terminal_scc_count": {orientation: legs["julia"]["terminal_scc_count"][orientation] for orientation in orientations},
        "terminal_scc_sizes": {orientation: legs["julia"]["terminal_scc_sizes"][orientation] for orientation in orientations},
        "scc_count": {orientation: legs["julia"]["scc_count"][orientation] for orientation in orientations},
        "quotient_class_count": {orientation: legs["julia"]["quotient_class_count"][orientation] for orientation in orientations},
        "smt_equivariance_flip": smt,
        "all_three_agree": len(failures) == 0,
        "failures": failures,
        "classification": "scratch_diagnostic",
        "promotion_allowed": False,
        "formal_admission_allowed": False
    }
    out = os.path.join(HERE, "results", f"{SIM_ID}_agreement_results.json")
    with open(out, "w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2, sort_keys=True)
        handle.write("\n")
    print(json.dumps(report, indent=2, sort_keys=True))
    if failures:
        print(f"AGREEMENT CHECK FAILED ({len(failures)} issue(s))", file=sys.stderr)
        return 1
    print("AGREEMENT CHECK OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
