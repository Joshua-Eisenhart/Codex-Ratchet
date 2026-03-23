# WORK_SYSTEM_V3_AND_TO_SEND_TO_PRO_AUDIT__2026_03_10__v1

Status: DRAFT / NONCANON / A2 AUDIT OUTPUT
Date: 2026-03-10
Role: bounded audit of `work/system_v3` and `work/to_send_to_pro` to separate active send/control surfaces from stale staging residue

## 1) `work/system_v3` classification

Current size:
- `136M` total

Dominant contents:
- `117M` `work/system_v3/runs`
- `11M` `work/system_v3/runtime`
- then mirrored alias/owner-like surfaces:
  - `deterministic_runtime_execution_surface`
  - `a2_state`
  - `a2_persistent_context_and_memory_surface`
  - `tools`
  - `a2_derived_indices_noncanonical`
  - `control_plane_bundle_work`
  - `specs`

Run concentration inside `work/system_v3/runs`:
- `93M` `WIGGLE_AUTO_001`
- `12M` `TEST_REFINED_050`
- `6.2M` `TEST_REFINED_001`
- `4.4M` `_CURRENT_STATE`

Audit read:
- `work/system_v3` is not an active owner path
- it is a mirrored legacy/test/prototype system fragment
- its main size burden is an embedded old run subtree, not active live control surfaces

Classification:
- overall: `quarantine`
- strongest next subtarget inside it: `work/system_v3/runs`

## 2) `work/to_send_to_pro` classification

Current size:
- `117M` total

Largest contents:
- `29M` `STAGE3_FULLBOOT__v1_2`
- `20M` `PRO_CONTEXT_PACK__BRANCH_DUAL_DOC_EXTRACTION__v1`
- `15M` `tmp__PRO_THREAD_UPDATE_PACK__v1`
- `8.7M` `jobs`
- `7.7M` `tmp__STAGE_V1_OUTPUTS__v1`
- `5.3M` `PRO_CONTEXT_PACK__BRANCH_DUAL_DOC_EXTRACTION__LIGHT__v1`

Active-vs-stale split:

### Clearly active / still useful
- `work/to_send_to_pro/jobs`
  - but only with bounded selection inside it
- current smaller update/context packs still tied to live workflows

### Mixed or likely stale staging residue
- `STAGE3_FULLBOOT__v1_2`
- `PRO_CONTEXT_PACK__BRANCH_DUAL_DOC_EXTRACTION__v1`
- `PRO_CONTEXT_PACK__BRANCH_DUAL_DOC_EXTRACTION__LIGHT__v1`
- `tmp__PRO_THREAD_UPDATE_PACK__v1`
- `tmp__STAGE_V1_OUTPUTS__v1`
- `tmp__PRO_THREAD_DELTA__v1`
- `tmp__PRO_THREAD_DELTA__v2`

## 3) `jobs` sub-audit

Inside `work/to_send_to_pro/jobs`:
- keep:
  - `PRO_BOOT_JOB__...__20260309_204341Z.zip`
  - `PRO_BOOT_JOB__...__20260309_204341Z.zip.sha256`
- stale / superseded:
  - `PRO_BOOT_JOB__...__20260309_204020Z.zip`
  - `PRO_BOOT_JOB__...__20260309_204020Z.zip.sha256`

Audit read:
- `jobs/` is active as a class
- but contains a clear stale oversized artifact pair that should be archived/quarantined before broader send-surface cleanup

## 4) Bounded decisions

### Keep
- `work/to_send_to_pro/jobs` as an active class
- the narrow `204341Z` external boot artifact pair
- `work/zip_subagents`
- `work/zip_job_templates`
- `work/zip_dropins`

### Quarantine
- `work/system_v3`

### Archive-or-quarantine candidates
- `work/to_send_to_pro/STAGE3_FULLBOOT__v1_2`
- `work/to_send_to_pro/PRO_CONTEXT_PACK__BRANCH_DUAL_DOC_EXTRACTION__v1`
- `work/to_send_to_pro/PRO_CONTEXT_PACK__BRANCH_DUAL_DOC_EXTRACTION__LIGHT__v1`
- `work/to_send_to_pro/tmp__PRO_THREAD_UPDATE_PACK__v1`
- `work/to_send_to_pro/tmp__STAGE_V1_OUTPUTS__v1`
- stale oversized `204020Z` boot artifact pair in `jobs/`

## 5) Strongest next follow-on

The strongest bounded next maintenance lane is:
- one archive/quarantine-prep pass for stale send/staging residue under `work/to_send_to_pro`

Subtargets, in order:
1. stale oversized `204020Z` boot artifact pair
2. `tmp__PRO_THREAD_UPDATE_PACK__v1`
3. `tmp__STAGE_V1_OUTPUTS__v1`
4. one older large context-pack family if clearly superseded

Separate later lane:
- quarantine-prep investigation for `work/system_v3`

## 6) Hard caution

Do not delete directly from this audit.

Next mutation must be:
- bounded
- archive/quarantine-first
- lineage-checked
