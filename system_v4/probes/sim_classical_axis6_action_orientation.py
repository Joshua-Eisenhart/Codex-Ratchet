#!/usr/bin/env python3
"""classical_axis6_action_orientation -- classical baseline: oriented action
surrogate via signed volume / Levi-Civita triple product for a 3-frame.

scope_note: system_v5/new docs/AXIS_AND_ENTROPY_REFERENCE.md, section "Axis 6 /
action-orientation"; LADDERS_FENCES_ADMISSION_REFERENCE.md orientation fences.
Classical surrogate (det), not the nonclassical action form.
"""
import numpy as np
from _doc_illum_common import build_manifest, write_results

TOOL_MANIFEST, TOOL_INTEGRATION_DEPTH = build_manifest()
TOOL_MANIFEST["numpy"] = {"tried": True, "used": True, "reason": "signed volume / det"}
TOOL_INTEGRATION_DEPTH["numpy"] = "load_bearing"


def signed_vol(frame):
    return float(np.linalg.det(frame))


def run_positive_tests():
    r = {}
    F = np.eye(3)
    r["right_handed_positive"] = {"pass": signed_vol(F) > 0, "val": signed_vol(F)}
    F2 = np.array([[1,0,0],[0,0,1],[0,1,0]], float)  # swap -> left-handed
    r["left_handed_negative"] = {"pass": signed_vol(F2) < 0, "val": signed_vol(F2)}
    return r


def run_negative_tests():
    r = {}
    F = np.array([[1,0,0],[1,0,0],[0,0,1]], float)  # degenerate
    r["degenerate_zero"] = {"pass": abs(signed_vol(F)) < 1e-12, "val": signed_vol(F)}
    return r


def run_boundary_tests():
    r = {}
    theta = 1e-8
    R = np.array([[np.cos(theta),-np.sin(theta),0],
                  [np.sin(theta), np.cos(theta),0],
                  [0,0,1]])
    r["small_rotation_preserves_orientation"] = {"pass": signed_vol(R) > 0, "val": signed_vol(R)}
    return r


if __name__ == "__main__":
    pos = run_positive_tests(); neg = run_negative_tests(); bnd = run_boundary_tests()
    allp = all(v["pass"] for v in {**pos, **neg, **bnd}.values())
    results = {
        "name": "classical_axis6_action_orientation",
        "classification": "classical_baseline",
        "scope_note": "AXIS_AND_ENTROPY_REFERENCE.md Axis 6; LADDERS_FENCES_ADMISSION_REFERENCE.md orientation",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos, "negative": neg, "boundary": bnd, "pass": allp,
    }
    write_results("classical_axis6_action_orientation", results)
