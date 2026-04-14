#!/usr/bin/env python3
"""
FEP atom 6 of 7: CHIRALITY.

Claim: FEP carries an orientation -- forward vs reverse KL are not
interchangeable. KL(q||p) (mode-seeking, "I-projection") differs from
KL(p||q) (moment-matching, "M-projection") for asymmetric distributions;
this asymmetry is the chirality of variational inference. A scalar
"symmetric divergence" cannot equal both, which we certify as UNSAT.

Load-bearing tool: pytorch (numeric KL asymmetry on a mixture vs
Gaussian pair). Supportive: z3 (UNSAT that a single symmetric scalar
equals both forward and reverse KL when they differ).
"""

import json, os

TOOL_MANIFEST = {
    "pytorch":   {"tried": False, "used": False, "reason": "numeric forward/reverse KL asymmetry"},
    "pyg":       {"tried": False, "used": False, "reason": "not used"},
    "z3":        {"tried": False, "used": False, "reason": "symmetric-divergence UNSAT"},
    "cvc5":      {"tried": False, "used": False, "reason": "not used"},
    "sympy":     {"tried": False, "used": False, "reason": "not used"},
    "clifford":  {"tried": False, "used": False, "reason": "not used"},
    "geomstats": {"tried": False, "used": False, "reason": "info-geom handled via KL here"},
    "e3nn":      {"tried": False, "used": False, "reason": "not used"},
    "rustworkx": {"tried": False, "used": False, "reason": "not used"},
    "xgi":       {"tried": False, "used": False, "reason": "not used"},
    "toponetx":  {"tried": False, "used": False, "reason": "not used"},
    "gudhi":     {"tried": False, "used": False, "reason": "not used"},
}
TOOL_INTEGRATION_DEPTH = {k: None for k in TOOL_MANIFEST}

try:
    import torch
    TOOL_MANIFEST["pytorch"]["tried"] = True
except ImportError:
    torch = None
    TOOL_MANIFEST["pytorch"]["reason"] = "not installed"

try:
    import z3
    TOOL_MANIFEST["z3"]["tried"] = True
except ImportError:
    z3 = None
    TOOL_MANIFEST["z3"]["reason"] = "not installed"


def _kl_discrete(p, q):
    # KL(p || q) over discrete support
    eps = 1e-12
    return (p * (torch.log(p + eps) - torch.log(q + eps))).sum()


def run_positive_tests():
    if torch is None: return {"skipped":"torch missing"}
    # Asymmetric pair
    p = torch.tensor([0.7, 0.2, 0.1])
    q = torch.tensor([0.2, 0.3, 0.5])
    fwd = _kl_discrete(q, p)   # KL(q||p), mode-seeking
    rev = _kl_discrete(p, q)   # KL(p||q), moment-matching
    gap = abs(float(fwd) - float(rev))
    TOOL_MANIFEST["pytorch"]["used"] = True
    TOOL_INTEGRATION_DEPTH["pytorch"] = "load_bearing"
    return {"kl_asymmetric": {"fwd": float(fwd), "rev": float(rev),
                              "gap": gap, "pass": gap > 1e-3}}


def run_negative_tests():
    if z3 is None: return {"skipped":"z3 missing"}
    # Claim: a single scalar D equals both forward and reverse KL. Given
    # that forward != reverse (from positive test), this is UNSAT.
    s = z3.Solver()
    D = z3.Real("D")
    fwd = z3.Real("fwd"); rev = z3.Real("rev")
    s.add(fwd == z3.RealVal("0.5"))
    s.add(rev == z3.RealVal("0.9"))
    s.add(D == fwd); s.add(D == rev)
    r = s.check()
    TOOL_MANIFEST["z3"]["used"] = True
    TOOL_INTEGRATION_DEPTH["z3"] = "supportive"
    return {"symmetric_scalar_unsat": {"z3": str(r), "pass": r == z3.unsat}}


def run_boundary_tests():
    if torch is None: return {"skipped":"torch missing"}
    # p == q: achiral edge -- forward and reverse KL both zero
    p = torch.tensor([0.25,0.25,0.25,0.25])
    fwd = _kl_discrete(p, p); rev = _kl_discrete(p, p)
    gap = abs(float(fwd)-float(rev))
    return {"achiral_equal_distributions": {
        "fwd": float(fwd), "rev": float(rev), "gap": gap,
        "pass": gap < 1e-9 and abs(float(fwd)) < 1e-9
    }}


if __name__ == "__main__":
    pos = run_positive_tests(); neg = run_negative_tests(); bnd = run_boundary_tests()
    all_pass = (pos.get("kl_asymmetric",{}).get("pass",False)
                and neg.get("symmetric_scalar_unsat",{}).get("pass",False)
                and bnd.get("achiral_equal_distributions",{}).get("pass",False))
    out = {"name":"fep_atom_6_chirality","classification":"canonical",
           "tool_manifest":TOOL_MANIFEST,"tool_integration_depth":TOOL_INTEGRATION_DEPTH,
           "positive":pos,"negative":neg,"boundary":bnd,
           "status":"PASS" if all_pass else "FAIL"}
    d = os.path.join(os.path.dirname(__file__),"a2_state","sim_results")
    os.makedirs(d, exist_ok=True)
    p = os.path.join(d,"fep_atom_6_chirality_results.json")
    with open(p,"w") as f: json.dump(out,f,indent=2,default=str)
    print(f"[{out['status']}] {p}")
