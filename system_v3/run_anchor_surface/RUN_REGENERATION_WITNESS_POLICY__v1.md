# RUN_REGENERATION_WITNESS_POLICY__v1

## Status

- surface class: noncanonical anchor/process support surface
- purpose: define the smallest retained witness needed to keep the memo -> cold-core -> selector path auditable after transient pruning

## Problem

- the live A1 regeneration path exists:
  - lawyer memos
  - cold-core strip
  - selector emission
- but old runs often lose replayability at the memo stage because transient memo workspaces are intentionally thinned

## Policy

- do not keep large transient memo trees locally for old runs just to preserve replayability
- when a run or family must remain auditable at the regeneration boundary, keep a compact witness instead

## Preferred Witness Shape

Per anchor run or anchor family, retain:

1. latest memo witness
- either the latest real memo request/response pair
- or a compact memo-summary witness if the raw memo exchange is too large

2. latest cold-core witness
- latest `A1_COLD_CORE_PROPOSALS_v1.json`

3. latest strategy witness
- latest emitted `A1_STRATEGY_v1`

4. provenance note
- tie the memo witness, cold-core witness, and strategy witness together
- include run id or anchor-family id
- include enough context to say this is the retained regeneration witness, not the full transient workspace

## Run-Class Rule

- `ACTIVE`
  - may keep transient memo state while live
- `ANCHOR`
  - should prefer compact regeneration witness retention over full transient memo directories
- `ARCHIVED`
  - should not require local transient memo workspaces

## Citation Rule

- cite this policy or a family/run anchor surface when the question is:
  - how much of memo -> cold-core -> selector history should remain
- do not cite large transient run trees directly unless the exact raw memo artifact matters
