# NEXT_MAINTENANCE_TARGET__TO_SEND_TO_PRO_ARCHIVE_PREP__2026_03_10__v1

Status: DRAFT / NONCANON / A2 CONTROL NOTE
Date: 2026-03-10
Role: explicit next local maintenance target after bounded audit of `work/system_v3` and `work/to_send_to_pro`

## Selected next target

Run one bounded archive/quarantine-prep lane on stale send/staging residue under:
- `work/to_send_to_pro`

## Why this target first

- it is a large local pressure surface (`117M`)
- it contains an active core (`jobs`) plus clearly stale/superseded residue
- it is safer to classify and thin than `work/system_v3`, which is more ambiguous and should remain a later quarantine/investigation lane

## Initial bounded candidate set

1. stale oversized external boot pair:
- `work/to_send_to_pro/jobs/PRO_BOOT_JOB__ZIP_JOB__EXTERNAL_RESEARCH_RETOOL_REFINERY__ENTROPY_CARNOT_SZILARD_ENGINE_FAMILIES__CHATUI_DROPIN__v1__20260309_204020Z.zip`
- matching `.sha256`

2. staging residue:
- `work/to_send_to_pro/tmp__PRO_THREAD_UPDATE_PACK__v1`
- `work/to_send_to_pro/tmp__STAGE_V1_OUTPUTS__v1`

3. then one older large context-pack family only if clearly superseded:
- `PRO_CONTEXT_PACK__BRANCH_DUAL_DOC_EXTRACTION__*`

## Hard rule

Do not mutate:
- the narrow `204341Z` boot artifact pair
- `jobs/` as an active class
- live current send artifacts without explicit supersession check

## Stop condition

Stop after:
- one archive/quarantine-prep list
- one exact mutation set
- one keep list

Do not broaden into `work/system_v3` in the same pass.
