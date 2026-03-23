# SOURCE_MAP__v1
Status: PROPOSED / NONCANONICAL / BOUNDED INTAKE ARTIFACT
Batch: `BATCH_archive_surface_heat_dumps_nested_cache_recent_purgeable__v1`
Extraction mode: `ARCHIVE_HEAT_DUMPS_NESTED_CACHE_RECENT_PURGEABLE_PASS`
Batch scope: archive-only intake of `HEAT_DUMPS/20260225T070252Z/repo_archive__moved_out_of_git/CACHE__HIGH_ENTROPY__RECENT__PURGEABLE`, bounded to its root structure, nested `HEAT_DUMPS` family inventory, representative rotation manifests, and representative late payload-only residue only
Date: 2026-03-09

## 1) Batch Selection
- selected sources:
  - direct archive object:
    - `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/HEAT_DUMPS/20260225T070252Z/repo_archive__moved_out_of_git/CACHE__HIGH_ENTROPY__RECENT__PURGEABLE`
  - direct child:
    - `HEAT_DUMPS`
  - representative manifested run-rotation anchors:
    - `HEAT_DUMPS/RUN_SURFACE_ROTATION__20260225T004921Z/rotation_manifest.json`
    - `HEAT_DUMPS/RUN_SURFACE_ROTATION__20260225T005815Z/rotation_manifest.json`
    - `HEAT_DUMPS/RUN_SURFACE_ROTATION__20260225T010616Z/rotation_manifest.json`
  - representative manifested save-export anchors:
    - `HEAT_DUMPS/SAVE_EXPORT_ROTATION__20260225T005827Z/rotation_manifest.json`
    - `HEAT_DUMPS/SAVE_EXPORT_ROTATION__20260225T010624Z/rotation_manifest.json`
    - `HEAT_DUMPS/SAVE_EXPORT_ROTATION__20260225T011419Z/rotation_manifest.json`
  - representative payload-only residue anchors:
    - `HEAT_DUMPS/RUN_SURFACE_ROTATION__20260225T050420Z/RUN_REAL_LOOP_DEEP_0025/RUN_MANIFEST_v1.json`
    - file inventory for `HEAT_DUMPS/SAVE_EXPORT_ROTATION__20260225T012831Z`
    - file inventory for `HEAT_DUMPS/SAVE_EXPORT_ROTATION__20260225T051154Z`
- reason for bounded family batch:
  - this pass resolves the nested cache root that the moved-out-of-git mirror batch deferred
  - the archive value is structural: the cache root is effectively a timestamped heat-dump carrier with multiple rotation conventions, not a generic recent cache
  - this object is useful for lineage because it preserves a transition from relative-path manifests to absolute-path manifests, then into late payload-only residue with missing manifests
- deferred next bounded batch in folder order:
  - `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/HEAT_DUMPS/20260225T070252Z/repo_archive__moved_out_of_git/CACHE__HIGH_ENTROPY__RECENT__PURGEABLE/HEAT_DUMPS`

## 2) Source Membership
### Source 1
- path: `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/HEAT_DUMPS/20260225T070252Z/repo_archive__moved_out_of_git/CACHE__HIGH_ENTROPY__RECENT__PURGEABLE`
- source class: nested cache root
- retained markers:
  - total subtree size:
    - `25172` files
    - `1154` directories
  - immediate children:
    - `.DS_Store`
    - `HEAT_DUMPS`
- archive meaning:
  - this cache root is effectively a one-child carrier for rotated heat-dump material

### Source 2
- path: `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/HEAT_DUMPS/20260225T070252Z/repo_archive__moved_out_of_git/CACHE__HIGH_ENTROPY__RECENT__PURGEABLE/HEAT_DUMPS`
- source class: nested cache heat-dump carrier
- retained markers:
  - subtree size:
    - `25171` files
    - `1153` directories
  - child family count:
    - `13`
  - family kinds:
    - `1` `RUN_SURFACE_ROTATION_A1_WORKING`
    - `1` `RUN_SURFACE_ROTATION_REAL_LOOP_HISTORY`
    - `5` generic `RUN_SURFACE_ROTATION`
    - `6` `SAVE_EXPORT_ROTATION`
  - timestamp coverage:
    - earliest `20260225T004921Z`
    - latest `20260225T051154Z`
- archive meaning:
  - nearly the entire nested cache payload is concentrated into one rotation-style heat-dump hub

### Source 3
- path: representative manifested run-rotation families under `HEAT_DUMPS`
- source class: run-surface rotation manifests
- retained markers:
  - early relative-path phase:
    - `RUN_SURFACE_ROTATION__20260225T004921Z` moves `17` `RUN_REAL_LOOP_DEEP_0001` through `0017`
    - `RUN_SURFACE_ROTATION_A1_WORKING__20260225T005137Z` moves `9` `RUN_A1_WORKING` families
    - `RUN_SURFACE_ROTATION_REAL_LOOP_HISTORY__20260225T005437Z` moves `2` `RUN_REAL_LOOP_DEEP_0018` and `0019`
    - source is `system_v3/runs`
    - destination is `archive/...`
  - later absolute-path phase:
    - `RUN_SURFACE_ROTATION__20260225T005815Z` keeps `RUN_REAL_LOOP_DEEP_0020` and `0021` but moves `53` mixed run/test families
    - `RUN_SURFACE_ROTATION__20260225T010616Z` and `011409Z` each move the same eight-object real-loop/test bundle while keeping two newer `RUN_REAL_LOOP_DEEP_*` families
    - source and destination switch to absolute workspace paths
- archive meaning:
  - run rotations preserve both archive-routing policy and path-format drift across one short time window

### Source 4
- path: representative save-export rotation families under `HEAT_DUMPS`
- source class: save-export rotation manifests
- retained markers:
  - manifested payload families:
    - `SAVE_EXPORT_ROTATION__20260225T005827Z`
    - `SAVE_EXPORT_ROTATION__20260225T010817Z`
    - `SAVE_EXPORT_ROTATION__20260225T011419Z`
  - manifest-only shell:
    - `SAVE_EXPORT_ROTATION__20260225T010624Z`
    - manifest keeps `8` files and moves `0`, but the folder retains only `rotation_manifest.json`
  - payload-only residue:
    - `SAVE_EXPORT_ROTATION__20260225T012831Z` retains `8` payload files with no manifest
    - `SAVE_EXPORT_ROTATION__20260225T051154Z` retains `4` payload files with no manifest
- archive meaning:
  - the save-export family preserves three distinct packaging states rather than one stable export pattern

### Source 5
- path: `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/HEAT_DUMPS/20260225T070252Z/repo_archive__moved_out_of_git/CACHE__HIGH_ENTROPY__RECENT__PURGEABLE/HEAT_DUMPS/RUN_SURFACE_ROTATION__20260225T050420Z`
- source class: late payload-only run-rotation residue
- retained markers:
  - no retained `rotation_manifest.json`
  - root keeps only `.DS_Store` plus one payload run family `RUN_REAL_LOOP_DEEP_0025`
  - `RUN_REAL_LOOP_DEEP_0025/RUN_MANIFEST_v1.json` survives with:
    - `created_utc: 2026-02-25T01:36:45Z`
    - `run_id: RUN_REAL_LOOP_DEEP_0025`
- archive meaning:
  - this late run-rotation family preserves real payload without its enclosing rotation manifest

## 3) Representative Evidence Anchors
- broad mixed rotation anchor:
  - `RUN_SURFACE_ROTATION__20260225T005815Z/rotation_manifest.json` keeps two real-loop families and moves `53` mixed run/test families, including `RUN_PHASE1_AUTORATCHET_0001`, `RUN_QIT_TOOLKIT_LAWYERS_0001`, `TEST_A1_PACKET_ZIP`, and `TEST_STATE_TRANSITION_MUTATION`
- repeated test-bundle anchor:
  - `RUN_SURFACE_ROTATION__20260225T010616Z/rotation_manifest.json` and `011409Z/rotation_manifest.json` each move the same eight-object test/real-loop bundle under a later kept-set boundary
- manifest-only anchor:
  - `SAVE_EXPORT_ROTATION__20260225T010624Z/rotation_manifest.json` records `8` kept artifacts and `0` moved artifacts, but the folder itself contains no zips or sidecars
- payload-only anchors:
  - `RUN_SURFACE_ROTATION__20260225T050420Z` has real run payload but no rotation manifest
  - `SAVE_EXPORT_ROTATION__20260225T012831Z` and `051154Z` retain save zips and `.sha256` sidecars but no rotation manifest

## 4) Archive Handling Decision
- treat this branch as:
  - retention/history/heat-dump nested cache carrier
  - useful for run/save rotation lineage, packaging drift, and archive routing patterns
  - not active runtime input or current authority
- do not infer:
  - that the cache root had a broader function than heat-dump carrying at this preserved boundary
  - that later payload-only families were never formally rotated, because only the manifest shell is missing
  - that manifest-only shells guarantee missing payloads were never present outside this retained snapshot
