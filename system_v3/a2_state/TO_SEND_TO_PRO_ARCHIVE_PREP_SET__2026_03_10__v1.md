# TO_SEND_TO_PRO_ARCHIVE_PREP_SET__2026_03_10__v1

Status: DRAFT / NONCANON / A2 CONTROL NOTE
Date: 2026-03-10
Role: exact keep set and exact mutation-prep set for the bounded `work/to_send_to_pro` archive/quarantine-prep lane

## 1) Active keep set

Keep without mutation in the next lane:

### Active jobs
- `work/to_send_to_pro/jobs/PRO_BOOT_JOB__ZIP_JOB__EXTERNAL_RESEARCH_RETOOL_REFINERY__ENTROPY_CARNOT_SZILARD_ENGINE_FAMILIES__CHATUI_DROPIN__v1__20260309_204341Z.zip`
- `work/to_send_to_pro/jobs/PRO_BOOT_JOB__ZIP_JOB__EXTERNAL_RESEARCH_RETOOL_REFINERY__ENTROPY_CARNOT_SZILARD_ENGINE_FAMILIES__CHATUI_DROPIN__v1__20260309_204341Z.zip.sha256`

### Small current update/context surfaces worth retaining for now
- `work/to_send_to_pro/PRO_THREAD_UPDATE_PACK__v5_SMALL`
- `work/to_send_to_pro/PRO_THREAD_UPDATE_PACK__v5_SMALL.zip`
- `work/to_send_to_pro/PRO_THREAD_UPDATE_PACK__v5_SMALL.zip.sha256`
- `work/to_send_to_pro/PRO_THREAD_UPDATE_PACK__v5_1_SMALL.zip`
- `work/to_send_to_pro/PRO_THREAD_UPDATE_PACK__v5_1_SMALL.zip.sha256`
- `work/to_send_to_pro/PRO_THREAD_UPDATE_PACK__v5_2_SMALL.zip`
- `work/to_send_to_pro/PRO_THREAD_UPDATE_PACK__v5_2_SMALL.zip.sha256`
- `work/to_send_to_pro/PRO_THREAD_UPDATE_PACK__v5_3_SMALL.zip`
- `work/to_send_to_pro/PRO_THREAD_UPDATE_PACK__v5_3_SMALL.zip.sha256`
- `work/to_send_to_pro/PRO_THREAD_UPDATE_PACK__v5_4_SMALL.zip`
- `work/to_send_to_pro/PRO_THREAD_UPDATE_PACK__v5_4_SMALL.zip.sha256`
- `work/to_send_to_pro/PRO_CONTEXT_PACK__THREAD_EXTRACT__AUTO__v1`
- `work/to_send_to_pro/PRO_CONTEXT_PACK__THREAD_EXTRACT__AUTO__v1.zip`
- `work/to_send_to_pro/PRO_CONTEXT_PACK__THREAD_EXTRACT__AUTO__v1.zip.sha256`

### Keep pending narrower family review
- `work/to_send_to_pro/PRO_CONTEXT_PACK__THREAD_EXTRACT__v1`
- `work/to_send_to_pro/PRO_CONTEXT_PACK__THREAD_EXTRACT__v1.zip`
- `work/to_send_to_pro/PRO_CONTEXT_PACK__THREAD_EXTRACT__v1.zip.sha256`
- `work/to_send_to_pro/SYSTEM_SAVE__BOOTSTRAP__LATEST__v1.zip`
- `work/to_send_to_pro/SYSTEM_SAVE__BOOTSTRAP__LATEST__v1.zip.sha256`
- `work/to_send_to_pro/PRO_RUN_LAUNCH__DUAL_THREAD_EXTRACTION__v1.md`

## 2) Exact mutation-prep set

These are the exact first mutation-prep candidates for the next bounded lane.
The next lane should archive or quarantine them with lineage notes, not broad-delete them.

### Clear stale oversized job artifact pair
- `work/to_send_to_pro/jobs/PRO_BOOT_JOB__ZIP_JOB__EXTERNAL_RESEARCH_RETOOL_REFINERY__ENTROPY_CARNOT_SZILARD_ENGINE_FAMILIES__CHATUI_DROPIN__v1__20260309_204020Z.zip`
- `work/to_send_to_pro/jobs/PRO_BOOT_JOB__ZIP_JOB__EXTERNAL_RESEARCH_RETOOL_REFINERY__ENTROPY_CARNOT_SZILARD_ENGINE_FAMILIES__CHATUI_DROPIN__v1__20260309_204020Z.zip.sha256`

### Clear tmp staging residue
- `work/to_send_to_pro/tmp__PRO_THREAD_UPDATE_PACK__v1`
- `work/to_send_to_pro/tmp__STAGE_V1_OUTPUTS__v1`
- `work/to_send_to_pro/tmp__PRO_THREAD_DELTA__v1`
- `work/to_send_to_pro/tmp__PRO_THREAD_DELTA__v2`

### Clear junk
- `work/to_send_to_pro/.DS_Store`

## 3) Second-wave investigate-before-mutate set

Do not include these in the first mutation unless the lane explicitly proves supersession:
- `work/to_send_to_pro/STAGE3_FULLBOOT__v1_2`
- `work/to_send_to_pro/PRO_CONTEXT_PACK__BRANCH_DUAL_DOC_EXTRACTION__v1`
- `work/to_send_to_pro/PRO_CONTEXT_PACK__BRANCH_DUAL_DOC_EXTRACTION__LIGHT__v1`
- zipped branch-dual extraction family:
  - `...__v1.zip`
  - `...__v1_1.zip`
  - `...__v1_2.zip`
  - `...__v1_3.zip`
  - `...__v1_4.zip`
  - `...__v1_5.zip`
  - light variant zip
- `work/to_send_to_pro/PRO_AUDIT__FULL_SYSTEM_V3_PLUS_AUTOWIGGLE_AND_LLM_LANE__SINGLE_ATTACHMENT__v1.zip`
- `work/to_send_to_pro/A2_DISTILLERY_TEST_OUTPUT__SMALL_HIGH_ENTROPY_DOCS__v1.zip`

Reason:
- these are large enough to matter
- but not yet cleanly proven superseded by the current narrow external lane alone

## 4) Recommended next mutation order

1. archive/quarantine the stale `204020Z` oversized boot pair
2. archive/quarantine the four `tmp__*` staging residues
3. remove `.DS_Store`
4. stop and re-audit size

Only after that:
5. run one narrower branch-dual/context-pack family review

## 5) Hard boundary

The next mutation lane should stay inside:
- `work/to_send_to_pro`

It should not broaden into:
- `work/system_v3`
- `system_v3/runs`
- other `work/` surfaces
