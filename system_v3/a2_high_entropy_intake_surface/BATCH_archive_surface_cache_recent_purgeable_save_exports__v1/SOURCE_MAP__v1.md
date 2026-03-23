# SOURCE_MAP__v1
Status: PROPOSED / NONCANONICAL / BOUNDED INTAKE ARTIFACT
Batch: `BATCH_archive_surface_cache_recent_purgeable_save_exports__v1`
Extraction mode: `ARCHIVE_CACHE_SAVE_EXPORT_PASS`
Batch scope: next archive-root cache-tier family after the packaged BATCH_01_OF_10 through BATCH_10_OF_10 sequence
Date: 2026-03-09

## 1) Batch Selection
- selected sources:
  - `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/CACHE__HIGH_ENTROPY__RECENT__PURGEABLE/SAFE_TO_DELETE_NOW__20260224_071639Z.txt`
  - `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/CACHE__HIGH_ENTROPY__RECENT__PURGEABLE/save_exports__20260224_070730Z/SYSTEM_SAVE__bootstrap__20260224_065046Z.zip`
  - `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/CACHE__HIGH_ENTROPY__RECENT__PURGEABLE/save_exports__20260224_070730Z/SYSTEM_SAVE__bootstrap__20260224_065046Z.zip.sha256`
  - `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/CACHE__HIGH_ENTROPY__RECENT__PURGEABLE/save_exports__20260224_070730Z/SYSTEM_SAVE__bootstrap__smoke.zip`
  - `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/CACHE__HIGH_ENTROPY__RECENT__PURGEABLE/save_exports__20260224_070730Z/SYSTEM_SAVE__bootstrap__smoke.zip.sha256`
  - `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/CACHE__HIGH_ENTROPY__RECENT__PURGEABLE/save_exports__20260224_070730Z/SYSTEM_SAVE__debug__RUN_PHASE1_AUTORATCHET_0001__20260224_065121Z.zip`
  - `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/CACHE__HIGH_ENTROPY__RECENT__PURGEABLE/save_exports__20260224_070730Z/SYSTEM_SAVE__debug__RUN_PHASE1_AUTORATCHET_0001__20260224_065121Z.zip.sha256`
  - `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/CACHE__HIGH_ENTROPY__RECENT__PURGEABLE/save_exports__20260224_070730Z/SYSTEM_SAVE__debug__RUN_PHASE1_AUTORATCHET_0001__20260224_070148Z.zip`
  - `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/CACHE__HIGH_ENTROPY__RECENT__PURGEABLE/save_exports__20260224_070730Z/SYSTEM_SAVE__debug__RUN_PHASE1_AUTORATCHET_0001__20260224_070148Z.zip.sha256`
  - `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/CACHE__HIGH_ENTROPY__RECENT__PURGEABLE/save_exports__20260224_070730Z/SYSTEM_SAVE__debug__RUN_PHASE1_AUTORATCHET_0001__smoke.zip`
  - `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/CACHE__HIGH_ENTROPY__RECENT__PURGEABLE/save_exports__20260224_070730Z/SYSTEM_SAVE__debug__RUN_PHASE1_AUTORATCHET_0001__smoke.zip.sha256`
- reason for bounded family batch:
  - this is the next unread archive-root family in folder order after the packaged batch sequence
  - it is explicitly marked purgeable cache, so it should be preserved as export-lineage and retention-policy evidence rather than mined for doctrine
  - keeping it isolated avoids flattening recent save exports into deeper milestone archives or legacy reference families
- deferred next bounded batch in folder order:
  - `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY`

## 2) Source Membership
### Source 1
- path: `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/CACHE__HIGH_ENTROPY__RECENT__PURGEABLE/SAFE_TO_DELETE_NOW__20260224_071639Z.txt`
- size bytes: `1127`
- line count: `14`
- source class: cache-tier delete-allow list

### Source 2
- path: `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/CACHE__HIGH_ENTROPY__RECENT__PURGEABLE/save_exports__20260224_070730Z/SYSTEM_SAVE__bootstrap__20260224_065046Z.zip`
- sha256: `335a3cb4d3cc24acd71d914929bd6eac34e4578df5f2f7dcf78141e0f78f3b31`
- size bytes: `2462921`
- container member count: `580`
- embedded manifest file count: `579`
- embedded profile: `bootstrap`
- embedded include_run_ids: `[]`
- source class: cache-tier bootstrap save export

### Source 3
- path: `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/CACHE__HIGH_ENTROPY__RECENT__PURGEABLE/save_exports__20260224_070730Z/SYSTEM_SAVE__bootstrap__20260224_065046Z.zip.sha256`
- size bytes: `65`
- line count: `1`
- source class: detached checksum sidecar

### Source 4
- path: `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/CACHE__HIGH_ENTROPY__RECENT__PURGEABLE/save_exports__20260224_070730Z/SYSTEM_SAVE__bootstrap__smoke.zip`
- sha256: `419225fae1dc9fd8b27f5ca1c1f2e22ad5a7acffc667fc01ad47c29d398f174e`
- size bytes: `2462624`
- container member count: `580`
- embedded manifest file count: `579`
- embedded profile: `bootstrap`
- embedded include_run_ids: `[]`
- source class: cache-tier bootstrap smoke save export

### Source 5
- path: `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/CACHE__HIGH_ENTROPY__RECENT__PURGEABLE/save_exports__20260224_070730Z/SYSTEM_SAVE__bootstrap__smoke.zip.sha256`
- size bytes: `65`
- line count: `1`
- source class: detached checksum sidecar

### Source 6
- path: `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/CACHE__HIGH_ENTROPY__RECENT__PURGEABLE/save_exports__20260224_070730Z/SYSTEM_SAVE__debug__RUN_PHASE1_AUTORATCHET_0001__20260224_065121Z.zip`
- sha256: `085912605838729b0d085b7c904a3d72ccabc9dc1273999da51ef2a5a385d0aa`
- size bytes: `2496318`
- container member count: `605`
- embedded manifest file count: `604`
- embedded profile: `debug`
- embedded include_run_ids: `["RUN_PHASE1_AUTORATCHET_0001"]`
- source class: cache-tier debug save export

### Source 7
- path: `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/CACHE__HIGH_ENTROPY__RECENT__PURGEABLE/save_exports__20260224_070730Z/SYSTEM_SAVE__debug__RUN_PHASE1_AUTORATCHET_0001__20260224_065121Z.zip.sha256`
- size bytes: `65`
- line count: `1`
- source class: detached checksum sidecar

### Source 8
- path: `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/CACHE__HIGH_ENTROPY__RECENT__PURGEABLE/save_exports__20260224_070730Z/SYSTEM_SAVE__debug__RUN_PHASE1_AUTORATCHET_0001__20260224_070148Z.zip`
- sha256: `e99bd03e6cfac2e9d71a52955a86e23fa5a8b7a9ff7e7153fded2eb0a1ea2b27`
- size bytes: `2496718`
- container member count: `605`
- embedded manifest file count: `604`
- embedded profile: `debug`
- embedded include_run_ids: `["RUN_PHASE1_AUTORATCHET_0001"]`
- source class: cache-tier later debug save export

### Source 9
- path: `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/CACHE__HIGH_ENTROPY__RECENT__PURGEABLE/save_exports__20260224_070730Z/SYSTEM_SAVE__debug__RUN_PHASE1_AUTORATCHET_0001__20260224_070148Z.zip.sha256`
- size bytes: `65`
- line count: `1`
- source class: detached checksum sidecar

### Source 10
- path: `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/CACHE__HIGH_ENTROPY__RECENT__PURGEABLE/save_exports__20260224_070730Z/SYSTEM_SAVE__debug__RUN_PHASE1_AUTORATCHET_0001__smoke.zip`
- sha256: `f00a5a57bf1b6d2f8d7c3bc2f06032a67d91e5270044f220cf98c5e9e545fc0b`
- size bytes: `2492554`
- container member count: `602`
- embedded manifest file count: `601`
- embedded profile: `debug`
- embedded include_run_ids: `["RUN_PHASE1_AUTORATCHET_0001"]`
- source class: cache-tier debug smoke save export

### Source 11
- path: `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/CACHE__HIGH_ENTROPY__RECENT__PURGEABLE/save_exports__20260224_070730Z/SYSTEM_SAVE__debug__RUN_PHASE1_AUTORATCHET_0001__smoke.zip.sha256`
- size bytes: `65`
- line count: `1`
- source class: detached checksum sidecar

## 3) Structural Map Of The Sources
### Segment A: purgeable cache policy layer
- source anchors:
  - source 1: whole file
- source role:
  - explicitly marks the whole family as cache-tier material that is safe to remove
- strong markers:
  - `Safe To Delete Now`
  - generated timestamp `20260224_071639Z`
  - all listed exports and their sidecars are inside `CACHE__HIGH_ENTROPY__RECENT__PURGEABLE`
  - retention value is lineage and audit, not authority

### Segment B: save-export family split
- source anchors:
  - sources 2, 4, 6, 8, 10: embedded `SYSTEM_SAVE_PROFILE_MANIFEST_v1.json`
- source role:
  - separates the family into `bootstrap` exports with no run ids and `debug` exports scoped to one autoratchet debug run identity
- strong markers:
  - `bootstrap`: `579` saved files
  - `debug`: `604` saved files in timestamped variants
  - `debug smoke`: `601` saved files
  - all exports preserve the same broad `core_docs/` and `system_v3/` save profile frame

### Segment C: detached integrity-sidecar layer
- source anchors:
  - sources 3, 5, 7, 9, 11
- source role:
  - preserves export integrity by detached one-line SHA sidecars rather than richer internal ledgers
- strong markers:
  - every zip has a sibling `.sha256`
  - sidecars match computed ZIP hashes exactly
  - integrity signaling is filename-external

### Segment D: bootstrap duplication layer
- source anchors:
  - sources 2 and 4: member-set and common-file comparison
- source role:
  - shows that the bootstrap timestamped and smoke exports are nearly identical save profiles
- strong markers:
  - both exports have the same `580` zip members and `579` saved-file manifest count
  - common-file drift is limited to `SYSTEM_SAVE_PROFILE_MANIFEST_v1.json` and `system_v3/WORKSPACE_LAYOUT_v1.md`
  - this is revision/packaging drift, not family-level content divergence

### Segment E: debug revision ladder layer
- source anchors:
  - sources 6, 8, 10: member-set and common-file comparison
- source role:
  - records a small debug export ladder across two timestamped saves and one smoke save
- strong markers:
  - the two timestamped debug exports have the same `605` members and `604` saved-file manifest count
  - their common-file drift is limited to `SYSTEM_SAVE_PROFILE_MANIFEST_v1.json`, `system_v3/runs/_CURRENT_RUN.txt`, `system_v3/runs/_CURRENT_STATE/sequence_state.json`, and `system_v3/runs/_CURRENT_STATE/state.json`
  - the debug smoke export drops three extra numbered `_CURRENT_STATE` files:
    - `sequence_state 3.json`
    - `sequence_state 4.json`
    - `state 2.json`
  - debug smoke also differs in `WORKSPACE_LAYOUT_v1.md`, `_CURRENT_RUN.txt`, `sequence_state.json`, `state.json`, `build_save_profile_zip.py`, and the manifest

### Segment F: embedded content-class layer
- source anchors:
  - all five zip member listings
- source role:
  - shows what kinds of artifacts were being cached in this purgeable family
- strong markers:
  - bootpacks, low-entropy library, A2 updated memory, A2 export packs, constraint-ladder docs, Thread-S full save contents, sim docs, simpy code, and `system_v3/tools/*`
  - the family is broad save-state capture, not narrow result-only export
  - Thread-S full save bodies and sidecars are present inside these cached zips even when later archive-derived extraction packages omitted them

## 4) Source-Class Read
- best classification:
  - archive cache-tier save-export lineage family with explicit deleteability, detached integrity sidecars, and small revision drift across bootstrap/debug and smoke/timestamped variants
- useful as:
  - historical witness of what the system considered recent/high-entropy/purgeable rather than milestone-worthy
  - export-lineage evidence for bootstrap versus debug save-profile packaging
  - comparison point showing how full save exports could retain bodies and sidecars that later archive-derived packages omitted
- not best classified as:
  - current active runtime state
  - long-retention authority
  - direct doctrine layer
- possible downstream consequence:
  - later archive passes can compare this purgeable cache family against deep-archive milestone saves to recover the system's retention gradient, not to revive these exact exports as active authority
