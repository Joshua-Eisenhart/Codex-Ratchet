#!/usr/bin/env python3
"""Lego 08: Equivalence-class cardinality for 2-qubit computational basis under local-unitary indistinguishability.
Restricted symmetry group: bit-flip on each qubit (Z2 x Z2). Class of |00>: {|00>,|01>,|10>,|11>}? No --
under local Z-basis population permutation only, classes are orbits. We verify orbit sizes via sympy group action.
"""
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
         "tool_manifest":TOOL_MANIFEST,"tool_integration_depth":TOOL_INTEGRATION_DEPTH,
         "positive":pos,"negative":neg,"boundary":bnd,"overall_pass":bool(all_pass)}
    od = os.path.join(os.path.dirname(__file__),"a2_state","sim_results"); os.makedirs(od,exist_ok=True)
    p = os.path.join(od,"lego_08_equiv_class_cardinality_2q_results.json")
    with open(p,"w") as f: json.dump(r,f,indent=2,default=str)
    print(p,"overall_pass=",all_pass)
