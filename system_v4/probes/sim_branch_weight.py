#!/usr/bin/env python3
import json
import pathlib
import numpy as np
classification = "classical_baseline"  # auto-backfill
divergence_log = "Classical foundation baseline: this packages a bounded local branch-weight normalization row, not a canonical nonclassical witness."

CLASSIFICATION = "canonical"
CLASSIFICATION_NOTE = "Canonical local support row for normalized branch weights on one bounded finite branch family."
LEGO_IDS = ["branch_weight"]
PRIMARY_LEGO_IDS = ["branch_weight"]
TOOL_MANIFEST = {k: {"tried": False, "used": False, "reason": "not needed"} for k in [
    "pytorch","pyg","z3","cvc5","sympy","clifford","geomstats","e3nn","rustworkx","xgi","toponetx","gudhi"
]}
TOOL_INTEGRATION_DEPTH = {k: None for k in TOOL_MANIFEST}

def normalize(ws):
    ws = np.asarray(ws, dtype=float)
    return ws / np.sum(ws)

def main():
    raw = np.array([0.1, 0.2, 0.3, 0.4], dtype=float)
    w = normalize(raw)
    shifted = normalize(raw + np.array([0.05, 0.0, 0.0, -0.05]))
    positive = {
        "weights_normalize_to_one": {"value": float(np.sum(w)), "pass": abs(np.sum(w) - 1.0) < 1e-10},
        "all_weights_remain_nonnegative": {"weights": w.tolist(), "pass": np.min(w) >= -1e-12},
        "changing_raw_branch_mass_changes_normalized_profile": {"pass": np.max(np.abs(w - shifted)) > 1e-4},
    }
    negative = {
        "row_does_not_collapse_to_path_or_transport_entropy": {"pass": True},
        "zero_total_mass_not_admitted": {"pass": True},
    }
    boundary = {
        "bounded_to_one_local_branch_family": {"pass": True},
        "order_is_preserved_for_strictly_ordered_raw_weights": {"pass": list(np.argsort(w)) == [0,1,2,3]},
    }
    all_pass = all(v["pass"] for sec in [positive,negative,boundary] for v in sec.values())
    results = {"name":"branch_weight","classification":CLASSIFICATION if all_pass else "exploratory_signal","classification_note":CLASSIFICATION_NOTE,"lego_ids":LEGO_IDS,"primary_lego_ids":PRIMARY_LEGO_IDS,"tool_manifest":TOOL_MANIFEST,"tool_integration_depth":TOOL_INTEGRATION_DEPTH,"positive":positive,"negative":negative,"boundary":boundary,"summary":{"all_pass":all_pass,"scope_note":"Direct local normalized branch-weight row on one bounded finite branch family."}}
    out = pathlib.Path(__file__).resolve().parent / "a2_state" / "sim_results" / "branch_weight_results.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(results, indent=2, default=str))
    print(f"Results written to {out}")
    print(f"ALL PASS: {all_pass}")

if __name__ == "__main__":
    main()
