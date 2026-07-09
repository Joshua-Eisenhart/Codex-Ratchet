#!/usr/bin/env python3
"""exceptional_lie_ratchet_sim -- the exceptional Lie algebras as a ratchet over the octonionic carrier. Sits directly
on top of jordan_octonion_observable_rung_sim: that rung forced octonions -> Jordan observables -> H_3(O) (Albert
algebra). This sim shows the SYMMETRY-GROUP shadow of that same ladder is the exceptional chain, ordered by nested
structure.

Owner frame (verbatim): "so g2 ratchets to f4? the exceptional lie algebras all have to be processed in the ratchet.
not sure order."

ANSWER (derived, not asserted): the order is G2 -> F4 -> E6 -> E7 -> E8, each the symmetry of ONE additional layer of
structure built on the SAME octonions (shortest-leaps-up):
  G2 = Aut(O)          = Der(octonions)                         dim 14  -- symmetry of the CARRIER
  F4 = Aut(H_3(O))     = Der(Albert algebra)                    dim 52  -- symmetry of the OBSERVABLE (Jordan) algebra
  E6 = str(H_3(O))     = Der + L_a(traceless)                   dim 78  -- symmetry of the CUBIC (determinant) form
  E7 = conf(H_3(O))    = Freudenthal triple system              dim 133 -- CONFORMAL level (cited, not derived here)
  E8 = magic-square corner                                      dim 248 -- FULL structure (cited, not derived here)

G2 -> F4 is EXACTLY the symmetry image of the O -> H_3(O) step: a G2 derivation of O, applied entrywise to the
octonionic off-diagonals of a Hermitian 3x3 matrix, IS an F4 derivation of H_3(O). So the carrier->observable ratchet
and the G2->F4 ratchet are the SAME step seen through automorphisms.

DERIVED FROM SCRATCH here (valid octonions, Fano-plane table): dim g2=14, dim f4=52, dim e6=78, and the G2 c F4
embedding (entrywise-extended derivation has zero Jordan-derivation defect). CITED from the Freudenthal-Tits magic
square (NOT derived): e7=133, e8=248. The derivation boundary is marked explicitly; the gate does not claim to have
built E7/E8.

GATE: the three derived dimensions must match (14/52/78) AND the G2 c F4 embedding must hold (defect < 1e-9) AND the
containment chain must be strictly increasing (14<52<78<133<248). Falsifiable: a wrong octonion table gives wrong
Der-dims; a non-derivation entrywise map gives nonzero Jordan defect.

scratch_diagnostic, promotion_allowed=false. Reports only computed values; E7/E8 flagged cited.
"""
import json, sys
import numpy as np

def build_octonion_table():
    tri=[(1,2,3),(1,4,5),(1,7,6),(2,4,6),(2,5,7),(3,4,7),(3,6,5)]
    sign=np.zeros((8,8),int); idx=np.zeros((8,8),int)
    for i in range(8):
        sign[0,i]=1; idx[0,i]=i; sign[i,0]=1; idx[i,0]=i
    for i in range(1,8): sign[i,i]=-1; idx[i,i]=0
    for (a,b,c) in tri:
        for (x,y,z) in [(a,b,c),(b,c,a),(c,a,b)]:
            sign[x,y]=1; idx[x,y]=z; sign[y,x]=-1; idx[y,x]=z
    return sign,idx
SIGN,IDX=build_octonion_table()
def omul(u,v):
    w=np.zeros(8)
    for i in np.nonzero(u)[0]:
        for j in np.nonzero(v)[0]: w[IDX[i,j]]+=SIGN[i,j]*u[i]*v[j]
    return w
def oconj(a): y=a.copy(); y[1:]*=-1; return y

def dim_g2():
    M=np.zeros((8,8,8))
    for i in range(8):
        for j in range(8): M[IDX[i,j],i,j]+=SIGN[i,j]
    rows=[]
    for i in range(8):
        for j in range(8):
            for k in range(8):
                row=np.zeros((8,8))
                for a in range(8): row[a,i]+=M[k,a,j]; row[a,j]+=M[k,i,a]
                for b in range(8): row[k,b]-=M[b,i,j]
                rows.append(row.flatten())
    for a in range(8):
        r=np.zeros((8,8)); r[a,0]=1; rows.append(r.flatten())
    A=np.array(rows); return 64-np.linalg.matrix_rank(A,tol=1e-9)

def albert_basis():
    B=[]
    for i in range(3):
        m=np.zeros((3,3,8)); m[i,i,0]=1.0; B.append(m)
    for (i,j) in [(0,1),(0,2),(1,2)]:
        for a in range(8):
            m=np.zeros((3,3,8)); e=np.zeros(8); e[a]=1.0; m[i,j]=e; m[j,i]=oconj(e); B.append(m)
    return B
def mm(A,C):
    R=np.zeros((3,3,8))
    for i in range(3):
        for j in range(3):
            s=np.zeros(8)
            for k in range(3): s+=omul(A[i,k],C[k,j])
            R[i,j]=s
    return R
def jor(A,C): return 0.5*(mm(A,C)+mm(C,A))

def structure_consts(B):
    N=len(B); Bmat=np.array([b.flatten() for b in B]).T
    S=np.zeros((N,N,N))
    for i in range(N):
        for j in range(N):
            x,*_=np.linalg.lstsq(Bmat,jor(B[i],B[j]).flatten(),rcond=None); S[:,i,j]=x
    return S

def dim_f4_and_e6():
    B=albert_basis(); N=27; S=structure_consts(B)
    rows=[]
    for i in range(N):
        for j in range(i,N):
            for k in range(N):
                row=np.zeros((N,N))
                for a in range(N): row[a,i]+=S[k,a,j]; row[a,j]+=S[k,i,a]
                for b in range(N): row[k,b]-=S[b,i,j]
                rows.append(row.flatten())
    f4=N*N-np.linalg.matrix_rank(np.array(rows),tol=1e-8)
    def Lmat(ai):
        Lm=np.zeros((N,N))
        for j in range(N):
            acc=np.zeros(N)
            for i in range(N): acc+=ai[i]*S[:,i,j]
            Lm[:,j]=acc
        return Lm
    Ls=[]
    for k in range(3,N):
        a=np.zeros(N); a[k]=1.0; Ls.append(Lmat(a).flatten())
    for (p,q) in [(0,1),(1,2)]:
        a=np.zeros(N); a[p]=1.0; a[q]=-1.0; Ls.append(Lmat(a).flatten())
    rankL=np.linalg.matrix_rank(np.array(Ls),tol=1e-8)
    return int(f4),int(f4+rankL),int(rankL)

def g2_embeds_in_f4():
    M=np.zeros((8,8,8))
    for i in range(8):
        for j in range(8): M[IDX[i,j],i,j]+=SIGN[i,j]
    rows=[]
    for i in range(8):
        for j in range(8):
            for k in range(8):
                row=np.zeros((8,8))
                for a in range(8): row[a,i]+=M[k,a,j]; row[a,j]+=M[k,i,a]
                for b in range(8): row[k,b]-=M[b,i,j]
                rows.append(row.flatten())
    for a in range(8):
        r=np.zeros((8,8)); r[a,0]=1; rows.append(r.flatten())
    _,_,Vt=np.linalg.svd(np.array(rows)); D0=Vt[-1].reshape(8,8)
    def Dmat(X):
        R=np.zeros((3,3,8))
        for i in range(3):
            for j in range(3): R[i,j]=D0@X[i,j]
        return R
    def rand_herm():
        m=np.zeros((3,3,8))
        for i in range(3):
            m[i,i,0]=np.random.randn()
            for j in range(i+1,3):
                e=np.random.randn(8); m[i,j]=e; m[j,i]=oconj(e)
        return m
    np.random.seed(7); defs=[]
    for _ in range(6):
        X=rand_herm(); Y=rand_herm()
        defs.append(np.linalg.norm(Dmat(jor(X,Y))-(jor(Dmat(X),Y)+jor(X,Dmat(Y)))))
    return float(max(defs))

def main():
    g2=int(dim_g2()); f4,e6,ntraceless=dim_f4_and_e6(); emb=g2_embeds_in_f4()
    e7,e8=133,248  # CITED from the Freudenthal-Tits magic square, not derived
    derived_ok=bool(g2==14 and f4==52 and e6==78 and emb<1e-9)
    chain=[g2,f4,e6,e7,e8]
    chain_increasing=all(chain[i]<chain[i+1] for i in range(4))
    verdict=bool(derived_ok and chain_increasing)
    out={"classification":"scratch_diagnostic","promotion_allowed":False,
         "derived_from_scratch":{"g2_dim":g2,"f4_dim":f4,"e6_dim":e6,"e6_traceless_L_count":ntraceless,
             "g2_embeds_in_f4_jordan_derivation_defect":emb},
         "cited_from_magic_square_not_derived":{"e7_dim":e7,"e8_dim":e8},
         "ratchet_order":"G2(carrier,14) -> F4(observable/Jordan,52) -> E6(cubic form,78) -> E7(conformal,133) -> E8(full,248)",
         "order_forced_by":"nesting of preserved structure over the SAME octonions -- each step the symmetry of one additional layer (carrier -> Jordan product -> cubic form -> triple product -> full); shortest-leaps-up",
         "g2_to_f4_is_carrier_to_observable_image":bool(emb<1e-9),
         "containment_chain_strictly_increasing":chain_increasing,
         "derivation_boundary":"g2,f4,e6 DERIVED from the octonion/Albert structure in-sim; e7,e8 CITED (Freudenthal-Tits magic square). The gate does NOT claim to have built E7/E8.",
         "verdict":"PASS" if verdict else "FAIL"}
    path=__file__.replace(".py","_results.json"); json.dump(out,open(path,"w"),indent=1)
    print("EXCEPTIONAL LIE RATCHET over the octonionic carrier\n")
    print(f"  DERIVED from scratch (valid octonions):")
    print(f"     G2 = Aut(O) = Der(octonions)           dim {g2}  (expect 14)")
    print(f"     F4 = Aut(H3(O)) = Der(Albert algebra)   dim {f4}  (expect 52)")
    print(f"     E6 = str(H3(O)) = Der + L_traceless     dim {e6}  (expect 78; {ntraceless} traceless L's)")
    print(f"     G2 c F4 (entrywise-extended derivation Jordan defect): {emb:.2e}  embeds={emb<1e-9}")
    print(f"  CITED (Freudenthal-Tits magic square, NOT derived here):")
    print(f"     E7 = conformal/Freudenthal-triple        dim {e7}")
    print(f"     E8 = full magic-square corner            dim {e8}")
    print(f"\n  RATCHET ORDER: G2(14) -> F4(52) -> E6(78) -> E7(133) -> E8(248)")
    print(f"     forced by nested structure over the SAME octonions (carrier -> Jordan product -> cubic form -> triple -> full)")
    print(f"     chain strictly increasing: {chain_increasing}")
    print(f"\n  VERDICT: {'PASS' if verdict else 'FAIL'} (g2/f4/e6 derived correct + G2cF4 + chain increasing)")
    if verdict: print("PASS exceptional_lie_ratchet")
    print("ALL_GATES:","PASS" if verdict else "FAIL","->",path)
    sys.exit(0 if verdict else 1)

if __name__=="__main__":
    main()
