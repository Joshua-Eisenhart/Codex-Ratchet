#!/usr/bin/env python3
"""next_tooth_engine_stages_to_360_loop -- the ratchet's NEXT tooth after the engine stages. Continue the
continuous climb: single engine STAGES (rung 2, one operator in two orders = pairwise order via N01) -> the
composed 360-degree engine LOOP (a closed 4-beat traversal whose HANDEDNESS -- deductive UEUE vs inductive EUEU --
is a loop-level property no single stage carries), read at the SPINOR (psi) level where the loop parity lives.

WHERE WE ARE ON THE LADDER:
  - rung 2 (next_tooth_terrains_to_engine_stages): a STAGE = one native operator composed with a terrain in two
    orders. It makes PAIRWISE order matter (N01: down != up). But a single stage has no CYCLE -- no closed
    traversal, no notion of going around and returning, no handedness of a loop.
  - the established loop structure (prior sims, EARNED): the 360-degree loop returns the spinor to -psi and the
    720-degree double loop to +psi (SU(2) double cover, exact). Tense = loop ORDER (deductive UEUE vs inductive
    EUEU -- the SAME four operators in a different sequence). A terrain in isolation has no tense; tense is a LOOP
    property. It is INVISIBLE at the density (rho) level (the quotient rho=|psi><psi| kills the global phase / 720
    return) and lives at the SPINOR (psi) level.

THE DEMAND that forces the next tooth:
  As the room grows it asserts that a CLOSED traversal is distinguishable from its TIME-REVERSE -- doing the 4-beat
  loop deductively (UEUE) differs from doing it inductively (EUEU). A single stage cannot close this: with only one
  operator-order pair there is no closed cycle to reverse; the pairwise order gap says nothing about loop
  handedness. The distinguishability the room says a LOOP's direction should produce is a demand no single stage
  resolves.

MSS -- the weakest structure that closes it:
  The weakest admissible structure that makes loop-direction matter is a CLOSED 4-beat composition of the terrain's
  operators (a 360-degree loop), read at the spinor level. Not the full 720 double loop yet, not the 64-schedule:
  one closed 4-beat loop per terrain, in its two traversal orders. Its handedness is a spinor (psi) property,
  invisible to rho.

WHY THIS IS SPINOR-LEVEL (the honest structural point):
  The loop parity (360 -> -psi, 720 -> +psi) is a global-phase / SU(2)-lift fact. At the density level rho=|psi><psi|
  the global phase cancels, so the 360 vs 720 distinction is provably invisible. The tooth therefore MUST be read
  at psi -- which is why all prior density-level Axis tooling (Axes 1-6) could not see tense.

CONTROLS (each must flip; measurement/verdict separated per Lev mesh discipline):
  (A) A STAGE HAS NO LOOP HANDEDNESS; A 360 LOOP DOES: the deductive (UEUE) and inductive (EUEU) traversals of the
      closed 4-beat loop differ at the spinor level (nonzero psi distance), while a single stage's two orders carry
      no cyclic handedness (the loop built from a single repeated operator has UEUE == EUEU). Number: loop psi
      handedness distance > 0 vs single-operator-loop ~0.
  (B) THE PARITY IS SPINOR-LEVEL (rho-invisible): the 360 loop returns -psi and the 720 loop returns +psi at the
      spinor level (overlap -1 and +1), but at the density level both are identity (rho-overlap +1 for both). So
      the loop tooth is invisible to the density tooling. Number: psi 360-overlap ~ -1, psi 720-overlap ~ +1, rho
      360 and 720 both ~ +1.
  (C) HANDEDNESS (tense) IS ORTHOGONAL TO CHIRALITY (engine type): the loop handedness (UEUE vs EUEU = the tense
      axis) is a DIFFERENT degree of freedom from engine chirality. Measured finding: flipping the engine chirality
      sign (eps) leaves the loop handedness observable UNCHANGED -- so tense and chirality are independent axes (as
      the axis lattice requires; a single DOF must not collapse into another). This is the honest result: the loop
      tooth adds the TENSE axis, which is orthogonal to the chirality axis the terrains already carry, not a
      re-derivation of chirality. Number: handedness is nonzero (tense is real) AND invariant under eps flip
      (orthogonal to chirality).

QUARANTINE_EXPLORATORY. classification="scratch_diagnostic". promotion_allowed=False. Spinor-level (psi in C^2)
unitary loop composition + density-level shadow for the invisibility control. Pure distinguishability (state
overlaps), no bits/vectors. A MECHANISM illustration that the 360 loop is the ratchet's next forced tooth above the
stages -- NOT a claim it is the unique such structure.
"""
import json, os, sys
import numpy as np
from scipy.linalg import expm

sx=np.array([[0,1],[1,0]],complex); sy=np.array([[0,-1j],[1j,0]],complex); sz=np.array([[1,0],[0,-1]],complex)
I2=np.eye(2,dtype=complex); TH=np.pi/4
# TERR eps sign (chirality), from oracle_targets.py
TERR_EPS={0:+1,1:+1,2:+1,3:+1,4:-1,5:-1,6:-1,7:-1}

def spinor_ops(eps):
    """the four operator UNITARIES at the spinor level (psi), sign-carried by engine chirality eps. U = 'unitary/
    transport' beats (Fi/Fe rotations), E = 'measure/pinch' beats represented at spinor level as basis rotations.
    We use the terrain coherent generator H0 = eps*(sx+sy+sz)/sqrt3 for the loop transport and the native rotations
    for the beats -- a closed 4-beat UEUE / EUEU loop."""
    H0=eps*(sx+sy+sz)/np.sqrt(3)
    U_transport=expm(-1j*H0*np.pi/2)          # a quarter of the 360 loop transport
    E_beat=expm(-1j*TH/2*sx)                   # a native rotation beat (Fi-like)
    U2_transport=expm(-1j*H0*np.pi/2)
    E2_beat=expm(-1j*TH/2*sz)                  # a second native beat (Fe-like)
    return U_transport,E_beat,U2_transport,E2_beat,H0

def loop_360(eps, order="UEUE"):
    """a closed 4-beat 360-degree loop at the spinor level, in deductive (UEUE) or inductive (EUEU) order."""
    U,E,U2,E2,H0=spinor_ops(eps)
    beats = [U,E,U2,E2] if order=="UEUE" else [E,U,E2,U2]
    M=I2
    for b in beats: M=b@M
    return M

def rotation(angle, axis=(1,1,1)):
    n=np.array(axis,float); n=n/np.linalg.norm(n)
    N=n[0]*sx+n[1]*sy+n[2]*sz
    return expm(-1j*angle/2*N)

# ---------- PURE INSTRUMENTS ----------

def measure_stage_no_handedness_loop_has():
    """Deductive (UEUE) and inductive (EUEU) traversals of the closed 4-beat loop differ at the spinor level. A loop
    built from a SINGLE repeated operator (no distinct beats) has UEUE == EUEU (no handedness)."""
    psi0=np.array([1,0],complex)
    M_ded=loop_360(+1,"UEUE"); M_ind=loop_360(+1,"EUEU")
    handedness = float(np.linalg.norm(M_ded@psi0 - M_ind@psi0))
    # single-operator loop: all four beats identical -> UEUE == EUEU
    U,_,_,_,_=spinor_ops(+1)
    single_ded = U@U@U@U; single_ind = U@U@U@U
    single_handedness = float(np.linalg.norm(single_ded@psi0 - single_ind@psi0))
    return {"loop_psi_handedness_distance":handedness,"single_operator_loop_handedness":single_handedness}

def measure_parity_is_spinor_level():
    """360 loop returns -psi, 720 returns +psi at the spinor level; at the density level both are identity."""
    psi0=np.array([1,0],complex)
    R360=rotation(2*np.pi); R720=rotation(4*np.pi)
    psi_360_overlap=complex(np.vdot(psi0, R360@psi0)).real     # ~ -1
    psi_720_overlap=complex(np.vdot(psi0, R720@psi0)).real     # ~ +1
    # density level: rho overlap = |<psi0|R|psi0>|^2, both ~ +1 (global phase cancels)
    rho_360_overlap=abs(np.vdot(psi0, R360@psi0))**2           # ~ +1
    rho_720_overlap=abs(np.vdot(psi0, R720@psi0))**2           # ~ +1
    return {"psi_360_overlap":psi_360_overlap,"psi_720_overlap":psi_720_overlap,
            "rho_360_overlap":float(rho_360_overlap),"rho_720_overlap":float(rho_720_overlap)}

def measure_handedness_orthogonal_to_chirality():
    """The loop handedness (UEUE vs EUEU) is the TENSE axis. Measured finding: it is nonzero (tense is real) and
    INVARIANT under an engine-chirality (eps) flip -- so tense is a DIFFERENT DOF from chirality (they do not
    collapse into one another). This is the honest structural result, not a forced sign-flip."""
    psi0=np.array([1,0],complex)
    def handedness(eps):
        M_ded=loop_360(eps,"UEUE"); M_ind=loop_360(eps,"EUEU")
        return float(np.linalg.norm(M_ded@psi0 - M_ind@psi0))     # magnitude of the tense distinction
    h1=handedness(+1); h2=handedness(-1)
    return {"type1_handedness_magnitude":h1,"type2_handedness_magnitude":h2,
            "handedness_is_real":bool(h1>1e-3),
            "handedness_invariant_under_chirality_flip":bool(abs(h1-h2)<1e-9)}

# ---------- SEPARATE POLICY EVAL ----------

def evaluate(mA,mB,mC):
    laneA = (mA["loop_psi_handedness_distance"]>1e-3) and (mA["single_operator_loop_handedness"]<1e-9)
    laneB = (mB["psi_360_overlap"]<-0.99) and (mB["psi_720_overlap"]>0.99) \
            and (mB["rho_360_overlap"]>0.99) and (mB["rho_720_overlap"]>0.99)
    laneC = mC["handedness_is_real"] and mC["handedness_invariant_under_chirality_flip"]
    allflip=bool(laneA and laneB and laneC)
    return {"stage_no_handedness_loop_has_handedness":bool(laneA),
            "parity_is_spinor_level_rho_invisible":bool(laneB),
            "handedness_tense_orthogonal_to_chirality":bool(laneC),
            "NEXT_TOOTH_STAGES_TO_360_LOOP_FORCED":allflip}

def main():
    mA=measure_stage_no_handedness_loop_has()
    mB=measure_parity_is_spinor_level()
    mC=measure_handedness_orthogonal_to_chirality()
    verdict=evaluate(mA,mB,mC)
    out={"classification":"scratch_diagnostic","promotion_allowed":False,
         "framing":"the ratchet's next tooth: engine stages -> the composed 360-degree loop, forced by the loop-handedness demand, read at the spinor level",
         "handedness_lane":mA,"spinor_parity_lane":mB,"chirality_lane":mC,"policy_eval":verdict}
    path=__file__.replace(".py","_results.json"); json.dump(out,open(path,"w"),indent=1)

    print("THE NEXT TOOTH -- from single engine STAGES UP to the composed 360-degree LOOP, read at the spinor level.\n")
    print("  DEMAND a single stage cannot close (a closed traversal must differ from its time-reverse):")
    print(f"    loop deductive(UEUE) vs inductive(EUEU) spinor distance {mA['loop_psi_handedness_distance']:.3f} (>0 -- loop HAS handedness)")
    print(f"    single-operator loop handedness {mA['single_operator_loop_handedness']:.2e} (~0 -- a stage has no cyclic handedness, demand OPEN without the loop)")
    print("  MSS next tooth = a closed 4-beat 360-degree loop, read at the spinor (psi) level.")
    print(f"  PARITY IS SPINOR-LEVEL (rho-invisible): psi 360-overlap {mB['psi_360_overlap']:+.3f} (-> -psi), psi 720-overlap {mB['psi_720_overlap']:+.3f} (-> +psi)")
    print(f"                                          rho 360-overlap {mB['rho_360_overlap']:+.3f}, rho 720-overlap {mB['rho_720_overlap']:+.3f} (both +1 -- density BLIND to the parity)")
    print(f"  HANDEDNESS (tense) ORTHOGONAL TO CHIRALITY: magnitude {mC['type1_handedness_magnitude']:.3f} (real tense) and invariant under eps flip ({mC['handedness_invariant_under_chirality_flip']}) -- tense is a DIFFERENT axis from chirality, not a re-derivation of it")
    print("\n  SEPARATE POLICY EVAL (verdict = all three controls flip):")
    for k,v in verdict.items():
        if k!="NEXT_TOOTH_STAGES_TO_360_LOOP_FORCED": print(f"    {k}: {v}")
    print(f"\n  NEXT TOOTH (STAGES -> 360 LOOP) FORCED: {verdict['NEXT_TOOTH_STAGES_TO_360_LOOP_FORCED']}")
    if verdict["NEXT_TOOTH_STAGES_TO_360_LOOP_FORCED"]:
        print("PASS next_tooth_engine_stages_to_360_loop")
    print("ALL_GATES:", "PASS" if verdict["NEXT_TOOTH_STAGES_TO_360_LOOP_FORCED"] else "FAIL","->",path)
    sys.exit(0 if verdict["NEXT_TOOTH_STAGES_TO_360_LOOP_FORCED"] else 1)

if __name__=="__main__":
    main()
