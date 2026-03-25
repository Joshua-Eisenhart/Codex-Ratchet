# A1_TRIGGER_QUEUE_AND_A2_DISPATCH_RULE__2026_03_11__v1

Status: ACTIVE CONTROL NOTE / NONCANON
Date: 2026-03-11
Role: define when A1 is allowed to run and how A2 should surface A1-ready work

## 1) Core rule

A1 does not free-run.

A1 runs only when:
- A2 has completed a bounded pass,
- A2 has a concrete handoff artifact set,
- and A2 marks the work as A1-ready.

This means:
- A2 and A1 should not be treated as concurrently free-running chat layers for the same work unit
- A1 is dispatch-driven by A2
- A1 proposal work begins from explicit A2 handoff, not from raw source or ambient thread memory

## 2) Current operating split

### A2
- reads
- mines
- refreshes understanding
- preserves contradictions
- identifies residue / rescue / negative pressure classes
- emits bounded handoff artifacts

### A1
- takes explicit A2 handoff artifacts only
- generates proposal-side families
- emits positive, negative, and rescue candidates
- does not claim earned truth

### Lower loop
- A0 / B / SIM remain runtime / code / contract governed
- they do not require chat-thread boots in the same way A2/A1 do

## 3) Boot rule

### A2 threads
Must run with an explicit A2 boot / A2 operator rule set.

### A1 threads
Must run with an explicit A1 boot / A1 wiggle execution contract.

### ZIP subagents
If a ZIP_JOB is being used as an A2 or A1 worker lane, the boot contract should be carried inside the bundle or explicitly bound by the bundle manifest/task contract.

## 4) A1 trigger queue

The system should maintain an A1-ready queue owned by A2.

Meaning:
- A2 keeps meta-awareness of whether there is real A1-ready work
- A1 is not started unless the queue is non-empty
- if the queue is empty, the answer to `a1?` should be `NO_WORK`

## 5) Minimal queue statuses

For each candidate A1 dispatch item, track:
- `dispatch_id`
- `status`
- `source_a2_artifacts`
- `target_a1_scope`
- `reason_to_run`

Allowed status values:
- `NO_WORK`
- `READY_FROM_NEW_A2_HANDOFF`
- `READY_FROM_EXISTING_FUEL`
- `READY_FROM_A2_PREBUILT_BATCH`
- `BLOCKED_MISSING_A2`
- `BLOCKED_MISSING_BOOT`
- `BLOCKED_MISSING_ARTIFACTS`
- `IN_PROGRESS`
- `DONE`
- `SUPERSEDED`

## 6) A2-side rule for `a1?`

When asked `a1?`, the controller should answer in one of these ways:

### Case 1: no A1-ready work
Return:
- `A1_QUEUE_STATUS: NO_WORK`
- one short reason

### Case 2: A1-ready work exists
Return:
- one exact ready status from:
  - `A1_QUEUE_STATUS: READY_FROM_NEW_A2_HANDOFF`
  - `A1_QUEUE_STATUS: READY_FROM_EXISTING_FUEL`
  - `A1_QUEUE_STATUS: READY_FROM_A2_PREBUILT_BATCH`
- one exact bounded dispatch prompt
- required A2 handoff artifacts
- required A1 boot
- stop condition

No broad explanation should be required at dispatch time.

Current response surface:
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/specs/32_A1_QUEUE_STATUS_SURFACE__v1.md`

## 7) Current A1 boot surface

Current primary A1 boot surface:
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/specs/31_A1_THREAD_BOOT__v1.md`

Precursor boot surface:
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/specs/26_BOOTPACK_A1_WIGGLE__v1.md`

Current required A1 working context:
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/a1_state/A1_BRAIN_SLICE__v1.md`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/a2_state/A2_TO_A1_DISTILLATION_INPUTS__v1.md`

Current interpretation:
- A1 has a current explicit boot
- dispatch discipline is now repo-held
- remaining process work is refinement/automation, not missing basic coordination law

## 8) Dispatch artifact rule

A2 should hand A1 only:
- explicit A2 update notes
- explicit A2-to-A1 impact notes
- explicit delta / handoff packets
- optionally ZIP_JOB packets when the A1 lane is being run through ZIP subagents

A2 should not hand A1:
- raw external source mass directly
- ambient controller memory
- uncategorized theory spill

## 9) Current system implication

The right near-term model is:
- one booted A2 controller thread
- dormant A1 unless called
- A1 invoked only by A2 dispatch
- many A1 ZIP subagents are allowed if explicitly dispatched from A2 and boot-bound

Current role-split surface:
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/specs/33_A2_VS_A1_ROLE_SPLIT__v1.md`

## 10) Immediate next build implication

The system still needs:
1. optional tighter queue packet tooling if later needed

Current state:
- `A2_THREAD_BOOT` exists
- `A2_TO_A1_HANDOFF_CONTRACT` exists
- `A1_QUEUE_STATUS_SURFACE` exists

Until richer automation exists, A1 should still be treated as manually dispatched from A2 by explicit prompt, not as an always-on parallel thread.
