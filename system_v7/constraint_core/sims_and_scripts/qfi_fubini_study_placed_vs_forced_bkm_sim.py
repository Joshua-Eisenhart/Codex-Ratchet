#!/usr/bin/env python3
"""qfi_fubini_study_placed_vs_forced_bkm -- PURE MATH. 2026-07-10 (rebuilt after cross-family panel audit). PLACES the
Quantum Information Geometry from the attachments (Fubini-Study / Quantum Fisher Information) relative to the metric the
constraint core already uses: the BKM metric.

AUDIT HISTORY. A first version gated (1) BKM = rel-entropy Hessian, (2) SLD/QFI != BKM on noncommuting but = on
commuting, (3) SLD is "fidelity-curvature". A cross-family panel (Gemini-3.1-pro, Grok-4.5, Qwen-3.5, GLM-5.2) made
four correct catches: (a) "FORCED to be BKM" is smuggled -- this sim verifies BKM=Hessian(rel-entropy) but does NOT
re-gate that the PAWL is relative entropy (that is prior work, pawl_forced_by_DPI); (b) claim3 asserted SLD=fidelity-
curvature WITHOUT computing fidelity; (c) claim1 (BKM=Hessian(RE)) is a near-tautology since BKM is DEFINED as that
Hessian -- a self-consistency check, not a physics test; (d) the prose "QFI/FS coincides with BKM in the pure-state
limit" is FALSE (verified: near-pure SLD=1.0 vs BKM=4.6). This rebuild computes the fidelity Hessian to substantiate
(b), labels (c) honestly as a self-consistency identity, makes "forced" explicitly CONDITIONAL on the cited prior
result, and removes the false pure-state claim.

WHAT IS EARNED (the panel agreed the metric-family distinction is real and well-posed):
  (1) SELF-CONSISTENCY (labeled, not a physics test): the Morozova-Chentsov BKM kernel g_BKM equals the numerically-
      computed Hessian of the Umegaki relative entropy to ~1e-4. This is BKM's DEFINITION verified in code, stated so
      the chain is legible -- NOT claimed as a forced physics result.
  (2) SLD/QFI IS A DIFFERENT MONOTONE METRIC: on a NONCOMMUTING mixed direction g_SLD != g_BKM (differ ~0.076). HONEST
      SCOPE OF THE CONTROL (Qwen-3.5 round-2 [warn], correct and adopted): the coincidence on the commuting/classical
      submanifold (g_SLD = g_BKM = classical Fisher) is GUARANTEED by the Morozova-Chentsov theorem (every monotone
      metric reduces to classical Fisher on commuting states) -- so `agree_commuting` is a CONSISTENCY CHECK, NOT a
      control that could have flipped. The genuinely failable content is therefore the noncommuting DIFFERENCE (~0.076;
      it would be ~0 if SLD and BKM were the same metric) TOGETHER WITH claim (3): that the difference is specifically
      SLD=fidelity-curvature vs BKM=rel-entropy-curvature. Not "distinguishable only in the quantum sector as a flipping
      control" -- the commuting agreement is definitional; the quantum difference + the two-divergence identification is
      the earned distinction.
  (3) SLD/QFI IS THE FIDELITY (BURES) CURVATURE -- NOW COMPUTED, not asserted: the Hessian of the Bures distance^2
      d^2/dt^2 [2(1-sqrt(F(rho,rho+tA)))] equals g_SLD/2 (Bures metric = 1/4 SLD-Fisher; the dist^2 Hessian carries the
      convention factor). So SLD/QFI is the curvature of FIDELITY, while BKM is the curvature of RELATIVE ENTROPY --
      two different divergences, two different metrics.

PLACEMENT (conditional, honestly scoped). By PRIOR forced results (pawl_forced_by_DPI: the co-ratchet pawl is the
Umegaki relative entropy; surface_identity_is_BKM: the surface metric is its Hessian), the model's metric is BKM. This
sim does NOT re-derive that pawl; it shows the DOWNSTREAM fact: GIVEN a relative-entropy pawl, the metric is BKM (not
QFI), because QFI is the curvature of a DIFFERENT divergence (fidelity). So the attachments' Fubini-Study/QFI is placed
as the FIDELITY-family metric -- correct and useful (state estimation, quantum speed limit), coinciding with BKM only
on the classical submanifold -- and it would be the model's metric only if the drive were fidelity-based, which is not
what prior work forced.

HONEST SCOPE. Earns: SLD/QFI and BKM are DIFFERENT monotone metrics (computed: QFI=fidelity curvature, BKM=rel-entropy
curvature), coinciding only on the classical submanifold; so QIG is the fidelity-family alternative, and the model's
metric follows BKM CONDITIONAL on the prior-forced relative-entropy pawl. Does NOT re-derive the pawl (prior work, not
re-gated here), does NOT claim pure-state coincidence (false), does NOT claim QFI is useless, does NOT build a QIG
layer. scratch_diagnostic, promotion_allowed=false.
"""
import json, os, sys
import numpy as np
from scipy.linalg import logm, sqrtm

sy=np.array([[0,-1j],[1j,0]]); sz=np.array([[1,0],[0,-1]],complex)
def g_SLD(rho,A):
    w,V=np.linalg.eigh(rho); Ap=V.conj().T@A@V; s=0.0
    for i in range(len(w)):
        for j in range(len(w)):
            s+=2*abs(Ap[i,j])**2/(w[i]+w[j])
    return s.real
def g_BKM(rho,A):
    w,V=np.linalg.eigh(rho); Ap=V.conj().T@A@V; s=0.0
    for i in range(len(w)):
        for j in range(len(w)):
            c=1.0/w[i] if abs(w[i]-w[j])<1e-9 else (np.log(w[i])-np.log(w[j]))/(w[i]-w[j])
            s+=abs(Ap[i,j])**2*c
    return s.real
def relent(sig,rho): return np.trace(sig@(logm(sig)-logm(rho))).real
def bkm_hessian(rho,A,h=1e-4):
    f=lambda t: relent(rho+t*A,rho); return (f(h)-2*f(0)+f(-h))/h**2
def fidelity(rho,sig):
    s=sqrtm(rho); M=sqrtm(s@sig@s); return (np.trace(M).real)**2
def bures2_hessian(rho,A,h=1e-3):
    f=lambda t: 2*(1-np.sqrt(max(fidelity(rho,rho+t*A),0))); return (f(h)-2*f(0)+f(-h))/h**2

def main():
    path=os.path.join(os.path.dirname(os.path.abspath(__file__)),"qfi_fubini_study_placed_vs_forced_bkm_sim_results.json")
    rho=np.array([[0.7,0.1],[0.1,0.3]],complex); rho=(rho+rho.conj().T)/2; rho/=np.trace(rho)
    A=sy*0.5
    # (1) self-consistency (labeled): BKM = rel-entropy Hessian (BKM's definition, verified in code)
    bkm=g_BKM(rho,A); hess=bkm_hessian(rho,A)
    g1=bool(abs(bkm-hess)<1e-3)
    # (2) the real structural result: SLD != BKM on noncommuting, = on commuting (control flips)
    sld=g_SLD(rho,A); differ_noncommuting=abs(sld-bkm)
    rhoC=np.array([[0.7,0],[0,0.3]],complex); AC=sz*0.5
    sldC=g_SLD(rhoC,AC); bkmC=g_BKM(rhoC,AC); agree_commuting=abs(sldC-bkmC)  # reported CONSISTENCY CHECK (Morozova-Chentsov guaranteed), NOT a flipping control
    g2=bool(differ_noncommuting>1e-3)   # SLD != BKM on a noncommuting direction (~0.076; would be ~0 if they were the same metric)
    # (3) NOW COMPUTED and GATING: SLD/QFI is the fidelity (Bures) curvature, distinct from the rel-entropy (BKM) curvature
    bures_h=bures2_hessian(rho,A)
    sld_is_fidelity_curv=abs(bures_h - sld/2.0)
    g3=bool(sld_is_fidelity_curv<1e-2 and abs(sld-hess)>1e-3)   # SLD IS the Bures/fidelity curvature AND != the rel-entropy Hessian -> two divergences, two metrics
    # Qwen round-2 [warn] adopted: agree_commuting is Morozova-Chentsov-definitional, NOT a control, so it does NOT gate.
    # The failable content is the noncommuting DIFFERENCE (g2) TOGETHER WITH the computed fidelity-vs-rel-entropy curvature distinction (g3).
    verdict=bool(g2 and g3)
    out={"classification":"scratch_diagnostic","promotion_allowed":False,
         "framing":"PLACES the attachments' QIG (Fubini-Study/QFI) vs the model's BKM metric. QFI is COMPUTED to be the fidelity/Bures curvature; BKM is the relative-entropy curvature; they are different monotone metrics coinciding only on the classical submanifold. The model's metric follows BKM CONDITIONAL on the prior-forced relative-entropy pawl (not re-derived here). Rebuilt after a panel caught smuggled 'forced' language, an uncomputed fidelity claim, and a false pure-state-coincidence claim.",
         "claim1_bkm_is_relentropy_hessian_selfconsistency":{"g_BKM":bkm,"relentropy_Hessian":hess,"abs_diff":abs(bkm-hess),"pass":g1,
             "is_physics_test":False,
             "note":"SELF-CONSISTENCY identity (labeled): BKM is DEFINED as the Hessian of relative entropy; matching the Morozova-Chentsov kernel to the finite-difference Hessian verifies the code, it is NOT a forced physics result (panel catch)."},
         "claim2_qfi_is_different_metric":{"g_SLD_QFI":sld,"g_BKM":bkm,"differ_on_noncommuting":differ_noncommuting,
             "g_SLD_commuting":sldC,"g_BKM_commuting":bkmC,"agree_on_commuting":agree_commuting,"pass":g2,
             "note":"SLD/QFI != BKM on a noncommuting mixed direction (~0.076). The commuting-submanifold coincidence (both = classical Fisher) is GUARANTEED by the Morozova-Chentsov theorem -> agree_commuting is a CONSISTENCY CHECK, NOT a flipping control (Qwen-3.5 round-2 [warn], adopted). The earned distinction is the noncommuting difference TOGETHER WITH claim3 (SLD=fidelity curvature vs BKM=rel-entropy curvature), not the definitional commuting agreement."},
         "claim3_qfi_is_fidelity_curvature_computed":{"bures_dist2_Hessian":bures_h,"g_SLD_over_2":sld/2.0,
             "abs_diff":sld_is_fidelity_curv,"g_SLD_vs_relentropy_Hessian":abs(sld-hess),"pass":g3,
             "note":"NOW COMPUTED (panel catch: was asserted): the Hessian of the Bures distance^2 [2(1-sqrt F)] equals g_SLD/2, so SLD/QFI IS the fidelity curvature; and SLD != the relative-entropy Hessian. Two divergences (fidelity vs relative entropy) -> two metrics (QFI vs BKM)."},
         "placement":"Fubini-Study/QFI = the fidelity/Bures-family metric (COMPUTED here as the Bures dist^2 curvature). The model's metric is BKM CONDITIONAL on the prior-forced relative-entropy pawl (pawl_forced_by_DPI, surface_identity_is_BKM -- not re-gated here). QFI coincides with BKM only on the classical submanifold; it does NOT coincide at pure states (near-pure SLD=1.0 vs BKM=4.6). So QIG is placed as the fidelity-family alternative, not the model's foundation.",
         "audit_provenance":"cross-family panel over TWO rounds (Gemini-3.1-pro, Grok-4.5, Qwen-3.5, GLM-5.2). Round-1 flagged smuggled 'forced-BKM' language (now conditional on cited prior), an uncomputed fidelity-curvature assertion (now computed: Bures dist^2 Hessian = g_SLD/2), claim1 as a self-consistency identity (now labeled), and a FALSE pure-state coincidence claim (removed; near-pure SLD=1.0 != BKM=4.6). Round-2: Qwen-3.5 [warn] that agree_commuting is Morozova-Chentsov-GUARANTEED (every monotone metric = classical Fisher on commuting states), so it is a consistency check NOT a flipping control -- ADOPTED: the verdict no longer gates on agree_commuting; it gates on the noncommuting difference (g2) AND the computed fidelity-vs-rel-entropy curvature distinction (g3). An earlier report of this sim OVERSTATED round-2 as 'all three responding models agree claim2 is well-posed' -- corrected: Grok+GLM [ok], Qwen [warn] (adopted), Gemini 503'd. Fixed in the claims/measurement, not by relaxing gates.",
         "honest_scope":"Earns: QFI and BKM are different monotone metrics -- QFI=fidelity (Bures) curvature (computed), BKM=rel-entropy curvature -- differing on a noncommuting direction; they coincide on the commuting submanifold by the Morozova-Chentsov theorem (definitional, not a control). The model's metric follows BKM CONDITIONAL on the prior-forced relative-entropy pawl. Does NOT re-derive the pawl, does NOT claim pure-state coincidence, does NOT claim QFI useless, does NOT build a QIG layer.",
         "gating":"VERDICT gates on g2 AND g3: the noncommuting DIFFERENCE (SLD!=BKM, ~0.076; would vanish if they were the same metric) TOGETHER WITH the COMPUTED two-divergence identification (g3: SLD=Bures/fidelity curvature AND != rel-entropy Hessian). agree_commuting is REPORTED as a Morozova-Chentsov consistency check but does NOT gate (Qwen round-2 [warn], adopted). g1 (BKM=Hessian(rel-entropy)) is a definitional self-consistency identity and does NOT gate.",
         "supporting_identities_nongating":{"g1_bkm_is_relentropy_curvature":g1,"agree_commuting_morozova_chentsov_consistency":float(agree_commuting)},
         "policy_eval":{"qfi_differs_on_noncommuting_FAILABLE":g2,"qfi_is_fidelity_not_relentropy_curvature_FAILABLE":g3,"QIG_PLACED_AS_FIDELITY_FAMILY_CONDITIONAL_ON_PRIOR_PAWL":verdict}}
    json.dump(out,open(path,"w"),indent=2)
    print(f"(1) SELF-CONSISTENCY (labeled, not physics): g_BKM={bkm:.6f} = rel-entropy Hessian {hess:.6f} (|diff| {abs(bkm-hess):.2e}) -> {g1}")
    print(f"(2) QFI DIFFERS ON NONCOMMUTING (failable): g_SLD={sld:.6f} != g_BKM={bkm:.6f} (differ {differ_noncommuting:.4f}) -> {g2}")
    print(f"    [commuting agreement {sldC:.6f}={bkmC:.6f} (|diff| {agree_commuting:.2e}) is Morozova-Chentsov consistency, NOT a gating control -- Qwen round-2]")
    print(f"(3) QFI = FIDELITY CURVATURE, != REL-ENTROPY (failable, COMPUTED): Bures dist^2 Hessian={bures_h:.6f} = g_SLD/2={sld/2.0:.6f} (|diff| {sld_is_fidelity_curv:.2e}); SLD vs rel-entropy Hessian differ {abs(sld-hess):.4f} -> {g3}")
    print(f"    => QFI/Fubini-Study is the FIDELITY-family curvature; BKM is the RELATIVE-ENTROPY curvature. Model's metric follows BKM CONDITIONAL on the prior-forced rel-entropy pawl. QFI coincides only on the classical face (NOT at pure states).")
    print(f"\n  [gating: verdict = g2 AND g3 (noncommuting difference + computed two-divergence distinction); commuting agreement & g1 are non-gating consistency checks]")
    print(f"  VERDICT: {'PASS' if verdict else 'FAIL'} (QIG placed as fidelity-family metric via the failable SLD!=BKM distinction; model's metric = BKM conditional on prior-forced pawl)")
    if verdict: print("PASS qfi_fubini_study_placed_vs_forced_bkm")
    print("ALL_GATES:","PASS" if verdict else "FAIL","->",path)
    sys.exit(0 if verdict else 1)

if __name__=="__main__":
    main()
