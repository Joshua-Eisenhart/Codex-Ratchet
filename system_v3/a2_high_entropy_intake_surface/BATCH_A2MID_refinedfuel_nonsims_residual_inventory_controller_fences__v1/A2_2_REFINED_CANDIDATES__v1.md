# A2_2_REFINED_CANDIDATES__v1
Status: PROPOSED / NONCANONICAL / A2-2 REFINED CANDIDATES
Batch: `BATCH_A2MID_refinedfuel_nonsims_residual_inventory_controller_fences__v1`
Extraction mode: `A2_MID_REFINEMENT_PASS`
Date: 2026-03-09

## Candidate RC1: `NONSIMS_REFINEDFUEL_DIRECT_SOURCE_COVERAGE_IS_CLOSED_AND_THE_ONLY_RESIDUAL_IS_HYGIENE`
- candidate read:
  - controller reads should preserve that the non-sims refined-fuel root is direct-source complete and that the only residual surface is `.DS_Store`, which remains hygiene-only residue rather than an unbatched source family
- why candidate:
  - this is the parent's strongest closure boundary
- parent dependencies:
  - `CLUSTER_MAP__v1.md:1`
  - `CLUSTER_MAP__v1.md:2`
  - `TENSION_MAP__v1.md:1`
  - `SOURCE_MAP__v1.md`
  - `MANIFEST.json`

## Candidate RC2: `BROAD_SAME_ROOT_SOURCE_EXTRACTION_SHOULD_STOP_AFTER_FULL_SLICE_COVERAGE`
- candidate read:
  - controller reads should preserve that top-level docs, `THREAD_S_FULL_SAVE`, and `constraint ladder` are all fully represented, so new broad same-root source extraction is weaker than the completed root-slice coverage already recorded here
- why candidate:
  - this is the cleanest compression of the parent's stop-enumerating rule
- parent dependencies:
  - `CLUSTER_MAP__v1.md:2`
  - `SOURCE_MAP__v1.md`
  - `A2_3_DISTILLATES__v1.md`

## Candidate RC3: `MULTI_COVERAGE_IS_ROUTING_DEBT_NOT_MISSING_SOURCE_CONTACT`
- candidate read:
  - controller reads should preserve that the `20` multi-covered direct members represent routing and reuse discipline debt rather than proof of missing source contact
- why candidate:
  - this is the parent's strongest anti-duplication-overread rule
- parent dependencies:
  - `CLUSTER_MAP__v1.md:3`
  - `TENSION_MAP__v1.md:2`
  - `SOURCE_MAP__v1.md`
  - `A2_3_DISTILLATES__v1.md`

## Candidate RC4: `REVISIT_REQUIRED_REENTRY_NOW_DOMINATES_AND_CONSTRAINTS_ENTROPY_IS_THE_NOMINATED_START`
- candidate read:
  - controller reads should preserve that the next quality gap is the `REVISIT_REQUIRED` refined-fuel queue and that the nominated high-value start is `Constraints. Entropy.md` rather than any new broad source-map campaign
- why candidate:
  - this is the parent's strongest live handoff rule
- parent dependencies:
  - `CLUSTER_MAP__v1.md:4`
  - `TENSION_MAP__v1.md:3`
  - `A2_2_CANDIDATE_SUMMARIES__v1.md`
  - `A2_3_DISTILLATES__v1.md`
  - `MANIFEST.json`

## Candidate RC5: `CLOSURE_AUDIT_IS_A_ROUTING_BOUNDARY_NOT_SEMANTIC_CLOSURE_OR_ACTIVE_AUTHORITY`
- candidate read:
  - controller reads must keep this batch as a routing-boundary artifact only: it can close broad non-sims refined-fuel enumeration, but it cannot grant semantic closure, canon, runtime truth, or mutation authority
- why candidate:
  - this is the narrowest controller-usable read that preserves the audit's value without overpromoting it
- parent dependencies:
  - `TENSION_MAP__v1.md:4`
  - `A2_3_DISTILLATES__v1.md`
  - `MANIFEST.json`

## Quarantined Q1: `DOT_DS_STORE_AS_A_REAL_UNBATCHED_SOURCE_FAMILY`
- quarantine read:
  - do not treat the remaining `.DS_Store` file as evidence of a real unbatched refined-fuel source family
- why quarantined:
  - the parent explicitly preserves it as hygiene-only residue
- parent dependencies:
  - `CLUSTER_MAP__v1.md:1`
  - `TENSION_MAP__v1.md:1`
  - `A2_3_DISTILLATES__v1.md`

## Quarantined Q2: `MULTI_COVERAGE_AS_PROOF_THAT_SOURCE_COVERAGE_IS_STILL_INCOMPLETE`
- quarantine read:
  - do not let the `20` multi-covered direct members become proof that root coverage failed or that new broad source enumeration must resume
- why quarantined:
  - the parent explicitly separates multi-coverage from missing coverage
- parent dependencies:
  - `CLUSTER_MAP__v1.md:3`
  - `TENSION_MAP__v1.md:2`
  - `A2_3_DISTILLATES__v1.md`

## Quarantined Q3: `CLOSURE_SIGNALS_AS_SEMANTIC_CLOSURE_CANON_OR_MUTATION_PERMISSION`
- quarantine read:
  - do not treat archive-manifest closure markers, coverage completion, or root-audit totals as proof of semantic closure, canon status, runtime authority, or permission to mutate active A2 surfaces
- why quarantined:
  - the parent is useful precisely because it is routing-only rather than authorizing
- parent dependencies:
  - `TENSION_MAP__v1.md:4`
  - `A2_3_DISTILLATES__v1.md`
  - `MANIFEST.json`

## Quarantined Q4: `NEW_BROAD_REFINEDFUEL_SOURCE_MAP_SWEEP_INSTEAD_OF_SELECTIVE_REENTRY`
- quarantine read:
  - do not reopen broad same-root refined-fuel source mapping while the real unresolved work remains concentrated in the `REVISIT_REQUIRED` queue
- why quarantined:
  - the parent explicitly routes next work into selective re-entry
- parent dependencies:
  - `CLUSTER_MAP__v1.md:4`
  - `TENSION_MAP__v1.md:3`
  - `A2_2_CANDIDATE_SUMMARIES__v1.md`
