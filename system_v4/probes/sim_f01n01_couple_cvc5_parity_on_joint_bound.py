#!/usr/bin/env python3
"""F01xN01 coupling 7: cvc5 parity check on the joint cardinality bound.
Exclusion claim: cvc5 independently rules UNSAT on the same joint-bound violation that z3 excluded.
cvc5 load-bearing: cross-solver exclusion witness.
"""
import json, os

TOOL_MANIFEST = {t:{"tried":False,"used":False,"reason":"n/a"} for t in
    ["pytorch","pyg","z3","cvc5","sympy","clifford","geomstats","e3nn","rustworkx","xgi","toponetx","gudhi"]}

try:
    import cvc5
    from cvc5 import Kind
    CVC5_OK = True
    TOOL_MANIFEST["cvc5"] = {"tried":True,"used":True,"reason":"cross-solver UNSAT parity on F01+N01 joint bound; load-bearing"}
except ImportError:
    CVC5_OK = False
    TOOL_MANIFEST["cvc5"] = {"tried":True,"used":False,"reason":"cvc5 not importable"}

TOOL_INTEGRATION_DEPTH = {"cvc5":"load_bearing" if CVC5_OK else None}

def _mk_solver():
    s = cvc5.Solver(); s.setOption("produce-models","true"); s.setLogic("QF_LIA")
    return s

def check_unsat(P_val, C_val_lower):
    s = _mk_solver()
    Int = s.getIntegerSort()
    P = s.mkConst(Int,"P"); C = s.mkConst(Int,"C")
    two_P = s.mkInteger(2**P_val)
    s.assertFormula(s.mkTerm(Kind.EQUAL, P, s.mkInteger(P_val)))
    s.assertFormula(s.mkTerm(Kind.GT, C, s.mkInteger(C_val_lower)))
    s.assertFormula(s.mkTerm(Kind.LEQ, C, two_P))
    r = s.checkSat()
    return r.isUnsat()

def check_sat(P_val, C_val):
    s = _mk_solver()
    Int = s.getIntegerSort()
    P = s.mkConst(Int,"P"); C = s.mkConst(Int,"C")
    two_P = s.mkInteger(2**P_val)
    s.assertFormula(s.mkTerm(Kind.EQUAL, P, s.mkInteger(P_val)))
    s.assertFormula(s.mkTerm(Kind.EQUAL, C, s.mkInteger(C_val)))
    s.assertFormula(s.mkTerm(Kind.LEQ, C, two_P))
    return s.checkSat().isSat()

def run_positive_tests():
    if not CVC5_OK: return {"cvc5_unavailable": False}
    return {"cvc5_unsat_P3_over_8": check_unsat(3, 8)}

def run_negative_tests():
    if not CVC5_OK: return {"cvc5_unavailable": False}
    return {"cvc5_sat_P3_eq_8": check_sat(3, 8)}

def run_boundary_tests():
    if not CVC5_OK: return {"cvc5_unavailable": False}
    # P=1, asserting C>2 is excluded
    return {"cvc5_unsat_P1_over_2": check_unsat(1, 2)}

if __name__ == "__main__":
    pos=run_positive_tests(); neg=run_negative_tests(); bnd=run_boundary_tests()
    all_pass = all(list(pos.values())+list(neg.values())+list(bnd.values()))
    r = {"name":"f01n01_couple_cvc5_parity_on_joint_bound","classification":"canonical",
         "tool_manifest":TOOL_MANIFEST,"tool_integration_depth":TOOL_INTEGRATION_DEPTH,
         "positive":pos,"negative":neg,"boundary":bnd,"overall_pass":bool(all_pass),
         "exclusion_statement":"F01+N01 joint bound C<=2^P excluded by cvc5 (cross-solver parity with z3)."}
    od = os.path.join(os.path.dirname(__file__),"a2_state","sim_results"); os.makedirs(od,exist_ok=True)
    p = os.path.join(od,"f01n01_couple_cvc5_parity_on_joint_bound_results.json")
    with open(p,"w") as f: json.dump(r,f,indent=2,default=str)
    print(p,"overall_pass=",all_pass)
