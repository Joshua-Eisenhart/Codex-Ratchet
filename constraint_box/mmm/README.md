# Constraint Box MMM

The MMM primes an LLM with Constraint Box language and evidence boundaries before it produces work. Call it through `PYTHONPATH=src python -m constraintbox mmm <pack>...` from `constraint_box`, or call `mmm/prime.sh <pack>...` from any directory.

| Pack | Job |
| --- | --- |
| `claimgate` | Judge completion from checks, receipts, and mechanically computed verdicts. |
| `cr-ratchet` | Compare probe-honest candidates by constrained distinguishability and retain an antichain of survivors. |
| `lev-os` | Require replay-grade execution evidence and mechanically enforced admission gates. |
| `constraint-programming` | Declare finite variables, domains, and constraints, then separate modelling defects from solver defects. |
| `smt` | Fix theories and encodings before interpreting SAT, UNSAT, models, or unknown results. |
| `nominalist` | Ground identity in an active probe family, admissibility, and the resulting quotient. |
