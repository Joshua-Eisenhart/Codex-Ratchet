# 2026-04-12 Overnight 8h Run Plan

Status: OPEN-ENDED OVERNIGHT RUN PLAN — geometry-first, bottom-up lego work, high parallelism, broader pre-Axis geometry scope, and controller-audited closure.

Purpose: define a real 8-hour overnight work program that keeps advancing the full geometry/pre-Axis machinery stack step by step, with many parallel lanes, visible progress, anti-stuck behavior, and only bounded fallback use of the classical/QIT engine lane.

Authority surfaces used:
- `new docs/LLM_CONTROLLER_CONTRACT.md`
- `new docs/ENFORCEMENT_AND_PROCESS_RULES.md`
- `new docs/EXPLICIT_CONTROLLER_MODEL.md`
- `new docs/ANOMALOUS_COMPUTER_SCIENCE_TRANSLATION.md`
- `new docs/16_lego_build_catalog.md`
- `new docs/17_actual_lego_registry.md`
- `new docs/LLM_RESEARCH_GAP_MATRIX.json`
- `docs/plans/sim_backlog_matrix.md`
- `docs/plans/sim_truth_audit.md`
- `docs/plans/tool_integration_maintenance_matrix.md`
- `docs/plans/controller_maintenance_checklist.md`
- `docs/plans/on-demand-telegram-runner.md`
- `system_v5/READ ONLY Reference Docs/Pre axies math and geometry work out.md`
- `system_v5/READ ONLY Reference Docs/Formal constraints and geometry .md`
- `system_v5/READ ONLY Reference Docs/AXIS_0_1_2_QIT_MATH.md`
- `system_v5/READ ONLY Reference Docs/operator math explicit.md`
- `system_v5/READ ONLY Reference Docs/Weyl Flux.md`

## 1. Correct model of an 8-hour run

This should NOT be a tiny fixed list that clearly finishes in under 2 hours.

An actual 8-hour run here should:
- keep pulling the next bounded lego packet from the live queue
- use many parallel lanes where file sets do not overlap
- close each packet with rerun + truth/audit + maintenance sync
- continue to the next packet while health remains good
- stop widening only when the queue reaches a real blocker or the run budget ends

So the overnight run is:
- one long controller session
- many bounded worker packets
- multiple successive waves
- geometry-first by default
- classical/QIT lane only as fallback or side lane after geometry waves are healthy

## 2. Non-negotiable run rules

Hard rules:
- geometry-before-axis
- bottom-up lego work only
- no bridge / Axis widening
- no flux promotion
- standard math terms only for geometry-lego work
- many parallel workers allowed only on non-overlapping file sets
- after every successful packet:
  - rerun with canonical interpreter
  - run `system_v4/probes/probe_truth_audit.py`
  - run `system_v4/probes/controller_alignment_audit.py`
  - patch only directly stale surfaces
- use only the four controller truth labels:
  - `exists`
  - `runs`
  - `passes local rerun`
  - `canonical by process`

## 3. Broader geometry scope from system_v5

The geometry scope for this overnight run is broader than the currently convenient queue labels.
The `system_v5` reference docs make the intended pre-Axis machinery explicit as this chain:

1. finite carrier and density states
2. Hopf carrier and nested torus seat structure
3. Weyl refinement
4. density refinement (`rho_L`, `rho_R`)
5. loop grammar
6. transport refinement
7. chirality refinement
8. candidate pre-Axis current/change surfaces
9. only later bridge / cut-state / entropy / axis machinery

So “all the geometry” here means the broader pre-Axis machinery stack, not merely a few already-convenient result rows.

## 4. Already rerun-backed from this session

These should not be the default first overnight targets unless a process gap requires another pass:
- `sphere_geometry_results.json`
- `nested_torus_geometry_results.json`
- `fubini_study_geometry_results.json`
- `bures_geometry_results.json`
- `torch_hopf_connection_results.json`
- `graph_shell_geometry_results.json`
- `cell_complex_geometry_results.json`
- `persistence_geometry_results.json`
- `fiber_base_transport_test_results.json`
- `weyl_spinor_hopf_results.json`
- `weyl_nested_shell_results.json`
- `lego_pauli_algebra_results.json`

This matters because a real 8-hour run should spend most of its time on still-partial packets, not just re-run already landed rows.

## 5. Primary overnight objective

Advance as many still-partial geometry/chirality/operator legos as honestly possible, one bounded packet at a time, with continuous maintenance closure.

Primary target families:
- Hopf-map / fiber / connection packet
- density-refinement / chiral-bookkeeping packet
- loop-law packet
- local operator action packet
- local order-sensitivity packet
- transport / holonomy deepen packet
- graph / cell / persistence deepen packet
- pre-Axis change-surface packet below flux and below Axis language

Secondary target family:
- classical Carnot / Szilard QIT-aligned companion rows, only after geometry waves are healthy or when geometry workers are blocked

## 6. Open-ended overnight lane inventory

### Geometry lane G1 — Hopf projection packet
Goal:
- `hopf_map_s3_to_s2`

Expected output:
- direct rerun-backed truth row for the explicit Hopf-map packet, not just generic Hopf geometry

### Geometry lane G2 — fiber equivalence packet
Goal:
- `hopf_fiber_equivalence`

Expected output:
- direct density-invariance / fiber-equivalence row

### Geometry lane G3 — density refinement packet
Goal:
- make the left/right density layer explicit as its own bounded packet

Math target:
- `rho_L = psi_L psi_L^dagger`
- `rho_R = psi_R psi_R^dagger`
- direct bookkeeping identities and comparison surfaces on one fixed carrier / torus family

### Geometry lane G4 — chiral bookkeeping packet
Goal:
- `chiral_density_bookkeeping`

Expected output:
- direct `rho_L`, `rho_R`, and joint bookkeeping packet, not just projector/topology shell claims

### Geometry lane G5 — loop-law packet
Goal:
- `fiber_loop_law`
- `base_loop_law`

Expected output:
- explicit density-stationary versus density-traversing packet
- horizontal condition / loop-law distinction made result-backed

### Geometry lane G6 — local operator action packet
Goal:
- `local_operator_action`

Expected output:
- direct primitive-operator-on-local-state packet below engine promotion

### Geometry lane G7 — composition-order packet
Goal:
- `composition_order_noncommutation`

Expected output:
- direct local order-sensitivity row

### Geometry lane G8 — transport/holonomy packet
Goal:
- `transport_geometry`
- `holonomy_geometry`

Expected output:
- stronger, more explicit transport/holonomy packet built from the current Hopf-connection anchor

### Geometry lane G9 — graph/cell/persistence deepen packet
Goal:
- deepen still-partial geometry views:
  - `graph_shell_geometry`
  - `cell_complex_geometry`
  - `persistence_geometry`

Expected output:
- stronger tool depth and cleaner truth/ledger separation for those rows

### Geometry lane G10 — pre-Axis change-surface packet
Goal:
- simulate raw pre-Axis change surfaces before any flux promotion

Math target:
- stagewise deltas
- chirality differential
- transport-sensitive change surfaces

Why it matters:
- `system_v5/Weyl Flux.md` documents flux as a candidate family that must be built from these lower surfaces first
- this lane stays pre-flux and pre-axis; it is still geometry/refinement work

### Maintenance lane M1 — truth / tool / ledger / wiki sync
Goal:
- keep controller surfaces honest after each geometry packet

Touched surfaces when justified:
- `docs/plans/sim_truth_audit.md`
- `docs/plans/tool_integration_maintenance_matrix.md`
- `new docs/16_lego_build_catalog.md`
- `new docs/17_actual_lego_registry.md`
- touched wiki pages only if concept framing materially changed

### Classical lane C1 — fallback or side-lane maintenance
Only if geometry workers stall or finish a wave cleanly:
- `qit_carnot_finite_time_companion`
- `qit_carnot_hold_policy_companion`
- `qit_szilard_record_companion`

These remain separate from geometry proof.

## 7. 8-hour wave design

The run should continue across waves until the budget is exhausted.

### Wave 1 (hours 0–1.5)
Run in parallel:
- Worker A: G1 Hopf map
- Worker B: G2 fiber equivalence
- Worker C: G3/G4 density refinement + chiral bookkeeping
- Worker D: M1 truth/maintenance closure once any one of A/B/C lands

### Wave 2 (hours 1.5–3)
Run in parallel:
- Worker E: G5 loop-law packet
- Worker F: G6 local operator action
- Worker G: G7 composition-order noncommutation
- Worker H: M1 maintenance closure

### Wave 3 (hours 3–4.5)
Run in parallel:
- Worker I: G8 transport/holonomy deepen
- Worker J: G9 graph shell deepen
- Worker K: G9 cell-complex deepen
- Worker L: G9 persistence deepen
- Worker M: M1 maintenance closure

### Wave 4 (hours 4.5–6)
If geometry is healthy:
- Worker N: G10 pre-Axis change-surface packet
- Worker O: second-pass density/chiral bookkeeping if still partial
- Worker P: second-pass operator/local-action packet if still partial
- Worker Q: M1 maintenance closure

### Wave 5 (hours 6–7)
If geometry is still healthy:
- take whichever of G1–G10 still remains partial and split it into the next bounded packet
- keep up to 4 geometry workers active plus 1 maintenance worker

### Wave 6 (hours 7–8)
If geometry packets are blocked or mostly landed for the night:
- activate classical side-lane workers on companion rows
- keep geometry maintenance worker alive in parallel

Possible side-lane workers:
- Carnot finite-time companion
- Carnot hold-policy companion
- Szilard record companion

## 8. Worker policy for a real overnight run

Every worker must be bounded, but the overall run is open-ended.

That means:
- the worker closes one packet
- then the controller decides the next packet
- then launches another worker
- repeat until time budget is exhausted

Each worker prompt must include:
1. exact read order
2. exact bounded target lego
3. allowed claims only
4. required rerun command
5. required audit commands
6. stop rules if the file is missing / wrong packet / process gap too large

## 9. Progress visibility and anti-stuck design

The overnight run must visibly prove that it is alive.

### Heartbeat cadence
- immediate launch heartbeat
- then heartbeat every 15 minutes
- if no material change, still report alive / healthy / blocked state

### Minimum heartbeat payload
- wall-clock time
- currently active workers
- current packets
- last successful result file(s)
- current health state: healthy / blocked / degraded
- whether truth / maintenance closure is caught up or lagging

### Anti-stuck rules
- if a worker fails twice on the same packet family:
  - stop retrying blindly
  - mark packet blocked for the night
  - move to the next packet family
- if a worker produces no result file path:
  - do not accept its claim
  - mark blocked and move on
- if a packet widens into axis / bridge / flux:
  - stop it
  - discard that widening from promotion logic
- if maintenance closure falls behind by 3 packets:
  - pause new geometry launches
  - run maintenance-only catch-up wave

## 10. What should count as a good 8-hour night

A good 8-hour run is not “it ran for 8 hours.”
A good 8-hour run means:
- multiple bounded packets closed
- truth rows updated conservatively
- audits kept passing
- no widening drift
- several partial rows moved to rerun-backed status

### Minimum acceptable overnight outcome
- at least 4 bounded packets closed honestly
- at least 2 of the Tier-1 missing geometry gaps land fresh rerun-backed rows
- at least 1 of the explicit density / loop / change-surface lanes from `system_v5` lands a rerun-backed row
- final `probe_truth_audit.py` passes
- final `controller_alignment_audit.py` passes

### Strong overnight outcome
- all Tier-1 geometry gaps are attempted
- at least 3 Tier-1 packets land rerun-backed rows
- at least 1 operator/transport packet lands
- at least 1 graph/cell/persistence deepen packet lands
- maintenance surfaces stay current enough that no morning reconciliation scramble is needed

## 11. First actual overnight launch recommendation

If launching now, the first controller wave should be:
- Lane G1: `hopf_map_s3_to_s2`
- Lane G2: `hopf_fiber_equivalence`
- Lane G3/G4: explicit density refinement + `chiral_density_bookkeeping`
- Lane M1: truth / maintenance closure

That is the correct center of the missing geometry.

## 12. What does NOT count as an 8-hour plan

These would be too small and are explicitly disallowed:
- one tiny fixed batch that clearly finishes in under 2 hours
- rerunning already-landed rows with no queue movement
- using “more sims” as a proxy for progress
- a plan with no heartbeat / progress visibility
- a plan with no anti-stuck behavior

## 13. Morning closeout requirements

By the end of the overnight run:
- identify exactly which packets closed
- list exact result paths touched
- list exact truth-label changes
- list exact blocked packets
- list next bounded move for the next run
- ensure final `probe_truth_audit.py` and `controller_alignment_audit.py` outputs are recorded
