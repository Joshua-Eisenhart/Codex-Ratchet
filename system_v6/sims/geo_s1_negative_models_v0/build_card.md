# BUILD CARD: geo_s1_negative_models_v0 — NEGATIVE foundation sims (three models that must FAIL in predicted ways)

Foundation-breadth lane (owner directive: negative sims). Stays at Stage 1. CLAIM UNDER TEST: three deliberately wrong foundation models fail their geometry tests in the exact predicted ways with measured magnitudes — establishing that the S1 invariant suite has teeth (a suite that wrong models pass is decorative).

Ceiling: scratch_diagnostic, promotion_allowed=false, formal_admission_allowed=false. Every negative is labeled negative_model=true; no negative is ever a claim candidate.

## Negative model 1: the no-conjugate map (a fake Hopf)
f(z1,z2) = (|z1|^2-|z2|^2, 2Re(z1 z2), 2Im(z1 z2))  [z2 NOT conjugated]
Predicted failures (compute each): image still lands on S^2 (norm identity still holds — emit this as the "looks right at first glance" receipt), but PHASE INVARIANCE FAILS: f(e^{i alpha}psi) != f(psi) — measure the orbit spread (max image distance over the alpha sweep, predicted order 1); "fibers" are not well-defined (preimage of a base point is not a phase orbit — compute the discrepancy). The suite must catch it via the phase-invariance receipt, NOT via the norm receipt.

## Negative model 2: the naive grid (double-cover ignored)
The N x N (phi,chi) grid treated as 1:1 with T_eta. Predicted failures: distinct-point count N^2 instead of N^2/2 (compute actual distinct spinor count); chart area integral 4pi^2 sin(2eta) vs true 2pi^2 sin(2eta) (factor exactly 2 — emit both and the ratio); volume integral 4pi^2 vs 2pi^2. The identification (a,b)~(a+N/2,b+N/2) computed explicitly for even N including the parity-preservation fact.

## Negative model 3: the classical bit (the N01-negative carrier)
State space = probability p in [0,1] (the simplex); probes = the single diagonal observable family; all probes commute. Predicted failures vs the S1 suite: no phase to erase (the quotient question is empty); reconstructed state-space dimension 1 (vs 3); no double cover (the rotation path question is empty — a 2pi path returns trivially); no fibration (nothing links). Emit each as a computed absence-with-magnitude, not prose. This is the model the roots EXCLUDE: N01 has nothing to act on.

## Controls
The positive S1 model run through the same suite in the same code path (must PASS everything the negatives fail — the shared-path requirement is the anti-fixture-isolation guard); suite-blindness control: each negative must fail ONLY its predicted receipts and pass the others (a negative failing everything means the suite conflates failure modes — report the selectivity matrix).

## Proofs (z3+cvc5, raw values)
Bind negative-1's computed orbit spread: UNSAT that the spread is zero; the true-Hopf control rows -> SAT for zero. Bind negative-2's ratio: UNSAT that ratio != 2 ... careful: assert ratio = 2 exactly from computed integers (distinct counts), UNSAT for any other value; control = corrected grid -> ratio 1.

## Engines (three-engine; identical PIN; source_sha256); R3-v2 lessons binding.
## Files: system_v6/sims/geo_s1_negative_models_v0/ (atomic). No audit_verdict.md. No edits elsewhere.
## Acceptance: validator --require-pytorch ok:true; the selectivity matrix complete (3 negatives x suite receipts, each failure predicted and measured); positive control passes everything; proofs flip; ceiling exact.
