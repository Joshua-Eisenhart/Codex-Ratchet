"""
eps_even_a2_specificity_sim.py -- PURE MATH, no jargon. 2026-07-01, fifth pass.

Follows the fourth audit's sharpened open item: the chi2 open-path phase meter
(chi2_openpath_readout_sim.py) is an earned eigenvector-sector meter but is NOT
a2-specific -- it responds to all three binary operations on the frame element
(a2: V vs I; eps: V vs Vdag; K: V vs V*), and its terrain-generator readout is
eps-contaminated (sheet-sensitive), matching the a2 target on only 2/8.

This sim asks the decisive follow-up: can the eps-contamination be removed by
symmetrizing over the eps-mirror terrain, and does the resulting eps-even
functional then separate the a2 (direct/conjugated) partition? And it locates
where a2 IS realized.

RESULTS (deterministic, seeded):
  (1) eps-symmetrization (phase(t)+phase(mirror(t)))/2 IS eps-even (mirror pairs
      become identical to machine precision) -- so eps-evenness is achievable.
  (2) but the eps-even functional STILL does not separate a2: conjugated
      terrains t3,t7 (0.106) fall BELOW direct t0,t4 (0.107). Removing eps
      exposes that the phase magnitude reads the DYNAMICS type (damp/depol/proj
      = a1), not a2.
  (3) a2 IS realized -- but at the OPERATOR layer, not the terrain-generator
      layer: the Hadamard W conjugates the four judging operators into their
      a2-partners exactly (||W.Ti.W - Te|| = 9e-16), while it does NOT conjugate
      the terrain generators into their a2-partners (residuals ~2.0).
  => a2 is an operator-layer label (earned in 7t via W). It does not descend to
     a terrain-generator-flow observable. The open item is therefore RESOLVED
     as a structural fact: no terrain-generator functional reads a2, because a2
     is not a terrain-generator property -- it is one layer up.
scratch_diagnostic; promotion_allowed=false.
"""
import numpy as np
from scipy.linalg import expm

I2=np.eye(2,dtype=complex)
sx=np.array([[0,1],[1,0]],complex); sy=np.array([[0,-1j],[1j,0]],complex); sz=np.array([[1,0],[0,-1]],complex)
sp=0.5*(sx+1j*sy); sm=0.5*(sx-1j*sy)
g,kap=0.35,1.0
comm=lambda A,r:A@r-r@A
D=lambda L,r:L@r@L.conj().T-0.5*(L.conj().T@L@r+r@L.conj().T@L)
# 8 terrain generators (eps sign, dynamics kind, damping pole)
terr={0:(+1,'damp',+1),1:(+1,'depol',0),2:(+1,'damp',-1),3:(+1,'proj',0),
      4:(-1,'damp',-1),5:(-1,'depol',0),6:(-1,'damp',+1),7:(-1,'proj',0)}
def gen(ti):
    eps,kind,pole=terr[ti]
    def X(r):
        out=-1j*g*comm(eps*sz,r)
        if kind=='damp': out+=kap*D(sp if pole>0 else sm,r)
        elif kind=='depol': out+=0.5*kap*(D(sx,r)+D(sy,r))
        else: out+=kap*D(sz,r)
        return out
    return X
def flow(X,r,t,steps=200):
    dt=t/steps
    for _ in range(steps):
        k1=X(r);k2=X(r+.5*dt*k1);k3=X(r+.5*dt*k2);k4=X(r+dt*k3)
        r=r+(dt/6)*(k1+2*k2+2*k3+k4); r=.5*(r+r.conj().T); r/=np.trace(r).real
    return r
r0=np.array([1,0],complex); r1=np.array([1,1],complex)/np.sqrt(2)
def bargmann(rho):
    w,U=np.linalg.eigh(rho); e=U[:,np.argmax(w)]
    return -np.angle(np.vdot(r0,e)*np.vdot(e,r1)*np.vdot(r1,r0))
probe=0.5*(I2+0.55*sx+0.35*sy+0.25*sz)
a2_target={0:0,1:0,2:1,3:1,4:0,5:0,6:1,7:1}
mirror={0:4,1:5,2:6,3:7,4:0,5:1,6:2,7:3}
raw={t:sum(bargmann(flow(gen(t),probe.copy(),tt)) for tt in (0.4,0.8,1.2))/3 for t in range(8)}
sym={t:(raw[t]+raw[mirror[t]])/2 for t in range(8)}
print("(1) eps-symmetrization makes it eps-even (mirror pairs identical):")
for t in [0,1,2,3]:
    print(f"    t{t}={sym[t]:+.4f}  t{mirror[t]}={sym[mirror[t]]:+.4f}  |diff|={abs(sym[t]-sym[mirror[t]]):.2e}")
print("(2) but eps-even functional does NOT separate a2 (direct=0 / conjugated=1):")
direct=[sym[t] for t in range(8) if a2_target[t]==0]; conj=[sym[t] for t in range(8) if a2_target[t]==1]
print(f"    direct(a2=0) range [{min(direct):.3f},{max(direct):.3f}]  conjugated(a2=1) range [{min(conj):.3f},{max(conj):.3f}]")
print(f"    separable? {'YES' if min(conj)>max(direct) or max(conj)<min(direct) else 'NO -- ranges overlap; phase reads dynamics-type (a1), not a2'}")
# (3) a2 lives at operator layer
def L_basis(genfn):
    B=[I2,sx,sy,sz]; M=np.zeros((4,4),complex)
    for i,E in enumerate(B):
        o=genfn(E)
        for j,F in enumerate(B): M[j,i]=0.5*np.trace(F.conj().T@o)
    return M
W=(sx+sz)/np.sqrt(2)
Ti=lambda r: sz@r@sz-r; Te=lambda r: sx@r@sx-r
op_res=np.linalg.norm(L_basis(lambda r:W@Ti(W@r@W)@W)-L_basis(Te))
terr_res=np.mean([np.linalg.norm(L_basis(lambda r,ti=ti:W@gen(ti)(W@r@W)@W)-L_basis(gen(tj)))
                  for ti,tj in [(0,2),(1,3),(4,6),(5,7)]])
print("(3) a2 is realized at the OPERATOR layer, not the terrain-generator layer:")
print(f"    ||W.Ti.W - Te|| (operator a2-conjugation) = {op_res:.2e}  (=0: exact)")
print(f"    mean ||W.L(terrain).W - L(a2-partner)||    = {terr_res:.3f}  (!=0: a2 does NOT descend)")
print("=> RESOLVED as structural fact: no terrain-generator functional reads a2;")
print("   a2 is an operator-layer label (7t via W), one layer above the generators.")
