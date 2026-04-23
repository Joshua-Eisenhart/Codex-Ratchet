---
title: Actual Lego Registry
created: 2026-04-10
updated: 2026-04-16
type: summary
tags: [reference, research, system, simulation, planning]
sources:
  - raw/articles/new-docs/17_actual_lego_registry.md
framing: current
---

# Actual Lego Registry

## Overview
This is the exhaustive one-row-per-lego registry. It is broader and more granular than [[lego-build-catalog]]. The registry is still active and still being completed, so it should be treated as a working ledger rather than a finished canon list.

The registry is the machine-facing expansion of the grouped catalog: where the catalog says "one row covers a family," the registry says "each concrete math object that deserves its own local simulation gets its own row."

## Registry families
The registry splits the lego space into explicit families:
- root and admission legos
- state representation legos
- compression and spectral legos
- geometry legos
- loop, connection, and placement legos
- operator and channel legos
- graph / topology legos
- bipartite and correlation legos
- entropy legos
- bridge, axis, and support legos
- boundary falsifier legos

That split matters because several bundled rows in the catalog hide separate objects that should eventually be tracked independently.

## Coverage states
The registry uses a few compact coverage labels:
- `covered`
- `partial`
- `not_normalized_yet`
- `blocked_as_late_surface`

Those labels are about ledger maturity, not canonical truth. A row can be useful even when it is still incomplete or blocked from early assembly.

Current controller docs also keep separate result-truth labels:
- `exists`
- `runs`
- `passes local rerun`
- `canonical by process`

The registry should not silently substitute those truth labels for coverage state.

## Why this registry exists
The registry makes the local math legos explicit enough that later coupling, coexistence, and boundary-pressure work can reference them without smuggling in bridge assumptions.

It is especially important for distinguishing:
- local carrier admission from later bridge objects
- operator legality from channel dynamics
- graph topology from cell-complex persistence
- entropy summaries from the lower-lego surfaces they depend on

## Relationship to the contract
Use this page together with [[lego-sim-contract]] so the ledger format and the sim contract stay aligned. The contract defines what a valid lego sim must declare; the registry defines which lego objects currently deserve separate rows.

## Current maintenance note
Recent registry-sync maintenance surfaces several notes that matter for the public summary:
- `state_class_binding_geometry` via `toponetx_state_class_binding_results.json` remains a strong inspected TopoNetX anchor
- `werner_local_structure` via `pyg_dynamic_edge_werner_results.json` remains a strong inspected PyG/Werner local anchor
- `spinor_geometry` has an alternate-carrier/nested-torus anchor in `lego_weyl_hopf_spinor_bridge_results.json`; until a fresh rerun is cited, that anchor should still be summarized conservatively as an `exists` surface rather than silently promoted
- `hypergraph_geometry` has a Weyl-labelled local companion entry in `lego_weyl_hypergraph_local_results.json`; that also belongs in the registry summary as an `exists` anchor until rerun evidence is cited
- `g_structure_tower` is a useful support-manifold baseline anchor at `passes local rerun`, but it remains below `canonical by process` because the artifact still self-classifies as `classical_baseline`
- the separate follow-on `gstructure_compatibility_coupling_results.json` is the bounded local follow-on artifact for the S³→S² Hopf-coupling claim; that does not collapse the whole G-structure tower lane into one finished theorem stack
- `partial_trace_operator` and `reduced_state_object` should be separated more explicitly in audits/docs instead of staying blurred together
- `joint_density_matrix` and `correlation_tensor_object` are still useful examples of rows that clearly belong in the registry even when they are not yet normalized cleanly into the stronger machine-routing surfaces

These notes do not replace the broader geometry spine, and they do not close the graph/topology lane or the geometry lane by themselves. They make the graph/topology, spinor/chirality, support-manifold, and bipartite/correlation lanes more concrete for immediate maintenance and rerun work.

Registry-sync maintenance also needs one process distinction stated explicitly: the automated sim runner and the wiki-builder path are separate. The sim runner produces or reruns bounded artifacts; the wiki-builder path ingests those honest status changes into the ledgers and `/Users/joshuaeisenhart/wiki`.

Result-truth terms should also stay aligned with the controller contract:
- `exists`
- `runs`
- `passes local rerun`
- `canonical by process`

The current backlog matrix sharpens the same point by explicitly calling the B20/B21 bipartite rows out as maintenance-sensitive surfaces rather than leaving them implicit inside the broader `bipartite_structure_local` bundle.

The 2026-04-14 sim tranche adds another registry-side reminder: explicit result artifacts are present for F01/N01 micro-sims, deeper tool-native packets, gerbe-family steps, G-tower reductions, motives-family steps, and standalone Cl(3)/Cl(6) micro-sims. In this maintenance pass those artifacts should still be summarized at `exists` unless a fresh rerun is cited, but they clearly belong to the registry-normalization queue rather than staying only as implicit repo math or stray probe files.

For the queue-and-closeout reading of why these registry updates matter, see [[controller-state-transition-model]] and [[sim-build-spine-and-wiki-maintenance]]. They make explicit that registry repairs are part of honest state transition closure, not just optional summary cleanup.

## Related pages
- [[sim-build-spine-and-wiki-maintenance]]
- [[controller-state-transition-model]]
- [[lego-build-catalog]]
- [[llm-research-gap-matrix]]
- [[current-canonical-spine]]
- [[topic-map]]
- [[lego-sim-contract]]
- [[current-architecture-core]]
- [[ladders-fences-admission-reference]]
- [[falsification-sim-designs]]
