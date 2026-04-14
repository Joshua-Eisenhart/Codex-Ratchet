#!/usr/bin/env python3
"""classical_igt_nash_2x2 -- doc illumination (classical).
scope_note: Pure-strategy Nash equilibrium in 2x2 coordination game. Docs:
system_v5/new docs/OWNER_DOCTRINE_SELF_SIMILAR_FRAMEWORKS.md;
wiki/concepts/self-similar-frameworks-and-teleological-doctrine.md.
"""
import numpy as np
from _doc_illum_common import build_manifest, write_results
SCOPE = "IGT 2x2 Nash equilibrium enumeration (classical baseline)."

def nash(A, B):
    eq = []
    for i in range(2):
        for j in range(2):
            if A[i,j] >= A[1-i,j] and B[i,j] >= B[i,1-j]:
                eq.append((i,j))
    return eq

def pos():
    # Coordination: (0,0) and (1,1) both Nash
    A = np.array([[2,0],[0,1]]); B = A
    eq = nash(A,B)
    ok = (0,0) in eq and (1,1) in eq
    return {"two_pure_nash":{"eq":eq,"status":"PASS" if ok else "FAIL"}}
def neg():
    # Matching pennies: no pure Nash
    A = np.array([[1,-1],[-1,1]]); B = -A
    eq = nash(A,B)
    ok = len(eq) == 0
    return {"no_pure_nash":{"status":"PASS" if ok else "FAIL"}}
def bnd():
    # All equal -> every cell is Nash
    A = np.zeros((2,2)); B = np.zeros((2,2))
    eq = nash(A,B); ok = len(eq) == 4
    return {"degenerate_all_nash":{"status":"PASS" if ok else "FAIL"}}

if __name__ == "__main__":
    tm,d = build_manifest(); p,n,b = pos(),neg(),bnd()
    ap = all(v["status"]=="PASS" for x in (p,n,b) for v in x.values())
    write_results("classical_igt_nash_2x2",{
        "name":"classical_igt_nash_2x2","classification":"classical_baseline",
        "scope_note":SCOPE,"numpy_load_bearing":True,
        "tool_manifest":tm,"tool_integration_depth":d,
        "positive":p,"negative":n,"boundary":b,"pass":ap})
