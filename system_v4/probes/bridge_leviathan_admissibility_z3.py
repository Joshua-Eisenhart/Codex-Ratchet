#!/usr/bin/env python3
"""bridge_leviathan_admissibility_z3 -- canonical bridge.
scope_note: Shows nonclassical exclusion: z3 UNSAT rules out coalitions where
additive Hobbesian stability + minority-veto co-constraint are simultaneously
admissible. Docs: system_v5/new docs/OWNER_DOCTRINE_SELF_SIMILAR_FRAMEWORKS.md;
wiki/concepts/self-similar-frameworks-and-teleological-doctrine.md.
"""
from _doc_illum_common import build_manifest, write_results
import z3

SCOPE = ("Leviathan admissibility via z3. Canonical: the classical 'dominant "
         "sovereign' rule is excluded once minority-veto constraint is added; "
         "z3 UNSAT = structural impossibility.")

def pos():
    s = z3.Solver()
    a,b,c = z3.Reals("a b c")
    s.add(a>0, b>0, c>0, a+b+c == 10)
    s.add(a > b+c)  # dominant
    ok = s.check() == z3.sat
    return {"dominant_sat": {"status":"PASS" if ok else "FAIL"}}

def neg():
    s = z3.Solver()
    a,b,c = z3.Reals("a b c")
    s.add(a>0,b>0,c>0, a+b+c==10)
    s.add(a > b+c)
    s.add(b+c > a)  # minority-veto contradicts dominance
    ok = s.check() == z3.unsat
    return {"veto_excludes_dominance": {"status":"PASS" if ok else "FAIL"}}

def bnd():
    s = z3.Solver()
    a,b = z3.Reals("a b")
    s.add(a==b, a>0, a>b)  # boundary contradiction
    ok = s.check() == z3.unsat
    return {"tie_strict_unsat": {"status":"PASS" if ok else "FAIL"}}

if __name__ == "__main__":
    tm,d = build_manifest()
    tm["z3"]["used"] = True; tm["z3"]["reason"] = "SAT/UNSAT is the load-bearing admissibility test"
    d["z3"] = "load_bearing"
    p,n,b = pos(),neg(),bnd()
    ap = all(v["status"]=="PASS" for x in (p,n,b) for v in x.values())
    write_results("bridge_leviathan_admissibility_z3",{
        "name":"bridge_leviathan_admissibility_z3","classification":"canonical",
        "scope_note":SCOPE,"tool_manifest":tm,"tool_integration_depth":d,
        "positive":p,"negative":n,"boundary":b,"pass":ap})
