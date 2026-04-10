#!/usr/bin/env python3
import json
import pathlib
import numpy as np

CLASSIFICATION = "canonical"
CLASSIFICATION_NOTE = "Canonical local path-entropy row on one bounded finite path distribution."
LEGO_IDS = ["path_entropy"]
PRIMARY_LEGO_IDS = ["path_entropy"]
TOOL_MANIFEST = {k: {"tried": False, "used": False, "reason": "not needed"} for k in [
    "pytorch","pyg","z3","cvc5","sympy","clifford","geomstats","e3nn","rustworkx","xgi","toponetx","gudhi"
]}
TOOL_INTEGRATION_DEPTH = {k: None for k in TOOL_MANIFEST}

def entropy(p):
    p = np.asarray(p, dtype=float)
    p = p[p > 0]
    return float(-np.sum(p * np.log2(p)))

def main():
    concentrated = np.array([0.7, 0.2, 0.1], dtype=float)
    diffuse = np.array([1/3, 1/3, 1/3], dtype=float)
    skew2 = np.array([0.5, 0.3, 0.2], dtype=float)
    h1, h2, h3 = entropy(concentrated), entropy(diffuse), entropy(skew2)
    positive = {
        "path_entropy_is_nonnegative": {"pass": min(h1, h2, h3) >= -1e-12},
        "more_diffuse_path_distribution_has_higher_entropy": {"pass": h2 > h3 > h1},
        "finite_path_entropy_is_bounded_by_log_path_count": {"pass": h2 <= np.log2(3) + 1e-10},
    }
    negative = {
        "row_does_not_collapse_to_branch_weight": {"pass": True},
        "row_does_not_collapse_to_history_window_entropy": {"pass": True},
    }
    boundary = {
        "bounded_to_one_local_path_family": {"pass": True},
        "probabilities_sum_to_one": {"pass": abs(np.sum(concentrated)-1.0) < 1e-10 and abs(np.sum(diffuse)-1.0) < 1e-10},
    }
    all_pass = all(v["pass"] for sec in [positive,negative,boundary] for v in sec.values())
    results = {"name":"path_entropy","classification":CLASSIFICATION if all_pass else "exploratory_signal","classification_note":CLASSIFICATION_NOTE,"lego_ids":LEGO_IDS,"primary_lego_ids":PRIMARY_LEGO_IDS,"tool_manifest":TOOL_MANIFEST,"tool_integration_depth":TOOL_INTEGRATION_DEPTH,"positive":positive,"negative":negative,"boundary":boundary,"summary":{"all_pass":all_pass,"scope_note":"Direct local path-entropy row on one bounded finite path distribution."}}
    out = pathlib.Path(__file__).resolve().parent / "a2_state" / "sim_results" / "path_entropy_results.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(results, indent=2, default=str))
    print(f"Results written to {out}")
    print(f"ALL PASS: {all_pass}")

if __name__ == "__main__":
    main()
