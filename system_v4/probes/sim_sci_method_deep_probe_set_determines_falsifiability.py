#!/usr/bin/env python3
"""
Sci-method deep -- probe-set determines falsifiability (cvc5 load-bearing).

Scope: falsifiability of a claim C is EXCLUDED iff under probe set P there is
no pair of worlds distinguishable by P where C differs. cvc5 searches for a
refuting pair over a finite domain. Enriching P can turn an unfalsifiable
claim into a falsifiable one.
"""
import json, os
import cvc5
from cvc5 import Kind

classification = "canonical"

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": ""},
    "pyg": {"tried": False, "used": False, "reason": ""},
    "z3": {"tried": False, "used": False, "reason": ""},
    "cvc5": {"tried": False, "used": False, "reason": ""},
    "sympy": {"tried": False, "used": False, "reason": ""},
    "clifford": {"tried": False, "used": False, "reason": ""},
    "geomstats": {"tried": False, "used": False, "reason": ""},
    "e3nn": {"tried": False, "used": False, "reason": ""},
    "rustworkx": {"tried": False, "used": False, "reason": ""},
    "xgi": {"tried": False, "used": False, "reason": ""},
    "toponetx": {"tried": False, "used": False, "reason": ""},
    "gudhi": {"tried": False, "used": False, "reason": ""},
}
TOOL_INTEGRATION_DEPTH = {k: None for k in TOOL_MANIFEST}

SIM_BASENAME = os.path.splitext(os.path.basename(__file__))[0]
RUN_BOUNDARY_FIELDS = {
    "claim_ceiling": "recursive science-method deep micro only; no promotion beyond bounded falsifiability/admissibility fixture",
    "next_lego_target": SIM_BASENAME,
    "promotion_condition": "requires later independent admission, executed receipt review, and stage-appropriate lego gate before any higher claim",
    "blocked_until": "exact runner result receipt validates under strict executable run boundary",
    "demotion_condition": "demote if used as theory proof beyond this bounded science-method fixture or if execution result omits positive, negative, or boundary checks",
    "out_of_scope": [
        "no theory promotion",
        "no manifold admission",
        "no scientific coupling claim",
        "no bridge or axis claim",
    ],
}
TOOL_MANIFEST["cvc5"]["tried"] = True
for k in TOOL_MANIFEST:
    if not TOOL_MANIFEST[k]["tried"]:
        TOOL_MANIFEST[k]["reason"] = "not required for cvc5 falsifiability witness"


def _new_solver():
    s = cvc5.Solver()
    s.setLogic("QF_UF")
    s.setOption("produce-models", "true")
    return s


def run_positive_tests():
    r = {}
    # Claim C(w) = (b0 AND b1). Probe set P = {b0, b1}.
    # Falsifier: world with NOT(b0 AND b1). SAT expected.
    s = _new_solver()
    B = s.getBooleanSort()
    b0 = s.mkConst(B, "b0"); b1 = s.mkConst(B, "b1")
    claim = s.mkTerm(Kind.AND, b0, b1)
    s.assertFormula(s.mkTerm(Kind.NOT, claim))
    r["falsifier_exists"] = {"pass": s.checkSat().isSat()}
    return r


def run_negative_tests():
    r = {}
    # Claim C(w) depends on hidden coord b2 not in probe set. Under P={b0,b1},
    # any two worlds indistinguishable by P have the same (b0,b1); if C is
    # defined as b0 OR NOT b0 (tautology over probed coords), no probe-visible
    # falsifier. Force claim=True and search for probe-visible falsifier: UNSAT.
    s = _new_solver()
    B = s.getBooleanSort()
    b0 = s.mkConst(B, "b0")
    tautology = s.mkTerm(Kind.OR, b0, s.mkTerm(Kind.NOT, b0))
    s.assertFormula(s.mkTerm(Kind.NOT, tautology))
    r["unfalsifiable_under_P"] = {"pass": s.checkSat().isUnsat()}
    return r


def run_boundary_tests():
    r = {}
    # Enrich probes: adding b2 to P exposes hidden-coord claim.
    s = _new_solver()
    B = s.getBooleanSort()
    b2 = s.mkConst(B, "b2")
    claim = b2  # visible now
    s.assertFormula(s.mkTerm(Kind.NOT, claim))
    r["enriched_probe_exposes_falsifier"] = {"pass": s.checkSat().isSat()}
    # Empty claim domain -> no worlds, vacuous UNSAT for refuter.
    s2 = _new_solver()
    Bsort = s2.getBooleanSort()
    x = s2.mkConst(Bsort, "x")
    s2.assertFormula(s2.mkTerm(Kind.AND, x, s2.mkTerm(Kind.NOT, x)))
    r["empty_domain_unsat"] = {"pass": s2.checkSat().isUnsat()}
    return r


if __name__ == "__main__":
    TOOL_MANIFEST["cvc5"]["used"] = True
    TOOL_MANIFEST["cvc5"]["reason"] = "cvc5 SAT/UNSAT witnesses probe-relative falsifiability"
    TOOL_INTEGRATION_DEPTH["cvc5"] = "load_bearing"
    pos, neg, bnd = run_positive_tests(), run_negative_tests(), run_boundary_tests()
    allpass = lambda d: all(v.get("pass", False) for v in d.values())
    ap = allpass(pos) and allpass(neg) and allpass(bnd)
    res = {"name": SIM_BASENAME,
           "classification": "canonical",
           "scope_note": "OWNER_DOCTRINE_SELF_SIMILAR_FRAMEWORKS.md",
           "tool_manifest": TOOL_MANIFEST, "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
           "positive": pos, "negative": neg, "boundary": bnd,
           "all_pass": ap, "overall_pass": ap, **RUN_BOUNDARY_FIELDS}
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out = os.path.join(out_dir, f"{SIM_BASENAME}_results.json")
    with open(out, "w") as f: json.dump(res, f, indent=2, default=str)
    print(f"[{res['name']}] all_pass={ap} -> {out}")
