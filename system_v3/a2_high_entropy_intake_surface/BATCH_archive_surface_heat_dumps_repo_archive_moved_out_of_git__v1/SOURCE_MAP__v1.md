# SOURCE_MAP__v1
Status: PROPOSED / NONCANONICAL / BOUNDED INTAKE ARTIFACT
Batch: `BATCH_archive_surface_heat_dumps_repo_archive_moved_out_of_git__v1`
Extraction mode: `ARCHIVE_HEAT_DUMPS_REPO_ARCHIVE_MOVED_OUT_OF_GIT_PASS`
Batch scope: archive-only intake of `HEAT_DUMPS/20260225T070252Z/repo_archive__moved_out_of_git`, bounded to its root taxonomy, archive index, representative checkpoint manifests, representative cache rotation manifests, and representative ops-log signatures only
Date: 2026-03-09

## 1) Batch Selection
- selected sources:
  - direct archive object:
    - `/home/ratchet/Desktop/Codex_Ratchet__archive/HEAT_DUMPS/20260225T070252Z/repo_archive__moved_out_of_git`
  - direct root control file:
    - `ARCHIVE_INDEX_v1.json`
  - direct child families:
    - `CACHE__HIGH_ENTROPY__RECENT__PURGEABLE`
    - `DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY`
    - `HEAT_DUMPS`
    - `OPS_LOGS`
  - representative nested anchors:
    - `DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/CHECKPOINTS/SYSTEM_V3_A1_TUNING_20260225T011355Z/checkpoint_manifest.json`
    - `CACHE__HIGH_ENTROPY__RECENT__PURGEABLE/HEAT_DUMPS/RUN_SURFACE_ROTATION__20260225T010616Z/rotation_manifest.json`
    - `CACHE__HIGH_ENTROPY__RECENT__PURGEABLE/HEAT_DUMPS/SAVE_EXPORT_ROTATION__20260225T011419Z/rotation_manifest.json`
    - `OPS_LOGS/CLEANUP_BOOKKEEPING__20260225T005927Z.json`
    - `OPS_LOGS/CLEANUP_BOOKKEEPING__20260225T051102Z.json`
- reason for bounded family batch:
  - this pass resolves the nested moved-out-of-git branch that the earlier timestamped root-split batch deferred
  - the archive value is structural: this object is already a self-contained archive mirror with its own index, checkpoint ladder, cache heat-dump carrier, and cleanup ledger
  - the branch is useful for lineage because it preserves a mirror of an older `archive/` root inside a later heat dump, along with the path and naming seams that relocation did not normalize
- deferred next bounded batch in folder order:
  - `/home/ratchet/Desktop/Codex_Ratchet__archive/HEAT_DUMPS/20260225T070252Z/repo_archive__moved_out_of_git/CACHE__HIGH_ENTROPY__RECENT__PURGEABLE`

## 2) Source Membership
### Source 1
- path: `/home/ratchet/Desktop/Codex_Ratchet__archive/HEAT_DUMPS/20260225T070252Z/repo_archive__moved_out_of_git`
- source class: nested archive mirror root
- retained top-level members:
  - `ARCHIVE_INDEX_v1.json`
  - `CACHE__HIGH_ENTROPY__RECENT__PURGEABLE`
  - `DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY`
  - `HEAT_DUMPS`
  - `OPS_LOGS`
  - `.DS_Store`
- archive meaning:
  - this branch is not loose spill; it is a compacted root mirror of an older external archive layout

### Source 2
- path: `/home/ratchet/Desktop/Codex_Ratchet__archive/HEAT_DUMPS/20260225T070252Z/repo_archive__moved_out_of_git/ARCHIVE_INDEX_v1.json`
- source class: nested archive root index
- retained markers:
  - `schema: ARCHIVE_INDEX_v1`
  - latest checkpoint:
    - `archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/CHECKPOINTS/SYSTEM_V3_A1_TUNING_20260225T011355Z`
  - recent heat dump count:
    - `10`
  - every recent heat-dump reference points under:
    - `archive/CACHE__HIGH_ENTROPY__RECENT__PURGEABLE/HEAT_DUMPS/`
- archive meaning:
  - the mirror preserves its own re-entry map and treats cache-hosted heat dumps, not the direct `HEAT_DUMPS` child, as active recent history

### Source 3
- path: `/home/ratchet/Desktop/Codex_Ratchet__archive/HEAT_DUMPS/20260225T070252Z/repo_archive__moved_out_of_git/CACHE__HIGH_ENTROPY__RECENT__PURGEABLE`
- source class: nested cache archive carrier
- retained markers:
  - total subtree size:
    - `25172` files
    - `1154` directories
  - immediate children:
    - `.DS_Store`
    - `HEAT_DUMPS`
  - representative heat-dump families under nested cache:
    - `RUN_SURFACE_ROTATION_A1_WORKING__20260225T005137Z`
    - `RUN_SURFACE_ROTATION_REAL_LOOP_HISTORY__20260225T005437Z`
    - `RUN_SURFACE_ROTATION__20260225T004921Z`
    - `RUN_SURFACE_ROTATION__20260225T005815Z`
    - `RUN_SURFACE_ROTATION__20260225T010616Z`
    - `RUN_SURFACE_ROTATION__20260225T011409Z`
    - `RUN_SURFACE_ROTATION__20260225T050420Z`
    - `SAVE_EXPORT_ROTATION__20260225T005827Z`
    - `SAVE_EXPORT_ROTATION__20260225T010624Z`
    - `SAVE_EXPORT_ROTATION__20260225T010817Z`
    - `SAVE_EXPORT_ROTATION__20260225T011419Z`
    - `SAVE_EXPORT_ROTATION__20260225T012831Z`
    - `SAVE_EXPORT_ROTATION__20260225T051154Z`
- archive meaning:
  - the nested cache root acts almost entirely as a heat-dump carrier rather than as a generic cache surface

### Source 4
- path: `/home/ratchet/Desktop/Codex_Ratchet__archive/HEAT_DUMPS/20260225T070252Z/repo_archive__moved_out_of_git/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY`
- source class: nested milestone deep archive
- retained markers:
  - total subtree size:
    - `30` files
    - `8` directories
  - immediate child:
    - `CHECKPOINTS`
  - retained checkpoints:
    - `SYSTEM_V3_A1_TUNING_20260225T004854Z`
    - `SYSTEM_V3_A1_TUNING_20260225T005429Z`
    - `SYSTEM_V3_A1_TUNING_20260225T005847Z`
    - `SYSTEM_V3_A1_TUNING_20260225T010608Z`
    - `SYSTEM_V3_A1_TUNING_20260225T011355Z`
  - latest checkpoint manifest anchor:
    - notes `Added orthogonality relation probes/terms and validated full loop pass.`
    - run id `RUN_REAL_LOOP_DEEP_0023`
    - source save exports still referenced as live-era paths under `system_v3/runs/_save_exports`
- archive meaning:
  - the deep archive preserves a five-step low-entropy checkpoint ladder, not a broad archive tree

### Source 5
- path: `/home/ratchet/Desktop/Codex_Ratchet__archive/HEAT_DUMPS/20260225T070252Z/repo_archive__moved_out_of_git/HEAT_DUMPS`
- source class: empty direct heat-dumps child
- retained markers:
  - `0` files
  - `0` directories
- archive meaning:
  - the direct child exists as a shell only; actual recent heat history was redirected into the nested cache subtree

### Source 6
- path: `/home/ratchet/Desktop/Codex_Ratchet__archive/HEAT_DUMPS/20260225T070252Z/repo_archive__moved_out_of_git/OPS_LOGS`
- source class: nested cleanup/janitor ledger
- retained markers:
  - `7` bookkeeping JSON files
  - timestamp range:
    - earliest `20260225T005927Z`
    - latest `20260225T051102Z`
  - representative schema:
    - `SYSTEM_STORAGE_JANITOR_RESULT_v1`
  - log bodies still reference live-era absolute paths rooted at:
    - `/home/ratchet/Desktop/Codex Ratchet/archive/...`
    - `/home/ratchet/Desktop/Codex Ratchet/system_v3/...`
- archive meaning:
  - the mirror carries later cleanup history than its checkpoint ladder and preserves path references from before this mirror was moved into the heat dump

## 3) Representative Evidence Anchors
- archive-index anchor:
  - `ARCHIVE_INDEX_v1.json` names the latest deep checkpoint but sends all recent-heat attention into nested cache rotations
- run-rotation anchor:
  - `RUN_SURFACE_ROTATION__20260225T010616Z/rotation_manifest.json` says source was `/home/ratchet/Desktop/Codex Ratchet/system_v3/runs`, destination was `/home/ratchet/Desktop/Codex Ratchet/archive/...`, and moved eight retained run/test surfaces including `TEST_A1_PACKET_ZIP`, `TEST_DET_A`, and `TEST_STATE_TRANSITION_MUTATION`
- save-export anchor:
  - `SAVE_EXPORT_ROTATION__20260225T011419Z/rotation_manifest.json` keeps one bootstrap/debug pair while moving the older `RUN_REAL_LOOP_DEEP_0022` save pair into the nested archive destination
- checkpoint anchor:
  - `SYSTEM_V3_A1_TUNING_20260225T011355Z/checkpoint_manifest.json` binds the latest low-entropy milestone to `RUN_REAL_LOOP_DEEP_0023`
- path-seam anchor:
  - early checkpoint note `bootstrap_build.log` under `SYSTEM_V3_A1_TUNING_20260225T004854Z` still outputs to `/home/ratchet/Desktop/Codex Ratchet/archive/CHECKPOINTS/...`
  - later checkpoint note `bootstrap_build.log` under `SYSTEM_V3_A1_TUNING_20260225T005429Z` outputs to `/home/ratchet/Desktop/Codex Ratchet/archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY/CHECKPOINTS/...`
- janitor anchor:
  - `CLEANUP_BOOKKEEPING__20260225T051102Z.json` postdates the latest checkpoint and still plans/deletes `.DS_Store` and `__pycache__` under the old live `archive/` and `system_v3/` tree

## 4) Archive Handling Decision
- treat this branch as:
  - retention/history/heat-dump nested archive mirror
  - useful for archive-layout lineage, checkpoint/save-rotation ancestry, and cleanup-path drift
  - not active runtime input or current authority
- do not infer:
  - that the live-era absolute paths are still valid authorities
  - that the empty direct `HEAT_DUMPS` child means heat history was absent
  - that the checkpoint ladder captures all later archive maintenance, because ops logs continue after the latest checkpoint timestamp
