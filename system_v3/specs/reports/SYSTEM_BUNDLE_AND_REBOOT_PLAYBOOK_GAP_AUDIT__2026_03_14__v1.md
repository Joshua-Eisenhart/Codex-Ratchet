# SYSTEM_BUNDLE_AND_REBOOT_PLAYBOOK_GAP_AUDIT__2026_03_14__v1
Status: NONCANON / AUDIT
Date: 2026-03-14

## Scope

Audit current system bundle and reboot coverage against:
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/specs/76_SYSTEM_BUNDLE_AND_REBOOT_PLAYBOOK__v1.md`

Primary witness surface:
- `/home/ratchet/Desktop/Codex Ratchet/core_docs/upgrade docs/BOOTPACKS/MEGABOOT_RATCHET_SUITE_v7.4.8-PROJECTS copy.md`

Audited current surfaces:
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/specs/16_ZIP_SAVE_AND_TAPES_SPEC.md`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/specs/73_FULL_PLUS_SEMANTIC_SAVE_ZIP__v1.md`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/specs/74_A0_SAVE_REPORT_SURFACES__v1.md`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/specs/75_A2_MINING_AND_ROSETTA_ARTIFACT_PACKS__v1.md`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/specs/40_PARALLEL_CODEX_THREAD_CONTROL__v1.md`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/specs/66_PARALLEL_CODEX_RUN_PLAYBOOK__v1.md`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/build_full_plus_save_zip.py`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/audit_full_plus_save_zip.py`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/build_project_save_doc.py`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/audit_project_save_doc.py`

## Findings

### 1. The missing bundle-level orchestration surface is now repaired at the spec level

Before `76_SYSTEM_BUNDLE_AND_REBOOT_PLAYBOOK__v1.md`, current bundle behavior was split across save/tape law, boot law, launch playbooks, and mining/sim repair surfaces.

Current status:
- fixed at the spec/playbook layer

Gap closed:
- one current bundle control surface now exists
- old `A/S/B/SIM/M` roles are mapped to current `A2/A1/A0/B/SIM`

### 2. Save building and save auditing exist, but restore extraction is still manual

Current tools can:
- build semantic `FULL+`
- audit semantic `FULL+`
- build `PROJECT_SAVE_DOC`
- audit `PROJECT_SAVE_DOC`

Witness:
- [build_full_plus_save_zip.py](/home/ratchet/Desktop/Codex%20Ratchet/system_v3/tools/build_full_plus_save_zip.py#L90)
- [audit_full_plus_save_zip.py](/home/ratchet/Desktop/Codex%20Ratchet/system_v3/tools/audit_full_plus_save_zip.py#L56)
- [build_project_save_doc.py](/home/ratchet/Desktop/Codex%20Ratchet/system_v3/tools/build_project_save_doc.py#L125)
- [audit_project_save_doc.py](/home/ratchet/Desktop/Codex%20Ratchet/system_v3/tools/audit_project_save_doc.py#L14)

Remaining gap:
- there is no dedicated helper that extracts or emits the exact `THREAD_S_SAVE_SNAPSHOT v2` restore witness from an audited `PROJECT_SAVE_DOC` or semantic `FULL+`
- the restore path is documented, but not yet one bounded tool step

### 3. `B` restore boundary remains implicit in current tooling

Current specs still preserve snapshot-based `B` restore as the kernel-facing rule.

Witness:
- [03_B_KERNEL_SPEC.md](/home/ratchet/Desktop/Codex%20Ratchet/system_v3/specs/03_B_KERNEL_SPEC.md#L19)
- [audit_full_plus_save_zip.py](/home/ratchet/Desktop/Codex%20Ratchet/system_v3/tools/audit_full_plus_save_zip.py#L75)

Remaining gap:
- there is no current top-level `prepare_b_restore_from_semantic_save` or equivalent tool that turns an audited save into one explicit restore payload for the `B` boundary

### 4. Bundle discovery is improved but still late-added

Current status:
- `00_MANIFEST.md` now lists specs `72` through `76` as active process supplements

Remaining gap:
- there is still no dedicated bundle-sync or reboot-readiness audit that checks all live bundle members together

## Exact patch targets

1. Add one restore extraction helper:
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/extract_thread_s_snapshot_from_semantic_save.py`

Expected job:
- accept `--project-save-doc` and/or `--full-plus-zip`
- fail closed unless audit passes or required members are present
- emit exactly the `THREAD_S_SAVE_SNAPSHOT v2` restore witness

2. Add one top-level bundle restore preparer:
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/prepare_b_restore_from_semantic_save.py`

Expected job:
- validate semantic save
- extract snapshot
- emit one explicit restore packet or restore-ready text payload for the `B` boundary

3. Add one bundle sync/reboot audit:
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/system_bundle_reboot_audit.py`

Expected checks:
- bundle role map present
- save/audit tools present
- restore extraction path present
- current boot surfaces present
- tapes/save/mining/sim supplements discoverable

## Bounded next step

The next best bounded execution slice is:
- implement `extract_thread_s_snapshot_from_semantic_save.py`
- then implement `prepare_b_restore_from_semantic_save.py`

That closes the main remaining gap between the repaired bundle spec and an actual end-to-end reboot path.
