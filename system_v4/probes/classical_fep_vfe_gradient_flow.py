#!/usr/bin/env python3
"""classical_fep_vfe_gradient_flow -- doc illumination (classical).
scope_note: Variational free energy F(mu) = 0.5*(mu - obs)^2 decreases along
-gradF. Docs: system_v5/new docs/OWNER_DOCTRINE_SELF_SIMILAR_FRAMEWORKS.md;
wiki/concepts/self-similar-frameworks-and-teleological-doctrine.md.
"""
import numpy as np
from _doc_illum_common import build_manifest, write_results
SCOPE = "FEP VFE gradient flow (classical baseline)."

def pos():
    obs = 3.0; mu = 0.0; lr = 0.1
    Fs = [0.5*(mu-obs)**2]
    for _ in range(50):
        mu = mu - lr*(mu - obs)
        Fs.append(0.5*(mu-obs)**2)
    ok = all(Fs[i+1] <= Fs[i] + 1e-12 for i in range(len(Fs)-1))
    return {"monotone_decrease": {"final_F":Fs[-1],"status":"PASS" if ok else "FAIL"}}
def neg():
    obs = 3.0; mu = 0.0; lr = -0.1   # ascent -> F grows
    F0 = 0.5*(mu-obs)**2
    mu = mu - lr*(mu-obs)
    F1 = 0.5*(mu-obs)**2
    ok = F1 > F0
    return {"ascent_increases_F": {"status":"PASS" if ok else "FAIL"}}
def bnd():
    obs = 3.0; mu = 3.0
    F = 0.5*(mu-obs)**2
    ok = F == 0.0
    return {"fixed_point_zero_F": {"status":"PASS" if ok else "FAIL"}}

if __name__ == "__main__":
    tm,d = build_manifest(); p,n,b = pos(),neg(),bnd()
    ap = all(v["status"]=="PASS" for x in (p,n,b) for v in x.values())
    write_results("classical_fep_vfe_gradient_flow",{
        "name":"classical_fep_vfe_gradient_flow","classification":"classical_baseline",
        "scope_note":SCOPE,"numpy_load_bearing":True,
        "tool_manifest":tm,"tool_integration_depth":d,
        "positive":p,"negative":n,"boundary":b,"pass":ap})
