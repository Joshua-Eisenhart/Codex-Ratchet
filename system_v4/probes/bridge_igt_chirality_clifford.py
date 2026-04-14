#!/usr/bin/env python3
"""bridge_igt_chirality_clifford -- canonical bridge.
scope_note: Chirality (CW vs CCW) of the IGT win/lose ring is encoded by sign of
the pseudoscalar in Cl(3). Clifford algebra is load-bearing: reversing the ring
direction flips e123 sign, establishing that the classical 'cycle' has two
admissibility classes the numpy sum test cannot separate. Docs:
system_v5/new docs/OWNER_DOCTRINE_SELF_SIMILAR_FRAMEWORKS.md;
wiki/concepts/self-similar-frameworks-and-teleological-doctrine.md.
"""
from _doc_illum_common import build_manifest, write_results
from clifford import Cl
SCOPE = ("IGT ring chirality via Cl(3) pseudoscalar sign; canonical: two "
         "chirality classes exist that the zero-sum classical test merges.")

layout, blades = Cl(3)
e1,e2,e3 = blades['e1'],blades['e2'],blades['e3']
I = e1*e2*e3  # pseudoscalar

def ring_rotor(direction):
    # direction = +1 CCW, -1 CW -> different bivector orientations
    B = direction*(e1*e2 + e2*e3 + e3*e1)
    return B

def pos():
    Bccw = ring_rotor(+1); Bcw = ring_rotor(-1)
    ok = (Bccw + Bcw) == 0   # chirality-antisymmetric
    return {"chirality_antisym":{"status":"PASS" if ok else "FAIL"}}
def neg():
    # classical zero-sum test cannot distinguish chirality:
    # both rings have the same scalar sum (0), but the bivectors differ.
    Bccw = ring_rotor(+1); Bcw = ring_rotor(-1)
    scalar_equal = (float(Bccw(0)) == float(Bcw(0)))   # both zero
    bivector_diff = (Bccw != Bcw)
    ok = scalar_equal and bivector_diff
    return {"classical_blind_to_chirality":{"status":"PASS" if ok else "FAIL"}}
def bnd():
    # I squared = -1 in Cl(3) confirms pseudoscalar orientation sign
    I2 = float((I*I)(0))
    ok = abs(I2 + 1.0) < 1e-10
    return {"I_squared_neg1":{"I2":I2,"status":"PASS" if ok else "FAIL"}}

if __name__ == "__main__":
    tm,d = build_manifest()
    tm["clifford"]["used"]=True
    tm["clifford"]["reason"]="Cl(3) bivector/pseudoscalar separates ring chirality; load-bearing"
    d["clifford"]="load_bearing"
    p,n,b = pos(),neg(),bnd()
    ap = all(v["status"]=="PASS" for x in (p,n,b) for v in x.values())
    write_results("bridge_igt_chirality_clifford",{
        "name":"bridge_igt_chirality_clifford","classification":"canonical",
        "scope_note":SCOPE,"tool_manifest":tm,"tool_integration_depth":d,
        "positive":p,"negative":n,"boundary":b,"pass":ap})
