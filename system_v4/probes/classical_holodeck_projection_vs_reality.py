#!/usr/bin/env python3
"""classical_holodeck_projection_vs_reality -- doc illumination (classical).
scope_note: Projection P onto observer subspace loses info iff ker(P) nontrivial.
Docs: system_v5/new docs/OWNER_DOCTRINE_SELF_SIMILAR_FRAMEWORKS.md;
wiki/concepts/self-similar-frameworks-and-teleological-doctrine.md.
"""
import numpy as np
from _doc_illum_common import build_manifest, write_results
SCOPE = "Holodeck projection vs reality (classical baseline)."

def pos():
    P = np.diag([1.,1.,0.]); v = np.array([1.,2.,3.]); pv = P@v
    ok = np.allclose(pv, [1.,2.,0.])
    return {"projection_drops_dim": {"status":"PASS" if ok else "FAIL"}}
def neg():
    P = np.eye(3); v = np.array([1.,2.,3.])
    # full-rank projection loses NOTHING; claim "lossy" is false
    lost = not np.allclose(P@v, v)
    ok = not lost
    return {"identity_is_lossless": {"status":"PASS" if ok else "FAIL"}}
def bnd():
    P = np.diag([1.,0.]); v0 = np.zeros(2)
    ok = np.allclose(P@v0, v0)
    return {"zero_vector_fixed": {"status":"PASS" if ok else "FAIL"}}

if __name__ == "__main__":
    tm,d = build_manifest(); p,n,b = pos(),neg(),bnd()
    ap = all(v["status"]=="PASS" for x in (p,n,b) for v in x.values())
    write_results("classical_holodeck_projection_vs_reality",{
        "name":"classical_holodeck_projection_vs_reality","classification":"classical_baseline",
        "scope_note":SCOPE,"numpy_load_bearing":True,
        "tool_manifest":tm,"tool_integration_depth":d,
        "positive":p,"negative":n,"boundary":b,"pass":ap})
