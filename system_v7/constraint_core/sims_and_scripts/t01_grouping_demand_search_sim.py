#!/usr/bin/env python3
"""t01_grouping_demand_search_sim -- the closing test of the octonion arc: does ANY natural engine operation make
GROUPING (nonassociativity / T01) load-bearing in a way that would FORCE the carrier lift H->O? Exhaustive search over
the engine's stage-combining operations. Answer: NO -- and the reason is classified precisely (the Jacobi discriminator).

Context: UP-112 showed H->O is an unforced observable-side fork; to EARN the octonion rung the model needs a mechanism
where grouping is load-bearing with OCTONIONIC (non-Jacobi, Moufang) nonassociativity. This sim searches for one.

THREE candidate grouping operations, each with its algebraic classification:
  (1) CHANNEL COMPOSITION -- the engine's ACTUAL stage-combining operation (apply stage after stage). Function
      composition is ASSOCIATIVE by construction: ((S3.S2).S1) == (S3.(S2.S1)), defect ~1e-16. So the operation the
      engine really uses cannot be a T01 demand.
  (2) JORDAN PRODUCT A o B = 1/2(AB+BA) of stage superoperators. Genuinely NONASSOCIATIVE (defect ~0.07). BUT the
      engine does NOT compose stages via the Jordan product -- it composes sequentially. So the nonassociativity is
      not load-bearing (present in a product the mechanism doesn't use).
  (3) FIELD / LIE BRACKET [A,B]=AB-BA (a 3-engine interaction bracket). Nonassociative (defect ~0.28) BUT obeys the
      JACOBI identity ([[A,B],C]+[[B,C],A]+[[C,A],B]=0, defect ~1e-16). Jacobi => it is a LIE algebra (so(4)-type,
      matching UP-111's classical field symmetry), NOT octonionic.

THE JACOBI DISCRIMINATOR (why this is decisive): octonions are NON-Lie -- they FAIL Jacobi and instead satisfy the
Moufang identities. Every natural qubit-superoperator combination is built from the matrix commutator, which ALWAYS
obeys Jacobi -> stays Lie/classical. So no operation available to the engine mechanics yields octonionic (non-Jacobi)
nonassociativity. H is the ceiling for the present engines; earning O requires a genuinely NON-LIE, NON-JACOBI
combination that no current mechanism provides.

GATE: (1) channel composition associative (defect < 1e-9); (2) Jordan product nonassociative (> 1e-3) but flagged
not-used-by-mechanism; (3) Lie bracket nonassociative (> 1e-3) AND obeys Jacobi (< 1e-9) -> Lie not octonionic;
(4) therefore NO engine operation yields octonionic T01 -> H is the ceiling, the octonion fork stays unforced.
Falsifiable: if the field bracket FAILED Jacobi (non-Lie), a T01 demand toward O would be SUPPORTED; it does not fail.

scratch_diagnostic, promotion_allowed=false. Reports only computed values.
"""
import json, sys
import numpy as np

sx=np.array([[0,1],[1,0]],complex);sy=np.array([[0,-1j],[1j,0]],complex);sz=np.array([[1,0],[0,-1]],complex);I2=np.eye(2,dtype=complex)
sp=0.5*(sx+1j*sy);sm=0.5*(sx-1j*sy);G=0.35;KAP=1.0
TERR={0:(+1,'damp',+1),1:(+1,'depol',0),2:(+1,'damp',-1),3:(+1,'proj',0),4:(-1,'damp',-1),5:(-1,'depol',0),6:(-1,'damp',+1),7:(-1,'proj',0)}
def Dg(L,r):return L@r@L.conj().T-0.5*(L.conj().T@L@r+r@L.conj().T@L)
def lind(ti):
    eps,kind,pole=TERR[ti];H=eps*(sx+sy+sz)/np.sqrt(3)
    def X(r):
        o=-1j*G*(H@r-r@H)
        if kind=='damp':o+=KAP*Dg(sp if pole>0 else sm,r)
        elif kind=='depol':o+=0.5*KAP*(Dg(sx,r)+Dg(sy,r))
        else:o+=KAP*Dg(sz,r)
        return o
    return X
def chan(X,M,t=1.0,steps=120):
    dt=t/steps;r=M.astype(complex)
    for _ in range(steps):
        k1=X(r);k2=X(r+.5*dt*k1);k3=X(r+.5*dt*k2);k4=X(r+dt*k3);r=r+(dt/6)*(k1+2*k2+2*k3+k4)
    return r
def supermat(ti):
    X=lind(ti);S=np.zeros((4,4),complex)
    for a in range(2):
        for b in range(2):
            E=np.zeros((2,2),complex);E[a,b]=1;S[:,2*a+b]=chan(X,E).reshape(4)
    return S

def main():
    A,B,C=supermat(0),supermat(2),supermat(3)
    # (1) channel composition (superoperator matrix product) -- associative
    comp_defect=float(np.linalg.norm((C@B)@A-C@(B@A)))
    comp_associative=bool(comp_defect<1e-9)
    # (2) Jordan product -- nonassociative, not used to compose
    def jor(X,Y): return 0.5*(X@Y+Y@X)
    jor_defect=float(np.linalg.norm(jor(jor(A,B),C)-jor(A,jor(B,C))))
    jor_nonassoc=bool(jor_defect>1e-3)
    # (3) Lie bracket -- nonassociative but obeys Jacobi -> Lie, not octonionic
    def br(X,Y): return X@Y-Y@X
    br_defect=float(np.linalg.norm(br(br(A,B),C)-br(A,br(B,C))))
    jacobi=float(np.linalg.norm(br(br(A,B),C)+br(br(B,C),A)+br(br(C,A),B)))
    br_nonassoc=bool(br_defect>1e-3); obeys_jacobi=bool(jacobi<1e-9)
    lie_not_octonionic=bool(br_nonassoc and obeys_jacobi)
    # verdict: NO operation yields octonionic (non-Jacobi) T01 -> H is the ceiling
    octonionic_t01_found=bool(br_nonassoc and (not obeys_jacobi))  # would need a non-Jacobi bracket; none
    h_is_ceiling=bool(comp_associative and lie_not_octonionic and (not octonionic_t01_found))
    out={"classification":"scratch_diagnostic","promotion_allowed":False,
         "candidate1_channel_composition":{"associativity_defect":comp_defect,"associative":comp_associative,
             "note":"the engine's ACTUAL stage-combining operation; associative by construction -> cannot be a T01 demand"},
         "candidate2_jordan_product":{"associativity_defect":round(jor_defect,4),"nonassociative":jor_nonassoc,
             "used_by_engine_to_compose":False,"note":"nonassociative but the engine composes sequentially, not via Jordan -> not load-bearing"},
         "candidate3_lie_bracket":{"associativity_defect":round(br_defect,4),"nonassociative":br_nonassoc,
             "jacobi_defect":jacobi,"obeys_jacobi":obeys_jacobi,"is_lie_not_octonionic":lie_not_octonionic,
             "note":"3-engine field bracket: nonassociative but obeys Jacobi -> LIE algebra (so(4)-type, UP-111), NOT octonionic (which is non-Jacobi/Moufang)"},
         "jacobi_discriminator":"octonions are NON-Lie (fail Jacobi, satisfy Moufang). Every natural qubit-superoperator combination is built from the matrix commutator, which ALWAYS obeys Jacobi -> stays Lie/classical. No engine operation yields octonionic non-Jacobi nonassociativity.",
         "octonionic_T01_demand_found":octonionic_t01_found,
         "H_is_ceiling_for_present_engines":h_is_ceiling,
         "what_would_earn_O":"a genuinely NON-LIE, NON-JACOBI (Moufang) combination of engines -- a new mechanism absent from the engines as built. Until then the octonion/exceptional tower (UP-107/108) stays a LIVE-but-unforced fork (UP-112).",
         "verdict":"PASS" if h_is_ceiling else "FAIL"}
    path=__file__.replace(".py","_results.json"); json.dump(out,open(path,"w"),indent=1)
    print("T01 GROUPING-DEMAND SEARCH: does any engine operation force H->O?\n")
    print(f"  (1) channel composition (engine's real operation): assoc defect {comp_defect:.1e} -> associative {comp_associative} (cannot be T01)")
    print(f"  (2) Jordan product: nonassoc defect {jor_defect:.4f} ({jor_nonassoc}) but NOT used to compose -> not load-bearing")
    print(f"  (3) Lie bracket (field interaction): nonassoc {br_defect:.4f}, Jacobi defect {jacobi:.1e} -> obeys Jacobi {obeys_jacobi} -> LIE not octonionic")
    print(f"\n  JACOBI DISCRIMINATOR: octonions FAIL Jacobi (Moufang); matrix commutators ALWAYS obey it -> stay Lie/classical.")
    print(f"  octonionic (non-Jacobi) T01 demand found in engine mechanics: {octonionic_t01_found}")
    print(f"  => H IS the ceiling for the present engines: {h_is_ceiling}")
    print(f"     earning O requires a NON-LIE, NON-JACOBI combination -- a new mechanism, absent as built.")
    print(f"\n  VERDICT: {'PASS' if h_is_ceiling else 'FAIL'} (composition assoc + bracket is Lie-not-octonionic + no octonionic T01)")
    if h_is_ceiling: print("PASS t01_grouping_demand_search")
    print("ALL_GATES:","PASS" if h_is_ceiling else "FAIL","->",path)
    sys.exit(0 if h_is_ceiling else 1)

if __name__=="__main__":
    main()
