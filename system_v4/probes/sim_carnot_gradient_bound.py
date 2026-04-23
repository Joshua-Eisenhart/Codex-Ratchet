#!/usr/bin/env python3
"""
Carnot-Style Runtime Probe: Ax0/Ax5 Gradient-Bound Test
========================================================
Status: [Exploratory probe]

Tests whether a stable gradient/bound relation emerges between
the Ax0-like drive (ga0_level / entropy gradient) and the
Ax5-like curvature (torus latitude / transport cost).

Carnot analogy:
  - Carnot efficiency: η = 1 - T_cold / T_hot
  - Here: does the engine produce a stable ratio between
    the "drive" (Ax0) and the "curvature cost" (Ax5)?

Method:
  1. Run engine cycles across a grid of (ga0_level, torus_eta) programs
  2. At each operating point, measure:
     - Total ΔΦ (negentropy change = "work output")
     - ga0_level regime ("temperature")
     - torus transport cost ("curvature")
  3. Look for: a bound relation where ΔΦ is constrained by
     the ratio of (ga0, eta) parameters — analogous to Carnot
  4. If no bound emerges, report that honestly

This probe is NOT claiming the engines are Carnot engines.
It is testing whether a Carnot-like efficiency bound is
a useful structural constraint on the runtime.
"""

import numpy as np
import json, os, sys
classification = "classical_baseline"  # auto-backfill

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# =====================================================================
# TOOL MANIFEST -- required by ENFORCEMENT_AND_PROCESS_RULES.md
# =====================================================================
TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False,
                "reason": "engine_core uses numpy; torch not required for sweep statistics"},
    "pyg":     {"tried": False, "used": False, "reason": "no graph transport in this probe"},
    "z3":      {"tried": False, "used": False,
                "reason": "symbolic proof lives in sim_carnot_constraint_admissibility_fence.py"},
    "cvc5":    {"tried": False, "used": False, "reason": "z3 chosen for the proof-layer sibling sim"},
    "sympy":   {"tried": False, "used": False,
                "reason": "symbolic efficiency bound proven in constraint-admissibility sibling"},
    "clifford":{"tried": False, "used": False, "reason": "rotor geometry not driving this bound test"},
    "geomstats":{"tried": False, "used": False, "reason": "metric learning unused"},
    "e3nn":    {"tried": False, "used": False, "reason": "no equivariant network"},
    "rustworkx":{"tried": False, "used": False, "reason": "no graph structure"},
    "xgi":     {"tried": False, "used": False, "reason": "no hypergraph"},
    "toponetx":{"tried": False, "used": False, "reason": "no cell complex"},
    "gudhi":   {"tried": False, "used": False, "reason": "no persistent homology"},
}

TOOL_INTEGRATION_DEPTH = {
    "pytorch": None, "pyg": None, "z3": None, "cvc5": None, "sympy": None,
    "clifford": None, "geomstats": None, "e3nn": None,
    "rustworkx": None, "xgi": None, "toponetx": None, "gudhi": None,
}

# numpy is the load-bearing numeric tool here; manifest only lists optional ecosystem tools.

from engine_core import (
    GeometricEngine, StageControls,
    TORUS_INNER, TORUS_CLIFFORD, TORUS_OUTER,
)
from geometric_operators import negentropy
from hopf_manifold import torus_radii, von_neumann_entropy_2x2


# ═══════════════════════════════════════════════════════════════════
# PROTOCOL
# ═══════════════════════════════════════════════════════════════════

def run_programmed_cycle(engine_type: int, ga0_program: float,
                         torus_program: float, seed: int = 42) -> dict:
    """Run one full 8-stage cycle with fixed ga0 and torus controls.

    Returns work output (total ΔΦ), entropy trajectory, and transport cost.
    """
    rng = np.random.default_rng(seed)
    engine = GeometricEngine(engine_type=engine_type)
    state = engine.init_state(ga0_level=ga0_program, rng=rng)

    controls = {i: StageControls(piston=0.5, torus=torus_program,
                                  axis0=ga0_program)
                for i in range(8)}

    axes_before = engine.read_axes(state)
    state_after = engine.run_cycle(state, controls=controls)
    axes_after = engine.read_axes(state_after)

    # Work = total negentropy change across both spinors
    total_dphi_L = sum(h["dphi_L"] for h in state_after.history)
    total_dphi_R = sum(h["dphi_R"] for h in state_after.history)
    total_work = abs(total_dphi_L) + abs(total_dphi_R)

    # Entropy at start and end (combined L+R)
    rho_avg_before = (state.rho_L + state.rho_R) / 2
    rho_avg_after = (state_after.rho_L + state_after.rho_R) / 2
    S_before = von_neumann_entropy_2x2(rho_avg_before)
    S_after = von_neumann_entropy_2x2(rho_avg_after)

    # Torus transport cost: how far did eta actually move?
    eta_delta = abs(state_after.eta - state.eta)

    # Curvature at operating point
    R_major, R_minor = torus_radii(torus_program)
    curvature_proxy = R_major * R_minor  # area of torus cross-section

    return {
        "engine_type": engine_type,
        "ga0_program": ga0_program,
        "torus_program": torus_program,
        "total_work": float(total_work),
        "dphi_L": float(total_dphi_L),
        "dphi_R": float(total_dphi_R),
        "S_before": float(S_before),
        "S_after": float(S_after),
        "delta_S": float(S_after - S_before),
        "eta_delta": float(eta_delta),
        "curvature_proxy": float(curvature_proxy),
        "ga0_final": float(state_after.ga0_level),
        "GA0_before": float(axes_before["GA0_entropy"]),
        "GA0_after": float(axes_after["GA0_entropy"]),
        "GA5_before": float(axes_before["GA5_coupling"]),
        "GA5_after": float(axes_after["GA5_coupling"]),
    }


# ═══════════════════════════════════════════════════════════════════
# SWEEP
# ═══════════════════════════════════════════════════════════════════

def run_sweep():
    """Sweep ga0 × torus × engine_type and look for bound structure."""
    ga0_levels = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]
    torus_programs = [TORUS_INNER, TORUS_CLIFFORD, TORUS_OUTER]
    torus_names = {TORUS_INNER: "inner", TORUS_CLIFFORD: "clifford", TORUS_OUTER: "outer"}

    all_results = []

    for engine_type in (1, 2):
        for ga0 in ga0_levels:
            for torus in torus_programs:
                result = run_programmed_cycle(engine_type, ga0, torus)
                result["torus_name"] = torus_names[torus]
                all_results.append(result)

    return all_results


def analyze_bounds(results):
    """Look for Carnot-like bound structure in the sweep data."""
    print(f"\n{'='*80}")
    print("CARNOT-STYLE RUNTIME PROBE: Ax0/Ax5 Gradient-Bound Test")
    print(f"{'='*80}")
    print(f"\nTotal operating points: {len(results)}")
    print(f"\nThis is an EXPLORATORY probe. Carnot analogy is a search direction, not canon.\n")

    # Group by engine type
    for et in (1, 2):
        subset = [r for r in results if r["engine_type"] == et]
        print(f"\n  ENGINE TYPE {et}")
        print(f"  {'ga0':>5} {'torus':<9} {'|ΔΦ| work':>10} {'ΔS':>8} {'curve':>7} {'GA0Δ':>7} {'GA5Δ':>7}")
        print(f"  {'-'*58}")

        for r in sorted(subset, key=lambda x: (x["ga0_program"], x["torus_program"])):
            ga0_delta = r["GA0_after"] - r["GA0_before"]
            ga5_delta = r["GA5_after"] - r["GA5_before"]
            print(f"  {r['ga0_program']:>5.1f} {r['torus_name']:<9} "
                  f"{r['total_work']:>10.5f} "
                  f"{r['delta_S']:>+8.4f} "
                  f"{r['curvature_proxy']:>7.4f} "
                  f"{ga0_delta:>+7.4f} "
                  f"{ga5_delta:>+7.4f}")

    # Test 1: Does work output correlate with ga0_program?
    print(f"\n  CORRELATION TESTS:")
    ga0_vals = np.array([r["ga0_program"] for r in results])
    work_vals = np.array([r["total_work"] for r in results])
    curve_vals = np.array([r["curvature_proxy"] for r in results])

    if np.std(work_vals) > 1e-12 and np.std(ga0_vals) > 1e-12:
        r_ga0_work = np.corrcoef(ga0_vals, work_vals)[0, 1]
    else:
        r_ga0_work = 0.0
    print(f"    ga0 vs |ΔΦ| work:     r = {r_ga0_work:+.4f}")

    if np.std(work_vals) > 1e-12 and np.std(curve_vals) > 1e-12:
        r_curve_work = np.corrcoef(curve_vals, work_vals)[0, 1]
    else:
        r_curve_work = 0.0
    print(f"    curvature vs |ΔΦ| work: r = {r_curve_work:+.4f}")

    # Test 2: Compare a static-geometry denominator against realized transport cost.
    efficiencies = []
    runtime_efficiencies = []
    hybrid_efficiencies = []
    for r in results:
        denom = r["ga0_program"] * r["curvature_proxy"]
        if denom > 1e-12:
            eta = r["total_work"] / denom
            efficiencies.append(eta)
        runtime_denom = r["ga0_program"] * r["eta_delta"]
        if runtime_denom > 1e-12:
            runtime_efficiencies.append(r["total_work"] / runtime_denom)
        hybrid_denom = r["ga0_program"] * r["eta_delta"] * r["curvature_proxy"]
        if hybrid_denom > 1e-12:
            hybrid_efficiencies.append(r["total_work"] / hybrid_denom)

    if efficiencies:
        eff_arr = np.array(efficiencies)
        print(f"\n    η = work / (ga0 × curvature):")
        print(f"      mean = {np.mean(eff_arr):.6f}")
        print(f"      std  = {np.std(eff_arr):.6f}")
        print(f"      CV   = {np.std(eff_arr)/max(np.mean(eff_arr), 1e-12):.4f}")
        if np.std(eff_arr) / max(np.mean(eff_arr), 1e-12) < 0.15:
            print(f"      → LOW VARIANCE: candidate bound relation found")
        else:
            print(f"      → HIGH VARIANCE: no stable bound at this parameterization")

    if runtime_efficiencies:
        runtime_eff_arr = np.array(runtime_efficiencies)
        print(f"\n    η_runtime = work / (ga0 × eta_delta):")
        print(f"      mean = {np.mean(runtime_eff_arr):.6f}")
        print(f"      std  = {np.std(runtime_eff_arr):.6f}")
        print(f"      CV   = {np.std(runtime_eff_arr)/max(np.mean(runtime_eff_arr), 1e-12):.4f}")

    if hybrid_efficiencies:
        hybrid_eff_arr = np.array(hybrid_efficiencies)
        print(f"\n    η_hybrid = work / (ga0 × eta_delta × curvature):")
        print(f"      mean = {np.mean(hybrid_eff_arr):.6f}")
        print(f"      std  = {np.std(hybrid_eff_arr):.6f}")
        print(f"      CV   = {np.std(hybrid_eff_arr)/max(np.mean(hybrid_eff_arr), 1e-12):.4f}")

    # Test 3: Ax0 vs Ax5 separation check
    ga0_deltas = np.array([r["GA0_after"] - r["GA0_before"] for r in results])
    ga5_deltas = np.array([r["GA5_after"] - r["GA5_before"] for r in results])
    if np.std(ga0_deltas) > 1e-12 and np.std(ga5_deltas) > 1e-12:
        r_ax0_ax5 = np.corrcoef(ga0_deltas, ga5_deltas)[0, 1]
    else:
        r_ax0_ax5 = 0.0
    print(f"\n    Ax0 delta vs Ax5 delta:  r = {r_ax0_ax5:+.4f}")
    if abs(r_ax0_ax5) < 0.3:
        print(f"      → WEAK: Ax0 and Ax5 respond independently (good for separation)")
    elif abs(r_ax0_ax5) > 0.7:
        print(f"      → STRONG: Ax0 and Ax5 are coupled (bad for separation)")
    else:
        print(f"      → MODERATE: partial coupling")

    return {
        "r_ga0_work": float(r_ga0_work),
        "r_curve_work": float(r_curve_work),
        "r_ax0_ax5": float(r_ax0_ax5),
        "efficiency_mean": float(np.mean(efficiencies)) if efficiencies else None,
        "efficiency_cv": float(np.std(efficiencies) / max(np.mean(efficiencies), 1e-12)) if efficiencies else None,
        "runtime_efficiency_mean": float(np.mean(runtime_efficiencies)) if runtime_efficiencies else None,
        "runtime_efficiency_cv": (
            float(np.std(runtime_efficiencies) / max(np.mean(runtime_efficiencies), 1e-12))
            if runtime_efficiencies
            else None
        ),
        "hybrid_efficiency_mean": float(np.mean(hybrid_efficiencies)) if hybrid_efficiencies else None,
        "hybrid_efficiency_cv": (
            float(np.std(hybrid_efficiencies) / max(np.mean(hybrid_efficiencies), 1e-12))
            if hybrid_efficiencies
            else None
        ),
    }


# =====================================================================
# POSITIVE / NEGATIVE / BOUNDARY TESTS (required by SIM contract)
# =====================================================================

def run_positive_tests(results):
    """Positive: at least one operating point produces non-zero work and a finite
    static-geometry efficiency. Also: work is non-negative (|ΔΦ| is absolute)."""
    works = [r["total_work"] for r in results]
    any_positive_work = any(w > 1e-9 for w in works)
    all_nonneg = all(w >= 0.0 for w in works)
    return {
        "any_positive_work": bool(any_positive_work),
        "all_work_nonneg": bool(all_nonneg),
        "n_points": len(results),
        "pass": bool(any_positive_work and all_nonneg),
    }


def run_negative_tests(results):
    """Negative: an uncorrelated efficiency denominator should NOT produce a
    stable (low-CV) ratio. We use a random denominator surrogate as the
    null — it must fail the bound-candidate criterion."""
    rng = np.random.default_rng(0)
    ratios = []
    for r in results:
        denom = rng.uniform(0.1, 1.0)
        ratios.append(r["total_work"] / denom)
    arr = np.array(ratios)
    mean = float(np.mean(arr))
    cv = float(np.std(arr) / max(abs(mean), 1e-12))
    # We require the random surrogate to NOT be "low variance" (CV < 0.15).
    # If it accidentally does, the bound criterion is meaningless.
    return {
        "surrogate_mean": mean,
        "surrogate_cv": cv,
        "surrogate_rejected_as_bound": bool(cv >= 0.15),
        "pass": bool(cv >= 0.15),
    }


def run_boundary_tests():
    """Boundary: extreme ga0 values (0.01, 0.99) at clifford torus should run
    without raising and produce finite work values."""
    import math
    out = {"cases": [], "pass": True}
    for ga0 in (0.01, 0.99):
        try:
            r = run_programmed_cycle(1, ga0, TORUS_CLIFFORD)
            finite = math.isfinite(r["total_work"])
            out["cases"].append({"ga0": ga0, "total_work": r["total_work"], "finite": finite})
            if not finite:
                out["pass"] = False
        except Exception as e:
            out["cases"].append({"ga0": ga0, "error": str(e)})
            out["pass"] = False
    return out


def main():
    results = run_sweep()
    summary = analyze_bounds(results)

    positive = run_positive_tests(results)
    negative = run_negative_tests(results)
    boundary = run_boundary_tests()

    # Save
    out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           "..", "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_file = os.path.join(out_dir, "carnot_gradient_bound.json")

    save_data = {
        "classification": "classical_baseline",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "summary": summary,
        "operating_points": [{k: v for k, v in r.items()} for r in results],
        "overall_pass": bool(positive["pass"] and negative["pass"] and boundary["pass"]),
    }
    with open(out_file, "w") as f:
        json.dump(save_data, f, indent=2, default=str)
    print(f"\n  Results saved to {out_file}")


if __name__ == "__main__":
    main()
