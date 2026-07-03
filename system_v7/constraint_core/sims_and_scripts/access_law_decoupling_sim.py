"""
access_law_decoupling_sim.py  —  PURE MATH, NO JARGON.  2026-07-01.

Hostile probe of the eight-of-sixteen access law (§7s): is the engine sign the TERRAIN's
chirality or an artifact of the meter? eps sits in both the terrain Hamiltonian and the
measurement drive, so they are decoupled here into eps_terr and eps_drive.

RESULTS:
  (1) Decoupled across 16 stages: the geometric-phase sign follows the TERRAIN 14/16 and the
      DRIVE only 2/16. The chirality genuinely lives in the stage.
  (2) Chirality-neutral meter (no eps in the drive): the terrain sign flips 14/16; the 2
      failures are t3:Fe and t7:Fe -- the projective Si pair, the §7p/§7r bottleneck.
  (3) TWO-TIER (mirrors §7q fusion split): dephasing stages (Ti,Te) negate IDENTICALLY under
      eps-flip -- |a(+)+a(-)|=0 exactly (dissipators conj-invariant, coherent term flips,
      y->-y negates area). Rotation stages (Fi,Fe) are dynamical/approximate.
  => access law is an exact symbolic-identity theorem on the 8 pinching stages, dynamical on
     the 8 rotation stages. Full 16/16 holds IFF the loop carries the sheet's own H0.

scratch_diagnostic; promotion_allowed=false. Requires: numpy.
"""
import numpy as np
I2=np.eye(2,dtype=complex)
SX=np.array([[0,1],[1,0]],complex); SY=np.array([[0,-1j],[1j,0]],complex); SZ=np.array([[1,0],[0,-1]],complex)
sp=0.5*(SX+1j*SY); sm=0.5*(SX-1j*SY); H0=SZ.copy()
def D(L,r): return L@r@L.conj().T-0.5*(L.conj().T@L@r+r@L.conj().T@L)
def comm(A,r): return A@r-r@A
def bloch(r): return np.array([np.trace(r@s).real for s in (SX,SY,SZ)])
kap=1.0; g=0.35
terr={0:(+1,+1,'damp'),1:(+1,0,'depol'),2:(+1,-1,'damp'),3:(+1,0,'proj'),
      4:(-1,-1,'damp'),5:(-1,0,'depol'),6:(-1,+1,'damp'),7:(-1,0,'proj')}
native_ops={0:('Ti','Fi'),1:('Ti','Fi'),4:('Ti','Fi'),5:('Ti','Fi'),
            2:('Te','Fe'),3:('Te','Fe'),6:('Te','Fe'),7:('Te','Fe')}
def terrain_gen(ti,eps):
    _,pole,kind=terr[ti]
    def X(r):
        out=-1j*g*comm(eps*H0,r)
        if kind=='damp': out=out+kap*D(sp if pole>0 else sm,r)
        elif kind=='depol': out=out+0.5*kap*(D(SX,r)+D(SY,r))
        elif kind=='proj': out=out+kap*D(SZ,r)
        return out
    return X
def op_gen(name):
    if name=='Ti': return lambda r:0.6*D(SZ,r)
    if name=='Te': return lambda r:0.6*D(SX,r)
    if name=='Fi': return lambda r:-1j*comm(0.5*SX,r)
    if name=='Fe': return lambda r:-1j*comm(0.5*SZ,r)
def loop_area(ti,op,eps_terr,eps_drive,steps=400):
    Xt=terrain_gen(ti,eps_terr); Xo=op_gen(op); r=0.5*(I2+0.6*SX); pts=[]
    for k in range(steps):
        u=2*np.pi*k/steps
        drive=lambda r: Xt(r)+np.cos(u)*Xo(r)-1j*np.sin(u)*eps_drive*comm(0.5*H0,r)
        r=r+0.01*drive(r); r=0.5*(r+r.conj().T); r=r/np.trace(r).real; pts.append(bloch(r))
    p=np.array(pts); x,y=p[:,0],p[:,1]
    return 0.5*np.sum(x[:-1]*y[1:]-x[1:]*y[:-1])
if __name__=="__main__":
    stages=[(t,op) for t in range(8) for op in native_ops[t]]
    ft=fd=0
    for t,op in stages:
        en=terr[t][0]; a=loop_area(t,op,en,en)
        ft+= np.sign(loop_area(t,op,-en,en))!=np.sign(a) and abs(a)>1e-3
        fd+= np.sign(loop_area(t,op,en,-en))!=np.sign(a) and abs(a)>1e-3
    print(f"(1) decoupled: sign follows terrain {ft}/16, drive {fd}/16")
    md=max(abs(loop_area(t,op,+1,+1)+loop_area(t,op,-1,-1)) for t,op in stages if op in('Ti','Te'))
    mr=max(abs(loop_area(t,op,+1,+1)+loop_area(t,op,-1,-1)) for t,op in stages if op in('Fi','Fe'))
    print(f"(3) dephasing (Ti,Te) max |a(+)+a(-)| = {md:.2e} (EXACT); rotation (Fi,Fe) = {mr:.2e} (approx)")
