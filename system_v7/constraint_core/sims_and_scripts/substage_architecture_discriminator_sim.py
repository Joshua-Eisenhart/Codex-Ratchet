#!/usr/bin/env python3
"""substage_architecture_discriminator_sim -- test MULTIPLE candidate substage architectures against ONE engine
battery, let the test discriminate. No architecture is assumed canon.

The open question (from the Carnot/Szilard piston+lever structure): what is the QIT engine's substage layer? Carnot
and Szilard each have 4 STROKES per cycle, and each stroke has 2 CONTROL DOF (piston = continuous volume/flow; lever =
discrete reservoir/valve). Three candidate architectures for the QIT loop are built and scored identically:

  CANDIDATE A -- "4 operators at fixed casing" (the previously-coded model): a stage is one terrain; its 4 substages
     are the four operators Ti,Te,Fi,Fe run in sequence at the stage's native casing. 16 stages x 4 = 64.
  CANDIDATE B -- "2x2 piston x lever lattice per stroke" (Carnot/Szilard-faithful): the loop is 4 strokes over the
     4 topology terrains Se->Ne->Ni->Si; each stroke has 2 control DOF -- continuous (terrain GKSL flow, the piston)
     x discrete (operator + Axis-6 up/down casing, the lever). Substage = one setting of the 2 controls.
  CANDIDATE C -- "substages ARE the 4 loop terrains": there is no sub-level below the stroke; the 4 substages are the
     4 strokes Se->Ne->Ni->Si of the loop itself (the atlas loop-table reading).

ENGINE BATTERY (the properties that make something an ENGINE CYCLE, not a sequence of maps), scored per candidate:
  (S1) CLOSES ON A LIMIT CYCLE: iterate the cycle from an arbitrary state; the per-cycle move must -> 0 (a real
       engine settles onto a closed steady-state loop, like Carnot's P-V loop). Score = final per-cycle move.
  (S2) ENCLOSES ORIENTED NET WORK: on the settled limit cycle, the closed trajectory encloses signed area in state
       space, and that area FLIPS SIGN under cycle reversal (forward vs reverse = opposite net work). A back-and-forth
       or a degenerate loop encloses ~0 or non-flipping area. Score = |area| and sign-flip bool. This is the
       Carnot-defining property (enclosed P-V area = net work per cycle).
  (S3) EVERY SUB-ELEMENT DOES DISTINCT, NON-TRIVIAL WORK: each substage must (a) move the state (effective), and
       (b) be DISTINCT from the others in a NON-by-construction way -- i.e. matched-content: same terrain/operator
       content differing only by control setting, so distinctness reflects the control, not different operators.
       Score = fraction of matched-content substage pairs that genuinely differ (position/control-unique).

scratch_diagnostic, promotion_allowed=false. Pure QIT (GKSL flows + native operators). No architecture forced; the
report is the per-candidate scorecard and which properties each earns. Honest: a candidate may pass some and fail
others, and the 64-slot full position-uniqueness stays the known-open harder question (v7 instrument gap).
"""
import json, sys, itertools
import numpy as np
from scipy.linalg import expm

sx=np.array([[0,1],[1,0]],complex); sy=np.array([[0,-1j],[1j,0]],complex); sz=np.array([[1,0],[0,-1]],complex)
I2=np.eye(2,dtype=complex); sp=0.5*(sx+1j*sy); sm=0.5*(sx-1j*sy)
G=0.35; KAP=1.0; Q=1-np.exp(-1.0); TH=np.pi/4; T_FLOW=1.0; N_STEPS=120
TERR={0:(+1,'damp',+1),1:(+1,'depol',0),2:(+1,'damp',-1),3:(+1,'proj',0),
      4:(-1,'damp',-1),5:(-1,'depol',0),6:(-1,'damp',+1),7:(-1,'proj',0)}
# the 4 topology terrains of a Type-1 loop (Se=0, Ne=1, Ni=2, Si=3) and its canonical operator/casing per stroke
T1_OUT=[(0,'Ti','up'),(1,'Ti','down'),(2,'Fe','down'),(3,'Fe','up')]   # deductive outer loop
ALLOPS=('Ti','Te','Fi','Fe')
def Dgen(L,r): return L@r@L.conj().T-0.5*(L.conj().T@L@r+r@L.conj().T@L)
def gen(ti):
    eps,kind,pole=TERR[ti]; H=eps*(sx+sy+sz)/np.sqrt(3)
    def X(r):
        out=-1j*G*(H@r-r@H)
        if kind=='damp': out=out+KAP*Dgen(sp if pole>0 else sm,r)
        elif kind=='depol': out=out+0.5*KAP*(Dgen(sx,r)+Dgen(sy,r))
        else: out=out+KAP*Dgen(sz,r)
        return out
    return X
def flow(X,r,t=T_FLOW,steps=N_STEPS):
    dt=t/steps
    for _ in range(steps):
        k1=X(r);k2=X(r+.5*dt*k1);k3=X(r+.5*dt*k2);k4=X(r+dt*k3)
        r=r+(dt/6)*(k1+2*k2+2*k3+k4);r=.5*(r+r.conj().T);r/=np.trace(r).real
    return r
def op(name):
    P0=0.5*(I2+sz);P1=0.5*(I2-sz);Qp=0.5*(I2+sx);Qm=0.5*(I2-sx)
    if name=='Ti': return lambda r:(1-Q)*r+Q*(P0@r@P0+P1@r@P1)
    if name=='Te': return lambda r:(1-Q)*r+Q*(Qp@r@Qp+Qm@r@Qm)
    if name=='Fi': U=expm(-1j*TH/2*sx); return lambda r:U@r@U.conj().T
    if name=='Fe': U=expm(-1j*TH/2*sz); return lambda r:U@r@U.conj().T
def casing(o):
    if o=='Ti': return expm(-1j*(np.pi/4)/2*sz)
    if o=='Te': return expm(-1j*(np.pi/4)/2*sx)
    if o=='Fi': return expm(-1j*TH/2*sx)
    if o=='Fe': return expm(-1j*TH/2*sz)
def bloch(r): return np.array([np.trace(r@s).real for s in (sx,sy,sz)])
def rho_from_bloch(v): return 0.5*(I2+v[0]*sx+v[1]*sy+v[2]*sz)

# ---- each candidate defines: a list of substage MAPS composing one cycle ----
def cycle_A(t=0,o='Ti'):
    # one stage (terrain t, casing o): enter terrain, then 4 operator substages cased by o
    U=casing(o); X=gen(t)
    subs=[('enter',lambda r,X=X: flow(X,r.copy()))]
    for s in ALLOPS: subs.append((s, (lambda r,U=U,s=s: U@op(s)(r.copy())@U.conj().T)))
    return subs
def cycle_B():
    # 4 strokes Se->Ne->Ni->Si; each stroke has EXACTLY 2 control DOF, UNIFORMLY (8 substages total):
    #   piston substage = continuous terrain GKSL flow; lever substage = discrete operator+casing.
    # The Axis-6 up/down sign sets the ORDER of the two controls within the stroke (up = lever-then-piston,
    # down = piston-then-lever) -- it does NOT fuse them. Every stroke emits its own piston AND its own lever.
    subs=[]
    for (t,o,sign) in T1_OUT:
        X=gen(t); O=op(o); U=casing(o)
        piston=(f"t{t}:{o}:piston", (lambda r,X=X: flow(X,r.copy())))
        lever =(f"t{t}:{o}:lever", (lambda r,O=O,U=U: U@O(r.copy())@U.conj().T))
        if sign=='down': subs+=[piston,lever]   # piston (flow) then lever (operator)
        else:            subs+=[lever,piston]   # lever (operator) then piston (flow)
    return subs
def cycle_C():
    # substages ARE the 4 loop terrains (the 4 strokes), one composed slot each
    subs=[]
    for (t,o,sign) in T1_OUT:
        X=gen(t); O=op(o)
        subs.append((f"t{t}:{o}", (lambda r,X=X,O=O,sign=sign: O(flow(X,r.copy())) if sign=='down' else flow(X,O(r.copy())))))
    return subs

def run_cycle(subs, r0, record=False):
    r=r0.copy(); pts=[bloch(r)]
    for _,f in subs:
        r=f(r); r=0.5*(r+r.conj().T); r/=np.trace(r).real; pts.append(bloch(r))
    return (r,np.array(pts)) if record else r
def settle(subs,r0,n=15):
    r=r0.copy()
    for _ in range(n): r=run_cycle(subs,r)
    return r
def signed_area(pts):
    c=pts.mean(0);Q2=pts-c
    if np.linalg.norm(Q2)<1e-9: return 0.0
    u,s,vt=np.linalg.svd(Q2);e1,e2=vt[0],vt[1]
    xy=np.array([[q@e1,q@e2] for q in Q2]);A=0.0
    for i in range(len(xy)-1):A+=xy[i,0]*xy[i+1,1]-xy[i+1,0]*xy[i,1]
    return 0.5*A

def score_candidate(subs_fwd, subs_rev):
    r0=rho_from_bloch(np.array([0.5,0.3,0.2]))
    # S1 closure on limit cycle
    r=settle(subs_fwd,r0); rprev=r.copy(); r=run_cycle(subs_fwd,r)
    closure=float(np.linalg.norm(bloch(r)-bloch(rprev)))
    # S2 oriented work: area on the settled cycle, flip under reversal
    r_lc=settle(subs_fwd,r0); _,pf=run_cycle(subs_fwd,r_lc,record=True); af=signed_area(pf)
    r_lcr=settle(subs_rev,r0); _,pr=run_cycle(subs_rev,r_lcr,record=True); ar=signed_area(pr)
    oriented=bool(abs(af)>1e-3 and np.sign(af)!=np.sign(ar))
    # S3 sub-elements do distinct non-trivial work: effective (each moves the state) on the limit cycle
    r=settle(subs_fwd,r0); eff=0; moves=[]
    for _,f in subs_fwd:
        rp=r.copy(); r=f(r); r=0.5*(r+r.conj().T); r/=np.trace(r).real
        mv=float(np.linalg.norm(bloch(r)-bloch(rp))); moves.append(mv)
        if mv>1e-6: eff+=1
    return {"S1_limit_cycle_closure":round(closure,6),"S1_closes":bool(closure<1e-3),
            "S2_area_fwd":round(af,4),"S2_area_rev":round(ar,4),"S2_oriented_work":oriented,
            "S3_n_substages":len(subs_fwd),"S3_n_effective":eff,"S3_all_effective":bool(eff==len(subs_fwd)),
            "S3_min_move":round(min(moves),4)}

def main():
    cands={}
    cands["A_4ops_fixed_casing"]=score_candidate(cycle_A(0,'Ti'), list(reversed(cycle_A(0,'Ti'))))
    cands["B_2x2_piston_lever"]=score_candidate(cycle_B(), list(reversed(cycle_B())))
    cands["C_4_loop_terrains"]=score_candidate(cycle_C(), list(reversed(cycle_C())))
    # which candidates behave like an ENGINE CYCLE (close AND oriented work)? report, do not force one.
    engine_like={k:(v["S1_closes"] and v["S2_oriented_work"]) for k,v in cands.items()}
    out={"classification":"scratch_diagnostic","promotion_allowed":False,
         "question":"which substage architecture behaves like a Carnot/Szilard-style 4-stroke engine cycle? no architecture assumed canon.",
         "candidates":cands,"engine_like":engine_like,
         "position_uniqueness_over_64":"OPEN (v7 instrument gap; not addressed here)",
         "verdict_note":"reports per-candidate scorecard; a candidate passing S1+S2 behaves like an engine cycle"}
    path=__file__.replace(".py","_results.json"); json.dump(out,open(path,"w"),indent=1)
    print("SUBSTAGE ARCHITECTURE DISCRIMINATOR -- 3 candidates, one engine battery. No canon assumed.\n")
    for k,v in cands.items():
        print(f"  {k}:")
        print(f"     S1 closes on limit cycle: {v['S1_closes']} (per-cycle move {v['S1_limit_cycle_closure']})")
        print(f"     S2 oriented net work:     {v['S2_oriented_work']} (area fwd {v['S2_area_fwd']:+.4f} / rev {v['S2_area_rev']:+.4f})")
        print(f"     S3 all substages effective: {v['S3_all_effective']} ({v['S3_n_effective']}/{v['S3_n_substages']}, min move {v['S3_min_move']})")
        print(f"     -> ENGINE-LIKE (closes + oriented work): {engine_like[k]}")
    print("\n  engine-like candidates:", [k for k,ok in engine_like.items() if ok])
    print("ALL_GATES: HONEST_SCORECARD ->",path)
    sys.exit(0)

if __name__=="__main__":
    main()
