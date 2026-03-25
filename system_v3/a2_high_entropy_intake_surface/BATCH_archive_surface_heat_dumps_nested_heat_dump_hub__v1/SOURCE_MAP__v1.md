# SOURCE_MAP__v1
Status: PROPOSED / NONCANONICAL / BOUNDED INTAKE ARTIFACT
Batch: `BATCH_archive_surface_heat_dumps_nested_heat_dump_hub__v1`
Extraction mode: `ARCHIVE_HEAT_DUMPS_NESTED_HEAT_DUMP_HUB_PASS`
Batch scope: archive-only intake of `HEAT_DUMPS/20260225T070252Z/repo_archive__moved_out_of_git/CACHE__HIGH_ENTROPY__RECENT__PURGEABLE/HEAT_DUMPS`, bounded to child-family taxonomy, representative rotation manifests, and representative late payload-only residue only
Date: 2026-03-09

## 1) Batch Selection
- selected sources:
  - direct archive object:
    - `/home/ratchet/Desktop/Codex_Ratchet__archive/HEAT_DUMPS/20260225T070252Z/repo_archive__moved_out_of_git/CACHE__HIGH_ENTROPY__RECENT__PURGEABLE/HEAT_DUMPS`
  - representative run-rotation manifests:
    - `RUN_SURFACE_ROTATION__20260225T004921Z/rotation_manifest.json`
    - `RUN_SURFACE_ROTATION_A1_WORKING__20260225T005137Z/rotation_manifest.json`
    - `RUN_SURFACE_ROTATION_REAL_LOOP_HISTORY__20260225T005437Z/rotation_manifest.json`
    - `RUN_SURFACE_ROTATION__20260225T005815Z/rotation_manifest.json`
    - `RUN_SURFACE_ROTATION__20260225T010616Z/rotation_manifest.json`
    - `RUN_SURFACE_ROTATION__20260225T011409Z/rotation_manifest.json`
  - representative save-export manifests:
    - `SAVE_EXPORT_ROTATION__20260225T005827Z/rotation_manifest.json`
    - `SAVE_EXPORT_ROTATION__20260225T010624Z/rotation_manifest.json`
    - `SAVE_EXPORT_ROTATION__20260225T010817Z/rotation_manifest.json`
    - `SAVE_EXPORT_ROTATION__20260225T011419Z/rotation_manifest.json`
  - representative payload-only residue anchors:
    - `RUN_SURFACE_ROTATION__20260225T050420Z/RUN_REAL_LOOP_DEEP_0025/RUN_MANIFEST_v1.json`
    - root file inventories for `SAVE_EXPORT_ROTATION__20260225T012831Z`
    - root file inventories for `SAVE_EXPORT_ROTATION__20260225T051154Z`
- reason for bounded family batch:
  - this pass resolves the nested `HEAT_DUMPS` hub that the cache-root batch deferred
  - the archive value is structural: this subtree is the actual carrier for recent run/save demotion waves inside the nested mirror
  - the subtree is useful for lineage because it preserves a short-lived sequence of demotion/rotation conventions across path style, family width, and packaging completeness
- deferred next bounded batch in folder order:
  - `/home/ratchet/Desktop/Codex_Ratchet__archive/HEAT_DUMPS/20260225T070252Z/repo_archive__moved_out_of_git/CACHE__HIGH_ENTROPY__RECENT__PURGEABLE/HEAT_DUMPS/RUN_SURFACE_ROTATION_A1_WORKING__20260225T005137Z`

## 2) Source Membership
### Source 1
- path: `/home/ratchet/Desktop/Codex_Ratchet__archive/HEAT_DUMPS/20260225T070252Z/repo_archive__moved_out_of_git/CACHE__HIGH_ENTROPY__RECENT__PURGEABLE/HEAT_DUMPS`
- source class: nested heat-dump rotation hub
- retained markers:
  - subtree size:
    - `25171` files
    - `1153` directories
  - child family count:
    - `13`
  - child family kinds:
    - `RUN_SURFACE_ROTATION_A1_WORKING`: `1`
    - `RUN_SURFACE_ROTATION_REAL_LOOP_HISTORY`: `1`
    - `RUN_SURFACE_ROTATION`: `5`
    - `SAVE_EXPORT_ROTATION`: `6`
  - timestamp coverage:
    - earliest `20260225T004921Z`
    - latest `20260225T051154Z`
- archive meaning:
  - this subtree is the real high-entropy carrier inside the nested cache root, not just a small side folder

### Source 2
- path: representative manifested run-rotation families
- source class: run-surface demotion waves
- retained markers:
  - early relative-path waves:
    - `RUN_SURFACE_ROTATION__20260225T004921Z` moves `17` `RUN_REAL_LOOP_DEEP_0001` through `0017`
    - `RUN_SURFACE_ROTATION_A1_WORKING__20260225T005137Z` moves `9` `RUN_A1_WORKING` runs
    - `RUN_SURFACE_ROTATION_REAL_LOOP_HISTORY__20260225T005437Z` moves `2` `RUN_REAL_LOOP_DEEP_0018` and `0019`
    - source string is `system_v3/runs`
    - destination string is `archive/...`
  - later absolute-path mixed waves:
    - `RUN_SURFACE_ROTATION__20260225T005815Z` keeps `2` real-loop runs and moves `53` mixed run/test families
    - `RUN_SURFACE_ROTATION__20260225T010616Z` keeps `2` real-loop runs and moves `8` objects
    - `RUN_SURFACE_ROTATION__20260225T011409Z` keeps `2` real-loop runs and moves the same `8`-object bundle one wave later
    - source and destination switch to absolute workspace paths
- archive meaning:
  - the run-rotation family preserves both the scale shift from broad sweep to compact repeated carry-forward and the path-format shift from relative to absolute

### Source 3
- path: representative manifested save-export families
- source class: save-export rotation waves
- retained markers:
  - stable manifested families:
    - `SAVE_EXPORT_ROTATION__20260225T005827Z`
    - `SAVE_EXPORT_ROTATION__20260225T010817Z`
    - `SAVE_EXPORT_ROTATION__20260225T011419Z`
  - manifested fields:
    - `schema: SAVE_EXPORT_ROTATION_MANIFEST_v1`
    - source is `/home/ratchet/Desktop/Codex Ratchet/system_v3/runs/_save_exports`
    - destination is `/home/ratchet/Desktop/Codex Ratchet/archive/...`
  - kept/moved progression:
    - `005827Z` keeps `4` newer files and moves `4` older files
    - `010817Z` keeps `4` newer files and moves `4` older files
    - `011419Z` keeps `4` newer files and moves `4` older files
- archive meaning:
  - the save-export family initially looks regular and fully manifested before later packaging drift appears

### Source 4
- path: `SAVE_EXPORT_ROTATION__20260225T010624Z`
- source class: manifest-only save-export shell
- retained markers:
  - folder retains only `rotation_manifest.json`
  - manifest declares:
    - `8` kept files
    - `0` moved files
- archive meaning:
  - this family preserves bookkeeping without the payload it describes

### Source 5
- path: `RUN_SURFACE_ROTATION__20260225T050420Z`
- source class: payload-only late run-rotation residue
- retained markers:
  - no retained `rotation_manifest.json`
  - root keeps `.DS_Store` and one child run `RUN_REAL_LOOP_DEEP_0025`
  - inner `RUN_MANIFEST_v1.json` survives with:
    - `run_id: RUN_REAL_LOOP_DEEP_0025`
    - `created_utc: 2026-02-25T01:36:45Z`
- archive meaning:
  - the outer rotation wrapper is missing, but a substantial run payload still survives inside

### Source 6
- path: `SAVE_EXPORT_ROTATION__20260225T012831Z` and `SAVE_EXPORT_ROTATION__20260225T051154Z`
- source class: payload-only late save-export residue
- retained markers:
  - `012831Z` retains `8` payload files:
    - two bootstrap zips plus sidecars
    - two debug `RUN_REAL_LOOP_DEEP_0023` zips plus sidecars
  - `051154Z` retains `4` payload files:
    - one bootstrap zip plus sidecar
    - one debug `RUN_REAL_LOOP_DEEP_0024` zip plus sidecar
  - neither folder retains `rotation_manifest.json`
- archive meaning:
  - late save-export residue keeps payload but loses the archival bookkeeping wrapper

## 3) Representative Evidence Anchors
- broad mixed-sweep anchor:
  - `RUN_SURFACE_ROTATION__20260225T005815Z/rotation_manifest.json` moves `53` heterogeneous run/test objects including `RUN_PHASE1_AUTORATCHET_0001`, `RUN_QIT_TOOLKIT_LAWYERS_0001`, `TEST_A1_PACKET_ZIP`, and `TEST_STATE_TRANSITION_MUTATION`
- repeated compact-bundle anchor:
  - `RUN_SURFACE_ROTATION__20260225T010616Z` and `RUN_SURFACE_ROTATION__20260225T011409Z` each preserve the same eight-object moved set with a one-step-shifted kept frontier
- manifest-only save anchor:
  - `SAVE_EXPORT_ROTATION__20260225T010624Z` records `8` kept files and `0` moved files but retains no payload alongside the manifest
- payload-only run anchor:
  - `RUN_SURFACE_ROTATION__20260225T050420Z` keeps `RUN_REAL_LOOP_DEEP_0025` payload and inner run manifest but no outer rotation manifest
- payload-only save anchors:
  - `SAVE_EXPORT_ROTATION__20260225T012831Z` and `SAVE_EXPORT_ROTATION__20260225T051154Z` keep zip payloads and `.sha256` sidecars only

## 4) Archive Handling Decision
- treat this subtree as:
  - retention/history/heat-dump rotation hub
  - useful for demotion lineage, packaging drift, and archive-routing evolution
  - not active runtime input or current authority
- do not infer:
  - that a missing manifest means a rotation never occurred
  - that a retained manifest guarantees the payload is still present in this snapshot
  - that the outer family timestamp and inner payload creation time are the same event clock
