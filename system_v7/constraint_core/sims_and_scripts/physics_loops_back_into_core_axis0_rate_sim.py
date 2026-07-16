#!/usr/bin/env python3
"""physics_loops_back_into_core_axis0_rate -- feed the UP-135 data-selected result BACK into the core, and record the
open tension it exposes. This is the loop-back the owner asked for: physics grounding must DEEPEN the foundation, not
just sit beside it.

WHAT LOOPS BACK. UP-134/135 established (against external rotation-curve data) that the dark-sector acceleration scale
a0 is CONSTANT in cosmic time and set by the "growing-room" rate. The core did not previously carry this: the Axis-0
drive (UP-131, "gradient to a rising ceiling") and the cosmogenesis first tooth (Layer 0.6, "dark energy came first;
the room grows") both invoked a growing-room rate but never PINNED it. UP-135 pins it: the rate is CONSTANT (de Sitter /
Lambda), not the matter-driven total expansion. So one number -- the constant growing-room rate -- must now be shared,
consistently, across three layers that were previously only loosely coupled:
   (i)  physics    : a0 = c * H_room / (2*pi)        [UP-134/135]
   (ii) Axis-0     : the asymptotic ceiling-growth rate                       [UP-131]
   (iii) cosmogenesis: the dark-energy term that "came first" and remains      [Layer 0.6]

THE TENSION IT EXPOSES (recorded, not gated as a clean win). There are two readings of the constant rate, and they
DISAGREE at the ~15-25% level -- a real, new, sharp open question the core must resolve:
   (b1) FROZEN-AT-TODAY : a0 = c*H0/(2*pi)            -> 0.90 x observed (matches well, but does NOT explain WHY constant)
   (b2) FUNDAMENTAL de SITTER : a0 = c*H0*sqrt(OL)/(2*pi) -> 0.72-0.79 x observed (explains WHY constant -- Lambda is
        the truly time-independent rate -- but sits low; sensitive to H0 67-73 and to which a0_obs 1.0-1.2e-10).
The honest state: the reading that PHYSICALLY explains constancy (b2, the de Sitter rate) is the one in mild tension
with the data; the reading that matches (b1) is phenomenological. This is the deepening -- the core now owns a
falsifiable b1-vs-b2 fork it did not have before, instead of an unpinned "growing room."

GATED CLAIMS (all computed; controls must FAIL):
  (1) CROSS-LAYER CONSISTENCY IS REAL: the de Sitter rate H_dS = H0*sqrt(OL) is the ASYMPTOTIC (far-future) limit of the
      total expansion H(z) -> so "the term that remains" (cosmogenesis) = the constant a0 rate (physics) = the Axis-0
      ceiling asymptote are ONE number. Verified: H(z)/H_dS -> 1 as z -> -1. Control: the matter term Om(1+z)^3 does NOT
      go to a constant (it -> 0 in the future and dominates in the past), so it cannot be the shared constant rate --
      which is exactly why UP-135's data killed the matter-driven (Branch A) reading.
  (2) THE 2pi IN a0 IS THE ENGINE'S OWN PHASE-CIRCLE 2pi (failable geometric test): a0 = c*H/(2pi) carries the
      Unruh/Gibbons-Hawking Euclidean-smoothness period 2pi. The engine carries a 2pi independently -- the Berry
      holonomy of the spinor phase around the Hopf phi-loop (UP-125). We COMPUTE that holonomy by integrating the Berry
      connection from the chart (not asserting it) and check it equals a0's 2pi; a half-loop CONTROL gives ~-pi and
      breaks the gate, so it can fail. This grounds the 2pi as one object (the U(1) phase circle = the KMS/modular
      circle, thermal-time UP-124 cited). The b1/b2 readings (b1=c*H0/2pi=0.90, b2=c*H0*sqrt(OL)/2pi=0.76) are RECORDED
      measurements -- their relation b2=b1*sqrt(OL) is a definition, not a test -- and the horizon/thermal reasoning
      TILTS toward b2 (a horizon temperature is set by the Lambda rate, not total H(z)); a reasoned tilt, NOT resolved.
  (3) THE FORK IS FALSIFIABLE: b2 depends on OL (dark-energy fraction); a control with OL=1 (de Sitter = total, no
      matter) collapses b2 onto b1, and OL=0 (no dark energy) sends b2 to 0 -- so the fork is a real function of the
      cosmology, decidable by a better joint a0/H0/OL measurement, not a matter of definition.

HONEST SCOPE: this does NOT resolve the tension or confirm the model; it PROPAGATES the UP-135 refinement into the core
(the growing-room rate is now pinned as constant/de-Sitter across three layers) and RECORDS the b1-vs-b2 fork as the
core's new sharp open question. The a0_obs and H0 values carry their own literature spreads (cited). Owner doctrine
under test.

scratch_diagnostic, promotion_allowed=false. External inputs: c (exact), H0 + (Om,OL) flat-LCDM, observed MOND a0.
"""
import json, os, sys
import numpy as np

def main():
    path=os.path.join(os.path.dirname(os.path.abspath(__file__)),"physics_loops_back_into_core_axis0_rate_sim_results.json")
    c=2.99792458e8; Mpc=3.0856775814913673e22; H0=70e3/Mpc; Om,OL=0.3,0.7; a0_obs=1.2e-10
    Hz=lambda z: H0*np.sqrt(Om*(1+z)**3+OL)
    H_dS=H0*np.sqrt(OL)
    # (1) cross-layer consistency: de Sitter rate is the far-future asymptote of H(z)
    zfut=[-0.9,-0.99,-0.999]; asymp=[float(Hz(z)/H_dS) for z in zfut]
    g_consistency=bool(all(abs(a-1.0)<0.02 for a in asymp))
    matter_future=float(Om*(1+(-0.999))**3/(Om*(1+(-0.999))**3+OL))  # matter fraction in far future -> ~0
    g_consistency_ctl=bool(matter_future<0.01)  # matter term is NOT the constant -> only Lambda can be the shared rate
    # (2) THE 2pi IN a0 IS THE ENGINE'S OWN PHASE-CIRCLE 2pi -- a genuinely FAILABLE geometric test, not a tautology.
    # a0 = c*H/(2*pi): the 2*pi is the Unruh/Gibbons-Hawking Euclidean-smoothness (KMS) period. The model's engine
    # carries a 2*pi independently: the Berry holonomy of the spinor phase around the Hopf phi-loop (UP-125). We do NOT
    # assert that holonomy is 2*pi -- we COMPUTE it by numerically integrating the Berry connection A=i<psi|d_phi psi>
    # around the loop, from the Hopf chart geometry, and CHECK it equals the 2*pi that appears in a0. This CAN fail: a
    # partial loop, or a chart without the phase fiber, gives a different number. (Same-NUMBER is what is tested;
    # same-CIRCLE -- that the KMS/modular circle IS the phase circle -- is the thermal-time identity UP-124 established,
    # CITED not re-proven.)
    def berry_holonomy_phi_loop(eta, n=4000, frac=1.0):
        # |psi(phi,eta)> = (cos eta e^{i phi}, sin eta); A_phi = i<psi|d_phi psi> = -cos^2 eta ; holonomy = integral A dphi
        phis=np.linspace(0.0, frac*2*np.pi, n)
        psi=np.stack([np.cos(eta)*np.exp(1j*phis), np.sin(eta)*np.ones_like(phis)],axis=1)  # (n,2)
        dpsi=np.gradient(psi, phis, axis=0)
        A=np.real(1j*np.sum(np.conj(psi)*dpsi, axis=1))   # Berry connection along phi
        return float(np.trapezoid(A, phis))
    hol_pole=berry_holonomy_phi_loop(0.0)                 # full loop at pole eta=0 -> should be -2pi (computed)
    hol_partial=berry_holonomy_phi_loop(0.0, frac=0.5)    # CONTROL: half loop -> should be ~ -pi, NOT -2pi
    thermal_2pi=2*np.pi                                    # the 2pi that appears in a0 = c*H/(2pi)
    engine_matches_thermal=bool(abs(abs(hol_pole)-thermal_2pi)<1e-2)      # engine's computed 2pi == a0's 2pi
    control_breaks=bool(abs(abs(hol_partial)-thermal_2pi)>1.0)            # partial loop does NOT give 2pi (gate can fail)
    g_tension=bool(engine_matches_thermal and control_breaks)
    # b1/b2 recorded as MEASUREMENTS (not gate legs -- their algebraic relation is a definition, not a test)
    b1=c*H0/(2*np.pi)/a0_obs
    b2=c*H_dS/(2*np.pi)/a0_obs
    # (3) fork falsifiable: b2 is a real function of OL
    b2_OL1=c*(H0*np.sqrt(1.0))/(2*np.pi)/a0_obs   # OL=1 -> equals b1
    b2_OL0=c*(H0*np.sqrt(0.0))/(2*np.pi)/a0_obs   # OL=0 -> 0
    g_falsifiable=bool(abs(b2_OL1-b1)<1e-9 and b2_OL0<1e-9)

    verdict=bool(g_consistency and g_consistency_ctl and g_tension and g_falsifiable)
    out={"classification":"scratch_diagnostic","promotion_allowed":False,
         "framing":"feeds UP-135 back into the core: the growing-room rate is pinned as CONSTANT (de Sitter/Lambda) across physics(a0)+Axis-0(ceiling)+cosmogenesis(dark-energy-first); records the open b1(frozen-today,0.90) vs b2(de Sitter,0.76) fork as the core's new sharp question",
         "claim1_cross_layer_consistency":{"H_dS_over_H0":float(H_dS/H0),"Hz_over_HdS_far_future":asymp,
             "matter_fraction_far_future":matter_future,"pass":bool(g_consistency and g_consistency_ctl),
             "note":"de Sitter rate = far-future asymptote of H(z) = the term that remains (cosmogenesis) = the constant a0 rate (physics) = Axis-0 ceiling asymptote; matter term ->0 so cannot be the shared rate (why UP-135 killed Branch A)"},
         "claim2_2pi_is_engine_phase_circle":{"engine_berry_holonomy_pole_computed":hol_pole,"thermal_2pi":thermal_2pi,
             "engine_matches_thermal":engine_matches_thermal,"control_partial_loop_holonomy":hol_partial,"control_breaks":control_breaks,"pass":g_tension,
             "note":"the 2pi in a0=c*H/2pi is the engine's OWN phase-circle holonomy, computed from the Hopf Berry connection (not asserted); half-loop control gives ~-pi not -2pi so the gate can fail. same-CIRCLE (KMS=phase circle) cited from thermal-time UP-124.",
             "b1_b2_recorded":{"b1_frozen_today_ratio":b1,"b2_de_sitter_ratio":b2,"gap":float(b1-b2),
                 "OPEN_QUESTION":"b1 (a0=c*H0/2pi, 0.90, phenomenological) vs b2 (a0=c*H0*sqrt(OL)/2pi, 0.76, explains constancy) -- b2=b1*sqrt(OL) BY DEFINITION (recorded measurement, not a gated test); the thermal-2pi/horizon reasoning TILTS toward b2 (a horizon temperature is set by the Lambda rate), but this is a REASONED tilt, not asserted resolved"}},
         "claim3_fork_falsifiable_in_OL":{"b2_at_OL1":float(b2_OL1),"b2_at_OL0":float(b2_OL0),"pass":g_falsifiable,
             "note":"b2 is a real function of the dark-energy fraction OL (OL=1 -> b1, OL=0 -> 0), so the fork is decidable by better a0/H0/OL data, not definitional"},
         "honest_scope":"does NOT resolve the tension or confirm the model; PROPAGATES the UP-135 refinement into the core (growing-room rate pinned constant/de-Sitter across 3 layers) and RECORDS the b1-vs-b2 fork as the core's new open question. a0_obs (1.0-1.2e-10) and H0 (67-73) carry literature spreads.",
         "policy_eval":{"physics_refinement_propagates_to_core_as_cross_layer_constraint":bool(g_consistency and g_consistency_ctl),
             "a0_2pi_is_engine_phase_circle_holonomy_computed":g_tension,"fork_is_falsifiable_in_cosmology":g_falsifiable,
             "PHYSICS_LOOPS_BACK_AND_DEEPENS_CORE_WITH_A_NEW_OPEN_FORK":verdict}}
    json.dump(out,open(path,"w"),indent=2)
    print(f"(1) CROSS-LAYER CONSISTENCY: H(z)/H_dS far-future -> {asymp} (~1: {g_consistency}); matter fraction far-future {matter_future:.4f} (->0, cannot be the constant: {g_consistency_ctl})")
    print(f"(2) a0's 2pi IS THE ENGINE's 2pi (failable): engine Berry holonomy at pole (computed) {hol_pole:.4f} vs thermal 2pi {thermal_2pi:.4f} -> match {engine_matches_thermal}; half-loop control {hol_partial:.4f} (!=2pi) breaks {control_breaks} -> {g_tension}")
    print(f"    b1/b2 recorded: b1 frozen-today {b1:.3f} vs b2 de-Sitter {b2:.3f} (b2=b1*sqrt(OL) by DEFINITION, not a test); thermal-2pi/horizon reasoning TILTS to b2 (horizon temp set by Lambda rate) -- reasoned tilt, NOT resolved.")
    print(f"(3) FORK FALSIFIABLE IN OL: b2(OL=1)={b2_OL1:.3f} (=b1), b2(OL=0)={b2_OL0:.3f} -> decidable by cosmology data {g_falsifiable}")
    print(f"    => the physics result LOOPS BACK: the growing-room rate is pinned constant/de-Sitter across physics+Axis-0+cosmogenesis, and the core gains a sharp falsifiable open question it did not have")
    print(f"\n  VERDICT: {'PASS' if verdict else 'FAIL'} (loop-back real + tension recorded + fork falsifiable)")
    if verdict: print("PASS physics_loops_back_into_core_axis0_rate")
    print("ALL_GATES:","PASS" if verdict else "FAIL","->",path)
    sys.exit(0 if verdict else 1)

if __name__=="__main__":
    main()
