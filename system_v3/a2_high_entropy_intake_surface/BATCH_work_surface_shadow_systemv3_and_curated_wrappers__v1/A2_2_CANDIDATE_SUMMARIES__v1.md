# A2_2_CANDIDATE_SUMMARIES__v1
Status: PROPOSED / NONCANONICAL / CANDIDATE REDUCTIONS
Batch: `BATCH_work_surface_shadow_systemv3_and_curated_wrappers__v1`
Extraction mode: `SHADOW_SYSTEMV3_DUPLICATE_AND_CURATED_WRAPPER_PASS`

## Candidate 1: `EXACT_ALIAS_SURFACE_PACKET`
- candidate type:
  - duplicate-tree subset
- compressed read:
  - several `work/system_v3` surfaces are byte-identical aliases under different directory names, including derived-index, control-plane, public-facing, and conformance families
- promotion caution:
  - keep the alias-naming migration debt explicit; do not compress it into “just another mirror”

## Candidate 2: `A2_STATE_MIRROR_DRIFT_PACKET`
- candidate type:
  - state-surface subset
- compressed read:
  - `a2_state` and `a2_persistent_context_and_memory_surface` share the same core summary files but diverge in append-oriented persistence files
- promotion caution:
  - preserve the line-count and sequence drift, not just the shared intent shell

## Candidate 3: `FROZEN_RUNTIME_TOOLING_PACKET`
- candidate type:
  - shadow-runtime subset
- compressed read:
  - the tooling shadow is almost exact duplication, while the deterministic runtime shadow is a reduced subset with a divergent autowiggle implementation
- promotion caution:
  - keep the difference between “subset omission” and “shared-file divergence” visible

## Candidate 4: `CURATED_THREAD_WRAPPER_PACKET`
- candidate type:
  - packaging subset
- compressed read:
  - curated zips package the shadow-system materials into increasingly broad understanding-transfer bundles for existing Pro threads
- promotion caution:
  - preserve the wrappers’ broad contents and their “reduced flooding” claim together

## Candidate 5: `QUARANTINED_PROPOSAL_PACKET`
- candidate type:
  - pre-shadow proposal subset
- compressed read:
  - the minimax spillover quarantine holds a 215-doc proposed-doc snapshot that is related to, but not identical with, the later shadow-system copies
- promotion caution:
  - preserve non-identity with the later shadow tree rather than implying direct lineage by name alone
