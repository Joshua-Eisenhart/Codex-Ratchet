# DOTMOTIF STRUCTURAL PATTERN CATALOG — v1

> **Generated**: 2026-03-22T03:55 PDT  
> **Tool**: dotmotif 0.14.0 + NetworkXExecutor  
> **Probe**: `system_v4/probes/dotmotif_pattern_catalog.py`

## Methodology

Six structural motif patterns were defined in the dotmotif DSL and executed via subgraph isomorphism (NetworkXExecutor) against three system graphs. The `a2_high_intake_graph_v1.json` (8,793 nodes) was subsampled to 500 nodes via BFS from the highest-degree seed node.

### Motif Definitions

| # | Pattern | Description | DSL |
|---|---------|-------------|-----|
| 1 | Triangle | A→B→C→A | Cyclic dependency (3-cycle) |
| 2 | Star (hub-3) | A→B, A→C, A→D | Hub node with 3+ outgoing edges |
| 3 | Chain-of-3 | A→B→C | Two-hop dependency chain |
| 4 | Bidirectional | A→B, B→A | Mutual dependency |
| 5 | Fork | A→B, A→C | Branching from single node |
| 6 | Diamond | A→B, A→C, B→D, C→D | Converging paths through two intermediaries |

## Graph Summary

| Graph | Nodes | Edges | Notes |
|---|---:|---:|---|
| a2_low_control | 419 | 801 | Full graph |
| promoted_subgraph | 296 | 731 | Full graph |
| a2_high_intake_500 | 500 | 1,437 | BFS subsample of 8,793-node graph |

## Results

| Pattern | a2_low_control | promoted_subgraph | a2_high_intake_500 |
|---|---:|---:|---:|
| Triangle (A→B→C→A) | 1,356 | 42 | 18 |
| Star (hub-3: A→B,C,D) | 305,316 | 41,754 | 769,110 |
| Chain-of-3 (A→B→C) | 8,262 | 3,181 | 12,937 |
| Bidirectional (A↔B) | 104 | 0 | 6 |
| Fork (A→B, A→C) | 13,514 | 4,100 | 25,622 |
| Diamond (A→B,C→D) | 110,296 | 4,044 | 246,926 |
| **TOTAL** | **438,848** | **53,121** | **1,054,619** |

## Most Common Pattern

**Star (hub-3)** dominates across all three graphs:
- a2_low_control: 305,316 (69.6% of all motif instances)
- promoted_subgraph: 41,754 (78.6%)
- a2_high_intake_500: 769,110 (72.9%)

This indicates the graphs are heavily hub-concentrated — a small number of nodes serve as high-fan-out connectors.

## Flagged Surprises

### 🔴 Unexpected Cycles

| Graph | Triangle Count | Assessment |
|---|---:|---|
| a2_low_control | 1,356 | Significant — if intended as a DAG-like dependency graph, 1,356 three-cycles is a structural concern |
| promoted_subgraph | 42 | Minor — but cycles exist even in the promoted (curated) subgraph |
| a2_high_intake_500 | 18 | Low relative to size — consistent with intake being less structured |

### 🟡 Bidirectional (Mutual Dependencies)

| Graph | Count | % of Edges |
|---|---:|---|
| a2_low_control | 104 | 12.98% |
| promoted_subgraph | 0 | 0% |
| a2_high_intake_500 | 6 | 0.42% |

**Notable**: `promoted_subgraph` has **zero** bidirectional edges — the promotion pipeline successfully eliminates mutual dependencies. The low_control graph has 104 mutual pairs (≈13% of edges), which is unexpectedly high.

### 🟠 Extreme Star Concentration

All graphs show star counts dramatically exceeding node count (305K stars among 419 nodes in low_control). This means a few hub nodes have very high out-degree, each participating in combinatorially many 3-star instances. This is a sign of **scale-free** or **power-law degree distribution**.

### 🟡 Diamond Convergence Bottlenecks

| Graph | Diamond Count | Assessment |
|---|---:|---|
| a2_low_control | 110,296 | Very high — many converging paths create structural bottlenecks |
| a2_high_intake_500 | 246,926 | Highest absolute count — dense convergence in intake graph |
| promoted_subgraph | 4,044 | Lowest — promotion reduces structural fan-in |

## Key Structural Insights

1. **Hub dominance**: These are scale-free graphs with extreme hub concentration. Any hub node failure would cascade widely.
2. **Promotion cleans structure**: `promoted_subgraph` has fewer of every pattern type per-node, zero bidirectional edges, and far fewer diamonds — the promotion pipeline effectively prunes structural noise.
3. **Low_control has mutual dependency debt**: 104 bidirectional edge pairs (13% of edges) is a maintenance concern — these create tight coupling.
4. **Cycles exist everywhere**: Even the curated promoted graph contains 42 triangular cycles, suggesting some cyclic dependencies are intentional or unavoidable in the domain model.

## Execution Timing

| Pattern | a2_low_control | promoted_subgraph | a2_high_intake_500 |
|---|---:|---:|---:|
| Triangle | 0.406s | 0.125s | 0.144s |
| Star (hub-3) | 7.822s | 1.264s | 20.252s |
| Chain-of-3 | 0.365s | 0.096s | 0.475s |
| Bidirectional | 0.097s | 0.005s | 0.010s |
| Fork | 0.409s | 0.100s | 0.738s |
| Diamond | 3.405s | 0.261s | 7.513s |
