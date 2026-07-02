#!/usr/bin/env python3
"""Lego 08: restricted Z2 x Z2 computational-basis bit-flip orbit count.

This fixture proves only the finite local bit-flip action on two computational
basis qubits. It does not claim full local-unitary equivalence or a continuous
U(2) x U(2) orbit cardinality.
"""
classification = 'diagnostic_only'

import json, os, sympy as sp
from itertools import product

TOOL_MANIFEST = {t:{"tried":False,"used":False,"reason":"n/a"} for t in
    ["pytorch","pyg","z3","cvc5","sympy","clifford","geomstats","e3nn","rustworkx","xgi","toponetx","gudhi"]}
TOOL_MANIFEST["sympy"] = {"tried":True,"used":True,"reason":"orbit enumeration via symbolic matrices; load-bearing"}
TOOL_INTEGRATION_DEPTH = {"sympy":"load_bearing"}

X = sp.Matrix([[0,1],[1,0]]); I2 = sp.eye(2)

def basis(i,j):
    v = sp.zeros(4,1); v[2*i+j] = 1; return v

def act(op, v): return op*v

def orbit(v, ops):
    seen = [v]
    frontier = [v]
    while frontier:
        nxt = []
        for u in frontier:
            for op in ops:
                w = op*u
                if not any(w == s for s in seen):
                    seen.append(w); nxt.append(w)
        frontier = nxt
    return seen

def run_positive_tests():
    ops = [sp.kronecker_product(X,I2), sp.kronecker_product(I2,X), sp.kronecker_product(X,X)]
    orb00 = orbit(basis(0,0), ops)
    return {"Z2xZ2_orbit_size_4": len(orb00) == 4}

def run_negative_tests():
    # trivial group => orbit size 1
    orb = orbit(basis(0,0), [sp.kronecker_product(I2,I2)])
    return {"trivial_orbit_size_1": len(orb) == 1}

def run_boundary_tests():
    # single generator X on qubit 1 => orbit size 2
    orb = orbit(basis(0,0), [sp.kronecker_product(X,I2)])
    return {"single_gen_orbit_2": len(orb) == 2}

if __name__ == "__main__":
    pos=run_positive_tests(); neg=run_negative_tests(); bnd=run_boundary_tests()
    all_pass = all(list(pos.values())+list(neg.values())+list(bnd.values()))
    r = {"name":"lego_08_equiv_class_cardinality_2q","classification":"canonical",
         "claim_ceiling":"local_lego_only",
         "next_lego_target":"restricted_z2x_z2_basis_bitflip_orbit_count",
         "promotion_condition":"requires controller reconciliation of this exact result path plus sibling F01/N01 lego receipts before any quotient, coupling, bridge, axis, or engine claim",
         "blocked_until":"blocked from downstream promotion until the controller reads this result JSON and records ledger loopback/admission for the exact restricted Z2 x Z2 bit-flip orbit row",
         "demotion_condition":"demote if the Z2 x Z2 orbit of |00> is not size 4, the trivial orbit is not size 1, the single-generator orbit is not size 2, or this fixture is used as a full local-unitary equivalence claim",
         "out_of_scope":[
             "full local-unitary equivalence",
             "continuous U(2) x U(2) orbit cardinality",
             "quotient theorem beyond the finite Z2 x Z2 computational-basis bit-flip fixture",
             "tool-tool coupling",
             "bridge or axis claim",
             "engine placement claim",
             "queue/admission readiness without controller reconciliation"
         ],
         "tool_manifest":TOOL_MANIFEST,"tool_integration_depth":TOOL_INTEGRATION_DEPTH,
         "positive":{k:bool(v) for k,v in pos.items()},
         "negative":{k:bool(v) for k,v in neg.items()},
         "boundary":{k:bool(v) for k,v in bnd.items()},
         "overall_pass":bool(all_pass)}
    od = os.path.join(os.path.dirname(__file__),"a2_state","sim_results"); os.makedirs(od,exist_ok=True)
    p = os.path.join(od,"lego_08_equiv_class_cardinality_2q_results.json")
    with open(p,"w") as f: json.dump(r,f,indent=2,default=str)
    print(p,"overall_pass=",all_pass)
