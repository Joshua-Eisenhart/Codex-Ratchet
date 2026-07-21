# Bridge-validation audit — CLEAN (fresh opus adversarial, 2026-07-20)

BRIDGE_VALIDATION AUDIT: CLEAN — all 12 checks (9 controls + 3 self-tests) independently
re-derived and matched results/bridge_validation.json; C2 catches illicit relabeling by
outcome content where a partition-only check provably would NOT (identical digits
(0,1,2,1,2,0,0) while content flips pos<->neg); hidden-table smuggle caught both ways; no
primitive probability (Outcome rejects non-int/non-positive multiplicities) or primitive
time (step_C is a pure fold over an ordered finite word); os._exit preserves the honest
exit code. Decorative-solver falsifier: erasing the measured value flips z3+cvc5 sat->unsat
-> "SMT tautological" hypothesis KILLED.

TWO NON-FATAL CAVEATS (honestly labeled in-code, not fabrication):
1. C9 "two-bridge agreement" is STRUCTURAL, not independent: bridge_smt_relational.py induces
   its partition from _reference_same (the SAME recursion as the action-predictive signature);
   z3/cvc5 GATE agreement but do not DECIDE the partition. As built the two bridges CANNOT
   disagree. Labeled "concordance" not "corroboration", promotion_allowed=false. => the owner's
   "two LIVE RIVALS" requirement is NOT yet met.
2. The z3/cvc5 lane is load-bearing on the outcome value (verdict flips when value erased) but
   adds NO capability beyond the pure-Python reference, because a fully-ground finite behavior
   table makes distinguishability mere equality-checking. SMT only earns its place if candidates
   compile to a THEORY (relations + axioms) decided by entailment/search — the grok design's
   actual intent, not what was built.

FIX to make the bridges genuine rivals: implement the SMT-relational bridge per its design —
candidate behavior compiles to a finite theory (ground model + carrier axioms) over the shared
vocabulary; z3/cvc5 decide distinguishability by entailment (SAT=distinct, UNSAT=forced-same);
partition induced from the solver decisions, INDEPENDENT of _reference_same. Then C9 tests real
agreement and disagreement -> HOLD becomes meaningful.
