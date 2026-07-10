# Fabrication Audit

Verdict: `found_fabrication_in_final_receipts: false` after correction commit
`8615977aa`.

## Defects Found And Repaired

A fresh-context audit found two overstatements in the first selection
controller:

1. normalized score-projection hashes were labelled as complete-record hashes;
2. the controller compared engine-declared shortlists and winners without
   independently deriving them.

The correction renames the hashes, narrows the cross-runtime claim, rederives
all three top-32 shortlists and exact winners, and marks the frozen sizes as not
claim-bearing before validation. The winner values did not change.

## Independent Audits

- A fresh Codex auditor independently recomputed all shortlists and winners and
  identified the original controller defects.
- Lev executed a read-only audit of the pre-correction freeze. Its header
  advertised Sonnet, but its sealed receipt reports Claude Opus 4.6; this model
  routing mismatch is preserved and the audit is advisory only.
- A direct Claude Fable 5 medium audit of corrected commit `8615977aa` confirmed
  both repairs and emphasized the remaining shared-bug and self-attested read
  confinement risks. See `advisory/FABLE_FREEZE_V2_AUDIT.md`.

## Remaining Limits

- JAX/Julia agreement does not eliminate a shared authoring or specification
  bug. Boundary brute-force controls reduce but do not remove that risk.
- Prohibited-read lists are source declarations checked by the controller, not
  operating-system traces.
- The train search is exact only within the preregistered 32-design shortlist
  after an exhaustive cheap screen; it is not a global exact optimum of the
  relation objective.
- The carrier and target are authored finite ECA constructions. No semantic
  object, perception, or real-world sensing claim follows.

## Final Claim Ceiling

Independent JAX and Julia implementations exactly reject these three frozen
target-aware ECA observation designs on the reserved validation family. This
earns a finite experimental-design falsification and a better specification for
the next experiment. It earns no learner, perception engine, spontaneous object
formation, four substages, 64-stage schedule, MMM, ontology, Axis0, or physics
promotion.
