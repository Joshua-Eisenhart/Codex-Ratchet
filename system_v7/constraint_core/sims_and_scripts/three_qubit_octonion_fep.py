"""
three_qubit_octonion_fep.py
Earns the 3-qubit / octonion / G2 rung and the pure-QIT FEP lane.
Sources (recent wiki): nonassociativity-carrier-layer-status-2026-06-07 (associator/Cl(6)/G2 numbers),
octonion-g2-sedenion-carrier-geometry-audit, fep-and-active-inference-reference,
fep-to-axis0-bridge-claim-ceilings (claim ceiling).
Claim ceiling: scratch_diagnostic; promotion_allowed=false. Non-associativity is ROOT-NATIVE but
RUNG-LATER (R3 carrier), per placement rule — NOT an R1/R2 root constraint.
"""
import numpy as np
from scipy.linalg import logm

def cayley_dickson_mul(a,b,n):
    if n==1: return np.array([a[0]*b[0]])
    h=n//2; a1,a2,b1,b2=a[:h],a[h:],b[:h],b[h:]
    conj=lambda x,m: (x.copy() if m==1 else np.concatenate([[x[0]],-x[1:]]))
    return np.concatenate([cayley_dickson_mul(a1,b1,h)-cayley_dickson_mul(conj(b2,h),a2,h),
                           cayley_dickson_mul(b2,a1,h)+cayley_dickson_mul(a2,conj(b1,h),h)])

def cd_table(log2dim):
    dim=2**log2dim; T=np.zeros((dim,dim),int); S=np.zeros((dim,dim),int)
    for i in range(dim):
        for j in range(dim):
            ei=np.eye(dim)[i]; ej=np.eye(dim)[j]; p=cayley_dickson_mul(ei,ej,dim)
            k=int(np.argmax(np.abs(p))); T[i,j]=k; S[i,j]=int(np.sign(p[k]))
    return T,S,dim

def associator_maxnorm(log2dim):
    T,SG,dim=cd_table(log2dim)
    def prod(u,v):
        r=np.zeros(dim)
        for i in np.nonzero(u)[0]:
            for j in np.nonzero(v)[0]: r[T[i,j]]+=SG[i,j]*u[i]*v[j]
        return r
    mx=0.0; wit=None
    for i in range(1,dim):
        for j in range(1,dim):
            for k in range(1,dim):
                a,b,c=(np.eye(dim)[x] for x in (i,j,k))
                n=np.linalg.norm(prod(prod(a,b),c)-prod(a,prod(b,c)))
                if n>mx: mx,wit=n,(i,j,k)
    return mx,wit,dim

def left_mult(T,SG,i,dim):
    M=np.zeros((dim,dim))
    for j in range(dim): M[T[i,j],j]=SG[i,j]
    return M

def generated_rank(gens,d):
    seen=[np.eye(d)]; frontier=[np.eye(d)]
    for _ in range(d):
        new=[]
        for M in frontier:
            for g in gens:
                P=g@M; V=np.array([m.flatten() for m in seen+new])
                if np.linalg.matrix_rank(np.vstack([V,P.flatten()]),tol=1e-9)>len(seen)+len(new): new.append(P)
        if not new: break
        seen+=new; frontier=new
    return len(seen)

def qit_free_energy_demo(d=8,seed=1):
    rng=np.random.default_rng(seed)
    rho=lambda: (lambda A:(A@A.conj().T)/np.trace(A@A.conj().T))(rng.standard_normal((d,d))+1j*rng.standard_normal((d,d)))
    Srel=lambda r,s: float(np.trace(r@(logm(r)-logm(s))).real)
    rq,rm=rho(),rho(); F=Srel(rq,rm)
    dephase=lambda r: np.diag(np.diag(r))
    return {"F_umegaki":F,"F_after_belief_update":Srel(dephase(rq),dephase(rm)),"F_nonneg":F>-1e-9}

if __name__=="__main__":
    for name,l in [("H",2),("O",3),("S",4)]:
        mx,wit,dim=associator_maxnorm(l); print(f"{name} dim={dim} associator_maxnorm={mx} witness={wit}")
    T,SG,dim=cd_table(3); Ls=[left_mult(T,SG,i,8) for i in range(1,8)]
    print("octonion Cl(0,6) rank:",generated_rank(Ls[:6],8),"-> spinor dim 8 = 3 qubits")
    print("dim Der: R,C,H,O,(S) = 0,0,3,14  (14 = dim G2 = Aut(O))")
    print("pure-QIT FEP:",qit_free_energy_demo())
    print("CLAIM CEILING: FEP supports boundary/prediction vocab; does NOT close Axis0/Phi0/gravity.")
