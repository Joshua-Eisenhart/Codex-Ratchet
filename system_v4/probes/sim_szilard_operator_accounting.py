#!/usr/bin/env python3
"""
Szilard-Style Operator Accounting Probe
========================================
Status: [Exploratory probe]

Assigns per-operator information/work-style bookkeeping to Ti/Fe/Te/Fi
and tests whether erase/measure/extract/reset-style asymmetries are
stable across engine types and terrains.

Szilard analogy:
  - Szilard engine: 1 measurement → 1 bit → kT ln 2 work
  - Here: does each operator have a consistent information-theoretic
    "role" (eraser, extractor, measurer, resetter) that is stable
    across terrains and types?

Method:
  1. Run both engine types through full cycles
  2. For each of the 4 operators (Ti, Fe, Te, Fi), measure:
     - ΔS (entropy change = "information cost")
     - ΔΦ (negentropy change = "work output")
     - |ΔS| / |ΔΦ| ratio = "operator efficiency"
     - Sign pattern: does this operator increase or decrease entropy?
  3. Test stability: do these roles hold across terrains and types?
  4. Look for Landauer-like bounds: is |ΔΦ| bounded by |ΔS|?

This probe is NOT claiming the operators are literal Szilard engines.
It tests whether information-work accounting is a useful structural
description of operator behavior.
"""

import numpy as np
import json, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from engine_core import (
    GeometricEngine, StageControls, TERRAINS, OPERATORS,
)
from geometric_operators import negentropy
from hopf_manifold import von_neumann_entropy_2x2


# ═══════════════════════════════════════════════════════════════════
# PER-OPERATOR BOOKKEEPING
# ═══════════════════════════════════════════════════════════════════

def run_operator_accounting(engine_type: int = 1, seed: int = 42,
                            n_cycles: int = 2) -> dict:
    """Run engine and track per-operator information/work balance."""
    rng = np.random.default_rng(seed)
    engine = GeometricEngine(engine_type=engine_type)
    state = engine.init_state(rng=rng)

    # Accumulate per-operator stats
    op_stats = {op: {
        "dphi_L_total": 0.0, "dphi_R_total": 0.0,
        "dphi_L_list": [], "dphi_R_list": [],
        "dga0_list": [],
        "count": 0,
        "sign_positive_L": 0, "sign_negative_L": 0,
        "sign_positive_R": 0, "sign_negative_R": 0,
        "by_terrain": {t["name"]: {"dphi_L": [], "dphi_R": [], "dga0": []}
                       for t in TERRAINS},
        "by_loop": {"fiber": {"dphi_L": [], "dphi_R": []},
                    "base": {"dphi_L": [], "dphi_R": []}},
    } for op in OPERATORS}

    for cycle in range(n_cycles):
        for stage_idx in range(8):
            terrain = TERRAINS[stage_idx]
            state = engine.step(state, stage_idx=stage_idx)

            n_history = len(state.history)
            new_entries = state.history[n_history - 4: n_history]

            for entry in new_entries:
                op = entry["op_name"]
                dphi_L = entry["dphi_L"]
                dphi_R = entry["dphi_R"]
                dga0 = entry["ga0_after"] - entry["ga0_before"]

                stats = op_stats[op]
                stats["dphi_L_total"] += dphi_L
                stats["dphi_R_total"] += dphi_R
                stats["dphi_L_list"].append(dphi_L)
                stats["dphi_R_list"].append(dphi_R)
                stats["dga0_list"].append(dga0)
                stats["count"] += 1

                if dphi_L > 0:
                    stats["sign_positive_L"] += 1
                else:
                    stats["sign_negative_L"] += 1
                if dphi_R > 0:
                    stats["sign_positive_R"] += 1
                else:
                    stats["sign_negative_R"] += 1

                stats["by_terrain"][terrain["name"]]["dphi_L"].append(dphi_L)
                stats["by_terrain"][terrain["name"]]["dphi_R"].append(dphi_R)
                stats["by_terrain"][terrain["name"]]["dga0"].append(dga0)
                stats["by_loop"][terrain["loop"]]["dphi_L"].append(dphi_L)
                stats["by_loop"][terrain["loop"]]["dphi_R"].append(dphi_R)

    return {
        "engine_type": engine_type,
        "seed": seed,
        "n_cycles": n_cycles,
        "op_stats": op_stats,
    }


def classify_operator(stats: dict) -> str:
    """Attempt to classify an operator's information-theoretic role."""
    avg_dphi_L = np.mean(stats["dphi_L_list"]) if stats["dphi_L_list"] else 0
    avg_dphi_R = np.mean(stats["dphi_R_list"]) if stats["dphi_R_list"] else 0
    avg_dga0 = np.mean(stats["dga0_list"]) if stats["dga0_list"] else 0

    total_dphi = avg_dphi_L + avg_dphi_R

    # Classification based on information-work patterns
    if total_dphi < -0.01 and avg_dga0 < -0.01:
        return "ERASER (destroys order, lowers ceiling)"
    elif total_dphi < -0.01 and avg_dga0 >= -0.01:
        return "DISSIPATOR (destroys order, stable ceiling)"
    elif total_dphi > 0.01 and avg_dga0 > 0.01:
        return "EXTRACTOR (creates order, raises ceiling)"
    elif total_dphi > 0.01 and avg_dga0 <= 0.01:
        return "CONCENTRATOR (creates order, stable ceiling)"
    elif abs(total_dphi) <= 0.01 and abs(avg_dga0) > 0.01:
        return "REGULATOR (neutral work, shifts ceiling)"
    else:
        return "NEUTRAL (minimal effect)"


def print_accounting(result: dict):
    """Print human-readable operator accounting."""
    et = result["engine_type"]
    print(f"\n{'='*80}")
    print(f"SZILARD-STYLE OPERATOR ACCOUNTING: Engine Type {et}")
    print(f"{'='*80}")
    print(f"\nThis is an EXPLORATORY probe. Szilard analogy is a search direction, not canon.\n")

    print(f"  PER-OPERATOR SUMMARY:")
    print(f"  {'Op':<4} {'avg ΔΦ_L':>10} {'avg ΔΦ_R':>10} {'avg Δga0':>10} "
          f"{'sign L(+/-)':>12} {'sign R(+/-)':>12} {'Classification':<30}")
    print(f"  {'-'*90}")

    for op in OPERATORS:
        s = result["op_stats"][op]
        avg_L = np.mean(s["dphi_L_list"]) if s["dphi_L_list"] else 0
        avg_R = np.mean(s["dphi_R_list"]) if s["dphi_R_list"] else 0
        avg_ga0 = np.mean(s["dga0_list"]) if s["dga0_list"] else 0
        role = classify_operator(s)
        print(f"  {op:<4} {avg_L:>+10.5f} {avg_R:>+10.5f} {avg_ga0:>+10.5f} "
              f"{s['sign_positive_L']:>5}/{s['sign_negative_L']:<5} "
              f"{s['sign_positive_R']:>5}/{s['sign_negative_R']:<5} "
              f"{role:<30}")

    # Cross-terrain stability
    print(f"\n  CROSS-TERRAIN STABILITY:")
    print(f"  {'Op':<4} {'fiber avg':>10} {'base avg':>10} {'fiber/base':>12}")
    print(f"  {'-'*40}")
    for op in OPERATORS:
        s = result["op_stats"][op]
        fiber_L = s["by_loop"]["fiber"]["dphi_L"]
        base_L = s["by_loop"]["base"]["dphi_L"]
        fiber_avg = np.mean(fiber_L) if fiber_L else 0
        base_avg = np.mean(base_L) if base_L else 0
        if abs(base_avg) > 1e-8:
            ratio = fiber_avg / base_avg
        else:
            ratio = float('inf') if abs(fiber_avg) > 1e-8 else 1.0
        print(f"  {op:<4} {fiber_avg:>+10.5f} {base_avg:>+10.5f} {ratio:>+12.3f}")

    # Landauer-like bound check: is |ΔΦ| < |ΔS| (per operator)?
    print(f"\n  LANDAUER-LIKE BOUND CHECK:")
    print(f"  If operators respect information-work accounting,")
    print(f"  |work| should be bounded by |entropy cost|.\n")
    print(f"  {'Op':<4} {'|avg ΔΦ|':>10} {'|avg Δga0|':>11} {'bound?':>8}")
    print(f"  {'-'*36}")
    for op in OPERATORS:
        s = result["op_stats"][op]
        avg_dphi = abs(np.mean(s["dphi_L_list"]) + np.mean(s["dphi_R_list"]))
        avg_dga0 = abs(np.mean(s["dga0_list"]))
        bounded = "YES" if avg_dphi <= avg_dga0 + 0.001 else "NO"
        print(f"  {op:<4} {avg_dphi:>10.5f} {avg_dga0:>11.5f} {bounded:>8}")


def main():
    print("SZILARD-STYLE OPERATOR ACCOUNTING PROBE")
    print("Testing per-operator information/work bookkeeping.\n")

    all_results = {}
    for engine_type in (1, 2):
        for seed in (42, 123):
            result = run_operator_accounting(engine_type=engine_type, seed=seed)
            print_accounting(result)
            all_results[f"type{engine_type}_seed{seed}"] = result

    # Cross-type comparison
    print(f"\n{'='*80}")
    print("CROSS-TYPE OPERATOR ROLE STABILITY")
    print(f"{'='*80}")
    print(f"\n  Do operators keep the same classification across types and seeds?\n")

    for op in OPERATORS:
        roles = []
        for key, result in all_results.items():
            role = classify_operator(result["op_stats"][op])
            roles.append(f"{key}: {role}")
        stable = len(set(r.split(": ")[1] for r in roles)) == 1
        print(f"  {op}: {'STABLE ✅' if stable else 'UNSTABLE ⚠️'}")
        for r in roles:
            print(f"    {r}")

    # Save
    out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           "..", "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_file = os.path.join(out_dir, "szilard_operator_accounting.json")

    save_data = {}
    for key, result in all_results.items():
        ops = {}
        for op in OPERATORS:
            s = result["op_stats"][op]
            ops[op] = {
                "avg_dphi_L": float(np.mean(s["dphi_L_list"])),
                "avg_dphi_R": float(np.mean(s["dphi_R_list"])),
                "avg_dga0": float(np.mean(s["dga0_list"])),
                "count": s["count"],
                "classification": classify_operator(s),
            }
        save_data[key] = {
            "engine_type": result["engine_type"],
            "seed": result["seed"],
            "operators": ops,
        }

    with open(out_file, "w") as f:
        json.dump(save_data, f, indent=2)
    print(f"\n  Results saved to {out_file}")


if __name__ == "__main__":
    main()
