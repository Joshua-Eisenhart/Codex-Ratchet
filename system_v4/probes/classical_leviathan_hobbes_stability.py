#!/usr/bin/env python3
"""classical_leviathan_hobbes_stability -- doc illumination (classical baseline).
scope_note: Hobbesian stability: a single dominant actor's power > sum of rivals =>
covenant stable. Docs: system_v5/new docs/OWNER_DOCTRINE_SELF_SIMILAR_FRAMEWORKS.md;
wiki/concepts/self-similar-frameworks-and-teleological-doctrine.md.
"""
import numpy as np
from _doc_illum_common import build_manifest, write_results
SCOPE = "Leviathan Hobbesian stability test. Classical only."

def pos():
    sovereign = 10.; rivals = np.array([2.,3.,1.]); ok = sovereign > rivals.sum()
    return {"dominant_stable": {"status":"PASS" if ok else "FAIL"}}
def neg():
    sovereign = 2.; rivals = np.array([3.,3.]); ok = not (sovereign > rivals.sum())
    return {"weak_sovereign_unstable": {"status":"PASS" if ok else "FAIL"}}
def bnd():
    sovereign = 5.; rivals = np.array([5.]); ok = not (sovereign > rivals.sum())  # equal => unstable
    return {"tie_not_stable": {"status":"PASS" if ok else "FAIL"}}

if __name__ == "__main__":
    tm,d = build_manifest(); p,n,b = pos(),neg(),bnd()
    ap = all(v["status"]=="PASS" for x in (p,n,b) for v in x.values())
    write_results("classical_leviathan_hobbes_stability",{
        "name":"classical_leviathan_hobbes_stability","classification":"classical_baseline",
        "scope_note":SCOPE,"numpy_load_bearing":True,
        "tool_manifest":tm,"tool_integration_depth":d,
        "positive":p,"negative":n,"boundary":b,"pass":ap})
