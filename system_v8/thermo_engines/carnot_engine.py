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
      (two independent numerical paths -- per-stroke jnp.trapezoid sum vs a
       single closed-loop shoelace/trapz pass over the concatenated P-V trace --
       must agree; this is the "P-V area = net work" cross-check)
  C4 (boundary/negative control): degenerate cycle Th=Tc must give
      eta = 0 and W_net = 0 to abs tolerance 1e-9 (a Carnot engine across
      zero temperature difference extracts no work -- this is the negative
      control paired with the positive C1/C2/C3 claims)
  C5 (cross-engine): the independent jax leg (jnp trapezoid + diffrax
      thermal-contact Lindblad) and julia leg (Julia trapezoid + QuantumOptics
      master-equation thermal contact) must each recompute the headline
      scalars, agreeing |eta_jax - eta_julia| <= 1e-6 and
      |W_jax - W_julia| / |W_analytic| <= 1e-6.
ALL_PASS iff C1 and C2 and C3 and C4 and C5 all hold. No partial credit language.

TOOLS
-----
jax.numpy (x64) is the base compute substrate (classical ideal-gas P-V
integration; numpy is fully removed -- jax is the base, per the three-engine
contract). Two independent engine legs recompute the headline scalars:
carnot_engine_jax.py (jnp trapezoid; diffrax Dopri5 Lindblad thermal-contact
cross-check, the pattern proven in sim_engines/stress/
diffrax_lindblad_cycle_probe.py) and carnot_engine_julia.jl (Julia trapezoid;
QuantumOptics timeevolution.master thermal-contact cross-check). qutip was
considered for the MAIN cycle and is NOT used: a classical ideal gas has no
Hilbert-space/operator content, so invoking it in the cycle itself would be
decorative, not load-bearing. The thermal-contact Lindblad legs live where
quantum machinery genuinely applies -- the bath-contact premise -- not in the
classical cycle arithmetic.

Interpreter: /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3
"""

import json
import math
import os
import subprocess
from pathlib import Path

os.environ.setdefault("JAX_PLATFORMS", "cpu")
import jax

jax.config.update("jax_enable_x64", True)
import jax.numpy as jnp

# =====================================================================
# TOOL MANIFEST (lean, task-scoped -- not the full geometry-stack template;
# this is an explicitly out-of-axis competence-check probe)
# =====================================================================
TOOL_MANIFEST = {
    "jax": {
        "tried": True,
        "used": True,
        "reason": "BASE ENGINE: classical ideal-gas P-V thermodynamics on "
                   "jax.numpy x64 -- numeric trapezoid integration of P(V) "
                   "along each stroke, closed-loop area cross-check, and "
                   "root-level arithmetic. The independent jax leg "
                   "(carnot_engine_jax.py) recomputes the headline scalars "
                   "and adds a diffrax Lindblad thermal-contact cross-check; "
                   "the three_engine_seal re-runs that leg to re-derive.",
    },
    "julia": {
        "tried": True,
        "used": True,
        "reason": "Authoritative independent leg (carnot_engine_julia.jl): "
                   "Julia trapezoid recompute of eta/W_net plus a "
                   "QuantumOptics timeevolution.master detailed-balance "
                   "relaxation to the Gibbs populations at Th and Tc "
                   "(thermal-contact premise). Reference on disagreement.",
    },
    "diffrax": {
        "tried": True,
        "used": True,
        "reason": "In the jax leg only: ODETerm+Dopri5+PIDController "
                   "detailed-balance Lindblad relaxation, cross-checked "
                   "against the closed-form Gibbs approach (pattern proven "
                   "in sim_engines/stress/diffrax_lindblad_cycle_probe.py). "
                   "Supportive: grounds the isothermal-stroke premise; the "
                   "cycle itself is quasi-static and needs no time solver.",
    },
    "qutip": {
        "tried": True,
        "used": False,
        "reason": "no Hilbert space / operator content in the classical ideal "
                   "gas cycle itself; importing qutip here would be decorative, "
                   "not load-bearing, so it is honestly left unused. The "
                   "quantum thermal-contact cross-checks run in the engine "
                   "legs (dynamiqs-family diffrax / QuantumOptics) instead.",
    },
}
TOOL_INTEGRATION_DEPTH = {
    "jax": "load_bearing",
    "julia": "load_bearing",
    "diffrax": "supportive",
    "qutip": None,
}

R = 8.314462618  # J / (mol K), CODATA exact-derived ideal gas constant
N_MOL = 1.0
GAMMA = 5.0 / 3.0  # monatomic ideal gas, Cv = 3/2 R
CV = 1.5 * R * N_MOL

REL_TOL = 1e-6
DEGENERATE_ABS_TOL = 1e-9

GRID_N = 200_000  # trapezoid points per stroke

PY_ENGINE = "/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3"
JULIA_PROJECT = "/Users/joshuaeisenhart/Codex-Ratchet/system_v5/julia_carrier"


def isothermal_work(T, V_a, V_b, n=GRID_N):
    """W = integral_{V_a}^{V_b} (N_MOL R T / V) dV, via fine trapezoid grid."""
    V = jnp.linspace(V_a, V_b, n)
    P = N_MOL * R * T / V
    return float(jnp.trapezoid(P, V)), V, P


def adiabatic_work(V_start, T_start, V_end, n=GRID_N):
    """P(V) = P_start * (V_start/V)^gamma along the adiabat starting at
    (V_start, T_start). Returns integral of P dV from V_start to V_end."""
    P_start = N_MOL * R * T_start / V_start
    V = jnp.linspace(V_start, V_end, n)
    P = P_start * (V_start / V) ** GAMMA
    return float(jnp.trapezoid(P, V)), V, P


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
        W23, VV23, PP23 = 0.0, jnp.array([V2]), jnp.array([N_MOL * R * Th / V2])
        W34, VV34, PP34 = isothermal_work(Tc, V3, V4)
        W41, VV41, PP41 = 0.0, jnp.array([V1]), jnp.array([N_MOL * R * Tc / V1])
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
    V_loop = jnp.concatenate([VV12, VV23[1:], VV34[1:], VV41[1:], VV12[:1]])
    P_loop = jnp.concatenate([PP12, PP23[1:], PP34[1:], PP41[1:], PP12[:1]])
    W_net_loop_area = float(jnp.trapezoid(P_loop, V_loop))

    W_net_analytic = N_MOL * R * (Th - Tc) * math.log(expansion_ratio) if Th != Tc else 0.0
    eta_analytic = 1.0 - Tc / Th
    eta_numeric = W_net_stroke_sum / Qh if Qh != 0 else 0.0

    return {
        "Th_K": Th, "Tc_K": Tc,
        "V1_m3": V1, "V2_m3": V2, "V3_m3": float(V3), "V4_m3": float(V4),
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


def _run_leg(cmd):
    """Run one engine leg as an independent subprocess (no echo -- each
    recomputes from scratch) and parse its single JSON line."""
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=600,
                              cwd=str(Path(__file__).resolve().parent))
    except Exception as exc:  # noqa: BLE001
        return {"ran": False, "reason": f"dispatch failed: {exc}"}
    if proc.returncode != 0:
        return {"ran": False, "reason": f"exit {proc.returncode}: {proc.stderr.strip()[-200:]}"}
    lines = [ln for ln in proc.stdout.splitlines() if ln.strip().startswith("{")]
    if not lines:
        return {"ran": False, "reason": "no JSON on stdout"}
    data = json.loads(lines[-1])
    data["ran"] = True
    return data


def run_engine_legs():
    """Julia (QuantumOptics, authoritative) + JAX (jnp+diffrax), each
    recomputing the headline scalars INDEPENDENTLY, sequentially (julia
    startup is expensive; never parallel julia)."""
    here = Path(__file__).resolve().parent
    julia = _run_leg(["julia", f"--project={JULIA_PROJECT}",
                      str(here / "carnot_engine_julia.jl")])
    jax_leg = _run_leg([PY_ENGINE, str(here / "carnot_engine_jax.py")])
    return {"julia": julia, "jax": jax_leg}


if __name__ == "__main__":
    positive = run_positive_tests()
    negative = run_negative_tests()
    boundary = run_boundary_tests()

    # C5: independent engine legs (julia authoritative, jax re-derivable).
    legs = run_engine_legs()
    for eng in ("julia", "jax"):
        if not legs[eng].get("ran"):
            raise SystemExit(f"{eng} leg did not run: {legs[eng].get('reason')} "
                             f"-- refusing to write a receipt without both engines.")
    eta_jax = float(legs["jax"]["eta_numeric"])
    eta_julia = float(legs["julia"]["eta_numeric"])
    w_jax = float(legs["jax"]["W_net_J"])
    w_julia = float(legs["julia"]["W_net_J"])
    w_analytic = positive["cycle"]["W_net_analytic_J"]
    eta_div = abs(eta_jax - eta_julia)
    w_rel_div = abs(w_jax - w_julia) / abs(w_analytic)
    base_vs_jax_eta = abs(positive["cycle"]["eta_numeric"] - eta_jax)
    base_vs_jax_w = abs(positive["cycle"]["W_net_stroke_sum_J"] - w_jax)
    c5_pass = (eta_div <= REL_TOL and w_rel_div <= REL_TOL
               and base_vs_jax_eta <= REL_TOL and base_vs_jax_w / abs(w_analytic) <= REL_TOL)
    engines_section = {
        "C5_cross_engine_agreement": {
            "pass": bool(c5_pass),
            "eta_jax": eta_jax, "eta_julia": eta_julia,
            "eta_abs_divergence": eta_div,
            "W_net_jax_J": w_jax, "W_net_julia_J": w_julia,
            "W_net_rel_divergence": w_rel_div,
            "base_vs_jax_eta_abs": base_vs_jax_eta,
            "base_vs_jax_W_abs_J": base_vs_jax_w,
            "tol": REL_TOL,
            "note": "julia (QuantumOptics thermal contact + Julia trapezoid) "
                    "and jax (diffrax thermal contact + jnp trapezoid) each "
                    "recompute eta and W_net independently; values must be "
                    "consistent with each other and with the base jnp cycle. "
                    "Julia is the reference on disagreement.",
        },
        "thermal_contact_cross_check": {
            "jax_gibbs_closed_form_div": [legs["jax"].get("gibbs_closed_form_div_Th"),
                                          legs["jax"].get("gibbs_closed_form_div_Tc")],
            "julia_gibbs_closed_form_div": [legs["julia"].get("gibbs_closed_form_div_Th"),
                                            legs["julia"].get("gibbs_closed_form_div_Tc")],
            "jax_thermal_contact_ok": legs["jax"].get("thermal_contact_ok"),
            "julia_thermal_contact_ok": legs["julia"].get("thermal_contact_ok"),
            "note": "detailed-balance Lindblad relaxation to the Gibbs "
                    "populations at Th and Tc, per leg -- the isothermal-stroke "
                    "bath-contact premise run as actual dynamics, consistent "
                    "with the closed form in both engines.",
        },
    }

    all_checks = [
        positive["C1_eta_matches_1_minus_Tc_over_Th"]["pass"],
        positive["C2_Wnet_matches_analytic_nR_dT_lnr"]["pass"],
        positive["C3_stroke_sum_matches_loop_area"]["pass"],
        negative["C4_degenerate_Th_eq_Tc_zero_work_control"]["pass"],
        boundary["r_sweep_eta_invariance"]["pass"],
        engines_section["C5_cross_engine_agreement"]["pass"],
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
        "engines": engines_section,
        "engine_values": {
            "julia_eta_carnot": eta_julia,
            "jax_eta_carnot": eta_jax,
            "julia_W_net_J": w_julia,
            "jax_W_net_J": w_jax,
            "jax_base_eta_carnot": positive["cycle"]["eta_numeric"],
            "jax_base_W_net_J": positive["cycle"]["W_net_stroke_sum_J"],
        },
        "max_cross_engine_divergence": max(eta_div, w_rel_div),
        "engine_contract": {
            "mode": "two_leg_full_recompute",
            "semantic_owner": "julia",
            "reference": "julia:QuantumOptics+trapezoid",
            "engines_agree_to": max(eta_div, w_rel_div),
            "n_authoritative_engines": 2,
        },
        "three_engine_legs": legs,
        "engines_ran": {"jax": True, "julia": True, "qutip": False},
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
        "criteria_checked": ["C1", "C2", "C3", "C4", "r_sweep_boundary",
                              "C5_cross_engine"],
        "engine_machinery_used": {
            "qutip_mesolve": False,
            "qutip_unitary": False,
            "qutip_counts": False,
            "jnp_trapezoid_integration": True,
            "diffrax_lindblad_thermal_contact": True,
            "quantumoptics_master_equation_thermal_contact": True,
            "note": "the cycle itself is classical ideal-gas P-V "
                    "thermodynamics on jax.numpy x64 (quasi-static -- no time "
                    "solver needed); the bath-contact premise is grounded by "
                    "Lindblad relaxation in both engine legs (diffrax / "
                    "QuantumOptics), where quantum machinery genuinely applies.",
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
    print(f"C5 cross-engine: eta_julia={eta_julia:.10f} eta_jax={eta_jax:.10f} "
          f"(div {eta_div:.3e})  W_julia={w_julia:.6f} W_jax={w_jax:.6f} "
          f"(rel div {w_rel_div:.3e})")
    print(f"ALL_PASS = {all_pass}")
    if not all_pass:
        for name, val in [("C1", positive["C1_eta_matches_1_minus_Tc_over_Th"]),
                           ("C2", positive["C2_Wnet_matches_analytic_nR_dT_lnr"]),
                           ("C3", positive["C3_stroke_sum_matches_loop_area"]),
                           ("C4", negative["C4_degenerate_Th_eq_Tc_zero_work_control"]),
                           ("boundary", boundary["r_sweep_eta_invariance"]),
                           ("C5", engines_section["C5_cross_engine_agreement"])]:
            print(f"  {name}: pass={val['pass']}")
        raise SystemExit(1)
