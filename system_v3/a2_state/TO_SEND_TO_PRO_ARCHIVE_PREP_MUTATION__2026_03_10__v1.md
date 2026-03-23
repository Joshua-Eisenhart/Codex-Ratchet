# TO_SEND_TO_PRO_ARCHIVE_PREP_MUTATION__2026_03_10__v1

Status: DRAFT / NONCANON / A2 CONTROL NOTE
Date: 2026-03-10
Role: record of the first bounded archive-first mutation on `work/to_send_to_pro`

## 1) Mutation performed

Moved from active `work/to_send_to_pro` into:
- `archive/distillery/TO_SEND_TO_PRO_ARCHIVE_PREP__2026_03_10__v1`

Moved set:
- stale oversized external boot pair:
  - `PRO_BOOT_JOB__...__20260309_204020Z.zip`
  - matching `.sha256`
- staging residues:
  - `tmp__PRO_THREAD_UPDATE_PACK__v1`
  - `tmp__STAGE_V1_OUTPUTS__v1`
  - `tmp__PRO_THREAD_DELTA__v1`
  - `tmp__PRO_THREAD_DELTA__v2`
- junk:
  - `.DS_Store`

## 2) Post-mutation size

- `work/to_send_to_pro` before: `117M`
- `work/to_send_to_pro` after: `85M`
- archived prep set size: `32M`

## 3) Active keep confirmation

`work/to_send_to_pro/jobs` now contains only:
- `PRO_BOOT_JOB__...__20260309_204341Z.zip`
- matching `.sha256`

This is the correct current external-lane boot artifact pair.

## 4) Remaining large second-wave targets

Still active and unresolved:
- `STAGE3_FULLBOOT__v1_2`
- `PRO_CONTEXT_PACK__BRANCH_DUAL_DOC_EXTRACTION__v1`
- `PRO_CONTEXT_PACK__BRANCH_DUAL_DOC_EXTRACTION__LIGHT__v1`
- zipped branch-dual extraction family
- `PRO_AUDIT__FULL_SYSTEM_V3_PLUS_AUTOWIGGLE_AND_LLM_LANE__SINGLE_ATTACHMENT__v1.zip`

## 5) Next bounded follow-on

Do not broaden yet.

Next maintenance lane:
- review the branch-dual/context-pack family for supersession and active need
- then archive/quarantine one bounded second-wave family only

## 6) Operational consequence

The first send-surface cleanup pass succeeded without touching:
- the active narrow boot artifact
- the active `jobs/` class
- any other `work/` or `system_v3/` surfaces
