# FULL TOPOLOGY COMPARISON — v1
**Generated**: 2026-03-22T11:12:16Z
**Scope**: All graphs < 5000 nodes in `system_v4/a2_state/graphs/`
**Tool versions**: leidenalg 0.11.0, GUDHI 3.11.0, igraph 1.0.0

## 1. Graph Census and Persistence Homology (GUDHI)

| Graph | Nodes | Edges | β₀ (Components) | β₁ (Cycles) | H0 Stats | H1 Stats |
|-------|------:|------:|----------------:|------------:|----------|----------|
| **a1_jargoned_graph_v1** | 420 | 1120 | 75 | 0 | 420 total, max_life=1.0 | 58 total, max_life=2.0 |
| **a2_low_control_graph_v1** | 419 | 749 | 272 | 0 | 419 total, max_life=1.0 | 3 total, max_life=1.0 |
| **a2_mid_refinement_graph_v1** | 858 | 3011 | 547 | 0 | 858 total, max_life=1.0 | 2 total, max_life=1.0 |
| **enriched_a2_low_control_graph_v1** | 419 | 749 | 272 | 0 | 419 total, max_life=1.0 | 3 total, max_life=1.0 |
| **nested_graph_v1** | 0 | 0 | 0 | 0 | 0 total, max_life=0 | 0 total, max_life=0 |
| **promoted_subgraph** | 296 | 731 | 14 | 0 | 296 total, max_life=1.0 | 98 total, max_life=2.0 |
| **system_graph_v3_full_system_ingest_v1** | 1236 | 0 | 1236 | 0 | 0 total, max_life=0 | 0 total, max_life=0 |
| **system_graph_v3_ingest_pass1** | 298 | 133 | 202 | 0 | 298 total, max_life=1.0 | 2 total, max_life=1.0 |

## 2. Multi-Resolution Community Detection (leidenalg)

### a1_jargoned_graph_v1
| Res | Communities | Modularity (Q) | Top-5 Sizes |
|----:|------------:|---------------:|-------------|
| 0.1 | 76 | 0.6336 | [188, 47, 43, 20, 11] |
| 0.5 | 80 | 0.8047 | [86, 47, 43, 40, 39] |
| 1.0 | 81 | 0.8063 | [59, 47, 44, 40, 35] |
| 2.0 | 86 | 0.8006 | [35, 32, 31, 30, 27] |
| 5.0 | 105 | 0.6321 | [18, 17, 17, 17, 15] |

### a2_low_control_graph_v1
| Res | Communities | Modularity (Q) | Top-5 Sizes |
|----:|------------:|---------------:|-------------|
| 0.1 | 273 | 0.391 | [46, 16, 12, 10, 7] |
| 0.5 | 274 | 0.3927 | [44, 16, 12, 10, 7] |
| 1.0 | 277 | 0.395 | [40, 12, 10, 9, 7] |
| 2.0 | 304 | 0.2238 | [12, 10, 9, 7, 7] |
| 5.0 | 307 | 0.2179 | [12, 10, 9, 7, 7] |

### a2_mid_refinement_graph_v1
| Res | Communities | Modularity (Q) | Top-5 Sizes |
|----:|------------:|---------------:|-------------|
| 0.1 | 547 | 0.7431 | [50, 44, 43, 22, 20] |
| 0.5 | 548 | 0.7436 | [50, 44, 39, 22, 20] |
| 1.0 | 548 | 0.7436 | [50, 44, 39, 22, 20] |
| 2.0 | 549 | 0.743 | [48, 44, 39, 22, 20] |
| 5.0 | 634 | 0.3083 | [39, 22, 20, 13, 10] |

### enriched_a2_low_control_graph_v1
| Res | Communities | Modularity (Q) | Top-5 Sizes |
|----:|------------:|---------------:|-------------|
| 0.1 | 273 | 0.391 | [46, 16, 12, 10, 7] |
| 0.5 | 274 | 0.3927 | [44, 16, 12, 10, 7] |
| 1.0 | 277 | 0.395 | [40, 12, 10, 9, 7] |
| 2.0 | 304 | 0.2238 | [12, 10, 9, 7, 7] |
| 5.0 | 307 | 0.2179 | [12, 10, 9, 7, 7] |

### nested_graph_v1
| Res | Communities | Modularity (Q) | Top-5 Sizes |
|----:|------------:|---------------:|-------------|
| 0.1 | 0 | 0 | [] |
| 0.5 | 0 | 0 | [] |
| 1.0 | 0 | 0 | [] |
| 2.0 | 0 | 0 | [] |
| 5.0 | 0 | 0 | [] |

### promoted_subgraph
| Res | Communities | Modularity (Q) | Top-5 Sizes |
|----:|------------:|---------------:|-------------|
| 0.1 | 15 | 0.3228 | [200, 65, 5, 3, 3] |
| 0.5 | 22 | 0.6167 | [87, 65, 35, 27, 17] |
| 1.0 | 24 | 0.6535 | [64, 44, 34, 33, 27] |
| 2.0 | 32 | 0.6254 | [64, 28, 22, 18, 15] |
| 5.0 | 44 | 0.5635 | [64, 16, 12, 11, 10] |

### system_graph_v3_full_system_ingest_v1
| Res | Communities | Modularity (Q) | Top-5 Sizes |
|----:|------------:|---------------:|-------------|
| 0.1 | 1236 | 0 | [1, 1, 1, 1, 1] |
| 0.5 | 1236 | 0 | [1, 1, 1, 1, 1] |
| 1.0 | 1236 | 0 | [1, 1, 1, 1, 1] |
| 2.0 | 1236 | 0 | [1, 1, 1, 1, 1] |
| 5.0 | 1236 | 0 | [1, 1, 1, 1, 1] |

### system_graph_v3_ingest_pass1
| Res | Communities | Modularity (Q) | Top-5 Sizes |
|----:|------------:|---------------:|-------------|
| 0.1 | 203 | 0.625 | [43, 31, 9, 6, 5] |
| 0.5 | 208 | 0.7266 | [25, 19, 9, 9, 9] |
| 1.0 | 209 | 0.7354 | [18, 16, 11, 9, 9] |
| 2.0 | 214 | 0.7152 | [10, 9, 9, 9, 8] |
| 5.0 | 219 | 0.6479 | [9, 6, 6, 5, 5] |
