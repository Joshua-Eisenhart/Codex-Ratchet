#!/usr/bin/env python3
"""
carnot_engine.py -- classical Carnot cycle competence check.

Purpose (owner framing): this is NOT a Codex-Ratchet axis/lego/bridge claim.
It is a competence check -- "if you can't sim them you can't sim my engines."
classification="classical_baseline", promotion_allowed=False throughout.

PHYSICS
-------
Working substance: n=1 mol monatomic ideal gas (Cv = 3/2 R, gamma = Cp/Cv = 5/3),
PV = nRT. Four reversible strokes:
  1->2  isothermal expansion at Th   (V1 -> V2, V2 > V1)
  2->3  adiabatic  expansion         (Th -> Tc)
  3->4  isothermal compression at Tc (V3 -> V4, V4 < V3)
  4->1  adiabatic  compression       (Tc -> Th)
Adiabats: T V^(gamma-1) = const, which forces V3/V2 = V4/V1 = (Th/Tc)^(1/(gamma-1))
-- the standard Carnot closure condition. Under that closure:
  Qh = n R Th ln(V2/V1),  Qc = n R Tc ln(V3/V4),  Qc/Qh = Tc/Th  exactly,
  eta = 1 - Qc/Qh = 1 - Tc/Th  exactly, independent of gamma and of the volumes.

PREREGISTERED PASS CRITERIA (checked in header, before any run)
-----------------------------------------------------------------
  C1: |eta_numeric - (1 - Tc/Th)| / (1 - Tc/Th)          <= 1e-6   (relative)
  C2: |W_net_numeric - W_net_analytic| / |W_net_analytic| <= 1e-6   (relative)
  C3: |W_net_stroke_sum - W_net_loop_area| / |W_net_analytic| <= 1e-6
      (two independent numerical paths -- per-stroke np.trapezoid sum vs a single
       closed-loop shoelace/trapz pass over the concatenated P-V trace --
       must agree; this is the "P-V area = net work" cross-check)
  C4 (boundary/negative control): degenerate cycle Th=Tc must give
      eta = 0 and W_net = 0 to abs tolerance 1e-9 (a Carnot engine across
      zero temperature difference extracts no work -- this is the negative
      control paired with the positive C1/C2/C3 claims)
ALL_PASS iff C1 and C2 and C3 and C4 all hold. No partial credit language.

TOOLS
-----
numpy is the load-bearing computation tool (classical ideal-gas P-V
integration; no Hilbert-space/operator content exists in this problem).
qutip was considered and is NOT used here: a classical ideal gas has no
quantum-operator content, so invoking qutip would be decorative, not
load-bearing. That absence is itself the honest tool-fit finding for this
engine (see tool_manifest below).

Interpreter: /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3
"""

import json
import os
import numpy as np

# =====================================================================
# TOOL MANIFEST (lean, task-scoped -- not the full geometry-stack template;
# this is an explicitly out-of-axis competence-check probe)
# =====================================================================
TOOL_MANIFEST = {
    "numpy": {
        "tried": True,
        "used": True,
        "reason": "classical ideal-gas P-V thermodynamics: numeric trapezoid "
                   "integration of P(V) along each stroke, closed-loop area "
                   "cross-check, and root-level arithmetic. This is the "
                   "correct primary tool, not a fallback.",
    },
    "qutip": {
        "tried": True,
        "used": False,
        "reason": "no Hilbert space / operator content in a classical ideal "
                   "gas cycle; importing qutip here would be decorative, not "
                   "load-bearing, so it is honestly left unused.",
    },
}
TOOL_INTEGRATION_DEPTH = {
    "numpy": "load_bearing",
    "qutip": None,
}

R = 8.314462618  # J / (mol K), CODATA exact-derived ideal gas constant
N_MOL = 1.0
GAMMA = 5.0 / 3.0  # monatomic ideal gas, Cv = 3/2 R
CV = 1.5 * R * N_MOL

REL_TOL = 1e-6
DEGENERATE_ABS_TOL = 1e-9

GRID_N = 200_000  # trapezoid points per stroke


def isothermal_work(T, V_a, V_b, n=GRID_N):
    """W = integral_{V_a}^{V_b} (N_MOL R T / V) dV, via fine trapezoid grid."""
    V = np.linspace(V_a, V_b, n)
    P = N_MOL * R * T / V
    return float(np.trapezoid(P, V)), V, P


def adiabatic_work(V_start, T_start, V_end, n=GRID_N):
    """P(V) = P_start * (V_start/V)^gamma along the adiabat starting at
    (V_start, T_start). Returns integral of P dV from V_start to V_end."""
    P_start = N_MOL * R * T_start / V_start
    V = np.linspace(V_start, V_end, n)
    P = P_start * (V_start / V) ** GAMMA
    return float(np.trapezoid(P, V)), V, P


def run_carnot_cycle(Th, Tc, V1, expansion_ratio):
    """Run one full Carnot cycle, return all numerics needed for the checks."""
    V2 = V1 * expansion_ratio
    if Th == Tc:
        # Degenerate boundary case: adiabats collapse (no temperature drop to
        # traverse), so the whole "cycle" is a single isothermal round trip
        # V1->V2->V1 at constant T -- net work over a closed isothermal loop
        # covering the same path forward and back is exactly zero.
        V3, V4 = V2, V1
        W12, VV12, PP12 = isothermal_work(Th, V1, V2)
        W23, VV23, PP23 = 0.0, np.array([V2]), np.array([N_MOL * R * Th / V2])
        W34, VV34, PP34 = isothermal_work(Tc, V3, V4)
        W41, VV41, PP41 = 0.0, np.array([V1]), np.array([N_MOL * R * Tc / V1])
        Qh = W12
    else:
        ratio_pow = (Th / Tc) ** (1.0 / (GAMMA - 1.0))
        V3 = V2 * ratio_pow
        V4 = V1 * ratio_pow

        W12, VV12, PP12 = isothermal_work(Th, V1, V2)          # 1->2 isothermal @ Th
        W23, VV23, PP23 = adiabatic_work(V2, Th, V3)             # 2->3 adiabatic expansion
        W34, VV34, PP34 = isothermal_work(Tc, V3, V4)             # 3->4 isothermal @ Tc
        W41, VV41, PP41 = adiabatic_work(V4, Tc, V1)             # 4->1 adiabatic compression
        Qh = W12

    W_net_stroke_sum = W12 + W23 + W34 + W41

    # Independent cross-check: single pass around the closed P-V loop.
    V_loop = np.concatenate([VV12, VV23[1:], VV34[1:], VV41[1:], VV12[:1]])
    P_loop = np.concatenate([PP12, PP23[1:], PP34[1:], PP41[1:], PP12[:1]])
    W_net_loop_area = float(np.trapezoid(P_loop, V_loop))

    W_net_analytic = N_MOL * R * (Th - Tc) * np.log(expansion_ratio) if Th != Tc else 0.0
    eta_analytic = 1.0 - Tc / Th
    eta_numeric = W_net_stroke_sum / Qh if Qh != 0 else 0.0

    return {
        "Th_K": Th, "Tc_K": Tc,
        "V1_m3": V1, "V2_m3": V2, "V3_m3": V3, "V4_m3": V4,
        "expansion_ratio": expansion_ratio,
        "Qh_J": Qh, "Qc_J": -W34,
        "W12_J": W12, "W23_J": W23, "W34_J": W34, "W41_J": W41,
        "W_net_stroke_sum_J": W_net_stroke_sum,
        "W_net_loop_area_J": W_net_loop_area,
        "W_net_analytic_J": W_net_analytic,
        "eta_numeric": eta_numeric,
        "eta_analytic": eta_analytic,
    }


def run_positive_tests():
    """C1, C2, C3: main Carnot cycle, Th=400K, Tc=300K, r=V2/V1=2.5."""
    Th, Tc, V1, r = 400.0, 300.0, 1.0e-3, 2.5
    cyc = run_carnot_cycle(Th, Tc, V1, r)

    eta_rel_err = abs(cyc["eta_numeric"] - cyc["eta_analytic"]) / cyc["eta_analytic"]
    c1_pass = eta_rel_err <= REL_TOL

    wnet_rel_err = abs(cyc["W_net_stroke_sum_J"] - cyc["W_net_analytic_J"]) / abs(cyc["W_net_analytic_J"])
    c2_pass = wnet_rel_err <= REL_TOL

    loop_vs_stroke_rel_err = abs(cyc["W_net_stroke_sum_J"] - cyc["W_net_loop_area_J"]) / abs(cyc["W_net_analytic_J"])
    c3_pass = loop_vs_stroke_rel_err <= REL_TOL

    return {
        "cycle": cyc,
        "C1_eta_matches_1_minus_Tc_over_Th": {
            "pass": bool(c1_pass), "rel_err": eta_rel_err, "tol": REL_TOL,
            "eta_numeric": cyc["eta_numeric"], "eta_analytic": cyc["eta_analytic"],
        },
        "C2_Wnet_matches_analytic_nR_dT_lnr": {
            "pass": bool(c2_pass), "rel_err": wnet_rel_err, "tol": REL_TOL,
            "W_net_numeric_J": cyc["W_net_stroke_sum_J"], "W_net_analytic_J": cyc["W_net_analytic_J"],
        },
        "C3_stroke_sum_matches_loop_area": {
            "pass": bool(c3_pass), "rel_err": loop_vs_stroke_rel_err, "tol": REL_TOL,
            "W_net_stroke_sum_J": cyc["W_net_stroke_sum_J"], "W_net_loop_area_J": cyc["W_net_loop_area_J"],
        },
    }


def run_negative_tests():
    """C4: degenerate Th=Tc control must extract exactly zero work."""
    Th = Tc = 350.0
    cyc = run_carnot_cycle(Th, Tc, 1.0e-3, 2.5)
    eta_ok = abs(cyc["eta_numeric"] - 0.0) <= DEGENERATE_ABS_TOL
    wnet_ok = abs(cyc["W_net_stroke_sum_J"] - 0.0) <= DEGENERATE_ABS_TOL
    c4_pass = eta_ok and wnet_ok
    return {
        "C4_degenerate_Th_eq_Tc_zero_work_control": {
            "pass": bool(c4_pass),
            "Th_K": Th, "Tc_K": Tc,
            "eta_numeric": cyc["eta_numeric"],
            "W_net_J": cyc["W_net_stroke_sum_J"],
            "abs_tol": DEGENERATE_ABS_TOL,
            "note": "Carnot engine across zero temperature difference must "
                    "admit zero net work -- this is the negative control "
                    "paired against the positive eta=1-Tc/Th claim.",
        }
    }


def run_boundary_tests():
    """Sweep the expansion ratio r to confirm eta is r-independent (as the
    closed-form derivation requires: eta cancels V1,V2 entirely) -- this is
    the boundary probe checking where the closure condition could break
    resolution (it does not, at any tested r)."""
    Th, Tc = 400.0, 300.0
    etas = []
    for r in [1.05, 1.5, 2.5, 5.0, 10.0]:
        cyc = run_carnot_cycle(Th, Tc, 1.0e-3, r)
        etas.append({"r": r, "eta_numeric": cyc["eta_numeric"]})
    eta_analytic = 1.0 - Tc / Th
    max_dev = max(abs(e["eta_numeric"] - eta_analytic) for e in etas)
    return {
        "r_sweep_eta_invariance": {
            "etas_by_expansion_ratio": etas,
            "eta_analytic": eta_analytic,
            "max_abs_deviation": max_dev,
            "pass": bool(max_dev <= REL_TOL * eta_analytic),
            "note": "eta must be independent of the isothermal expansion "
                    "ratio r=V2/V1 by construction; this sweep is the "
                    "boundary check that this invariance actually holds "
                    "numerically, not just algebraically.",
        }
    }


if __name__ == "__main__":
    positive = run_positive_tests()
    negative = run_negative_tests()
    boundary = run_boundary_tests()

    all_checks = [
        positive["C1_eta_matches_1_minus_Tc_over_Th"]["pass"],
        positive["C2_Wnet_matches_analytic_nR_dT_lnr"]["pass"],
        positive["C3_stroke_sum_matches_loop_area"]["pass"],
        negative["C4_degenerate_Th_eq_Tc_zero_work_control"]["pass"],
        boundary["r_sweep_eta_invariance"]["pass"],
    ]
    all_pass = bool(all(all_checks))

    results = {
        "name": "carnot_engine",
        "engine": "Carnot cycle, monatomic ideal gas working substance",
        "probe_family": "M_numeric_PV_trapezoid_integration",
        "constraint_set": "C_reversible_quasi_static_ideal_gas_cycle",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "classification": "classical_baseline",
        "surviving_alternatives": [],
        "claim_ceiling": "engine_competence_check_only",
        "promotion_allowed": False,
        "next_lego_target": "none",
        "promotion_condition": "not applicable -- this is a tool/engine "
                                "competence check, not a Codex-Ratchet "
                                "lego/bridge/axis admission attempt",
        "out_of_scope": [
            "no lego promotion from this result",
            "no bridge, axis, engine-estate, emergence, or nonclassical claim",
        ],
        "all_pass": all_pass,
        "criteria_checked": ["C1", "C2", "C3", "C4", "r_sweep_boundary"],
        "engine_machinery_used": {
            "qutip_mesolve": False,
            "qutip_unitary": False,
            "qutip_counts": False,
            "numpy_trapezoid_integration": True,
            "note": "purely classical ideal-gas P-V thermodynamics; no "
                    "quantum engine machinery is applicable or used.",
        },
    }

    out_dir = os.path.join(os.path.dirname(__file__), "results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "carnot_engine.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)

    print(f"Results written to {out_path}")
    print(f"eta_numeric={positive['cycle']['eta_numeric']:.10f}  "
          f"eta_analytic(1-Tc/Th)={positive['cycle']['eta_analytic']:.10f}")
    print(f"W_net_stroke_sum={positive['cycle']['W_net_stroke_sum_J']:.6f} J  "
          f"W_net_loop_area={positive['cycle']['W_net_loop_area_J']:.6f} J  "
          f"W_net_analytic={positive['cycle']['W_net_analytic_J']:.6f} J")
    print(f"C4 degenerate control: eta={negative['C4_degenerate_Th_eq_Tc_zero_work_control']['eta_numeric']:.3e}  "
          f"W_net={negative['C4_degenerate_Th_eq_Tc_zero_work_control']['W_net_J']:.3e} J")
    print(f"ALL_PASS = {all_pass}")
    if not all_pass:
        for name, val in [("C1", positive["C1_eta_matches_1_minus_Tc_over_Th"]),
                           ("C2", positive["C2_Wnet_matches_analytic_nR_dT_lnr"]),
                           ("C3", positive["C3_stroke_sum_matches_loop_area"]),
                           ("C4", negative["C4_degenerate_Th_eq_Tc_zero_work_control"]),
                           ("boundary", boundary["r_sweep_eta_invariance"])]:
            print(f"  {name}: pass={val['pass']}")
