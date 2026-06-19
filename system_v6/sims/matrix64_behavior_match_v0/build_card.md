# BUILD CARD -- matrix64_behavior_match_v0

Owner card: additive Matrix64 behavior packet. No git add/commit.

## Authority

- I Ching match packet and audit:
  - `system_v6/sims/iching_symmetry_match_v0/iching_symmetry_match_v0.py`
  - `system_v6/sims/iching_symmetry_match_v0/results/iching_symmetry_match_v0_results.json`
  - `system_v6/sims/iching_symmetry_match_v0/audit_verdict.md`
  - User-supplied audit hash hint: `2b32714a0`
- Fingerprint IDs packet:
  - `system_v6/sims/eng64_stage_fingerprint_ids_v0/eng64_stage_fingerprint_ids_v0.py`
  - `system_v6/sims/eng64_stage_fingerprint_ids_v0/results/eng64_stage_fingerprint_ids_v0_results.json`
  - User-supplied hash hint: `fab7b2253`
- Audited 64-run:
  - `system_v5/julia_carrier/eng_64_hexagram_julia_results.json`
  - User-supplied audit/run hash hint: `23cfa5536`

## Object

Compute the realization-relative behavioral symmetry of the pinned 64-stage realization.

Question: for each generator of the address-level hexagram transformation group, does the induced address permutation descend through the stable 16-component fingerprint quotient?

Descent criterion: for every fingerprint component, all member stages must map under the generator into one target fingerprint component.

Emit:

- one row per named generator;
- the full 256-element address group size;
- the subgroup of full group elements that descend;
- breaking component witnesses for non-descending generators;
- a check row against the I Ching audit's prior pointwise/preserve finding;
- controls for identity, random stage-to-component relabeling, and a deliberately coarsened quotient.

## Fences

- STRICTLY ADDITIVE: write only inside `system_v6/sims/matrix64_behavior_match_v0/`.
- No git add/commit.
- `classification` is `scratch_diagnostic`.
- `promotion_allowed=false`; `formal_admission_allowed=false`.
- Claim ceiling: realization-relative behavioral-symmetry table only.
- This is the pinned realization's behavioral symmetry, not Matrix64-in-general.
- No 64-behavior isomorphism, Matrix64 completion, King-Wen-order correspondence, QIT admission, physics admission, bridge claim, axis closure, or canonical promotion.
- King-Wen stays comparator-only and fenced out of the behavior claim.

## Standards

- Use `scripts/builder_audit_boundary.py` from birth.
- G.2a is binding from birth: validator/tests must not hard-assert that `audit_verdict.md` is absent.
- Result envelope must include `classification`, `TOOL_MANIFEST`, `TOOL_INTEGRATION_DEPTH`, claim boundary, controls, and source locks.
- Packet-local validator must write a validator result and fail closed on schema/control/claim-boundary drift.
