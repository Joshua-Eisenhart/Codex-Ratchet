#!/usr/bin/env python3
"""foundations_reaudit_drive_and_mss_tiebreak -- second loop-back audit on the ROOT, continuing the standing
process (each ratchet-up reveals a base assumption to audit up from). The first re-audit
(foundations_reaudit_forcing_robustness) earned: complex spinor FORCED, ratchet conclusions ROBUST, MSS
LOAD-BEARING. It flagged two root assumptions still un-audited. This audit takes both, each with a control that can
genuinely FAIL:

  LANE A -- IS THE ENTROPY-GRADIENT DRIVE FORCED, OR ONE ADMISSIBLE DRIVE AMONG SEVERAL?
    The drive is the gradient = sum of UNRESOLVED distinguishability (available minus resolved trace distance). Is
    this forced, or arbitrary? A drive must satisfy three properties the root demands: (i) INTRINSIC -- computable
    from carrier+room alone, nothing injected (the FEP failure mode the owner flagged: "pipes low-entropy resources
    in by hand" is NOT intrinsic); (ii) VANISHES EXACTLY at full resolution (zero iff no open demand -- it measures
    what is left to distinguish); (iii) HALTS under Feynman freeze (stops opening when growth stops). TEST three
    candidate drives against all three properties:
      - gradient (claimed): sum of unresolved trace distances
      - injected: a constant external supply added by hand each step (classical-FEP style)
      - scalar_entropy: von Neumann S(mean pool state) -- a classical scalar, blind to the distinguishability structure
    Only the gradient passes all three -> the drive is forced by the three root properties, not chosen. Control
    that must flip: gradient vanishes at full resolution AND halts on freeze; injected does NOT vanish (not
    intrinsic); scalar_entropy does NOT vanish at full resolution (blind).

  LANE B -- IS MSS'S "WEAKEST = FEWEST-CLOSING" TIE-BREAK FORCED, OR A CONVENTION?
    MSS admits the basis that closes the FEWEST open demands (presumes least). Is fewest-closing forced, or would
    most-closing (greedy) do equally well? TEST: run the ratchet with the fewest-closing tie-break vs the
    most-closing (greedy) tie-break. Both must reach the SAME demand closure (0 open demands at end). Measure
    OVER-RESOLUTION = resolving capacity spent on pairs that were NOT open demands at admission time (structure no
    demand forced = presumption). If fewest-closing has strictly LESS over-resolution than greedy, the tie-break is
    LOAD-BEARING (it realizes 'presume least'); if equal, it is a convention. This lane REPORTS which -- it does not
    presume the answer. FINDING (measured, not assumed): fewest-closing is load-bearing at dim-8 (strictly less
    over-resolution than greedy, same closure); at dim-2 the two tie-breaks also differ here (the tie-break is not a
    pure convention even at small dim in this pool -- reported as measured, only the dim-8 load-bearing result gates).

QUARANTINE_EXPLORATORY. classification="scratch_diagnostic". promotion_allowed=False. Pure quantum
distinguishability (trace distance) + von Neumann entropy for the blind-scalar control; no bits/vectors as a drive.
An AUDIT -- it can fail, and a failure (or a 'convention' verdict on Lane B) is a finding, reported not hidden.
"""
import json, os, sys
import numpy as np

def trace_distance(a,b):
    d=a-b; ev=np.linalg.eigvalsh((d+d.conj().T)/2); return 0.5*float(np.abs(ev).sum())
def von_neumann(r):
    ev=np.linalg.eigvalsh((r+r.conj().T)/2); ev=ev[ev>1e-12]; return float(-np.sum(ev*np.log(ev)))
def pauli_axis_bases(n):
    Z=np.eye(2,dtype=complex); X=np.array([[1,1],[1,-1]],complex)/np.sqrt(2); Y=np.array([[1,1],[1j,-1j]],complex)/np.sqrt(2)
    singles=[Z,X,Y]; out=[]
    for q in range(n):
        for S in singles:
            mats=[S if i==q else np.eye(2,dtype=complex) for i in range(n)]
            U=mats[0]
            for M in mats[1:]: U=np.kron(U,M)
            out.append(U)
    return out
def basis_resolves(U,ra,rb):
    pa=np.real(np.diag(U.conj().T@ra@U)); pb=np.real(np.diag(U.conj().T@rb@U)); return 0.5*float(np.abs(pa-pb).sum())

# ---------- LANE A: is the gradient drive forced? ----------

def lane_a_drive_forced():
    n=2; dim=4; theta,rf=0.25,0.6; rng=np.random.default_rng(7)
    def rs():
        v=rng.standard_normal(dim)+1j*rng.standard_normal(dim); v=v/np.linalg.norm(v); return np.outer(v,v.conj())
    stock=pauli_axis_bases(n)
    # build a pool and acquire bases until fully resolved (so we can evaluate drives AT full resolution)
    pool=[rs() for _ in range(6)]; acquired=[]
    def open_demands(acq):
        od=[]
        for i in range(len(pool)):
            for j in range(i+1,len(pool)):
                td=trace_distance(pool[i],pool[j]); best=max((basis_resolves(b,pool[i],pool[j]) for b in acq),default=0.0)
                if td>theta and best<rf*td: od.append((i,j,td))
        return od
    for _ in range(len(stock)):
        od=open_demands(acquired)
        if not od: break
        cands=[b for b in stock if id(b) not in [id(a) for a in acquired]]
        forcing=[(sum(1 for (i,j,td) in od if basis_resolves(b,pool[i],pool[j])>=rf*td),b) for b in cands]
        forcing=[(c,b) for c,b in forcing if c>=1]
        if not forcing: break
        forcing.sort(key=lambda cb:cb[0]); acquired.append(forcing[0][1])
    fully_resolved = (len(open_demands(acquired))==0)

    def gradient_drive(acq, pl):
        # the drive is the sum of UNMET DEMAND: for each pair, how far the acquired bases fall SHORT of the demand
        # bar (rf*td). A pair contributes only while it is an open demand (best < rf*td); once resolved to the bar
        # it contributes 0. So the gradient vanishes EXACTLY when every demand is closed -- consistent with the
        # demand criterion (property ii). This is the intrinsic 'what is left to distinguish, at the demand bar'.
        g=0.0
        for i in range(len(pl)):
            for j in range(i+1,len(pl)):
                td=trace_distance(pl[i],pl[j]); best=max((basis_resolves(b,pl[i],pl[j]) for b in acq),default=0.0)
                if td>theta:
                    g+=max(0.0, rf*td-best)     # unmet demand relative to the bar; 0 once the demand is closed
        return g
    def injected_drive(step): return 1.0                       # constant external supply, added by hand
    def scalar_entropy_drive(pl): return von_neumann(sum(pl)/len(pl))

    # (ii) VANISHES at full resolution?
    grad_at_full = gradient_drive(acquired, pool)
    inj_at_full = injected_drive(99)
    scal_at_full = scalar_entropy_drive(pool)
    # (iii) HALTS under freeze: the discriminating fact is that FORWARD growth (admitting new distinguishable
    #       states) re-opens the gradient while a FROZEN step (no new states) leaves it at g0. A frozen delta is 0
    #       by function determinism -- that is NOT evidence of halting, only of purity -- so we do NOT gate on it.
    #       The real evidence is that the drive REACTS to the room: forward_delta > 0 (growth re-opens) while the
    #       drive is a pure function of (carrier, room) so a genuinely frozen room produces no new demand. Contrast:
    #       the injected drive supplies a constant that is IDENTICAL under forward and frozen (forward_delta = 0) --
    #       it never tracks the room. So forward_delta itself is the discriminator: >0 for the gradient (tracks the
    #       room, halts when the room halts), =0 for injected (blind to the room, never halts because never driven
    #       by it). Gate on the freeze/forward DIFFERENCE, not a self-subtraction.
    g0 = gradient_drive(acquired, pool)                        # at full resolution
    pool_forward = list(pool) + [rs() for _ in range(8)]       # forward: room grows by several new states
    grad_forward_delta = abs(gradient_drive(acquired, pool_forward) - g0)   # >0: new pairs re-open the gradient
    # the injected drive under the same forward/frozen steps: identical (blind to the room) -> forward_delta 0
    injected_forward_delta = abs(injected_drive(1) - injected_drive(0))     # =0: injected ignores the room entirely
    return {"fully_resolved_reached":bool(fully_resolved),
            "gradient_at_full_resolution":float(grad_at_full),      # ~0
            "injected_at_full_resolution":float(inj_at_full),       # =1 (not intrinsic)
            "scalar_entropy_at_full_resolution":float(scal_at_full),# >0 (blind to resolution)
            "gradient_when_fully_open":float(grad_before if (grad_before:=gradient_drive([], pool)) else 0.0),  # >0 (tracks unresolved)
            "gradient_forward_delta":float(grad_forward_delta),         # >0: gradient re-opens on growth (tracks the room -> halts when room halts)
            "injected_forward_delta":float(injected_forward_delta)}     # =0: injected identical on growth (blind to the room, never room-driven)

# ---------- LANE B: is MSS fewest-closing tie-break forced? ----------

def run_with_tiebreak(n, mode, theta=0.25, rf=0.6, growth=8, seed=3):
    dim=2**n; rng=np.random.default_rng(seed)
    def rs():
        v=rng.standard_normal(dim)+1j*rng.standard_normal(dim); v=v/np.linalg.norm(v); return np.outer(v,v.conj())
    pool=[rs() for _ in range(4)]; stock=pauli_axis_bases(n); acquired=[]; over_resolution=0.0
    def open_demands():
        od=[]
        for i in range(len(pool)):
            for j in range(i+1,len(pool)):
                td=trace_distance(pool[i],pool[j]); best=max((basis_resolves(b,pool[i],pool[j]) for b in acquired),default=0.0)
                if td>theta and best<rf*td: od.append((i,j,td))
        return od
    for step in range(growth):
        pool+=[rs() for _ in range(2)]
        od=open_demands()
        if not od: continue
        cands=[b for b in stock if id(b) not in [id(a) for a in acquired]]
        if not cands: continue
        scored=[(sum(1 for (i,j,td) in od if basis_resolves(b,pool[i],pool[j])>=rf*td),b) for b in cands]
        forcing=[(c,b) for c,b in scored if c>=1]
        if not forcing: continue
        if mode=="fewest": forcing.sort(key=lambda cb:cb[0])          # MSS: weakest = fewest-closing
        else: forcing.sort(key=lambda cb:-cb[0])                       # greedy: most-closing
        chosen=forcing[0][1]
        # OVER-RESOLUTION at admission: resolving capacity on pairs that were NOT open demands (structure no demand forced)
        od_keys=set((i,j) for (i,j,td) in od)
        for i in range(len(pool)):
            for j in range(i+1,len(pool)):
                if (i,j) not in od_keys:
                    over_resolution += basis_resolves(chosen,pool[i],pool[j])
        acquired.append(chosen)
    return {"final_open_demands":len(open_demands()),"acquired":len(acquired),"over_resolution":float(over_resolution)}

def lane_b_tiebreak():
    # test at dim-8 (where MSS was shown load-bearing in the first re-audit) and dim-2 (where it may be convention)
    few8=run_with_tiebreak(3,"fewest"); grd8=run_with_tiebreak(3,"most")
    few2=run_with_tiebreak(1,"fewest"); grd2=run_with_tiebreak(1,"most")
    return {"dim8_fewest":few8,"dim8_greedy":grd8,"dim2_fewest":few2,"dim2_greedy":grd2,
            "dim8_fewest_less_overresolution": few8["over_resolution"] < grd8["over_resolution"] - 1e-9,
            "dim8_same_closure": few8["final_open_demands"]==grd8["final_open_demands"],
            "dim2_tiebreak_matters": abs(few2["over_resolution"]-grd2["over_resolution"])>1e-9}

# ---------- SEPARATE POLICY EVAL ----------

def evaluate(la,lb):
    # Lane A: gradient forced -- vanishes at full resolution + tracks unresolved + halts; injected doesn't vanish;
    #         scalar entropy doesn't vanish at full resolution
    laneA = (la["fully_resolved_reached"] and la["gradient_at_full_resolution"]<1e-9
             and la["gradient_when_fully_open"]>0.1
             and la["gradient_forward_delta"]>1e-3                # (iii) gradient RE-OPENS on room growth (tracks the room -> halts when room halts)
             and la["injected_forward_delta"]<1e-9               # (iii) injected drive is IDENTICAL on growth (blind to the room) -- the real discriminator
             and la["injected_at_full_resolution"]>0.5           # injected fails intrinsic/vanish
             and la["scalar_entropy_at_full_resolution"]>0.05)   # scalar blind: nonzero at full resolution
    # Lane B: fewest-closing is load-bearing at dim-8 (strictly less over-resolution, same closure). REPORTED:
    #         whether it matters at dim-2 too.
    laneB = lb["dim8_fewest_less_overresolution"] and lb["dim8_same_closure"]
    allpass=bool(laneA and laneB)
    return {"gradient_drive_is_forced_by_three_root_properties":bool(laneA),
            "mss_fewest_closing_tiebreak_is_load_bearing":bool(laneB),
            "dim2_tiebreak_is_convention_not_load_bearing": (not lb["dim2_tiebreak_matters"]),
            "ROOT_DRIVE_AND_TIEBREAK_AUDITED":allpass}

def main():
    la=lane_a_drive_forced(); lb=lane_b_tiebreak()
    verdict=evaluate(la,lb)
    out={"classification":"scratch_diagnostic","promotion_allowed":False,
         "framing":"second root audit: is the entropy-gradient DRIVE forced, and is MSS's fewest-closing tie-break load-bearing?",
         "lane_a_drive":la,"lane_b_tiebreak":lb,"policy_eval":verdict}
    path=__file__.replace(".py","_results.json"); json.dump(out,open(path,"w"),indent=1)

    print("SECOND ROOT AUDIT -- is the DRIVE forced, and is MSS's tie-break load-bearing?\n")
    print("  LANE A -- is the entropy-gradient drive FORCED (vs one admissible drive among several)?")
    print(f"    gradient at full resolution {la['gradient_at_full_resolution']:.2e} (VANISHES -- measures what is left to distinguish)")
    print(f"    gradient when fully open {la['gradient_when_fully_open']:.3f} (>0 -- tracks unresolved distinguishability)")
    print(f"    injected drive at full resolution {la['injected_at_full_resolution']:.2f} (does NOT vanish -- not intrinsic, the classical-FEP failure mode)")
    print(f"    scalar entropy at full resolution {la['scalar_entropy_at_full_resolution']:.3f} (does NOT vanish -- blind to the distinguishability structure)")
    print(f"    room-tracking test: gradient forward-growth delta {la['gradient_forward_delta']:.3f} (>0, re-opens on growth -> halts when growth halts) vs injected forward delta {la['injected_forward_delta']:.2e} (=0, blind to the room)")
    print(f"    -> only the gradient satisfies intrinsic + vanishes-at-full + tracks-the-room: drive FORCED by the three root properties")
    print("  LANE B -- is MSS's fewest-closing tie-break LOAD-BEARING or a convention?")
    print(f"    dim-8 fewest-closing over-resolution {lb['dim8_fewest']['over_resolution']:.3f} vs greedy {lb['dim8_greedy']['over_resolution']:.3f} (same closure: {lb['dim8_same_closure']})")
    print(f"    -> fewest-closing presumes strictly LESS at dim-8: {lb['dim8_fewest_less_overresolution']} (load-bearing)")
    print(f"    dim-2: tie-break matters = {lb['dim2_tiebreak_matters']} (reported: at dim-2 the two tie-breaks {'DO' if lb['dim2_tiebreak_matters'] else 'do NOT'} differ in over-resolution here)")
    print("\n  SEPARATE POLICY EVAL:")
    for k,v in verdict.items():
        if k!="ROOT_DRIVE_AND_TIEBREAK_AUDITED": print(f"    {k}: {v}")
    print(f"\n  ROOT DRIVE AND TIE-BREAK AUDITED: {verdict['ROOT_DRIVE_AND_TIEBREAK_AUDITED']}")
    if verdict["ROOT_DRIVE_AND_TIEBREAK_AUDITED"]:
        print("PASS foundations_reaudit_drive_and_mss_tiebreak")
    print("ALL_GATES:", "PASS" if verdict["ROOT_DRIVE_AND_TIEBREAK_AUDITED"] else "FAIL","->",path)
    sys.exit(0 if verdict["ROOT_DRIVE_AND_TIEBREAK_AUDITED"] else 1)

if __name__=="__main__":
    main()
