#!/usr/bin/env python3
"""sim_classical_jarzynski_equality_small_system

scope_note: Illuminates Landauer section of
  system_v5/docs/CONSTRAINT_ON_DISTINGUISHABILITY_FULL_MATH.md
  via <exp(-beta W)> = exp(-beta Delta F) for a two-level system driven
  by a stochastic work protocol.
"""
import numpy as np
from _doc_illum_common import write_results

NAME = "classical_jarzynski_equality_small_system"
SCOPE_NOTE = ("Illuminates CONSTRAINT_ON_DISTINGUISHABILITY_FULL_MATH.md "
              "(Landauer section): Jarzynski equality as identity linking "
              "fluctuating work to free-energy difference.")
CLASSIFICATION = "classical_baseline"
divergence_log = (
    "Classical stochastic-work baseline for the Jarzynski equality; contrasts "
    "exponential work averaging against naive mean-work estimates without "
    "promoting a nonclassical thermodynamic witness."
)
TOOL_MANIFEST = {
    "numpy": {"tried": True, "used": True, "reason": "load-bearing stochastic work sampling and exponential averaging"},
    "pytorch": {"tried": False, "used": False, "reason": "not needed for this classical stochastic-work baseline"},
    "pyg": {"tried": False, "used": False, "reason": "not needed: no graph layer"},
    "z3": {"tried": False, "used": False, "reason": "not needed: no SMT claim"},
    "cvc5": {"tried": False, "used": False, "reason": "not needed: no SMT claim"},
    "sympy": {"tried": False, "used": False, "reason": "not needed: no symbolic manipulation"},
    "clifford": {"tried": False, "used": False, "reason": "not needed: no geometric algebra"},
    "geomstats": {"tried": False, "used": False, "reason": "not needed: no manifold-distance computation"},
    "e3nn": {"tried": False, "used": False, "reason": "not needed: no equivariant neural layer"},
    "rustworkx": {"tried": False, "used": False, "reason": "not needed: no graph algorithm"},
    "xgi": {"tried": False, "used": False, "reason": "not needed: no hypergraph"},
    "toponetx": {"tried": False, "used": False, "reason": "not needed: no cell-complex computation"},
    "gudhi": {"tried": False, "used": False, "reason": "not needed: no persistence computation"},
}
TOOL_INTEGRATION_DEPTH = {
    "numpy": "load_bearing",
    "pytorch": None,
    "pyg": None,
    "z3": None,
    "cvc5": None,
    "sympy": None,
    "clifford": None,
    "geomstats": None,
    "e3nn": None,
    "rustworkx": None,
    "xgi": None,
    "toponetx": None,
    "gudhi": None,
}
TM = TOOL_MANIFEST
DEPTH = TOOL_INTEGRATION_DEPTH


def jarzynski_estimate(work_samples, beta=1.0):
    return -np.log(np.mean(np.exp(-beta * work_samples))) / beta


def run_positive():
    rng = np.random.default_rng(7)
    out = {}
    # Construct W ~ Gaussian with mean=dF + sigma^2/2 so that
    # <exp(-beta W)> = exp(-beta dF) exactly in expectation.
    for dF in [0.0, 0.5, 1.2]:
        sigma = 0.3
        beta = 1.0
        mean_W = dF + beta * sigma**2 / 2.0
        W = rng.normal(mean_W, sigma, size=200000)
        est = jarzynski_estimate(W, beta)
        out[f"dF_{dF}"] = {"dF_est": float(est), "dF_true": float(dF),
                          "abs_err": float(abs(est - dF)),
                          "ok": bool(abs(est - dF) < 0.02)}
    return out


def run_negative():
    rng = np.random.default_rng(3)
    # If we ignore exponential average and use mean(W), <W> != dF
    # for irreversible drives; record that the naive estimate violates.
    dF = 0.5; sigma = 0.8
    mean_W = dF + sigma**2 / 2.0
    W = rng.normal(mean_W, sigma, size=200000)
    naive = float(np.mean(W))
    return {"naive_biased_above_dF": bool(naive > dF + 0.1),
            "naive": naive, "dF_true": dF}


def run_boundary():
    # Zero-work protocol: every sample 0 => estimator returns 0
    W = np.zeros(1000)
    return {"zero_work": {"dF_est": float(jarzynski_estimate(W))}}


if __name__ == "__main__":
    pos = run_positive(); neg = run_negative(); bnd = run_boundary()
    ok = (all(v["ok"] for v in pos.values())
          and neg["naive_biased_above_dF"]
          and bnd["zero_work"]["dF_est"] == 0.0)
    results = {
        "name": NAME, "scope_note": SCOPE_NOTE,
        "classification": CLASSIFICATION,
        "divergence_log": divergence_log,
        "tool_manifest": TM, "tool_integration_depth": DEPTH,
        "load_bearing_tool": "numpy",
        "positive": pos, "negative": neg, "boundary": bnd,
        "pass": bool(ok),
    }
    write_results(NAME, results)
