#!/usr/bin/env python3
"""Agreement check for the finite probe quotient inverse-limit tower.

This is a separate adjudicator. It reads the three engine result JSONs and exits
0 iff the shared invariants agree and the required ceilings remain fenced.
"""

import json
import os
import sys
from datetime import datetime, timezone

SIM_ID = "finite_probe_quotient_inverse_limit_tower_1q_through_4q"
HERE = os.path.dirname(os.path.abspath(__file__))
DEPTHS = ["1q", "2q", "3q", "4q"]
SEAL_FIELD = "seals_by_construction_on_marginal_closed_fixture"


def norm_classes(classes):
    return sorted(sorted(c) for c in classes)


def load_leg(engine):
    path = os.path.join(HERE, "results", f"{SIM_ID}_{engine}_results.json")
    with open(path) as f:
        return json.load(f)


def main():
    legs = {engine: load_leg(engine) for engine in ("julia", "jax", "pytorch")}
    failures = []

    styles = {engine: legs[engine].get("computation_style") for engine in legs}
    if len(set(styles.values())) != 3:
        failures.append(f"engine legs do not have 3 distinct computation styles: {styles}")

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
        if result.get("ladder_useful_depth") != "3q":
            failures.append(f"{engine}: ladder_useful_depth is not 3q")
        if result.get("ladder_one_beyond") != "4q":
            failures.append(f"{engine}: ladder_one_beyond is not 4q")

    required_4q_states = {
        "w4",
        "dicke4_2",
        "ghz_ab_prod_cd",
        "bell_ac_prod_bd",
        "mix_0000_1111",
    }
    for engine, result in legs.items():
        labels_4q = set(result["rungs"]["4q"]["state_labels"])
        missing = sorted(required_4q_states - labels_4q)
        if missing:
            failures.append(f"{engine}: missing required enriched 4q states: {missing}")

    quotient_counts = {}
    quotient_classes = {}
    for depth in DEPTHS:
        quotient_counts[depth] = {
            engine: {
                "full": legs[engine]["rungs"][depth]["quotient_class_count_full"],
                "erased": legs[engine]["rungs"][depth]["quotient_class_count_erased"],
            }
            for engine in legs
        }
        quotient_classes[depth] = {
            engine: {
                "full": norm_classes(legs[engine]["rungs"][depth]["quotient_classes_full"]),
                "erased": norm_classes(legs[engine]["rungs"][depth]["quotient_classes_erased"]),
            }
            for engine in legs
        }
        if len({json.dumps(v, sort_keys=True) for v in quotient_counts[depth].values()}) != 1:
            failures.append(f"{depth}: quotient counts disagree: {quotient_counts[depth]}")
        if len({json.dumps(v, sort_keys=True) for v in quotient_classes[depth].values()}) != 1:
            failures.append(f"{depth}: quotient classes disagree")
        for engine in legs:
            if depth not in legs[engine]["rungs"]:
                failures.append(f"{engine}: missing rung {depth}")

    for depth in DEPTHS:
        for label in legs["julia"]["rungs"][depth]["state_labels"]:
            for engine in ("jax", "pytorch"):
                if label not in legs[engine]["rungs"][depth]["probe_expectations_full"]:
                    failures.append(f"{engine}: missing expectations for {depth}/{label}")
                    continue
                a = legs["julia"]["rungs"][depth]["probe_expectations_full"][label]
                b = legs[engine]["rungs"][depth]["probe_expectations_full"][label]
                if len(a) != len(b) or any(abs(float(x) - float(y)) > 1e-8 for x, y in zip(a, b)):
                    failures.append(f"{depth}/{label}: full probe expectations disagree for julia vs {engine}")

    smt = legs["jax"]["smt_flip"]["quotient_class_flip"]
    if not (smt["z3_full"] == "sat" and smt["z3_erased"] == "unsat"):
        failures.append(f"z3 flip wrong: {smt['z3_full']}/{smt['z3_erased']}")
    if not (smt["cvc5_full"] == "sat" and smt["cvc5_erased"] == "unsat"):
        failures.append(f"cvc5 flip wrong: {smt['cvc5_full']}/{smt['cvc5_erased']}")
    if smt.get("real_vs_erased_flip_confirmed") is not True:
        failures.append("real_vs_erased_flip_confirmed is not true")

    if legs["pytorch"]["autograd_receipt"].get("jacobian_matches_structural_identity") is not True:
        failures.append("PyTorch autograd structural identity failed")

    compatibility = {
        engine: {
            SEAL_FIELD: legs[engine]["compatibility"][SEAL_FIELD],
            "one_beyond_self_seals": legs[engine]["compatibility"]["one_beyond_self_seals"],
        }
        for engine in legs
    }
    if len({json.dumps(v, sort_keys=True) for v in compatibility.values()}) != 1:
        failures.append(f"compatibility/self-seal verdicts disagree: {compatibility}")
    if compatibility["julia"][SEAL_FIELD] is not True or compatibility["julia"]["one_beyond_self_seals"] is not True:
        failures.append(f"tower did not self-seal: {compatibility['julia']}")

    open_state_seal_test = {}
    for engine in legs:
        block = legs[engine]["compatibility"].get("open_state_seal_test")
        if not isinstance(block, dict):
            failures.append(f"{engine}: missing open_state_seal_test block")
            continue
        projection_booleans = {
            f"{row.get('higher_state')}->{row.get('target_depth')}:{row.get('kept_subset')}": row.get("lands_in_existing_nonclosure_class")
            for row in block.get("projections", [])
        }
        open_state_seal_test[engine] = {
            "open_fixture_seals": block.get("open_fixture_seals"),
            "total_projection_count": block.get("total_projection_count"),
            "landing_projection_count": block.get("landing_projection_count"),
            "missing_projection_count": block.get("missing_projection_count"),
            "projection_booleans": projection_booleans,
        }
    if open_state_seal_test and len({json.dumps(v, sort_keys=True) for v in open_state_seal_test.values()}) != 1:
        failures.append(f"open_state_seal_test verdicts disagree: {open_state_seal_test}")

    forecast_matches = {
        engine: {depth: legs[engine]["forecast"]["forecast_matches_computed"][depth]["matches"] for depth in DEPTHS}
        for engine in legs
    }
    if any(not all(v.values()) for v in forecast_matches.values()):
        failures.append(f"forecast check did not match on all rungs: {forecast_matches}")
    forecast_1q = {engine: legs[engine]["forecast"]["forecast_matches_computed"]["1q"] for engine in legs}
    for engine, block in forecast_1q.items():
        if block.get("hopf_fibration_computed") is not False:
            failures.append(f"{engine}: 1q forecast does not explicitly fence Hopf fibration computation")
        claim = block.get("claim", "")
        if "Bloch-radius separation only" not in claim or "NOT tested" not in claim:
            failures.append(f"{engine}: 1q forecast claim is not honest about Bloch-only evidence")
    forecast_4q = {engine: legs[engine]["forecast"]["forecast_matches_computed"]["4q"] for engine in legs}
    for engine, block in forecast_4q.items():
        if block.get("rank_tuple_lattice_computed") is not True:
            failures.append(f"{engine}: 4q forecast did not compute the finite rank-tuple lattice consistency object")
        if block.get("all_cross_rung_consistent") is not True:
            failures.append(f"{engine}: 4q cross-rung rank consistency failed")
        if len(block.get("lattice_nodes", [])) < 3:
            failures.append(f"{engine}: 4q rank-tuple lattice has fewer than 3 nodes")
        rank_tuples = block.get("computed_rank_tuple_lattice", {})
        if rank_tuples.get("w4") in (None, [], rank_tuples.get("q0000")):
            failures.append(f"{engine}: w4 rank tuple missing or product-like")
        schmidt = legs[engine]["rungs"]["4q"]["representative_states"]
        w4_coeffs = schmidt.get("w4", {}).get("schmidt_coefficients", {}).get("coefficients_by_cut", {})
        ghz4_coeffs = schmidt.get("ghz4", {}).get("schmidt_coefficients", {}).get("coefficients_by_cut", {})
        q0000_coeffs = schmidt.get("q0000", {}).get("schmidt_coefficients", {}).get("coefficients_by_cut", {})
        if not w4_coeffs or w4_coeffs == ghz4_coeffs or w4_coeffs == q0000_coeffs:
            failures.append(f"{engine}: w4 Schmidt coefficient profile missing or not distinct from ghz4/product")
    forecast_gate_projection = {
        engine: {
            "1q_claim": forecast_1q[engine].get("claim"),
            "1q_hopf_fibration_computed": forecast_1q[engine].get("hopf_fibration_computed"),
            "4q_claim": forecast_4q[engine].get("claim"),
            "4q_rank_tuple_lattice_computed": forecast_4q[engine].get("rank_tuple_lattice_computed"),
            "4q_matches": forecast_4q[engine].get("matches"),
            "4q_all_cross_rung_consistent": forecast_4q[engine].get("all_cross_rung_consistent"),
            "4q_lattice_nodes": forecast_4q[engine].get("lattice_nodes"),
        }
        for engine in legs
    }
    if len({json.dumps(v, sort_keys=True) for v in forecast_gate_projection.values()}) != 1:
        failures.append("forecast gate fields disagree across engines")

    negative_controls = {}
    for engine, result in legs.items():
        controls = result.get("negative_controls")
        if not isinstance(controls, dict):
            failures.append(f"{engine}: missing negative_controls block")
            continue
        negative_controls[engine] = {
            name: {
                "fired": controls.get(name, {}).get("fired"),
                "violates_compatibility": controls.get(name, {}).get("violates_compatibility"),
                "name_echo_would_pass": controls.get(name, {}).get("name_echo_would_pass"),
                "partial_trace_rejects": controls.get(name, {}).get("partial_trace_rejects"),
            }
            for name in ("perturbed_marginal_excluded", "label_echo_trap")
        }
        if controls.get("perturbed_marginal_excluded", {}).get("fired") is not True:
            failures.append(f"{engine}: perturbed_marginal_excluded did not fire")
        if controls.get("perturbed_marginal_excluded", {}).get("violates_compatibility") is not True:
            failures.append(f"{engine}: perturbed marginal was not excluded from class lookup")
        label_trap = controls.get("label_echo_trap", {})
        if label_trap.get("fired") is not True:
            failures.append(f"{engine}: label_echo_trap did not fire")
        if label_trap.get("name_echo_would_pass") is not True or label_trap.get("partial_trace_rejects") is not True:
            failures.append(f"{engine}: label echo trap lacks name-pass plus partial-trace-reject evidence")
    if negative_controls and len({json.dumps(v, sort_keys=True) for v in negative_controls.values()}) != 1:
        failures.append(f"negative control verdicts disagree: {negative_controls}")

    report = {
        "schema": "codex_ratchet.agreement_result.v1",
        "sim_id": SIM_ID,
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "computation_styles": styles,
        "hilbert_dimensions_by_depth": {
            depth: legs["julia"]["rungs"][depth]["hilbert_dimension"] for depth in DEPTHS
        },
        "quotient_counts": quotient_counts["julia"] if "julia" in quotient_counts else quotient_counts,
        "per_rung_counts": {depth: quotient_counts[depth]["julia"] for depth in DEPTHS},
        "per_rung_quotient_classes": {depth: quotient_classes[depth]["julia"] for depth in DEPTHS},
        "smt_flip": {
            "z3": [smt["z3_full"], smt["z3_erased"]],
            "cvc5": [smt["cvc5_full"], smt["cvc5_erased"]],
            "confirmed": smt["real_vs_erased_flip_confirmed"],
        },
        "autograd_identity_ok": legs["pytorch"]["autograd_receipt"]["jacobian_matches_structural_identity"],
        "compatibility": compatibility["julia"],
        "open_state_seal_test": legs["julia"]["compatibility"].get("open_state_seal_test", {}),
        "forecast_matches_computed": forecast_matches["julia"],
        "forecast_gate_projection": forecast_gate_projection.get("julia", {}),
        "negative_controls": negative_controls.get("julia", {}),
        "ladder_useful_depth": "3q",
        "ladder_useful_depth_evidence": legs["julia"]["ladder_useful_depth_evidence"],
        "ladder_one_beyond": "4q",
        "ladder_one_beyond_evidence": legs["julia"]["ladder_one_beyond_evidence"],
        "all_three_agree": len(failures) == 0,
        "failures": failures,
        "classification": "scratch_diagnostic",
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "does_not_self_upgrade": True,
    }

    out = os.path.join(HERE, "results", f"{SIM_ID}_agreement_results.json")
    with open(out, "w") as f:
        json.dump(report, f, indent=2)
    print(json.dumps(report, indent=2))
    if failures:
        print(f"\nAGREEMENT CHECK FAILED ({len(failures)} issue(s))", file=sys.stderr)
        sys.exit(1)
    print("\nAGREEMENT CHECK OK: three independent legs agree on shared invariants.")


if __name__ == "__main__":
    main()
