# A2_BOOT_READ_ORDER__CURRENT__v1
Status: ACTIVE / DERIVED_A2 / BOOT COMPANION
Date: 2026-03-21
Role: minimal bounded read order for rebuilding A2 working context from `system_v3` without drowning in `a2_state`

## Why This Exists

`system_v3/a2_state/` currently contains too many files to function as a usable persistent brain by simple directory reading.

This file gives the bounded "start here" path for:

- understanding how A2 is supposed to work
- recovering the standing A2 brain/control surfaces
- keeping `system_v4` work grounded in the previous system instead of drifting into graph-only construction

## Step 1 — Read The Owner Law First

Read these before treating any working notes as meaningful:

1. `system_v3/specs/01_REQUIREMENTS_LEDGER.md`
   - root requirements and the A2 requirement family
2. `system_v3/specs/02_OWNERSHIP_MAP.md`
   - which docs actually own which requirement ranges
3. `system_v3/specs/07_A2_OPERATIONS_SPEC.md`
   - what A2 is supposed to do
4. `system_v3/specs/19_A2_PERSISTENT_BRAIN_AND_CONTEXT_SEAL_CONTRACT.md`
   - how A2 persistent memory/seal/compaction is supposed to work

## Step 2 — Read The Active A2 Brain Surfaces

These are the bounded A2 brain/control surfaces that should be read as a set:

1. `system_v3/a2_state/INTENT_SUMMARY.md`
2. `system_v3/a2_state/A2_BRAIN_SLICE__v1.md`
3. `system_v3/a2_state/A2_SYSTEM_UNDERSTANDING_UPDATE__SOURCE_BOUND_v2.md`
4. `system_v3/a2_state/A2_TERM_CONFLICT_MAP__v1.md`
5. `system_v3/a2_state/A2_TO_A1_DISTILLATION_INPUTS__v1.md`
6. `system_v3/a2_state/OPEN_UNRESOLVED__v1.md`
7. `system_v3/a2_state/A2_CONTROLLER_STATE_RECORD__CURRENT__v1.md`
8. `system_v3/a2_state/SURFACE_CLASS_AND_MEMORY_ADMISSION_RULES__v1.md`
9. `system_v3/a2_state/A2_KEY_CONTEXT_APPEND_LOG__v1.md`
10. `system_v3/a2_state/A2_SKILL_SOURCE_INTAKE_PROCEDURE__CURRENT__v1.md`

## Step 3 — Read The Canonical A2 Persistent-State Files

These are not the same thing as the human-readable brain surfaces, but they matter:

1. `system_v3/a2_state/memory.jsonl`
2. `system_v3/a2_state/doc_index.json`
3. `system_v3/a2_state/fuel_queue.json`
4. `system_v3/a2_state/rosetta.json`
5. `system_v3/a2_state/constraint_surface.json`

## Step 4 — Treat These As Derived / Supporting, Not The Brain

These may be useful, but should not be mistaken for the standing A2 brain:

- one-off `A2_UPDATE_NOTE__...`
- one-off `A2_TO_A1_IMPACT_NOTE__...`
- `A2_WORKER_PROMPT__...`
- launch packets and send-text packets
- ingest packets
- runtime/run evidence
- noncanonical helper audits

## Current Practical Rule

If `system_v4` work is being done and the current A2 state feels lost:

1. read Step 1
2. read Step 2
3. only then consult Step 3 and Step 4

Do not start by browsing `system_v3/a2_state/` as a raw directory and hoping the current truth emerges.

## Current Diagnosis

The problem is not only "graph missing."

The bigger problem is:

- A2 owner law exists
- A2 persistent-brain contract exists
- but the active human boot path through `a2_state` has been too weak

That means:

- `system_v4` cannot safely be built as if the previous system were already fully processed and understood
- system_v3 still needs explicit reading, processing, graphing, and integration
- graph-building must stay subordinate to actual system understanding
