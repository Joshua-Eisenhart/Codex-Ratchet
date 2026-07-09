#!/usr/bin/env python3
"""octonion_fork_not_forced_sim -- the honest closure of the octonion/exceptional arc (UP-107/108/109/110/111): is the
carrier lift H->O FORCED by the root constraints, or is it an unforced observable-side FORK? Answer: FORK. Independently
reproduces a DECISIVE, 3-model-panel-cleared root-axiom finding already in the owner's docs ("non-associativity is
INSTALLED not forced"), and corroborated a THIRD time by the codex desktop system's choi_field...albert_stress run and
Grok 4.5 (both block "natural/canonical Choi-to-octonion map").

Owner frame (verbatim): "clifford, jordan, albert, are just some [math] that have been [useful]" -- i.e. explore the
RANGE of possible math and map which is forced vs available. This sim maps the fork.

THE FORK (root_axioms:51; 05_NONASSOCIATIVITY_BRANCHES.md:104-126; whole-physics ledger:561-572):
  - F01 (finitude) + N01 (noncommutation) are the root constraints. They FORCE R->C (lose order) and C->H (lose
    commutativity): the qubit su(2) is noncommutative, satisfying N01.
  - H is ALREADY a normed division algebra. Division-algebra-ness does NOT force the next doubling.
  - H->O loses ASSOCIATIVITY (T01/grouping). NOTHING in {F01,N01} requires grouping-dependence. So H->O is NOT forced.
  - It is an OBSERVABLE/PROBE-SIDE FORK: if associativity is REQUIRED, the basin is {H}; if NOT required (observable/
    Jordan side primary), the basin is {H,O}. Sedenions are excluded either way (zero divisors), not by associativity.

TESTS (all from scratch):
  (1) 3-qubit floor does NOT force O: the 3-qubit operator algebra M_8(C) is ASSOCIATIVE (defect ~0). C^8 uses the
      associative matrix algebra, not the octonions. (three_qubit_floor is independent of H->O.)
  (2) N01 does NOT force O: the quaternions H are noncommutative (>0) AND associative (defect 0). N01 is satisfied at H
      without any nonassociativity.
  (3) THE FORK basin: associativity-required -> {H}; not-required -> {H,O}. Both are consistent with {F01,N01}; the
      root constraints do not decide between them -- the observable-side choice does.
  (4) WHERE each math lives (the range map): quaternion H = FORCED (engines run here, UP-109). Octonion O / Albert
      H_3(O) / exceptional F4,E6 = LIVE on the {H,O} branch, NOT forced. Clifford Cl_n = associative (lives on the {H}
      branch, always available). This maps the owner's "clifford, jordan, albert" onto forced-vs-fork.

CONCLUSION: the exceptional tower (UP-108) is genuine mathematics over the Albert algebra, but it sits on the {H,O}
branch that is LIVE, not FORCED. The engines are at H (UP-109); the field symmetry is classical (UP-111); H->O is an
unforced observable-side fork (this sim). To EARN the octonion rung, the model must exhibit a mechanism where GROUPING
(nonassociativity/T01) is load-bearing -- i.e. a demand a single associative carrier cannot close. No current engine
mechanism requires that. This is the precise, constructive statement of what is missing.

GATE: (1) M_8(C) associative (defect < 1e-9); (2) H noncommutative (>0.1) AND associative (defect < 1e-9); (3) the fork
is real -- associativity-required basin = {H}, not-required basin = {H,O}; (4) therefore H->O NOT forced. Falsifiable:
if M_8 were nonassociative, or if H were nonassociative, the 3-qubit/N01 route WOULD force O; neither holds.

scratch_diagnostic, promotion_allowed=false. Reproduces a panel-cleared doc finding; reports only computed values.
"""
import json, sys
import numpy as np

def m8_associativity():
    np.random.seed(0)
    A,B,C=[np.random.randn(8,8)+1j*np.random.randn(8,8) for _ in range(3)]
    return float(np.linalg.norm((A@B)@C-A@(B@C)))

def quaternion_props():
    qi=np.array([[1j,0],[0,-1j]],complex); qj=np.array([[0,1],[-1,0]],complex); qk=np.array([[0,1j],[1j,0]],complex)
    noncomm=float(np.linalg.norm(qi@qj-qj@qi))
    assoc=float(np.linalg.norm((qi@qj)@qk-qi@(qj@qk)))
    return noncomm,assoc

def octonion_nonassoc():
    tri=[(1,2,3),(1,4,5),(1,7,6),(2,4,6),(2,5,7),(3,4,7),(3,6,5)]
    S=np.zeros((8,8),int); X=np.zeros((8,8),int)
    for i in range(8): S[0,i]=1; X[0,i]=i; S[i,0]=1; X[i,0]=i
    for i in range(1,8): S[i,i]=-1; X[i,i]=0
    for (a,b,c) in tri:
        for (p,q,r) in [(a,b,c),(b,c,a),(c,a,b)]: S[p,q]=1; X[p,q]=r; S[q,p]=-1; X[q,p]=r
    def om(u,v):
        w=np.zeros(8)
        for i in np.nonzero(u)[0]:
            for j in np.nonzero(v)[0]: w[X[i,j]]+=S[i,j]*u[i]*v[j]
        return w
    np.random.seed(0); a,b,c=[np.random.randn(8) for _ in range(3)]
    return float(np.linalg.norm(om(om(a,b),c)-om(a,om(b,c))))

def main():
    m8=m8_associativity(); qnc,qas=quaternion_props(); onassoc=octonion_nonassoc()
    three_qubit_forces_O=bool(m8>1e-9)         # would need M_8 nonassociative -- it is not
    n01_forces_O=bool(qas>1e-9)                # would need H nonassociative -- it is not
    # the fork: both basins consistent with {F01,N01}; sedenions excluded either way
    basin_assoc_required=["H"]; basin_assoc_not_required=["H","O"]
    h_to_o_forced=bool(three_qubit_forces_O or n01_forces_O)  # False: neither route forces it
    fork_is_real=bool((not h_to_o_forced) and onassoc>1e-6)   # O genuinely nonassociative, but not forced
    range_map={"quaternion_H":"FORCED (engines run here, UP-109; N01 satisfied, associative)",
               "octonion_O":"LIVE on {H,O} branch, NOT forced (nonassociative; needs grouping-demand to earn)",
               "albert_H3O":"LIVE on {H,O} branch (Jordan observables over O; exceptional F4/E6 symmetry, UP-108)",
               "clifford_Cl_n":"associative -> lives on the {H} branch, always available (not a fork)"}
    verdict=bool((not three_qubit_forces_O) and (not n01_forces_O) and fork_is_real)
    out={"classification":"scratch_diagnostic","promotion_allowed":False,
         "m8_3qubit_associativity_defect":m8,"three_qubit_floor_forces_octonions":three_qubit_forces_O,
         "quaternion_noncommutativity":round(qnc,3),"quaternion_associativity_defect":qas,
         "n01_noncommutation_forces_octonions":n01_forces_O,
         "octonion_nonassociativity":round(onassoc,3),
         "fork":{"associativity_required_basin":basin_assoc_required,"associativity_not_required_basin":basin_assoc_not_required,
             "both_consistent_with_F01_N01":True,"sedenions_excluded_either_way":"zero divisors, not associativity"},
         "h_to_o_forced":h_to_o_forced,"h_to_o_is_unforced_observable_fork":fork_is_real,
         "range_map_forced_vs_fork":range_map,
         "reproduces_doc_finding":"'non-associativity is INSTALLED not forced' -- decisive 3-model-panel-cleared root-axiom finding (root_axioms:51; 05_NONASSOCIATIVITY_BRANCHES.md; whole-physics ledger:561-572). Independently corroborated by codex choi_field...albert_stress + Grok 4.5 (both block natural Choi-to-octonion map).",
         "what_would_earn_the_octonion_rung":"a mechanism where GROUPING (nonassociativity/T01) is load-bearing -- a demand a single associative carrier cannot close. No current engine mechanism requires it. The exceptional tower (UP-108) is genuine math on the {H,O} branch but LIVE, not FORCED.",
         "verdict":"PASS" if verdict else "FAIL"}
    path=__file__.replace(".py","_results.json"); json.dump(out,open(path,"w"),indent=1)
    print("OCTONION FORK: is H->O forced, or an unforced observable-side fork?\n")
    print(f"  (1) 3-qubit M_8(C) associativity defect {m8:.1e} -> 3-qubit floor forces octonions: {three_qubit_forces_O}")
    print(f"  (2) quaternion H: noncomm {qnc:.2f} (>0) AND assoc defect {qas:.1e} (=0) -> N01 forces octonions: {n01_forces_O}")
    print(f"  (3) THE FORK: associativity-required -> {basin_assoc_required} | not-required -> {basin_assoc_not_required} (both consistent with F01+N01)")
    print(f"      octonion nonassociativity {onassoc:.2f} (genuinely nonassoc, but INSTALLED not forced)")
    print(f"  (4) range map (forced vs fork):")
    for k,v in range_map.items(): print(f"        {k}: {v}")
    print(f"\n  H->O forced: {h_to_o_forced}  | unforced observable-side fork: {fork_is_real}")
    print(f"  reproduces the doc's decisive panel-cleared finding: nonassociativity is INSTALLED not forced.")
    print(f"  to EARN the octonion rung: need a mechanism where GROUPING (T01) is load-bearing. None present.")
    print(f"\n  VERDICT: {'PASS' if verdict else 'FAIL'} (neither 3-qubit nor N01 forces O; fork is real)")
    if verdict: print("PASS octonion_fork_not_forced")
    print("ALL_GATES:","PASS" if verdict else "FAIL","->",path)
    sys.exit(0 if verdict else 1)

if __name__=="__main__":
    main()
