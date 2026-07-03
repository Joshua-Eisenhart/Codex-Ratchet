"""
sixteen_stage_engine_sim.py  —  PURE MATH, NO JARGON.

The 16 engine stages = 8 terrains x 2 native operators each, in a signed Axis-6 order.
Built on the operator-geometry-fusion foundation (7q). Structural indices t0..t7 and Ti/Te/Fi/Fe;
personality names in rosetta_layer.json.

RESULTS:
 (1) all 16 stages DISTINCT under a dynamical fingerprint (mean pairwise dist 4.6); bottleneck at
     the projective Si stages t3:Te-t7:Te (same near-degeneracy as 7p/7q).
 (2) all 16 stages ORDER-SENSITIVE (N01): operator-first vs terrain-first give different outputs =>
     each stage does unique information processing.
 (3) fusion split (from 7q containment residuals): exactly 8/16 operator-fused stages (projective +
     depolarizing terrains) and 8/16 source-surplus stages (amplitude-damping/source-locked terrains).
     The source-surplus stages are the dissipative half — the same half that makes the parity
     readable (7o gauge-breaking law).
scratch_diagnostic; promotion_allowed=false.
"""
import numpy as np
from itertools import combinations

I2=np.eye(2,dtype=complex)
SX=np.array([[0,1],[1,0]],complex); SY=np.array([[0,-1j],[1j,0]],complex); SZ=np.array([[1,0],[0,-1]],complex)
SM=np.array([[0,0],[1,0]],complex); SP=np.array([[0,1],[0,0]],complex)
AXIS=np.array([1,1,1.])/np.sqrt(3); H0=AXIS[0]*SX+AXIS[1]*SY+AXIS[2]*SZ
EPS=0.15
def D(L,r): return L@r@L.conj().T-0.5*(L.conj().T@L@r+r@L.conj().T@L)
def comm(A,r): return A@r-r@A
OP={"Ti":lambda r:0.5*(SZ@r@SZ-r),"Te":lambda r:0.5*(SX@r@SX-r),
    "Fi":lambda r:-1j*comm(0.5*SX,r),"Fe":lambda r:-1j*comm(0.5*SZ,r)}
TERR={0:("ADamp",+1,+0.86,["Ti","Fi"]),1:("Depol",+1,None,["Ti","Fi"]),
      2:("Sink",+1,-0.92,["Te","Fe"]),3:("Proj",+1,None,["Te","Fe"]),
      4:("ADamp",-1,-0.86,["Ti","Fi"]),5:("Depol",-1,None,["Ti","Fi"]),
      6:("Source",-1,+0.92,["Te","Fe"]),7:("Proj",-1,None,["Te","Fe"])}
RESID={0:0.666,1:0.115,2:0.705,3:0.000,4:0.666,5:0.115,6:0.705,7:0.000}  # from 7q
def tgen(i):
    fam,s,zt,_=TERR[i]; H=s*H0
    if fam=="ADamp": gp=(1+zt)/2; gm=(1-zt)/2; return lambda r:gp*D(SP,r)+gm*D(SM,r)-1j*EPS*comm(H,r)
    if fam=="Depol": return lambda r:-1j*comm(H,r)+EPS*(D(SX,r)+D(SY,r)+D(SZ,r))
    if fam=="Sink":  return lambda r:D(SM,r)-1j*EPS*comm(H,r)
    if fam=="Source":return lambda r:D(SP,r)-1j*EPS*comm(H,r)
    if fam=="Proj":  return lambda r:-1j*EPS*comm(H,r)+0.7*D(SZ,r)
def stage_ch(i,op,order):
    g=tgen(i); O=OP[op]
    def sg(r,dt=0.35): rr=r+dt*g(r); rr=0.5*(rr+rr.conj().T); return rr/np.trace(rr).real
    def so(r,dt=0.6): rr=r+dt*O(r); rr=0.5*(rr+rr.conj().T); return rr/np.trace(rr).real
    return (lambda r: sg(so(r))) if order=="op_first" else (lambda r: so(sg(r)))
PROBE=0.5*(I2+(SX+SY+SZ)/np.sqrt(3))
def stage_fp(i,op,order):
    r=stage_ch(i,op,order)(PROBE.copy())
    b=np.array([np.trace(r@P).real for P in (SX,SY,SZ)])
    ev=np.clip(np.linalg.eigvalsh(r).real,1e-12,1)
    return np.concatenate([b,[np.linalg.norm(b),-(ev*np.log2(ev)).sum()]])

if __name__=="__main__":
    stages=[(i,op) for i in range(8) for op in TERR[i][3]]
    fps=[]; og=[]
    for i,op in stages:
        of=stage_fp(i,op,"op_first"); tf=stage_fp(i,op,"terr_first")
        fps.append(np.concatenate([of,tf,[np.linalg.norm(of-tf)]])); og.append(np.linalg.norm(of-tf))
    F=np.array(fps); Fs=(F-F.mean(0))/(F.std(0)+1e-12)
    dd=[np.linalg.norm(Fs[a]-Fs[b]) for a,b in combinations(range(16),2)]
    fused=sum(1 for i,op in stages if RESID[i]<0.4)
    print(f"16 stages, all distinct: {min(dd)>1e-6} (min={min(dd):.3f}, mean={np.mean(dd):.3f})")
    print(f"all order-sensitive (N01): {sum(1 for g in og if g>1e-3)}/16")
    print(f"fusion split: {fused}/16 operator-fused, {16-fused}/16 source-surplus")
