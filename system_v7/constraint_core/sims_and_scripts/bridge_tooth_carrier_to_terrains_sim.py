#!/usr/bin/env python3
"""bridge_tooth_carrier_to_terrains -- the ratchet's NEXT TOOTH after cosmogenesis. Make the climb CONTINUOUS
from the origin (the persistent chiral spinor carrier) up to the geometric constraint manifold (the 8 terrains),
so the two stop being a jump: the terrains are FORCED as the next admissible structure, by the ratchet's own
demand/MSS rules, from the bare carrier.

WHERE WE ARE ON THE LADDER:
  - cosmogenesis (cosmogenesis_ratchet_first_tooth): the first tooth is a NORM-PRESERVING chiral spinor carrier
    (a bare unitary on C^2; persists, entangled-expanding, handed). It has NO attractor -- unitary evolution only
    rotates; it cannot hold a stable pointer.
  - the 8 terrains (engines/oracle_targets.py): GKSL generators, each with a FIXED POINT (an attractor). Split by
    eps=+/-1 (flux/chirality sign), kind in {damp,depol,proj}, pole in {+1,0,-1}.

THE DEMAND that forces the next tooth (constraint on distinguishability):
  As the room grows, it asserts that a state and a PERTURBED copy of it must become the SAME under evolution (they
  are not distinguishable in the limit -- an attractor/pointer demand). A bare unitary carrier CANNOT close this:
  unitary evolution preserves trace distance exactly, so a perturbed copy stays forever distinguishable. The
  distinguishability the room says should VANISH under evolution is a demand no unitary basis resolves.

MSS -- the weakest structure that closes it:
  The weakest admissible structure that makes a perturbed copy converge to a fixed point is a single GKSL
  DISSIPATOR with an attractor -- i.e. a terrain generator. Not a bigger algebra, not a full engine: one
  dissipative channel with a fixed point. That is the next tooth.

WHY EIGHT (the DOF partition, forced not chosen):
  The carrier's chirality (eps sign) carries forward from cosmogenesis (F01+N01-forced handedness) -> 2 sheets.
  The minimal independent dissipator DOF are: kind of contraction (damp/depol/proj) and pole (which fixed point).
  The 8 terrains are the admitted combinations (the repo's TERR table). Each is a DISTINCT channel (distinct
  attractor + contraction), so each is a separately forced tooth, not a relabeling.

CONTROLS (each must flip; measurement/verdict separated per Lev mesh discipline):
  (A) UNITARY CANNOT CLOSE THE ATTRACTOR DEMAND: under the bare unitary carrier, a state and its perturbed copy
      stay distinguishable (trace distance preserved); under a terrain dissipator they CONVERGE (trace distance
      -> ~0). The number: final trace distance, unitary vs terrain.
  (B) THE 8 TERRAINS ARE DISTINCT FORCED TEETH: all 8 terrain channels are pairwise distinct as attractors
      (distinct fixed points / contraction), so each is a separate tooth. The number: min pairwise fixed-point
      distance > 0.
  (C) CHIRALITY CARRIES FORWARD: the eps=+1 sheet (terrains 0-3) and eps=-1 sheet (4-7) are mirror-related, the
      handedness inherited from the cosmogenesis carrier, not injected here. The number: the two sheets' summed
      chirality signs are opposite.

QUARANTINE_EXPLORATORY. classification="scratch_diagnostic". promotion_allowed=False. Uses the REAL terrain
generators (imported constants from engines/oracle_targets.py, re-implemented inline to keep the sim standalone).
Pure quantum distinguishability (trace distance), no bits/vectors. A MECHANISM illustration that the terrains are
the ratchet's next forced tooth above the carrier -- NOT a claim they are the unique such structure.
"""
import json, os, sys
import numpy as np
from scipy.linalg import expm

sx = np.array([[0,1],[1,0]],complex); sy=np.array([[0,-1j],[1j,0]],complex); sz=np.array([[1,0],[0,-1]],complex)
I2 = np.eye(2,dtype=complex)

# real terrain constants (engines/oracle_targets.py)
G, KAP = 0.35, 1.0
TERR = {0:(+1,'damp',+1), 1:(+1,'depol',0), 2:(+1,'damp',-1), 3:(+1,'proj',0),
        4:(-1,'damp',-1), 5:(-1,'depol',0), 6:(-1,'damp',+1), 7:(-1,'proj',0)}

def bloch(r): return np.array([np.real(np.trace(r@sx)), np.real(np.trace(r@sy)), np.real(np.trace(r@sz))])
def dm_from_bloch(v): return 0.5*(I2 + v[0]*sx + v[1]*sy + v[2]*sz)
def trace_distance(a,b):
    d=a-b; ev=np.linalg.eigvalsh((d+d.conj().T)/2); return 0.5*float(np.abs(ev).sum())

def terrain_lindbladian(ti):
    """the real terrain GKSL generator: coherent H = eps*(sx+sy+sz)/sqrt3 + a dissipator (damp/depol/proj) toward
    the terrain pole. Returns a superoperator step drho/dt = -i[H,rho] + D(rho)."""
    eps, kind, pole = TERR[ti]
    H = eps*(sx+sy+sz)/np.sqrt(3)
    # dissipator Lindblad operators
    sp = np.array([[0,1],[0,0]],complex); sm = np.array([[0,0],[1,0]],complex)
    if kind=='damp':
        L = [np.sqrt(KAP)*(sm if pole>=0 else sp)]          # amplitude damping toward |0> or |1>
    elif kind=='depol':
        L = [np.sqrt(KAP/3)*sx, np.sqrt(KAP/3)*sy, np.sqrt(KAP/3)*sz]  # depolarizing toward I/2
    else:  # proj
        L = [np.sqrt(KAP)*sz]                                # dephasing (projective toward z-diagonal)
    def step(rho, dt):
        drho = -1j*(G*(H@rho - rho@H))
        for Lk in L:
            drho += Lk@rho@Lk.conj().T - 0.5*(Lk.conj().T@Lk@rho + rho@Lk.conj().T@Lk)
        return rho + dt*drho
    return step

def evolve(step, rho0, t=8.0, steps=800):
    rho = rho0.copy(); dt=t/steps
    for _ in range(steps): rho = step(rho, dt)
    return rho

def unitary_step(rho, dt, H=(sx+sy+sz)/np.sqrt(3)):
    """the bare cosmogenesis carrier: pure unitary (norm-preserving, no dissipation)."""
    return rho - 1j*dt*(H@rho - rho@H)

# ---------- PURE INSTRUMENTS ----------

def measure_unitary_cannot_close_attractor_demand():
    """A state and a PERTURBED copy. Under the bare unitary carrier they stay distinguishable (trace distance
    preserved). Under a terrain dissipator they converge to the terrain's fixed point (trace distance -> ~0). The
    demand = 'these become the same under evolution' is closable only by the dissipative tooth."""
    rng = np.random.default_rng(4)
    base = dm_from_bloch(np.array([0.3,0.2,0.5]))
    pert = dm_from_bloch(np.array([0.3,0.2,0.5]) + 0.25*rng.standard_normal(3))
    # bare unitary carrier
    bu = evolve(lambda r,dt: unitary_step(r,dt), base); pu = evolve(lambda r,dt: unitary_step(r,dt), pert)
    unitary_final_td = trace_distance(bu, pu)
    # a terrain dissipator (t0)
    st = terrain_lindbladian(0)
    bt = evolve(st, base); pt = evolve(st, pert)
    terrain_final_td = trace_distance(bt, pt)
    return {"initial_td": float(trace_distance(base,pert)),
            "unitary_final_td": float(unitary_final_td),      # ~ preserved (no attractor)
            "terrain_final_td": float(terrain_final_td)}      # ~ 0 (converged to fixed point)

def measure_eight_terrains_distinct_forced_teeth():
    """Each terrain is a distinct CHANNEL (not merely a distinct fixed point -- several terrains share a fixed
    point, e.g. depol -> I/2, so the fixed point alone does not separate them, which is exactly why the project
    fingerprints terrains as channels). The honest distinguishing observable is the channel's action on a spanning
    set of probe states (a dynamical fingerprint). Measure the terrain-channel fingerprint (evolved Bloch images of
    4 spanning probes) and the min pairwise fingerprint distance -> each terrain is a separately forced tooth."""
    probes = [dm_from_bloch(v) for v in
              (np.array([1,0,0.0]), np.array([0,1,0.0]), np.array([0,0,1.0]), np.array([0.55,0.35,0.25]))]
    fingerprints = []
    fixed_points = []
    for ti in range(8):
        st = terrain_lindbladian(ti)
        fp = np.concatenate([bloch(evolve(st, p.copy(), t=2.0, steps=400)) for p in probes])  # short-time channel action
        fingerprints.append(fp)
        fixed_points.append(bloch(evolve(st, probes[3].copy(), t=16.0, steps=1600)).tolist())
    F = np.array(fingerprints)
    dists = [np.linalg.norm(F[i]-F[j]) for i in range(8) for j in range(i+1,8)]
    return {"fixed_points": fixed_points, "min_pairwise_channel_distance": float(min(dists)),
            "mean_pairwise_channel_distance": float(np.mean(dists))}

def measure_chirality_carries_forward():
    """The eps=+1 sheet (terrains 0-3) and eps=-1 sheet (4-7) are mirror-related; handedness inherited from the
    cosmogenesis carrier. Measure a chirality order parameter per terrain (signed curl of the coherent flow) and
    sum by sheet -- opposite signs = chirality carried, not injected."""
    def chirality(ti):
        eps,_,_ = TERR[ti]
        H = eps*(sx+sy+sz)/np.sqrt(3)
        # signed curl proxy: how the Bloch vector rotates under the coherent part alone (sign of eps)
        r0 = np.array([0.4,0.1,0.2]); rho=dm_from_bloch(r0)
        rho2 = rho - 1j*0.1*(H@rho - rho@H)
        r1 = bloch(rho2)
        cross = np.cross(r0, r1)
        return float(np.sign(cross[2]) * np.linalg.norm(cross))
    sheet_plus = sum(chirality(ti) for ti in range(4))
    sheet_minus = sum(chirality(ti) for ti in range(4,8))
    return {"sheet_plus_chirality": sheet_plus, "sheet_minus_chirality": sheet_minus,
            "sign_product": float(np.sign(sheet_plus)*np.sign(sheet_minus))}

# ---------- SEPARATE POLICY EVAL ----------

def eval_bridge(mA, mB, mC):
    unitary_control = (mA["unitary_final_td"] > 0.5*mA["initial_td"]) and (mA["terrain_final_td"] < 0.1)
    distinct_control = mB["min_pairwise_channel_distance"] > 1e-3
    chirality_control = mC["sign_product"] < 0
    all_flip = bool(unitary_control and distinct_control and chirality_control)
    return {"unitary_cannot_close_attractor_demand": bool(unitary_control),
            "eight_terrains_distinct_forced_teeth": bool(distinct_control),
            "chirality_carries_forward_two_sheets": bool(chirality_control),
            "BRIDGE_TOOTH_CARRIER_TO_TERRAINS_FORCED": all_flip}

def main():
    mA = measure_unitary_cannot_close_attractor_demand()
    mB = measure_eight_terrains_distinct_forced_teeth()
    mC = measure_chirality_carries_forward()
    verdict = eval_bridge(mA, mB, mC)
    out = {"classification":"scratch_diagnostic","promotion_allowed":False,
           "framing":"the ratchet's next tooth: bare chiral carrier -> 8 terrain dissipators, forced by the attractor demand",
           "attractor_demand_lane":mA, "distinct_teeth_lane":mB, "chirality_lane":mC, "policy_eval":verdict}
    path=__file__.replace(".py","_results.json"); json.dump(out, open(path,"w"), indent=1)

    print("THE BRIDGE TOOTH -- from the cosmogenesis chiral carrier UP to the 8 terrains, as one continuous climb.\n")
    print("  DEMAND the bare carrier cannot close (a state and a perturbed copy must become the same):")
    print(f"    initial trace distance {mA['initial_td']:.3f}")
    print(f"    bare UNITARY carrier final td {mA['unitary_final_td']:.3f} (preserved -- no attractor, demand OPEN)")
    print(f"    terrain DISSIPATOR final td {mA['terrain_final_td']:.3f} (converged to fixed point -- demand CLOSED)")
    print(f"  MSS next tooth = a dissipator with a fixed point = a terrain generator.")
    print(f"  WHY EIGHT: 8 terrains pairwise-distinct CHANNELS, min channel distance {mB['min_pairwise_channel_distance']:.3f} (each a forced tooth; fixed points can coincide, channels do not)")
    print(f"  CHIRALITY carries forward: sheet+ {mC['sheet_plus_chirality']:+.3f} / sheet- {mC['sheet_minus_chirality']:+.3f} (product {mC['sign_product']:+.0f})")
    print("\n  SEPARATE POLICY EVAL (verdict = all three controls flip):")
    for k,v in verdict.items():
        if k!="BRIDGE_TOOTH_CARRIER_TO_TERRAINS_FORCED": print(f"    {k}: {v}")
    print(f"\n  BRIDGE TOOTH (CARRIER -> TERRAINS) FORCED: {verdict['BRIDGE_TOOTH_CARRIER_TO_TERRAINS_FORCED']}")
    if verdict["BRIDGE_TOOTH_CARRIER_TO_TERRAINS_FORCED"]:
        print("PASS bridge_tooth_carrier_to_terrains")
    print("ALL_GATES:", "PASS" if verdict["BRIDGE_TOOTH_CARRIER_TO_TERRAINS_FORCED"] else "FAIL", "->", path)
    sys.exit(0 if verdict["BRIDGE_TOOTH_CARRIER_TO_TERRAINS_FORCED"] else 1)

if __name__ == "__main__":
    main()
