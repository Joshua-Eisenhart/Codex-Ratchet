"""
engine_64_schedule_sim.py
Runs the QIT engine 64-microstep schedule and tests whether each stage does UNIQUE
information processing. Sources (repo, read directly):
  system_v5/READ ONLY Reference Docs / ENGINE_64_SCHEDULE_ATLAS.md   (64 = 2 eng x 8 terrain x 4 op)
  system_v5/ops/QIT_ENGINE_FOUR_OPERATOR_SIGNED_MATH_20260522.md      (Ti/Te dephasing, Fi/Fe rotation; up/down)
Key result: an ORDER-BLIND coarse readout collapses 64 -> ~11 distinct (the documented eng_64 degeneracy);
the N01 ORDER-SENSITIVE readout (terrain-first vs operator-first) lifts it to 64/64. So uniqueness is an
N01 (noncommutation) property of the observable, not of adding terrains/operators.
Claim ceiling: scratch_diagnostic; promotion_allowed=false.
"""
import numpy as np, itertools, json
from scipy.linalg import expm
I2=np.eye(2,dtype=complex)
sx=np.array([[0,1],[1,0]],complex); sy=np.array([[0,-1j],[1j,0]],complex); sz=np.array([[1,0],[0,-1]],complex)
sm=np.array([[0,0],[1,0]],complex)
bloch=lambda rho:np.array([np.trace(rho@s).real for s in (sx,sy,sz)])
from_bloch=lambda r:0.5*(I2+r[0]*sx+r[1]*sy+r[2]*sz)
D=lambda L,rho:L@rho@L.conj().T-0.5*(L.conj().T@L@rho+rho@L.conj().T@L)
comm=lambda A,rho:A@rho-rho@A
n=np.array([1,1,1.])/np.sqrt(3); H0=n[0]*sx+n[1]*sy+n[2]*sz; eps=0.15
q=1-np.exp(-1.0)
P0=from_bloch([0,0,1]);P1=from_bloch([0,0,-1]);Qp=from_bloch([1,0,0]);Qm=from_bloch([-1,0,0])
def Ti(rho):K=[np.sqrt(1-q)*I2,np.sqrt(q)*P0,np.sqrt(q)*P1];return sum(k@rho@k.conj().T for k in K)
def Te(rho):K=[np.sqrt(1-q)*I2,np.sqrt(q)*Qp,np.sqrt(q)*Qm];return sum(k@rho@k.conj().T for k in K)
def Fi(rho,th=np.pi/2):U=expm(-1j*th*sx/2);return U@rho@U.conj().T
def Fe(rho,ph=np.pi/2):U=expm(-1j*ph*sz/2);return U@rho@U.conj().T
OPS={"Ti":Ti,"Te":Te,"Fi":Fi,"Fe":Fe}
def terr_apply(rho,topo,flux,H,t=1.0,steps=60):
    def gen(r):
        if topo=="Se":base=D(sz,r)-1j*eps*comm(H,r)
        elif topo=="Ne":base=-1j*comm(H,r)+eps*D(sz,r)
        elif topo=="Ni":base=D(sm,r)-1j*eps*comm(H,r)
        else:
            p0=from_bloch([0,0,1]);p1=from_bloch([0,0,-1])
            base=-1j*eps*comm(H,r)+sum(P@r@P-0.5*(P@r+r@P) for P in (p0,p1))
        return base if flux=="in" else -0.5*base+D(sm,r)
    dt=t/steps
    for _ in range(steps):
        k1=gen(rho);k2=gen(rho+0.5*dt*k1);k3=gen(rho+0.5*dt*k2);k4=gen(rho+dt*k3)
        rho=rho+(dt/6)*(k1+2*k2+2*k3+k4);rho=0.5*(rho+rho.conj().T);rho/=np.trace(rho).real
    return rho
def run():
    ENG={"L":+H0,"R":-H0};sched=list(itertools.product(ENG,["Se","Ne","Ni","Si"],["in","out"],OPS))
    seed=from_bloch([0.4,0.4,0.4]);coarse=[];fine=[];gaps=[]
    for e,t,f,o in sched:
        H=ENG[e];op=OPS[o]
        down=lambda r,H=H,t=t,f=f,op=op:op(terr_apply(r,t,f,H))
        up  =lambda r,H=H,t=t,f=f,op=op:terr_apply(op(r),t,f,H)
        ra=(bloch(down(seed))+bloch(up(seed)))/2
        coarse.append((round(0.5*(1+np.linalg.norm(ra)**2),1),int(np.sign(round(ra[2],1)))))
        fine.append(tuple(np.round(np.concatenate([bloch(down(from_bloch(v))) for v in [[.5,0,0],[0,.5,0],[0,0,.5]]]),2)))
        gaps.append(float(np.linalg.norm(np.concatenate([bloch(down(from_bloch(v)))-bloch(up(from_bloch(v))) for v in [[.5,0,0],[0,.5,0],[0,0,.5]]]))))
    return {"n_orderblind":len(set(coarse)),"n_ordersensitive":len(set(fine)),
            "n_with_order_gap":sum(1 for g in gaps if g>1e-3),"mean_order_gap":float(np.mean(gaps))}
if __name__=="__main__":
    print(json.dumps(run(),indent=2))
