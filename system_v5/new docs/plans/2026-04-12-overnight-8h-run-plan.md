# 2026-04-12 Overnight 8h Run Plan

Status: OPEN-ENDED OVERNIGHT RUN PLAN — geometry-first, bottom-up lego work, high parallelism, bounded by controller rules rather than by a tiny fixed batch.

Purpose: define a real 8-hour overnight work program that can keep advancing legos across multiple waves, with many parallel lanes, while staying inside the actual controller/process rules.

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

## 1. Correct model of an 8-hour run

This should NOT be a tiny fixed list that finishes in 60–90 minutes.

An actual 8-hour run here should behave like this:
- keep pulling the next bounded lego packet from the live queue
- use many parallel lanes where file sets do not overlap
- close each packet with rerun + truth/audit + maintenance sync
- continue to the next packet if health remains good
- stop widening only when the queue reaches a real blocker or the run budget ends

So the overnight run is better understood as:
- one long controller session
- many bounded worker packets
- multiple successive waves
- geometry-first by default
- classical/QIT lane only as fallback or side lane once the geometry waves are healthy

## 2. Non-negotiable run rules

Hard rules:
- geometry-before-axis
- bottom-up lego work only
- no bridge/Axis widening
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

## 3. Current already-landed rerun-backed geometry from this session

These should not be the default first overnight targets unless they need process repair:
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

This matters because a real 8-hour run should spend most of its time on the still-partial or still-misaligned packets, not re-running already-landed rows for no queue gain.

## 4. Primary overnight objective

Advance as many still-partial geometry/chirality/operator legos as honestly possible, one bounded packet at a time, with continuous maintenance closure.

Primary target families:
- Hopf-map / fiber / connection packet
- chiral density bookkeeping packet
- local operator action packet
- local order-sensitivity packet
- graph/cell/persistence deepen packet

Secondary target family:
- classical Carnot/Szilard QIT-aligned companion rows, only after geometry waves are healthy or when geometry workers are blocked

## 5. Open-ended overnight lane inventory

### Geometry lane G1 — Hopf projection packet
Goal:
- `hopf_map_s3_to_s2`

Expected output:
- direct rerun-backed truth row for the explicit Hopf-map packet, not just generic Hopf geometry

Why it matters:
- still partial in the registry
- central to the missing projection/fiber packet

### Geometry lane G2 — fiber equivalence packet
Goal:
- `hopf_fiber_equivalence`

Expected output:
- direct density-invariance or fiber-equivalence row

Why it matters:
- still partial
- still hidden under broader Hopf results if not separated cleanly

### Geometry lane G3 — chiral bookkeeping packet
Goal:
- `chiral_density_bookkeeping`

Expected output:
- direct `rho_L`, `rho_R`, and joint bookkeeping packet

Why it matters:
- explicitly still open
- `weyl_nested_shell` does NOT close this gap by itself

### Geometry lane G4 — local operator action packet
Goal:
- `local_operator_action`

Expected output:
- direct primitive-operator-on-local-state packet below engine promotion

Why it matters:
- operator packet is still thinner than the geometry packet

### Geometry lane G5 — composition-order packet
Goal:
- `composition_order_noncommutation`

Expected output:
- direct local order-sensitivity row

Why it matters:
- still partial
- needed before later placement-law stories

### Geometry lane G6 — transport/holonomy deepen packet
Goal:
- `transport_geometry`
- `holonomy_geometry`

Expected output:
- stronger, more explicit packet built from the current Hopf-connection anchor

### Geometry lane G7 — graph/cell/persistence deepen packet
Goal:
- deepen already-rerun-backed but still partial graph/topology geometry
- `graph_shell_geometry`
- `cell_complex_geometry`
- `persistence_geometry`

Expected output:
- stronger tool-depth and cleaner ledger/truth separation for those rows

### Maintenance lane M1 — truth / tool / ledger sync
Goal:
- keep the controller surfaces honest after each geometry packet

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

## 6. 8-hour wave design

The run should continue across waves until the budget is exhausted.

### Wave 1 (hours 0–1.5)
Run in parallel:
- Worker A: G1 Hopf map
- Worker B: G2 fiber equivalence
- Worker C: G3 chiral bookkeeping
- Worker D: M1 truth/maintenance closure once any one of A/B/C lands

### Wave 2 (hours 1.5–3)
Run in parallel:
- Worker E: G4 local operator action
- Worker F: G5 composition-order noncommutation
- Worker G: G6 transport/holonomy deepen
- Worker H: M1 maintenance closure

### Wave 3 (hours 3–4.5)
Run in parallel:
- Worker I: graph shell deepen
- Worker J: cell-complex deepen
- Worker K: persistence deepen
- Worker L: M1 maintenance closure

### Wave 4 (hours 4.5–6)
If geometry is healthy:
- take whichever of G1–G7 still remains partial and split it into the next bounded packet
- keep up to 4 geometry workers active plus 1 maintenance worker

Examples:
- second-pass chiral bookkeeping
- second-pass local operator action
- channel-local action if operator packet broadens honestly
- graph/cell persistence tool-depth follow-on

### Wave 5 (hours 6–8)
If geometry packets are blocked or mostly landed for the night:
- activate classical side-lane workers on companion rows
- keep geometry maintenance worker alive in parallel

Possible side-lane workers:
- Carnot finite-time companion
- Carnot hold-policy companion
- Szilard record companion

## 7. Worker policy for a real overnight run

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

## 8. Progress visibility and anti-stuck design

The overnight run must visibly prove that it is alive.

### Heartbeat cadence
- immediate launch heartbeat
- then heartbeat every 15 minutes
- if no material change, still report alive/healthy/blocked state

### Minimum heartbeat payload
- wall-clock time
- currently active workers
- current packets
- last successful result file(s)
- current health state: healthy / blocked / degraded
- whether truth/maintenance closure is caught up or lagging

### Anti-stuck rules
- if a worker fails twice on the same packet family:
  - stop retrying blindly
  - mark packet blocked for the night
  - move to the next packet family
- if a worker produces no result file path:
  - do not accept its claim
  - mark blocked and move on
- if a packet widens into axis/bridge/flux:
  - stop it
  - discard that widening from promotion logic
- if maintenance closure falls behind by 3 packets:
  - pause new geometry launches
  - run maintenance-only catch-up wave

## 9. What should count as a good 8-hour night

A good 8-hour run is not “it ran for 8 hours.”
A good 8-hour run means:
- multiple bounded packets closed
- truth rows updated conservatively
- audits kept passing
- no widening drift
- several partial rows moved to rerun-backed status

### Minimum acceptable overnight outcome
- at least 4 bounded packets closed honestly
- at least 2 of the Tier-1 geometry gaps land fresh rerun-backed rows
- final `probe_truth_audit.py` passes
- final `controller_alignment_audit.py` passes

### Strong overnight outcome
- all Tier-1 geometry gaps attempted
- at least 3 Tier-1 packets land rerun-backed rows
- at least 1 operator/transport packet lands
- at least 1 graph/cell/persistence deepen packet lands
- maintenance surfaces stay current enough that no morning reconciliation scramble is needed

## 10. First actual overnight launch recommendation

If launching now, the first controller wave should be:
- Lane G1: `hopf_map_s3_to_s2`
- Lane G2: `hopf_fiber_equivalence`
- Lane G3: `chiral_density_bookkeeping`
- Lane M1: truth/maintenance closure

That is the correct center of missing geometry.

## 11. What does NOT count as an 8-hour plan

These would be too small and were the failure mode to avoid:
- one single fixed batch that clearly finishes in under 2 hours
- rerunning already-landed rows with no queue movement
- using “more sims” as a proxy for progress
- a plan with no heartbeat/progress visibility
- a plan with no anti-stuck behavior

## 12. Morning closeout requirements

By the end of the overnight run:
- identify exactly which packets closed
- list exact result paths touched
- list exact truth-label changes
- list exact blocked packets
- list next bounded move for the next run
- ensure final `probe_truth_audit.py` and `controller_alignment_audit.py` outputs are recorded
