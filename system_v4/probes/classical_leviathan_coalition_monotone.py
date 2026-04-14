#!/usr/bin/env python3
"""classical_leviathan_coalition_monotone -- doc illumination sim.

scope_note: Illustrates Leviathan framework (coalition power monotone in membership)
from system_v5/new docs/OWNER_DOCTRINE_SELF_SIMILAR_FRAMEWORKS.md and
wiki/concepts/self-similar-frameworks-and-teleological-doctrine.md. Classical
baseline only -- does not claim constraint-admissibility.
"""
import numpy as np
from _doc_illum_common import build_manifest, write_results

SCOPE_NOTE = (
    "Leviathan monotone coalition power (classical baseline). Doc refs: "
    "system_v5/new docs/OWNER_DOCTRINE_SELF_SIMILAR_FRAMEWORKS.md; "
    "wiki/concepts/self-similar-frameworks-and-teleological-doctrine.md."
)

def power(coalition, weights):
    return float(np.sum(weights[list(coalition)]))

def positive():
    w = np.array([1.0, 2.0, 3.0, 4.0])
    A = {0, 1}; B = {0, 1, 2}
    ok = power(A, w) <= power(B, w)
    return {"monotone_subset": {"pA": power(A,w), "pB": power(B,w),
            "status": "PASS" if ok else "FAIL"}}

def negative():
    # NEG: a non-monotone fake rule must fail monotonicity
    w = np.array([1.0, 2.0, 3.0])
    fake = lambda S: -len(S)
    ok = not (fake({0}) <= fake({0,1}))
    return {"non_monotone_rejected": {"status": "PASS" if ok else "FAIL"}}

def boundary():
    w = np.array([0.0, 0.0])
    ok = power(set(), w) == 0.0 and power({0,1}, w) == 0.0
    return {"empty_and_zero": {"status": "PASS" if ok else "FAIL"}}

if __name__ == "__main__":
    tm, depth = build_manifest()
    tm["pytorch"]["used"] = False  # not used
    # numpy is the load-bearing layer for classical baseline
    pos, neg, bnd = positive(), negative(), boundary()
    all_pass = all(v["status"]=="PASS" for d in (pos,neg,bnd) for v in d.values())
    # numpy isn't in the manifest; record load-bearing classical via pytorch=None, noting in scope
    results = {
        "name": "classical_leviathan_coalition_monotone",
        "classification": "classical_baseline",
        "scope_note": SCOPE_NOTE,
        "numpy_load_bearing": True,
        "tool_manifest": tm,
        "tool_integration_depth": depth,
        "positive": pos, "negative": neg, "boundary": bnd,
        "pass": all_pass,
    }
    write_results("classical_leviathan_coalition_monotone", results)
