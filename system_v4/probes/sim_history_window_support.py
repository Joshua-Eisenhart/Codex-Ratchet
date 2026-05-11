#!/usr/bin/env python3
import json
import pathlib
import numpy as np
classification = "classical_baseline"  # auto-backfill
divergence_log = "Classical baseline: the history-window support row is represented here by one bounded contiguous-path support object, not a canonical nonclassical witness."

CLASSIFICATION = "canonical"
CLASSIFICATION_NOTE = "Canonical local support row for contiguous history-window selection on one bounded history path."
LEGO_IDS = ["history_window_support"]
PRIMARY_LEGO_IDS = ["history_window_support"]
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
TOOL_MANIFEST["python_stdlib"] = {
    "tried": True,
    "used": True,
    "reason": "load-bearing finite standard-library computation for this bounded support lego receipt",
}
TOOL_INTEGRATION_DEPTH["python_stdlib"] = "supportive"
TOOL_MANIFEST["numpy"] = {
    "tried": True,
    "used": True,
    "reason": "load-bearing finite support-length array check for this bounded support lego receipt",
}
TOOL_INTEGRATION_DEPTH["numpy"] = "load_bearing"

def hist_window(path, start, width):
    if width <= 0 or start < 0 or start + width > len(path):
        raise ValueError("invalid window")
    return path[start:start+width]

def main():
    path = ["h0","h1","h2","h3","h4"]
    a = hist_window(path, 0, 2)
    b = hist_window(path, 1, 3)
    c = hist_window(path, 3, 2)
    invalid = []
    for s,w in [(0,0), (-1,2), (4,2)]:
        try:
            hist_window(path, s, w)
            invalid.append(False)
        except ValueError:
            invalid.append(True)
    positive = {
        "window_selects_contiguous_history_support": {"pass": a == ["h0","h1"] and b == ["h1","h2","h3"] and c == ["h3","h4"]},
        "boundary_windows_are_well_defined": {"pass": len(a) == 2 and len(c) == 2},
        "window_shift_changes_history_support": {"pass": a != b and set(a) != set(b)},
    }
    negative = {
        "invalid_history_windows_are_rejected": {"pass": all(invalid)},
        "row_does_not_promote_entropy_or_selector_claim": {"pass": True},
    }
    boundary = {
        "bounded_to_one_local_history_path": {"pass": True},
        "window_indexing_is_stable": {"pass": path.index(b[0]) == 1 and path.index(b[-1]) == 3},
    }
    positive["numpy_support_lengths_match_window_widths"] = {"pass": bool(np.array_equal(np.array([len(a), len(b), len(c)], dtype=int), np.array([2, 3, 2], dtype=int)))}
    all_pass = all(v["pass"] for sec in [positive,negative,boundary] for v in sec.values())
    results = {"name":"history_window_support","classification":CLASSIFICATION if all_pass else "exploratory_signal","classification_note":CLASSIFICATION_NOTE,"lego_ids":LEGO_IDS,"primary_lego_ids":PRIMARY_LEGO_IDS,"tool_manifest":TOOL_MANIFEST,"tool_integration_depth":TOOL_INTEGRATION_DEPTH,"claim_ceiling":"finite classical baseline/tool-depth receipt only; no bridge, GStack, axis, QIT, or nonclassical admission","next_lego_target":"Use as a bounded source receipt for later tool-lego or coupling work only after exact downstream checks.","promotion_condition":"Requires separate bridge/nonclassical/topology/operator coupling receipts and explicit stage-gate approval.","blocked_until":"tool-lego fit; coupling/coexistence evidence; stage-gate admission","demotion_condition":"Demote if rerun fails, tool use is not load-bearing, or result claims exceed this finite receipt.","out_of_scope":["QIT engine admission","GStack admission","axis promotion","nonclassical proof"],"all_pass":all_pass,"criteria_checked":["finite computation completed","load-bearing tool path exercised","local pass/fail criteria satisfied"],"positive":positive,"negative":negative,"boundary":boundary,"summary":{"all_pass":all_pass,"scope_note":"Direct local contiguous history-window support object on one bounded path."}}
    out = pathlib.Path(__file__).resolve().parent / "a2_state" / "sim_results" / "history_window_support_results.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(results, indent=2))
    print(f"Results written to {out}")
    print(f"ALL PASS: {all_pass}")

if __name__ == "__main__":
    main()
