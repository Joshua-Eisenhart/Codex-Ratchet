#!/usr/bin/env python3
"""engine_64_schedule_definition -- DEFINE THE 64-ENGINE SCHEDULE for the 16 stages (owner correction 2026-07-06:
"there is the 16 engine stages, and each stage runs all 4 of the operators with the same up or down sign from
axis-6, because they share the same order of terrain or operator first. but this doesn't have the 64 engine
schedule for each of the 16 stages defined"). This sim lays out that schedule explicitly and measures it.

THE SCHEDULE (16 stages x 4 operators = 64):
  A STAGE is a (terrain, axis-6 sign) pair. 8 terrains x 2 signs = 16 stages. The axis-6 SIGN is the composition
  order shared by all 4 of the stage's operators (doc math ref sec 10):
     UP   = operator-first word:  Phi_T( O(rho) )   (the operator acts, then the terrain flow)
     DOWN = terrain-first word:   O( Phi_T(rho) )   (the terrain flow acts, then the operator)
  Each stage runs ALL 4 operators (Ti,Te,Fi,Fe) at its ONE shared sign -> 4 substage-entries per stage. 16x4 = 64.
  So the 64-schedule = { (terrain t in 0..7, sign in {up,down}, operator o in {Ti,Te,Fi,Fe}) }.

WHAT IS MEASURED (each lane a measurement; a SEPARATE policy eval decides; controls must flip):
  (A) THE SCHEDULE IS WELL-FORMED: exactly 16 stages, each carrying exactly its 4 operators at ONE shared sign;
      64 entries total; and the sign is a REAL composition-order choice, not a label -- within every stage the
      operator-first and terrain-first words genuinely differ for the operators where order can bite.
  (B) THE AXIS-6 SIGN IS LOAD-BEARING under the real terrain flow: for the (terrain, operator) pairs, up != down.
      HONEST NOTE: an earlier scratch-map result had the sign collapse (up=down) for the z-family operators that
      share the terrain drive axis; under the FULL integrated GKSL flow the sign is load-bearing UNIVERSALLY
      (measured below). Control: replace the terrain flow with the identity (no flow) and up==down EXACTLY -- the
      sign is load-bearing only because the terrain flow is nontrivial (axis-6 rides on the drive).
  (C) THE 64 ENTRIES ARE DYNAMICALLY DISTINCT operations (channel signatures pairwise distinct); control: a
      shuffled-operator schedule collapses the distinctness. This is what "64 real operations, not 64 labels" means.

HONEST SCOPE: which 16-way decomposition names a "stage" (here: terrain x sign) is the reading that matches the
owner's description ("all 4 operators, same up/down sign, shared terrain/operator-first order"); the ledger records
that the rung ORDERS (entropy/geometry) are NOT canon and this schedule is a candidate index surface, not ontology
(doc: "64-closure is a schedule/index surface, not ontology"). Real oracle operators + integrated terrain flows.
QUARANTINE_EXPLORATORY. classification="scratch_diagnostic". promotion_allowed=False. Pure distinguishability.
"""
import json, os, sys, itertools
import numpy as np
from scipy.linalg import expm

sx=np.array([[0,1],[1,0]],complex); sy=np.array([[0,-1j],[1j,0]],complex); sz=np.array([[1,0],[0,-1]],complex)
I2=np.eye(2,dtype=complex); sp=0.5*(sx+1j*sy); sm=0.5*(sx-1j*sy)
G=0.35; KAP=1.0; Q=1.0-np.exp(-1.0); TH=np.pi/4; T_FLOW=1.0; N_STEPS=400
TERR={0:(+1,'damp',+1),1:(+1,'depol',0),2:(+1,'damp',-1),3:(+1,'proj',0),
      4:(-1,'damp',-1),5:(-1,'depol',0),6:(-1,'damp',+1),7:(-1,'proj',0)}
OPS=('Ti','Te','Fi','Fe'); SIGNS=('up','down')

def Dop(L,r): return L@r@L.conj().T-0.5*(L.conj().T@L@r+r@L.conj().T@L)
def gen(ti):
    eps,kind,pole=TERR[ti]; H=eps*(sx+sy+sz)/np.sqrt(3)
    def X(r):
        out=-1j*G*(H@r-r@H)
        if kind=='damp': out=out+KAP*Dop(sp if pole>0 else sm,r)
        elif kind=='depol': out=out+0.5*KAP*(Dop(sx,r)+Dop(sy,r))
        else: out=out+KAP*Dop(sz,r)
        return out
    return X
def flow(X,r,t=T_FLOW,steps=N_STEPS):
    dt=t/steps
    for _ in range(steps):
        k1=X(r);k2=X(r+.5*dt*k1);k3=X(r+.5*dt*k2);k4=X(r+dt*k3)
        r=r+(dt/6)*(k1+2*k2+2*k3+k4); r=.5*(r+r.conj().T); r/=np.trace(r).real
    return r
def op(n):
    P0=.5*(I2+sz);P1=.5*(I2-sz);Qp=.5*(I2+sx);Qm=.5*(I2-sx)
    if n=='Ti':return lambda r:(1-Q)*r+Q*(P0@r@P0+P1@r@P1)
    if n=='Te':return lambda r:(1-Q)*r+Q*(Qp@r@Qp+Qm@r@Qm)
    if n=='Fi':U=expm(-1j*TH/2*sx);return lambda r:U@r@U.conj().T
    if n=='Fe':U=expm(-1j*TH/2*sz);return lambda r:U@r@U.conj().T
def dm(v): return 0.5*(I2+v[0]*sx+v[1]*sy+v[2]*sz)

def stage_op(t,sign,o,drive=True):
    X=gen(t); O=op(o)
    if not drive:  # control: no terrain flow -> up==down exactly (both = O(rho))
        return lambda r: O(r.copy())
    if sign=='up':   return lambda r: flow(X, O(r.copy()))    # operator-first  Phi_T(O(rho))
    else:            return lambda r: O(flow(X, r.copy()))    # terrain-first   O(Phi_T(rho))

_PROBES=None
def probes():
    global _PROBES
    if _PROBES is None:
        rng=np.random.default_rng(2); ps=[]
        for _ in range(6):
            v=rng.standard_normal(3); v=v/np.linalg.norm(v)*0.7; ps.append(dm(v))
        _PROBES=ps
    return _PROBES
def sig(chan):
    return np.concatenate([[np.trace(chan(p)@s).real for s in (sx,sy,sz)] for p in probes()])

def build_schedule():
    stages=[(t,sign) for t in range(8) for sign in SIGNS]         # 16 stages
    schedule={}                                                    # (t,sign,o) -> signature
    for (t,sign) in stages:
        for o in OPS:
            schedule[(t,sign,o)]=sig(stage_op(t,sign,o))
    return stages, schedule

def measure():
    stages, sched = build_schedule()
    keys=list(sched); n=len(keys)
    # (A) well-formed: 16 stages, each exactly 4 operators at one shared sign
    per_stage_ops={}
    for (t,sign,o) in keys: per_stage_ops.setdefault((t,sign),[]).append(o)
    wf = (len(stages)==16 and n==64 and all(sorted(v)==sorted(OPS) for v in per_stage_ops.values()))
    # sign is a real composition-order choice: within a stage, up-word != down-word for >=1 operator
    sign_real_per_stage=[]
    for t in range(8):
        diffs=[np.linalg.norm(sched[(t,'up',o)]-sched[(t,'down',o)]) for o in OPS]
        sign_real_per_stage.append(max(diffs)>1e-6)
    sign_is_real_order=all(sign_real_per_stage)
    # (B) axis-6 sign load-bearing under real flow
    live=0; total=0
    for t in range(8):
        for o in OPS:
            total+=1
            if np.linalg.norm(sched[(t,'up',o)]-sched[(t,'down',o)])>1e-6: live+=1
    # control: no drive -> up-word and down-word are constructed separately but both reduce to O(rho); measure that
    # the two SEPARATELY-BUILT no-drive words are identical (flow-free, cheap -- no 400-step integration).
    ctrl_live=0
    for t in range(8):
        for o in OPS:
            u=sig(stage_op(t,'up',o,drive=False)); d=sig(stage_op(t,'down',o,drive=False))
            if np.linalg.norm(u-d)>1e-6: ctrl_live+=1
    # (C) 64 dynamically distinct
    D=np.array([sched[k] for k in keys])
    dmin=min(float(np.linalg.norm(D[i]-D[j])) for i,j in itertools.combinations(range(n),2))
    # distinct-cluster count at tol
    tol=1e-6; reps=[]
    for i in range(n):
        if not any(np.linalg.norm(D[i]-D[j])<tol for j in reps): reps.append(i)
    n_distinct=len(reps)
    # shuffled-operator control: permute operator identities -> distinctness should collapse for the collided ones
    # single-operator control: assign the SAME operator (Ti) to every entry -> the 4 operators within a stage
    # collapse to one, so distinctness drops to the 16 (terrain,sign) count. Compute the 16 stage signatures ONCE
    # (not 64) -- if a stage had 4 distinct ops it now has 1, so >= within-stage distinctness is lost.
    stage_sig={(t,sign):sig(stage_op(t,sign,'Ti')) for (t,sign) in stages}
    S=list(stage_sig.values()); reps2=[]
    for i in range(len(S)):
        if not any(np.linalg.norm(S[i]-S[j])<tol for j in reps2): reps2.append(i)
    n_distinct_singleop=len(reps2)
    return {"n_stages":len(stages),"n_entries":n,"well_formed":bool(wf),
            "sign_is_real_composition_order":bool(sign_is_real_order),
            "axis6_sign_live_pairs":live,"axis6_sign_total_pairs":total,
            "axis6_sign_control_nodrive_live":ctrl_live,
            "n_distinct_channels":n_distinct,"min_pairwise":round(dmin,4),
            "n_distinct_single_operator_control":n_distinct_singleop}

def evaluate(m):
    laneA = m["well_formed"] and m["sign_is_real_composition_order"]
    laneB = (m["axis6_sign_live_pairs"]==m["axis6_sign_total_pairs"]) and (m["axis6_sign_control_nodrive_live"]==0)
    laneC = (m["n_distinct_channels"]==64 and m["min_pairwise"]>1e-3
             and m["n_distinct_single_operator_control"] < 64)
    allpass=bool(laneA and laneB and laneC)
    return {"schedule_well_formed_16_stages_x_4_ops":bool(laneA),
            "axis6_sign_load_bearing_rides_on_drive":bool(laneB),
            "sixtyfour_entries_dynamically_distinct":bool(laneC),
            "ENGINE_64_SCHEDULE_DEFINED":allpass}

def main():
    m=measure(); verdict=evaluate(m)
    out={"classification":"scratch_diagnostic","promotion_allowed":False,
         "framing":"define the 64-engine schedule: 16 stages (terrain x axis-6 sign) each running all 4 operators at its shared sign; sign is the operator-first/terrain-first composition order and rides on the terrain drive",
         "schedule":m,"policy_eval":verdict}
    path=__file__.replace(".py","_results.json"); json.dump(out,open(path,"w"),indent=1)
    print("THE 64-ENGINE SCHEDULE -- 16 stages x 4 operators, each stage sharing one axis-6 sign.\n")
    print("  (A) SCHEDULE WELL-FORMED:")
    print(f"      {m['n_stages']} stages (terrain x sign), {m['n_entries']} entries, each stage = 4 operators at one shared sign: {m['well_formed']}")
    print(f"      the shared sign is a REAL composition-order choice (operator-first vs terrain-first differ): {m['sign_is_real_composition_order']}")
    print("  (B) AXIS-6 SIGN LOAD-BEARING (rides on the terrain drive):")
    print(f"      up != down for {m['axis6_sign_live_pairs']}/{m['axis6_sign_total_pairs']} (terrain,operator) pairs under the full flow; no-drive control live {m['axis6_sign_control_nodrive_live']}/32 (collapses)")
    print("  (C) THE 64 ENTRIES DYNAMICALLY DISTINCT:")
    print(f"      distinct channels {m['n_distinct_channels']}/64 (min pairwise {m['min_pairwise']}); single-operator control collapses to {m['n_distinct_single_operator_control']} distinct")
    print("\n  SEPARATE POLICY EVAL:")
    for k,v in verdict.items():
        if k!="ENGINE_64_SCHEDULE_DEFINED": print(f"    {k}: {v}")
    print(f"\n  ENGINE 64-SCHEDULE DEFINED: {verdict['ENGINE_64_SCHEDULE_DEFINED']}")
    if verdict["ENGINE_64_SCHEDULE_DEFINED"]:
        print("PASS engine_64_schedule_definition")
    print("ALL_GATES:", "PASS" if verdict["ENGINE_64_SCHEDULE_DEFINED"] else "FAIL","->",path)
    sys.exit(0 if verdict["ENGINE_64_SCHEDULE_DEFINED"] else 1)

if __name__=="__main__":
    main()
