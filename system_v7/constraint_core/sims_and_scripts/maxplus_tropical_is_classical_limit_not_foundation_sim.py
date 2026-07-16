#!/usr/bin/env python3
"""maxplus_tropical_is_classical_limit_not_foundation -- PURE MATH. 2026-07-10 (rebuilt after cross-family panel audit).
PLACES tropical / max-plus (idempotent) algebra relative to the nonclassical constraint core. New math arrived
(attachments: Max-Plus/tropical geometry, Tropical Attention, idempotent analysis / HJB as the "arithmetic of Bellman /
credit assignment"). Every structure must be PLACED by the constraints, never admitted by assertion.

AUDIT HISTORY. A first version gated THREE claims: (1) interference excludes max-plus, (2) max-plus is commutative so
fails N01, (3) max-plus is the T->0 limit of log-sum-exp. A cross-family LLM panel (Gemini-3.1-pro, Grok-4.5, Qwen-3.5,
GLM-5.2) UNANIMOUSLY rated gate (1) SOUND and failable, but flagged (2) as a TAUTOLOGY (max is commutative BY
DEFINITION, so the commutator is identically 0 -- unfailable) and (3) as textbook log-sum-exp calculus on hand-picked
values (the ~1e-15 gap is floating-point underflow, not a forcing). They also flagged the "Bellman / oracle / deductive
face" prose as SMUGGLED (the code has no paths, graphs, or Bellman equations -- only scalar arithmetic). They were right.
This rebuild keeps ONLY the one genuinely failable structural gate and demotes the rest to clearly-labelled context.

THE ONE EARNED, FAILABLE RESULT (interference vs monotonicity). Max-plus tropical-add is MONOTONE: max(a,b) >= a and
>= b, always. Quantum amplitude combination is NOT monotone: coherent destructive interference drives the combined
outcome BELOW the strongest single contribution, |a1+a2|^2 < max(|a1|^2,|a2|^2), with nonzero visibility across a phase
sweep. So a max-plus arithmetic STRUCTURALLY cannot reproduce the core's amplitude combination -- max-plus is excluded
from the nonclassical foundation. CONTROL (flips): a DECOHERED process (interference removed, incoherent sum) restores
monotonicity (combined = |a1|^2+|a2|^2 >= strongest) and has zero phase visibility -- so the exclusion is SPECIFICALLY
about coherent interference, not a generic property of two numbers. This control failing is what makes the gate real.

CONTEXT (NOT gated -- standard facts, stated so the placement is legible, not claimed as forced by this sim):
  - Max-plus tropical-add is commutative; the model's N01 (noncommutation) constraint independently disfavours any
    commutative foundation. (Textbook; not gated here to avoid a tautological rubber stamp -- the panel's catch.)
  - Max-plus = the T->0 limit of the classical log-sum-exp (standard idempotent-analysis fact). This is why max-plus
    is the natural arithmetic of the DEDUCTIVE / Bellman / single-optimal-path limit -- reached from the coherent core
    by decoherence then T->0. Stated as placement CONTEXT, not proven as a forced ratchet step by this sim.

HONEST SCOPE. Earns exactly ONE thing: coherent quantum interference violates max-plus monotonicity (with a decohered
control that flips), so max-plus cannot be the nonclassical foundation -- a clean NEGATIVE placement (negatives matter
as much as positives). It does NOT prove the N01 exclusion or the T->0 placement as forced steps (those are context),
does NOT claim max-plus is wrong/useless (it is the correct arithmetic of the deductive limit and useful in RL credit
assignment, per the source attachments), and does NOT build a tropical engine layer. scratch_diagnostic,
promotion_allowed=false.
"""
import json, os, sys
import numpy as np

def main():
    path=os.path.join(os.path.dirname(os.path.abspath(__file__)),"maxplus_tropical_is_classical_limit_not_foundation_sim_results.json")
    # THE ONE GATE: coherent interference violates max-plus monotonicity; decohered control restores it.
    a1=1.0+0j; mag2=1.0
    phis=np.linspace(0,2*np.pi,200)
    Pq=np.array([abs(a1+mag2*np.exp(1j*p))**2 for p in phis])      # coherent amplitude combination
    strongest=max(abs(a1)**2,mag2**2)
    combined_min=float(Pq.min())                                   # destructive dip (below strongest iff interference)
    monotonicity_violation=float(strongest-combined_min)           # >0 iff max-plus monotonicity is violated
    vis_q=float((Pq.max()-Pq.min())/(Pq.max()+Pq.min()))
    # decohered control: incoherent (probability) sum, phase-independent
    P_decohered=abs(a1)**2+mag2**2
    decohered_violation=float(strongest-P_decohered)               # <=0: monotonicity RESTORED
    # the gate: interference breaks monotonicity WITH visibility, AND the decohered control flips both
    gate=bool(monotonicity_violation>0.1 and vis_q>0.5 and decohered_violation<=1e-9)
    verdict=gate
    out={"classification":"scratch_diagnostic","promotion_allowed":False,
         "framing":"PLACES max-plus/tropical algebra via ONE failable gate: coherent interference violates max-plus monotonicity (decohered control flips) -> max-plus cannot be the nonclassical foundation. Rebuilt after a cross-family panel caught the prior N01 and T->0 gates as tautological/textbook and the Bellman/oracle framing as smuggled.",
         "claim_interference_excludes_maxplus":{"strongest_single":strongest,"quantum_combined_min":combined_min,
             "monotonicity_violation":monotonicity_violation,"quantum_visibility":vis_q,
             "decohered_combined":P_decohered,"decohered_violation":decohered_violation,"pass":gate,
             "note":"coherent destructive interference drives combined BELOW strongest single (violates max-plus monotonicity max(a,b)>=a,b) with visibility>0.5; decohered control (incoherent sum) restores monotonicity and has zero visibility -> the exclusion is specifically coherent interference. The one earned, failable gate (panel-confirmed sound)."},
         "context_not_gated":{
             "N01_commutativity":"max-plus tropical-add is commutative; N01 independently disfavours a commutative foundation. STANDARD FACT, not gated here (a commutator of a commutative op is a tautological gate -- panel catch).",
             "T0_placement":"max-plus = T->0 limit of classical log-sum-exp (idempotent-analysis fact); this is why it is the arithmetic of the deductive/Bellman/single-optimal-path limit, reached from the coherent core by decohere-then-T->0. Placement CONTEXT, not a forced step proven here."},
         "honest_scope":"Earns ONE clean negative placement: coherent interference violates max-plus monotonicity (decohered control flips), so max-plus is not the nonclassical foundation. Does NOT prove N01/T->0 as forced steps (context), does NOT claim max-plus is useless (correct arithmetic of the deductive limit), does NOT build a tropical layer.",
         "audit_provenance":"cross-family panel (Gemini-3.1-pro, Grok-4.5, Qwen-3.5, GLM-5.2) unanimously rated the interference gate sound and failable; flagged the prior N01 gate as tautological, the T->0 gate as textbook, and the oracle-duality framing as smuggled prose. Fixed by removing the two weak gates and demoting the narrative to context -- not by relaxing anything.",
         "policy_eval":{"interference_excludes_maxplus_from_foundation":gate,
             "MAXPLUS_NOT_THE_NONCLASSICAL_FOUNDATION":verdict}}
    json.dump(out,open(path,"w"),indent=2)
    print(f"GATE -- INTERFERENCE EXCLUDES MAX-PLUS: quantum combined_min={combined_min:.4f} < strongest={strongest:.4f}")
    print(f"  monotonicity violation={monotonicity_violation:.4f}, quantum visibility={vis_q:.4f}")
    print(f"  decohered control: combined={P_decohered:.4f}, violation={decohered_violation:.2e} (monotonicity RESTORED, visibility 0) -> control flips")
    print(f"  => coherent interference structurally violates max-plus monotonicity; max-plus cannot be the nonclassical foundation -> {gate}")
    print(f"  CONTEXT (not gated, standard facts): max-plus is commutative (N01 disfavours it); max-plus = T->0 limit of log-sum-exp (the deductive/Bellman limit arithmetic)")
    print(f"\n  VERDICT: {'PASS' if verdict else 'FAIL'} (ONE earned gate: interference excludes max-plus from the nonclassical foundation; N01/T->0 kept as honest context after panel audit)")
    if verdict: print("PASS maxplus_tropical_is_classical_limit_not_foundation")
    print("ALL_GATES:","PASS" if verdict else "FAIL","->",path)
    sys.exit(0 if verdict else 1)

if __name__=="__main__":
    main()
