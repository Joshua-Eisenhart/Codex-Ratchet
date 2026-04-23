#!/usr/bin/env python3
"""F01xN01 coupling 4: indistinguishable pairs saturate probe capacity.
Exclusion claim: once N01 declares two states indistinguishable under F01, no additional
probe drawn from the same F01 family can separate them. Adding such a separator is excluded.
z3 load-bearing: UNSAT on "exists same-family probe that separates an N01-equivalent pair".
"""
import json, os, z3

TOOL_MANIFEST = {t:{"tried":False,"used":False,"reason":"n/a"} for t in
    ["pytorch","pyg","z3","cvc5","sympy","clifford","geomstats","e3nn","rustworkx","xgi","toponetx","gudhi"]}
TOOL_MANIFEST["z3"] = {"tried":True,"used":True,"reason":"UNSAT proof that no F01-family probe separates N01-equivalent pair; load-bearing"}
TOOL_INTEGRATION_DEPTH = {"z3":"load_bearing"}

def run_positive_tests():
    # Model: probe signatures s1,s2 in {0,1}^3 already equal (N01-equivalent under F01 of size 3).
    # Claim no 4th probe in the span of existing 3 separates them.
    s = z3.Solver()
    # represent the "4th probe" as linear combination coeffs a,b,c over the 3 existing probes
    a,b,c = z3.Reals('a b c')
    # outputs on state 1 and state 2 - identical because probe signatures identical
    # coupling-level assertion: signatures equal => any linear combo also equal
    sig1_0, sig1_1, sig1_2 = z3.Reals('p1_0 p1_1 p1_2')
    sig2_0, sig2_1, sig2_2 = z3.Reals('p2_0 p2_1 p2_2')
    s.add(sig1_0 == sig2_0, sig1_1 == sig2_1, sig1_2 == sig2_2)  # N01 equivalence
    out1 = a*sig1_0 + b*sig1_1 + c*sig1_2
    out2 = a*sig2_0 + b*sig2_1 + c*sig2_2
    s.add(out1 != out2)  # ask for separator
    return {"unsat_no_separator_in_family": s.check() == z3.unsat}

def run_negative_tests():
    # If signatures differ on even one probe, a separator exists => SAT
    s = z3.Solver()
    a,b,c = z3.Reals('a b c')
    sig1_0, sig1_1, sig1_2 = z3.Reals('p1_0 p1_1 p1_2')
    sig2_0, sig2_1, sig2_2 = z3.Reals('p2_0 p2_1 p2_2')
    s.add(sig1_0 != sig2_0, sig1_1 == sig2_1, sig1_2 == sig2_2)
    out1 = a*sig1_0 + b*sig1_1 + c*sig1_2
    out2 = a*sig2_0 + b*sig2_1 + c*sig2_2
    s.add(out1 != out2)
    return {"sat_when_signatures_differ": s.check() == z3.sat}

def run_boundary_tests():
    # zero linear combination never separates
    s = z3.Solver()
    a,b,c = z3.Reals('a b c'); s.add(a==0,b==0,c==0)
    sig1_0 = z3.Real('p1_0'); sig2_0 = z3.Real('p2_0')
    s.add(sig1_0 != sig2_0)
    s.add(a*sig1_0 != a*sig2_0)
    return {"zero_combo_unsat": s.check() == z3.unsat}

if __name__ == "__main__":
    pos=run_positive_tests(); neg=run_negative_tests(); bnd=run_boundary_tests()
    all_pass = all(list(pos.values())+list(neg.values())+list(bnd.values()))
    r = {"name":"f01n01_couple_indistinguishable_saturates_probe_capacity","classification":"canonical",
         "tool_manifest":TOOL_MANIFEST,"tool_integration_depth":TOOL_INTEGRATION_DEPTH,
         "positive":pos,"negative":neg,"boundary":bnd,"overall_pass":bool(all_pass),
         "exclusion_statement":"F01+N01 jointly exclude in-family separators between N01-equivalent state pairs."}
    od = os.path.join(os.path.dirname(__file__),"a2_state","sim_results"); os.makedirs(od,exist_ok=True)
    p = os.path.join(od,"f01n01_couple_indistinguishable_saturates_probe_capacity_results.json")
    with open(p,"w") as f: json.dump(r,f,indent=2,default=str)
    print(p,"overall_pass=",all_pass)
