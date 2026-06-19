# basin_grid_refinement_control_v0

Status: builder packet only.
Ceiling: `scratch_diagnostic`, `promotion_allowed=false`, `formal_admission_allowed=false`.
Cost class: light-to-medium bounded finite graphs; no dense carriers.

## Goal

Close C1 from `basin_generating_set_sweep_v0`: decide whether the three G1
rotation terminal classes are invariant geometry or grid artifacts.

## Parents

- `basin_generating_set_sweep_v0`, committed parent `ba1bfc4d1`, supplies the
  three G1 rotation classes and carried CAVEAT C1.
- `basin_rc_transition_graph_v0`, committed parent `631f1c3db`, supplies the
  partition machinery.
- Basin contract parent `000f48e71`.

## Controls

- G1 anchor: rederive the committed 33-cell G1 partition byte-exact through the
  parent partition machinery.
- Grid refinement: recompute G1 on bounded 2x and 3x cell-density child grids:
  `66` and `99` cells.
- Rotated grid: recompute G1 on the same `33`-cell-density grid after a pinned
  non-axis rotation around `(1,1,1)` by angle `pi * (sqrt(2)-1)`.
- Continuous cross-check: compute the generated rotation-group closure and the
  continuum invariant decomposition.
- G0 dissipative control: recompute G0 on both refined grids and require one
  terminal class.
- Designed-fail artifact: axis-snapped fake class must die under the rotated
  grid.
- z3/cvc5 persistence identity with erased fate flip.

## Deliverables

- containment-based persistence correspondence for each committed G1 class;
- refined and rotated-grid class fates: `PERSIST`, `MERGE`, `SPLIT_FURTHER`, or
  `DISSOLVE`;
- finite-vs-continuum comparison with the h=`1/2` time-step role stated;
- real Julia Graphs/Z3 leg;
- JAX/Python and PyTorch legs with source-backed tool calls;
- envelope via `scripts/build_three_engine_envelope.py`;
- packet-local validator and generic source-backed validator green.
