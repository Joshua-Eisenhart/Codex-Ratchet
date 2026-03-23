# SYSTEM_BUNDLE_AND_REBOOT_PLAYBOOK__v1
Status: DRAFT / NONCANON / REPAIR TARGET
Date: 2026-03-14
Owner: current `A2` controller / `A0` save-restore tooling / `SIM` process repair

## Purpose

This spec restores the good part of the old megaboot as one current bundle-level control surface.

It exists because current `system_v3` now has:
- explicit `A2` boot law
- explicit `A1` boot law
- explicit save/tape law
- explicit `FULL+` repair spec
- explicit `A0` save/report surfaces
- explicit `SIM` campaign process
- explicit `A2` mining / Rosetta artifact packs

but still lacks one clean surface that says:
- what the current system bundle actually is
- how old thread roles map to the current architecture
- what the current reboot kit is
- what the current restore path is
- what the current live boot order is

Legacy witness surface:
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/upgrade docs/BOOTPACKS/MEGABOOT_RATCHET_SUITE_v7.4.8-PROJECTS copy.md`

Current normative anchors:
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/specs/03_B_KERNEL_SPEC.md`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/specs/16_ZIP_SAVE_AND_TAPES_SPEC.md`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/specs/27_MASTER_CONTROLLER_THREAD_PROCESS__v1.md`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/specs/28_A2_THREAD_BOOT__v1.md`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/specs/31_A1_THREAD_BOOT__v1.md`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/specs/40_PARALLEL_CODEX_THREAD_CONTROL__v1.md`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/specs/66_PARALLEL_CODEX_RUN_PLAYBOOK__v1.md`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/specs/72_SIM_CAMPAIGN_AND_SUITE_MODES__v1.md`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/specs/73_FULL_PLUS_SEMANTIC_SAVE_ZIP__v1.md`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/specs/74_A0_SAVE_REPORT_SURFACES__v1.md`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/specs/75_A2_MINING_AND_ROSETTA_ARTIFACT_PACKS__v1.md`

## Core rule

The current system bundle is not the old thread topology restored literally.

The current bundle is:
- `A2` controller/worker architecture
- `A1` proposal architecture
- `A0` deterministic tooling and save/report surfaces
- `B` kernel authority
- `SIM` runtime/evidence process

Legacy bootpacks remain high-value witness surfaces.
They do not outrank the current repo-held process spine.

## Current bundle members

### 1. `B` kernel authority

Current home:
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/specs/03_B_KERNEL_SPEC.md`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/specs/17_BOOTPACK_THREAD_B_v3.9.13_ENFORCEABLE_CONTRACT_EXTRACT_FOR_IMPLEMENTATION_v1.md`

Role:
- lower-loop kernel authority
- restore target for `THREAD_S_SAVE_SNAPSHOT v2`
- sole ratchet truth surface among the old bundle roles

### 2. `A0` deterministic tooling and save/report layer

Current home:
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/specs/04_A0_COMPILER_SPEC.md`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/specs/16_ZIP_SAVE_AND_TAPES_SPEC.md`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/specs/73_FULL_PLUS_SEMANTIC_SAVE_ZIP__v1.md`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/specs/74_A0_SAVE_REPORT_SURFACES__v1.md`

Role:
- compile deterministic artifacts
- build and audit semantic save carriers
- maintain export/campaign tape lineage
- provide restore/audit/report control surfaces

### 3. `A2` controller/workers

Current home:
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/specs/27_MASTER_CONTROLLER_THREAD_PROCESS__v1.md`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/specs/28_A2_THREAD_BOOT__v1.md`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/specs/40_PARALLEL_CODEX_THREAD_CONTROL__v1.md`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/specs/66_PARALLEL_CODEX_RUN_PLAYBOOK__v1.md`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/specs/71_A2_CONTROLLER_LAUNCH_PACKET__v1.md`

Role:
- current upper-loop control
- understanding refresh
- routing
- mining
- queue/readiness decisions
- bounded repair/audit/build passes

### 4. `A1` proposal workers

Current home:
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/specs/30_A2_TO_A1_HANDOFF_CONTRACT__v1.md`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/specs/31_A1_THREAD_BOOT__v1.md`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/specs/32_A1_QUEUE_STATUS_SURFACE__v1.md`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/specs/34_A1_READY_PACKET__v1.md`

Role:
- proposal-only branch generation
- rosetta stripping / packaging / proposal family work
- never direct canon authority

### 5. `SIM` process layer

Current home:
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/specs/06_SIM_EVIDENCE_AND_TIERS_SPEC.md`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/specs/72_SIM_CAMPAIGN_AND_SUITE_MODES__v1.md`

Role:
- staged evidence campaigns
- failure isolation
- graveyard rescue pressure
- replay/proof/regression support

### 6. Optional `M`-style mining/Rosetta lane

Current home:
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/specs/15_ROSETTA_AND_MINING_ARTIFACTS.md`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/specs/75_A2_MINING_AND_ROSETTA_ARTIFACT_PACKS__v1.md`

Role:
- noncanon mining / rosetta / overlay continuity
- explicit artifact packs:
  - `FUEL_DIGEST`
  - `ROSETTA_MAP`
  - `OVERLAY_SAVE_DOC`
  - `EXPORT_CANDIDATE_PACK`

This is optional support structure, not a required live thread role.

## Legacy-to-current role map

Old witness role -> current mapped role:

- `THREAD_B`
  - maps to current `B` kernel authority and restore target

- `THREAD_S`
  - maps to current `A0` save/report/tape tooling
  - not a current live chat-thread identity

- `THREAD_SIM`
  - maps to current `SIM` runtime + evidence wrapper/tooling
  - not a separate canon layer

- `THREAD_M`
  - maps to current optional `A2` mining / Rosetta artifact lane
  - remains noncanon

- `THREAD_A`
  - maps partially to current controller/operator discipline
  - does not override the current `A2_CONTROLLER` architecture

## Hard rules

1. `BUNDLE_CONTROL_NOT_KERNEL_AUTHORITY`
- this playbook coordinates the bundle
- it does not override `B` kernel authority

2. `NO_LITERAL_THREAD_TOPOLOGY_RESTORE`
- do not restore `THREAD_A`, `THREAD_S`, `THREAD_M`, or `THREAD_SIM` as mandatory current runtime topology

3. `A2_A1_REMAIN_PRIMARY`
- the newer `A2` and `A1` architecture remains the primary upper-loop design

4. `SAVE_RESTORE_IS_A0_OWNED`
- semantic save building, auditing, and restore sufficiency are owned by current `A0` tooling surfaces

5. `M_OPTIONAL_NOT_AUTHORITY`
- mining/Rosetta overlays may help recovery and proposal shaping
- they never justify canon by themselves

6. `B_RESTORE_STILL_USES_SNAPSHOT`
- canonical restore remains snapshot-based at the kernel boundary
- the required restore witness is still `THREAD_S_SAVE_SNAPSHOT v2`

7. `NO_CANON_FROM_MEGABOOT_LABELS`
- old bundle files may call themselves canon
- current repo-held process spine outranks those labels

## Current reboot kit

The current recommended reboot kit is:

1. this bundle/reboot playbook
2. one current semantic save surface:
   - `PROJECT_SAVE_DOC v1`
   - or semantic `FULL+` ZIP
   - or semantic `FULL++` ZIP
3. current restore/audit tools
4. current `B` kernel restore boundary

Minimum useful reboot surfaces:
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/specs/76_SYSTEM_BUNDLE_AND_REBOOT_PLAYBOOK__v1.md`
- one `PROJECT_SAVE_DOC v1` or semantic `FULL+`
- current `B` kernel spec spine

## Current restore path

### Path A: restore from `PROJECT_SAVE_DOC v1`

1. audit the project save:
   - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/tools/audit_project_save_doc.py`
2. confirm `restore_sufficiency.status = PASS`
3. recover or extract the embedded restore witness:
   - `THREAD_S_SAVE_SNAPSHOT v2`
4. pass that snapshot to the `B` restore boundary
5. verify current `B` state/report surfaces
6. continue with current `A2` controller boot

### Path B: restore from semantic `FULL+`

1. audit the ZIP:
   - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/tools/audit_full_plus_save_zip.py`
2. extract:
   - `THREAD_S_SAVE_SNAPSHOT_v2.txt`
   - companion restore members if needed for audit/report regeneration
3. pass the snapshot to the `B` restore boundary
4. use companion `A0` report tools to reconstruct or verify save state

### Path C: restore from semantic `FULL++`

1. treat `FULL++` as:
   - `FULL+`
   - plus tapes
   - plus optional overlays
2. restore `B` from the embedded snapshot exactly as in `FULL+`
3. use:
   - `CAMPAIGN_TAPE`
   - `EXPORT_TAPE`
   - optional overlay artifacts
   only for replay, audit, migration, and upper-loop continuity

## Current live boot order

The current live boot order is not the old `A -> S -> B -> SIM` paste order.

The current live order is:

1. verify `B` restore/state boundary if a restore is needed
2. bring current `A0` save/report tools online if audit or recovery is needed
3. boot the single `A2_CONTROLLER`
4. optionally launch one or two bounded `A2_WORKER` lanes
5. launch `A1_WORKER` only from valid queue-ready status
6. run `SIM` campaigns as explicit evidence work, not as ambient background identity

Default safe live layout:
- `A2_CONTROLLER`
- `0..2` bounded `A2_WORKER`
- `0..1` bounded `A1_WORKER`
- `A0` and `SIM` as tooling/runtime surfaces, not freeform replacement controllers

## Save levels in the current bundle

### `MIN`
- fast rebootable checkpoint
- enough to restore a bounded current state pointer or snapshot path
- not enough for the full old semantic rebuild

### `FULL+`
- semantic restore carrier
- enough to restore `B` canon-facing state and continue

### `FULL++`
- `FULL+`
- plus tapes and optional overlays
- best for replay, migration, sim recovery, and mining continuity

## Current loop picture

The old loop picture survives, but in translated form:

- old `S <-> B`
  - now:
    - `A0` save/report/tape tooling <-> `B` restore/state boundary

- old `A <-> SIM`
  - now:
    - `A2` controller/runtime orchestration <-> explicit staged `SIM` campaigns

- old optional `M`
  - now:
    - optional `A2` mining / Rosetta artifact lane

This translation should be preserved explicitly.
It is one of the main bundle-level truths that drifted.

## Required operator-visible outputs

Any bundle-level reboot or restart procedure should be able to state:
- restore source used
- save level used
- whether audit passed
- whether snapshot extraction succeeded
- whether `B` restore succeeded
- whether current controller boot succeeded
- whether tapes/overlays were used for replay only or for active upper-loop continuity

## Acceptance criteria

This spec is satisfied only when:
- the current bundle has one explicit orchestration/reboot playbook
- old `A/S/B/SIM/M` roles are mapped forward without literal topology restoration
- current restore path is explicit and tool-backed
- `A2`/`A1` remain the center while older bundle strengths are preserved
