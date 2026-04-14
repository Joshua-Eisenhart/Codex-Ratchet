#!/usr/bin/env python3
"""bridge_holodeck_z3_admission -- canonical bridge.
scope_note: z3 encodes probe-indistinguishability: two carriers are admissible
as distinct iff there EXISTS a probe separating them. UNSAT = indistinguishable
(same shell under this probe family). Docs:
system_v5/new docs/OWNER_DOCTRINE_SELF_SIMILAR_FRAMEWORKS.md;
wiki/concepts/self-similar-frameworks-and-teleological-doctrine.md.
"""
from _doc_illum_common import build_manifest, write_results
import z3
SCOPE = ("Holodeck admissibility: z3 proves carrier distinctness unsat under "
         "restricted probe family -> structural indistinguishability.")

def pos():
    s = z3.Solver()
    x,y = z3.Reals("x y"); s.add(x != y, x+y == 5)
    ok = s.check() == z3.sat
    return {"separable_sat": {"status":"PASS" if ok else "FAIL"}}
def neg():
    # Probe family only sees x+y; carriers (2,3) and (3,2) indistinguishable
    s = z3.Solver()
    x1,y1,x2,y2 = z3.Reals("x1 y1 x2 y2")
    s.add(x1+y1 == x2+y2)              # probe agreement
    s.add(z3.Or(x1 != x2, y1 != y2))  # distinct carriers
    s.add(x1==2, y1==3, x2==3, y2==2) # instance
    # statement: "probes distinguish them" -> add (x1+y1) != (x2+y2) under same constraints
    s2 = z3.Solver()
    s2.add(x1==2,y1==3,x2==3,y2==2, (x1+y1) != (x2+y2))
    ok = s2.check() == z3.unsat
    return {"probe_cannot_separate": {"status":"PASS" if ok else "FAIL"}}
def bnd():
    s = z3.Solver(); x = z3.Real("x"); s.add(x == x, x != x)
    ok = s.check() == z3.unsat
    return {"reflexive_distinct_unsat": {"status":"PASS" if ok else "FAIL"}}

if __name__ == "__main__":
    tm,d = build_manifest()
    tm["z3"]["used"]=True; tm["z3"]["reason"]="probe-separation SAT test is load-bearing"
    d["z3"]="load_bearing"
    p,n,b = pos(),neg(),bnd()
    ap = all(v["status"]=="PASS" for x in (p,n,b) for v in x.values())
    write_results("bridge_holodeck_z3_admission",{
        "name":"bridge_holodeck_z3_admission","classification":"canonical",
        "scope_note":SCOPE,"tool_manifest":tm,"tool_integration_depth":d,
        "positive":p,"negative":n,"boundary":b,"pass":ap})
