#!/usr/bin/env python3
"""classical_igt_prisoners_dilemma -- doc illumination (classical).
scope_note: PD has unique Nash (D,D) despite Pareto-dominant (C,C). Docs:
system_v5/new docs/OWNER_DOCTRINE_SELF_SIMILAR_FRAMEWORKS.md;
wiki/concepts/self-similar-frameworks-and-teleological-doctrine.md.
"""
import numpy as np
from _doc_illum_common import build_manifest, write_results
SCOPE = "IGT Prisoner's Dilemma Nash & Pareto (classical baseline)."

# row=player1, col=player2; 0=C,1=D; classic T>R>P>S
A = np.array([[3,0],[5,1]])  # player1 payoff
B = A.T

def nash(A,B):
    out=[]
    for i in range(2):
        for j in range(2):
            if A[i,j]>=A[1-i,j] and B[i,j]>=B[i,1-j]: out.append((i,j))
    return out

def pos():
    eq = nash(A,B); ok = eq == [(1,1)]
    return {"unique_DD_nash":{"eq":eq,"status":"PASS" if ok else "FAIL"}}
def neg():
    # CC is NOT Nash
    eq = nash(A,B); ok = (0,0) not in eq
    return {"CC_not_nash":{"status":"PASS" if ok else "FAIL"}}
def bnd():
    # Pareto: CC dominates DD
    ok = A[0,0] > A[1,1] and B[0,0] > B[1,1]
    return {"CC_pareto_dominates_DD":{"status":"PASS" if ok else "FAIL"}}

if __name__ == "__main__":
    tm,d = build_manifest(); p,n,b = pos(),neg(),bnd()
    ap = all(v["status"]=="PASS" for x in (p,n,b) for v in x.values())
    write_results("classical_igt_prisoners_dilemma",{
        "name":"classical_igt_prisoners_dilemma","classification":"classical_baseline",
        "scope_note":SCOPE,"numpy_load_bearing":True,
        "tool_manifest":tm,"tool_integration_depth":d,
        "positive":p,"negative":n,"boundary":b,"pass":ap})
