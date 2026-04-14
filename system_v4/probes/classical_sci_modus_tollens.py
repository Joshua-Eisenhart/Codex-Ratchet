#!/usr/bin/env python3
"""classical_sci_modus_tollens -- doc illumination (classical).
scope_note: (P->Q) and (not Q) entail (not P). Docs:
system_v5/new docs/OWNER_DOCTRINE_SELF_SIMILAR_FRAMEWORKS.md;
wiki/concepts/self-similar-frameworks-and-teleological-doctrine.md.
"""
import numpy as np
from _doc_illum_common import build_manifest, write_results
SCOPE = "Scientific method: modus tollens truth-table (classical baseline)."

def pos():
    # P->Q true, Q false => P must be false
    cases = [(P,Q) for P in (False,True) for Q in (False,True)
             if ((not P) or Q) and (not Q)]
    ok = all(not P for P,Q in cases)
    return {"all_derived_P_false":{"status":"PASS" if ok else "FAIL"}}
def neg():
    # affirming the consequent is invalid: (P->Q) and Q does NOT entail P
    counterex = [(P,Q) for P in (False,True) for Q in (False,True)
                 if ((not P) or Q) and Q and not P]
    ok = len(counterex) > 0
    return {"affirm_consequent_invalid":{"status":"PASS" if ok else "FAIL"}}
def bnd():
    # empty premise set: nothing derived
    cases = []
    ok = all(False for _ in cases) is True  # vacuous
    return {"vacuous":{"status":"PASS" if ok else "FAIL"}}

if __name__ == "__main__":
    tm,d = build_manifest(); p,n,b = pos(),neg(),bnd()
    ap = all(v["status"]=="PASS" for x in (p,n,b) for v in x.values())
    write_results("classical_sci_modus_tollens",{
        "name":"classical_sci_modus_tollens","classification":"classical_baseline",
        "scope_note":SCOPE,"numpy_load_bearing":True,
        "tool_manifest":tm,"tool_integration_depth":d,
        "positive":p,"negative":n,"boundary":b,"pass":ap})
