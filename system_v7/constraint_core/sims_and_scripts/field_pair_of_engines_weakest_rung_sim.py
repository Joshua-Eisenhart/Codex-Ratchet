#!/usr/bin/env python3
"""field_pair_of_engines_weakest_rung -- SCAFFOLD, NOT AN EARNED RUNG. NOT IN THE HARNESS. 2026-07-09.

STATUS AFTER TWO PANEL ROUNDS + A CHIRALITY-LOAD-BEARING TEST: this sim does NOT earn a field-of-engines rung and was
de-registered from run_all.py. Kept only as an honest scratch record of what was tried and why it fell short.

WHY IT DOES NOT EARN A RUNG (the decisive findings):
  1. The first version's core gate (g=0 -> R=0, R = deviation-from-product) was a TAUTOLOGY (R is defined as
     deviation-from-product) -- caught by 3 of the 4 cross-family panel models (Gemini-3.1-pro, Grok-4.5, GLM-5.2
     flagged it fail-level; Qwen-3.5 rated it sound). A 3-of-4 majority, not unanimous.
  2. The rebuild used entanglement NEGATIVITY (a real monotone) + a classical-correlation control (MI>0, negativity=0).
     That fixed the tautology, but the panel's deeper objection stood: gates 1/3 are TEXTBOOK QM (an entangler makes
     negativity>0, a local map does not), true for ANY two qubits -- not theory-specific.
  3. DIRECT TEST of whether the model's own structure (opposite Weyl chirality, Type-1 vs Type-2) is load-bearing:
     opposite-chirality and same-chirality pairs give IDENTICAL negativity (0.4660 both) -- the local unitaries wash
     out under the entangler. So the chirality distinction is DECORATIVE here; the negativity is generic 2-qubit QM.
  4. A chirality-SENSITIVE relational geometric phase looked promising (a clean +/-1.57 sign-flip with chirality) but
     a coupling/loop-length SWEEP showed the antisymmetry holds ONLY at the special angle th=1.2 -- an angle artifact,
     not a robust invariant. Nearly banked as a second artifact; the sweep caught it.

HONEST RESIDUE. The one non-textbook, non-tautological thing that survives is a CONDITIONAL, generic-QI claim: IF the
two engines couple, the pair is nonclassical (negativity>0, created from a product start) and classical correlation
(MI>0) is provably insufficient to reproduce it. That is TRUE but is not theory-specific and does not need the
field/engine framing -- so it is not a field rung. The genuine field-of-engines rung remains OPEN: it needs a pair
observable that (a) is relational (needs both engines + coupling) AND (b) is load-bearing on this model's structure
(chirality / the Weyl distinction) AND (c) is robust, not an angle coincidence. None of those three held together here.

------------------------------------------------------------------------------------------------------------------
(original scaffold text follows; retained for the record)
First rung of the FIELD OF ENGINES (owner's axes-7-12 level, each node of a space itself an engine). MSS: admit only
the structure the constraints FORCE for two engines to become one object.

AUDIT HISTORY (why this is the rebuilt version). The first version gated on R = trace-distance of the joint channel
from the product of its own marginals, with a g=0 (product) control giving R=0. A cross-family LLM panel (Gemini-3.1-
pro, Grok-4.5, Qwen-3.5, GLM-5.2), 3 of 4 (Gemini, Grok, GLM; Qwen-3.5 rated it sound), flagged this as a TAUTOLOGY:
R is DEFINED as deviation-from-product, so g=0 forces R=0 by linear algebra, not physics -- a gate that cannot fail
(rubber stamp). The majority was right. This rebuild
puts the fix in the MEASUREMENT (never the gate): the honest content of "two engines are a new object" is
NONCLASSICALITY -- correlation a classical / shared-randomness pair CANNOT reproduce -- not mere non-productness (which
any entangler gives trivially).

MSS DERIVATION -- and its honest boundary (sharpened after a SECOND panel round). The two engines are already forced
(the two Weyl chiralities Type-1 eps=+1 / Type-2 eps=-1, earned in prior rungs). Two engines side by side with only
CLASSICAL correlation (shared randomness) are still separable -- reducible to a probabilistic mixture of independent
engine states. The WEAKEST structure that makes the pair a genuinely NEW object, irreducible to any classical
composition of its parts, is one ENTANGLING degree of freedom.

  WHAT THIS SIM DOES AND DOES NOT EARN (the panel's correct objection). This sim does NOT re-derive from {F01,N01}
  that the pair MUST couple -- "entanglement is central" is inherited project doctrine, asserted elsewhere, not
  re-proven here. So the claim is CONDITIONAL: *IF* the two engines couple at all (via ANY entangler), *THEN* the pair
  becomes a genuinely nonclassical object that no classically-correlated composition of the parts can reproduce. The
  earned, non-trivial content is the SEPARATION -- that classical correlation (MI>0) is provably insufficient, so the
  new object is nonclassical, not merely correlated -- and that this holds for the entangling CLASS (ZxZ and XxX
  alike), not a hand-picked generator. The word "forced" is downgraded to "conditional on the core entanglement
  doctrine"; this is a WARN-honest conditional rung, not an unconditional forcing proof. The full forcing (does the
  field DYNAMICS compel coupling?) is deferred to the field-metric rung.

GATED CLAIMS (all computed; controls must FAIL):
  (1) THE PAIR IS A GENUINELY NONCLASSICAL OBJECT: with an entangling coupling the joint state has entanglement
      NEGATIVITY > 0. CONTROL: a SEPARABLE product evolution (no coupling) gives negativity = 0. Negativity is an
      entanglement monotone (|sum of negative eigenvalues of the partial transpose|), NOT "deviation from product", so
      this is not the circular quantity the panel flagged.
  (2) CORRELATION IS NOT THE CRITERION -- nonclassicality is (the non-tautological heart). A CLASSICALLY-CORRELATED
      control: a Z-correlated SEPARABLE mixture (shared randomness) that has mutual information MI > 0 (it IS
      correlated, joint != product of marginals) but negativity = 0. So a merely-correlated pair is NOT the new
      object; only the entangled pair is. This control has R>0 in the OLD (tautological) metric yet correctly FAILS
      the nonclassicality test -- it is exactly the case the old gate could not distinguish.
  (3) NOT GENERATOR-SPECIFIC (answers "ZZ is smuggled"): two DIFFERENT entangling generators (Z(x)Z and X(x)X) BOTH
      give negativity > 0, and BOTH classical/product controls give 0. The earned claim is about the entangling class
      forced by core entanglement, not a hand-picked Z(x)Z form. CONTROL: a separable (local-only) generator gives 0.

HONEST SCOPE. Earns a CONDITIONAL weakest field rung: IF the two engines couple (any entangler), the pair is a
genuinely nonclassical object (negativity>0) that no classically-correlated composition can reproduce -- and classical
correlation (MI>0) is provably insufficient (the non-tautological, non-textbook content). Does NOT re-derive that the
pair must couple (inherited doctrine, not re-proven here -- flagged by the panel), does NOT build the field metric (flat
vs curved -- next rung, where the owner conjectures the exceptional algebras may become load-bearing), does NOT claim
the exceptional algebras appear here, does NOT presume the axes-7-12 layout. Verified entanglement is CREATED from a
genuine product start (|++> has negativity 0), not present initially. Two engines use opposite Weyl chirality (prior
rung). scratch_diagnostic, promotion_allowed=false.
"""
import json, os, sys
import numpy as np

I=np.eye(2); sx=np.array([[0,1],[1,0]],complex); sz=np.array([[1,0],[0,-1]],complex)
def expm_h(H):
    w,V=np.linalg.eigh(H); return V@np.diag(np.exp(-1j*w))@V.conj().T
def negativity(rho):                       # entanglement monotone: |sum neg eigs of partial transpose on B|
    r=rho.reshape(2,2,2,2).transpose(0,3,2,1).reshape(4,4)
    ev=np.linalg.eigvalsh((r+r.conj().T)/2); return float(np.sum(np.abs(ev[ev<0])))
def SvN(m):
    w=np.linalg.eigvalsh((m+m.conj().T)/2); w=w[w>1e-12]; return float(-np.sum(w*np.log2(w)))
def mutual_info(rho):
    rA=rho.reshape(2,2,2,2).trace(axis1=1,axis2=3); rB=rho.reshape(2,2,2,2).trace(axis1=0,axis2=2)
    return SvN(rA)+SvN(rB)-SvN(rho)
TH=0.6; GC=0.6
UA=expm_h(TH*sz/2)      # engine A chirality + (Type-1, forced)
UB=expm_h(-TH*sz/2)     # engine B chirality - (Type-2, opposite Weyl, forced)

def quantum_pair(gen):
    psi=np.kron([1,1],[1,1])/2.0; rho0=np.outer(psi,psi.conj()).astype(complex)
    U=expm_h(GC*gen)@np.kron(UA,UB)
    return U@rho0@U.conj().T
def product_pair():     # separable: local engines only, no coupling
    psi=np.kron([1,1],[1,1])/2.0; rho0=np.outer(psi,psi.conj()).astype(complex)
    U=np.kron(UA,UB); return U@rho0@U.conj().T
def classical_correlated():   # Z-correlated separable mixture (shared randomness): correlated but NOT entangled
    P0=np.outer([1,0],[1,0]).astype(complex); P1=np.outer([0,1],[0,1]).astype(complex)
    return 0.5*np.kron(P0,P0)+0.5*np.kron(P1,P1)

def main():
    path=os.path.join(os.path.dirname(os.path.abspath(__file__)),"field_pair_of_engines_weakest_rung_sim_results.json")
    # (1) nonclassical object CREATED from a genuine product start; product control flips
    psi=np.kron([1,1],[1,1])/2.0; start_neg=negativity(np.outer(psi,psi.conj()).astype(complex))
    nq=negativity(quantum_pair(np.kron(sz,sz)))
    npd=negativity(product_pair())
    g1=bool(nq>0.05 and npd<1e-9 and start_neg<1e-9)   # entanglement CREATED (start=0), not present initially
    # (2) correlation is not the criterion: classical control has MI>0 but negativity=0
    rcl=classical_correlated(); mi_cl=mutual_info(rcl); neg_cl=negativity(rcl)
    g2=bool(mi_cl>0.5 and neg_cl<1e-9)         # correlated (MI>0) yet not entangled -> correlation != criterion
    # (3) not generator-specific: ZZ and XX both entangle; separable (local) control does not
    nq_zz=negativity(quantum_pair(np.kron(sz,sz)))
    nq_xx=negativity(quantum_pair(np.kron(sx,sx)))
    neg_local=negativity(quantum_pair(np.kron(sz,I)+np.kron(I,sz)))   # separable local generator -> no entanglement
    g3=bool(nq_zz>0.05 and nq_xx>0.05 and neg_local<1e-9)
    verdict=bool(g1 and g2 and g3)
    out={"classification":"scratch_diagnostic","promotion_allowed":False,
         "framing":"CONDITIONAL rung, twice panel-audited. IF the two Weyl engines couple (any entangler), the pair is a NONCLASSICAL object (negativity>0, CREATED from a product start) that no classically-correlated composition reproduces; and classical correlation (MI>0) is provably insufficient. Does NOT re-derive that the pair must couple (inherited doctrine). Not the field metric or exceptional algebras (next rung).",
         "claim1_nonclassical_object_created":{"start_negativity":start_neg,"negativity_quantum":nq,"negativity_product_control":npd,"pass":g1,
             "note":"entanglement is CREATED: |++> start has negativity 0 (genuine product, verified after panel flagged a possible Bell-state start), coupling lifts it to >0; negativity is an entanglement monotone (neg eigs of partial transpose), NOT deviation-from-product; product control =0 is a real separable-state theorem"},
         "claim2_correlation_is_not_the_criterion":{"classical_mutual_info":mi_cl,"classical_negativity":neg_cl,"pass":g2,
             "note":"Z-correlated separable mixture: MI=1.0 bit (genuinely correlated, joint!=product) yet negativity=0. A merely-correlated pair is NOT the new object -- exactly the case the old tautological R-gate could not tell from an entangled one. This is the non-tautological heart."},
         "claim3_not_generator_specific":{"negativity_ZZ":nq_zz,"negativity_XX":nq_xx,"negativity_local_separable_control":neg_local,"pass":g3,
             "note":"two different entangling generators (ZxZ, XxX) both give negativity>0; a separable local generator gives 0. The claim is the entangling CLASS (core-forced entanglement), not a hand-picked ZxZ -- answers the panel's smuggled-generator finding."},
         "audit_provenance":"cross-family panel (Gemini-3.1-pro, Grok-4.5, Qwen-3.5, GLM-5.2): 3 of 4 (Gemini, Grok, GLM) flagged the prior g=0->R=0 gate as tautological; Qwen-3.5 rated it sound. A 3-of-4 majority, not unanimous. Fixed in the measurement (negativity + classical-correlation control), not by relaxing the gate.",
         "honest_scope":"earns ONLY the weakest field rung (pair is a nonclassical object, not reducible to classical correlation, via one core-forced entangling DOF). Does NOT build the field metric, claim exceptional algebras, or presume the axes-7-12 layout.",
         "policy_eval":{"nonclassical_object_created_from_product":g1,"correlation_alone_is_not_the_criterion":g2,
             "nonclassicality_is_generator_class_not_smuggled_form":g3,"CONDITIONAL_FIELD_WEAKEST_RUNG_EARNED":verdict,
             "forcing_of_coupling_re_derived_here":False}}
    json.dump(out,open(path,"w"),indent=2)
    print(f"(1) NONCLASSICAL OBJECT CREATED: start |++> negativity={start_neg:.2e} ~ 0 (genuine product), quantum end negativity={nq:.4f} > 0; separable product control={npd:.2e} ~ 0 -> {g1}")
    print(f"(2) CORRELATION IS NOT THE CRITERION: classical Z-correlated control MI={mi_cl:.4f} bit (correlated!) but negativity={neg_cl:.2e} ~ 0 -> {g2}")
    print(f"    (this is the case the OLD tautological R-gate could not distinguish; nonclassicality, not correlation, is the earned criterion)")
    print(f"(3) NOT GENERATOR-SPECIFIC: negativity ZZ={nq_zz:.4f}, XX={nq_xx:.4f} both >0; separable local generator={neg_local:.2e} ~ 0 -> {g3}")
    print(f"    => the two-engine pair is a genuinely nonclassical object, irreducible to any classical composition of its parts, via one core-forced entangling DOF (MSS); claim is the entangling class, not a smuggled ZZ form")
    print(f"    HONEST: this is CONDITIONAL -- it earns 'IF coupled THEN nonclassical & irreducible to classical correlation', NOT that coupling is forced (inherited doctrine, not re-derived here)")
    print(f"\n  VERDICT: {'PASS' if verdict else 'FAIL'} (CONDITIONAL field weakest rung: nonclassical pair-object created + correlation!=criterion + generator-class not smuggled)")
    if verdict: print("PASS field_pair_of_engines_weakest_rung")
    print("ALL_GATES:","PASS" if verdict else "FAIL","->",path)
    sys.exit(0 if verdict else 1)

if __name__=="__main__":
    main()
