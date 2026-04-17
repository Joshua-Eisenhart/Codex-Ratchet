---
title: Lego Build Catalog
created: 2026-04-10
updated: 2026-04-14
type: summary
tags: [reference, research, system, simulation, planning]
sources:
  - raw/articles/new-docs/16_lego_build_catalog.md
framing: current
---

# Lego Build Catalog

## Overview
This is the grouped maintenance ledger for the small sim legos. It is not a theory essay, not a raw sim dump, and not a bridge or axis plan. Its job is to say which local math legos exist, which ones are still thin, which tools are load-bearing, and which successor each lego should feed next.

The catalog sits in the current pre-Axis maintenance stack alongside [[lego-sim-contract]], [[current-preaxis-status-and-ordering-note]], and [[ladders-fences-admission-reference]]. It is the compressed operator-facing view of the lego program.

Under the current controller-facing framing, it is also a maintenance surface: when new docs land or reruns materially change the honest state of a lego, this grouped ledger should be patched together with the registry and the matching wiki concept pages.

## What it organizes
The ledger groups legos into the main local families:
- constraint and probe admissibility
- carrier admission and density-matrix representability
- geometry cross-checks on the same carrier
- operator-family admission
- graph / topology legos
- bipartite / information legos
- entropy cross-checks
- boundary falsifier legos

The important split is between a lego that is actually local and a surface that only looks local but is really a coupling, bridge, or assembly object.

## Status vocabulary
The catalog uses a small status vocabulary so the controller does not collapse distinct states:
- `covered`
- `partial`
- `needs_deeper_lego_work`
- `ready_for_pairwise`
- `blocked_from_assembly`

It also distinguishes queue state from lego status, so "ready now" is not confused with "safe for coexistence" or "blocked from assembly."

The surrounding controller docs also keep separate truth labels for concrete result files:
- `exists`
- `runs`
- `passes local rerun`
- `canonical by process`

Those truth labels are about result-file honesty, not grouped-ledger status.

## Tool pressure
This ledger makes tool pressure explicit instead of decorative. The main load-bearing surfaces are:
- `z3` and `cvc5` for constraint and impossibility pressure
- `geomstats` and `clifford` for geometry cross-checks
- `pyg`, `toponetx`, `xgi`, and `gudhi` for graph, cell-complex, hypergraph, and persistence surfaces
- `pytorch` and `sympy` for the core carrier and operator work

That matters because the catalog is not just naming objects; it is naming which tools must actually do work.

Recent maintenance surfaces sharpen three cautions:
- one strong tool anchor does not mean the full lane is complete
- geometry-before-axis remains the controlling order, even when graph, PyG, or engine-side anchors look strong
- `exists` anchors that have not been fresh-rerun should be described that way rather than being silently promoted

In particular, `state_class_binding_geometry` is represented in the maintenance ledger as a strong TopoNetX successor anchor and `werner_local_structure` as a stronger PyG/Werner local anchor, but neither closes the broader topology lane or the geometry spine by itself. The same ledger also carries `lego_weyl_hopf_spinor_bridge_results.json` as an added spinor/nested-torus geometry anchor and `lego_weyl_hypergraph_local_results.json` as an added Weyl-labelled hypergraph anchor; for honest wiki maintenance those should still be read as `exists` anchors unless a fresh rerun is cited.

The backlog framing adds another bounded maintenance reminder here: `partial_trace_operator` / `reduced_state_object` and `joint_density_matrix` / `correlation_tensor_object` should no longer be treated as invisible subcases of the bipartite bundle when maintenance surfaces are being repaired.

Another bounded maintenance reminder from the 2026-04-14 sim tranche: the grouped ledger includes artifact-side pressure from explicit F01/N01 micro-sims, deeper tool-native packets, gerbe-family steps, G-tower reductions, motives-family steps, and standalone Cl(3)/Cl(6) micro-sims. In this pass those packets should still be summarized as `exists` unless a fresh rerun is cited, but they are real bounded objects that later grouped-ledger rows can normalize rather than leaving them as pure doctrine or naming-only surfaces.

## Controller queue framing in this snapshot
The build plan in this snapshot splits work into:
- Lane A: classical engine baseline work
- Lane B: geometry-manifold work as the primary lane
- Lane C: maintenance/control surfaces

Within that framing, the grouped catalog mostly serves Lane B plus the maintenance closure that keeps Lane C honest.

See [[sim-build-spine-and-wiki-maintenance]] for the compact explanation of why the geometry lane is treated as the primary lane and why ledger/wiki sync is part of the same batch closeout rather than a separate optional documentation pass.

## Relationship to the registry
The grouped catalog is intentionally broader than the exhaustive registry. It compresses multiple concrete math objects into the smallest useful set of controller rows. When a grouped row becomes too broad, the registry should split it into separate rows.

See [[actual-lego-registry]] for the one-row-per-lego version.

## Related pages
- [[sim-build-spine-and-wiki-maintenance]]
- [[controller-state-transition-model]]
- [[actual-lego-registry]]
- [[llm-research-gap-matrix]]
- [[current-canonical-spine]]
- [[topic-map]]
- [[lego-sim-contract]]
- [[current-architecture-core]]
- [[current-preaxis-status-and-ordering-note]]
- [[ladders-fences-admission-reference]]
