# [Controller-safe] Dual-Loop Spinor Grammar

**Status:** Owner grammar preservation surface.  
**Purpose:** Preserve the engine's dual-loop spinor structure as a discrete grammar so future docs and sims do not flatten it into a single generic 8-terrain runtime.

---

## Owner Preservations

These are the owner statements this surface preserves:

- Two engine types are stacked on left/right Weyl spinor structure.
- Both engine types have a cooling loop and a heating loop.
- The difference is not "one heats, one cools"; the difference is the placement/order of those loops.
- Left-handed engine:
  - cooling outer
  - heating inner
- Right-handed engine:
  - heating outer
  - cooling inner

Primary extraction source:
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/ultra high entropy docs/txt/GPT 12_29 pro plan vs browser crashes.md.txt`

Relevant owner wording:
- lines around `6203`
- lines around `6340`

---

## What This Grammar Is

1. `spinor_type`
- left-handed engine family
- right-handed engine family

2. `loop_outer`
- one full 4-stage loop
- carries either cooling or heating role depending on engine type

3. `loop_inner`
- one full 4-stage loop
- carries the complementary role to `loop_outer`

4. `loop_role`
- heating
- cooling
- note: thermodynamic words are metaphor handles, not literal classical thermodynamics

5. `loop_ordering`
- the loops run in opposed order/direction patterns
- this is part of the engine grammar, not a loose visualization preference

---

## What This Grammar Is Not

- not the same thing as Axis 6 precedence
- not the same thing as induction/deduction
- not the same thing as type labels alone
- not the same thing as current flattened runtime terrain order
- not a claim that the live runtime already implements this faithfully

---

## Runtime Reality Check

The current runtime in `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/probes/engine_core.py` does **not** yet model these as first-class objects.

It currently exposes:
- one engine instance
- 8 macro-stages
- 4 repeated operator slots
- type-dependent weighting

It does **not** yet expose:
- explicit `outer_loop` / `inner_loop`
- explicit `heating_loop` / `cooling_loop`
- explicit inversion of loop-role placement across left/right engine families

---

## Allowed Use

This document may be used to:
- block flattened restatements of the engine
- preserve loop-role ownership during rebuilds
- define what future runtime/state models must keep distinct

This document may not be used to:
- claim the runtime already implements the dual-loop spinor grammar
- force exact formal thermodynamic equations onto `heating/cooling`
- collapse type, flow, and precedence into one distinction
