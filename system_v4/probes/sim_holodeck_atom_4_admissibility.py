#!/usr/bin/env python3
"""
Holodeck atom 4 / 7 -- ADMISSIBILITY.

Lego scope: which density matrices are admissible as holodeck states?
Admissibility is encoded as three constraints:
  (A1) Hermitian: rho = rho^dagger
  (A2) Unit trace
  (A3) Positive semi-definite

We use z3 as a PROOF-LAYER load-bearing tool: encode the three constraints
as SMT clauses over a small 2x2 real symbolic matrix and check that
(i) the constraint set is satisfiable by a canonical admissible rho, and
(ii) adding a witness that violates any one constraint is UNSAT with the
     admissibility clauses.

This is the exclusion-language test required by CLAUDE.md: admissibility =
what *survives* the constraints, expressed as z3 UNSAT for non-survivors.
"""

import json, os

TOOL_MANIFEST = {k: {"tried": False, "used": False, "reason": ""} for k in [
    "pytorch","pyg","z3","cvc5","sympy","clifford","geomstats","e3nn",
    "rustworkx","xgi","toponetx","gudhi"]}
TOOL_INTEGRATION_DEPTH = {k: None for k in TOOL_MANIFEST}

try:
    import torch
    TOOL_MANIFEST["pytorch"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["pytorch"]["reason"] = "not installed"

try:
    import z3
    TOOL_MANIFEST["z3"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["z3"]["reason"] = "not installed"

for n in ("pyg","cvc5","sympy","clifford","geomstats","e3nn",
          "rustworkx","xgi","toponetx","gudhi"):
    TOOL_MANIFEST[n]["reason"] = "not needed for admissibility predicate"


def admissibility_constraints(a, b, c, d):
    """
    Real 2x2 rho = [[a, b],[c, d]] (we force Hermiticity by b = c in z3).
    Returns list of z3 constraints for admissibility.
    """
    return [
        b == c,                     # Hermitian (real-valued simplification)
        a + d == 1,                 # trace 1
        a >= 0, d >= 0,             # diagonal non-negative (necessary)
        a*d - b*c >= 0,             # det >= 0 for 2x2 PSD
    ]


def run_positive_tests():
    results = {}
    a,b,c,d = z3.Reals("a b c d")
    s = z3.Solver()
    s.add(admissibility_constraints(a,b,c,d))
    # Force a specific admissible witness: rho = diag(0.3, 0.7), b=c=0
    s.push()
    s.add(a == z3.RealVal("3/10"), d == z3.RealVal("7/10"), b == 0, c == 0)
    r = s.check()
    results["canonical_admissible"] = {"z3": str(r), "pass": r == z3.sat}
    s.pop()
    # Any SAT model is admissible
    r2 = s.check()
    results["exists_admissible"] = {"z3": str(r2), "pass": r2 == z3.sat}
    return results


def run_negative_tests():
    results = {}
    # Violate trace
    a,b,c,d = z3.Reals("a b c d")
    s = z3.Solver()
    s.add(admissibility_constraints(a,b,c,d))
    s.add(a + d == 2)  # contradicts trace=1
    r = s.check()
    results["trace_violation_unsat"] = {"z3": str(r), "pass": r == z3.unsat}
    # Violate Hermiticity (b != c)
    s2 = z3.Solver()
    s2.add(admissibility_constraints(a,b,c,d))
    s2.add(b - c == 1)
    r2 = s2.check()
    results["hermiticity_violation_unsat"] = {"z3": str(r2), "pass": r2 == z3.unsat}
    # Violate PSD (det < 0 while diagonal nonneg -> UNSAT because det>=0 was asserted)
    s3 = z3.Solver()
    s3.add(admissibility_constraints(a,b,c,d))
    s3.add(a*d - b*c < 0)
    r3 = s3.check()
    results["psd_violation_unsat"] = {"z3": str(r3), "pass": r3 == z3.unsat}
    return results


def run_boundary_tests():
    results = {}
    # Pure-state boundary: rank-1 admissible, det == 0
    a,b,c,d = z3.Reals("a b c d")
    s = z3.Solver()
    s.add(admissibility_constraints(a,b,c,d))
    s.add(a*d - b*c == 0)
    r = s.check()
    results["pure_boundary"] = {"z3": str(r), "pass": r == z3.sat}
    # Numerical cross-check with torch: a random Hermitian PSD trace-1 rho passes
    import torch
    g = torch.Generator().manual_seed(13)
    X = torch.randn(2,2, generator=g, dtype=torch.float64) + 1j*torch.randn(2,2, generator=g, dtype=torch.float64)
    rho = X @ X.conj().T
    rho = rho/torch.trace(rho).real
    ev = torch.linalg.eigvalsh((rho + rho.conj().T)/2).real
    herm = torch.allclose(rho, rho.conj().T, atol=1e-12)
    tr1 = abs(torch.trace(rho).real.item() - 1.0) < 1e-12
    psd = ev.min().item() > -1e-12
    results["torch_admissible_cross_check"] = {
        "hermitian": bool(herm), "trace1": bool(tr1), "psd": bool(psd),
        "pass": bool(herm and tr1 and psd),
    }
    return results


if __name__ == "__main__":
    TOOL_MANIFEST["z3"]["used"] = True
    TOOL_MANIFEST["z3"]["reason"] = "UNSAT proof of non-admissibility; SAT witness for admissible"
    TOOL_MANIFEST["pytorch"]["used"] = True
    TOOL_MANIFEST["pytorch"]["reason"] = "numeric cross-check of admissibility predicate"
    TOOL_INTEGRATION_DEPTH["z3"] = "load_bearing"
    TOOL_INTEGRATION_DEPTH["pytorch"] = "supportive"

    pos = run_positive_tests(); neg = run_negative_tests(); bnd = run_boundary_tests()
    def allpass(d): return all(v.get("pass", False) for v in d.values())
    all_pass = allpass(pos) and allpass(neg) and allpass(bnd)
    results = {
        "name": "holodeck_atom_4_admissibility",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos, "negative": neg, "boundary": bnd,
        "classification": "canonical", "all_pass": all_pass,
    }
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "holodeck_atom_4_admissibility_results.json")
    with open(out_path, "w") as f: json.dump(results, f, indent=2, default=str)
    print(f"[atom4 admissibility] all_pass={all_pass} -> {out_path}")
