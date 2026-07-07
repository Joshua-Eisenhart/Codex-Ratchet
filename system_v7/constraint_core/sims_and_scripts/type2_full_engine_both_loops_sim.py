#!/usr/bin/env python3
"""type2_full_engine_both_loops -- RUNG 4 of the staged engine build (owner: "after both type 1 and 2 have had
both their loops"). This builds the Type-2 (RIGHT Weyl, eps=-1, terrains [4,5,6,7]) full engine the same
doc-faithful way rung 2+3 built Type 1: both loops as 4-stage objects, shown distinct, composed into the full
engine, with axis-0 threaded to the spinor-level polarity readout -- and the SAME falsifiable chirality-erase
control. Type 2 is the mirror engine; its polarity must read OPPOSITE to Type 1.

THE TWO LOOPS (doc attachment 2026-07-06T08-14 sec 5, Type-2 chart):
  OUTER loop is INDUCTIVE for Type 2: terrain order Se->Si->Ni->Ne = [4,7,6,5], operators (Fi,Te,Te,Fi).
  INNER loop is DEDUCTIVE for Type 2: terrain order Se->Ne->Ni->Si = [4,5,6,7], operators (Ti,Ti,Fe,Fe).
  (Note the outer/inner loop-tense assignment is MIRRORED vs Type 1, per the source chart -- Type 1 outer is
  deductive, Type 2 outer is inductive. This is part of what makes them mirror engines, not relabelings.)

FOUR LANES (each a measurement; SEPARATE policy eval; controls flip):
  (A) EACH LOOP IS 4 ORDERED STAGES: both Type-2 loops have pairwise-distinct stage maps and are order-sensitive
      (permutation spread) vs a genuinely-commuting control (~0).
  (B) THE TWO LOOPS ARE DISTINCT: different endpoints over a probe ensemble AND complementary operator families
      (outer {Fi,Fi,Te,Te}, inner {Fe,Fe,Ti,Ti}). Control: same loop twice -> gap 0.
  (C) THE FULL ENGINE = BOTH LOOPS, LOOP-ORDER SENSITIVE (N01 between loops): outer-then-inner != inner-then-outer.
      Control: two commuting loops -> gap 0.
  (D) AXIS-0 POLARITY IS OPPOSITE TO TYPE 1: the full-engine polarity is the density-trajectory SIGNED VOLUME
      through the whole flow+operators (an operator-dependent chirality readout, NOT a label read-back). Type 2
      reads the OPPOSITE sign to Type 1 (~+0.011 vs ~-0.020, robust across seeds). TWO REAL CONTROLS: (1) flip the
      Hamiltonian chirality IN THE FLOW (eps->+1 for every Type-2 terrain, keeping operators/poles/kinds) -- this
      genuinely changes Type-2's trajectory and it then reads Type-1's sign (opposition collapses); (2) no Bloch-
      axis relabeling (any of the 8 sign-flips) maps Type-2's endpoint signature onto Type-1's -- min distance ~1.5
      -- so they are genuinely different channels, not relabelings. This corrects an earlier circular readout (the
      spinor holonomy used only eps, so it read the chirality label back and its "erase" control was a no-op).

QUARANTINE_EXPLORATORY. classification="scratch_diagnostic". promotion_allowed=False. Real oracle operators
(reconstructed inline verbatim). Pure distinguishability. Doc-faithful canonical slots (attachment sec 5). NOT a
claim of a full validated engine; the loop ORDERS are the source chart's, not re-derived here.
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
# Type-2 canonical slots (attachment sec 5): (terrain, operator, axis-6 sign)
T2_OUT=[(4,'Fi','up'),(7,'Te','up'),(6,'Te','down'),(5,'Fi','down')]   # outer inductive Se->Si->Ni->Ne
T2_IN =[(4,'Ti','down'),(5,'Ti','up'),(6,'Fe','up'),(7,'Fe','down')]   # inner deductive Se->Ne->Ni->Si
# Type-1 slots (for the polarity comparison)
T1_OUT=[(0,'Ti','up'),(1,'Ti','down'),(2,'Fe','down'),(3,'Fe','up')]
T1_IN =[(0,'Fi','down'),(3,'Te','down'),(2,'Te','up'),(1,'Fi','up')]

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
    if sign=='up': return lambda r: flow(X, O(r.copy()))
    else:          return lambda r: O(flow(X, r.copy()))
def _step(slot, r, eps_override=None):
    t,o,sign=slot; X=gen(t,eps_override); O=op(o)
    r2=flow(X,O(r.copy())) if sign=='up' else O(flow(X,r.copy()))
    r2=.5*(r2+r2.conj().T); r2/=np.trace(r2).real; return r2
def loop_traj(slots, probe):
    r=dm(np.array(probe,float)); traj=[bloch(r).copy()]
    for s in slots: r=_step(s,r); traj.append(bloch(r).copy())
    return np.array(traj)
def compose_loops(slots1, slots2, probe, eps_override=None):
    r=dm(np.array(probe,float)); traj=[bloch(r).copy()]
    for s in slots1+slots2: r=_step(s,r,eps_override); traj.append(bloch(r).copy())
    return np.array(traj)
def signed_volume(traj):
    # density-trajectory chirality: signed volume of successive Bloch triples. Depends on the FULL flow AND the
    # operators (not a label read-back). This is the full-engine polarity readout.
    return float(sum(np.dot(traj[i],np.cross(traj[i+1],traj[i+2])) for i in range(len(traj)-2)))

def _loop_is_ordered(slots, seed):
    rng=np.random.default_rng(seed); probes=[p/np.linalg.norm(p)*0.7 for p in [rng.standard_normal(3) for _ in range(6)]]
    chans=[stage_channel(s) for s in slots]
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
    return dmin, spread, cspread

# ---------- lane A ----------
def measure_loops_ordered():
    od,os_,oc=_loop_is_ordered(T2_OUT,4); idd,is_,ic=_loop_is_ordered(T2_IN,5)
    return {"outer_min_pairwise":round(od,4),"outer_order_spread":round(os_,4),"outer_commuting_control":round(oc,8),
            "inner_min_pairwise":round(idd,4),"inner_order_spread":round(is_,4),"inner_commuting_control":round(ic,8),
            "both_loops_four_ordered_stages":bool(od>1e-3 and os_>1e-2 and oc<1e-9 and idd>1e-3 and is_>1e-2 and ic<1e-9)}

# ---------- lane B ----------
def measure_two_loops_distinct():
    rng=np.random.default_rng(8); probes=[p/np.linalg.norm(p)*0.6 for p in [rng.standard_normal(3) for _ in range(8)]]
    out_ends=[loop_traj(T2_OUT,p)[-1] for p in probes]; in_ends=[loop_traj(T2_IN,p)[-1] for p in probes]
    mean_gap=float(np.mean([np.linalg.norm(a-b) for a,b in zip(out_ends,in_ends)]))
    same_gap=float(np.mean([np.linalg.norm(loop_traj(T2_OUT,p)[-1]-loop_traj(T2_OUT,p)[-1]) for p in probes]))
    out_ops=sorted(o for (_,o,_) in T2_OUT); in_ops=sorted(o for (_,o,_) in T2_IN)
    return {"outer_vs_inner_endpoint_gap":round(mean_gap,4),"same_loop_control_gap":round(same_gap,8),
            "outer_operators":out_ops,"inner_operators":in_ops,
            "two_loops_distinct":bool(mean_gap>1e-2 and same_gap<1e-9),
            "loops_use_complementary_operators":bool(out_ops!=in_ops)}

# ---------- lane C ----------
def measure_full_engine_composition():
    rng=np.random.default_rng(6); probes=[p/np.linalg.norm(p)*0.6 for p in [rng.standard_normal(3) for _ in range(8)]]
    oi=[compose_loops(T2_OUT,T2_IN,p)[-1] for p in probes]; io=[compose_loops(T2_IN,T2_OUT,p)[-1] for p in probes]
    loop_order_gap=float(np.mean([np.linalg.norm(a-b) for a,b in zip(oi,io)]))
    def zdeph(g):
        P0=.5*(I2+sz);P1=.5*(I2-sz); return lambda r:(1-g)*r+g*(P0@r@P0+P1@r@P1)
    def cc(gs,probe):
        r=dm(np.array(probe,float))
        for g in gs: r=zdeph(g)(r.copy())
        return bloch(r)
    cgap=float(np.mean([np.linalg.norm(cc([0.2,0.4,0.6,0.8],p)-cc([0.6,0.8,0.2,0.4],p)) for p in probes]))
    return {"full_engine_loop_order_gap":round(loop_order_gap,4),"commuting_loop_order_control_gap":round(cgap,8),
            "full_engine_loop_order_sensitive":bool(loop_order_gap>1e-2 and cgap<1e-9)}

# ---------- lane D ----------
def measure_axis0_mirror():
    rng=np.random.default_rng(9); probes=[p/np.linalg.norm(p)*0.6 for p in [rng.standard_normal(3) for _ in range(40)]]
    # POLARITY = density-trajectory signed volume through the FULL flow+operators (operator-dependent, not a label
    # read-back). Type-2 reads OPPOSITE sign to Type-1 -- measured, robust across seeds.
    read_T2=float(np.mean([signed_volume(compose_loops(T2_OUT,T2_IN,p)) for p in probes]))
    read_T1=float(np.mean([signed_volume(compose_loops(T1_OUT,T1_IN,p)) for p in probes]))
    # REAL CONTROL 1: flip the Hamiltonian chirality IN THE FLOW for Type-2 (eps->+1 everywhere) -- this genuinely
    # changes Type-2's trajectory (keeps its operators, poles, terrain kinds; only the coherent drive sign flips).
    # Type-2 then reads Type-1's sign: the mirror opposition collapses.
    erased_T2=float(np.mean([signed_volume(compose_loops(T2_OUT,T2_IN,p,eps_override=+1)) for p in probes]))
    # REAL CONTROL 2: are T1/T2 just Bloch-axis relabelings? Try all 8 sign-flips of the Bloch axes on T2's endpoint
    # signature; if none maps it onto T1 (min distance large), they are genuinely DIFFERENT channels, not relabels.
    sigT1=np.concatenate([compose_loops(T1_OUT,T1_IN,p)[-1] for p in probes[:8]])
    best=1e9
    for fx in (1,-1):
        for fy in (1,-1):
            for fz in (1,-1):
                F=np.diag([fx,fy,fz]).astype(float)
                sigT2=np.concatenate([F@compose_loops(T2_OUT,T2_IN,p)[-1] for p in probes[:8]])
                best=min(best, float(np.linalg.norm(sigT1-sigT2)))
    return {"type2_polarity":round(read_T2,5),"type1_polarity":round(read_T1,5),
            "type2_chirality_flipped_in_flow":round(erased_T2,5),
            "best_bloch_relabeling_distance":round(best,4),
            "type2_opposite_to_type1":bool(np.sign(read_T2)!=np.sign(read_T1)),
            "chirality_flip_collapses_opposition":bool(np.sign(erased_T2)==np.sign(read_T1)),
            "not_a_relabeling_of_type1":bool(best>0.1)}

def evaluate(a,b,c,d):
    laneA=a["both_loops_four_ordered_stages"]
    laneB=b["two_loops_distinct"] and b["loops_use_complementary_operators"]
    laneC=c["full_engine_loop_order_sensitive"]
    laneD=d["type2_opposite_to_type1"] and d["chirality_flip_collapses_opposition"] and d["not_a_relabeling_of_type1"]
    allpass=bool(laneA and laneB and laneC and laneD)
    return {"both_loops_four_ordered_stages":bool(laneA),
            "two_loops_distinct_complementary":bool(laneB),
            "full_engine_both_loops_order_sensitive":bool(laneC),
            "axis0_polarity_opposite_to_type1":bool(laneD),
            "TYPE2_FULL_ENGINE_BOTH_LOOPS_BUILT":allpass}

def main():
    a=measure_loops_ordered(); b=measure_two_loops_distinct(); c=measure_full_engine_composition(); d=measure_axis0_mirror()
    verdict=evaluate(a,b,c,d)
    out={"classification":"scratch_diagnostic","promotion_allowed":False,
         "framing":"rung 4 of the staged engine build: the Type-2 (RIGHT Weyl, mirror) full engine -- both loops as 4-stage objects, distinct, composed and loop-order sensitive, axis-0 polarity OPPOSITE to Type 1 at the spinor level with a falsifiable chirality-erase control",
         "loops_ordered":a,"two_loops":b,"full_engine":c,"axis0_mirror":d,"policy_eval":verdict}
    path=__file__.replace(".py","_results.json"); json.dump(out,open(path,"w"),indent=1)
    print("TYPE 2 FULL ENGINE (RIGHT Weyl, mirror) -- both loops + axis-0 polarity opposite to Type 1.\n")
    print("  (A) EACH LOOP IS 4 ORDERED STAGES:")
    print(f"      outer: min {a['outer_min_pairwise']}, spread {a['outer_order_spread']} vs ctrl {a['outer_commuting_control']}; inner: min {a['inner_min_pairwise']}, spread {a['inner_order_spread']} vs ctrl {a['inner_commuting_control']} -> {a['both_loops_four_ordered_stages']}")
    print("  (B) THE TWO LOOPS ARE DISTINCT (complementary operators):")
    print(f"      outer vs inner endpoint gap {b['outer_vs_inner_endpoint_gap']} (same-loop ctrl {b['same_loop_control_gap']}); outer ops {b['outer_operators']} vs inner ops {b['inner_operators']} -> {b['loops_use_complementary_operators']}")
    print("  (C) FULL ENGINE = BOTH LOOPS, LOOP-ORDER SENSITIVE:")
    print(f"      outer-then-inner vs inner-then-outer gap {c['full_engine_loop_order_gap']} vs commuting ctrl {c['commuting_loop_order_control_gap']} -> {c['full_engine_loop_order_sensitive']}")
    print("  (D) AXIS-0 POLARITY OPPOSITE TO TYPE 1 (density signed-volume through the full flow):")
    print(f"      Type-2 polarity {d['type2_polarity']:+.5f} vs Type-1 {d['type1_polarity']:+.5f} (opposite {d['type2_opposite_to_type1']})")
    print(f"      CONTROL 1 (flip Hamiltonian chirality in the flow, eps->+1): Type-2 -> {d['type2_chirality_flipped_in_flow']:+.5f} = Type-1 sign, opposition collapses {d['chirality_flip_collapses_opposition']}")
    print(f"      CONTROL 2 (Bloch-axis relabeling): best T1<->T2 distance {d['best_bloch_relabeling_distance']} -> genuinely different channels, not a relabeling {d['not_a_relabeling_of_type1']}")
    print("\n  SEPARATE POLICY EVAL:")
    for k,v in verdict.items():
        if k!="TYPE2_FULL_ENGINE_BOTH_LOOPS_BUILT": print(f"    {k}: {v}")
    print(f"\n  TYPE 2 FULL ENGINE (BOTH LOOPS) BUILT: {verdict['TYPE2_FULL_ENGINE_BOTH_LOOPS_BUILT']}")
    if verdict["TYPE2_FULL_ENGINE_BOTH_LOOPS_BUILT"]:
        print("PASS type2_full_engine_both_loops")
    print("ALL_GATES:", "PASS" if verdict["TYPE2_FULL_ENGINE_BOTH_LOOPS_BUILT"] else "FAIL","->",path)
    sys.exit(0 if verdict["TYPE2_FULL_ENGINE_BOTH_LOOPS_BUILT"] else 1)

if __name__=="__main__":
    main()
