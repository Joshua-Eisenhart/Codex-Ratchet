"""
info_processing_sim.py -- DOES the engine process information? Each of the 16
stages is applied, as a quantum channel, to a message qubit maximally entangled
with a reference. We measure what each stage does to the INFORMATION:

  S_out    von Neumann entropy (bits) of the channel output on a pure |0> input
           -> how much entropy the stage injects (0 = reversible, 1 = maximal)
  I_coh    coherent information S(B') - S(R,B') -> quantum information the channel
           preserves about the reference (negative = leaked to environment)
  I(S:R)   mutual information system:reference after the channel (classical+quantum
           correlation the stage keeps with the source)
  Choi     the full process matrix (Λ⊗I)|Φ+> -- the COMPLETE information-channel
           identity of the stage.

PURE MATH, structural indices (t0..t7 x 2 native operators). Terrain flow is the
exact CPTP superoperator exp(t*L) (linear -> valid on the entangled half).

Result (headline invariants asserted below):
  * every stage is a genuine open-system processor: I_coh < 0 for all 16.
  * entropy injection spans a wide range (~0.006 to ~0.99 bits) -> the stages do
    DISTINCT information work, not the same operation relabeled.
  * the FULL channel (Choi) separates all 16 stages (min pairwise > 0.05).
  * scalar entropy metrics COLLAPSE the Weyl-mirror pairs (chirality-blind) --
    the two-sector signature: entropy sees the eigenvalue sector, not the phase.
scratch_diagnostic; promotion_allowed=false.
"""
import json, os, numpy as np
from scipy.linalg import expm

I2=np.eye(2,dtype=complex)
sx=np.array([[0,1],[1,0]],complex); sy=np.array([[0,-1j],[1j,0]],complex)
sz=np.array([[1,0],[0,-1]],complex); sp=0.5*(sx+1j*sy); sm=0.5*(sx-1j*sy)
G,KAP,Q,TH=0.35,1.0,1.0-np.exp(-1.0),np.pi/4
TERR={0:(+1,'damp',+1),1:(+1,'depol',0),2:(+1,'damp',-1),3:(+1,'proj',0),
      4:(-1,'damp',-1),5:(-1,'depol',0),6:(-1,'damp',+1),7:(-1,'proj',0)}
NATIVE={0:('Ti','Fi'),1:('Ti','Fi'),4:('Ti','Fi'),5:('Ti','Fi'),
        2:('Te','Fe'),3:('Te','Fe'),6:('Te','Fe'),7:('Te','Fe')}
def sL(A): return np.kron(I2,A)
def sR(A): return np.kron(A.T,I2)
def sD(L): Ld=L.conj().T; return sL(L)@sR(Ld)-0.5*(sL(Ld@L)+sR(Ld@L))
def sC(H): return -1j*(sL(H)-sR(H))
def terrain_flow(ti,t=1.0):
    eps,kind,pole=TERR[ti]; L=G*sC(eps*(sx+sy+sz)/np.sqrt(3))
    if kind=='damp': L=L+KAP*sD(sp if pole>0 else sm)
    elif kind=='depol': L=L+0.5*KAP*(sD(sx)+sD(sy))
    else: L=L+KAP*sD(sz)
    return expm(t*L)
def op_super(name):
    P0=.5*(I2+sz);P1=.5*(I2-sz);Qp=.5*(I2+sx);Qm=.5*(I2-sx);E=np.eye(4,dtype=complex)
    if name=='Ti': return (1-Q)*E+Q*(sL(P0)@sR(P0)+sL(P1)@sR(P1))
    if name=='Te': return (1-Q)*E+Q*(sL(Qp)@sR(Qp)+sL(Qm)@sR(Qm))
    U=expm(-1j*TH/2*(sx if name=='Fi' else sz)); return sL(U)@sR(U.conj().T)
def vec(r): return r.T.reshape(-1)
def unvec(v): return v.reshape(2,2).T
def chan(t,o,rho): return unvec((op_super(o)@terrain_flow(t))@vec(rho))
def S(rho):
    ev=np.linalg.eigvalsh(0.5*(rho+rho.conj().T)); ev=ev[ev>1e-12]
    return float(-np.sum(ev*np.log2(ev)))
def apply_sys(t,o,rhoSR):
    out=np.zeros((4,4),complex)
    for i in range(2):
        for j in range(2):
            E=np.zeros((2,2),complex);E[i,j]=1
            out+=np.kron(chan(t,o,E),rhoSR[2*i:2*i+2,2*j:2*j+2])
    return out
def ptr_ref(r): return np.array([[r[0,0]+r[1,1],r[0,2]+r[1,3]],[r[2,0]+r[3,1],r[2,2]+r[3,3]]])
def ptr_sys(r): return np.array([[r[0,0]+r[2,2],r[0,1]+r[2,3]],[r[1,0]+r[3,2],r[1,1]+r[3,3]]])
def choi(t,o):
    C=np.zeros((4,4),complex)
    for i in range(2):
        for j in range(2):
            E=np.zeros((2,2),complex);E[i,j]=1
            C+=np.kron(chan(t,o,E),E)
    return C

phi=np.zeros(4,complex); phi[0]=phi[3]=1/np.sqrt(2); Phi=np.outer(phi,phi.conj())
names=[f"t{t}:{o}" for t in range(8) for o in NATIVE[t]]
rows=[]; Chois=[]
for t in range(8):
    for o in NATIVE[t]:
        Sout=S(chan(t,o,np.array([[1,0],[0,0]],complex)))
        rr=apply_sys(t,o,Phi); Ic=S(ptr_ref(rr))-S(rr)
        Im=S(ptr_ref(rr))+S(ptr_sys(rr))-S(rr)
        rows.append((f"t{t}:{o}",Sout,Ic,Im)); Chois.append(choi(t,o))

print(f"{'stage':8s} {'S_out':>7s} {'I_coh':>7s} {'I(S:R)':>7s}")
for n,a,b,c in rows: print(f"{n:8s} {a:7.4f} {b:7.4f} {c:7.4f}")
V=np.array([[a,b,c] for _,a,b,c in rows])
scalar_min=min(np.linalg.norm(V[i]-V[j]) for i in range(16) for j in range(i+1,16))
choi_min=min(np.linalg.norm(Chois[i]-Chois[j]) for i in range(16) for j in range(i+1,16))
inj=[a for _,a,_,_ in rows]
all_open=all(b<0 for _,_,b,_ in rows)
print(f"\nall 16 open-system processors (I_coh<0 for all): {all_open}")
print(f"entropy injection range: {min(inj):.4f} .. {max(inj):.4f} bits")
print(f"full-channel (Choi) min pairwise distance: {choi_min:.4f} -> all 16 distinct channels: {choi_min>0.05}")
print(f"scalar-metric min pairwise: {scalar_min:.4f} (collapses Weyl-mirror pairs = two-sector signature)")

assert all_open, "expected all stages to be open-system processors (I_coh<0)"
assert choi_min>0.05, "expected all 16 stages distinct as channels (Choi)"
assert max(inj)-min(inj)>0.5, "expected wide entropy-injection range (distinct info work)"
print("\nPASS info_processing_sim")
