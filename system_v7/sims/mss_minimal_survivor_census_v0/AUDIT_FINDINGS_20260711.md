# Fresh-context audit — mss_minimal_survivor_census_v0 (2026-07-11)

Verdict: CLEAN. Strongest falsifier applied and survived: the auditor REIMPLEMENTED the full census from scratch
(independent decoder, canonicalizer over all 6 permutations, quotient-witness checker, associator search) and
reproduced every count exactly: 19,683 tables; 729 commutative N01-kills (=3^6, matches the declared obligation,
no narrowing); 17,752 quotient-only minima in 2,989 iso classes; association split 24 raw / 6 iso associative vs
17,728 / 2,983 witnessed-nonassociative. 5 nonassociative witnesses and all 6 associative minima hand-verified.
3 quotient-kill records verified as genuine homomorphisms onto N01+probe-surviving targets. z3 partition check
flips on erasure (SAT->UNSAT); its ceiling honestly stated as count-consistency only. Byte-identical reruns.

AUDIT DISCOVERY (structural, disclosed): probe-distinguishability is PROVABLY INERT at N=3 — exactly 3 tables in
the entire space fail it (the three constant tables), all commutative, so N01 subsumes it completely at this
carrier size. The 0-kill count is a theorem of the space, not decorative weakness. OPEN DIG: test the probe
obligation's independent bite at N>3 (does it kill anything N01 misses on 4-element carriers?) before treating it
as a filtering constraint anywhere.

Headline that survives at ceiling (classical_baseline, promotion false, exhaustive-N=3, quotient-only floor):
witnessed nonassociativity is generic among minimal survivors in this grammar (99.8% of iso classes); associativity
is the rare special structure — the direct measurement behind
corrections/OWNER_NONASSOCIATIVITY_FLOOR_CORRECTION_20260711.md.
