#!/usr/bin/env python3
"""
sim_gerbe_admissibility_dixmier_douady -- Family #3 Gerbes, lego 4/6.

Admissibility test = Dixmier-Douady class [H] in H^3(X, Z) integrality.
On a discrete surrogate we demand the 2-cochain B integrate to an integer
over each 2-cell (quantization). z3 certifies UNSAT when we ask for a
fractional DD class satisfying integrality.
"""
import json, os
import numpy as np

classification = "canonical"

TOOL_MANIFEST = {
    "numpy": {"tried": True, "used": True,  "reason": "integer lattice arithmetic"},
    "z3":    {"tried": False,"used": False, "reason": ""},
}
TOOL_INTEGRATION_DEPTH = {"numpy": "supportive", "z3": "load_bearing"}

try:
    import z3
    TOOL_MANIFEST["z3"].update(tried=True, used=True,
        reason="SAT: integer DD class exists; UNSAT: fractional forbidden")
except Exception as e:
    TOOL_MANIFEST["z3"]["reason"] = f"unavailable: {e}"


def run_positive_tests():
    r = {}
    # integer fluxes on 4 2-cells summing to a total class
    s = z3.Solver()
    f = [z3.Int(f"f{i}") for i in range(4)]
    s.add(z3.Sum(f) == 2)
    s.add(*[f[i] >= -5 for i in range(4)])
    s.add(*[f[i] <= 5 for i in range(4)])
    r["integer_DD_class_SAT"] = (s.check() == z3.sat)
    m = s.model()
    vals = [m[f[i]].as_long() for i in range(4)]
    r["integer_solution"] = vals
    r["integer_sum_matches"] = bool(sum(vals) == 2)
    return r


def run_negative_tests():
    r = {}
    # ask for integer fluxes whose sum is literally 1/2 -> UNSAT
    s = z3.Solver()
    f = [z3.Int(f"f{i}") for i in range(4)]
    s.add(2 * z3.Sum(f) == 1)  # no integer solution
    r["half_integer_DD_UNSAT"] = (s.check() == z3.unsat)

    # incompatibility: integer fluxes with sum in [0.3, 0.7] -> UNSAT (no int)
    s2 = z3.Solver()
    g = [z3.Int(f"g{i}") for i in range(3)]
    total = z3.Real("total"); s2.add(total == z3.Sum(g))
    s2.add(total > 0, total < 1)
    r["non_integer_total_UNSAT"] = (s2.check() == z3.unsat)
    return r


def run_boundary_tests():
    r = {}
    # zero DD class (trivial gerbe) always admissible
    s = z3.Solver()
    f = [z3.Int(f"f{i}") for i in range(4)]
    s.add(*[f[i] == 0 for i in range(4)])
    r["trivial_gerbe_SAT"] = (s.check() == z3.sat)

    # very large integer total remains SAT (no magnitude bound)
    s2 = z3.Solver()
    g = [z3.Int(f"g{i}") for i in range(2)]
    s2.add(z3.Sum(g) == 10 ** 9)
    r["large_DD_class_SAT"] = (s2.check() == z3.sat)
    return r


if __name__ == "__main__":
    results = {
        "name": "gerbe_admissibility_dixmier_douady",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": run_positive_tests(),
        "negative": run_negative_tests(),
        "boundary": run_boundary_tests(),
        "classification": "canonical",
    }
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "gerbe_admissibility_dixmier_douady_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out_path}")
    print(json.dumps({k: results[k] for k in ("positive", "negative", "boundary")},
                     indent=2, default=str))
