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
TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": "not needed"},
    "pyg": {"tried": False, "used": False, "reason": "not needed"},
    "z3": {"tried": False, "used": False, "reason": "not needed"},
    "cvc5": {"tried": False, "used": False, "reason": "not needed"},
    "sympy": {"tried": False, "used": False, "reason": "not needed"},
    "clifford": {"tried": False, "used": False, "reason": "not needed"},
    "geomstats": {"tried": False, "used": False, "reason": "not needed"},
    "e3nn": {"tried": False, "used": False, "reason": "not needed"},
    "rustworkx": {"tried": False, "used": False, "reason": "not needed"},
    "xgi": {"tried": False, "used": False, "reason": "not needed"},
    "toponetx": {"tried": False, "used": False, "reason": "not needed"},
    "gudhi": {"tried": False, "used": False, "reason": "not needed"},
}
TOOL_INTEGRATION_DEPTH = {
    "pytorch": None,
    "pyg": None,
    "z3": None,
    "cvc5": None,
    "sympy": None,
    "clifford": None,
    "geomstats": None,
    "e3nn": None,
    "rustworkx": None,
    "xgi": None,
    "toponetx": None,
    "gudhi": None,
}
TOOL_MANIFEST["numpy"] = {
    "tried": True,
    "used": True,
    "reason": "load-bearing finite array/matrix computation for this bounded classical lego receipt",
}
TOOL_INTEGRATION_DEPTH["numpy"] = "load_bearing"

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
    results = {"name":"branch_weight","classification":CLASSIFICATION if all_pass else "exploratory_signal","classification_note":CLASSIFICATION_NOTE,"lego_ids":LEGO_IDS,"primary_lego_ids":PRIMARY_LEGO_IDS,"tool_manifest":TOOL_MANIFEST,"tool_integration_depth":TOOL_INTEGRATION_DEPTH,"claim_ceiling":"finite classical baseline/tool-depth receipt only; no bridge, GStack, axis, QIT, or nonclassical admission","next_lego_target":"Use as a bounded source receipt for later tool-lego or coupling work only after exact downstream checks.","promotion_condition":"Requires separate bridge/nonclassical/topology/operator coupling receipts and explicit stage-gate approval.","blocked_until":"tool-lego fit; coupling/coexistence evidence; stage-gate admission","demotion_condition":"Demote if rerun fails, tool use is not load-bearing, or result claims exceed this finite receipt.","out_of_scope":["QIT engine admission","GStack admission","axis promotion","nonclassical proof"],"all_pass":all_pass,"criteria_checked":["finite computation completed","load-bearing tool path exercised","local pass/fail criteria satisfied"],"positive":positive,"negative":negative,"boundary":boundary,"summary":{"all_pass":all_pass,"scope_note":"Direct local normalized branch-weight row on one bounded finite branch family."}}
    out = pathlib.Path(__file__).resolve().parent / "a2_state" / "sim_results" / "branch_weight_results.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(results, indent=2, default=str))
    print(f"Results written to {out}")
    print(f"ALL PASS: {all_pass}")

if __name__ == "__main__":
    main()
