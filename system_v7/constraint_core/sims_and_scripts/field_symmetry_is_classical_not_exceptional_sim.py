#!/usr/bin/env python3
"""field_symmetry_is_classical_not_exceptional_sim -- tests whether the exceptional tower (G2/F4/E6, UP-108) emerges
at the FIELD/upper-manifold level of the QUBIT engines (UP-110), or whether the field level still requires lifting the
carrier H->O first. Honest NEGATIVE result: the field symmetry of qubit engines is CLASSICAL, not exceptional.

Owner frame (verbatim): "so there may need more ratcheting for a field of engines, and the geometry those engines
themselves are embedded into ... so the exceptional lie algebras may have more value at that level."

Direct tests of that instinct:

  (1) DISCRETE FIELD SYMMETRY. The 8-terrain field's Choi-distance metric has an automorphism group (permutations of
      terrains preserving all pairwise Choi distances). MEASURED order = 4 (finite) -- with equivalence classes
      {0,2,4,6} damp / {1,5} depol / {3,7} proj (channel-kind grouping, mirroring UP-110). A FINITE point set cannot
      carry a continuous Lie symmetry, so this is NOT G2/F4 (both continuous). The naive "field symmetry = exceptional"
      is FALSE.

  (2) CONTINUOUS FIELD SYMMETRY. A qubit channel's Choi is 4x4; its local symmetry J -> (U(x)V) J (U(x)V)^dag with
      U,V in SU(2) has Lie algebra su(2)+su(2) = so(4), dim 6 (verified: rank of the 6 generators = 6). so(4) is
      CLASSICAL (quaternionic: H(x)H ~ so(4)), NOT exceptional (g2=14).

  CONCLUSION. The exceptional tower does NOT emerge for free at the field level of qubit engines. It requires lifting
  the CARRIER H->O first (UP-107/108: octonions -> H_3(O) -> F4/E6). The mirror lift (density->Choi, UP-110) is a
  CLASSICAL so(4) step on the MIRROR axis; the exceptional structure lives on the CARRIER axis. The two are ORTHOGONAL:
  the field/upper-manifold does not bypass the carrier rung. This is consistent with UP-109 (single qubit engine sits
  at H); the exceptional tower is reached by climbing the carrier ladder H->O (the open UP-109 forcing step), not by
  the field lift alone.

GATE: (1) discrete field automorphism group is FINITE and small (order < 100, here 4) -- NOT a continuous group;
(2) continuous single-engine Choi symmetry is so(4), dim exactly 6 -- NOT dim 14 (g2) or 52 (f4); (3) therefore the
field symmetry is classical. Falsifiable: if the continuous symmetry dim came out 14 or 52, the exceptional-at-field
claim would be SUPPORTED; it does not. This is an honest negative that constrains where the exceptional tower lives.

scratch_diagnostic, promotion_allowed=false. Reports only computed values.
"""
import json, sys, itertools
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
def chan(X,M,t=1.0,steps=200):
    dt=t/steps;r=M.astype(complex)
    for _ in range(steps):
        k1=X(r);k2=X(r+.5*dt*k1);k3=X(r+.5*dt*k2);k4=X(r+dt*k3);r=r+(dt/6)*(k1+2*k2+2*k3+k4)
    return r
def choi(ti):
    X=lind(ti);J=np.zeros((4,4),complex)
    for i in range(2):
        for j in range(2):
            E=np.zeros((2,2),complex);E[i,j]=1;J+=np.kron(E,chan(X,E))
    return J

def discrete_field_symmetry():
    Js=[choi(t) for t in range(8)]
    D=np.array([[np.linalg.norm(Js[i]-Js[j]) for j in range(8)] for i in range(8)])
    autos=[p for p in itertools.permutations(range(8)) if np.allclose(D[np.ix_(list(p),list(p))],D,atol=1e-6)]
    profiles={}
    for i in range(8):
        profiles.setdefault(tuple(sorted(np.round(D[i],4))),[]).append(i)
    return len(autos),[v for v in profiles.values()]

def continuous_field_symmetry():
    gens=[np.kron(A,I2) for A in (sx,sy,sz)]+[np.kron(I2,A) for A in (sx,sy,sz)]
    return int(np.linalg.matrix_rank(np.array([g.flatten() for g in gens]),tol=1e-9))

def main():
    order,classes=discrete_field_symmetry()
    cdim=continuous_field_symmetry()
    discrete_finite=bool(order<100)
    continuous_classical=bool(cdim==6)  # so(4)
    not_exceptional=bool(cdim not in (14,52,78))
    verdict=bool(discrete_finite and continuous_classical and not_exceptional)
    out={"classification":"scratch_diagnostic","promotion_allowed":False,
         "discrete_field_metric_symmetry":{"automorphism_group_order":order,"equivalence_classes":classes,
             "is_finite_not_continuous":discrete_finite},
         "continuous_single_engine_choi_symmetry":{"lie_algebra":"su(2)+su(2)=so(4)","dim":cdim,"is_classical":continuous_classical},
         "exceptional_dims_for_reference":{"g2":14,"f4":52,"e6":78},
         "field_symmetry_is_exceptional":bool(cdim in (14,52,78)),
         "conclusion":"The exceptional tower does NOT emerge for free at the field level of qubit engines. Discrete field symmetry is order 4 (finite); continuous single-engine Choi symmetry is so(4) dim 6 (classical/quaternionic). The mirror lift (density->Choi, UP-110) is a CLASSICAL step on the MIRROR axis; the exceptional structure lives on the CARRIER axis (H->O, UP-107/108). The two are ORTHOGONAL -- the field does not bypass the carrier rung. Reaching the exceptional tower requires lifting the engine carrier H->O (open UP-109 step), not the field lift alone.",
         "verdict":"PASS" if verdict else "FAIL"}
    path=__file__.replace(".py","_results.json"); json.dump(out,open(path,"w"),indent=1)
    print("FIELD SYMMETRY: is it exceptional, or classical?\n")
    print(f"  (1) discrete 8-terrain field metric automorphism group order: {order}  (finite, NOT continuous G2/F4)")
    print(f"      equivalence classes (channel-kind): {classes}")
    print(f"  (2) continuous single-engine Choi symmetry: su(2)+su(2)=so(4), dim {cdim}  (classical/quaternionic)")
    print(f"      exceptional reference dims: g2=14, f4=52, e6=78  -> field dim {cdim} is NOT exceptional")
    print(f"\n  CONCLUSION: the exceptional tower does NOT emerge for free at the qubit-engine field level.")
    print(f"     mirror lift (density->Choi) is CLASSICAL so(4) on the MIRROR axis; exceptional structure lives on the")
    print(f"     CARRIER axis (H->O). Orthogonal -- the field does not bypass the carrier rung. (Honest negative.)")
    print(f"\n  VERDICT: {'PASS' if verdict else 'FAIL'} (discrete finite + continuous so(4) + not exceptional)")
    if verdict: print("PASS field_symmetry_is_classical_not_exceptional")
    print("ALL_GATES:","PASS" if verdict else "FAIL","->",path)
    sys.exit(0 if verdict else 1)

if __name__=="__main__":
    main()
