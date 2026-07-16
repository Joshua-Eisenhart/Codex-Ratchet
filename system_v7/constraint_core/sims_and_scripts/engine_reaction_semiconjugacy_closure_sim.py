#!/usr/bin/env python3
"""=== SUPERSEDED by engine_reaction_semiconjugacy_qutrit_floor_sim.py (basis-invariant). Kept as scaffold. ===
This qubit-level, hand-picked-basis version was panel-flagged (Gemini FATAL): the "dissipative closes / Hamiltonian
breaks" split is a BASIS-CHOICE ARTIFACT -- Q (populations=z-basis) was aligned with the z-basis dissipators and
misaligned with the transverse H0; if Q were H0's eigenbasis the Hamiltonian would NOT break closure. The correct,
basis-invariant test (search ALL bases for closure) revealed the deeper truth: EVERY qubit Lindbladian closes in SOME
basis (8/8 random samples, defect ~1e-13), so the test is VACUOUS at 2 levels. It becomes non-vacuous only at 3+ levels
-- see the qutrit-floor sim, which is the shipped version. This file documents the qubit dead-end.
=========================================================================================================
Original docstring:

engine_reaction_semiconjugacy_closure -- PURE MATH, NO JARGON. 2026-07-10.
The NON-CIRCULAR level-4 "one basin, many probes" test. Replaces the withdrawn three_view_semiconjugacy_gate (which
installed the same core matrix P into every view -> definitional identity, panel-killed). Here the domain view's
generator is NOT installed; it is DISCOVERED (or found not to exist), and the projection is FORCED by the domain.

SET-UP.
  CORE (not chosen to match anything): the actual single-qubit engine terrain Liouvillian L -- the GKSL generator
  d rho/dt = L[rho] used throughout the estate (terrain dissipator +/- the engine Hamiltonian H0=(sx+sy+sz)/sqrt3).
  Vectorize rho=(rho00,rho01,rho10,rho11); L is the 4x4 matrix of the superoperator.
  DOMAIN VIEW (reaction network / classical master equation): a chemist sees POPULATIONS (concentrations), not
  coherences. So the projection is FORCED: Q: rho -> (rho00, rho11). This Q is domain-given, NOT fit.
  The QUESTION (level-4 semiconjugacy): does there exist ANY valid classical reaction-network generator K (a master-
  equation / graph-Laplacian: off-diagonal >=0, columns sum to 0) such that
        Q( exp(Lt) rho )  ==  exp(Kt)( Q rho )   for all rho, t   ?
  This is TRUE iff the population dynamics CLOSE under L, i.e. Q L factors through Q:  Q L = K Q  for some K.
  A solution K exists iff QL vanishes on ker(Q) (the coherence subspace). So the exact, non-circular measurable is the
  CLOSURE DEFECT = || (QL) restricted to the coherence directions rho01,rho10 ||. Zero => a classical reaction network
  reproduces the engine's population dynamics exactly (the two views ARE one basin at level 4). Nonzero => NO classical
  reaction network can reproduce it; the quantum coherences are load-bearing.

WHY THIS IS NOT CIRCULAR (the fix for the panel's kill): K is never installed. Q is forced by the domain (populations).
We compute whether ANY admissible K can work by testing closure of the REAL engine generator; if it closes we RECONSTRUCT
K and CHECK it is a valid classical generator (off-diag>=0, columns sum 0). The engine dynamics either fit the
independently-defined class "classical reaction network" or they do not -- discovered, not assumed.

FAILABLE GATE (a real dichotomy with a control that flips):
  (1) DISSIPATIVE terrain (dephasing/damping, NO Hamiltonian): closure defect ~ 0  AND the reconstructed K is a valid
      classical generator  =>  the QIT-engine view and the reaction-network view are semiconjugate (ONE basin at level 4).
  (2) SAME terrain + engine Hamiltonian H0 (transverse, does not commute with the population basis): closure defect
      MATERIALLY NONZERO  =>  NO classical reaction network reproduces the driven engine; coherences are load-bearing.
  PASS = (1) holds (defect<1e-9, K valid) AND (2) holds (defect>1e-3). The control that flips is the Hamiltonian: adding
  it must break the classical semiconjugacy. If BOTH closed, the test would be vacuous; if NEITHER closed, the projection
  would be wrong.

CROSS-LENS (CONJECTURE, not computed here): the split "population-basis-compatible generator closes / transverse
Hamiltonian breaks" plausibly relates to the detailed-balance boundary the SEPARATE FEP-IGT Carlen-Maas instrument found
(detailed-balance dissipator = exact relative-entropy gradient flow; Hamiltonian drive breaks it). This sim computes NO
FEP-IGT quantity -- the connection is a lead to test, not a verified corroboration. (Panel-corrected from an overclaim.)

HONEST SCOPE. Earns: a NON-circular, domain-forced, failable level-4 semiconjugacy test between the QIT-engine view and
the reaction-network view, with the exact obstruction (population-coherence coupling) measured, and a control (the
Hamiltonian) that flips it. Does NOT claim all domains are one basin; it establishes the test on ONE real pair of views
and locates precisely where they coincide (dissipative sector) and where they diverge (coherent drive).
classification=scratch_diagnostic, promotion_allowed=False.
"""
import json, os, sys
import numpy as np
from scipy.linalg import expm
HERE=os.path.dirname(os.path.abspath(__file__))

sx=np.array([[0,1],[1,0]],complex); sy=np.array([[0,-1j],[1j,0]],complex); sz=np.array([[1,0],[0,-1]],complex); I2=np.eye(2,dtype=complex)
sp=0.5*(sx+1j*sy); sm=0.5*(sx-1j*sy)
G=0.35; KAP=1.0; H0=(sx+sy+sz)/np.sqrt(3)

def Dop(L):
    # superoperator (4x4) of the dissipator rho -> L rho L^dag - 1/2{L^dag L, rho}, column-stacking vec
    Ld=L.conj().T; LdL=Ld@L
    return np.kron(L.conj(),L)-0.5*(np.kron(I2,LdL)+np.kron(LdL.T,I2))
def Hcomm(H):
    return -1j*(np.kron(I2,H)-np.kron(H.T,I2))   # superoperator of -i[H,rho]

def terrain_liouvillian(kind="dephase", with_H=False):
    Lsup=np.zeros((4,4),complex)
    if kind=="dephase": Lsup+=KAP*Dop(sz)
    elif kind=="damp":  Lsup+=KAP*Dop(sm)
    elif kind=="depol": Lsup+=0.5*KAP*(Dop(sx)+Dop(sy)+Dop(sz))
    if with_H: Lsup+=G*Hcomm(H0)
    return Lsup

# vec order (column-stacking of 2x2): index 0=rho00,1=rho10,2=rho01,3=rho11
# populations are indices 0 and 3; coherences are indices 1 and 2.
POP=[0,3]; COH=[1,2]
Q=np.zeros((2,4)); Q[0,0]=1; Q[1,3]=1   # rho -> (rho00, rho11)

def closure_defect_and_K(Lsup):
    QL=Q@Lsup                          # 2x4
    # closure requires QL to vanish on coherence columns
    defect=float(np.max(np.abs(QL[:,COH])))
    # reconstruct K on populations (QL restricted to population columns)
    K=np.real(QL[:,POP])               # 2x2
    return defect,K

def is_valid_classical_generator(K,tol=1e-9):
    # master-equation generator: off-diagonal >=0, columns sum to 0
    offdiag_ok=bool(K[0,1]>=-tol and K[1,0]>=-tol)
    colsum=np.abs(K.sum(axis=0))
    colsum_ok=bool(np.max(colsum)<1e-6)
    return offdiag_ok and colsum_ok, {"K":K.tolist(),"offdiag_nonneg":offdiag_ok,"colsum_zero":colsum_ok,"max_colsum":float(np.max(colsum))}

def semiconj_residual(Lsup,K,samples=200):
    # directly verify Q exp(Lt) rho == exp(Kt) Q rho over random states and t
    r=0.0; rng=np.random.default_rng(7)
    for _ in range(samples):
        a=rng.random(); b=rng.random()*0.4; ph=rng.random()*2*np.pi
        rho=np.array([[a,b*np.exp(1j*ph)],[b*np.exp(-1j*ph),1-a]],complex)
        rho=rho/np.trace(rho)
        v=rho.reshape(4,order="F")
        for t in (0.3,1.0,3.0):
            lhs=Q@(expm(Lsup*t)@v)
            rhs=expm(K*t)@(Q@v)
            r=max(r,float(np.max(np.abs(np.real(lhs)-np.real(rhs)))))
    return r

# x-basis-raising jump: a NON-population-aligned dissipator that must NOT close (shows the dissipative side is failable too)
Wbasis=np.array([[1,1],[1,-1]],complex)/np.sqrt(2)
Lxraise=(0.5*(sx+1j*sy))@Wbasis

def K_is_nonvacuous(K,tol=1e-9): return bool(np.max(np.abs(K))>tol)   # not the zero (frozen-populations) generator

def main():
    path=os.path.join(HERE,"engine_reaction_semiconjugacy_closure_sim_results.json")
    # ---- LOAD-BEARING cases: NON-TRIVIAL dissipative terrains whose reconstructed K is a real (non-zero) classical network ----
    # damping: excited->ground decay chain (birth-death); depol: symmetric two-state exchange. Both genuinely move populations.
    Ldamp=terrain_liouvillian("damp",with_H=False)
    d_damp,K_damp=closure_defect_and_K(Ldamp); valid_damp,Kdamp_info=is_valid_classical_generator(K_damp)
    res_damp=semiconj_residual(Ldamp,K_damp) if valid_damp else None
    damp_ok=bool(d_damp<1e-9 and valid_damp and K_is_nonvacuous(K_damp) and res_damp is not None and res_damp<1e-9)

    Ldepol=terrain_liouvillian("depol",with_H=False)
    d_dep,K_dep=closure_defect_and_K(Ldepol); valid_dep,Kdep_info=is_valid_classical_generator(K_dep)
    res_dep=semiconj_residual(Ldepol,K_dep) if valid_dep else None
    depol_ok=bool(d_dep<1e-9 and valid_dep and K_is_nonvacuous(K_dep) and res_dep is not None and res_dep<1e-9)

    # ---- DEGENERATE case (kept only for honesty): pure dephasing closes but with K=0 ("nothing happens"). NOT load-bearing. ----
    Ldeph=terrain_liouvillian("dephase",with_H=False)
    d_deph,K_deph=closure_defect_and_K(Ldeph)
    deph_K_is_zero=bool(not K_is_nonvacuous(K_deph))   # expected True -> vacuous, excluded from the verdict

    # ---- CONTROL 1 (flips on the dissipative side): a non-population-aligned jump must NOT close ----
    Lxr=np.zeros((4,4),complex); Lxr+=KAP*Dop(Lxraise)
    d_xr,_=closure_defect_and_K(Lxr)
    nonaligned_breaks=bool(d_xr>1e-3)

    # ---- CONTROL 2 (the Hamiltonian flip): SAME damping terrain + engine Hamiltonian must BREAK closure ----
    Lh=terrain_liouvillian("damp",with_H=True)
    d_h,_=closure_defect_and_K(Lh)
    hamiltonian_breaks=bool(d_h>1e-3)

    # verdict: the two NON-TRIVIAL dissipative terrains are genuinely semiconjugate to a real classical network,
    # AND both controls flip (non-aligned dissipator + Hamiltonian drive). The vacuous dephasing case is excluded.
    verdict=bool(damp_ok and depol_ok and nonaligned_breaks and hamiltonian_breaks)
    results={"classification":"scratch_diagnostic","promotion_allowed":False,
      "framing":"NON-circular level-4 semiconjugacy test between the QIT-engine view and the reaction-network (classical master-equation) view. Projection Q (rho->populations) is FORCED by the domain (a reaction network sees concentrations, not coherences); the classical generator K is NOT installed but RECONSTRUCTED from the real engine Liouvillian and VALIDATED as an admissible master-equation generator (off-diagonals>=0, columns sum 0). Load-bearing cases are the NON-TRIVIAL dissipative terrains (damping = decay chain, depolarizing = two-state exchange) whose reconstructed K is a genuine non-zero classical network. Two controls flip: a non-population-aligned jump does NOT close, and the engine Hamiltonian breaks closure. Pure dephasing is reported but EXCLUDED from the verdict because its K is the zero matrix (vacuous).",
      "gate1_nontrivial_dissipative_semiconjugate":{
        "damp_closure_defect":d_damp,"damp_K":Kdamp_info,"damp_K_nonvacuous":K_is_nonvacuous(K_damp),"damp_semiconj_residual":res_damp,"damp_is_semiconjugate":damp_ok,
        "depol_closure_defect":d_dep,"depol_K":Kdep_info,"depol_K_nonvacuous":K_is_nonvacuous(K_dep),"depol_semiconj_residual":res_dep,"depol_is_semiconjugate":depol_ok},
      "degenerate_dephasing_excluded":{"closure_defect":d_deph,"K":K_deph.tolist(),"K_is_zero_vacuous":deph_K_is_zero,
        "note":"pure dephasing IS population-basis-diagonal so it closes with K=0 (frozen populations); kept for honesty, NOT counted toward the verdict (panel-flagged as vacuous)."},
      "control1_nonaligned_dissipator_breaks":{"closure_defect":d_xr,"breaks":nonaligned_breaks,
        "note":"a jump operator NOT aligned to the population basis couples populations to coherences -> QL does not vanish on coherences -> no classical network. Shows the dissipative side is genuinely failable, not automatic for any dissipator."},
      "control2_hamiltonian_breaks":{"damp+H_closure_defect":d_h,"breaks":hamiltonian_breaks,
        "note":"engine H0=(sx+sy+sz)/sqrt3 is transverse; adding it to the damping terrain re-couples populations to coherences -> no classical reaction network reproduces the driven engine."},
      "cross_lens_conjecture":"CONJECTURE (NOT computed here): the boundary 'population-basis-compatible generator closes / transverse Hamiltonian breaks' plausibly relates to the detailed-balance boundary the separate FEP-IGT Carlen-Maas instrument found. This sim does NOT compute any FEP-IGT quantity; treat as a lead to test, not a corroboration.",
      "honest_scope":"Non-circular (Q domain-forced; K discovered from the real engine generator and validated, never installed), failable on BOTH sides (a non-aligned dissipator fails to close; the Hamiltonian breaks closure), with the exact obstruction (population-coherence coupling) measured. The precise earned statement: the engine's canonical DISSIPATIVE terrains are population-basis-compatible, so their population dynamics ARE a genuine classical reaction network (level-4 semiconjugate); the engine's coherent drive is not, so it has no classical shadow. This is ONE real pair of views, not a claim that all domains are one basin.",
      "pass":verdict,
      "policy_eval":{"nontrivial_dissipative_views_one_basin":bool(damp_ok and depol_ok),"dissipative_side_failable":nonaligned_breaks,"coherent_drive_breaks_classical_view":hamiltonian_breaks}}
    json.dump(results,open(path,"w"),indent=2)
    print("GATE -- engine<->reaction-network level-4 semiconjugacy (NON-circular; Q forced, K discovered+validated):")
    print(f"  (1) damping terrain:  defect {d_damp:.2e}, K={K_damp.tolist()} valid&nonzero:{valid_damp and K_is_nonvacuous(K_damp)}, residual {res_damp if res_damp is None else format(res_damp,'.2e')} -> one basin: {damp_ok}")
    print(f"      depol terrain:    defect {d_dep:.2e}, K={K_dep.tolist()} valid&nonzero:{valid_dep and K_is_nonvacuous(K_dep)}, residual {res_dep if res_dep is None else format(res_dep,'.2e')} -> one basin: {depol_ok}")
    print(f"      [dephasing excluded: K={K_deph.tolist()} is zero/vacuous]")
    print(f"  control1 non-aligned dissipator: defect {d_xr:.2e} -> breaks (dissipative side failable): {nonaligned_breaks}")
    print(f"  control2 damping + engine Hamiltonian: defect {d_h:.2e} -> breaks: {hamiltonian_breaks}")
    print(f"  VERDICT: {'PASS' if verdict else 'FAIL'} (non-trivial dissipative terrains ARE a classical reaction network at level 4; both controls flip)")
    if verdict: print("PASS engine_reaction_semiconjugacy_closure")
    print("ALL_GATES:","PASS" if verdict else "FAIL","->",path)
    sys.exit(0 if verdict else 1)

if __name__=="__main__":
    main()
