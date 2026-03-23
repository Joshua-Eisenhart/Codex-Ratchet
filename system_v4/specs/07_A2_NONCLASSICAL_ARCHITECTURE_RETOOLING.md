# V4 System Spec 07: Nonclassical Architecture Retooling

**Date:** 2026-03-22
**Status:** BINDING ARCHITECTURAL SPECIFICATION

## 1. The Nonclassical Law

The system must be rebuilt from the top down under strict nonclassical constraints, as recovered from the `MAX` thread extract (2026-03-17).

1. **No Preferred Truth:** The system maintains multiple live perspectives without forcing narrative collapse or premature flattening.
2. **Elimination Over Truth:** Constraints act as evolutionary pressure, eliminating paths rather than stamping them as "True".
3. **Graveyard is Active System Structure:** Dead-ends and rejected branches are not deleted; they form the boundaries of the attractor basin and define the classical/nonclassical divide.
4. **Entropy First:** Bounded context layers process correlation, mutual entropy, and structural diversity before domain logic.
5. **Graph as Control Substrate:** The graph is not a picture or a map—it is the direct mechanism of system routing, admission, and retention.

## 2. Empirical State of the Graphs (As of 2026-03-22)

Two massive analytical probes (`dotmotif_pattern_catalog` and `cross_graph_overlap_analyzer`) were run against the live A2 graphs (`A2_INTAKE`, `A2_REFINEMENT`, `A2_CONTROL`, and `PROMOTED`). The results demonstrate a **catastrophic breakdown in nonclassical graph execution:**

### A. Graph Connectivity Breakdown (Flow Failure)
The layers of A2 are entirely disconnected from each other:
- `A2_INTAKE` shares **0 nodes** with `A2_REFINEMENT`.
- `A2_REFINEMENT` shares **0 nodes** with `A2_CONTROL`.
- The `PROMOTED` subgraph is fundamentally detached from `A2_CONTROL` (missing 248 nodes), failing the essential `Promoted ⊆ Low-Control` invariant.

This broken topology explains why `A1_JARGONED` failed to materialize nodes locally: the Rosetta packets mapped upstream have no actual valid edges propagating downward through the strata.

### B. Severe Hub/Diamond Bottlenecking (Classical Collapse)
The motif catalog revealed rampant classical collapse into centralized points:
- **A2_CONTROL:** Contains `110,296` Diamond patterns and `305,316` Star hubs on only `419` nodes.
- **A2_INTAKE (500-node subsample):** Contains `246,926` Diamond patterns and `769,110` Star hubs.
This indicates the pipeline is structurally enforcing narrative collapse and chokepoints, entirely violating the "multiple pathways / no smoothing" rule.

## 3. Retooling Roadmap

To rectify the collapsed topology and implement the Nonclassical Law, the Phase 1–3 tools must be integrated directly into the `nested_graph_builder.py` pipeline.

### Step 1: Topological Ingestion (GUDHI & Leidenalg)
The current pipeline builds flat JSON dicts. It must be retrofitted to use `leidenalg` for identifying hierarchical graph-of-graphs clusters and `gudhi` to track persistent homology (uncovering persistent loops and holes instead of diamond bottlenecks).

### Step 2: Formal Verification of Strata (Hypothesis & Egg-smol)
The `A2_INTAKE → A2_REFINEMENT → A2_CONTROL` pipeline needs property-based testing across transformations. `egg-smol` (e-graph rewriting) will be used to verify that no node is lost between strata without an explicit graveyard deletion record.

### Step 3: Admission Gates (OPA/Conftest)
The `A1_JARGONED_GRAPH_BUILDER` is currently hardcoded to drop packets. We will refactor it to delegate to an Open Policy Agent (OPA) rule (`a1_admission.rego`) to test whether a packet mathematically qualifies for entry based on the nonclassical topology requirements.

### Step 4: Continuity Evidence (pycrdt & Phoenix)
To ensure the graveyard and active lineage remain intrinsically linked across threads without destructive overwrites, memory updates across A2 will migrate to Conflict-free Replicated Data Types (`pycrdt`).

## 4. Immediate Blockers for the A2→A1 Bridge

The A2→A1 Rosetta Bridge remains **status="BROKEN"** because `A2_CONTROL` lacks the nodes populated in `A2_REFINEMENT` and `PROMOTED`. 
**Resolution:** The graph merge tools must be rewritten to preserve the cross-layer edges derived in Step 1, rather than simply extracting subgraphs and breaking the lineage.
