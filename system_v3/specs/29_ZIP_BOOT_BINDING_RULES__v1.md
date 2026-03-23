# ZIP_BOOT_BINDING_RULES__v1
Status: DRAFT / NONCANON / ACTIVE PROCEDURE SURFACE
Date: 2026-03-11
Owner: Codex thread boots and ZIP subagent carriers

## Purpose

This note defines how boots bind to thread-carried and ZIP-carried work.

Rule:
- every thread-class and ZIP-subagent lane must have an explicit boot binding
- no worker lane should rely on operator memory alone

## Binding classes

### 1. Codex controller thread

Example:
- this current thread

Required boot:
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/specs/28_A2_THREAD_BOOT__v1.md`

Binding rule:
- the thread must load its boot from repo-held surfaces before bounded work starts

### 2. Codex `A1` thread

Required boot:
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/specs/31_A1_THREAD_BOOT__v1.md`
- precursor surface:
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/specs/26_BOOTPACK_A1_WIGGLE__v1.md`

Binding rule:
- `A1` runs only from explicit bounded fuel and its own boot
- `A1` must not inherit `A2` role by conversational drift

### 3. ZIP subagent bundle

Required boot:
- the ZIP must carry either:
  - a boot file directly
  - or a manifest pointer to the exact repo-held boot surface

Minimum acceptable boot-binding locations inside ZIP/dropin surfaces:
- `00_RUN_ME_FIRST__...`
- `meta/README.md`
- `meta/ZIP_JOB_MANIFEST_v1.json`

Binding rule:
- a ZIP job is not fully boot-bound unless it states:
  - what role it is
  - what boot surface governs it
  - what it may and may not do

## Hard rules

1. `NO_UNBOOTED_THREADS`
- if a thread’s operating role is nontrivial, it must have an explicit boot surface

2. `NO_DESKTOP_PROCEDURE_NOTES`
- Desktop is for issued artifacts like zips, not operating-law notes
- procedure instructions must be self-contained in chat or repo-held system surfaces

3. `BOOT_ROLE_MATCH`
- `A2` work loads an `A2` boot
- `A1` work loads an `A1` boot
- a ZIP worker binds to the boot matching its declared role

4. `BOOT_OVERRIDES_AD_HOC_PROMPTING`
- prompts may specify the immediate bounded task
- boots define the governing rules for how that task is allowed to run

5. `CORRECTED_ARTIFACT_REISSUE`
- if a ZIP or boot-carrier artifact is corrected, issue a fresh filename
- do not silently tell the operator to reuse an older handoff artifact

## Minimum boot declaration fields for future ZIP jobs

Every future ZIP job should expose:
- `ROLE`
- `BOOT_SURFACE`
- `ALLOWED_ACTIONS`
- `BLOCKED_ACTIONS`
- `REQUIRED_OUTPUTS`
- `STOP_RULE`

These can be carried in:
- run-me file
- manifest
- README
- or multiple redundant locations if needed

## Immediate implication

Current system gap closed by this note:
- `A2` controller threads now have an explicit repo-held active boot surface

Still pending:
- optional small queue-status surface or packet schema if later needed

Until then:
- `A1` remains governed by the current `A1_THREAD_BOOT` plus predecessor boot surfaces where relevant
