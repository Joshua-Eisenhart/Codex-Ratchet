# BRANCH_DUAL_CONTEXT_PACK_FAMILY_REVIEW__2026_03_10__v1

Status: DRAFT / NONCANON / A2 CONTROL NOTE
Date: 2026-03-10
Role: bounded review and mutation record for the branch-dual context-pack family under `work/to_send_to_pro`

## 1) Family read

The family had three distinct classes:
- unpacked full pack:
  - `PRO_CONTEXT_PACK__BRANCH_DUAL_DOC_EXTRACTION__v1`
- unpacked light pack:
  - `PRO_CONTEXT_PACK__BRANCH_DUAL_DOC_EXTRACTION__LIGHT__v1`
- zipped full-version chain:
  - `v1.zip`
  - `v1_1.zip`
  - `v1_2.zip`
  - `v1_3.zip`
  - `v1_4.zip`
  - `v1_5.zip`
- zipped light variant:
  - `LIGHT__v1.zip`

## 2) Classification decision

### Keep
- `PRO_CONTEXT_PACK__BRANCH_DUAL_DOC_EXTRACTION__v1`
  - distinct because it contains the unpacked working/output structure
- `PRO_CONTEXT_PACK__BRANCH_DUAL_DOC_EXTRACTION__LIGHT__v1`
  - distinct light variant
- `PRO_CONTEXT_PACK__BRANCH_DUAL_DOC_EXTRACTION__v1_5.zip`
  - latest full zipped version
- `PRO_CONTEXT_PACK__BRANCH_DUAL_DOC_EXTRACTION__v1_5.zip.sha256`
- `PRO_CONTEXT_PACK__BRANCH_DUAL_DOC_EXTRACTION__LIGHT__v1.zip`
- `PRO_CONTEXT_PACK__BRANCH_DUAL_DOC_EXTRACTION__LIGHT__v1.zip.sha256`

### Archive-prep moved
- `PRO_CONTEXT_PACK__BRANCH_DUAL_DOC_EXTRACTION__v1.zip`
- `PRO_CONTEXT_PACK__BRANCH_DUAL_DOC_EXTRACTION__v1.zip.sha256`
- `PRO_CONTEXT_PACK__BRANCH_DUAL_DOC_EXTRACTION__v1_1.zip`
- `PRO_CONTEXT_PACK__BRANCH_DUAL_DOC_EXTRACTION__v1_1.zip.sha256`
- `PRO_CONTEXT_PACK__BRANCH_DUAL_DOC_EXTRACTION__v1_2.zip`
- `PRO_CONTEXT_PACK__BRANCH_DUAL_DOC_EXTRACTION__v1_2.zip.sha256`
- `PRO_CONTEXT_PACK__BRANCH_DUAL_DOC_EXTRACTION__v1_3.zip`
- `PRO_CONTEXT_PACK__BRANCH_DUAL_DOC_EXTRACTION__v1_3.zip.sha256`
- `PRO_CONTEXT_PACK__BRANCH_DUAL_DOC_EXTRACTION__v1_4.zip`
- `PRO_CONTEXT_PACK__BRANCH_DUAL_DOC_EXTRACTION__v1_4.zip.sha256`

Moved destination:
- `archive/distillery/TO_SEND_TO_PRO_BRANCH_DUAL_ARCHIVE_PREP__2026_03_10__v1`

## 3) Size result

- `work/to_send_to_pro` before this family move: `85M`
- `work/to_send_to_pro` after this family move: `68M`
- archive-prep set size: `17M`

## 4) Family decision

The correct live remainder is:
- unpacked full pack
- unpacked light pack
- latest full zip (`v1_5`)
- light zip

Older full zipped versions are superseded and no longer need to remain in the active send surface.

## 5) Next follow-on

Do not broaden back into the already-resolved branch-dual family.

The next bounded local maintenance target inside `work/to_send_to_pro` is now:
- review `STAGE3_FULLBOOT__v1_2`
- review `PRO_AUDIT__FULL_SYSTEM_V3_PLUS_AUTOWIGGLE_AND_LLM_LANE__SINGLE_ATTACHMENT__v1.zip`
- decide whether each is still live reference or archive-ready
