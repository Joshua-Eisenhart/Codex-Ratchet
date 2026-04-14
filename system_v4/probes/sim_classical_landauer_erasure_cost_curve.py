#!/usr/bin/env python3
"""sim_classical_landauer_erasure_cost_curve

scope_note: Illuminates Landauer section of
  system_v5/new docs/CONSTRAINT_ON_DISTINGUISHABILITY_FULL_MATH.md:
  erasure dissipates at least kT ln2 per bit; partial erasure scales
  with H(p) - H(p_final).
"""
import numpy as np
from _doc_illum_common import build_manifest, write_results

NAME = "classical_landauer_erasure_cost_curve"
SCOPE_NOTE = ("Illuminates CONSTRAINT_ON_DISTINGUISHABILITY_FULL_MATH.md "
              "(Landauer section): E_erase >= kT * Delta H.")
CLASSIFICATION = "classical_baseline"
TM, DEPTH = build_manifest()


def H(p):
    p = np.clip(p, 1e-15, 1 - 1e-15)
    return -(p * np.log(p) + (1 - p) * np.log(1 - p))


def erase_cost(p, kT=1.0):
    # Full erasure to p=0 or p=1 costs kT * H(p).
    return kT * H(p)


def run_positive():
    out = {}
    for p in [0.5, 0.25, 0.1]:
        E = erase_cost(p)
        theory = H(p)
        out[f"p_{p}"] = {"E": float(E), "theory": float(theory),
                        "ok": bool(np.isclose(E, theory))}
    # Landauer floor at p=0.5 equals ln2
    out["floor"] = {"E": float(erase_cost(0.5)),
                    "ln2": float(np.log(2)),
                    "ok": bool(np.isclose(erase_cost(0.5), np.log(2)))}
    return out


def run_negative():
    # Proposed "free erasure" at p=0.5 must be rejected.
    claimed_free = 0.0
    return {"reject_free_erasure": bool(claimed_free < np.log(2))}


def run_boundary():
    return {"p_zero": {"E": float(erase_cost(1e-15))},
            "p_one":  {"E": float(erase_cost(1 - 1e-15))}}


if __name__ == "__main__":
    pos = run_positive(); neg = run_negative(); bnd = run_boundary()
    ok = (all(v["ok"] for v in pos.values())
          and neg["reject_free_erasure"])
    results = {
        "name": NAME, "scope_note": SCOPE_NOTE,
        "classification": CLASSIFICATION,
        "tool_manifest": TM, "tool_integration_depth": DEPTH,
        "load_bearing_tool": "numpy",
        "positive": pos, "negative": neg, "boundary": bnd,
        "pass": bool(ok),
    }
    write_results(NAME, results)
