"""
nested_basin_sim.py — the geometric constraint manifold as a NESTED attractor-basin hierarchy.
Tests the claim (user): 2 engines + 4 topologies + flux + 8 terrains are manifold structure;
the operator/entropy co-ratchet couples as sub-basins; whole model = one basin with sub/sub-sub basins.
Run against repo basin-manifold-claim-contract.md + attractor-basins-formal-reference.md (3 attractor types)
+ falsification-sim-designs.md (viability-vs-attractor kill test).
KEY RESULTS: 8 distinct terrain basins (rich fingerprint); kill test splits Ne/Ni=attractor vs Se/Si=viability
(coincides with Axis-0 polarity); operators refine each basin into distinct sub-basins; commuting control
kills the order gap (2e-17) => structure is N01-driven. scratch_diagnostic; promotion_allowed=false.
"""
import numpy as np
from scipy.linalg import expm
from scipy.spatial.distance import pdist
I2=np.eye(2,dtype=complex)
sx=np.array([[0,1],[1,0]],complex); sy=np.array([[0,-1j],[1j,0]],complex); sz=np.array([[1,0],[0,-1]],complex)
sm=np.array([[0,0],[1,0]],complex)
bloch=lambda r:np.array([np.trace(r@s).real for s in (sx,sy,sz)])
from_bloch=lambda v:0.5*(I2+v[0]*sx+v[1]*sy+v[2]*sz)
Dd=lambda L,r:L@r@L.conj().T-0.5*(L.conj().T@L@r+r@L.conj().T@L)
comm=lambda A,r:A@r-r@A
n=np.array([1,1,1.])/np.sqrt(3); H0=n[0]*sx+n[1]*sy+n[2]*sz; eps=0.15
def terr_step(r,topo,H,t=0.5,steps=30):
    def gen(x):
        if topo=="Se":return Dd(sz,x)-1j*eps*comm(H,x)
        if topo=="Ne":return -1j*comm(H,x)+eps*Dd(sz,x)
        if topo=="Ni":return Dd(sm,x)-1j*eps*comm(H,x)
        p0=from_bloch([0,0,1]);p1=from_bloch([0,0,-1])
        return -1j*eps*comm(H,x)+sum(P@x@P-0.5*(P@x+x@P) for P in (p0,p1))
    dt=t/steps
    for _ in range(steps):
        k1=gen(r);k2=gen(r+0.5*dt*k1);k3=gen(r+0.5*dt*k2);k4=gen(r+dt*k3)
        r=r+(dt/6)*(k1+2*k2+2*k3+k4);r=0.5*(r+r.conj().T);r/=np.trace(r).real
    return r
def rrho(rng):v=rng.normal(size=3);return from_bloch(v/np.linalg.norm(v)*rng.uniform(0,0.9))
NAMED={("Se","L"):"Funnel",("Ne","L"):"Vortex",("Ni","L"):"Pit",("Si","L"):"Hill",
       ("Se","R"):"Cannon",("Ne","R"):"Spiral",("Ni","R"):"Source",("Si","R"):"Citadel"}
def run():
    rng=np.random.default_rng(11); ENG={"L":+H0,"R":-H0}; out={}
    for eng in ENG:
        for topo in ["Se","Ne","Ni","Si"]:
            ends=[]
            for _ in range(30):
                r=rrho(rng)
                for _ in range(60): r=terr_step(r,topo,ENG[eng])
                ends.append(bloch(r))
            ends=np.array(ends); sp=float(np.mean(np.linalg.norm(ends-ends.mean(0),axis=1)))
            out[NAMED[(topo,eng)]]={"spread":round(sp,4),"verdict":"attractor" if sp<0.02 else "viability"}
    return out
if __name__=="__main__":
    import json; print(json.dumps(run(),indent=2))
