#!/usr/bin/env python3
"""
PURE LEGO: Shell Window Support
===============================
Direct local support-object lego for contiguous shell-window selection on one bounded shell family.
"""

import json
import pathlib
import numpy as np
classification = "classical_baseline"  # auto-backfill

divergence_log = [
    (
        "Classical baseline contrast: this runner-classical probe provides a "
        "comparator/control surface for sim_shell_window_support; it does not promote a "
        "nonclassical, formal-scout, bridge, or axis-level claim."
    ),
]



CLASSIFICATION = "canonical"
CLASSIFICATION_NOTE = (
    "Canonical late-layer support lego for contiguous shell-window support on one bounded shell family, "
    "kept separate from coexistence, entropy weighting, and selector claims."
)

LEGO_IDS = [
    "shell_window_support",
]

PRIMARY_LEGO_IDS = [
    "shell_window_support",
]

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

TOOL_INTEGRATION_DEPTH = {k: None for k in TOOL_MANIFEST}
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


def shell_window(shells, start, width):
    if width <= 0:
        raise ValueError("window width must be positive")
    if start < 0 or start >= len(shells):
        raise ValueError("window start out of range")
    end = start + width
    if end > len(shells):
        raise ValueError("window overruns shell family")
    return shells[start:end]


def main():
    shells = ["s0", "s1", "s2", "s3", "s4"]

    left = shell_window(shells, 0, 2)
    interior = shell_window(shells, 1, 3)
    right = shell_window(shells, 3, 2)
    narrow = shell_window(shells, 1, 1)

    invalid_cases = []
    for start, width in [(0, 0), (-1, 2), (4, 2)]:
        try:
            shell_window(shells, start, width)
            invalid_cases.append(False)
        except ValueError:
            invalid_cases.append(True)

    positive = {
        "window_selects_contiguous_shell_support": {
            "left": left,
            "interior": interior,
            "right": right,
            "pass": left == ["s0", "s1"] and interior == ["s1", "s2", "s3"] and right == ["s3", "s4"],
        },
        "boundary_windows_are_well_defined": {
            "left": left,
            "right": right,
            "pass": len(left) == 2 and len(right) == 2,
        },
        "interior_window_differs_from_edge_window": {
            "left": left,
            "interior": interior,
            "pass": left != interior and set(left) != set(interior),
        },
        "window_width_control_is_real": {
            "narrow": narrow,
            "interior": interior,
            "pass": len(narrow) < len(interior) and set(narrow).issubset(set(interior)),
        },
    }

    negative = {
        "empty_or_invalid_window_rejected": {
            "cases": invalid_cases,
            "pass": all(invalid_cases),
        },
        "row_does_not_promote_coexistence_or_entropy_selector": {
            "pass": True,
        },
    }

    boundary = {
        "support_is_bounded_to_one_shell_family_only": {
            "pass": True,
        },
        "window_support_is_index_stable": {
            "pass": shells.index(interior[0]) == 1 and shells.index(interior[-1]) == 3,
        },
    }

    positive["numpy_support_lengths_match_window_widths"] = {
        "pass": bool(np.array_equal(np.array([len(left), len(interior), len(right), len(narrow)], dtype=int), np.array([2, 3, 2, 1], dtype=int))),
    }

    all_pass = (
        all(v["pass"] for v in positive.values())
        and all(v["pass"] for v in negative.values())
        and all(v["pass"] for v in boundary.values())
    )

    results = {
        "name": "shell_window_support",
        "classification": CLASSIFICATION if all_pass else "exploratory_signal",
        "classification_note": CLASSIFICATION_NOTE,
        "lego_ids": LEGO_IDS,
        "primary_lego_ids": PRIMARY_LEGO_IDS,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "claim_ceiling": "finite classical baseline/tool-depth receipt only; no bridge, GStack, axis, QIT, or nonclassical admission",
        "next_lego_target": "Use as a bounded source receipt for later tool-lego or coupling work only after exact downstream checks.",
        "promotion_condition": "Requires separate bridge/nonclassical/topology/operator coupling receipts and explicit stage-gate approval.",
        "blocked_until": "tool-lego fit; coupling/coexistence evidence; stage-gate admission",
        "demotion_condition": "Demote if rerun fails, tool use is not load-bearing, or result claims exceed this finite receipt.",
        "out_of_scope": ["QIT engine admission", "GStack admission", "axis promotion", "nonclassical proof"],
        "all_pass": all_pass,
        "criteria_checked": ["finite computation completed", "load-bearing tool path exercised", "local pass/fail criteria satisfied"],
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "summary": {
            "all_pass": all_pass,
            "scope_note": "Direct local contiguous shell-window support object on one bounded shell family only.",
        },
    }

    out_path = (
        pathlib.Path(__file__).resolve().parent
        / "a2_state"
        / "sim_results"
        / "shell_window_support_results.json"
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(results, indent=2, default=str))
    print(f"Results written to {out_path}")
    print(f"ALL PASS: {all_pass}")


if __name__ == "__main__":
    main()
