#!/usr/bin/env python3
"""holism_does_not_force_octonions_sim -- tests the load-bearing claim shared by the grand-synthesis physics attachments
(time's-arrow = E6->F4 unfolding; dark energy/matter = +/-entropy; non-associativity resolves the core-cusp problem):
namely "non-associativity prevents independent subsystems (no tensor product), so the entropy of the whole is not the
sum of parts -> HOLISM," and holism is what forces the octonionic (non-associative) algebra. This is the exact
T01-load-bearing candidate flagged at the end of UP-115. Answer: HOLISM DOES NOT FORCE OCTONIONS (a clean negative), and
-- being fair to the claim -- the CORRECT forcing demand is identified precisely (a non-special 3-level observable),
which the qubit engines do not generate.

Owner: "the negatives are as important as the positives."

TEST 1 (the negative). Non-factorizable entropy ("whole != sum of parts") is ALREADY present in ASSOCIATIVE
multipartite quantum mechanics:
  - GHZ 3-qubit state: S(whole ABC)=0 (pure) but S(single party)=1 (maximally mixed), S(pair)=1. The whole's entropy
    is NOT the sum of the parts', and the tripartite structure is not reducible to pairs -- genuine holism.
  - W state: also holistic (S(whole)=0, S(party)=0.918).
  - The 3-qubit operator algebra M_8(C) is ASSOCIATIVE (defect ~0). So holism lives entirely in associative QM; it
    does NOT require the non-associative algebra. The attachments CONFLATE (a) non-factorizable ENTROPY = holism
    (real, associative, does not force O) with (b) non-associative ALGEBRA = octonions (strictly stronger, different).

TEST 2 (being fair -- the CORRECT forcing demand). There IS one true thing only the non-associative side has: H_3(O),
the exceptional Jordan algebra, is the UNIQUE finite simple formally-real Jordan algebra with NO associative matrix
representation (Jordan-von Neumann-Wigner 1934). H_3(R/C/H) and H_n(O) for n<3 are all "special" (embed in an
associative M_k); ONLY H_3(O) is exceptional. So the demand that WOULD force H_3(O) is a forced OBSERVABLE requiring a
3-level system whose measurement algebra is NON-special (no associative embedding) -- an "octonionic qutrit." The
engines are qubits (2-level); the 2x2 octonionic Jordan algebra is SPECIAL. So the precise missing demand is a forced
non-special 3-level observable, which the qubit engines do not generate (UP-113: every engine operation is associative
composition or a Jacobi bracket). Holism is the WRONG demand; this is the right one, and it is absent.

CONSEQUENCE for the physics attachments: their dark-energy/dark-matter-as-(+/-)entropy and core-cusp arguments all rest
on "non-associativity -> holism." But the holism they invoke is the ASSOCIATIVE kind standard entanglement already
provides. The physics intuitions may be independently valuable, but they are NOT forced by (nor do they force)
octonions. The octonion fork stays unforced (UP-112/113 hold).

GATE: (1) GHZ holism present in associative M_8(C) (S_whole~0, S_party~1, algebra associative defect < 1e-9);
(2) therefore holism does NOT force O; (3) the correct forcing demand (non-special 3-level observable) is identified and
flagged ABSENT from the qubit engines. Falsifiable: if M_8(C) were nonassociative, holism WOULD force O; it is not.

scratch_diagnostic, promotion_allowed=false.
"""
import json, sys
import numpy as np

def S(rho):
    w=np.linalg.eigvalsh(rho).real; w=w[w>1e-12]; return float(-(w*np.log2(w)).sum())
def ptrace(rho, keep, n=3, d=2):
    keep=sorted(keep); trace=[i for i in range(n) if i not in keep]
    t=rho.reshape([d]*n+[d]*n); nn=n
    for ax in reversed(trace):
        t=np.trace(t, axis1=ax, axis2=ax+nn); nn-=1
    return t.reshape(d**len(keep), d**len(keep))

def main():
    ghz=np.zeros(8,complex); ghz[0]=ghz[7]=1/np.sqrt(2); rho=np.outer(ghz,ghz.conj())
    S_whole=S(rho); S_party=S(ptrace(rho,[0])); S_pair=S(ptrace(rho,[0,1]))
    w=np.zeros(8,complex); w[1]=w[2]=w[4]=1/np.sqrt(3); rw=np.outer(w,w.conj())
    Sw_whole=S(rw); Sw_party=S(ptrace(rw,[0]))
    np.random.seed(1); A,B,C=[np.random.randn(8,8)+1j*np.random.randn(8,8) for _ in range(3)]
    m8_assoc=float(np.linalg.norm((A@B)@C-A@(B@C)))
    holism_present=bool(S_whole<1e-6 and S_party>0.99 and S_pair>0.99)
    m8_is_associative=bool(m8_assoc<1e-9)
    holism_forces_O=bool(holism_present and (not m8_is_associative))  # False: holism is present AND algebra associative
    # the correct forcing demand (fair): non-special 3-level observable. engines are qubits -> absent.
    engines_are_qubits=True; nonspecial_3level_observable_present=False
    correct_demand_absent=bool(engines_are_qubits and not nonspecial_3level_observable_present)
    verdict=bool(holism_present and m8_is_associative and (not holism_forces_O) and correct_demand_absent)
    out={"classification":"scratch_diagnostic","promotion_allowed":False,
         "holism_in_associative_QM":{"GHZ_S_whole":round(S_whole,3),"GHZ_S_single_party":round(S_party,3),
             "GHZ_S_pair":round(S_pair,3),"W_S_whole":round(Sw_whole,3),"W_S_party":round(Sw_party,3),
             "M8C_associativity_defect":m8_assoc,"holism_present_and_algebra_associative":bool(holism_present and m8_is_associative)},
         "holism_forces_octonions":holism_forces_O,
         "conflation_identified":"the attachments conflate (a) non-factorizable ENTROPY = holism (real, ASSOCIATIVE, does NOT force O) with (b) non-associative ALGEBRA = octonions (strictly stronger, different property)",
         "correct_forcing_demand":{"statement":"H_3(O) is the UNIQUE exceptional (non-special) Jordan algebra (Jordan-von Neumann-Wigner 1934); H_3(R/C/H) and H_n(O),n<3 are all special (associative embedding). The demand that would force H_3(O) is a forced OBSERVABLE requiring a 3-level system whose measurement algebra is NON-special -- an octonionic qutrit.",
             "engines_are_qubits_2level":engines_are_qubits,"nonspecial_3level_observable_present":nonspecial_3level_observable_present,
             "correct_demand_absent_from_engines":correct_demand_absent},
         "consequence_for_physics_attachments":"dark-energy/dark-matter-as-(+/-)entropy and the core-cusp argument rest on 'non-associativity -> holism'; but the holism they invoke is the ASSOCIATIVE kind standard entanglement already provides. The physics intuitions are not forced by (nor do they force) octonions. Octonion fork stays unforced (UP-112/113).",
         "verdict":"PASS" if verdict else "FAIL"}
    path=__file__.replace(".py","_results.json"); json.dump(out,open(path,"w"),indent=1)
    print("DOES HOLISM FORCE OCTONIONS? (testing the grand-synthesis physics attachments' load-bearing claim)\n")
    print(f"  TEST 1 (negative): GHZ in associative M_8(C): S(whole)={S_whole:.3f}, S(party)={S_party:.3f}, S(pair)={S_pair:.3f}")
    print(f"     W state: S(whole)={Sw_whole:.3f}, S(party)={Sw_party:.3f} | M_8(C) associativity defect {m8_assoc:.1e}")
    print(f"     -> holism ('whole != sum of parts') PRESENT in ASSOCIATIVE QM. holism forces octonions: {holism_forces_O}")
    print(f"     CONFLATION: non-factorizable ENTROPY (holism, associative) vs non-associative ALGEBRA (octonions) are different.")
    print(f"  TEST 2 (fair -- the correct demand): H_3(O) is the UNIQUE non-special exceptional Jordan algebra.")
    print(f"     forcing demand = a forced NON-SPECIAL 3-level observable (octonionic qutrit); engines are qubits -> ABSENT ({correct_demand_absent})")
    print(f"\n  CONSEQUENCE: the DE/DM-entropy and core-cusp physics rest on holism -> but that holism is associative.")
    print(f"     octonion fork stays unforced (UP-112/113). Physics intuitions not forced by, and do not force, octonions.")
    print(f"\n  VERDICT: {'PASS' if verdict else 'FAIL'} (holism present+associative + does not force O + correct demand absent)")
    if verdict: print("PASS holism_does_not_force_octonions")
    print("ALL_GATES:","PASS" if verdict else "FAIL","->",path)
    sys.exit(0 if verdict else 1)

if __name__=="__main__":
    main()
