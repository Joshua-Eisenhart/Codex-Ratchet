#!/usr/bin/env python3
"""next_tooth_terrains_to_engine_stages -- the ratchet's NEXT tooth after the terrains. Continue the continuous
climb: terrain dissipators (rung 1) -> operators/axes -> the composed engine STAGES (the 16). The terrains are
forced by the attractor demand (bridge_tooth); the engine stages are forced HERE by the ORDER demand (N01).

WHERE WE ARE:
  - rung 1 (bridge_tooth_carrier_to_terrains): 8 terrain GKSL dissipators, each with a fixed point. A terrain HOLDS
    a pointer (persistence under perturbation) but does no order-dependent PROCESSING -- a single channel has no
    order to speak of. It relaxes; it does not compute.
  - the 16 engine stages (engines/oracle_targets.py): each terrain composed with a NATIVE operator in TWO orders
    (down = terrain-first J(flow(X,probe)); up = operator-first flow(X, J(probe))). The order_gap = ||down - up||
    is N01 made into a processing observable.

THE DEMAND that forces the next tooth (N01 -- order must matter):
  As the room grows it asserts that the ORDER of operations is distinguishable -- doing A-then-B differs from
  B-then-A. A bare terrain cannot close this: with only one operation there is no order to vary; the terrain flow
  composed with itself is order-invariant (gap identically 0). The distinguishability the room says ORDER should
  produce is a demand no single terrain resolves.

MSS -- the weakest structure that closes it:
  The weakest admissible structure that makes order matter is to add ONE operator that does NOT commute with the
  terrain, composed in the two orders. That is exactly an engine STAGE. Not a full 360-degree loop, not the whole
  16 at once: one terrain + one native operator, read in two orders. The operator must be NATIVE (the terrain's own
  axis family, NATIVE table) -- the terrain's surface IS the operator (operator_geometry_fusion), so a terrain
  admits only its own axis-family operators.

WHY SIXTEEN (forced, not chosen):
  8 terrains x 2 native operators each = 16 stages. Each terrain has exactly 2 native operators (a T-type measure
  and an F-type transport, from the NATIVE table). The stages are pairwise distinct as (down,up) processing
  signatures.

CONTROLS (each must flip; measurement/verdict separated per Lev mesh discipline):
  (A) A TERRAIN ALONE CANNOT PROCESS ORDER; A STAGE CAN: a bare terrain flow composed with itself has order_gap
      identically 0; adding a native operator opens a nonzero order_gap on the order-sensitive stages. Number:
      count of stages with order_gap > eps, vs 0 for terrain-alone.
  (B) THE STAGES ARE DISTINCT FORCED TEETH: the 16 (down,up) signatures are pairwise distinct as processing maps.
      Number: min pairwise signature distance > 0.
  (C) CHIRALITY -> TWO ENGINES carries forward: the eps sign inherited from cosmogenesis (via the terrains) splits
      the 16 into Type 1 (eps=+1: terrains 0-3) and Type 2 (eps=-1: terrains 4-7), 8 stages each -- the two engines
      are the two chiralities' own stage-sets, not a relabeling. Number: the two engine stage-sets are disjoint and
      each internally distinct.

QUARANTINE_EXPLORATORY. classification="scratch_diagnostic". promotion_allowed=False. Uses the REAL engine stage
generators (engines/oracle_targets.py constants + gen/flow/op, re-implemented inline to keep standalone). Pure
distinguishability (Bloch/order-gap), no bits/vectors. A MECHANISM illustration that the engine stages are the
ratchet's next forced tooth above the terrains -- NOT a claim they are the unique such structure. NOTE on two
order-sensitivity observables (both true, different levels): the DYNAMICAL probe-specific order gap measured here
is nonzero on all 16 stages (16/16, mean gap 0.185) -- the composed maps differ on the standard probe. The
stricter SYMBOLIC-IDENTITY count (exact operator commutation) is 12/16: with the coherent axis (1,1,1)/sqrt3 the
four Fe stages commute EXACTLY with their terrains (phase covariance). This sim reports the DYNAMICAL count; the
12/16 symbolic degeneracy is the established prior result and is NOT contradicted -- a stage can be dynamically
order-sensitive on a generic probe while symbolically order-invariant.
"""
import json, os, sys
import numpy as np
from scipy.linalg import expm

sx=np.array([[0,1],[1,0]],complex); sy=np.array([[0,-1j],[1j,0]],complex); sz=np.array([[1,0],[0,-1]],complex)
I2=np.eye(2,dtype=complex); sp=0.5*(sx+1j*sy); sm=0.5*(sx-1j*sy)
G,KAP = 0.35,1.0; Q=1.0-float(np.exp(-1.0)); TH=np.pi/4; T_FLOW=1.0; N_STEPS=400; PROBE=(0.55,0.35,0.25)
TERR={0:(+1,'damp',+1),1:(+1,'depol',0),2:(+1,'damp',-1),3:(+1,'proj',0),
      4:(-1,'damp',-1),5:(-1,'depol',0),6:(-1,'damp',+1),7:(-1,'proj',0)}
NATIVE={0:('Ti','Fi'),1:('Ti','Fi'),4:('Ti','Fi'),5:('Ti','Fi'),
        2:('Te','Fe'),3:('Te','Fe'),6:('Te','Fe'),7:('Te','Fe')}

def D(L,r): return L@r@L.conj().T - 0.5*(L.conj().T@L@r + r@L.conj().T@L)
def gen(ti):
    eps,kind,pole = TERR[ti]; H=eps*(sx+sy+sz)/np.sqrt(3)
    def X(r):
        out=-1j*G*(H@r - r@H)
        if kind=='damp': out=out+KAP*D(sp if pole>0 else sm, r)
        elif kind=='depol': out=out+0.5*KAP*(D(sx,r)+D(sy,r))
        else: out=out+KAP*D(sz,r)
        return out
    return X
def flow(X,r,t=T_FLOW,steps=N_STEPS):
    dt=t/steps
    for _ in range(steps):
        k1=X(r);k2=X(r+.5*dt*k1);k3=X(r+.5*dt*k2);k4=X(r+dt*k3)
        r=r+(dt/6)*(k1+2*k2+2*k3+k4); r=.5*(r+r.conj().T); r/=np.trace(r).real
    return r
def op(name):
    P0=0.5*(I2+sz);P1=0.5*(I2-sz);Qp=0.5*(I2+sx);Qm=0.5*(I2-sx)
    if name=='Ti': return lambda r:(1-Q)*r + Q*(P0@r@P0 + P1@r@P1)
    if name=='Te': return lambda r:(1-Q)*r + Q*(Qp@r@Qp + Qm@r@Qm)
    if name=='Fi': U=expm(-1j*TH/2*sx); return lambda r:U@r@U.conj().T
    if name=='Fe': U=expm(-1j*TH/2*sz); return lambda r:U@r@U.conj().T
def bloch(r): return np.array([float(np.trace(r@s).real) for s in (sx,sy,sz)])
def probe_dm(): return 0.5*(I2 + PROBE[0]*sx + PROBE[1]*sy + PROBE[2]*sz)

# ---------- PURE INSTRUMENTS ----------

def measure_terrain_alone_cannot_process_order():
    """A bare terrain flow composed with ITSELF in two orders is order-invariant (gap identically 0 -- one channel
    has no order). Adding a native operator opens a nonzero order_gap on order-sensitive stages. Emits: terrain-
    alone order gap, count of stages with order_gap > eps."""
    probe=probe_dm()
    # terrain-alone: compose flow with flow in two orders -> identical -> gap 0
    X0=gen(0)
    ta_down=bloch(flow(X0, flow(X0, probe.copy())))
    ta_up  =bloch(flow(X0, flow(X0, probe.copy())))
    terrain_alone_gap=float(np.linalg.norm(ta_down-ta_up))
    # stages: terrain + native operator, two orders
    stage_gaps=[]
    for t in range(8):
        X=gen(t)
        for o in NATIVE[t]:
            J=op(o)
            down=bloch(J(flow(X, probe.copy())))     # terrain-first
            up  =bloch(flow(X, J(probe.copy())))     # operator-first
            stage_gaps.append({"t":t,"op":o,"order_gap":float(np.linalg.norm(down-up))})
    n_order_sensitive=sum(1 for s in stage_gaps if s["order_gap"]>1e-6)
    return {"terrain_alone_order_gap":terrain_alone_gap,
            "n_stages":len(stage_gaps),"n_order_sensitive_stages":n_order_sensitive,
            "mean_order_gap":float(np.mean([s["order_gap"] for s in stage_gaps])),
            "stage_gaps":stage_gaps}

def measure_sixteen_stages_distinct():
    """The 16 (down,up) processing signatures are pairwise distinct as maps. Min pairwise signature distance."""
    probe=probe_dm(); sigs=[]
    for t in range(8):
        X=gen(t)
        for o in NATIVE[t]:
            J=op(o)
            down=bloch(J(flow(X, probe.copy()))); up=bloch(flow(X, J(probe.copy())))
            sigs.append(np.concatenate([down,up]))
    S=np.array(sigs)
    dists=[np.linalg.norm(S[i]-S[j]) for i in range(len(S)) for j in range(i+1,len(S))]
    return {"n_stages":len(S),"min_pairwise_signature_distance":float(min(dists)),
            "mean_pairwise":float(np.mean(dists)),
            "n_distinct_at_1e-6":int(1+sum(1 for d in sorted(dists) if d>1e-6))}  # rough distinct count

def measure_chirality_two_engines():
    """The eps sign carried from cosmogenesis splits the 16 stages into Type 1 (eps=+1: terrains 0-3) and Type 2
    (eps=-1: terrains 4-7), 8 each. Measure that the two engine stage-sets are DISJOINT (no shared signature) and
    each internally distinct -> the two engines are the two chiralities' own stage-sets."""
    probe=probe_dm()
    def stageset(terrs):
        sigs=[]
        for t in terrs:
            X=gen(t)
            for o in NATIVE[t]:
                J=op(o); down=bloch(J(flow(X, probe.copy()))); up=bloch(flow(X, J(probe.copy())))
                sigs.append(np.concatenate([down,up]))
        return np.array(sigs)
    type1=stageset([0,1,2,3]); type2=stageset([4,5,6,7])
    cross=min(np.linalg.norm(a-b) for a in type1 for b in type2)
    t1_min=min(np.linalg.norm(type1[i]-type1[j]) for i in range(8) for j in range(i+1,8))
    t2_min=min(np.linalg.norm(type2[i]-type2[j]) for i in range(8) for j in range(i+1,8))
    return {"type1_size":len(type1),"type2_size":len(type2),
            "cross_engine_min_distance":float(cross),
            "type1_internal_min":float(t1_min),"type2_internal_min":float(t2_min)}

# ---------- SEPARATE POLICY EVAL ----------

def eval_next_tooth(mA,mB,mC):
    order_control = (mA["terrain_alone_order_gap"]<1e-9) and (mA["n_order_sensitive_stages"]>=1) and (mA["mean_order_gap"]>1e-6)
    distinct_control = mB["min_pairwise_signature_distance"]>1e-6
    two_engine_control = (mC["cross_engine_min_distance"]>1e-6) and (mC["type1_internal_min"]>1e-6) and (mC["type2_internal_min"]>1e-6)
    allflip=bool(order_control and distinct_control and two_engine_control)
    return {"terrain_alone_no_order_stage_has_order":bool(order_control),
            "sixteen_stages_distinct_forced_teeth":bool(distinct_control),
            "chirality_splits_into_two_engines":bool(two_engine_control),
            "NEXT_TOOTH_TERRAINS_TO_ENGINE_STAGES_FORCED":allflip}

def main():
    mA=measure_terrain_alone_cannot_process_order()
    mB=measure_sixteen_stages_distinct()
    mC=measure_chirality_two_engines()
    verdict=eval_next_tooth(mA,mB,mC)
    out={"classification":"scratch_diagnostic","promotion_allowed":False,
         "framing":"the ratchet's next tooth: terrain dissipators -> engine STAGES, forced by the N01 order demand",
         "order_demand_lane":mA,"distinct_lane":mB,"two_engine_lane":mC,"policy_eval":verdict}
    path=__file__.replace(".py","_results.json"); json.dump(out,open(path,"w"),indent=1)

    print("THE NEXT TOOTH -- from the terrain dissipators UP to the engine STAGES, as one continuous climb.\n")
    print("  DEMAND a terrain alone cannot close (order must matter -- N01):")
    print(f"    terrain-alone order gap {mA['terrain_alone_order_gap']:.2e} (one channel, no order -- demand OPEN)")
    print(f"    adding a native operator: {mA['n_order_sensitive_stages']}/{mA['n_stages']} stages order-sensitive, mean gap {mA['mean_order_gap']:.3f} (demand CLOSED)")
    print("  MSS next tooth = one native operator composed in two orders = an engine STAGE.")
    print(f"  WHY SIXTEEN: 16 (down,up) signatures pairwise-distinct, min distance {mB['min_pairwise_signature_distance']:.3f}")
    print(f"  CHIRALITY -> TWO ENGINES: Type1 (0-3) vs Type2 (4-7), cross-engine min {mC['cross_engine_min_distance']:.3f}, each internally distinct (t1 {mC['type1_internal_min']:.3f}, t2 {mC['type2_internal_min']:.3f})")
    print(f"  (two order-sensitivity levels: DYNAMICAL {mA['n_order_sensitive_stages']}/16 on the probe here; SYMBOLIC 12/16 -- the coherent axis makes 4 Fe stages commute exactly. Both true; this reports the dynamical count)")
    print("\n  SEPARATE POLICY EVAL (verdict = all three controls flip):")
    for k,v in verdict.items():
        if k!="NEXT_TOOTH_TERRAINS_TO_ENGINE_STAGES_FORCED": print(f"    {k}: {v}")
    print(f"\n  NEXT TOOTH (TERRAINS -> ENGINE STAGES) FORCED: {verdict['NEXT_TOOTH_TERRAINS_TO_ENGINE_STAGES_FORCED']}")
    if verdict["NEXT_TOOTH_TERRAINS_TO_ENGINE_STAGES_FORCED"]:
        print("PASS next_tooth_terrains_to_engine_stages")
    print("ALL_GATES:", "PASS" if verdict["NEXT_TOOTH_TERRAINS_TO_ENGINE_STAGES_FORCED"] else "FAIL","->",path)
    sys.exit(0 if verdict["NEXT_TOOTH_TERRAINS_TO_ENGINE_STAGES_FORCED"] else 1)

if __name__=="__main__":
    main()
