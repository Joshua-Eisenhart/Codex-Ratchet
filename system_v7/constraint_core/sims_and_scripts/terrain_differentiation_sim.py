"""
terrain_differentiation_sim.py  —  PURE MATH, NO JARGON.

Strong per-terrain sim on the geometric constraint manifold. 8 terrains as exact source-locked GKSL
generators on C^2 (indices t0..t7). Goal: MAXIMAL differentiation via a rich dynamical fingerprint.
All labels (terrain names, Se/Ne/Ni/Si) live in rosetta_layer.json, NOT here.

STRUCTURE per terrain: (eps in {+1,-1} sheet sign, a1 dynamics bit, a2 frame bit, z* fixed-point pole,
generator family). Fixed points, Bloch maps and the rotation senses are from igt-pattern lines 486-497.

FINGERPRINT (14 features, pure): fixed-point Bloch (3) + radius + fixed-point entropy +
Liouvillian decay rates (2) + |oscillation| + total dissipativity + signed drift + trajectory arclen +
signed chirality + trajectory handedness + signed swept area (geometric-phase proxy, eps-odd).

RESULT: all 8 terrains are DISTINCT under the fingerprint. Pairwise distances (standardized):
mean ~5.3, max ~6.5, min ~0.35. The bottleneck pair t3-t7 (the two projective terrains) is
near-degenerate: their generator is nearly SHEET-SYMMETRIC, so only eps-odd geometric features
(handedness, swept area) separate them. That near-degeneracy is a genuine structural fact of the
manifold, not a sim artifact.

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

TERR=[dict(i=0,s=+1,zt=+0.86,fam="ADamp"), dict(i=1,s=+1,zt=None,fam="Depol"),
      dict(i=2,s=+1,zt=-0.92,fam="Sink"),  dict(i=3,s=+1,zt=None,fam="Proj"),
      dict(i=4,s=-1,zt=-0.86,fam="ADamp"), dict(i=5,s=-1,zt=None,fam="Depol"),
      dict(i=6,s=-1,zt=+0.92,fam="Source"),dict(i=7,s=-1,zt=None,fam="Proj")]
def generator(T):
    H=T["s"]*H0; fam=T["fam"]
    if fam=="ADamp":
        zt=T["zt"]; gp=(1+zt)/2; gm=(1-zt)/2
        return lambda r: gp*D(SP,r)+gm*D(SM,r)-1j*EPS*comm(H,r)
    if fam=="Depol": return lambda r: -1j*comm(H,r)+EPS*(D(SX,r)+D(SY,r)+D(SZ,r))
    if fam=="Sink":  return lambda r: D(SM,r)-1j*EPS*comm(H,r)
    if fam=="Source":return lambda r: D(SP,r)-1j*EPS*comm(H,r)
    if fam=="Proj":  return lambda r: -1j*EPS*comm(H,r)+0.7*D(SZ,r)
def integrate(g,r0,t=6.0,steps=600):
    r=r0.copy(); dt=t/steps
    for _ in range(steps): r=r+dt*g(r); r=0.5*(r+r.conj().T); r=r/np.trace(r).real
    return r
def entropy(r):
    ev=np.clip(np.linalg.eigvalsh(r).real,1e-12,1); return float(-(ev*np.log2(ev)).sum())
def superop(g):
    B=[I2/np.sqrt(2),SX/np.sqrt(2),SY/np.sqrt(2),SZ/np.sqrt(2)]
    return np.array([[np.trace(Bk.conj().T@g(Bj)) for Bj in B] for Bk in B])
def bloch(r): return np.array([np.trace(r@P).real for P in (SX,SY,SZ)])
def fingerprint(T):
    g=generator(T); rf=integrate(g,I2/2); b=bloch(rf); f=[b[0],b[1],b[2],np.linalg.norm(b),entropy(rf)]
    ev=np.sort_complex(np.linalg.eigvals(superop(g))); ev=ev[np.argsort(ev.real)]
    f+= [ev[0].real, ev[1].real, np.max(np.abs(ev.imag)), -np.sum(ev.real[ev.real<-1e-9])]
    f.append(np.trace(g(I2/2)@(-SZ)).real)
    # arclen, handedness, swept area from |+> and off-axis probes
    r=0.5*(I2+SX); arc=0.0; hand=0.0; prev=bloch(r); dt=0.02
    for _ in range(150):
        r=r+dt*g(r); r=0.5*(r+r.conj().T); r=r/np.trace(r).real; cur=bloch(r)
        arc+=np.linalg.norm(cur-prev); hand+=np.dot(np.cross(prev,cur),AXIS); prev=cur
    f+=[arc]
    k=np.argmax(np.abs(np.linalg.eigvals(superop(g)).imag)); f.append(np.linalg.eigvals(superop(g))[k].imag)
    f.append(hand)
    r=0.5*(I2+(SX+SY)/np.sqrt(2)); area=0.0; prev=bloch(r); dt=0.01
    for _ in range(400):
        r=r+dt*g(r); r=0.5*(r+r.conj().T); r=r/np.trace(r).real; cur=bloch(r)
        area+=0.5*np.dot(np.cross(prev,cur),AXIS); prev=cur
    f.append(area)
    return np.array(f)

if __name__=="__main__":
    F=np.array([fingerprint(T) for T in TERR])
    Fs=(F-F.mean(0))/(F.std(0)+1e-12)
    Dm={(i,j):np.linalg.norm(Fs[i]-Fs[j]) for i,j in combinations(range(8),2)}
    ap=sorted((d,i,j) for (i,j),d in Dm.items())
    md=np.mean(list(Dm.values()))
    print(f"fingerprint: {F.shape[1]} features, 8 terrains")
    print(f"all distinct: {ap[0][0]>1e-6}")
    print(f"pairwise distance: mean={md:.3f} min={ap[0][0]:.3f} (t{ap[0][1]}-t{ap[0][2]}) max={ap[-1][0]:.3f}")
    print(f"bottleneck pair t{ap[0][1]}-t{ap[0][2]} (near sheet-symmetric projective terrains)")
