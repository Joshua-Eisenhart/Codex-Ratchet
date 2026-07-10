#!/usr/bin/env python3
"""spin9_op2_coset_derived_from_albert_sim -- the one genuine POSITIVE construction in the octonion-fork arc. Derives
dim F4 = 52, the Spin(9) stabilizer of a primitive idempotent (dim 36), and the Cayley-plane coset OP2 = F4/Spin(9)
(dim 16) ENTIRELY from linear algebra over the constructed Albert product J3(O). Nothing is cited as input; every
dimension falls out of nullspaces of the Jordan-Leibniz constraints. Independently reproduces the codex-ratchet
spin9_stabilizer_op2_coset_sim.py.

Owner: "the Spin(9)/OP2 coset one in particular is a genuine positive construction ... which would balance the string
of negatives with a concrete piece of the exceptional structure built rather than just placed."

WHAT IS BUILT (all COMPUTED, none cited):
  1. J3(O): the 27-dim Albert algebra of 3x3 Hermitian octonionic matrices with the Jordan product AoB=(AB+BA)/2
     (octonionic matrix multiplication via the Fano-plane table). Real dim = 3 (diag) + 3x8 (off-diag) = 27.
  2. F4 = Der(J3(O)): a derivation D is a linear map on the 27-dim space obeying the Leibniz rule
     D(AoB)=D(A)oB+AoD(B) for all basis pairs. Stack the Leibniz conditions into a (10206, 729) constraint matrix on
     the 27x27=729 entries of D; its nullspace is f4. COMPUTED: rank 677 -> dim F4 = 729-677 = 52 (on the nose).
  3. Spin(9) = stabilizer of a primitive idempotent e=diag(1,0,0): the D in f4 with D(e)=0. The map f4 -> R^27,
     D|->D(e), has rank 16, so dim(stab) = 52-16 = 36 = dim Spin(9). COMPUTED.
  4. OP2 coset = F4/Spin(9): dim = 52 - 36 = 16 = dim of the Cayley projective plane OP2. COMPUTED as the action rank
     of f4 on e (the orbit/tangent dimension), matching dim OP2 exactly.

CONTROLS (the gate is falsifiable):
  - CORRUPTED FANO: a single upstream sign flip in the octonion table (e1*e2 coefficient of e3 negated) breaks the
    52-gate -- the derivation dimension collapses (the Albert algebra is no longer a Jordan algebra), so the 52 is a
    genuine consequence of the exact octonion structure, not an artifact of the linear-algebra machinery.
  - GENERIC (non-idempotent) diagonal element: stabilizing a generic diag(distinct) element instead of a primitive
    idempotent gives a DIFFERENT stabilizer (dim ~28, coset ~24) -- the 36/16 split is specific to primitive
    idempotents (the points of OP2), not any diagonal element.

HONEST PLACEMENT (the negatives still hold). This is a real, load-bearing POSITIVE construction: the exceptional group
F4, its maximal Spin(9) subgroup, and the Cayley plane all fall out of the Albert product with the correct dimensions.
BUT per UP-112/115/118, J3(O)/F4/OP2 live on the LIVE-BUT-UNFORCED {H,O} branch. The forced qubit engine runs on
H (associative; UP-115 Clifford, UP-118 Lie/Malcev), and nothing in {F01,N01} forces a primitive octonionic idempotent
or the Albert product into existence. So this sim BUILDS a concrete piece of the exceptional tower -- it does not EARN
it as forced. It is the positive counterpart to the negatives: the structure is real and constructible, the demand for
it is still absent from the forced ratchet.

GATE (all legs COMPUTED): (1) dim F4 = 52 on the nose from Der(J3(O)); (2) Spin(9) stabilizer dim = 36; (3) OP2 coset
= 52-36 = 16 = dim OP2; (4) corrupted-Fano breaks the 52-gate; (5) generic non-idempotent gives a different split.

scratch_diagnostic, promotion_allowed=false; UNFORCED-branch construction, no forcing/bridge/Axis0 claim.
"""
import json, sys
import numpy as np

def oct_table(corrupt=False):
    M=np.zeros((8,8),int); S=np.zeros((8,8),int)
    for i in range(8): M[0,i]=i; M[i,0]=i; S[0,i]=1; S[i,0]=1
    for i in range(1,8): M[i,i]=0; S[i,i]=-1
    for (a,b,c) in [(1,2,3),(1,4,5),(1,7,6),(2,4,6),(2,5,7),(3,4,7),(3,6,5)]:
        for (x,y,z,s) in [(a,b,c,1),(b,c,a,1),(c,a,b,1),(b,a,c,-1),(a,c,b,-1),(c,b,a,-1)]:
            M[x,y]=z; S[x,y]=s
    if corrupt: S[1,2]*=-1   # single upstream sign flip: e1*e2 coefficient of e3
    return M,S

def build(corrupt=False):
    OM,OS=oct_table(corrupt)
    def omul(u,v):
        r=np.zeros(8)
        for i in range(8):
            if u[i]==0: continue
            for j in range(8):
                if v[j]==0: continue
                r[OM[i,j]]+=OS[i,j]*u[i]*v[j]
        return r
    def oconj(u): w=-u.copy(); w[0]=u[0]; return w
    def vec_to_J(v):
        d=v[:3]; a=v[3:11]; b=v[11:19]; c=v[19:27]
        J=np.zeros((3,3,8)); J[0,0,0]=d[0];J[1,1,0]=d[1];J[2,2,0]=d[2]
        J[0,1]=a;J[1,0]=oconj(a);J[0,2]=b;J[2,0]=oconj(b);J[1,2]=c;J[2,1]=oconj(c); return J
    def Jmm(A,B):
        C=np.zeros((3,3,8))
        for i in range(3):
            for j in range(3):
                for k in range(3): C[i,j]+=omul(A[i,k],B[k,j])
        return C
    def jordan(A,B): return 0.5*(Jmm(A,B)+Jmm(B,A))
    def J_to_vec(J): return np.concatenate([[J[0,0,0],J[1,1,0],J[2,2,0]],J[0,1],J[0,2],J[1,2]])
    n=27
    basis=[vec_to_J(np.eye(n)[i]) for i in range(n)]
    P=np.zeros((n,n,n))
    for p in range(n):
        for q in range(n): P[p,q]=J_to_vec(jordan(basis[p],basis[q]))
    rows=[]
    for p in range(n):
        for q in range(p,n):
            for i in range(n):
                row=np.zeros(n*n)
                for j in range(n): row[i*n+j]+=P[p,q,j]
                for j in range(n): row[j*n+p]-=P[j,q,i]
                for j in range(n): row[j*n+q]-=P[p,j,i]
                rows.append(row)
    return np.array(rows), n

def main():
    n=27
    Cmat,_=build(corrupt=False)
    U,s,Vt=np.linalg.svd(Cmat)
    rank=int(np.sum(s>1e-8)); f4dim=n*n-rank
    f4_basis=Vt[rank:]
    # Spin(9) stabilizer of primitive idempotent e=diag(1,0,0): action of f4 on e
    cond=np.array([D.reshape(n,n)[:,0] for D in f4_basis])   # (52,27), each f4 gen's D(e)
    coset=int(np.linalg.matrix_rank(cond.T,tol=1e-8)); stab=f4dim-coset
    # control 1: corrupted Fano
    Cc,_=build(corrupt=True)
    sc=np.linalg.svd(Cc,compute_uv=False); f4_corrupt=n*n-int(np.sum(sc>1e-8))
    # control 2: generic non-idempotent diagonal diag(3,2,1) -> stabilizer differs
    gen=np.zeros(n); gen[0]=3.0; gen[1]=2.0; gen[2]=1.0
    # action of f4 on gen: D(gen) = D @ gen (coordinate)
    condg=np.array([D.reshape(n,n)@gen for D in f4_basis])   # (52,27)
    coset_g=int(np.linalg.matrix_rank(condg.T,tol=1e-8)); stab_g=f4dim-coset_g
    g_f4=bool(f4dim==52); g_stab=bool(stab==36); g_coset=bool(coset==16)
    g_corrupt=bool(f4_corrupt!=52); g_generic=bool(coset_g!=16)
    verdict=bool(g_f4 and g_stab and g_coset and g_corrupt and g_generic)
    out={"classification":"scratch_diagnostic","promotion_allowed":False,"branch":"unforced_H_O_branch",
         "reproduces":"system_v7/constraint_core/sims_and_scripts/spin9_stabilizer_op2_coset_sim.py (codex-ratchet)",
         "f4_from_albert":{"constraint_matrix_shape":list(Cmat.shape),"rank":rank,"f4_dimension":f4dim,"on_the_nose_52":g_f4},
         "spin9_stabilizer":{"primitive_idempotent":"e=diag(1,0,0)","stabilizer_dimension":stab,"spin9_dim_36":g_stab},
         "op2_coset":{"formula":"dim(F4)-dim(stabilizer)","coset_dimension":coset,"matches_dim_OP2_16":g_coset},
         "controls":{"corrupted_fano_f4_dim":f4_corrupt,"corrupted_breaks_52":g_corrupt,
             "generic_nonidempotent_coset_dim":coset_g,"generic_nonidempotent_stab_dim":stab_g,"generic_differs":g_generic},
         "honest_placement":"POSITIVE construction: F4 (52), Spin(9) (36), and the Cayley plane OP2 (16) all fall out of the constructed Albert product with the correct dimensions. But J3(O)/F4/OP2 live on the LIVE-BUT-UNFORCED {H,O} branch (UP-112/115/118); the forced qubit engine runs on associative H. This BUILDS a concrete piece of the exceptional tower; it does not EARN it as forced. The positive counterpart to the negatives.",
         "verdict":"PASS" if verdict else "FAIL"}
    path=__file__.replace(".py","_results.json"); json.dump(out,open(path,"w"),indent=1)
    print("SPIN(9)/OP2 COSET DERIVED FROM THE ALBERT PRODUCT (positive construction; reproduces codex spin9_stabilizer_op2_coset)\n")
    print(f"  F4 = Der(J3(O)): constraint matrix {Cmat.shape}, rank {rank} -> dim F4 = {f4dim} (=52 on the nose: {g_f4})")
    print(f"  Spin(9) = stabilizer of primitive idempotent e=diag(1,0,0): dim {stab} (=36: {g_stab})")
    print(f"  OP2 coset = F4/Spin(9) = 52-{stab} = {coset} (= dim OP2 = 16: {g_coset})")
    print(f"  CONTROL corrupted-Fano: dim F4 collapses to {f4_corrupt} (breaks the 52-gate: {g_corrupt})")
    print(f"  CONTROL generic non-idempotent diag(3,2,1): coset {coset_g}, stab {stab_g} (differs from 16/36: {g_generic})")
    print(f"\n  HONEST PLACEMENT: a genuine POSITIVE build of exceptional structure -- but on the UNFORCED {{H,O}} branch.")
    print(f"  Structure is real and constructible; the DEMAND for it is still absent from the forced ratchet (UP-112/115/118).")
    print(f"\n  VERDICT: {'PASS' if verdict else 'FAIL'} (F4=52 + Spin9=36 + coset=16 + corrupted breaks + generic differs)")
    if verdict: print("PASS spin9_op2_coset_derived_from_albert")
    print("ALL_GATES:","PASS" if verdict else "FAIL","->",path)
    sys.exit(0 if verdict else 1)

if __name__=="__main__":
    main()
