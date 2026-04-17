---
title: Sim Build Spine and Wiki Maintenance
created: 2026-04-11
updated: 2026-04-15
type: concept
framing: current
tags: [simulation, planning, geometry, maintenance, wiki]
sources:
  - /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v5/new docs/plans/2026-04-11-sim-build-plan.md
  - /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v5/new docs/plans/wiki_ingest_and_lego_maintenance.md
  - raw/articles/new-docs/16_lego_build_catalog.md
  - raw/articles/new-docs/17_actual_lego_registry.md
  - raw/articles/system-v5-reference-docs/Weyl Flux.md
---

# Sim Build Spine and Wiki Maintenance

## Role in the live wiki cluster
- Strongest use: controller-facing bridge page for the geometry-manifold build spine and the bounded wiki/ledger closeout surfaces that must be repaired after a repo run changes evidence.
- Weak use: whole-wiki front door, substitute for `current/`, or substitute for the live repo queue/truth/tool/checklist surfaces themselves.
- Authority boundary: this page summarizes the geometry-spine dependency chain and the maintenance surfaces it tends to stale; it does not outrank `current/` for entry behavior, and it does not replace fresh repo artifacts when the question is the strongest safe current status label.

## Recommended reading order
1. `current/read-first.md` and the rest of the `current/` spine
2. `projects/codex-ratchet/read-first.md`
3. `system_v5/new docs/ENFORCEMENT_AND_PROCESS_RULES.md`
4. `system_v5/new docs/LLM_CONTROLLER_CONTRACT.md`
5. `system_v5/new docs/plans/2026-04-11-sim-build-plan.md`
6. `system_v5/new docs/plans/wiki_ingest_and_lego_maintenance.md`
7. this page when the task is specifically about geometry-before-axis build order or about which ledger/wiki surfaces must close after a bounded run
8. the live repo surfaces named below when the question is the actual current queue/truth/tool/maintenance state

## Core claim
The geometry-manifold lane is the spine of the build. The local geometry stack should be completed in detail before any axis work, then the admitted geometries can be layered, nested, and run on each other as the basis of a larger super-sim.

## Spine chain
1. density matrices on the admitted finite carrier
2. `S^3` spinor carrier
3. Hopf map `S^3 -> S^2`
4. Hopf fibers and nested Hopf tori
5. left/right Weyl spinors running on the nested Hopf tori
6. Pauli action on the left/right Weyl layer
7. connection, loop, and transport grammar
8. chirality/differential machinery
9. candidate flux family only as a derived downstream layer
10. only after that: stacking/coexistence and later bridge work
11. only after that: any axis work

## Maintenance rule
The lego ledgers and wiki pages must be living surfaces, not stale references.

There are two separate automation paths and they should not be collapsed:
- the sim runner builds or reruns probes, batches, and controller audits
- the wiki-builder path ingests repo/doc/result changes into the ledgers and `/Users/joshuaeisenhart/wiki`

Whenever new docs appear or sims change the honest status of a lego:
- update the grouped controller ledger in `16_lego_build_catalog.md`
- update the exhaustive registry in `17_actual_lego_registry.md`
- update the matching wiki concept pages

Current controller maintenance docs make this closure more explicit: after any bounded run, check the truth audit, tool-integration matrix, controller checklist, the two lego ledgers, and the touched wiki concept pages before calling the batch closed.

The cited backlog matrix also tightens the spine itself. In that summary, the geometry-manifold lane is not just a generic geometry stack; it is phased as root/carrier admission, same-carrier geometry, graph/topology geometry, operator/chirality/differential work, bipartite/correlation local work, then late/local entropy and bridge gates.

## Controller framing in the cited docs
The cited controller stack treats the build program as three coordinated lanes:
- Lane A: classical engine baseline work
- Lane B: geometry-manifold work as the spine
- Lane C: maintenance/control surfaces

In that framing, the geometry-manifold lane still outranks the others for build order. Engine progress does not authorize skipping local geometry work, and maintenance work is supposed to keep that discipline visible instead of letting old prose drift.

In controller terms, this page is the lane-specific companion to [[controller-state-transition-model]] and [[codex-ratchet-cs-bounded-system-framing]]: those pages explain the general bounded-transition protocol, while this page names the specific geometry-spine dependency chain that the queue is supposed to preserve.

Lane C also has a more explicit bounded closure set in the cited maintenance framing: the truth audit, tool-integration matrix, controller maintenance checklist, and Telegram runner surface are all recurring maintenance objects before the two lego ledgers and touched wiki pages can be considered closed.

## Public truth labels vs closeout detail
When this page summarizes repo state, keep the public controller contract primary:
- `exists`
- `runs`
- `passes local rerun`
- `canonical by process`

Do not silently substitute implementation-detail or closeout-only vocabulary for that public spine. If a checklist, validator, or maintenance script still uses extra terms or finer internal wording, name that explicitly as local implementation detail and translate back to the public four-label ladder in the wiki summary.

That matters here because this page often sits next to queue/maintenance prose. Queue progress, ledger repair, or a completed batch closeout does not by itself upgrade a lego's truth label; the live truth surface and the cited artifact still decide the strongest safe label.

## Current wiki-maintenance priority pages
- [[actual-lego-registry]]
- [[lego-build-catalog]]
- [[aligned-sim-backlog-and-build-order]]
- [[controller-state-transition-model]]
- geometry/chirality/flux pages touched by the active batch

The current maintenance docs also name recurring repo-side closure surfaces that often force wiki sync:
- `system_v5/new docs/plans/sim_truth_audit.md`
- `system_v5/new docs/plans/tool_integration_maintenance_matrix.md`
- `system_v5/new docs/plans/controller_maintenance_checklist.md`
- `system_v5/new docs/plans/wiki_ingest_and_lego_maintenance.md`

## Flux note
`flux` should remain an open derived candidate family sourced from the dependency chain in [[weyl-flux]] until the lower carrier/geometry/transport/chirality objects are complete and negatively tested.

## External support note
External support surfaces, including `hermes-agent-self-evolution`, `lev.here.now/constraints/`, and `lev-os/leviathan`, can be used as reference/method surfaces for workflow, maintenance, runtime-health, and controller ideas, but they do not outrank repo-local authority.
