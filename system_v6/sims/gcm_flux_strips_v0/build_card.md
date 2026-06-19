# Build Card - `gcm_flux_strips_v0`

Bottom line: deepen the landed geometric-flux packet by computing every increasing occupied-shell strip, not only adjacent rows.

## Authority

- `5afa1ea53`: landed `gcm_connection_flux_attach_v0`, with audit caveat G2 noting stale conditionality metadata and thin leakage rows.
- `748fca97c`: landed `gcm_geometry_attach_v0` as `GENUINE-WITH-CAVEATS`; this packet treats the attach/geometry condition as resolved, not `in_flight`.
- `system_v6/sims/gcm_connection_flux_attach_v0/results/gcm_connection_flux_attach_v0_results.json`: source lineage, shell occupancy, formulas, and geometric-flux-only fence.

## Task

Compute the complete strip table over occupied shells:

```text
eta in {0, pi/8, pi/4, 3pi/8, pi/2}
all increasing ordered pairs (i,j), i < j: 10 strips
```

For each strip:

- compute boundary holonomy difference `h(eta_j)-h(eta_i)`;
- compute curvature integral `int F` over the eta strip and chi cycle;
- verify Stokes orientation closure: `h_delta + int_F = 0`;
- report the v0 "leakage" row as a per-strip closure adjudication.

## Contract

- classification: `scratch_diagnostic`
- claim ceiling: `scratch_diagnostic_layers_10_12_1Q_complete_geometric_flux_strip_table`
- layer declaration: `layers 10-12 | integrated | 1Q`
- substrate: positive `gcm_substrate_check` must pass against frozen lineage, and lineage-free negative must fail.
- flux fence: geometric Hopf curvature flux only; no runtime/QIT/chirality/memory/terrain/physics admission.

