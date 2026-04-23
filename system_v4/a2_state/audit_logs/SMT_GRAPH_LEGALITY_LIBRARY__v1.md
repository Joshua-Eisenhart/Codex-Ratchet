# SMT Graph Legality Library Report v1

- **generated_utc**: `2026-03-22T19:55:01Z`
- **data_source**: `a2_low_control_graph_v1.json`
- **node_count**: 419
- **edge_count**: 858

## Results Summary

| Formula | Z3 Status | cvc5 Status | Z3 Time (ms) | cvc5 Time (ms) |
|---------|-----------|-------------|--------------|---------------|
| 1_layer_membership | `SAT` | `SAT` | 18.35 | 10.30 |
| 2_edge_symmetry | `UNSAT` | `UNSAT` | 0.17 | 0.79 |
| 3_trust_monotonicity | `SAT` | `SAT` | 0.25 | 0.16 |
| 4_promotion_evidence | `UNSAT` | `UNSAT` | 0.08 | 0.07 |
| 5_no_orphan_clusters | `SAT` | `SAT` | 0.16 | 0.08 |
| 6_community_stability | `SAT` | `SAT` | 2.22 | 0.08 |
| 7_description_completeness | `SAT` | `SAT` | 0.20 | 0.12 |
| 8_rank_dependency | `SAT` | `SAT` | 0.18 | 0.12 |

- **Total Z3 Time**: 122.51 ms
- **Total cvc5 Time**: 18.75 ms

## Solver Agreement

- ✅ All solvers agree on all formulas.
