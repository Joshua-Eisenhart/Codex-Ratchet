#!/usr/bin/env python3
"""known_unknown_fep_field_sim -- KNOWN/UNKNOWN as a testable FEP model of the engine's attractor basin.

There is no testable win/lose definition -- win/lose is only a naming mapped onto the attractor-basin structure. But
KNOWN/UNKNOWN IS testable and is a genuinely better working definition, because surprise is the measure of the unknown
and FEP gives it a real handle. This sim develops known/unknown on its own terms (NOT compared to win/lose or any
other label), as a measured field over the engine's state space:

  known/unknown FIELD  U(rho) = S(rho || attractor)  -- Umegaki relative entropy in bits, where the attractor is the
  terrain's own GKSL fixed point (the state the engine settles into = what it has learned = the KNOWN). U is large
  where the state is off-basin (UNKNOWN) and -> 0 at the attractor (fully KNOWN). Pure QIT; no temperature, no energy,
  no -log p; the only measure is quantum relative entropy.

THE MODEL (three gated claims, each on the running engine, each with a control that can fail):
  (1) THE ATTRACTOR IS THE KNOWN. The field minimum sits at the terrain's GKSL fixed point: U(attractor) ~ 0, and U
      grows with Bloch-distance from it. Measured over a probe shell -> the "unknown" is a graded field, not a label.
  (2) THE ENGINE FLOW IS SURPRISE-DESCENT (FEP). Running a probe forward under the terrain's own GKSL flow makes U
      decrease monotonically -- the engine moves known-ward. This is free-energy minimization rendered as relative-
      entropy descent (data-processing inequality: a CPTP flow toward its fixed point is contractive in U).
  (3) THE KNOWN IS SPECIFIC. CONTROL that can fail: measure U against a WRONG belief (a foreign terrain's fixed
      point). The flow does NOT drive that surprise to 0 -- a residual unknown remains, because the engine only makes
      ITS OWN attractor known. If descent-to-zero happened for the wrong belief too, "known" would be vacuous.

DIRECTIONAL READING (the part of the earlier reframe that survives): Type-1 loops (candidate-first) start from a
declared belief and TEST it against the state = confirm-the-known; Type-2 loops (measurement-first) start from the
state and build the belief = reduce-the-unknown. That is the confirm/explore structure, and it is exactly FEP's two
moves (perception updates the belief; the flow reduces surprise). Reported here as context, gated at (1)-(3).

scratch_diagnostic, promotion_allowed=false. The claim is a FEP model of the engine's attractor basin, not a proof.
"""
import json, sys
import numpy as np
from scipy.linalg import expm, logm

sx=np.array([[0,1],[1,0]],complex); sy=np.array([[0,-1j],[1j,0]],complex); sz=np.array([[1,0],[0,-1]],complex)
I2=np.eye(2,dtype=complex); sp=0.5*(sx+1j*sy); sm=0.5*(sx-1j*sy)
G=0.35; KAP=1.0; T_FLOW=1.0; N_STEPS=200
TERR={0:(+1,'damp',+1),1:(+1,'depol',0),2:(+1,'damp',-1),3:(+1,'proj',0),
      4:(-1,'damp',-1),5:(-1,'depol',0),6:(-1,'damp',+1),7:(-1,'proj',0)}
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
def step(X,r,dt):
    k1=X(r);k2=X(r+.5*dt*k1);k3=X(r+.5*dt*k2);k4=X(r+dt*k3)
    r=r+(dt/6)*(k1+2*k2+2*k3+k4);r=.5*(r+r.conj().T);r/=np.trace(r).real; return r
def flow_traj(ti,r,steps=N_STEPS,t=T_FLOW):
    X=gen(ti); dt=t/steps; traj=[r.copy()]
    for _ in range(steps): r=step(X,r,dt); traj.append(r.copy())
    return traj
def attractor(ti):
    r=0.5*(I2+0.3*sx+0.2*sy+0.1*sz)
    for _ in range(8): r=flow_traj(ti,r)[-1]
    return r
def bloch(r): return np.array([np.trace(r@s).real for s in (sx,sy,sz)])
def rho_from_bloch(v): return 0.5*(I2+v[0]*sx+v[1]*sy+v[2]*sz)
def U(rho,belief):
    # surprise field: Umegaki relative entropy S(rho||belief) in bits. regularize belief off the boundary.
    b=belief+1e-9*I2; b=b/np.trace(b).real; rr=rho+1e-12*I2
    val=np.trace(rr@(logm(rr)-logm(b))).real/np.log(2)
    return float(max(val,0.0))
def probe_shell(seed,n=12,radius=0.7):
    rng=np.random.default_rng(seed); fam=[]
    for _ in range(n):
        v=rng.normal(size=3); v=radius*v/np.linalg.norm(v); fam.append(rho_from_bloch(v))
    return fam

def main():
    terrains=list(TERR)
    # (1) attractor is the known: U at attractor ~0, and U grows with distance from it
    field_rows=[]; att_U=[]; corr_list=[]
    atts={t:attractor(t) for t in terrains}
    for t in terrains:
        a=atts[t]; ua=U(a,a); att_U.append(ua)
        shell=probe_shell(3+t)
        dists=[np.linalg.norm(bloch(p)-bloch(a)) for p in shell]
        surs=[U(p,a) for p in shell]
        # correlation between off-attractor distance and surprise (graded field, not a label)
        c=float(np.corrcoef(dists,surs)[0,1])
        corr_list.append(c)
        field_rows.append({"terrain":t,"U_at_attractor_bits":round(ua,6),"dist_surprise_corr":round(c,4)})
    attractor_is_known=bool(max(att_U)<1e-3 and min(corr_list)>0.5)

    # (2) engine flow is surprise-descent: U decreases monotonically toward the attractor along the flow.
    # Run enough flow-time to converge into the basin (the attractor itself is computed with 8x flow), so "reaches
    # the known" means the surprise drops to a small fraction of where it started, monotonically the whole way.
    descent_rows=[]
    for t in terrains:
        a=atts[t]; p=probe_shell(50+t,n=6)[0]
        us=[]
        r=p
        # 12 x T_FLOW: the projective terrains (t3/t7) have a pure boundary fixed point where relative entropy
        # converges more slowly, so a longer flow budget is needed to actually reach the basin. Measured: all 8
        # terrains reach U < 2e-3 by 12x (t7 goes 0.039@6x -> 0.002@12x -> 0.0002@20x), confirming the residual is
        # convergence-rate, not a descent floor.
        for _ in range(12):
            traj=flow_traj(t,r); us+=[U(x,a) for x in traj]; r=traj[-1]
        mono=all(us[i+1]<=us[i]+1e-4 for i in range(len(us)-1))
        frac_remaining=us[-1]/max(us[0],1e-9)
        descent_rows.append({"terrain":t,"U_start_bits":round(us[0],4),"U_end_bits":round(us[-1],6),
                             "fraction_remaining":round(frac_remaining,4),"monotone_descent":bool(mono)})
    flow_is_descent=bool(all(r["monotone_descent"] for r in descent_rows) and all(r["fraction_remaining"]<0.02 for r in descent_rows))

    # (3) the known is specific: against a WRONG belief a residual unknown remains. The honest control is RELATIVE to
    # how far the wrong belief sits from the true attractor -- some terrain pairs share a fixed point (e.g. t5/t7 are
    # both eps=-1 near-mixed), so "wrong belief" is only meaningfully wrong when the two attractors actually differ.
    # residual_unknown holds iff U(end vs wrong) is a large fraction of U(true attractor vs wrong belief) -- i.e. the
    # flow made the state KNOWN to its own attractor but left it essentially as unknown to the wrong one as the
    # attractor itself is. Excludes pairs whose attractors coincide (no wrong belief to be wrong about).
    wrong_rows=[]
    for t in terrains:
        wrong_t=(t+2)%8; wa=atts[wrong_t]; a=atts[t]
        belief_gap=U(a,wa)                       # how unknown the true attractor already is to the wrong belief
        if belief_gap<1e-2:
            wrong_rows.append({"terrain":t,"wrong_belief_terrain":wrong_t,"belief_gap_bits":round(belief_gap,4),
                               "excluded_coincident_attractor":True}); continue
        p=probe_shell(90+t,n=6)[0]; r=p
        for _ in range(6): r=flow_traj(t,r)[-1]
        u_wrong_end=U(r,wa)
        wrong_rows.append({"terrain":t,"wrong_belief_terrain":wrong_t,"belief_gap_bits":round(belief_gap,4),
                           "U_end_vs_wrong_belief_bits":round(u_wrong_end,4),
                           "residual_fraction_of_gap":round(u_wrong_end/belief_gap,4),
                           "residual_unknown":bool(u_wrong_end>0.5*belief_gap)})
    tested=[r for r in wrong_rows if not r.get("excluded_coincident_attractor")]
    known_is_specific=bool(tested and all(r["residual_unknown"] for r in tested))

    verdict=bool(attractor_is_known and flow_is_descent and known_is_specific)
    out={"classification":"scratch_diagnostic","promotion_allowed":False,
         "definition":"known/unknown = surprise field U(rho)=S(rho||attractor) in bits; attractor=terrain GKSL fixed point=the known; U grows off-basin=the unknown. FEP: engine flow is surprise-descent.",
         "field_attractor_is_known":{"per_terrain":field_rows,"max_U_at_attractor":round(max(att_U),6),
                                     "min_dist_surprise_corr":round(min(corr_list),4),"claim":attractor_is_known},
         "flow_is_surprise_descent":{"per_terrain":descent_rows,"claim":flow_is_descent},
         "known_is_specific_wrong_belief_control":{"per_terrain":wrong_rows,"claim":known_is_specific},
         "KNOWN_UNKNOWN_FEP_MODEL":verdict}
    path=__file__.replace(".py","_results.json"); json.dump(out,open(path,"w"),indent=1)
    print("KNOWN/UNKNOWN as a FEP model of the engine attractor basin (surprise = the measure of the unknown).\n")
    print("(1) ATTRACTOR IS THE KNOWN (U~0 at attractor; U grows with off-basin distance):")
    for r in field_rows: print(f"    terrain {r['terrain']}: U(attractor)={r['U_at_attractor_bits']:.2e} bits  dist-surprise corr={r['dist_surprise_corr']:+.3f}")
    print(f"    -> attractor_is_known: {attractor_is_known}\n")
    print("(2) ENGINE FLOW IS SURPRISE-DESCENT (FEP free-energy minimization):")
    for r in descent_rows: print(f"    terrain {r['terrain']}: U {r['U_start_bits']:.4f} -> {r['U_end_bits']:.2e} bits  monotone: {r['monotone_descent']}")
    print(f"    -> flow_is_descent: {flow_is_descent}\n")
    print("(3) THE KNOWN IS SPECIFIC (CONTROL -- wrong belief keeps residual unknown, relative to belief gap):")
    for r in wrong_rows:
        if r.get("excluded_coincident_attractor"): print(f"    terrain {r['terrain']} vs belief {r['wrong_belief_terrain']}: EXCLUDED (attractors coincide, gap {r['belief_gap_bits']:.4f} bits)")
        else: print(f"    terrain {r['terrain']} vs belief {r['wrong_belief_terrain']}: U_end={r['U_end_vs_wrong_belief_bits']:.4f} of gap {r['belief_gap_bits']:.4f} bits ({r['residual_fraction_of_gap']:.2f})  residual_unknown: {r['residual_unknown']}")
    print(f"    -> known_is_specific: {known_is_specific}")
    print(f"\n  KNOWN/UNKNOWN FEP MODEL: {verdict}")
    if verdict: print("PASS known_unknown_fep_field")
    print("ALL_GATES:","PASS" if verdict else "FAIL","->",path)
    sys.exit(0 if verdict else 1)

if __name__=="__main__":
    main()
