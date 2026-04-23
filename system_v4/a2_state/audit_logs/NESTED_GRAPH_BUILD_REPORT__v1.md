# Nested Graph Build Report

- generated_utc: `2026-03-28T21:36:07Z`
- status: `built`
- layer_count: `6`
- total_nodes_across_layers: `11139`
- total_edges_across_layers: `22706`
- cross_layer_edge_count: `9135`
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
| QIT_ENGINE                |    105 |    272 |    4 |

## Cross-Layer Edges

- `A2_HIGH_INTAKE → A1_JARGONED`: 3639
- `A1_JARGONED → A2_HIGH_INTAKE`: 1048
- `A2_HIGH_INTAKE → A2_LOW_CONTROL`: 972
- `A2_LOW_CONTROL → A2_HIGH_INTAKE`: 848
- `A2_HIGH_INTAKE → A2_MID_REFINEMENT`: 653
- `A2_MID_REFINEMENT → A1_JARGONED`: 482
- `A2_LOW_CONTROL → A1_JARGONED`: 293
- `A2_MID_REFINEMENT → A2_HIGH_INTAKE`: 224
- `SIM_LAYER → B_LAYER`: 165
- `B_LAYER → A2_HIGH_INTAKE`: 136
- `SKILLS → A2_LOW_CONTROL`: 119
- `A2_MID_REFINEMENT → A2_LOW_CONTROL`: 109
- `GRAVEYARD → A2_HIGH_INTAKE`: 105
- `A1_JARGONED → A2_LOW_CONTROL`: 94
- `A2_LOW_CONTROL → A2_MID_REFINEMENT`: 79
- `GRAVEYARD → A2_MID_REFINEMENT`: 56
- `B_LAYER → A2_MID_REFINEMENT`: 30
- `GRAVEYARD → B_LAYER`: 20
- `TERM_LAYER → B_LAYER`: 20
- `B_LAYER → GRAVEYARD`: 17
- `A1_JARGONED → A2_MID_REFINEMENT`: 9
- `GRAVEYARD → A2_LOW_CONTROL`: 8
- `A2_LOW_CONTROL → QIT_ENGINE`: 5
- `B_LAYER → A2_LOW_CONTROL`: 2
- `GRAVEYARD → SKILLS`: 2
