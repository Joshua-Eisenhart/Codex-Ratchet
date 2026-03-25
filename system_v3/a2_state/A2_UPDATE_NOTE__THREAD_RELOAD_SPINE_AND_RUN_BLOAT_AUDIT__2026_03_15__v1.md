# A2_UPDATE_NOTE__THREAD_RELOAD_SPINE_AND_RUN_BLOAT_AUDIT__2026_03_15__v1

Status: DRAFT / NONCANON / DERIVED_A2 CONTROL NOTE
Date: 2026-03-15
Role: preserve the current controller-thread reload spine, recent review findings, and the grounded run-folder bloat read so a fresh thread can resume without reconstructing the session

## Scope

This note compresses the current controller-thread state after:
- the A1 runtime reset and family-slice ownership patches
- the local spec-object / queue / launch-surface rollout
- the bounded review pass over the recent family-slice object path
- the first grounded audit of `system_v3/runs/` as the main local bloat surface

This is a `DERIVED_A2` continuity surface.
It does not rewrite owner doctrine or promote runtime residue into canon.

## Read first on reload

1. `/home/ratchet/Desktop/Codex Ratchet/system_v3/a2_state/A2_UPDATE_NOTE__THREAD_RELOAD_SPINE_AND_RUN_BLOAT_AUDIT__2026_03_15__v1.md`
2. `/home/ratchet/Desktop/Codex Ratchet/system_v3/a2_state/A2_UPDATE_NOTE__A1_RUNTIME_RESET_AND_SPEC_OBJECT_DIRECTION__2026_03_15__v1.md`
3. `/home/ratchet/Desktop/Codex Ratchet/system_v3/a2_state/A2_UPDATE_NOTE__A1_FAMILY_SLICE_RECOVERY_SHAPE_OWNERSHIP_PATCH__2026_03_15__v1.md`
4. `/home/ratchet/Desktop/Codex Ratchet/system_v3/a2_state/A2_UPDATE_NOTE__FIRST_LOCAL_PYDANTIC_FAMILY_SLICE_STACK__2026_03_15__v1.md`
5. `/home/ratchet/Desktop/Codex Ratchet/system_v3/a2_state/A2_UPDATE_NOTE__FAMILY_SLICE_VALIDATOR_UNIFICATION_AND_PROVENANCE_PATCH__2026_03_15__v1.md`
6. `/home/ratchet/Desktop/Codex Ratchet/system_v3/a2_state/A2_UPDATE_NOTE__A1_QUEUE_BUNDLE_INTEGRITY_HARDENING__2026_03_15__v1.md`
7. `/home/ratchet/Desktop/Codex Ratchet/system_v3/a2_state/A2_UPDATE_NOTE__A1_FAMILY_SLICE_SCHEMA_ALIGNMENT_AND_PYDANTIC_REFRESH__2026_03_15__v1.md`
8. `/home/ratchet/Desktop/Codex Ratchet/system_v3/a2_state/A2_UPDATE_NOTE__A1_FAMILY_SLICE_GRAVEYARD_NEGATIVE_LIMIT_OWNERSHIP_PATCH__2026_03_15__v1.md`
9. `/home/ratchet/Desktop/Codex Ratchet/system_v3/a2_state/A2_UPDATE_NOTE__A1_FAMILY_SLICE_GRAVEYARD_BUDGET_OWNERSHIP_PATCH__2026_03_15__v1.md`
10. `/home/ratchet/Desktop/Codex Ratchet/system_v3/a2_state/A2_UPDATE_NOTE__A1_FAMILY_SLICE_LANE_VISIBILITY_AND_MINIMUM_COVERAGE_PATCH__2026_03_15__v1.md`
11. `/home/ratchet/Desktop/Codex Ratchet/system_v3/a2_state/A2_UPDATE_NOTE__A1_FAMILY_SLICE_SCAFFOLD_RESCUE_LANE_AND_LANE_MINIMUM_GATE__2026_03_15__v1.md`
12. `/home/ratchet/Desktop/Codex Ratchet/system_v3/a2_state/A2_UPDATE_NOTE__A1_FAMILY_SLICE_SCAFFOLD_RESCUE_MULTIPLICITY_PATCH__2026_03_15__v1.md`
13. `/home/ratchet/Desktop/Codex Ratchet/system_v3/a2_state/A2_UPDATE_NOTE__A1_FAMILY_SLICE_RESCUE_LINEAGE_FIELD_OWNERSHIP_PATCH__2026_03_15__v1.md`
14. `/home/ratchet/Desktop/Codex Ratchet/system_v3/a2_state/A2_UPDATE_NOTE__A1_FAMILY_SLICE_NON_RESCUE_BRANCH_LINEAGE_OWNERSHIP_PATCH__2026_03_15__v1.md`
15. `/home/ratchet/Desktop/Codex Ratchet/system_v3/a2_state/A2_UPDATE_NOTE__A1_BRANCH_PARENTAGE_VISIBILITY_AND_AUDIT_PATCH__2026_03_15__v1.md`
16. `/home/ratchet/Desktop/Codex Ratchet/system_v3/a2_state/A2_UPDATE_NOTE__A1_SINGLE_PRIMARY_ROOT_TOPOLOGY_PATCH__2026_03_15__v1.md`
17. `/home/ratchet/Desktop/Codex Ratchet/system_v3/a2_state/A2_UPDATE_NOTE__A1_BRANCH_GROUP_VISIBILITY_AND_AUDIT_PATCH__2026_03_15__v1.md`
18. `/home/ratchet/Desktop/Codex Ratchet/system_v3/a2_state/A2_UPDATE_NOTE__A1_BRANCH_TRACK_VISIBILITY_AND_AUDIT_PATCH__2026_03_15__v1.md`

If the next thread is about maintenance/cleanup, also read:
- `/home/ratchet/.codex/skills/safe-run-maintenance/SKILL.md`
- `/home/ratchet/.codex/skills/safe-run-maintenance/references/allowlist-denylist.md`
- `/home/ratchet/.codex/skills/safe-run-maintenance/references/loop-shape.md`

## Current high-signal state

### 1) Overall direction

The project is still on task at the architecture level:
- A1 runtime reset remains aimed at the right core seams
- family-slice-first control is now materially real in the planner/controller path
- the local `Pydantic + JSON + NetworkX + GraphML` object spine is real on family-slice, queue, and launch surfaces

But the repo is still mid-transition:
- the worktree is large and dirty
- compatibility scaffolds still exist
- the new object layer is not yet a single trustworthy contract boundary

### 2) Current grounded review findings

Locked findings from the recent audit:

1. Split validator law:
- the manual family-slice schema and the live Pydantic/runtime validator disagree
- result: a slice can pass prep in `jsonschema` mode and fail later in the live runtime
 - status now: materially improved by `jsonschema + runtime semantics` plus tighter SIM-family/SIM-tier schema constraints, but JSON schema still does not encode every live cross-field rule

2. Machine-dependent `auto` validation:
- `auto` switches between `jsonschema` and local Pydantic depending on whether `.venv_spec_graph` exists
- status now: packet/bundle/queue surfaces do record requested/resolved/source provenance, but cross-machine behavior is still environment-sensitive

3. Queue-packet trust boundary is weak:
- queue validators prove referenced bundle artifacts exist
- they do not prove the referenced packet/bundle companion/spine set belongs to the same dispatch
 - status now: fixed for the ready packet/bundle/companion/spine coherence path

4. Checked-in emitted Pydantic family-slice schema artifact is stale:
- the repo advertises it as current
- tests only emit/check temp schema files, not the committed artifact
 - status now: fixed for `A2_TO_A1_FAMILY_SLICE_v1`; committed emitted artifact refreshed and protected by a freshness regression

5. Local spec-graph path is under-tested where behavior is environment-sensitive:
- many relevant tests are skipped if `.venv_spec_graph` is missing
- green on another machine may not mean the same path was exercised

### 3) Focused runtime/core status

Recent runtime-core patches are real and worth keeping:
- family slices now own more planner behavior around:
  - negative obligations
  - target-class naming
  - graveyard-first negative expansion
  - probe-source ownership
  - SIM-family tiers
  - recovery shape
  - lane-minimum coverage visibility
  - branch-requirement visibility
  - scaffold rescue-lane emission
  - live lane-minimum satisfaction gating
  - scaffold rescue multiplicity from declared lane minima
  - rescue-lineage field ownership on emitted rescue branches
  - non-rescue branch-lineage field ownership on the main family branch set
  - explicit live branch parentage/grouping visibility plus controller audit coverage
  - single-primary-root family topology for non-rescue family-slice runs
  - explicit branch-group visibility on emitted family branches plus controller-audit comparison against actual grouping
  - explicit branch-track visibility on emitted family branches plus controller-audit comparison against actual emitted tracks
- `run_real_loop.py` is in a better place:
  - strict path separated from recovery path
  - recovery now has a dedicated entrypoint
  - compatibility recovery now emits explicit warning/manual-review signals

These seams are improved, but not complete.

## Run-folder bloat read

### Grounded current numbers

Current local run tree:
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/runs`
- approximate size: `275M`
- immediate child count: `90`

Pattern concentration:
- `49` `RUN_GRAVEYARD_VALIDITY_*`
- `11` `TEST_*`
- `8` `RUN_SUBSTRATE_*`
- `7` `RUN_AUTOWIGGLE*`
- `4` `RUN_A1_*`
- `4` `RUN_ENTROPY_*`

Largest members observed:
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/runs/_RUNS_REGISTRY.jsonl` about `15M`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/runs/RUN_DUAL_THREAD_NO_PRO_SMOKE_0004` about `15M`
- multiple `RUN_GRAVEYARD_VALIDITY_ENTROPY_BRIDGE_*` continuation families in the `7M-9M` range

### What is clearly protected/live

Never move from `system_v3/runs/`:
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/runs/_CURRENT_STATE`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/runs/_CURRENT_RUN.txt`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/runs/_RUNS_REGISTRY.jsonl`

Current recent safety-window surfaces:
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/runs/RUN_A1_WIGGLE_SMOKE_20260314_01`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/runs/RUN_A1_WIGGLE_SMOKE_20260314_02`

### Current maintenance judgment

The user’s diagnosis is correct:
- `system_v3/runs/` is the main local bloat surface
- much of that surface is experimental/test/graveyard-continuation residue
- that residue is not the same thing as trusted active runtime state

But no maintenance move has been executed yet.

Per the maintenance policy, the current exact decisions are:
- `KEEP_ACTIVE`
  - protected current surfaces
  - run dirs inside the recent safety window
- `BLOCKED_REQUIRES_PREP`
  - the large older run families, including `RUN_GRAVEYARD_VALIDITY_*`
  - `TEST_*`
  - smoke runs

Reason:
- run families may not be moved by size/name alone
- an exact archive-prep list is still required

## What the next thread should do

If continuing the architecture/runtime path:
1. continue shrinking remaining planner-global defaults inside family-slice mode
2. especially target any remaining mode-specific branch-shape defaults above the new scaffold rescue floor and any rescue-shape rules that still are not declared by the family slice
3. inspect whether any remaining family-branch clustering rules still sit only in planner code beyond the now-visible `BRANCH_GROUP` surface
4. inspect whether any remaining family-branch semantics are still only encoded in planner-local naming rules after the new `BRANCH_TRACK` surface

If continuing the bloat/cleanup path:
1. do a bounded archive-prep pass only on `/home/ratchet/Desktop/Codex Ratchet/system_v3/runs`
2. classify exact candidates as one of:
   - `KEEP_ACTIVE`
   - `MOVE_TO_ARCHIVE`
   - `MOVE_TO_QUARANTINE`
   - `BLOCKED_REQUIRES_PREP`
3. do not delete
4. do not touch owner surfaces
5. do not move run families by size/name alone

## Continuity reminder

This thread has produced many bounded A2 notes.
Do not reload by bulk-reading all of them.

Start from this note, then the two linked reset notes above, then branch:
- runtime/object-contract path
- or run-maintenance classification path

That is the intended short reload spine.
