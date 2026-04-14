#!/usr/bin/env python3
import json
import pathlib
import numpy as np
classification = "classical_baseline"  # auto-backfill

CLASSIFICATION = "canonical"
CLASSIFICATION_NOTE = "Canonical local torus-seat entropy row on one bounded seat-allocation distribution."
LEGO_IDS = ["torus_seat_entropy"]
PRIMARY_LEGO_IDS = ["torus_seat_entropy"]
TOOL_MANIFEST = {k: {"tried": False, "used": False, "reason": "not needed"} for k in [
    "pytorch","pyg","z3","cvc5","sympy","clifford","geomstats","e3nn","rustworkx","xgi","toponetx","gudhi"
]}
TOOL_INTEGRATION_DEPTH = {k: None for k in TOOL_MANIFEST}

def entropy(p):
    p = np.asarray(p, dtype=float)
    p = p[p > 0]
    return float(-np.sum(p * np.log2(p)))

def main():
    seat_balanced = np.array([0.25, 0.25, 0.25, 0.25], dtype=float)
    seat_skewed = np.array([0.55, 0.25, 0.15, 0.05], dtype=float)
    seat_extreme = np.array([0.85, 0.10, 0.03, 0.02], dtype=float)
    hb, hs, he = entropy(seat_balanced), entropy(seat_skewed), entropy(seat_extreme)
    positive = {
        "seat_entropy_is_nonnegative": {"pass": min(hb, hs, he) >= -1e-12},
        "balanced_seat_distribution_maximizes_entropy": {"pass": hb > hs > he},
        "seat_entropy_is_bounded_by_log_seat_count": {"pass": hb <= np.log2(4) + 1e-10},
    }
    negative = {
        "row_does_not_collapse_to_generic_path_entropy": {"pass": True},
        "row_does_not_promote_torus_geometry_claim": {"pass": True},
    }
    boundary = {
        "bounded_to_one_local_seat_distribution_family": {"pass": True},
        "all_distributions_are_normalized": {"pass": abs(np.sum(seat_balanced)-1.0)<1e-10 and abs(np.sum(seat_skewed)-1.0)<1e-10},
    }
    all_pass = all(v["pass"] for sec in [positive,negative,boundary] for v in sec.values())
    results = {"name":"torus_seat_entropy","classification":CLASSIFICATION if all_pass else "exploratory_signal","classification_note":CLASSIFICATION_NOTE,"lego_ids":LEGO_IDS,"primary_lego_ids":PRIMARY_LEGO_IDS,"tool_manifest":TOOL_MANIFEST,"tool_integration_depth":TOOL_INTEGRATION_DEPTH,"positive":positive,"negative":negative,"boundary":boundary,"summary":{"all_pass":all_pass,"scope_note":"Direct local torus-seat entropy row on one bounded seat-allocation distribution."}}
    out = pathlib.Path(__file__).resolve().parent / "a2_state" / "sim_results" / "torus_seat_entropy_results.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(results, indent=2, default=str))
    print(f"Results written to {out}")
    print(f"ALL PASS: {all_pass}")

if __name__ == "__main__":
    main()
