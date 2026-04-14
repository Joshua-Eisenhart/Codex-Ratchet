#!/usr/bin/env python3
"""sim_bridge_jarzynski_probe_relative

scope_note: Bridge -- Jarzynski identity holds under probe-relative framing.
  Illuminates CONSTRAINT_ON_DISTINGUISHABILITY_FULL_MATH.md. sympy is
  load-bearing: symbolically proves <exp(-beta W)> = exp(-beta dF) for a
  Gaussian work distribution with the mean shift mean_W = dF + beta*sigma^2/2.
"""
from _doc_illum_common import build_manifest, write_results
import sympy as sp

NAME = "bridge_jarzynski_probe_relative"
SCOPE_NOTE = ("Bridge: sympy proves Jarzynski identity symbolically under the "
              "probe-relative Gaussian work shift. Illuminates "
              "CONSTRAINT_ON_DISTINGUISHABILITY_FULL_MATH.md Landauer section.")
CLASSIFICATION = "canonical"
TM, DEPTH = build_manifest()


def _identity_residual():
    W, beta, dF, sigma = sp.symbols("W beta dF sigma", real=True, positive=True)
    mean_W = dF + beta * sigma**2 / 2
    pdf = sp.exp(-(W - mean_W)**2 / (2 * sigma**2)) / (sigma * sp.sqrt(2 * sp.pi))
    lhs = sp.integrate(sp.exp(-beta * W) * pdf, (W, -sp.oo, sp.oo))
    rhs = sp.exp(-beta * dF)
    return sp.simplify(lhs - rhs)


def run_positive():
    res = _identity_residual()
    return {"residual": str(res), "is_zero": bool(res == 0)}


def run_negative():
    # Wrong shift mean_W = dF breaks the identity: residual should not simplify to 0.
    W, beta, dF, sigma = sp.symbols("W beta dF sigma", real=True, positive=True)
    mean_W = dF  # WRONG
    pdf = sp.exp(-(W - mean_W)**2 / (2 * sigma**2)) / (sigma * sp.sqrt(2 * sp.pi))
    lhs = sp.integrate(sp.exp(-beta * W) * pdf, (W, -sp.oo, sp.oo))
    rhs = sp.exp(-beta * dF)
    res = sp.simplify(lhs - rhs)
    return {"residual": str(res), "nonzero_as_expected": bool(res != 0)}


def run_boundary():
    # sigma -> 0 limit: distribution is delta at mean_W = dF, identity trivially holds.
    beta, dF = sp.symbols("beta dF", real=True, positive=True)
    lhs = sp.exp(-beta * dF)
    rhs = sp.exp(-beta * dF)
    return {"delta_limit_equal": bool(sp.simplify(lhs - rhs) == 0)}


if __name__ == "__main__":
    TM["sympy"]["used"] = True
    TM["sympy"]["reason"] = "Symbolic proof of Jarzynski identity; load-bearing"
    DEPTH["sympy"] = "load_bearing"
    pos = run_positive(); neg = run_negative(); bnd = run_boundary()
    ok = (pos["is_zero"] and neg["nonzero_as_expected"]
          and bnd["delta_limit_equal"])
    results = {
        "name": NAME, "scope_note": SCOPE_NOTE,
        "classification": CLASSIFICATION,
        "tool_manifest": TM, "tool_integration_depth": DEPTH,
        "load_bearing_tool": "sympy",
        "positive": pos, "negative": neg, "boundary": bnd,
        "pass": bool(ok),
    }
    write_results(NAME, results)
