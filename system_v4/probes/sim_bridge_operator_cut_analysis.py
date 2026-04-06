#!/usr/bin/env python3
"""
sim_bridge_operator_cut_analysis.py
====================================

Two focused investigations on the 3-qubit bridge operator algebra.

Investigation 1: Fi vs Fe -- which operator bridges which cut?
  - Fe = XX x I on q1,q2   (intra-partition for cut1, cross-partition for cut2)
  - Fi = X x I x Z on q1,q3 (cross-partition for cut1 when q3 not Z-eigenstate)
  Tests 5 operator combinations across 3 bipartition cuts.

Investigation 2: q3 initial state |+> activates Fi
  Fi = X x I x Z commutes with q3 in |0> (Z eigenstate) -> no entanglement.
  When q3 = |+>, Fi no longer commutes -> genuine cross-partition action.
  Tests |000>, |00+>, |0+0>, |+00> initial states.

Output: a2_state/sim_results/bridge_operator_cut_analysis_results.json
"""

import json
import os
import sys
from datetime import datetime, UTC

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sim_3qubit_bridge_prototype import (
    I2, SIGMA_X, SIGMA_Y, SIGMA_Z,
    partial_trace_keep,
    von_neumann_entropy,
    ensure_valid_density,
    build_3q_Ti,
    build_3q_Fe,
    build_3q_Te,
    build_3q_Fi,
    BIPARTITIONS,
    compute_info_measures,
)


# ═══════════════════════════════════════════════════════════════════
# SANITIZE NUMPY TYPES FOR JSON
# ═══════════════════════════════════════════════════════════════════

def sanitize(obj):
    """Recursively convert numpy types to native Python for JSON."""
    if isinstance(obj, dict):
        return {k: sanitize(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [sanitize(v) for v in obj]
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating,)):
        return float(obj)
    if isinstance(obj, np.bool_):
        return bool(obj)
    if isinstance(obj, np.ndarray):
        return sanitize(obj.tolist())
    return obj


# ═══════════════════════════════════════════════════════════════════
# INVESTIGATION 1: OPERATOR-PER-CUT ISOLATION
# ═══════════════════════════════════════════════════════════════════

def run_operator_subset(rho_init, n_cycles, operators, dephasing=0.05):
    """
    Run n_cycles with only the named operators active.
    operators: dict of name -> callable, applied in order: Ti, Fe, Te, Fi
    (only those present in the dict).

    Returns per-cycle I_c for each cut, plus summary.
    """
    apply_order = ["Ti", "Fe", "Te", "Fi"]
    history = []
    rho = rho_init.copy()

    for cycle in range(1, n_cycles + 1):
        for op_name in apply_order:
            if op_name in operators:
                rho = operators[op_name](rho, polarity_up=True)

        info = compute_info_measures(rho)
        row = {"cycle": cycle}
        for cut_name in BIPARTITIONS:
            row[cut_name] = info[cut_name]["I_c"]
        history.append(row)

    # Summarize: max I_c per cut, total positive cycles per cut
    summary = {}
    for cut_name in BIPARTITIONS:
        values = [h[cut_name] for h in history]
        max_ic = max(values)
        pos_count = sum(1 for v in values if v > 1e-10)
        summary[cut_name] = {
            "max_ic": round(float(max_ic), 8),
            "positive_cycles": int(pos_count),
            "trajectory": [round(float(v), 8) for v in values],
        }
    return summary


def investigation_1(n_cycles=20, dephasing=0.05):
    """Fi vs Fe: which operator bridges which cut?"""
    print("\n" + "=" * 72)
    print("  INVESTIGATION 1: Fi vs Fe -- operator-per-cut isolation")
    print("=" * 72)

    # Initial state: |000>
    rho_init = np.zeros((8, 8), dtype=complex)
    rho_init[0, 0] = 1.0

    # Build operators with controlled dephasing
    Ti = build_3q_Ti(strength=dephasing)
    Fe = build_3q_Fe(strength=1.0, phi=0.4)
    Te = build_3q_Te(strength=dephasing, q=0.7)
    Fi = build_3q_Fi(strength=1.0, theta=np.pi)

    configs = {
        "Fe_only": {"Fe": Fe},
        "Fi_only": {"Fi": Fi},
        "both":    {"Fe": Fe, "Fi": Fi},
        "no_Fi":   {"Ti": Ti, "Te": Te, "Fe": Fe},
        "no_Fe":   {"Ti": Ti, "Te": Te, "Fi": Fi},
    }

    results = {}
    for config_name, ops in configs.items():
        print(f"\n  Config: {config_name} (operators: {list(ops.keys())})")
        summary = run_operator_subset(rho_init, n_cycles, ops, dephasing)
        results[config_name] = {}
        for cut_name in BIPARTITIONS:
            s = summary[cut_name]
            results[config_name][cut_name] = {
                "max_ic": s["max_ic"],
                "positive_cycles": s["positive_cycles"],
                "trajectory": s["trajectory"],
            }
            print(f"    {cut_name:20s}  max I_c = {s['max_ic']:+.6f}  "
                  f"pos_cycles = {s['positive_cycles']}")

    return results


# ═══════════════════════════════════════════════════════════════════
# INVESTIGATION 2: INITIAL STATE ACTIVATION OF Fi
# ═══════════════════════════════════════════════════════════════════

def make_initial_state_variants():
    """Build |000>, |00+>, |0+0>, |+00> as 8x8 density matrices."""
    states = {}

    # |000>
    v000 = np.zeros(8, dtype=complex)
    v000[0] = 1.0
    states["000"] = np.outer(v000, v000.conj())

    # |00+> = (1/sqrt2)(|000> + |001>) -> [1,1,0,0,0,0,0,0]/sqrt2
    v00p = np.zeros(8, dtype=complex)
    v00p[0] = 1.0 / np.sqrt(2)
    v00p[1] = 1.0 / np.sqrt(2)
    states["00+"] = np.outer(v00p, v00p.conj())

    # |0+0> = (1/sqrt2)(|000> + |010>) -> [1,0,1,0,0,0,0,0]/sqrt2
    v0p0 = np.zeros(8, dtype=complex)
    v0p0[0] = 1.0 / np.sqrt(2)
    v0p0[2] = 1.0 / np.sqrt(2)
    states["0+0"] = np.outer(v0p0, v0p0.conj())

    # |+00> = (1/sqrt2)(|000> + |100>) -> [1,0,0,0,1,0,0,0]/sqrt2
    vp00 = np.zeros(8, dtype=complex)
    vp00[0] = 1.0 / np.sqrt(2)
    vp00[4] = 1.0 / np.sqrt(2)
    states["+00"] = np.outer(vp00, vp00.conj())

    return states


def investigation_2(n_cycles=20, dephasing=0.05):
    """q3 initial state |+> activates Fi across partitions."""
    print("\n" + "=" * 72)
    print("  INVESTIGATION 2: Initial state activation of Fi")
    print("=" * 72)

    states = make_initial_state_variants()

    # Full operator set: Ti + Fe + Te + Fi
    Ti = build_3q_Ti(strength=dephasing)
    Fe = build_3q_Fe(strength=1.0, phi=0.4)
    Te = build_3q_Te(strength=dephasing, q=0.7)
    Fi = build_3q_Fi(strength=1.0, theta=np.pi)

    full_ops = {"Ti": Ti, "Fe": Fe, "Te": Te, "Fi": Fi}

    results = {}
    for state_name, rho_init in states.items():
        rho_init = ensure_valid_density(rho_init)
        print(f"\n  Initial state: |{state_name}>")
        summary = run_operator_subset(rho_init, n_cycles, full_ops, dephasing)

        state_result = {}
        total_positive = 0
        for cut_name in BIPARTITIONS:
            s = summary[cut_name]
            state_result[f"{cut_name}_max_ic"] = s["max_ic"]
            state_result[f"{cut_name}_trajectory"] = s["trajectory"]
            total_positive += s["positive_cycles"]
            print(f"    {cut_name:20s}  max I_c = {s['max_ic']:+.6f}  "
                  f"pos_cycles = {s['positive_cycles']}")

        state_result["positive_cycles"] = total_positive
        results[state_name] = state_result

    return results


# ═══════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════

def main():
    print("=" * 72)
    print("  BRIDGE OPERATOR CUT ANALYSIS")
    print("  Fi vs Fe isolation + initial state activation")
    print("=" * 72)

    inv1 = investigation_1(n_cycles=20, dephasing=0.05)
    inv2 = investigation_2(n_cycles=20, dephasing=0.05)

    # Build finding string
    # Analyze inv1 to determine which operator bridges which cut
    findings = []

    # Check Fe_only vs Fi_only for each cut
    for cut_name in BIPARTITIONS:
        fe_max = inv1["Fe_only"][cut_name]["max_ic"]
        fi_max = inv1["Fi_only"][cut_name]["max_ic"]
        both_max = inv1["both"][cut_name]["max_ic"]
        if fe_max > 1e-10 and fi_max <= 1e-10:
            findings.append(f"{cut_name}: Fe bridges (max={fe_max:.6f}), Fi inactive")
        elif fi_max > 1e-10 and fe_max <= 1e-10:
            findings.append(f"{cut_name}: Fi bridges (max={fi_max:.6f}), Fe inactive")
        elif fe_max > 1e-10 and fi_max > 1e-10:
            findings.append(f"{cut_name}: BOTH bridge (Fe={fe_max:.6f}, Fi={fi_max:.6f})")
        else:
            findings.append(f"{cut_name}: NEITHER bridges from |000>")

    # Check if |00+> activates Fi on cut1
    if "00+" in inv2:
        ic_00p_cut1 = inv2["00+"].get("cut1_1vs23_max_ic", 0)
        ic_000_cut1 = inv2["000"].get("cut1_1vs23_max_ic", 0)
        if ic_00p_cut1 > ic_000_cut1 + 1e-10:
            findings.append(
                f"|00+> activates Fi on cut1 (I_c={ic_00p_cut1:.6f} vs "
                f"|000> I_c={ic_000_cut1:.6f})"
            )

    finding_text = "; ".join(findings)
    print(f"\n  FINDING: {finding_text}")

    # Reshape inv2 for output format
    inv2_output = {}
    for state_name, data in inv2.items():
        inv2_output[state_name] = {
            "cut1_max_ic": data.get("cut1_1vs23_max_ic", 0),
            "cut2_max_ic": data.get("cut2_12vs3_max_ic", 0),
            "cut3_max_ic": data.get("cut3_13vs2_max_ic", 0),
            "cut1_trajectory": data.get("cut1_1vs23_trajectory", []),
            "cut2_trajectory": data.get("cut2_12vs3_trajectory", []),
            "cut3_trajectory": data.get("cut3_13vs2_trajectory", []),
            "positive_cycles": data.get("positive_cycles", 0),
        }

    # Reshape inv1 for output format
    inv1_output = {}
    for config_name, cuts in inv1.items():
        inv1_output[config_name] = {}
        for cut_name, data in cuts.items():
            inv1_output[config_name][cut_name] = {
                "max_ic": data["max_ic"],
                "positive_cycles": data["positive_cycles"],
                "trajectory": data["trajectory"],
            }

    output = {
        "name": "bridge_operator_cut_analysis",
        "investigation_1_operator_per_cut": inv1_output,
        "investigation_2_initial_states": inv2_output,
        "finding": finding_text,
        "timestamp": datetime.now(UTC).strftime("%Y-%m-%d"),
    }

    output = sanitize(output)

    out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "bridge_operator_cut_analysis_results.json")
    with open(out_path, "w") as f:
        json.dump(output, f, indent=2)
    print(f"\nResults written to {out_path}")

    return output


if __name__ == "__main__":
    main()
