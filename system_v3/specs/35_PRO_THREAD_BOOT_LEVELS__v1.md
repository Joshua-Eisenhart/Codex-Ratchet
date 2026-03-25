# PRO_THREAD_BOOT_LEVELS__v1
Status: DRAFT / NONCANON / ACTIVE PROCEDURE SURFACE
Date: 2026-03-11
Owner: current `A2` controller, external `Pro` research lanes, and ZIP-bound external research packs

## Purpose

This note defines the current `Pro` thread classes and the boot/context depth each class requires.

Main rule:
- not all `Pro` threads are the same
- some are narrow source workers
- some are lane-level refinery workers
- some are full-context exploratory `A2`-style reasoning spaces

Each class needs:
- the right boot depth
- the right trust rule
- the right audit rule

## Hard rules

1. `PRO_IS_NOT_AUTHORITY`
- no `Pro` thread is direct authority
- every `Pro` return must be audited before `A2` ingestion

2. `BOOT_CLASS_MUST_BE_EXPLICIT`
- every `Pro` lane must declare its class before launch

3. `CONTEXT_DEPTH_MUST_MATCH_ROLE`
- narrow workers should not receive full-system context by default
- full-context reasoning spaces should not pretend to be narrow source workers

4. `GENERATION_AND_AUDIT_SPLIT`
- generation = web UI `Pro`
- audit = web UI `Thinking / Heavy`

5. `ZIP_FIRST`
- if the lane is artifact-driven, its boot/context should travel primarily through the ZIP pack
- chat prompt specifies the bounded task, not hidden missing law

## Boot levels

### `PRO_BOOT_LEVEL_1__NARROW_SOURCE`

Use when:
- one source family
- one packet family
- one acquisition problem

Examples:
- `carnot_primary`
- `maxwell_demon_primary`
- `qit_reconstruction_primary`

Minimum context:
- one ZIP pack
- packet-local `sources/`
- packet-local `input/`
- packet-local `tasks/`
- packet-local `templates/`

Should not include by default:
- broad `system_v3`
- full `A2` brain
- unrelated packet families

Trust mode:
- source acquisition / extraction only

Audit expectation:
- completeness and citation audit
- overclaim audit
- fail closed if source-bearing coverage is still absent

### `PRO_BOOT_LEVEL_2__METHOD_COMPARE`

Use when:
- one bounded comparison across adjacent methods, labs, or thinkers
- several packet families but still one narrow question

Examples:
- solver vs model-check vs fuzz method comparison
- AlphaGeometry vs search-control method comparison

Minimum context:
- ZIP pack
- selected packet family set
- limited `A2` overlays if needed for comparison criteria

May include:
- selected `MODEL_CONTEXT` or `INTENT_SUMMARY` slices

Should not include by default:
- broad whole-system context
- unrelated run/runtime surfaces

Trust mode:
- comparative method scouting

Audit expectation:
- distinction preservation
- no method smoothing
- no thinker/lab authority inflation

### `PRO_BOOT_LEVEL_3__LANE_REFINERY`

Use when:
- one external lane spans multiple source families
- the goal is to produce a structured lane-wide research return

Examples:
- entropy / Carnot / Szilard / Maxwell lane
- QIT reconstruction + FEP + method bridge lane

Minimum context:
- ZIP pack with multiple packet families
- bounded current A2 framing for the lane
- explicit lane-level output contract

May include:
- selected current A2 state
- selected execution-state context
- selected queue/routing notes

Trust mode:
- lane-level fuel production

Audit expectation:
- source-bearing vs scaffold-only split must be explicit
- local-pack success is not enough for substantive promotion

### `PRO_BOOT_LEVEL_4__FULL_A2_REASONING_SPACE`

Use when:
- the task is exploratory, synthetic, retooling-heavy, or philosophy-heavy
- you want a high-context external reasoning space
- controlled hallucination is acceptable as long as later audit/reduction is strict

Examples:
- working out theory alignment
- testing retoolings across many external systems
- broad external idea synthesis against current project structure

Minimum context:
- large `A2` slice
- possibly broad `system_v3` process law
- bounded source packet selection where available

May include:
- current active `A2` owner surfaces
- selected execution-state/control surfaces
- large bounded project slices

Must include:
- explicit statement that this is exploratory and non-authoritative

Trust mode:
- exploratory `A2`-style reasoning only

Audit expectation:
- strongest audit burden
- treat output as exploratory fuel, not direct conclusion
- reduce into smaller source-bound keepers before any A2 admission

## Required launch declaration

Every `Pro` launch must state:
- `PRO_THREAD_CLASS`
- `BOOT_LEVEL`
- `ROLE`
- `BOUNDED_SCOPE`
- `RETURN_CONTRACT`
- `AUDIT_MODE`

Minimum acceptable values:
- `PRO_THREAD_CLASS = NARROW_SOURCE_WORKER | METHOD_COMPARE_WORKER | LANE_REFINERY_WORKER | FULL_A2_REASONING_SPACE`
- `AUDIT_MODE = Thinking/Heavy`

## Context-depth selection rule

Choose the lowest boot level that still lets the thread do its real job.

Escalate context only when:
- the narrower level would make the task fail
- or the task is explicitly exploratory/system-aware by design

Do not escalate just because:
- more context feels safer
- the operator wants “everything there”
- the lane has not been cleanly scoped

## Relation to scale envelope

This note defines thread classes.

Concurrency still follows:
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/a2_state/SCALE_UP_ENVELOPE__2026_03_11__v1.md`

Meaning:
- current safe external envelope remains `1` to `3` live `Pro` lanes
- this note only clarifies what kind of `Pro` lane each one is

## Immediate implication

Current gap closed by this note:
- `Pro` work no longer has to be treated as one undifferentiated class
- narrow worker lanes, method-compare lanes, lane-refinery lanes, and full-context exploratory lanes now have distinct boot/context rules

Current runnable templates:
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/specs/36_PRO_LAUNCH_TEMPLATE__NARROW_SOURCE__v1.md`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/specs/37_PRO_LAUNCH_TEMPLATE__FULL_A2_REASONING_SPACE__v1.md`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/specs/38_PRO_LAUNCH_TEMPLATE__LANE_REFINERY__v1.md`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/specs/39_PRO_LAUNCH_TEMPLATE__METHOD_COMPARE__v1.md`
