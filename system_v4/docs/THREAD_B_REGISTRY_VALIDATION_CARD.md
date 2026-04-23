# Thread B Registry Validation Card

**Date:** 2026-03-29
**Status:** Registry-readiness and fence-discipline audit only. This card does not promote permits, canon, or doctrine.

---

## 1. Lexemes Safe For Registry Check

These lexemes are safe to move into a formal registry check, provided their existing tier/fence annotations remain attached exactly as written.

`ROOT_EARNED` / math-basin clear:

- `finite_carrier`
- `noncommutative_composition`
- `finite_scalar_encoding`
- `density_matrix`
- `bipartite_density_matrix`
- `Lindblad_generator`
- `CPTP_semigroup`
- `Channel_composition`
- `basis_invariant`
- `density_derivative`

Safe with existing subordination or realization fence preserved:

- `CPTP_channel`
- `Unitary_commutator`
- `S3_carrier`
- `Hopf_fiber`
- `horizontal_lift_loop`
- `Weyl_sheet`
- `Interaction_unitary`
- `interaction_picture_equivalence`
- `Rotating_frame`
- `signed_cut_functional`

Read:

- The term map and stack audit support registry checking for the above as lexeme candidates only.
- `signed_cut_functional` is registry-check-safe only as a fenced lexeme; it does not advance any cut family.

---

## 2. Lexemes Blocked

Blocked from formal registry submission in the current state:

- `Non_commutativity`

Why blocked:

- the candidates surface carries duplicate / inconsistent naming pressure against the lowercase canonical form `non_commutativity`
- formal registry submission with this drift would weaken fence discipline and create avoidable registry ambiguity

Condition to unblock:

- normalize to one canonical lowercase entry, or remove the duplicate before submission

Highest-risk hold:

- `coherent_information_relation`

Read:

- this is not blocked from review as a fenced candidate, but it is blocked from any relaxed registry handling
- if cited without its hard fence, it would blur the boundary between `coherent_information` (`TERM_PERMITTED`) and `coherent_information_axis0` (`QUARANTINED`)

---

## 3. Term / Lexeme Fence Violations

Current fence-discipline findings:

1. `Non_commutativity` / `non_commutativity` naming drift
   Exact issue: one lexeme family is represented with inconsistent capitalization / duplicate placement, which is a registry-surface violation.

2. `coherent_information_relation` requires a hard fence
   Exact risk: the lexeme can be misread as stabilizing `coherent_information` or softening the quarantine on `coherent_information_axis0`.

3. Geometry lexemes must remain subordinate to term and label surfaces
   Affected lexemes: `Hopf_fiber`, `horizontal_lift_loop`, `Weyl_sheet`
   Exact risk: realization-specific lexemes could appear to outrank `fiber_loop` / `base_loop` or label-only `Hopf` / `Weyl` if their realization fence is dropped.

4. QIT object lexemes must not collapse into branch terms
   Affected lexemes: `CPTP_channel`, `Unitary_commutator`
   Exact risk: object/operator lexemes could be mistaken for promotion of `proper_cptp_branch` or `unitary_branch`.

No other direct term/lexeme fence violations are evident in the audited surfaces.

---

## 4. Exact Minimal Next Step

Produce one registry-clean follow-on patch to `THREAD_B_LEXEME_ADMISSION_CANDIDATES.md` that does only this:

- normalize `Non_commutativity` to one canonical lowercase `non_commutativity` entry and remove the duplicate, with no other admission or doctrine changes

Until that is done, keep the registry check at review-only status.
