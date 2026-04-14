#!/usr/bin/env python3
"""sim_classical_maxwell_demon_information_accounting

scope_note: Illuminates Landauer section of
  system_v5/new docs/CONSTRAINT_ON_DISTINGUISHABILITY_FULL_MATH.md:
  a Maxwell demon's extracted work is bookended by memory-erasure cost
  so net dissipation >= 0.
"""
import numpy as np
from _doc_illum_common import build_manifest, write_results

NAME = "classical_maxwell_demon_information_accounting"
SCOPE_NOTE = ("Illuminates CONSTRAINT_ON_DISTINGUISHABILITY_FULL_MATH.md "
              "(Landauer section): W_demon <= kT * I_memory, net dissipation non-negative "
              "once memory erasure is included.")
CLASSIFICATION = "classical_baseline"
TM, DEPTH = build_manifest()


def demon_balance(I_bits, W_extracted, kT=1.0):
    erase_cost = kT * I_bits * np.log(2)
    net = erase_cost - W_extracted
    return net, erase_cost


def run_positive():
    out = {}
    for I_bits, W in [(1.0, 0.5), (2.0, 1.0), (0.1, 0.05)]:
        net, ec = demon_balance(I_bits, W)
        out[f"I_{I_bits}_W_{W}"] = {
            "net_dissipation": float(net), "erase_cost": float(ec),
            "ok": bool(net >= -1e-12)
        }
    return out


def run_negative():
    # Claimed "free" demon extracting W > kT*I*ln2 violates balance.
    I_bits, W = 1.0, 2.0  # W > ln2
    net, _ = demon_balance(I_bits, W)
    return {"reject_overdraw_demon": bool(net < 0)}


def run_boundary():
    # Zero information => zero extractable work.
    net, ec = demon_balance(0.0, 0.0)
    return {"zero_info": {"net": float(net), "erase_cost": float(ec)}}


if __name__ == "__main__":
    pos = run_positive(); neg = run_negative(); bnd = run_boundary()
    ok = (all(v["ok"] for v in pos.values())
          and neg["reject_overdraw_demon"])
    results = {
        "name": NAME, "scope_note": SCOPE_NOTE,
        "classification": CLASSIFICATION,
        "tool_manifest": TM, "tool_integration_depth": DEPTH,
        "load_bearing_tool": "numpy",
        "positive": pos, "negative": neg, "boundary": bnd,
        "pass": bool(ok),
    }
    write_results(NAME, results)
