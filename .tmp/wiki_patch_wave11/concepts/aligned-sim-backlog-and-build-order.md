---
title: Aligned Sim Backlog and Build Order
created: 2026-04-07
updated: 2026-04-15
type: concept
framing: current
tags: [planning, simulation, validation, system]
sources:
  - raw/articles/new-docs/08_aligned_sim_backlog_and_build_order.md
  - raw/articles/new-docs/07_model_math_geometry_sim_plan.md
  - raw/articles/new-docs/05_research_index.md
  - /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v5/new docs/plans/2026-04-11-sim-build-plan.md
  - /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v5/new docs/plans/sim_backlog_matrix.md
---

# Aligned Sim Backlog and Build Order

## Role in the live wiki cluster
- Strongest use: queue-facing summary page for the current build order and lane split after the `current/` spine, project front door, and repo controller docs have already set entry behavior.
- Weak use: whole-wiki front door, substitute for `current/`, or substitute for the live repo queue/truth/maintenance surfaces when the question is the strongest safe current status label.
- Authority boundary: this page summarizes the ordering and lane discipline mirrored from repo-current planning docs; it does not outrank `current/` for entry behavior, and it does not replace fresh repo queue or artifact surfaces when the question is what is merely `exists`, what `runs`, what `passes local rerun`, or what is `canonical by process`.

## Recommended reading order
1. `current/read-first.md` and the rest of the `current/` spine
2. `projects/codex-ratchet/read-first.md`
3. `system_v5/new docs/ENFORCEMENT_AND_PROCESS_RULES.md`
4. `system_v5/new docs/LLM_CONTROLLER_CONTRACT.md`
5. `system_v5/new docs/plans/2026-04-11-sim-build-plan.md`
6. `system_v5/new docs/plans/sim_backlog_matrix.md`
7. this page when the task is specifically about the mirrored build order, lane split, or backlog-shaping logic
8. the live repo truth/tool/checklist surfaces when the question is the actual current queue closure state

## Purpose
This doc is the bridge from the L0 building blocks to the next simulations.

It pairs with [[model-math-geometry-sim-plan]] and [[stack-authority-and-capability-index]].

## Build-order snapshot
1. process repair, truth audit, and maintenance-surface upkeep
2. carrier and probe admissibility
3. same-carrier geometry packet as the spine
4. graph and topology geometry packet on that same admitted carrier
5. operator and channel admission
6. Weyl/chiral local packet
7. bipartite structure and correlation local packet
8. late/local entropy and bridge-gate work only after the lower packets are real
9. classical engine baseline cleanup/build as a coordinated side lane
10. bounded bridge work only after lower packets are real
11. axis work only after lower-layer admission

This is the ordering summarized from the cited controller docs, and it is stricter than the older five-step summary because it separates maintenance, same-carrier geometry, graph/topology work, chirality work, late entropy/bridge gates, and the classical engine lane.

## Lane split in the cited backlog matrix
- Lane A: classical engine baseline work
- Lane B: geometry-manifold work as the main spine
- Lane C: maintenance/control surfaces

The important rule in that matrix is that Lane A does not outrank Lane B. Engine work remains valuable, but geometry-before-axis and lower-local-before-bridge still control the queue.

The cited backlog matrix also makes Lane C more concrete than older summaries: truth audit, tool-integration maintenance, controller checklist/runner hygiene, lego-ledger upkeep, and wiki concept sync are all named queue surfaces rather than generic cleanup.

## Key separation rule
Do not collapse state representations, geometry families, entropy measures, operator families, or compression methods too early. They may align structurally, but they are not interchangeable by default.

Current controller docs add two more separation rules:
- do not collapse grouped-ledger status with result-truth labels
- do not treat one strong tool anchor as completion of a whole lane

## Public truth labels vs queue detail
When this page summarizes repo state, keep the public controller contract primary:
- `exists`
- `runs`
- `passes local rerun`
- `canonical by process`

Queue priority, backlog placement, or grouped-ledger progress do not by themselves upgrade a result above those labels. If a maintenance surface or backlog note uses finer queue wording, treat that as scheduling or closeout detail and translate back to the public four-label ladder in the wiki summary.

## Why it matters
The backlog keeps the work ordered from the constraint surface upward and prevents higher-level narrative from outrunning the evidence.

It also now functions as a maintenance surface: queue hygiene, truth audits, tool-role honesty, and wiki/ledger sync are part of the build order rather than after-the-fact cleanup.

The controller-facing bridge pages [[controller-state-transition-model]] and [[sim-build-spine-and-wiki-maintenance]] make that operational reading more explicit: this page names the ordering, while those pages explain how batches are supposed to move through the queue and which maintenance surfaces must be repaired before a run is honestly closed.

## Related pages
- [[controller-state-transition-model]]
- [[sim-build-spine-and-wiki-maintenance]]
- [[codex-ratchet-cs-bounded-system-framing]]
- [[constraint-on-distinguishability]]
- [[mass-equivalence-engine]]
- [[compression-to-density-matrix-map]]
- [[leviathan-system]]
- [[state-representation-views]]
- [[geometry-families-on-same-carrier]]
- [[entropy-and-information-families]]
- [[model-math-geometry-sim-plan]]
- [[aligned-sim-backlog-source-digest]]
