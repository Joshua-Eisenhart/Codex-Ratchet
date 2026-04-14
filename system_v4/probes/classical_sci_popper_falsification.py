#!/usr/bin/env python3
"""classical_sci_popper_falsification -- doc illumination (classical).
scope_note: A universal claim "all x P(x)" is falsified by one counterexample.
Docs: system_v5/new docs/OWNER_DOCTRINE_SELF_SIMILAR_FRAMEWORKS.md;
wiki/concepts/self-similar-frameworks-and-teleological-doctrine.md.
"""
import numpy as np
from _doc_illum_common import build_manifest, write_results
SCOPE = "Scientific method: Popper falsification (classical baseline)."

def claim_all_positive(xs): return all(x > 0 for x in xs)

def pos():
    xs = np.array([1,2,3,-1,5])
    ok = not claim_all_positive(xs)  # falsified
    return {"counterexample_falsifies": {"status":"PASS" if ok else "FAIL"}}
def neg():
    xs = np.array([1,2,3,4])
    ok = claim_all_positive(xs)  # not falsified
    return {"no_counterexample_not_falsified": {"status":"PASS" if ok else "FAIL"}}
def bnd():
    xs = np.array([])
    ok = claim_all_positive(xs)  # vacuous truth
    return {"empty_vacuous_true": {"status":"PASS" if ok else "FAIL"}}

if __name__ == "__main__":
    tm,d = build_manifest(); p,n,b = pos(),neg(),bnd()
    ap = all(v["status"]=="PASS" for x in (p,n,b) for v in x.values())
    write_results("classical_sci_popper_falsification",{
        "name":"classical_sci_popper_falsification","classification":"classical_baseline",
        "scope_note":SCOPE,"numpy_load_bearing":True,
        "tool_manifest":tm,"tool_integration_depth":d,
        "positive":p,"negative":n,"boundary":b,"pass":ap})
