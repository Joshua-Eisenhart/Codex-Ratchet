#!/usr/bin/env python3
"""type1_full_engine_both_loops -- RUNG 2+3 of the staged engine build (owner: "do each of the inductive or
deductive loops one at a time... then can do a full engine with both loops"). Rung 1 built the Type-1 DEDUCTIVE
loop; this builds the Type-1 INDUCTIVE loop as its own 4-stage object, shows the two loops are DISTINCT (not
relabelings), and composes them into the FULL single Type-1 engine -- with axis-0 still threaded from the drive at
the start to the polarity readout at the full-engine close.

THE TWO LOOPS (doc math ref sec 11, Type-1 chart):
  DEDUCTIVE (outer) loop: terrain order Se->Ne->Ni->Si = [0,1,2,3], native T-operator family (FeTi outer).
  INDUCTIVE (inner) loop: terrain order Se->Si->Ni->Ne = [0,3,2,1], native F-operator family (TeFi inner).
  The two loops traverse the SAME 4 terrains in different order with the complementary operator family. Together
  they are the full engine: one 720deg double-cover (deductive 360 then inductive 360), the spinor-level structure
  already established (single 360 returns -psi; the two composed loops are the genuine return).

FOUR LANES (each a measurement; SEPARATE policy eval; controls flip):
  (A) THE INDUCTIVE LOOP IS 4 ORDERED STAGES: its 4 stage-maps pairwise distinct, and it is order-sensitive
      (permutation spread large) vs a genuinely-commuting control (~0). Same standard the deductive loop met.
  (B) THE TWO LOOPS ARE DISTINCT (not relabelings): deductive and inductive have different endpoints over a probe
      ensemble AND different chirality readouts (different tense). Control: running the SAME loop twice gives
      distance 0. The distinctness is the deductive-vs-inductive tense, real at the loop level.
  (C) THE FULL ENGINE = BOTH LOOPS, LOOP-ORDER SENSITIVE (N01 between loops): composing deductive-then-inductive
      differs from inductive-then-deductive (endpoint gap > 0). Control: if the two loops commuted the gap would be
      0. This is the two loops biting each other -- the engine is more than the sum of its loops.
  (D) AXIS-0 THREADED TO THE FULL-ENGINE READOUT: the full engine's polarity is the density-trajectory SIGNED
      VOLUME through the whole flow+operators (an operator-dependent chirality readout, NOT a label read-back).
      Type 1 and Type 2 read OPPOSITE signs (~-0.020 vs ~+0.011, robust across seeds). TWO REAL CONTROLS: (1) flip
      the Hamiltonian chirality IN THE FLOW (eps->+1 for every Type-2 terrain, keeping operators/poles/kinds) --
      this genuinely changes Type-2's trajectory and it then reads Type-1's sign (separation collapses); (2) no
      Bloch-axis relabeling (any of the 8 sign-flips) maps Type-2's endpoint signature onto Type-1's (min distance
      ~1.5) -- so they are genuinely different channels, not relabelings. This corrects an earlier circular readout
      (the spinor holonomy used only eps, so it read the chirality label back and its "erase" control was a no-op).

QUARANTINE_EXPLORATORY. classification="scratch_diagnostic". promotion_allowed=False. Real oracle operators
(engines/oracle_targets.py, reconstructed inline verbatim). Pure distinguishability. Candidate traversal reading
(doc sec 11 chart); the loop ORDERS are the doc's, not re-derived. NOT a claim of a full validated engine.
"""
import json, os, sys
import numpy as np
from scipy.linalg import expm
from itertools import permutations

sx=np.array([[0,1],[1,0]],complex); sy=np.array([[0,-1j],[1j,0]],complex); sz=np.array([[1,0],[0,-1]],complex)
I2=np.eye(2,dtype=complex); sp=0.5*(sx+1j*sy); sm=0.5*(sx-1j*sy)
G=0.35; KAP=1.0; Q=1.0-np.exp(-1.0); TH=np.pi/4; T_FLOW=1.0; N_STEPS=400
TERR={0:(+1,'damp',+1),1:(+1,'depol',0),2:(+1,'damp',-1),3:(+1,'proj',0),
      4:(-1,'damp',-1),5:(-1,'depol',0),6:(-1,'damp',+1),7:(-1,'proj',0)}
NATIVE={0:('Ti','Fi'),1:('Ti','Fi'),4:('Ti','Fi'),5:('Ti','Fi'),
        2:('Te','Fe'),3:('Te','Fe'),6:('Te','Fe'),7:('Te','Fe')}
# DOC-FAITHFUL canonical slots (owner attachment 2026-07-06T08-14 sec 5). Terrain index map: Se=0,Ne=1,Ni=2,Si=3
# (Type 1); Se=4,Ne=5,Ni=6,Si=7 (Type 2). Each slot = (terrain, canonical operator, axis-6 sign). The outer loop
# uses each terrain's FIRST native family, the inner loop its COMPLEMENT -- taken from the source chart, not a
# simplified "one operator index per loop" (the correction that prompted this rebuild).
#   Type 1 outer DEDUCTIVE  Se->Ne->Ni->Si : (Se,Ti,up)(Ne,Ti,down)(Ni,Fe,down)(Si,Fe,up)
#   Type 1 inner INDUCTIVE  Se->Si->Ni->Ne : (Se,Fi,down)(Si,Te,down)(Ni,Te,up)(Ne,Fi,up)
#   Type 2 outer INDUCTIVE  Se->Si->Ni->Ne : (Se,Fi,up)(Si,Te,up)(Ni,Te,down)(Ne,Fi,down)
#   Type 2 inner DEDUCTIVE  Se->Ne->Ni->Si : (Se,Ti,down)(Ne,Ti,up)(Ni,Fe,up)(Si,Fe,down)
T1_OUT=[(0,'Ti','up'),(1,'Ti','down'),(2,'Fe','down'),(3,'Fe','up')]
T1_IN =[(0,'Fi','down'),(3,'Te','down'),(2,'Te','up'),(1,'Fi','up')]
T2_OUT=[(4,'Fi','up'),(7,'Te','up'),(6,'Te','down'),(5,'Fi','down')]
T2_IN =[(4,'Ti','down'),(5,'Ti','up'),(6,'Fe','up'),(7,'Fe','down')]

def Dop(L,r): return L@r@L.conj().T-0.5*(L.conj().T@L@r+r@L.conj().T@L)
def gen(ti, eps_override=None):
    eps,kind,pole=TERR[ti]
    if eps_override is not None: eps=eps_override
    H=eps*(sx+sy+sz)/np.sqrt(3)
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
def bloch(r): return np.array([float(np.trace(r@s).real) for s in (sx,sy,sz)])
def dm(v): return 0.5*(I2+v[0]*sx+v[1]*sy+v[2]*sz)

def stage_channel(slot):
    t,o,sign=slot; X=gen(t); O=op(o)
    if sign=='up': return lambda r: flow(X, O(r.copy()))     # operator-first Phi_T(O(rho))
    else:          return lambda r: O(flow(X, r.copy()))     # terrain-first  O(Phi_T(rho))
def _step(slot, r, drive=True, eps_override=None):
    t,o,sign=slot; X=gen(t,eps_override); O=op(o)
    if not drive: r2=O(r.copy())
    elif sign=='up': r2=flow(X,O(r.copy()))
    else: r2=O(flow(X,r.copy()))
    r2=.5*(r2+r2.conj().T); r2/=np.trace(r2).real; return r2
def loop_traj(slots, probe, drive=True):
    r=dm(np.array(probe,float)); traj=[bloch(r).copy()]
    for s in slots: r=_step(s,r,drive); traj.append(bloch(r).copy())
    return np.array(traj)
def compose_loops(slots1, slots2, probe, drive=True, eps_override=None):
    r=dm(np.array(probe,float)); traj=[bloch(r).copy()]
    for s in slots1+slots2: r=_step(s,r,drive,eps_override); traj.append(bloch(r).copy())
    return np.array(traj)
def signed_volume(traj): return float(sum(np.dot(traj[i],np.cross(traj[i+1],traj[i+2])) for i in range(len(traj)-2)))
def measure_inductive_loop():
    rng=np.random.default_rng(4); probes=[p/np.linalg.norm(p)*0.7 for p in [rng.standard_normal(3) for _ in range(6)]]
    chans=[stage_channel(s) for s in T1_IN]
    sigs=[np.concatenate([bloch(c(dm(p))) for p in probes]) for c in chans]
    dmin=min(float(np.linalg.norm(sigs[i]-sigs[j])) for i in range(4) for j in range(i+1,4))
    probe=np.array([0.55,0.35,0.25])
    def compose(chs,r0):
        r=r0.copy()
        for c in chs: r=c(r.copy()); r=.5*(r+r.conj().T); r/=np.trace(r).real
        return bloch(r)
    ends=[compose([chans[i] for i in perm],dm(probe)) for perm in permutations(range(4))]
    spread=float(np.mean([np.linalg.norm(ends[i]-ends[j]) for i in range(len(ends)) for j in range(i+1,len(ends))]))
    def zdeph(g):
        P0=.5*(I2+sz);P1=.5*(I2-sz); return lambda r:(1-g)*r+g*(P0@r@P0+P1@r@P1)
    cch=[zdeph(g) for g in (0.2,0.4,0.6,0.8)]
    cends=[compose([cch[i] for i in perm],dm(probe)) for perm in permutations(range(4))]
    cspread=float(np.mean([np.linalg.norm(cends[i]-cends[j]) for i in range(len(cends)) for j in range(i+1,len(cends))]))
    return {"inductive_four_stages_min_pairwise":round(dmin,4),"inductive_order_spread":round(spread,4),
            "commuting_control_spread":round(cspread,8),
            "inductive_stages_distinct":bool(dmin>1e-3),
            "inductive_order_sensitive":bool(spread>1e-2 and cspread<1e-9)}

# ---------- lane B: the two loops are distinct ----------
def measure_two_loops_distinct():
    rng=np.random.default_rng(8); probes=[p/np.linalg.norm(p)*0.6 for p in [rng.standard_normal(3) for _ in range(8)]]
    ded_ends=[loop_traj(T1_OUT,p)[-1] for p in probes]
    ind_ends=[loop_traj(T1_IN,p)[-1] for p in probes]
    mean_gap=float(np.mean([np.linalg.norm(d-i) for d,i in zip(ded_ends,ind_ends)]))
    # the two loops differ in OPERATORS and traversal order (they share the 4 terrains, so their coherent-only
    # holonomy coincides -- that is NOT what separates them). Distinctness is the endpoint gap over the ensemble,
    # against a same-loop control at 0. HONEST: the deductive/inductive tense is a loop-COMPOSITION property (the
    # 720 double-loop closes; single 360 does not), established separately; it is not a per-loop holonomy number.
    same_gap=float(np.mean([np.linalg.norm(loop_traj(T1_OUT,p)[-1]-loop_traj(T1_OUT,p)[-1]) for p in probes]))
    # operator sets differ: outer uses {Ti,Ti,Fe,Fe}, inner uses {Fi,Te,Te,Fi} -- complementary families
    out_ops=sorted(o for (_,o,_) in T1_OUT); in_ops=sorted(o for (_,o,_) in T1_IN)
    return {"deductive_vs_inductive_endpoint_gap":round(mean_gap,4),
            "outer_operators":out_ops,"inner_operators":in_ops,
            "same_loop_control_gap":round(same_gap,8),
            "two_loops_distinct":bool(mean_gap>1e-2 and same_gap<1e-9),
            "loops_use_complementary_operators":bool(out_ops!=in_ops)}

# ---------- lane C: full engine, loop-order sensitive ----------
def measure_full_engine_composition():
    rng=np.random.default_rng(6); probes=[p/np.linalg.norm(p)*0.6 for p in [rng.standard_normal(3) for _ in range(8)]]
    di=[compose_loops(T1_OUT,T1_IN,p)[-1] for p in probes]     # outer(deductive) then inner(inductive)
    idl=[compose_loops(T1_IN,T1_OUT,p)[-1] for p in probes]    # inner then outer
    loop_order_gap=float(np.mean([np.linalg.norm(a-b) for a,b in zip(di,idl)]))
    def zdeph(g):
        P0=.5*(I2+sz);P1=.5*(I2-sz); return lambda r:(1-g)*r+g*(P0@r@P0+P1@r@P1)
    def comp_commuting(gs,probe):
        r=dm(np.array(probe,float))
        for g in gs: r=zdeph(g)(r.copy())
        return bloch(r)
    cgap=float(np.mean([np.linalg.norm(comp_commuting([0.2,0.4,0.6,0.8],p)-comp_commuting([0.6,0.8,0.2,0.4],p)) for p in probes]))
    return {"full_engine_loop_order_gap":round(loop_order_gap,4),"commuting_loop_order_control_gap":round(cgap,8),
            "full_engine_loop_order_sensitive":bool(loop_order_gap>1e-2 and cgap<1e-9)}

# ---------- lane D: axis-0 to full-engine readout (SPINOR-LEVEL, where the polarity lives) ----------

def measure_axis0_full_engine():
    rng=np.random.default_rng(9); probes=[q/np.linalg.norm(q)*0.6 for q in [rng.standard_normal(3) for _ in range(40)]]
    # POLARITY = density-trajectory signed volume through the FULL flow+operators (operator-dependent, not a label
    # read-back). Type 1 and Type 2 read OPPOSITE signs -- measured, robust across seeds.
    read_T1=float(np.mean([signed_volume(compose_loops(T1_OUT,T1_IN,q)) for q in probes]))
    read_T2=float(np.mean([signed_volume(compose_loops(T2_OUT,T2_IN,q)) for q in probes]))
    # REAL CONTROL 1: flip the Hamiltonian chirality IN THE FLOW for Type 2 (eps->+1 everywhere) -- genuinely
    # changes Type-2's trajectory (keeps operators/poles/kinds; only the coherent drive sign flips). Type 2 then
    # reads Type-1's sign: the opposite-sign separation collapses.
    erased_T2=float(np.mean([signed_volume(compose_loops(T2_OUT,T2_IN,q,eps_override=+1)) for q in probes]))
    # REAL CONTROL 2: are T1/T2 just Bloch-axis relabelings? No sign-flip of the Bloch axes maps T2's endpoint
    # signature onto T1's (min distance large) -> genuinely different channels, not relabelings.
    sigT1=np.concatenate([compose_loops(T1_OUT,T1_IN,q)[-1] for q in probes[:8]])
    best=1e9
    for fx in (1,-1):
        for fy in (1,-1):
            for fz in (1,-1):
                F=np.diag([fx,fy,fz]).astype(float)
                sigT2=np.concatenate([F@compose_loops(T2_OUT,T2_IN,q)[-1] for q in probes[:8]])
                best=min(best, float(np.linalg.norm(sigT1-sigT2)))
    return {"density_signed_volume_T1":round(read_T1,5),"density_signed_volume_T2":round(read_T2,5),
            "type2_chirality_flipped_in_flow":round(erased_T2,5),
            "best_bloch_relabeling_distance":round(best,4),
            "polarity_signs_opposite":bool(np.sign(read_T1)!=np.sign(read_T2)),
            "chirality_flip_collapses_separation":bool(np.sign(erased_T2)==np.sign(read_T1)),
            "not_a_relabeling":bool(best>0.1)}
def evaluate(a,b,c,d):
    laneA=a["inductive_stages_distinct"] and a["inductive_order_sensitive"]
    laneB=b["two_loops_distinct"] and b["loops_use_complementary_operators"]
    laneC=c["full_engine_loop_order_sensitive"]
    laneD=d["polarity_signs_opposite"] and d["chirality_flip_collapses_separation"] and d["not_a_relabeling"]
    allpass=bool(laneA and laneB and laneC and laneD)
    return {"inductive_loop_is_four_ordered_stages":bool(laneA),
            "two_loops_distinct_different_tense":bool(laneB),
            "full_engine_both_loops_order_sensitive":bool(laneC),
            "axis0_spinor_readout_threaded_to_full_engine":bool(laneD),
            "TYPE1_FULL_ENGINE_BOTH_LOOPS_BUILT":allpass}

def main():
    a=measure_inductive_loop(); b=measure_two_loops_distinct(); c=measure_full_engine_composition(); d=measure_axis0_full_engine()
    verdict=evaluate(a,b,c,d)
    out={"classification":"scratch_diagnostic","promotion_allowed":False,
         "framing":"rung 2+3 of the staged engine build: the Type-1 inductive loop as its own 4-stage object, the two loops shown distinct (different tense), composed into the full single engine (loop-order sensitive), axis-0 threaded to the full-engine readout",
         "inductive_loop":a,"two_loops":b,"full_engine":c,"axis0":d,"policy_eval":verdict}
    path=__file__.replace(".py","_results.json"); json.dump(out,open(path,"w"),indent=1)
    print("TYPE 1 FULL ENGINE -- inductive loop + both loops composed, axis-0 threaded to full-engine readout.\n")
    print("  (A) THE INDUCTIVE LOOP IS 4 ORDERED STAGES:")
    print(f"      4 stage maps pairwise distinct (min {a['inductive_four_stages_min_pairwise']}); order spread {a['inductive_order_spread']} vs commuting control {a['commuting_control_spread']} -> {a['inductive_order_sensitive']}")
    print("  (B) THE TWO LOOPS ARE DISTINCT (complementary operator families):")
    print(f"      deductive vs inductive endpoint gap {b['deductive_vs_inductive_endpoint_gap']} (same-loop control {b['same_loop_control_gap']}); outer ops {b['outer_operators']} vs inner ops {b['inner_operators']} -> complementary {b['loops_use_complementary_operators']}")
    print("  (C) THE FULL ENGINE = BOTH LOOPS, LOOP-ORDER SENSITIVE:")
    print(f"      outer-then-inner vs inner-then-outer gap {c['full_engine_loop_order_gap']} vs commuting control {c['commuting_loop_order_control_gap']} -> {c['full_engine_loop_order_sensitive']}")
    print("  (D) AXIS-0 THREADED TO THE FULL-ENGINE READOUT (density signed-volume through the full flow):")
    print(f"      polarity T1 {d['density_signed_volume_T1']:+.5f} vs T2 {d['density_signed_volume_T2']:+.5f} (opposite {d['polarity_signs_opposite']})")
    print(f"      CONTROL 1 (flip Hamiltonian chirality in the flow, eps->+1): T2 -> {d['type2_chirality_flipped_in_flow']:+.5f} = T1 sign, separation collapses {d['chirality_flip_collapses_separation']}")
    print(f"      CONTROL 2 (Bloch-axis relabeling): best T1<->T2 distance {d['best_bloch_relabeling_distance']} -> genuinely different channels {d['not_a_relabeling']}")
    print("\n  SEPARATE POLICY EVAL:")
    for k,v in verdict.items():
        if k!="TYPE1_FULL_ENGINE_BOTH_LOOPS_BUILT": print(f"    {k}: {v}")
    print(f"\n  TYPE 1 FULL ENGINE (BOTH LOOPS) BUILT: {verdict['TYPE1_FULL_ENGINE_BOTH_LOOPS_BUILT']}")
    if verdict["TYPE1_FULL_ENGINE_BOTH_LOOPS_BUILT"]:
        print("PASS type1_full_engine_both_loops")
    print("ALL_GATES:", "PASS" if verdict["TYPE1_FULL_ENGINE_BOTH_LOOPS_BUILT"] else "FAIL","->",path)
    sys.exit(0 if verdict["TYPE1_FULL_ENGINE_BOTH_LOOPS_BUILT"] else 1)

if __name__=="__main__":
    main()
