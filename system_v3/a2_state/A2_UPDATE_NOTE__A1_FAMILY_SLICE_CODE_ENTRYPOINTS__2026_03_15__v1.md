# A2_UPDATE_NOTE__A1_FAMILY_SLICE_CODE_ENTRYPOINTS__2026_03_15__v1

Status: DRAFT / NONCANON / DERIVED_A2 CONTROL NOTE
Date: 2026-03-15
Role: preserve the exact live code entrypoints where `A2_TO_A1_FAMILY_SLICE_v1` must replace profile/ladder doctrine

## Scope

This note is the code-seam companion to:
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/a2_state/A2_UPDATE_NOTE__A1_FAMILY_SLICE_CONTRACT__2026_03_15__v1.md`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/a2_state/A2_UPDATE_NOTE__A1_FAMILY_SLICE_SCHEMA_DRAFT__2026_03_15__v1.md`

It does not mutate runtime code.
It pins the live entrypoints so the next rewrite step can land in the actual seam instead of adding more wrapper prose.

## Live seam map

### 1) Planner source of doctrinal substitution

Primary file:
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tools/a1_adaptive_ratchet_planner.py`

Current substitution points:
- `Goal` dataclass at line 85
- fixed goal tuples begin at:
  - `CORE_GOALS` line 95
  - `EXTENDED_GOALS` line 122
  - `PHYSICS_FUEL_GOALS` line 232
  - `AXIS_FOUNDATION_GOALS` line 282
  - `MASTER_CONJUNCTION_GOALS` line 335
  - `ENTROPY_BRIDGE_GOALS` line 350
  - `REFINED_FUEL_GOALS` line 437
- active strategy builder entry:
  - `build_strategy_from_state(...)` line 1006
- planner CLI selection logic:
  - `main()` line 1571
  - `--goal-profile` line 1577
  - profile -> goals switch lines 1590-1603

Meaning:
- the real doctrinal substitution is happening before strategy construction
- `build_strategy_from_state(...)` itself still only sees:
  - `state`
  - `run_id`
  - `sequence`
  - `goals`
  - `goal_selection`
  - `debate_mode`

That is the narrowest insertion seam for `A2_TO_A1_FAMILY_SLICE_v1`.

### 2) Planner behavior already worth preserving

Likely reusable inside the reset:
- goal picking:
  - `_next_goal(...)` line 110
- probe selection:
  - `_probe_term_for_goal(...)` line 134
- prerequisite decomposition and bootstrap:
  - `build_strategy_from_state(...)` lines 1059-1074 and 1507-1522
- batch assembly and SIM/negative emission:
  - `build_strategy_from_state(...)` lines 1076-1567

Meaning:
- the planner’s packet-building mechanics are more salvageable than its profile/ladder chooser

### 3) Where family-slice input should first land

Minimum viable reset seam:
- add a new planner input path such as:
  - `--family-slice-json /abs/path/to/A2_TO_A1_FAMILY_SLICE_v1.json`

Then:
1. load and validate the slice before profile selection
2. derive a bounded planner context from the slice
3. feed that context into `build_strategy_from_state(...)`

The first transition does **not** require immediate full family-native planning.
It only requires that family-slice input outrank hardcoded profiles for:
- target term list
- admissible debate mode / run mode
- negative obligations
- family head/passenger/witness placement

## Proposed planner reset phases

### Phase 1: slice outranks profile

Add to planner:
- `--family-slice-json`

If present:
- load the JSON
- validate against:
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/work/audit_tmp/spec_object_drafts/A2_TO_A1_FAMILY_SLICE_v1.schema.json`
- derive:
  - `goals`
  - `debate_mode`
  - allowed head terms
  - forbidden promoted terms

Keep old `--goal-profile` path only as fallback.

### Phase 2: scaffold profiles become explicit scaffold-only presets

Keep old profile tuples only under semantics like:
- `--scaffold-profile`

Do not let `goal_profile` continue pretending to be the main doctrine input for validity-mode runs.

### Phase 3: planner takes family context, not just goals

Replace:
- `goals`

with something closer to:
- `planner_context`

Expected minimum fields:
- ordered candidate terms
- head terms
- companion floor
- witness-only terms
- required negative classes
- rescue enablement
- graveyard fill/recovery policy

## Autoratchet seam

Primary file:
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tools/autoratchet.py`

Current substitution points:
- `_required_probe_terms_for_profile(...)` line 238
- main CLI starts line 278
- `--goal-profile` line 288
- profile -> `goal_terms` switch lines 342-355
- planner child command lines 449-470
- semantic gate required-probe-term selection lines 539-545

Meaning:
- `autoratchet.py` currently defines campaign meaning twice:
  1. planner input meaning
  2. gate expectation meaning

Reset requirement:
- the same family-slice object that drives planner input must also drive semantic-gate expectations
- otherwise the planner and gate will drift immediately

## Control wrapper seam

Primary file:
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/tools/run_a1_wiggle_control_cycle.py`

Current substitution points:
- operator-visible knob surface lines 60-89
- autoratchet child command lines 101-118

Meaning:
- this wrapper still forwards profile-era runtime policy
- it should become a thin runner over:
  - `--family-slice-json`
  - bounded cycles
  - controller result paths

## First concrete patch order

1. planner:
   - add `--family-slice-json`
   - load/validate slice
   - make slice outrank `--goal-profile`
2. autoratchet:
   - add `--family-slice-json`
   - stop deriving gate requirements from `goal_profile` when slice is present
3. control cycle wrapper:
   - accept/pass `--family-slice-json`
   - demote `--goal-profile` to scaffold/debug only

## Guardrail

Do not begin by teaching wrappers to pass the slice while the planner still ignores it.

The first real patch must land at the planner input seam.
