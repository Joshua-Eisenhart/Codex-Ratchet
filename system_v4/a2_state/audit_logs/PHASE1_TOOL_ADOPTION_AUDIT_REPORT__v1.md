# Phase 1+2 Tool Adoption — Combined Audit Report
Date: 2026-03-22
Status: COMPLETE — 7 PASS, 2 PARTIAL, 1 FAIL (API docs mismatch, not fundamental)

## Environment
- **Python**: 3.13.6 (arm64 macOS)
- **venv**: `.venv_spec_graph`
- **base stack preserved**: pydantic 2.12.5, networkx 3.6.1, torch 2.10.0

## All Packages Installed

### Phase 1 (11 packages)
| Package | Version | Tested | Status |
|---------|---------|--------|--------|
| hypothesis | 6.151.9 | ✅ | property tests 4/4 pass |
| hypofuzz | 25.11.1 | installed | ready for extended fuzzing |
| gudhi | 3.11.0 | ✅ | Betti [206,0] on low-control graph |
| leidenalg | 0.11.0 | ✅ | 276 communities, modularity 0.395 |
| igraph | 1.0.0 | ✅ | pre-existing, works |
| dotmotif | 0.14.0 | ✅ | 3181 chain motifs on promoted subgraph |
| mutmut | 3.5.0 | ⚠️ | v3 CLI syntax changed; needs adaptation |
| cosmic-ray | 8.4.4 | installed | ready |
| pysmt | 0.9.6 | ✅ | solver-agnostic formulas work |
| cvc5 | 1.3.3 | ✅ | QF_LIA tree constraint SAT |
| pyRankMCDA | 2.1.5 | ⚠️ | loads but API needs investigation |
| egg-smol | — | ❌ | Rust/maturin build fails on Python 3.13 |

### Phase 2 (3 packages + transitive)
| Package | Version | Tested | Status |
|---------|---------|--------|--------|
| egglog | 13.0.1 | ❌ | v13 API different from docs; EGraph creates but rules harder than expected |
| crosshair-tool | 0.0.102 | ⚠️ | CLI runs but NetworkX internals fail under symbolic execution |
| dvc | 3.67.0 | ✅ | version confirmed, ready for experiment tracking |
| z3-solver | 4.16.0 | transitive | available as PySMT backend |
| diskcache | 5.6.3 | transitive | available for graph caching |

## Experiment Results (all on real repo data)

### PASS (7)

| # | Experiment | Key Finding |
|---|-----------|-------------|
| 1 | **GUDHI persistence** | β₀=206, β₁=0 on 300-node subgraph. Highly fragmented: 206 connected components. No topological loops at radius 4. |
| 2 | **leidenalg communities** | 276 communities in 419-node/749-edge graph. Modularity 0.395. Largest cluster: 40 nodes (likely kernel concepts). |
| 3 | **dotmotif motifs** | 3,181 A→B→C chains in promoted subgraph (296 nodes, 731 edges). Dense multi-hop dependency structure. |
| 4 | **Hypothesis domain invariants** | 4/4 pass: (1) kernel nodes have admissibility_state, (2) refined nodes have authority, (3) no empty descriptions, (4) all edges have relation type |
| 5 | **PySMT formula** | `promoted → has_3_edges` satisfiable. Violation also satisfiable (invariant CAN be broken — real data check needed). |
| 6 | **cvc5 constraint** | Tree constraint `edges = nodes - 1` is SAT. Model: node_count=1, edge_count=0. |
| 7 | **DVC version** | DVC 3.67.0 available. Ready for `dvc init` and experiment tracking. |

### PARTIAL (2)

| # | Experiment | Issue | Next Step |
|---|-----------|-------|-----------|
| 1 | **mutmut** | v3 removed `--paths-to-mutate` flag. New CLI syntax. | Check `mutmut run --help`, adapt command |
| 2 | **pyRankMCDA** | Module loads but TOPSIS not directly accessible. Has `rank_aggregation` class. | Study `rank_aggregation` constructor, or use numpy TOPSIS directly |

### FAIL (1)

| # | Experiment | Issue | Fallback |
|---|-----------|-------|----------|
| 1 | **egglog** | v13 API changed significantly from documentation. `run_program` removed. Python DSL syntax differs from examples. | Study v13 tutorials. Core EGraph works; rule syntax needs learning. |

## Graph Format Discovery

Project graphs use custom JSON (NOT NetworkX `node_link_data`):
```python
# nodes: dict keyed by ID
# edges: list with source_id/target_id keys
G = nx.Graph()
for nid in data['nodes']: G.add_node(nid, **data['nodes'][nid])
for e in data['edges']: G.add_edge(e['source_id'], e['target_id'])
```

## Guardrails Respected
- ❌ No memory platform installed
- ❌ No framework imports (no LangGraph, Temporal, Airflow)
- ❌ No base graph stack replacement
- ❌ No speculative refactors
- ✅ All tools installed as sidecars only

## Next Recommended Tranche (Phase 3)

1. **Write pytest tests** for `nested_graph_builder.py` and `control_graph_bridge_gap_auditor.py` → then run mutmut
2. **Hypothesis on promoted subgraph**: "every promoted 2-cell has all boundary edges"
3. **DVC init** in repo → track graph artifact versions
4. **leidenalg on larger graphs**: `a2_high_intake_graph` (19MB), `system_graph_a2_refinery` (47MB)
5. **GUDHI comparison**: persistence on low-control vs promoted subgraph — do they have different topology?
6. **PySMT + Z3 + cvc5 cross-solver check**: same formula, both solvers, compare models
7. **Study egglog v13 API**: use `register` + `run` + `check` pattern from actual v13 docs
8. **Evaluate OPA/Conftest** for graph artifact policy checking
