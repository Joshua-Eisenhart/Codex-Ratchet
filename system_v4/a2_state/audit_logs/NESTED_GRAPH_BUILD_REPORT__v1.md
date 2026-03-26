# Nested Graph Build Report

- generated_utc: `2026-03-26T22:35:22Z`
- status: `built`
- layer_count: `6`
- total_nodes_across_layers: `11139`
- total_edges_across_layers: `22731`
- cross_layer_edge_count: `9084`
- toponetx_available: `False`
- toponetx_shape: `[]`
- pyg_available: `False`
- gudhi_available: `False`
- gudhi_betti_numbers: `[]`

## Layers

| Layer | Nodes | Edges | Rank |
|-------|-------|-------|------|
| A2_HIGH_INTAKE            |   8793 |  16279 |    0 |
| A2_MID_REFINEMENT         |    858 |   3029 |    1 |
| A2_LOW_CONTROL            |    667 |   1121 |    2 |
| A1_JARGONED               |    420 |   1288 |    3 |
| PROMOTED_SUBGRAPH         |    296 |    717 |   -1 |
| QIT_ENGINE                |    105 |    297 |    4 |

## Cross-Layer Edges

- `A2_HIGH_INTAKE → A1_JARGONED`: 3639
- `A1_JARGONED → A2_HIGH_INTAKE`: 1048
- `A2_HIGH_INTAKE → A2_LOW_CONTROL`: 773
- `A2_HIGH_INTAKE → A2_MID_REFINEMENT`: 606
- `A2_LOW_CONTROL → A2_HIGH_INTAKE`: 518
- `A2_MID_REFINEMENT → A1_JARGONED`: 471
- `PROMOTED_SUBGRAPH → A2_HIGH_INTAKE`: 369
- `A2_HIGH_INTAKE → PROMOTED_SUBGRAPH`: 246
- `A2_LOW_CONTROL → A1_JARGONED`: 213
- `A2_MID_REFINEMENT → A2_HIGH_INTAKE`: 185
- `SIM_LAYER → B_LAYER`: 165
- `B_LAYER → A2_HIGH_INTAKE`: 136
- `SKILLS → PROMOTED_SUBGRAPH`: 119
- `GRAVEYARD → A2_HIGH_INTAKE`: 105
- `PROMOTED_SUBGRAPH → A1_JARGONED`: 91
- `A1_JARGONED → A2_LOW_CONTROL`: 82
- `A2_MID_REFINEMENT → A2_LOW_CONTROL`: 53
- `A2_LOW_CONTROL → A2_MID_REFINEMENT`: 37
- `GRAVEYARD → PROMOTED_SUBGRAPH`: 32
- `GRAVEYARD → A2_MID_REFINEMENT`: 32
- `PROMOTED_SUBGRAPH → A2_LOW_CONTROL`: 29
- `B_LAYER → PROMOTED_SUBGRAPH`: 24
- `GRAVEYARD → B_LAYER`: 20
- `TERM_LAYER → B_LAYER`: 20
- `B_LAYER → GRAVEYARD`: 17
- `A1_JARGONED → PROMOTED_SUBGRAPH`: 13
- `A2_LOW_CONTROL → PROMOTED_SUBGRAPH`: 11
- `A1_JARGONED → A2_MID_REFINEMENT`: 8
- `B_LAYER → A2_MID_REFINEMENT`: 8
- `PROMOTED_SUBGRAPH → QIT_ENGINE`: 7
- `A2_MID_REFINEMENT → PROMOTED_SUBGRAPH`: 4
- `GRAVEYARD → SKILLS`: 2
- `PROMOTED_SUBGRAPH → A2_MID_REFINEMENT`: 1
