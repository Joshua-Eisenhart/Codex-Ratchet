#!/usr/bin/env python3
"""classical_igt_win_lose_win_lose_ring -- doc illumination (classical).
scope_note: A cyclic dominance ring (rock-paper-scissors-lizard) alternates
win/lose around a directed cycle; sum of payoffs around cycle = 0. Docs:
system_v5/new docs/OWNER_DOCTRINE_SELF_SIMILAR_FRAMEWORKS.md;
wiki/concepts/self-similar-frameworks-and-teleological-doctrine.md.
"""
import numpy as np
from _doc_illum_common import build_manifest, write_results
SCOPE = "IGT cyclic win/lose ring (classical baseline)."

def ring_payoffs(n):
    # directed cycle: i beats i+1 (+1), loses to i-1 (-1)
    M = np.zeros((n,n))
    for i in range(n):
        M[i,(i+1)%n] = 1
        M[i,(i-1)%n] = -1
    return M

def pos():
    M = ring_payoffs(4); ok = np.isclose(M.sum(), 0.0)
    return {"zero_sum_total":{"status":"PASS" if ok else "FAIL"}}
def neg():
    # asymmetric ring (all +1) -> not zero-sum
    n=4; M = np.zeros((n,n))
    for i in range(n): M[i,(i+1)%n]=1
    ok = not np.isclose(M.sum(), 0.0)
    return {"nonalternating_not_zero":{"status":"PASS" if ok else "FAIL"}}
def bnd():
    # n=2 degenerates (successor==predecessor); skip to n=3 as minimal meaningful ring
    M = ring_payoffs(3); ok = np.isclose(M.sum(),0.0)
    return {"n3_minimal_ring_zero":{"status":"PASS" if ok else "FAIL"}}

if __name__ == "__main__":
    tm,d = build_manifest(); p,n,b = pos(),neg(),bnd()
    ap = all(v["status"]=="PASS" for x in (p,n,b) for v in x.values())
    write_results("classical_igt_win_lose_win_lose_ring",{
        "name":"classical_igt_win_lose_win_lose_ring","classification":"classical_baseline",
        "scope_note":SCOPE,"numpy_load_bearing":True,
        "tool_manifest":tm,"tool_integration_depth":d,
        "positive":p,"negative":n,"boundary":b,"pass":ap})
