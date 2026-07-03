"""
data_processing_sim.py -- the QUANTUM DATA-PROCESSING INEQUALITY: information can only DECREASE
under any physical channel. This is the monotone that makes the co-ratchet DIRECTIONAL and that
einselection / Landauer / Holevo all obey. NOT ToE validation -- established quantum info theory.

Two forms, both verified against random CPTP channels (zero violations):
  (1) Relative-entropy monotonicity (Lindblad-Uhlmann): S(N(rho)||N(sigma)) <= S(rho||sigma)
      for any channel N. States can only become HARDER to tell apart under processing -- the
      master inequality the other info bounds descend from.
  (2) Chain DPI: for A-B with a channel on B (B->C), I(A:C) <= I(A:B). Post-processing cannot
      increase the correlation A already shares.

Ties a=a iff a~b to an ARROW: distinguishability is monotone non-increasing under the engine's
dissipative flow -- the directional co-ratchet. numpy-only. scratch_diagnostic; promotion_allowed=false.
"""
import sys
try:
    import numpy as np
except ImportError as e:
    print(f"SKIP_OPTIONAL data_processing_sim: missing tool ({e.name})"); sys.exit(0)

def S_bits(rho):
    w=np.linalg.eigvalsh(rho); w=w[w>1e-15]; return float(-np.sum(w*np.log2(w)))
def S_rel(rho,sigma):
    wr=np.linalg.eigvalsh(rho); ws,vs=np.linalg.eigh(sigma)
    lr=sum(w*np.log2(w) for w in wr if w>1e-15)
    ls=vs@np.diag([np.log2(w) if w>1e-15 else -1e9 for w in ws])@vs.conj().T
    return float((lr-np.trace(rho@ls)).real)
def dephase(rho,g):
    out=rho.copy(); out[0,1]*=(1-g); out[1,0]*=(1-g); return out
def bloch(nx,ny,nz):
    sx=np.array([[0,1],[1,0]],complex); sy=np.array([[0,-1j],[1j,0]]); sz=np.array([[1,0],[0,-1]],complex)
    n=np.array([nx,ny,nz],float);
    if np.linalg.norm(n)>1: n=n/np.linalg.norm(n)
    return 0.5*(np.eye(2)+n[0]*sx+n[1]*sy+n[2]*sz)
def rand_kraus(d,nk,rng):
    A=rng.normal(size=(d*nk,d))+1j*rng.normal(size=(d*nk,d)); Q,_=np.linalg.qr(A)
    return [Q[k*d:(k+1)*d,:] for k in range(nk)]
def apply_ch(rho,Ks): return sum(K@rho@K.conj().T for K in Ks)
def mutinf(rhoAB,dA,dB):
    rA=np.trace(rhoAB.reshape(dA,dB,dA,dB),axis1=1,axis2=3)
    rB=np.trace(rhoAB.reshape(dA,dB,dA,dB),axis1=0,axis2=2)
    return S_bits(rA)+S_bits(rB)-S_bits(rhoAB)

# (1) monotonicity under increasing dephasing
rho=bloch(0.8,0.2,0.3); sigma=bloch(-0.3,0.1,0.6); before=S_rel(rho,sigma)
seq=[S_rel(dephase(rho,g),dephase(sigma,g)) for g in [0.0,0.25,0.5,0.75,1.0]]
print("(1) S(N(rho)||N(sigma)) vs dephasing g=0..1:", [f"{x:.4f}" for x in seq])
mono_seq = all(seq[i+1]<=seq[i]+1e-9 for i in range(len(seq)-1))

# (2)+(3) random-channel stress test
rng=np.random.default_rng(1); N=400; vd=0; vm=0; minmarg=1e9
for _ in range(N):
    psi=rng.normal(size=4)+1j*rng.normal(size=4); psi/=np.linalg.norm(psi); rhoAB=np.outer(psi,psi.conj())
    Ks=[np.kron(np.eye(2),K) for K in rand_kraus(2,3,rng)]
    IAB=mutinf(rhoAB,2,2); IAC=mutinf(apply_ch(rhoAB,Ks),2,2); minmarg=min(minmarg,IAB-IAC)
    if IAC>IAB+1e-8: vd+=1
    p=rng.normal(size=2)+1j*rng.normal(size=2); p/=np.linalg.norm(p)
    q=rng.normal(size=2)+1j*rng.normal(size=2); q/=np.linalg.norm(q)
    r=0.7*np.outer(p,p.conj())+0.3*np.eye(2)/2; s=0.6*np.outer(q,q.conj())+0.4*np.eye(2)/2
    K1=rand_kraus(2,3,rng)
    if S_rel(apply_ch(r,K1),apply_ch(s,K1))>S_rel(r,s)+1e-8: vm+=1
print(f"(2) chain DPI I(A:C)<=I(A:B): {vd}/{N} violations, min margin {minmarg:.4f}")
print(f"(3) rel-entropy monotonicity: {vm}/{N} violations")

assert mono_seq, "relative entropy must be non-increasing under stronger dephasing"
assert vd==0, "chain DPI must never be violated"
assert vm==0, "relative-entropy monotonicity must never be violated"
assert minmarg>=-1e-8, "DPI margin must be non-negative"
print("\nPASS data_processing_sim")
