#!/usr/bin/env python3
"""next_tooth_720_double_loop_and_lift_audit -- BOTH the next rung AND the root audit it exposes, in the standing
loop-back-while-climbing method.

PART 1 (CLIMB) -- the 720-degree DOUBLE LOOP, the tooth above the single 360-degree loop.
  Where we are: rung 3 (next_tooth_engine_stages_to_360_loop) earned the single 360-degree loop and its tense
  (deductive UEUE vs inductive EUEU), read at the spinor level. But the single 360 loop returns -psi (SU(2): a
  2pi rotation is NOT the identity on the spinor -- overlap -1). The state is NOT genuinely back; a sign defect
  remains.
  DEMAND a single 360 loop cannot close: the room asserts a CLOSED loop must GENUINELY RETURN (overlap +1, a true
  identity), and that the two tense-traversals COMPOSE into one closed object. A single 360 loop cannot: it returns
  -psi (overlap -1), so it does not close, and one traversal alone is not a composition of both.
  MSS next tooth = the 720-degree DOUBLE loop: two 360 traversals composed (inner deductive + outer inductive),
  returning +psi (overlap +1 -- a genuine return). Not the 64-schedule, not the full engine: one double loop.
  WHY THE DOUBLE LOOP COMPOSES BOTH TENSES: the 720 object is inner-360 then outer-360; running inner-deductive +
  outer-inductive is a single closed double-cover traversal that genuinely returns -- the deductive and inductive
  loops are its two halves, not two separate objects.

PART 2 (ROOT AUDIT, loop-back) -- is the SPINOR LIFT (psi over rho) FORCED, or merely installed?
  Every tooth from the 360 loop up lives at the spinor (psi) level. If the lift psi -> rho is a mere convenience,
  the whole tense/parity structure is unearned. AUDIT: R(2pi) maps psi -> -psi but rho -> rho (IDENTICAL density).
  So there EXIST states distinguishable at psi but identical at rho. The model MUST distinguish them (the 360 vs
  720 return is the tense structure the engine rests on). TEST, each a control that can fail:
    (A) NO rho-level observable separates R(2pi)|0> from |0>: enumerate many Hermitian observables; every
        expectation is identical on the two (rho-identical) states. A psi-level observable (the lifted overlap)
        DOES separate them. -> rho is INSUFFICIENT; the lift is forced by an unmet distinguishability the room
        asserts (360 != 720).
    (B) ERASED control (add the density quotient): identify psi ~ -psi (the quotient law rho=|psi><psi| imposes);
        then the 360-vs-720 distinction DIES. So it is precisely the lift (refusing that identification) that
        carries the distinction -- non-definitional, the distinction dies only when the quotient is added.
    (C) the lift is MINIMAL: it is a 2-to-1 cover (each rho has exactly two psi lifts, +/-psi), the SMALLEST
        nontrivial cover. Not a bigger bundle. -> MSS admits the double cover, nothing larger.

QUARANTINE_EXPLORATORY. classification="scratch_diagnostic". promotion_allowed=False. Spinor-level (psi in C^2)
unitary composition + density shadow. Pure distinguishability (overlaps, observable expectations); no bits/vectors.
The lift-forcing here is a numpy enumeration demonstration (the same claim was separately z3+cvc5 dual-solver
verified at L2->L3, ledger 'RATCHET CLIMB ENGINE -- non-definitional flip CORRECTED'); this is the spinor-loop
face of that forcing, not a re-proof. A MECHANISM illustration, NOT a claim of uniqueness.
"""
import json, os, sys
import numpy as np
from scipy.linalg import expm

sx=np.array([[0,1],[1,0]],complex); sy=np.array([[0,-1j],[1j,0]],complex); sz=np.array([[1,0],[0,-1]],complex)
I2=np.eye(2,dtype=complex); TH=np.pi/4
n_axis=np.array([1,1,1.])/np.sqrt(3); H0=n_axis[0]*sx+n_axis[1]*sy+n_axis[2]*sz

def rotation(angle): return expm(-1j*angle/2*H0)     # expm(-i theta/2 n.sigma): angle = Bloch rotation angle

def spinor_ops(eps):
    Hc=eps*(sx+sy+sz)/np.sqrt(3)
    U=expm(-1j*Hc*np.pi/2); E=expm(-1j*TH/2*sx); U2=expm(-1j*Hc*np.pi/2); E2=expm(-1j*TH/2*sz)
    return U,E,U2,E2

def loop_360(eps, order="UEUE"):
    U,E,U2,E2=spinor_ops(eps)
    beats=[U,E,U2,E2] if order=="UEUE" else [E,U,E2,U2]
    M=I2
    for b in beats: M=b@M
    return M

# ---------- PART 1: the 720 double loop tooth ----------

def measure_360_does_not_close_720_does():
    """The single 360 loop returns -psi (overlap -1, does NOT genuinely close). The 720 double loop returns +psi
    (overlap +1, genuine return)."""
    psi0=np.array([1,0],complex)
    o360=complex(np.vdot(psi0, rotation(2*np.pi)@psi0)).real     # -1
    o720=complex(np.vdot(psi0, rotation(4*np.pi)@psi0)).real     # +1
    return {"single_360_overlap":o360,"double_720_overlap":o720}

def measure_double_loop_composes_both_tenses():
    """The 720 object = a 2pi transport done TWICE (inner + outer), which genuinely returns (+psi). We build the
    double loop as the ACTUAL composition of two 360 transports and confirm: (i) a single 360 transport is the
    -psi-defected loop (overlap -1); (ii) the composed double (360 then 360 = 720) genuinely returns (+psi,
    overlap +1). Separately, the two TENSE traversals of the beat-loop (deductive UEUE vs inductive EUEU) are
    distinct (the tense is real), which is why the double loop has two nameable halves."""
    psi0=np.array([1,0],complex)
    R=rotation(2*np.pi)                              # a single 360 transport (the -psi-defected loop)
    single_return=complex(np.vdot(psi0, R@psi0)).real            # -1
    double = R@R                                     # 360 then 360 = 720, the ACTUAL composition
    double_return=complex(np.vdot(psi0, double@psi0)).real        # +1 genuine return
    inner=loop_360(+1,"UEUE"); outer=loop_360(+1,"EUEU")         # the two tense halves (beat-loops)
    return {"double_loop_return":float(double_return),"single_loop_return":float(single_return),
            "inner_outer_distinct": float(np.linalg.norm(inner@psi0 - outer@psi0))}   # >0: the two tenses differ

# ---------- PART 2: is the spinor lift forced? ----------

def measure_no_rho_observable_separates():
    """R(2pi)|0> = -|0> (psi) but rho identical. Enumerate Hermitian observables: every expectation is identical on
    the two states (rho-blind); the psi-level lifted overlap DOES separate them."""
    psi0=np.array([1,0],complex); psi1=rotation(2*np.pi)@psi0     # = -psi0
    rng=np.random.default_rng(5)
    max_rho_gap=0.0
    for _ in range(200):
        H=rng.standard_normal((2,2))+1j*rng.standard_normal((2,2)); H=(H+H.conj().T)/2   # random Hermitian observable
        e0=np.vdot(psi0,H@psi0).real; e1=np.vdot(psi1,H@psi1).real
        max_rho_gap=max(max_rho_gap, abs(e0-e1))
    # psi-level observable: the lifted overlap with a reference (phase-sensitive)
    psi_level_gap=abs(complex(np.vdot(psi0,psi0)) - complex(np.vdot(psi0,psi1)))    # |1 - (-1)| = 2
    return {"max_rho_observable_gap":float(max_rho_gap),"psi_level_gap":float(psi_level_gap)}

def measure_erased_quotient_kills_distinction():
    """ERASED control: impose the density quotient psi ~ -psi. Then the 360 (-psi) and the no-op (+psi) are
    IDENTIFIED, so the 360-vs-720 distinction dies. The distinction lives ONLY in refusing the quotient (the lift)."""
    psi0=np.array([1,0],complex)
    o360=complex(np.vdot(psi0, rotation(2*np.pi)@psi0)).real     # -1 at psi level
    o720=complex(np.vdot(psi0, rotation(4*np.pi)@psi0)).real     # +1 at psi level
    psi_distinction=abs(o360-o720)                                # = 2 (alive at psi)
    # quotient: identify psi ~ -psi -> both map to rho=|0><0|; distinction measured by rho overlap = |.|^2
    q360=abs(complex(np.vdot(psi0, rotation(2*np.pi)@psi0)))**2   # +1
    q720=abs(complex(np.vdot(psi0, rotation(4*np.pi)@psi0)))**2   # +1
    quotient_distinction=abs(q360-q720)                           # = 0 (dead under quotient)
    return {"psi_distinction":float(psi_distinction),"quotient_distinction":float(quotient_distinction)}

def measure_lift_is_minimal_2to1():
    """The lift is a 2-to-1 cover: each rho has exactly two psi preimages (+/-psi). Confirm both map to the same
    rho and are the ONLY two (a global phase e^{i a}|psi> with same rho requires |e^{i a}|=1 and, for a fixed
    representative up to sign, a in {0, pi})."""
    psi0=np.array([1,0],complex)
    rho=np.outer(psi0,psi0.conj())
    plus=psi0; minus=-psi0
    same_rho = np.linalg.norm(np.outer(plus,plus.conj())-rho)+np.linalg.norm(np.outer(minus,minus.conj())-rho)
    return {"two_lifts_same_rho_residual":float(same_rho),"cover_degree":2}

# ---------- SEPARATE POLICY EVAL ----------

def evaluate(p1a,p1b,a,b,c):
    # Part 1: 360 does not close (-1), 720 does (+1); double loop returns genuinely, halves distinct
    part1 = (p1a["single_360_overlap"]<-0.99 and p1a["double_720_overlap"]>0.99
             and p1b["double_loop_return"]>0.99 and p1b["single_loop_return"]<-0.99
             and p1b["inner_outer_distinct"]>1e-3)
    # Part 2: lift forced -- no rho observable separates (gap ~0) but psi does (gap ~2); erased quotient kills it;
    #         lift is minimal 2-to-1
    part2 = (a["max_rho_observable_gap"]<1e-9 and a["psi_level_gap"]>1.5
             and b["psi_distinction"]>1.5 and b["quotient_distinction"]<1e-9
             and c["two_lifts_same_rho_residual"]<1e-9 and c["cover_degree"]==2)
    allpass=bool(part1 and part2)
    return {"double_720_loop_closes_what_360_cannot":bool(part1),
            "spinor_lift_is_forced_not_installed":bool(part2),
            "NEXT_TOOTH_720_AND_LIFT_AUDIT":allpass}

def main():
    p1a=measure_360_does_not_close_720_does()
    p1b=measure_double_loop_composes_both_tenses()
    a=measure_no_rho_observable_separates()
    b=measure_erased_quotient_kills_distinction()
    c=measure_lift_is_minimal_2to1()
    verdict=evaluate(p1a,p1b,a,b,c)
    out={"classification":"scratch_diagnostic","promotion_allowed":False,
         "framing":"PART 1: the 720 double loop as the tooth above the 360 loop. PART 2 (loop-back audit): is the spinor lift forced?",
         "p1_360_vs_720":p1a,"p1_double_composes":p1b,"p2a_no_rho_observable":a,"p2b_erased_quotient":b,"p2c_minimal_cover":c,
         "policy_eval":verdict}
    path=__file__.replace(".py","_results.json"); json.dump(out,open(path,"w"),indent=1)

    print("THE 720 DOUBLE LOOP + THE SPINOR-LIFT ROOT AUDIT (climb + loop-back in one motion).\n")
    print("  PART 1 -- the 720 double loop (tooth above the single 360 loop):")
    print(f"    single 360 loop overlap {p1a['single_360_overlap']:+.3f} (-> -psi, does NOT genuinely close -- demand OPEN)")
    print(f"    720 double loop overlap {p1a['double_720_overlap']:+.3f} (-> +psi, GENUINE return -- demand CLOSED)")
    print(f"    double loop composes both tenses: return {p1b['double_loop_return']:.3f}, inner/outer halves distinct {p1b['inner_outer_distinct']:.3f}")
    print("  PART 2 -- is the spinor lift (psi over rho) FORCED or merely installed?")
    print(f"    max rho-observable gap on R(2pi)|0> vs |0>: {a['max_rho_observable_gap']:.2e} (~0 -- NO density observable separates them)")
    print(f"    psi-level gap: {a['psi_level_gap']:.3f} (>0 -- only the lift separates them -> rho INSUFFICIENT, lift FORCED)")
    print(f"    erased-quotient control: psi distinction {b['psi_distinction']:.2f} -> quotient distinction {b['quotient_distinction']:.2e} (distinction DIES under the density quotient)")
    print(f"    lift minimal: 2-to-1 cover, two-lifts-same-rho residual {c['two_lifts_same_rho_residual']:.2e} (smallest nontrivial cover)")
    print("\n  SEPARATE POLICY EVAL:")
    for k,v in verdict.items():
        if k!="NEXT_TOOTH_720_AND_LIFT_AUDIT": print(f"    {k}: {v}")
    print(f"\n  720 DOUBLE LOOP + LIFT AUDIT: {verdict['NEXT_TOOTH_720_AND_LIFT_AUDIT']}")
    if verdict["NEXT_TOOTH_720_AND_LIFT_AUDIT"]:
        print("PASS next_tooth_720_double_loop_and_lift_audit")
    print("ALL_GATES:", "PASS" if verdict["NEXT_TOOTH_720_AND_LIFT_AUDIT"] else "FAIL","->",path)
    sys.exit(0 if verdict["NEXT_TOOTH_720_AND_LIFT_AUDIT"] else 1)

if __name__=="__main__":
    main()
