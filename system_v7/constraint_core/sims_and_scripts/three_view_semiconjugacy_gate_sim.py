#!/usr/bin/env python3
"""=== WITHDRAWN SCAFFOLD (NOT registered; harness stays 144). Retained as documented failed approach. ===
WITHDRAWN 2026-07-10 after unanimous adversarial panel (Grok-4.5/Qwen-3.5/GLM-5.2). The design is circular and no
amount of dressing fixes it within this construction:
  FATAL: each domain view-step T^(d) is DEFINED in terms of the same core matrix P (as diag(P.), or as a conjugation
  M_d P M_d^{-1}). So the semiconjugacy Q_d(Tx)=T^(d)(Q_d x) is TRUE BY CONSTRUCTION -- I installed P into every view
  and then "discovered" it intertwines. That proves only that three wrappers of the same linear map intertwine
  themselves; it does NOT test whether three INDEPENDENTLY-DEFINED domain dynamics (QIT channel from its own axioms,
  a reaction network from mass-action rules, an agent MDP from its own reward/transition rules) turn out to be
  projections of one core process. The controls (scramble, wrong-P) do flip, but they only confirm that P doesn't
  commute with a permutation and that P!=P' -- neither probes the non-tautological unification claim.
  (An intermediate fix made views B/C genuine invertible representations M_d P M_d^{-1} instead of identity -- that
  removed the "B and C are literally identical" defect the panel caught, but did NOT remove the core circularity,
  because M_d P M_d^{-1} still contains P by hand.)
WHAT A REAL LEVEL-4 TEST NEEDS (the honest frontier, a research build not a one-cell sim): define each domain's step
from ITS OWN domain rules with domain-specific parameters, fit ONLY the projection Q_d (not the dynamics), and then
MEASURE the residual Q_d(Tx)-T^(d)(Q_d x). Semiconjugacy is earned only if an independently-specified T^(d) is found
to intertwine -- e.g. the ACTUAL 16-stage engine Liouvillian (already built) vs a Catalyst reaction network fit to
match only at the fixed point, then tested off-fixed-point. That is the "Three-View Semiconjugacy Gate" build card;
this scaffold is a placeholder that documents why the naive version is circular.
=========================================================================================================
Original (circular) docstring follows for the record:

three_view_semiconjugacy_gate -- PURE MATH, NO JARGON. 2026-07-10.
Operationalizes the SINGLE highest-value recommendation across every external review: the test that separates
"one attractor basin seen through many probes" (the whole unification thesis) from "different domains with
similarly-shaped plots." The reviews call it the cross-view transfer hierarchy; only level >=4, DYNAMICAL
SEMICONJUGACY, justifies "one basin":

    Q_d( T(x) )  ==  T^(d)( Q_d(x) )          (the projection Q_d intertwines the core step T with the view step T^(d))

Below level 4 (analogy, formal-compat, structural-map) is just shared vocabulary. This sim builds ONE finite core
process T and asks whether three DIFFERENT domain projections each intertwine it -- with controls that MUST break.

THE CORE PROCESS (finite, minimal, no imported domain structure):
  A finite Markov-like stochastic step T on a small probability simplex over N=3 states (a column-stochastic matrix P
  acting on a distribution). This is the weakest object that has: finite state, order-sensitive composition
  (noncommuting with other stochastic maps), and a genuine attractor (the Perron fixed point). It is domain-NEUTRAL --
  it is not "really" QIT or chemistry or agents; those are the probe views below.

THREE DOMAIN PROJECTIONS (each maps the SAME core state/step into a domain's own dynamics):
  (A) QIT view: embed the distribution as the diagonal of a density matrix rho=diag(p); the view step is the
      corresponding classical-CPTP channel (a stochastic map lifted to act on diagonals). Q_A = diag-embed.
  (B) Reaction-network view: the distribution is species concentrations on the simplex; the view step is the
      SAME stochastic transition read as mass-action flux on a linear reaction graph (rate matrix = P). Q_B = identity
      on the simplex but with the reaction-graph generator as T^(B).
  (C) Agent state-machine view: the distribution is a belief over 3 discrete agent states; the view step is the belief
      update of a Markov decision process whose transition kernel IS P. Q_C = belief-simplex identity, T^(C)=belief push.

The three T^(d) are constructed to be the domain-native expression of the SAME P (that is the hypothesis: one process).
The gate measures, for each view, the semiconjugacy residual  || Q_d(T x) - T^(d)(Q_d x) ||  over many random x.

FAILABLE GATE (three legs must hold + two controls must break):
  (1) all three views intertwine T to < 1e-9 over a random state ensemble;
  (2) CONTROL A -- a SCRAMBLED projection (permute the state labels inside Q_d only) BREAKS semiconjugacy (residual
      >> 1e-9): proves the intertwining is a real structural fact, not automatic;
  (3) CONTROL B -- a WRONG view-step (use a DIFFERENT stochastic matrix P' != P as T^(d)) BREAKS it: proves the view
      must express the SAME core process, not just any process of the right shape.
  Additionally the shared attractor is reported: all three views must map the core Perron fixed point to their own
  fixed point (one basin, three renderings).

HONEST SCOPE. This is the LEVEL-4 test on a DELIBERATELY SIMPLE shared kernel (finite stochastic P). PASS earns:
"for this finite process, the QIT/reaction/agent views are genuine dynamical projections of one core step, and the
claim survives scramble + wrong-process controls." It does NOT yet prove the FULL 16-stage engine is tri-view
semiconjugate (that is the next rung -- swap P for the engine Liouvillian). It is the smallest honest instance of the
unification thesis made failable. classification=scratch_diagnostic, promotion_allowed=False.
"""
import json, os, sys
import numpy as np
rng=np.random.default_rng(20260710)
HERE=os.path.dirname(os.path.abspath(__file__))

N=3
def rand_colstoch(r):
    M=r.random((N,N))+0.1
    return M/M.sum(axis=0,keepdims=True)
def rand_dist(r):
    x=r.random(N)+0.05; return x/x.sum()

# ONE core process
P=rand_colstoch(rng)               # core stochastic step T: p -> P@p
Pprime=rand_colstoch(rng)          # a DIFFERENT process for control B

def T_core(p): return P@p

# Each view is a GENUINE (invertible) representation change M_d, so the domain step is a real CONJUGATION
# T^(d) = M_d P M_d^{-1}, and semiconjugacy Q_d(Tx)=T^(d)(Q_d x) is NON-trivial in all three views (not identity).
# This closes the "views B/C are just P again" tautology: only if the SAME P sits inside each conjugation does it hold.
def rand_invertible(r):
    while True:
        M=r.standard_normal((N,N))
        if abs(np.linalg.det(M))>0.3: return M

# --- View A: QIT (non-diagonal density embed via a fixed unitary basis) ---
# distribution p -> density rho = U diag(p) U^\dagger in a rotated basis; step is the lifted classical channel in that basis.
th=0.7
U=np.array([[np.cos(th),-np.sin(th),0],[np.sin(th),np.cos(th),0],[0,0,1]],dtype=complex)  # real orthogonal (unitary)
def QA(p): return U@np.diag(p).astype(complex)@U.conj().T
def _diag_in_basis(rho): return np.real(np.diag(U.conj().T@rho@U))
def TA(rho): return U@np.diag(P@_diag_in_basis(rho)).astype(complex)@U.conj().T   # = conjugation by U of (P on diagonal)
def QA_scram(p): return U@np.diag(p[[1,2,0]]).astype(complex)@U.conj().T
def TA_wrong(rho): return U@np.diag(Pprime@_diag_in_basis(rho)).astype(complex)@U.conj().T

# --- View B: reaction network in a linear-combination (extent) coordinate M_B ---
MB=rand_invertible(rng); MBinv=np.linalg.inv(MB)
def QB(p): return MB@p
def TB(c): return (MB@P@MBinv)@c                       # T^(B) = M_B P M_B^{-1}  (non-trivial conjugation)
def QB_scram(p): return MB@p[[2,0,1]]
def TB_wrong(c): return (MB@Pprime@MBinv)@c

# --- View C: agent belief MDP in a different (log-odds-like) linear coordinate M_C ---
MC=rand_invertible(rng); MCinv=np.linalg.inv(MC)
def QC(p): return MC@p
def TC(b): return (MC@P@MCinv)@b                       # T^(C) = M_C P M_C^{-1}
def QC_scram(p): return MC@p[[1,0,2]]
def TC_wrong(b): return (MC@Pprime@MCinv)@b

def residual(Q,Tview,Tcore,scram=False,samples=200):
    r=0.0
    for _ in range(samples):
        p=rand_dist(rng)
        lhs=Q(Tcore(p))            # Q_d(T x)
        rhs=Tview(Q(p))            # T^(d)(Q_d x)
        r=max(r, float(np.max(np.abs(np.asarray(lhs)-np.asarray(rhs)))))
    return r

def main():
    path=os.path.join(HERE,"three_view_semiconjugacy_gate_sim_results.json")
    # (1) the three genuine semiconjugacy residuals
    rA=residual(QA,TA,T_core); rB=residual(QB,TB,T_core); rC=residual(QC,TC,T_core)
    TOL=1e-9
    legA=rA<TOL; legB=rB<TOL; legC=rC<TOL
    all_intertwine=bool(legA and legB and legC)

    # (2) control A: scrambled projection must break each view
    sA=residual(QA_scram,TA,T_core); sB=residual(QB_scram,TB,T_core); sC=residual(QC_scram,TC,T_core)
    scramble_breaks=bool(sA>1e-6 and sB>1e-6 and sC>1e-6)

    # (3) control B: wrong view-step (different process) must break each view
    wA=residual(QA,TA_wrong,T_core); wB=residual(QB,TB_wrong,T_core); wC=residual(QC,TC_wrong,T_core)
    wrongproc_breaks=bool(wA>1e-6 and wB>1e-6 and wC>1e-6)

    # shared attractor: Perron fixed point of P renders as EACH view's fixed point (one basin, three renderings).
    # The test: Q_d(fp) is a fixed point of T^(d), i.e. T^(d)(Q_d fp) == Q_d(fp) for all three views.
    w,v=np.linalg.eig(P); k=int(np.argmin(np.abs(w-1.0))); fp=np.real(v[:,k]); fp=fp/fp.sum()
    aA=np.max(np.abs(np.asarray(TA(QA(fp)))-np.asarray(QA(fp))))
    aB=np.max(np.abs(TB(QB(fp))-QB(fp)))
    aC=np.max(np.abs(TC(QC(fp))-QC(fp)))
    attr_shared=bool(aA<1e-9 and aB<1e-9 and aC<1e-9)

    verdict=bool(all_intertwine and scramble_breaks and wrongproc_breaks and attr_shared)
    out={"classification":"scratch_diagnostic","promotion_allowed":False,
      "framing":"Level-4 DYNAMICAL SEMICONJUGACY test of 'one basin, many probes' on the smallest honest shared kernel: one finite stochastic core step T, projected into QIT / reaction-network / agent-belief views; each view step T^(d) must intertwine T (Q_d(Tx)=T^(d)(Q_d x)). This is the minimum bar the reviews require before calling domains 'the same attractor'; below it is mere analogy.",
      "core_process_P":P.tolist(),
      "gate1_three_views_intertwine":{"qit_residual":rA,"reaction_residual":rB,"agent_residual":rC,"all_below_1e-9":all_intertwine},
      "gate2_scrambled_projection_breaks":{"qit":sA,"reaction":sB,"agent":sC,"breaks":scramble_breaks,
        "note":"permuting state labels inside Q_d only -> semiconjugacy must fail; proves the intertwining is structural, not automatic."},
      "gate3_wrong_process_breaks":{"qit":wA,"reaction":wB,"agent":wC,"breaks":wrongproc_breaks,
        "note":"using a DIFFERENT stochastic matrix as T^(d) -> must fail; proves each view expresses the SAME core process, not any process of the right shape."},
      "shared_attractor":{"core_perron_fixed_point":fp.tolist(),"all_views_share_it":attr_shared},
      "honest_scope":"PASS earns level-4 semiconjugacy for a DELIBERATELY SIMPLE shared kernel (finite stochastic P) across three domain views, with scramble + wrong-process controls that break. It is the smallest failable instance of the unification thesis. It does NOT yet prove the full 16-stage engine Liouvillian is tri-view semiconjugate -- that is the next rung (swap P for the engine generator and re-run this exact gate).",
      "pass":verdict,
      "policy_eval":{"one_kernel_three_views_intertwine":all_intertwine,"controls_break":bool(scramble_breaks and wrongproc_breaks),"shared_attractor":attr_shared}}
    json.dump(out,open(path,"w"),indent=2)
    print("GATE -- three-view dynamical semiconjugacy (one basin, many probes) on a finite stochastic kernel:")
    print(f"  (1) intertwine residuals: QIT {rA:.2e}  reaction {rB:.2e}  agent {rC:.2e}  all<1e-9: {all_intertwine}")
    print(f"  (2) scrambled-projection control: {sA:.2e}/{sB:.2e}/{sC:.2e}  breaks: {scramble_breaks}")
    print(f"  (3) wrong-process control: {wA:.2e}/{wB:.2e}/{wC:.2e}  breaks: {wrongproc_breaks}")
    print(f"  shared Perron attractor across all three views: {attr_shared}")
    print(f"  VERDICT: {'PASS' if verdict else 'FAIL'} (level-4 semiconjugacy holds for one kernel across QIT/reaction/agent views; controls break)")
    if verdict: print("PASS three_view_semiconjugacy_gate")
    print("ALL_GATES:","PASS" if verdict else "FAIL","->",path)
    sys.exit(0 if verdict else 1)

if __name__=="__main__":
    main()
