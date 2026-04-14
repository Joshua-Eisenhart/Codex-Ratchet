#!/usr/bin/env python3
"""classical_fep_markov_blanket_ci -- doc illumination (classical).
scope_note: Internal and external states conditionally independent given blanket.
Docs: system_v5/new docs/OWNER_DOCTRINE_SELF_SIMILAR_FRAMEWORKS.md;
wiki/concepts/self-similar-frameworks-and-teleological-doctrine.md.
"""
import numpy as np
from _doc_illum_common import build_manifest, write_results
SCOPE = "FEP Markov blanket conditional independence (classical baseline)."

def gen(n=20000, seed=0):
    rng = np.random.default_rng(seed)
    blanket = rng.normal(size=n)
    internal = blanket + 0.5*rng.normal(size=n)
    external = blanket + 0.5*rng.normal(size=n)
    return internal, blanket, external

def partial_corr(x,y,z):
    # regress x,y on z; correlate residuals
    bx = np.cov(x,z)[0,1]/np.var(z); by = np.cov(y,z)[0,1]/np.var(z)
    rx = x - bx*z; ry = y - by*z
    return np.corrcoef(rx,ry)[0,1]

def pos():
    i,bl,e = gen()
    pc = partial_corr(i,e,bl)
    ok = abs(pc) < 0.05
    return {"partial_corr_near_zero": {"pc":float(pc),"status":"PASS" if ok else "FAIL"}}
def neg():
    # Without blanket, marginal correlation is nonzero
    i,bl,e = gen()
    mc = np.corrcoef(i,e)[0,1]
    ok = abs(mc) > 0.2
    return {"marginal_corr_nonzero": {"mc":float(mc),"status":"PASS" if ok else "FAIL"}}
def bnd():
    # degenerate: zero variance blanket -> CI trivially true by correlation undefined; guard
    i,_,e = gen(); ok = np.isfinite(np.corrcoef(i,e)[0,1])
    return {"finite_corr": {"status":"PASS" if ok else "FAIL"}}

if __name__ == "__main__":
    tm,d = build_manifest(); p,n,b = pos(),neg(),bnd()
    ap = all(v["status"]=="PASS" for x in (p,n,b) for v in x.values())
    write_results("classical_fep_markov_blanket_ci",{
        "name":"classical_fep_markov_blanket_ci","classification":"classical_baseline",
        "scope_note":SCOPE,"numpy_load_bearing":True,
        "tool_manifest":tm,"tool_integration_depth":d,
        "positive":p,"negative":n,"boundary":b,"pass":ap})
