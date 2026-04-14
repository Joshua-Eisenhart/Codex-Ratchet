# Corrected Bounded Automation Plan

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
   - A time budget does not permit widening.
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

### Current reset before the next relaunch

Before the next automated relaunch, the controller should treat the repo as being in a process-improvement reset, not just a stale-launch retry.

That means the next launch should default to:
- tool-capability foundation / counterpart-forging work first
- scientific successor-hardening second

Reason:
- we can simulate nearly everything with numpy/classical machinery
- the harder and more valuable task is learning exactly what each nonclassical tool can do here, under bounded conditions
- only after that should the controller lean harder on the full tool stack inside the more delicate quantum/tool-native packets

Operational rule:
- every major family should ideally gain three explicit surfaces:
  1. a classical baseline / numpy reference
  2. a canonical tool-native counterpart
  3. a comparison note explaining what the tool actually adds

Scope rule:
- the tool list and packet examples named in chat or in a launch note are seed examples, not an exhaustive whitelist of all valid next moves
- the controller must reread the broader authority docs, queue surfaces, registry rows, and wiki/tool-capability notes before launch and choose bounded packets from the full admissible nearby set
- do not overweight only the items most recently named in chat if adjacent bounded packets better satisfy the same lane and process contract

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
- if the active layer is the tool-capability lane, prefer packets that clarify one tool's real capability envelope before attempting broader tool-stack integration
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
- no ambiguity about whether transport changes the run logic

## 10. Immediate next bounded run shape

If launching soon, the run should NOT reuse the now-exhausted geometry/local-forging base-packet list, and it should not relaunch the old overnight contract unchanged.

That earlier local-forging slice is already process-canonical for the previously named launch packets.

The next honest default active layer is:
- tool-capability foundation / counterpart-forging layer

The next honest secondary layer is:
- successor-hardening / first pairwise-coupling layer

Recommended bounded packet sequence:
1. one bounded tool-capability packet or tiny wave on non-overlapping files
2. its direct baseline / canonical counterpart / comparison-note closure if that trio is not yet explicit
3. maintenance-only truth/tool/registry/wiki patches tied directly to those outcomes
4. only if the tool-capability lane is honestly blocked, use `operator_geometry_compatibility` and `compound_operator_geometry` as the bounded scientific successor-hardening fallback
5. stop if the best honest outcome remains baseline-only or supporting-only after rerun and audit; do not reopen already-canonical base geometry anchors just to stay busy

Recommended seed examples for the tool-capability lane:
- z3 impossibility micro-probes
- cvc5 cross-check / SyGuS micro-probes
- sympy derivation probes
- rustworkx DAG/routing probes
- PyG tensor-on-graph probes
- XGI multi-way interaction probes
- TopoNetX cell-complex probes
- GUDHI filtration/persistence probes
- clifford rotor/spinor probes
- e3nn equivariance probes
- geomstats geodesic/metric probes

These examples are illustrative, not exhaustive.
The controller should pick from the broader admissible nearby set when a neighboring bounded packet better serves the same tool-capability goal.

Do NOT automatically widen into:
- already-canonical local-forging anchors (`nested_torus_geometry`, `fiber_loop_law`, `base_loop_law`, `berry_holonomy`, `local_operator_action`) unless a concrete process defect is named
- broad classical side lanes
- graph/cell/persistence deepeners that bypass the active layer's current purpose
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
