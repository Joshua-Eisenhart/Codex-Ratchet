"""
engine_64_schedule_sim.py
Runs the QIT engine 64-microstep schedule and tests whether each stage does UNIQUE
information processing. Sources (repo, read directly):
  system_v5/READ ONLY Reference Docs / ENGINE_64_SCHEDULE_ATLAS.md   (64 = 2 eng x 8 terrain x 4 op)
  system_v5/ops/QIT_ENGINE_FOUR_OPERATOR_SIGNED_MATH_20260522.md      (Ti/Te dephasing, Fi/Fe rotation; up/down)
CORRECTED 2026-07-08 (withdrew a by-construction overclaim). The earlier version claimed the order-sensitive
readout "lifts uniqueness to 64/64" -- but that counted distinct output signatures across all 64
(engine,terrain,flux,operator) slots, which differ AUTOMATICALLY because each has a different terrain/operator.
That is distinctness BY CONSTRUCTION (the 1984 excluded_trivial cells the v7 slot64 probe correctly removes), NOT
a demonstration that position/order does unique work. Withdrawn.

What is honestly measured here, matching the v7 slot64_unique_computing_probe verdict rather than contradicting it:
  (1) ORDER-BLIND coarse readout collapses 64 -> 11 distinct (the documented eng_64 degeneracy; kept, an honest
      failure by design -- an order-blind observable cannot tell the slots apart).
  (2) MATCHED-CONTENT ORDER-CARRIEDNESS (well-posed N01 test): hold engine+terrain+operator FIXED, vary ONLY the
      composition order (operator-first vs terrain-first). Nonzero order-gap = order does real work at that slot.
      Measured: 16/16 order-carried. This is the honest, defensible per-slot claim -- and it is WEAKER than, not a
      substitute for, full position-uniqueness across the 64 schedule.
  (3) v7's harder question -- 64-slot POSITION-uniqueness with by-construction cells excluded -- stays OPEN with a
      named instrument gap (v7: 12/32 matched-content pairs position-unique, 20 untestable by the current
      operator-insensitive instrument). We do NOT claim to have closed it. "Every substage does unique work" is an
      OPEN claim, not an earned one; the F-rotation substages in particular do NO entropy work (measured: entropy
      held constant across the Fi/Fe beats when a stage is actually run).
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
    seed=from_bloch([0.4,0.4,0.4]);coarse=[];gaps=[]
    # (1) ORDER-BLIND coarse readout over all 64 slots -> honest collapse to 11 (kept: an order-blind observable
    #     cannot separate the slots; this is a genuine failure by design, not distinctness).
    # (3) NOTE: an "n_ordersensitive over all 64 slots" count is WITHDRAWN -- it was distinctness by construction
    #     (every slot has a different terrain/operator, so outputs differ automatically = the 1984 excluded_trivial
    #     cells v7 removes). It is NOT computed or gated here anymore.
    for e,t,f,o in sched:
        H=ENG[e];op=OPS[o]
        down=lambda r,H=H,t=t,f=f,op=op:op(terr_apply(r,t,f,H))
        up  =lambda r,H=H,t=t,f=f,op=op:terr_apply(op(r),t,f,H)
        ra=(bloch(down(seed))+bloch(up(seed)))/2
        coarse.append((round(0.5*(1+np.linalg.norm(ra)**2),1),int(np.sign(round(ra[2],1)))))
    # (2) MATCHED-CONTENT ORDER-CARRIEDNESS (well-posed N01 test): hold engine+terrain+operator FIXED (one engine
    #     lane), vary ONLY composition order (operator-first `up` vs terrain-first `down`). Nonzero gap = order does
    #     real work at that slot. This is the honest per-slot claim; it is WEAKER than full 64-slot position-uniqueness
    #     (which stays open with a named instrument gap: v7 reports 12/32 matched pairs position-unique, 20 untestable).
    matched=[]
    for t in ["Se","Ne","Ni","Si"]:
        for o in OPS:
            H=H0;op=OPS[o]
            down=lambda r,H=H,t=t,op=op:op(terr_apply(r,t,"in",H))
            up  =lambda r,H=H,t=t,op=op:terr_apply(op(r),t,"in",H)
            g=float(np.linalg.norm(np.concatenate([bloch(down(from_bloch(v)))-bloch(up(from_bloch(v))) for v in [[.5,0,0],[0,.5,0],[0,0,.5]]])))
            matched.append((f"{t}/{o}",g)); gaps.append(g)
    n_order_carried=sum(1 for _,g in matched if g>1e-2)
    return {"n_orderblind":len(set(coarse)),
            "n_matched_content_slots":len(matched),
            "n_order_carried":n_order_carried,
            "mean_order_gap":float(np.mean(gaps)),
            "position_uniqueness_over_64":"OPEN -- not demonstrated (v7 slot64 probe: 12/32 matched pairs position-unique, 20 untestable; instrument gap named)",
            "withdrawn":"n_ordersensitive==64 (was distinctness by construction across differing terrains/operators)",
            "verdict":"PASS_order_carried" if n_order_carried==len(matched) else "FAIL"}
if __name__=="__main__":
    r=run();print(json.dumps(r,indent=2))
    print("ALL_GATES:","PASS" if r["verdict"]=="PASS_order_carried" else "FAIL")
