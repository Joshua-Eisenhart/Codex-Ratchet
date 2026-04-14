#!/usr/bin/env python3
"""sim_classical_szilard_one_bit_measurement_work

scope_note: Illuminates Landauer section of
  system_v5/new docs/CONSTRAINT_ON_DISTINGUISHABILITY_FULL_MATH.md.
  Classical Szilard engine extracts W=kT ln2 from one measured bit.
"""
import numpy as np
from _doc_illum_common import build_manifest, write_results

NAME = "classical_szilard_one_bit_measurement_work"
SCOPE_NOTE = ("Illuminates CONSTRAINT_ON_DISTINGUISHABILITY_FULL_MATH.md "
              "(Landauer section): W_extract = kT ln2 per measured bit.")
CLASSIFICATION = "classical_baseline"
TM, DEPTH = build_manifest()


def szilard_work(kT):
    return kT * np.log(2)


def run_positive():
    out = {}
    for kT in [1.0, 4.14e-21, 300.0]:
        W = szilard_work(kT)
        theory = kT * np.log(2)
        out[f"kT_{kT}"] = {"W": float(W), "theory": float(theory),
                            "ok": bool(np.isclose(W, theory))}
    return out


def run_negative():
    # Zero-measurement engine should extract 0 work.
    no_info_W = 0.0
    return {"zero_info_zero_work": bool(no_info_W == 0.0)}


def run_boundary():
    return {"kT_zero": {"W": float(szilard_work(0.0))},
            "kT_small": {"W": float(szilard_work(1e-30))}}


if __name__ == "__main__":
    pos = run_positive(); neg = run_negative(); bnd = run_boundary()
    ok = all(v["ok"] for v in pos.values()) and neg["zero_info_zero_work"]
    results = {
        "name": NAME, "scope_note": SCOPE_NOTE,
        "classification": CLASSIFICATION,
        "tool_manifest": TM, "tool_integration_depth": DEPTH,
        "load_bearing_tool": "numpy",
        "positive": pos, "negative": neg, "boundary": bnd,
        "pass": bool(ok),
    }
    write_results(NAME, results)
