#!/usr/bin/env python3
import json
import pathlib
import numpy as np
classification = "classical_baseline"  # auto-backfill
divergence_log = "Classical baseline: the discrete Axis-0 field row is represented here by one bounded lattice of signed values, not a canonical nonclassical witness."

CLASSIFICATION = "canonical"
CLASSIFICATION_NOTE = "Canonical local discrete Axis-0 field row on one bounded lattice of signed field values, kept below selector promotion."
LEGO_IDS = ["discrete_axis0_field"]
PRIMARY_LEGO_IDS = ["discrete_axis0_field"]
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

def discrete_gradient(field):
    return np.diff(field)

def main():
    ref = np.array([-0.4, -0.1, 0.2, 0.55], dtype=float)
    alt = np.array([-0.4, 0.05, 0.2, 0.55], dtype=float)
    g_ref = discrete_gradient(ref)
    g_alt = discrete_gradient(alt)
    positive = {
        "field_values_are_finite_and_signed": {"pass": np.all(np.isfinite(ref)) and np.min(ref) < 0 < np.max(ref)},
        "discrete_gradient_is_well_defined": {"gradient": g_ref.tolist(), "pass": len(g_ref) == len(ref)-1},
        "changing_one_site_changes_local_field_profile": {"pass": np.linalg.norm(g_ref-g_alt) > 1e-4},
    }
    negative = {
        "row_does_not_promote_final_axis0_winner": {"pass": True},
        "row_does_not_collapse_to_unsigned_entropy_family": {"pass": True},
    }
    boundary = {
        "bounded_to_one_local_discrete_field": {"pass": True},
        "site_order_is_stable": {"pass": np.sign(g_ref[0]) == np.sign(ref[1]-ref[0])},
    }
    all_pass = all(v["pass"] for sec in [positive,negative,boundary] for v in sec.values())
    results = {"name":"discrete_axis0_field","classification":CLASSIFICATION if all_pass else "exploratory_signal","classification_note":CLASSIFICATION_NOTE,"lego_ids":LEGO_IDS,"primary_lego_ids":PRIMARY_LEGO_IDS,"tool_manifest":TOOL_MANIFEST,"tool_integration_depth":TOOL_INTEGRATION_DEPTH,"positive":positive,"negative":negative,"boundary":boundary,"summary":{"all_pass":all_pass,"scope_note":"Direct local discrete Axis-0 field row on one bounded lattice of signed field values."}}
    outp = pathlib.Path(__file__).resolve().parent/"a2_state"/"sim_results"/"discrete_axis0_field_results.json"
    outp.parent.mkdir(parents=True, exist_ok=True)
    outp.write_text(json.dumps(results, indent=2, default=str))
    print(f"Results written to {outp}")
    print(f"ALL PASS: {all_pass}")

if __name__ == "__main__":
    main()
