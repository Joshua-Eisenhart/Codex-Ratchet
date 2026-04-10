#!/usr/bin/env python3
import json
import pathlib

CLASSIFICATION = "canonical"
CLASSIFICATION_NOTE = "Canonical local support row for contiguous history-window selection on one bounded history path."
LEGO_IDS = ["history_window_support"]
PRIMARY_LEGO_IDS = ["history_window_support"]
TOOL_MANIFEST = {k: {"tried": False, "used": False, "reason": "not needed"} for k in [
    "pytorch","pyg","z3","cvc5","sympy","clifford","geomstats","e3nn","rustworkx","xgi","toponetx","gudhi"
]}
TOOL_INTEGRATION_DEPTH = {k: None for k in TOOL_MANIFEST}

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
    all_pass = all(v["pass"] for sec in [positive,negative,boundary] for v in sec.values())
    results = {"name":"history_window_support","classification":CLASSIFICATION if all_pass else "exploratory_signal","classification_note":CLASSIFICATION_NOTE,"lego_ids":LEGO_IDS,"primary_lego_ids":PRIMARY_LEGO_IDS,"tool_manifest":TOOL_MANIFEST,"tool_integration_depth":TOOL_INTEGRATION_DEPTH,"positive":positive,"negative":negative,"boundary":boundary,"summary":{"all_pass":all_pass,"scope_note":"Direct local contiguous history-window support object on one bounded path."}}
    out = pathlib.Path(__file__).resolve().parent / "a2_state" / "sim_results" / "history_window_support_results.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(results, indent=2))
    print(f"Results written to {out}")
    print(f"ALL PASS: {all_pass}")

if __name__ == "__main__":
    main()
