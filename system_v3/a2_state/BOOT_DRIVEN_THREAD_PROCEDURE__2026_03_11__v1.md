# BOOT_DRIVEN_THREAD_PROCEDURE__2026_03_11__v1

Status: ACTIVE PROCEDURE / NONCANON CONTROL LAW
Date: 2026-03-11
Role: restore boot-driven operator procedure for external research threads and future thread handoffs

## 1. Source basis

This procedure is derived from:
- `/home/ratchet/Desktop/Codex Ratchet/core_docs/upgrade docs/MEGABOOT_RATCHET_SUITE_v7.4.9-PROJECTS 2.md`
- `/home/ratchet/Desktop/Codex Ratchet/core_docs/upgrade docs/BOOTPACK_THREAD_A_v2.60.md`
- `/home/ratchet/Desktop/Codex Ratchet/core_docs/upgrade docs/BOOTPACK_THREAD_B_v3.9.13.md`

The missing rules that must govern all future handoffs are:
- ZIP bundles are the primary communication carrier.
- Handoffs must be atomic and explicit.
- The operator should not have to reconstruct procedure from scattered notes.
- External/proposal work and audit/enforcement work must remain split.

## 2. Procedure correction

The broken pattern was:
- put extra operator `.md` notes on the Desktop
- tell the operator to open one note to find another note
- rely on prior conversational context to explain what each file is for

That pattern is now rejected.

## 3. Hard operator rules

### RULE P-001 DESKTOP ROLE

Desktop is for issued operator artifacts only.

Allowed Desktop handoff artifacts:
- attachment files such as issued `.zip`
- returned result `.zip` files

Desktop must not be used for:
- procedure notes
- handoff notes
- “open this file and copy from it” instructions

### RULE P-002 SELF-CONTAINED ACTIONS

Every operational instruction given to the user must be self-contained in the chat message itself.

Each instruction block must include all of:
1. how many threads
2. which model
3. exact file to attach
4. exact prompt to paste
5. stop condition
6. next step after the return

If any one of those is missing, the handoff is incomplete.

### RULE P-003 NO REFERENCE-CHAIN HANDOFF

Do not tell the operator to:
- open a `.md`
- find a prompt inside it
- return to another `.md`
- use one note as reference-only while another note holds the actual action

The action must be in one chat block.

### RULE P-004 NEW ARTIFACT ISSUANCE

If a boot artifact is corrected, issue a new artifact filename.

Do not instruct the operator to reuse:
- an older boot zip
- an older Desktop note
- an earlier handoff artifact once a corrected one exists

### RULE P-005 EXTERNAL RESEARCH SPLIT

For external research lanes:
- generation thread = web UI `Pro`
- audit thread = web UI `Thinking` with `Heavy`

Audit must be separate from generation.

### RULE P-006 ATTACHMENT PREFLIGHT

Any external booted thread that depends on an attachment must begin with an attachment-read preflight.

The first return must prove one of:
- `ATTACHMENT_ACCESS_FAIL`
- `ZIP_ACCESS_OK`

Do not allow a fail-closed content package to stand in for attachment failure.

## 4. Canonical operator flow for current external lane

### Current boot artifact

Current issued artifact:
- `/home/ratchet/Desktop/PRO_BOOT_JOB__ENTROPY_CARNOT_SZILARD__20260311_v3.zip`

### Operator action shape

The operator handoff for the current external lane must be exactly:
1. open `1` new web UI thread
2. set model to `Pro`
3. attach the current issued zip
4. paste the full self-contained launch prompt in chat
5. wait for the first return
6. if `ATTACHMENT_ACCESS_FAIL`, stop and bring back the exact failure
7. if `ZIP_ACCESS_OK`, let it continue to final package return
8. after package return, open a new web UI thread
9. set model to `Thinking`
10. set thinking time to `Heavy`
11. paste the full self-contained audit prompt in chat
12. do not ingest to A2 until the audit passes

## 5. Why the old handoff failed

The old handoff was not boot-driven enough because it violated all of:
- ZIP-first communication simplicity
- atomic operator routing
- explicit next valid action discipline

It drifted into a Thread A-style explanatory note chain without preserving the atomicity discipline that Thread A itself requires.

## 6. Current interpretation of the boot docs

### From MEGABOOT

The active system must treat ZIP carriers as primary communication and avoid classical proof-style conservative motion.

### From BOOTPACK_THREAD_A

Operator guidance must be:
- literal
- atomic
- route-first
- copy/paste ready

### From BOOTPACK_THREAD_B

Enforcement requires:
- explicit message classes
- no smoothing
- no extra prose bundled with execution payloads

These constraints should have governed the external thread procedure from the start.

## 7. Enforcement for future handoffs

Before sending any future thread instruction, check:
- does the instruction contain all 6 required elements?
- does it require opening any Desktop `.md`?
- does it reuse a superseded artifact?
- does it distinguish generation model from audit model?
- does it specify the exact stop condition?

If any answer is bad, do not send the handoff yet.

## 8. Current live correction

The Desktop procedure-note pattern is now explicitly disallowed.

The only Desktop artifact that matters for the current external lane is:
- `/home/ratchet/Desktop/PRO_BOOT_JOB__ENTROPY_CARNOT_SZILARD__20260311_v3.zip`

Everything else should be delivered in-chat as a self-contained action block.
