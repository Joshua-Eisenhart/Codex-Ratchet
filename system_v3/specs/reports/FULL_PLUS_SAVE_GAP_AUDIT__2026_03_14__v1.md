# FULL_PLUS_SAVE_GAP_AUDIT__2026_03_14__v1
Status: NONCANON / AUDIT
Date: 2026-03-14

## Scope

Audit current save ZIP behavior against:
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/specs/73_FULL_PLUS_SEMANTIC_SAVE_ZIP__v1.md`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/specs/16_ZIP_SAVE_AND_TAPES_SPEC.md`

Legacy witness:
- `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/THREAD_S_FULL_SAVE/README.md`

Audited file:
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/build_save_profile_zip.py`

## Findings

### 1. Current save ZIP builder produces a broad file export, not a semantic `FULL+` bundle

Current builder gathers files from:
- `core_docs`
- `system_v3`

with exclusion patterns, then writes a generic manifest plus all selected files into one ZIP.

Witness:
- [build_save_profile_zip.py](/home/ratchet/Desktop/Codex%20Ratchet/system_v3/tools/build_save_profile_zip.py#L85)
- [build_save_profile_zip.py](/home/ratchet/Desktop/Codex%20Ratchet/system_v3/tools/build_save_profile_zip.py#L110)
- [build_save_profile_zip.py](/home/ratchet/Desktop/Codex%20Ratchet/system_v3/tools/build_save_profile_zip.py#L156)
- [build_save_profile_zip.py](/home/ratchet/Desktop/Codex%20Ratchet/system_v3/tools/build_save_profile_zip.py#L176)

Gap:
- this is a generic profile export
- it is not the old semantic Thread B restore packet

### 2. Current save ZIP builder has no required semantic member contract for `FULL+`

Old Thread B save witness defines a concrete restore bundle with:
- snapshot
- ledger bodies
- terms
- index
- policy state
- provenance
- hashes

Witness:
- [THREAD_S_FULL_SAVE/README.md](/home/ratchet/Desktop/Codex%20Ratchet/core_docs/a1_refined_Ratchet%20Fuel/THREAD_S_FULL_SAVE/README.md#L9)

Gap:
- current builder has no concept of these as mandatory `FULL+` members

### 3. Current save ZIP builder does not distinguish semantic `FULL+` from generic archive/debug export

The builder only exposes:
- `bootstrap`
- `debug`

Witness:
- [build_save_profile_zip.py](/home/ratchet/Desktop/Codex%20Ratchet/system_v3/tools/build_save_profile_zip.py#L198)
- [build_save_profile_zip.py](/home/ratchet/Desktop/Codex%20Ratchet/system_v3/tools/build_save_profile_zip.py#L222)

Gap:
- there is no dedicated `FULL+`
- there is no dedicated `FULL++`

### 4. Current save ZIP builder has no semantic audit tool

There is no current tool validating:
- required `FULL+` member presence
- semantic restore sufficiency
- contamination by broad unrelated payloads

Witness:
- current builder writes ZIP + manifest only:
  - [build_save_profile_zip.py](/home/ratchet/Desktop/Codex%20Ratchet/system_v3/tools/build_save_profile_zip.py#L236)

Gap:
- build exists
- semantic audit does not

## Exact patch targets

1. Add `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/build_full_plus_save_zip.py`
- build the semantic Thread B restore bundle only
- require the seven semantic member surfaces

2. Add `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/audit_full_plus_save_zip.py`
- pass/fail audit of semantic `FULL+` bundle

3. Keep `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/build_save_profile_zip.py`
- but keep it explicitly generic
- do not let it imply semantic `FULL+` compliance

4. Later extend to `FULL++`
- add campaign tape and optional overlays without changing `FULL+` sufficiency
