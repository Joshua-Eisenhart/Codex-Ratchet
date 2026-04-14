# 2026-04-12 Corrected Bounded Automation Plan

Status: PRE-LAUNCH AUTOMATION PLAN — intended to prevent off-rails runs by enforcing layer bounds, order discipline, and explicit stop/gate rules.

Purpose: define how a future automated run should behave so it does the requested work in the requested order, remains bounded, and only advances when the current bounded layer is complete and audited.

## 1. Core contract

This automation is NOT:
- an open-ended overnight autonomy experiment
- a generic "do useful work" controller
- a broad sim sweeper
- a side-lane opportunist

It IS:
- a bounded layer controller
- a strict-order executor
- a lego-forging workflow
- a truth/audit-maintained process

## 2. Root process rules

1. Order is load-bearing.
   - If the requested order is violated, the run fails.
   - Useful out-of-order work does not count as success.

2. Layer bounds are real.
   - A time budget (e.g. 8 hours) does not permit widening.
   - The run stays inside the current bounded layer until that layer is complete or honestly blocked.

3. Bounded packet units only.
   - One lego, or one explicit connection between legos, per worker packet.
   - Never "the whole chain" in one autoresearch/controller step.

4. Geometry-first on the constrained side.
   - Complete the geometry legos first.
   - Then test bounded layer connections between geometry legos.
   - Only later move toward larger multi-lego composed sims.

5. Tool integration must happen inside the order, not instead of the order.
   - Use the full stack where relevant.
   - Do not widen scope just to touch more tools.
   - Do not accept decorative tool presence.

## 3. Current preferred research/build program

### Phase A — Geometry lego forging

Bounded target class:
- same-carrier geometry legos
- chirality/local bookkeeping legos
- direct connection/transport legos
- local operator legos needed by geometry-first order

Intent:
- rich, full, running QIT geometry sims under the root constraints
- no classical shortcut substitution for the constrained geometry program
- each lego should be hammered from many angles: positive, negative, boundary, tool-depth, and local consistency

### Phase B — Layer connection tests

Only after Phase A legos are complete enough:
- one bounded connection at a time
- test which geometry legos can run on which
- test compatibility / layering / coexistence
- let natural order emerge from admissible layering behavior

### Phase C — Larger composed geometry sims

Only after enough links and link-compatibility tests are real:
- multi-lego composed geometry sims
- eventually one larger integrated geometry-side sim

## 4. Carnot / Szilard rule

Carnot and Szilard are not forbidden.
They are classical and easier, and deeper full running engine sims can still be useful to the constrained side.

But automation must respect the distinction:

Preferred constrained-side method:
- extract constraint-aligned legos from Carnot/Szilard
- sim those legos individually in bounded packets

Allowed supportive method:
- run deeper full classical engine sims as bounded baseline/support work

Automation rule:
- do not let broad Carnot/Szilard engine runs displace the current geometry-first constrained layer
- do not let classical engine work become the default lane while geometry-first legos are still the active required layer

## 5. Worker unit policy

Each worker packet must be one of:
- one lego
- one successor hardening pass for one lego
- one connection between two already-defined legos
- one maintenance packet tied directly to just-completed bounded work

Each worker prompt must include:
1. exact read order
2. exact bounded target
3. allowed claims only
4. exact rerun command
5. exact audit commands
6. exact stop rules
7. exact non-goals / forbidden widening

## 6. Automation control surfaces

Authority / live surfaces:
- `new docs/LLM_CONTROLLER_CONTRACT.md`
- `new docs/ENFORCEMENT_AND_PROCESS_RULES.md`
- `new docs/EXPLICIT_CONTROLLER_MODEL.md`
- `new docs/ANOMALOUS_COMPUTER_SCIENCE_TRANSLATION.md`
- `new docs/16_lego_build_catalog.md`
- `new docs/17_actual_lego_registry.md`
- `new docs/plans/sim_backlog_matrix.md`
- `new docs/plans/sim_truth_audit.md`
- `new docs/plans/tool_integration_maintenance_matrix.md`
- `new docs/plans/controller_maintenance_checklist.md`

Supportive harness surfaces:
- `/Users/joshuaeisenhart/wiki/concepts/wiki-as-harness-architecture.md`
- `/Users/joshuaeisenhart/wiki/concepts/nominalist-translation-rules.md`
- `/Users/joshuaeisenhart/wiki/concepts/llm-constraint-harness-wiki.md`

## 7. Exact automation behavior

Before launch:
- verify current bounded layer and its exact target rows
- verify no side-lane widening is queued implicitly
- verify worker commands/interpreter exist
- verify the run plan states explicit stop conditions

During run:
- choose the next bounded packet only from the active layer
- after each successful packet:
  - rerun with canonical interpreter
  - run `probe_truth_audit.py`
  - run `controller_alignment_audit.py`
  - patch only directly stale surfaces
- after each blocked packet:
  - record blocker
  - do not blind-retry the same packet family repeatedly
  - either move to the next packet in the same bounded layer or stop if the layer cannot progress honestly

Advancement rule:
- only move to the next bounded layer if the current layer is complete enough by explicit gate
- time remaining alone is not an advancement reason

## 8. Autoresearch policy

Autoresearch is allowed only on:
- one specific chain link
- or one specific chain connection

Never on:
- the whole chain
- the whole geometry layer
- the whole run

Good autoresearch units:
- direct fiber-equivalence packet hardening
- one local operator packet
- one layering-compatibility packet
- one manifest/depth hardening pass for one direct packet

## 9. Launch-readiness checklist

A future automated run is launch-ready only if all are true:
- active layer explicitly named
- allowed packet list explicitly named
- forbidden packet classes explicitly named
- advancement gate explicitly named
- heartbeat payload explicitly defined
- stop/blocked behavior explicitly defined
- maintenance surfaces to patch explicitly named
- worker orchestration model explicitly named
- no ambiguity about whether transport (Telegram/local/manual) changes the run logic

## 10. Immediate next bounded run shape

If launching soon, the run should stay inside the current geometry/local-forging layer.

Recommended bounded packet sequence:
1. remaining geometry/local lego hardening rows only
2. local operator packet(s) directly required by geometry-first order
3. bounded connection tests between already-forged geometry legos

Do NOT automatically widen into:
- broad classical side lanes
- bridge / axis / flux work
- whole-stack packet sweeps
- open-ended autoresearch

## 11. Success condition for the future automated run

The automated run counts as successful only if:
- it stays inside the bounded requested layer
- it follows the required order exactly
- it does not substitute nearby useful work for the requested packet order
- every promoted claim is tied to a rerun + truth audit + controller audit
- advancement to a new layer happens only because the prior layer was actually completed or honestly blocked
