#!/usr/bin/env python3
"""
Axis 0 — Orbit Phase Alignment Probe
======================================
Direct characterization of the ~4 failures per 32-step forward MI co-arising.

From the attractor basin probe (Q2): 27–28/31 steps co-arise in the forward
MI measure MI(L[t], R[t+1]). About 3–4 fail per cycle.

Questions:
  P1: Are failures concentrated at a specific 4-cycle phase (Ti=0,Fe=1,Te=2,Fi=3)?
  P2: Are failures in the outer vs inner half of the orbit?
  P3: What distinguishes failure steps from success steps (lr_asym, ga0, loop_position)?
  P4: Does Clifford have more failures than inner/outer?
  P5: Are failures consistent across engine types 1 and 2?

If failures cluster at a specific phase position across all configs:
  → The proof strategy must handle that phase specially.
  → That phase is where the forward pairing is weakest.
If failures are random:
  → The 87–90% rate is intrinsic noise of the pairing, not a proof gap.

For the proof strategy:
  If Ti always succeeds (100% confirmed) and Fi has a fixed failure rate at a known
  phase position, we can prove co-arising EXCEPT at those positions and then
  show the positions are measure-zero in the formal limit.
"""

from __future__ import annotations
import json, os, sys
from datetime import UTC, datetime
import numpy as np
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from engine_core import GeometricEngine
from geometric_operators import _ensure_valid_density
from hopf_manifold import TORUS_CLIFFORD, TORUS_INNER, TORUS_OUTER

PSI_MINUS = np.array([0, 1, -1, 0], dtype=complex) / np.sqrt(2)
BELL = np.outer(PSI_MINUS, PSI_MINUS.conj())
SIGMA_X = np.array([[0, 1], [1, 0]], dtype=complex)
SIGMA_Y = np.array([[0, -1j], [1j, 0]], dtype=complex)
SIGMA_Z = np.array([[1, 0], [0, -1]], dtype=complex)

RESULTS_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "a2_state", "sim_results"
)
os.makedirs(RESULTS_DIR, exist_ok=True)

TORUS_CONFIGS = [
    ("inner",    TORUS_INNER),
    ("clifford", TORUS_CLIFFORD),
    ("outer",    TORUS_OUTER),
]
ENGINE_TYPES = [1, 2]
PHASE_NAMES  = {0: "Ti", 1: "Fe", 2: "Te", 3: "Fi"}


# --------------------------------------------------------------------------- #
# MI utilities                                                                 #
# --------------------------------------------------------------------------- #

def bloch(rho):
    return np.array([float(np.real(np.trace(s @ rho))) for s in [SIGMA_X, SIGMA_Y, SIGMA_Z]])

def lr_asym(a, b):
    return float(np.clip(0.5 * np.linalg.norm(bloch(a) - bloch(b)), 0.0, 1.0))

def vne(rho):
    rho = (rho + rho.conj().T) / 2
    ev = np.real(np.linalg.eigvalsh(rho))
    ev = ev[ev > 1e-15]
    return float(-np.sum(ev * np.log2(ev))) if len(ev) else 0.0

def bridge_mi(rho_L, rho_R):
    p = float(np.clip(lr_asym(rho_L, rho_R), 0.01, 0.99))
    rho_AB = _ensure_valid_density((1 - p) * np.kron(rho_L, rho_R) + p * BELL)
    rho_A = np.trace(rho_AB.reshape(2, 2, 2, 2), axis1=1, axis2=3)
    rho_B = np.trace(rho_AB.reshape(2, 2, 2, 2), axis1=0, axis2=2)
    return max(0.0, vne(rho_A) + vne(rho_B) - vne(rho_AB))


# --------------------------------------------------------------------------- #
# Core analysis per trajectory                                                 #
# --------------------------------------------------------------------------- #

def analyze_trajectory(history: list[dict]) -> dict:
    """
    Compute per-step forward MI co-arising and characterize failures.
    Returns per-step analysis with failure flags and attractor features.
    """
    T = len(history)
    # Forward MI series: ct_mi[t] = MI(L[t], R[t+1])
    ct_mi = [bridge_mi(history[t]["rho_L"],
                       history[min(t+1, T-1)]["rho_R"]) for t in range(T)]

    steps = []
    for t in range(1, T):
        d_ct_mi = ct_mi[t] - ct_mi[t-1]
        ga0_curr = history[t]["ga0_after"]
        ga0_prev = history[t-1]["ga0_after"]
        d_ga0 = ga0_curr - ga0_prev

        phase_pos = t % 4          # 0=Ti, 1=Fe, 2=Te, 3=Fi within 4-cycle
        orbit_half = "outer" if t < 16 else "inner"
        loop_position = history[t].get("loop_position", "?")

        asym = lr_asym(history[t]["rho_L"], history[t]["rho_R"])

        # Co-arising check
        significant = abs(d_ct_mi) > 1e-6 and abs(d_ga0) > 1e-6
        if significant:
            coarises = (d_ga0 * d_ct_mi) > 0
        else:
            coarises = None   # near-zero: neutral

        steps.append({
            "step": t,
            "op_name": history[t]["op_name"],
            "phase_pos": phase_pos,
            "phase_name": PHASE_NAMES[phase_pos],
            "orbit_half": orbit_half,
            "loop_position": loop_position,
            "ga0_before": float(history[t-1]["ga0_after"]),
            "ga0_after": float(ga0_curr),
            "d_ga0": float(d_ga0),
            "ct_mi": float(ct_mi[t]),
            "d_ct_mi": float(d_ct_mi),
            "lr_asym": float(asym),
            "coarises": coarises,
        })

    n_success = sum(1 for s in steps if s["coarises"] is True)
    n_fail    = sum(1 for s in steps if s["coarises"] is False)
    n_neutral = sum(1 for s in steps if s["coarises"] is None)

    # Phase breakdown
    phase_stats = {}
    for ph in range(4):
        ph_steps = [s for s in steps if s["phase_pos"] == ph]
        ph_ok  = sum(1 for s in ph_steps if s["coarises"] is True)
        ph_bad = sum(1 for s in ph_steps if s["coarises"] is False)
        ph_neu = sum(1 for s in ph_steps if s["coarises"] is None)
        phase_stats[PHASE_NAMES[ph]] = {"ok": ph_ok, "fail": ph_bad, "neutral": ph_neu}

    # Half breakdown
    half_stats = {}
    for half in ["outer", "inner"]:
        h_steps = [s for s in steps if s["orbit_half"] == half]
        h_ok  = sum(1 for s in h_steps if s["coarises"] is True)
        h_bad = sum(1 for s in h_steps if s["coarises"] is False)
        half_stats[half] = {"ok": h_ok, "fail": h_bad}

    return {
        "n_steps": T,
        "n_success": n_success,
        "n_fail": n_fail,
        "n_neutral": n_neutral,
        "phase_stats": phase_stats,
        "half_stats": half_stats,
        "steps": steps,
    }


# --------------------------------------------------------------------------- #
# Main                                                                         #
# --------------------------------------------------------------------------- #

def main():
    print("Axis 0 Orbit Phase Alignment Probe")
    print("=" * 50)

    all_results = []
    # Aggregate failure phase counts
    agg_phase = defaultdict(lambda: {"ok": 0, "fail": 0, "neutral": 0})
    agg_half  = defaultdict(lambda: {"ok": 0, "fail": 0})
    failure_profiles = []   # details on all failure steps

    for engine_type in ENGINE_TYPES:
        for torus_name, torus_val in TORUS_CONFIGS:
            try:
                engine = GeometricEngine(engine_type=engine_type)
                state  = engine.init_state(eta=torus_val)
                final  = engine.run_cycle(state)
            except Exception as e:
                print(f"  [{engine_type}/{torus_name}] SKIP: {e}")
                continue

            traj = analyze_trajectory(final.history)
            key = f"{engine_type}/{torus_name}"

            # Accumulate per-phase
            for ph, stats in traj["phase_stats"].items():
                agg_phase[ph]["ok"]      += stats["ok"]
                agg_phase[ph]["fail"]    += stats["fail"]
                agg_phase[ph]["neutral"] += stats["neutral"]
            for half, stats in traj["half_stats"].items():
                agg_half[half]["ok"]   += stats["ok"]
                agg_half[half]["fail"] += stats["fail"]

            # Collect failure step profiles
            for s in traj["steps"]:
                if s["coarises"] is False:
                    failure_profiles.append({**s, "config": key})

            rate = traj["n_success"] / (traj["n_success"] + traj["n_fail"]) if (traj["n_success"] + traj["n_fail"]) > 0 else None
            print(f"\n  [{key}] ok={traj['n_success']} fail={traj['n_fail']} neutral={traj['n_neutral']} "
                  f"rate={rate:.3f}" if rate else f"  [{key}] no nonzero steps")
            print(f"    Phase: ", end="")
            for ph in ["Ti", "Fe", "Te", "Fi"]:
                st = traj["phase_stats"][ph]
                print(f"{ph}={st['ok']}/{st['ok']+st['fail']+st['neutral']} ", end="")
            print()
            print(f"    Half:  outer={traj['half_stats']['outer']['ok']}/{sum(traj['half_stats']['outer'].values())} "
                  f"inner={traj['half_stats']['inner']['ok']}/{sum(traj['half_stats']['inner'].values())}")

            all_results.append({
                "config": key,
                "engine_type": engine_type,
                "torus": torus_name,
                "eta": torus_val,
                "n_success": traj["n_success"],
                "n_fail": traj["n_fail"],
                "n_neutral": traj["n_neutral"],
                "forward_coarising_rate": rate,
                "phase_stats": traj["phase_stats"],
                "half_stats": traj["half_stats"],
            })

    # ---------- Aggregate analysis ---------------------------------------- #
    print("\n=== AGGREGATE PHASE ANALYSIS ===")
    for ph in ["Ti", "Fe", "Te", "Fi"]:
        st = agg_phase[ph]
        total_decided = st["ok"] + st["fail"]
        rate = st["ok"] / total_decided if total_decided > 0 else None
        bar = "✓" * st["ok"] + "✗" * st["fail"]
        print(f"  {ph}: {st['ok']:2d}/{total_decided:2d} ({rate*100:.0f}%)" if rate else
              f"  {ph}: all neutral")

    print("\n=== AGGREGATE HALF ANALYSIS ===")
    for half in ["outer", "inner"]:
        st = agg_half[half]
        total = st["ok"] + st["fail"]
        rate = st["ok"] / total if total > 0 else None
        print(f"  {half}: {st['ok']}/{total} ({rate*100:.0f}%)" if rate else f"  {half}: all neutral")

    print(f"\n=== FAILURE PROFILES ({len(failure_profiles)} total) ===")
    if failure_profiles:
        # Group by phase
        for ph in ["Ti", "Fe", "Te", "Fi"]:
            ph_fails = [f for f in failure_profiles if f["phase_name"] == ph]
            if ph_fails:
                print(f"\n  {ph} failures ({len(ph_fails)}):")
                for f in ph_fails[:4]:
                    print(f"    [{f['config']}] step={f['step']:2d} loop={f['loop_position']} "
                          f"lr_asym={f['lr_asym']:.3f} ga0={f['ga0_before']:.3f}→{f['ga0_after']:.3f} "
                          f"d_ct_mi={f['d_ct_mi']:+.4f} d_ga0={f['d_ga0']:+.4f}")

    # ---------- Clifford vs inner/outer comparison ------------------------- #
    print("\n=== CLIFFORD vs INNER/OUTER ===")
    for torus_name in ["inner", "clifford", "outer"]:
        configs = [r for r in all_results if r["torus"] == torus_name]
        if configs:
            mean_fail = np.mean([r["n_fail"] for r in configs])
            mean_rate = np.mean([r["forward_coarising_rate"] for r in configs if r["forward_coarising_rate"]])
            print(f"  {torus_name:9s}: mean_failures={mean_fail:.1f}  mean_rate={mean_rate:.3f}")

    # ---------- P5: engine type consistency -------------------------------- #
    print("\n=== ENGINE TYPE CONSISTENCY ===")
    for et in ENGINE_TYPES:
        configs = [r for r in all_results if r["engine_type"] == et]
        if configs:
            rates = [r["forward_coarising_rate"] for r in configs if r["forward_coarising_rate"]]
            print(f"  Engine {et}: mean={np.mean(rates):.3f}  std={np.std(rates):.3f}  "
                  f"range=[{min(rates):.3f},{max(rates):.3f}]")

    # ---------- Consistency check: do the same step indices fail? ---------- #
    print("\n=== FAILURE STEP CONSISTENCY ===")
    fail_positions = defaultdict(list)  # (engine_type, loop_position, phase_pos) → list of d_ct_mi
    for f in failure_profiles:
        key = (f["config"].split("/")[0], f["loop_position"], f["phase_name"])
        fail_positions[key].append(f["d_ct_mi"])
    for k, vals in sorted(fail_positions.items()):
        print(f"  {k}: {len(vals)} failures, d_ct_mi mean={np.mean(vals):+.4f}")

    # Serialize
    def strip(obj):
        if isinstance(obj, dict):   return {k: strip(v) for k, v in obj.items()}
        elif isinstance(obj, list): return [strip(v) for v in obj]
        elif isinstance(obj, (np.float32, np.float64)): return float(obj)
        elif isinstance(obj, (np.int32, np.int64)):     return int(obj)
        return obj

    results = {
        "timestamp": datetime.now(UTC).isoformat(),
        "probe": "sim_axis0_orbit_phase_alignment",
        "configs": strip(all_results),
        "aggregate_phase": dict(agg_phase),
        "aggregate_half": dict(agg_half),
        "failure_profiles": strip(failure_profiles),
        "n_total_failures": len(failure_profiles),
    }

    out = os.path.join(RESULTS_DIR, "axis0_orbit_phase_alignment_results.json")
    with open(out, "w") as fh:
        json.dump(results, fh, indent=2)
    print(f"\nResults written to {out}")
    return results


if __name__ == "__main__":
    main()
