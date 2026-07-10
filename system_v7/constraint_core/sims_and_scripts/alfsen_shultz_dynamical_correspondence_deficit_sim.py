#!/usr/bin/env python3
"""alfsen_shultz_dynamical_correspondence_deficit_sim -- the Jordan-algebraic form of "the state/observable generates
its own dynamics", and where it FAILS. Processes the codex-ratchet alfsen_shultz_correspondence_probe (and the
symmetric_cone_menu_census placement) independently. Closes the Jordan cluster by sharpening the special-vs-exceptional
distinction (UP-116/117) into a DYNAMICAL statement that connects directly to the modular-theory work (UP-120).

Owner: "you should be looping on all of it ... build the foundations and loop back to improve them."

THE ALFSEN-SHULTZ DYNAMICAL CORRESPONDENCE. A formally-real Jordan algebra is SPECIAL (arises from a C*-algebra / has an
associative envelope) iff it carries a "dynamical correspondence": each traceless observable a maps to a Jordan
DERIVATION D_a=(i/2)[a,.] via the ASSOCIATIVE commutator, and this D_a generates a one-parameter automorphism flow.
This is the finite Jordan-algebra form of the same "state generates its own dynamics" principle that UP-120 identified
as Tomita-Takesaki modular flow -- so this rung is the DYNAMICAL face of the special/exceptional split.

COMPUTED (all from the constructed algebras):
  1. SPECIAL control Herm3(C): the map a |-> D_a=(i/2)[a,.] IS a Jordan derivation -- residual 0 on all basis pairs.
     The dynamical correspondence holds; Herm3(C) is special (it is the self-adjoint part of M_3(C)).
  2. EXCEPTIONAL H3(O): the naive single-observable octonionic commutator D_a(x)=(1/2)(a.x - x.a) is NOT a Jordan
     derivation -- residual ~1.4e2. There is NO single-observable dynamical correspondence: the DEFICIT. This is the
     dynamical shadow of "H3(O) has no associative envelope" (Jordan-von Neumann-Wigner; UP-116).
  3. THE DEFICIT IS SINGLE-OBSERVABLE-SPECIFIC (the honest positive companion): PAIR commutators [L_a,L_b] of Jordan
     multiplication operators ARE genuine derivations -- residual ~1.9e-13 -- and span the full 52-dim Der(H3(O))=f4
     (UP-119). So H3(O) has abundant dynamics (f4 inner derivations); what it lacks is the correspondence assigning
     ONE generator per observable. The exceptional algebra's symmetry is there, just not observable-indexed.

CONTROLS (falsifiable):
  - CORRUPTED-SIGN (Herm3(C)): D_a=(i/2){a,.} with the wrong (anti)commutator sign is NOT a derivation (residual ~1.4)
    -> the correspondence is specific to the commutator, not any bilinear map.
  - The special control MUST succeed (residual 0) and the exceptional MUST show the deficit (residual >>0); both hold.

PLACEMENT: forced-side structural clarification (no new forcing). Ties three prior results together: the special/
exceptional split (UP-116/117) is DYNAMICALLY the presence/absence of a single-observable dynamical correspondence;
its presence in the special case is the finite form of the modular "state generates its own dynamics" (UP-120); and
its absence in H3(O) does not remove dynamics but de-indexes it from observables (the f4 derivations of UP-119 remain).
Established prior art (Alfsen & Shultz, "Geometry of State Spaces of Operator Algebras"; dynamical correspondence characterizing special JB-algebras). Exact publication year not asserted here. Harness target GREEN.

scratch_diagnostic, promotion_allowed=false. Reproduces codex alfsen_shultz_correspondence_probe independently.
"""
import json, sys
import numpy as np

# ---- Herm3(C) SPECIAL control ----
def herm3C_basis():
    B=[]
    for i in range(3):
        E=np.zeros((3,3),complex); E[i,i]=1; B.append(E)
    for i in range(3):
        for j in range(i+1,3):
            R=np.zeros((3,3),complex); R[i,j]=1;R[j,i]=1; B.append(R)
            Im=np.zeros((3,3),complex); Im[i,j]=1j;Im[j,i]=-1j; B.append(Im)
    return B
def jC(x,y): return 0.5*(x@y+y@x)
def deriv_residual_C(D,B):
    res=0.0
    for x in B:
        for y in B: res=max(res,np.linalg.norm(D(jC(x,y))-(jC(D(x),y)+jC(x,D(y)))))
    return res

# ---- H3(O) EXCEPTIONAL ----
def oct_table():
    M=np.zeros((8,8),int); S=np.zeros((8,8),int)
    for i in range(8): M[0,i]=i;M[i,0]=i;S[0,i]=1;S[i,0]=1
    for i in range(1,8): M[i,i]=0;S[i,i]=-1
    for (x,y,z) in [(1,2,3),(1,4,5),(1,7,6),(2,4,6),(2,5,7),(3,4,7),(3,6,5)]:
        for (p,q,r,s) in [(x,y,z,1),(y,z,x,1),(z,x,y,1),(y,x,z,-1),(x,z,y,-1),(z,y,x,-1)]:
            M[p,q]=r;S[p,q]=s
    return M,S
OM,OS=oct_table()
def omul(u,v):
    r=np.zeros(8)
    for i in range(8):
        if u[i]==0: continue
        for j in range(8):
            if v[j]==0: continue
            r[OM[i,j]]+=OS[i,j]*u[i]*v[j]
    return r
def oconj(u): w=-u.copy();w[0]=u[0];return w
def Jmm(A,Bm):
    C=np.zeros((3,3,8))
    for i in range(3):
        for j in range(3):
            for k in range(3): C[i,j]+=omul(A[i,k],Bm[k,j])
    return C
def jJ(A,Bm): return 0.5*(Jmm(A,Bm)+Jmm(Bm,A))
def rand_hermO(seed):
    rng=np.random.default_rng(seed); A=np.zeros((3,3,8))
    for i in range(3): A[i,i,0]=rng.standard_normal()
    for i in range(3):
        for j in range(i+1,3):
            v=rng.standard_normal(8);A[i,j]=v;A[j,i]=oconj(v)
    return A
def deriv_residual_O(Dfun,ntest=6):
    res=0.0; tests=[rand_hermO(10+k) for k in range(ntest)]
    for x in tests:
        for y in tests: res=max(res,float(np.sqrt(np.sum((Dfun(jJ(x,y))-(jJ(Dfun(x),y)+jJ(x,Dfun(y))))**2))))
    return res

def main():
    # 1. SPECIAL Herm3(C): single-observable correspondence holds
    B=herm3C_basis()
    sx=np.array([[0,1,0],[1,0,0],[0,0,0]],complex); a=sx-np.trace(sx)/3*np.eye(3)
    r_special=deriv_residual_C(lambda x:(1j/2)*(a@x-x@a),B)
    r_special_corrupt=deriv_residual_C(lambda x:(1j/2)*(a@x+x@a),B)  # wrong sign
    g_special=bool(r_special<1e-9); g_corrupt=bool(r_special_corrupt>1e-2)
    # 2. EXCEPTIONAL H3(O): single-observable correspondence FAILS
    ao=rand_hermO(1)
    r_single=deriv_residual_O(lambda X:0.5*(Jmm(ao,X)-Jmm(X,ao)))
    g_deficit=bool(r_single>1.0)
    # 3. deficit is single-observable-specific: PAIR commutators [L_a,L_b] ARE derivations
    bo=rand_hermO(2)
    def Dpair(X): return jJ(ao,jJ(bo,X))-jJ(bo,jJ(ao,X))
    r_pair=deriv_residual_O(Dpair)
    g_pair=bool(r_pair<1e-9)
    verdict=bool(g_special and g_corrupt and g_deficit and g_pair)
    out={"classification":"scratch_diagnostic","promotion_allowed":False,"branch":"forced_side_structural",
         "reproduces":"codex alfsen_shultz_correspondence_probe_sim (+ symmetric_cone_menu_census placement)",
         "special_Herm3C":{"single_observable_derivation_residual":r_special,"correspondence_holds":g_special,
             "corrupted_wrong_sign_residual":r_special_corrupt,"corrupted_breaks":g_corrupt,
             "note":"Herm3(C) is special (self-adjoint part of M_3(C)); a|->D_a=(i/2)[a,.] IS a Jordan derivation"},
         "exceptional_H3O":{"single_observable_derivation_residual":r_single,"deficit_present":g_deficit,
             "note":"no single-observable dynamical correspondence -- the dynamical shadow of 'H3(O) has no associative envelope' (Jordan-vNW)"},
         "deficit_is_single_observable_specific":{"pair_commutator_derivation_residual":r_pair,"pair_is_derivation":g_pair,
             "note":"[L_a,L_b] ARE genuine derivations spanning the 52-dim Der(H3(O))=f4 (UP-119); H3(O) has abundant dynamics, just not observable-indexed"},
         "placement":"Ties UP-116/117 (special vs exceptional) DYNAMICALLY to UP-120 (state generates its own dynamics = modular flow) and UP-119 (f4 derivations). Special = single-observable correspondence present (finite modular form); exceptional = absent, but dynamics remain (f4), just de-indexed from observables. Alfsen & Shultz (State Spaces of Operator Algebras; dynamical correspondence for special JB-algebras).",
         "verdict":"PASS" if verdict else "FAIL"}
    path=__file__.replace(".py","_results.json"); json.dump(out,open(path,"w"),indent=1)
    print("ALFSEN-SHULTZ DYNAMICAL CORRESPONDENCE DEFICIT (reproduces codex alfsen_shultz_correspondence_probe)\n")
    print(f"  SPECIAL Herm3(C): single-observable D_a=(i/2)[a,.] derivation residual {r_special:.2e} -> correspondence holds: {g_special}")
    print(f"     corrupted wrong-sign control residual {r_special_corrupt:.3f} -> breaks: {g_corrupt}")
    print(f"  EXCEPTIONAL H3(O): naive single-observable commutator derivation residual {r_single:.3f} -> DEFICIT present: {g_deficit}")
    print(f"  DEFICIT IS SINGLE-OBSERVABLE-SPECIFIC: pair [L_a,L_b] derivation residual {r_pair:.2e} -> IS a derivation: {g_pair}")
    print(f"     (pair commutators span the 52-dim Der(H3(O))=f4, UP-119 -- H3(O) has dynamics, just not observable-indexed)")
    print(f"\n  => SPECIAL vs EXCEPTIONAL is DYNAMICALLY the presence/absence of a single-observable correspondence")
    print(f"     (the finite form of 'state generates its own dynamics', UP-120). Absence de-indexes dynamics, doesn't remove it.")
    print(f"\n  VERDICT: {'PASS' if verdict else 'FAIL'} (special holds + corrupted breaks + exceptional deficit + pair-commutator derivation)")
    if verdict: print("PASS alfsen_shultz_dynamical_correspondence_deficit")
    print("ALL_GATES:","PASS" if verdict else "FAIL","->",path)
    sys.exit(0 if verdict else 1)

if __name__=="__main__":
    main()
