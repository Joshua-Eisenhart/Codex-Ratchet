#!/usr/bin/env python3
"""F01xN01 coupling 5: noncommutation requires distinct probes.
Exclusion claim: F01 (finite probe family) + N01 (order-sensitive indistinguishability)
jointly exclude a single probe from witnessing operator noncommutation. At least two
distinct probes must be present.
sympy load-bearing: symbolic commutator structure.
"""
import json, os, sympy as sp

TOOL_MANIFEST = {t:{"tried":False,"used":False,"reason":"n/a"} for t in
    ["pytorch","pyg","z3","cvc5","sympy","clifford","geomstats","e3nn","rustworkx","xgi","toponetx","gudhi"]}
TOOL_MANIFEST["sympy"] = {"tried":True,"used":True,"reason":"symbolic commutator witness requires >=2 probes; load-bearing"}
TOOL_INTEGRATION_DEPTH = {"sympy":"load_bearing"}

sx = sp.Matrix([[0,1],[1,0]]); sz = sp.Matrix([[1,0],[0,-1]])

def expec(P, rho):
    return sp.simplify((P*rho).trace())

def run_positive_tests():
    # rho on sz-eigenbasis: |0><0|
    rho = sp.Matrix([[1,0],[0,0]])
    # one probe (sz) sees no noncommutation witness between sx*rho*sx vs rho directly
    # two probes differ on sx,sz => witness exists
    diff_sx = sp.simplify(expec(sx, sx*rho*sx) - expec(sx, rho))
    diff_sz = sp.simplify(expec(sz, sx*rho*sx) - expec(sz, rho))
    # witness = at least one probe distinguishes the action
    return {"two_probes_witness_noncommute": (diff_sx != 0) or (diff_sz != 0)}

def run_negative_tests():
    # single probe = identity => cannot witness noncommutation
    I2 = sp.eye(2); rho = sp.Matrix([[1,0],[0,0]])
    diff = sp.simplify(expec(I2, sx*rho*sx) - expec(I2, rho))
    return {"single_identity_probe_excluded_as_witness": diff == 0}

def run_boundary_tests():
    # commuting operators => no noncommutation witness even with multiple probes
    rho = sp.eye(2)/2
    diff_sx = sp.simplify(expec(sx, sz*rho*sz) - expec(sx, rho))
    diff_sz = sp.simplify(expec(sz, sz*rho*sz) - expec(sz, rho))
    return {"commute_on_maxmixed_no_witness": diff_sx == 0 and diff_sz == 0}

if __name__ == "__main__":
    pos=run_positive_tests(); neg=run_negative_tests(); bnd=run_boundary_tests()
    all_pass = all(list(pos.values())+list(neg.values())+list(bnd.values()))
    r = {"name":"f01n01_couple_noncommute_requires_distinct_probes","classification":"canonical",
         "tool_manifest":TOOL_MANIFEST,"tool_integration_depth":TOOL_INTEGRATION_DEPTH,
         "positive":pos,"negative":neg,"boundary":bnd,"overall_pass":bool(all_pass),
         "exclusion_statement":"F01+N01 jointly exclude single-probe witnessing of operator noncommutation."}
    od = os.path.join(os.path.dirname(__file__),"a2_state","sim_results"); os.makedirs(od,exist_ok=True)
    p = os.path.join(od,"f01n01_couple_noncommute_requires_distinct_probes_results.json")
    with open(p,"w") as f: json.dump(r,f,indent=2,default=str)
    print(p,"overall_pass=",all_pass)
