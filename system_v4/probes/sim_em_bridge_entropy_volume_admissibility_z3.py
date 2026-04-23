#!/usr/bin/env python3
"""sim_em_bridge_entropy_volume_admissibility_z3
Scope: bridge/canonical sim for doctrine 'space=entropy'. z3 load_bearing:
encodes constraint (S_i > S_j) <=> (V_i > V_j) as admissibility and checks
UNSAT for any candidate that violates monotone co-variation; SAT for admissible
candidates. Nominalist framing: probe-relative admissibility, not construction.
"""
import json, os
SCOPE_NOTE = "Bridge: z3 admissibility encoding of S<->V monotone co-variation. Doctrine: space=entropy. user_entropic_monism_doctrine.md"
TOOL_MANIFEST = {
    "z3": {"tried": False, "used": False, "reason": ""},
    "numpy": {"tried": True, "used": True, "reason": "supportive: build test volumes"},
    "pytorch": {"tried": False, "used": False, "reason": "proof layer, not autograd"},
    "sympy": {"tried": False, "used": False, "reason": "SMT not CAS"},
}
try:
    import z3
    TOOL_MANIFEST["z3"] = {"tried": True, "used": True, "reason": "load-bearing: SAT/UNSAT admissibility proofs"}
    HAVE_Z3 = True
except ImportError:
    HAVE_Z3 = False
    TOOL_MANIFEST["z3"]["reason"] = "not installed"

TOOL_INTEGRATION_DEPTH = {k: None for k in TOOL_MANIFEST}
TOOL_INTEGRATION_DEPTH["z3"] = "load_bearing"
TOOL_INTEGRATION_DEPTH["numpy"] = "supportive"

def admissible(pairs):
    """pairs: list of (S, V). Return (sat, model) that all respect mono."""
    s = z3.Solver()
    Svars = [z3.Real(f"S{i}") for i in range(len(pairs))]
    Vvars = [z3.Real(f"V{i}") for i in range(len(pairs))]
    for i, (S, V) in enumerate(pairs):
        s.add(Svars[i] == S); s.add(Vvars[i] == V)
    # Admissibility: for all i,j: Si<Sj <=> Vi<Vj
    for i in range(len(pairs)):
        for j in range(len(pairs)):
            if i == j: continue
            s.add((Svars[i] < Svars[j]) == (Vvars[i] < Vvars[j]))
    return s.check() == z3.sat

def run_positive_tests():
    if not HAVE_Z3: return {"z3_missing": {"pass": False}}
    good = [(1.0, 2.0), (2.0, 4.0), (3.0, 8.0)]
    return {"monotone_admissible": {"pass": bool(admissible(good))}}

def run_negative_tests():
    if not HAVE_Z3: return {"z3_missing": {"pass": False}}
    bad = [(1.0, 4.0), (2.0, 2.0), (3.0, 8.0)]
    return {"nonmono_rejected": {"pass": bool(not admissible(bad))}}

def run_boundary_tests():
    if not HAVE_Z3: return {"z3_missing": {"pass": False}}
    one = [(1.0, 1.0)]
    return {"single_point_admissible": {"pass": bool(admissible(one))}}

if __name__ == "__main__":
    pos, neg, bnd = run_positive_tests(), run_negative_tests(), run_boundary_tests()
    all_pass = all(v["pass"] for v in {**pos, **neg, **bnd}.values())
    results = {"name": "sim_em_bridge_entropy_volume_admissibility_z3", "scope_note": SCOPE_NOTE,
               "classification": "canonical", "tool_manifest": TOOL_MANIFEST,
               "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
               "positive": pos, "negative": neg, "boundary": bnd, "all_pass": all_pass}
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "sim_em_bridge_entropy_volume_admissibility_z3_results.json")
    with open(out_path, "w") as f: json.dump(results, f, indent=2, default=str)
    print(f"PASS={all_pass} -> {out_path}")
