# Four-Substage Dual-Product v0 Results

Status: `passes local rerun` as a `scratch_diagnostic` only.

Julia Canon and JAX independently recover four source-premised channel classes and the same one-coordinate product-square cycle.

- cells: `Ti=(z,pinch)`, `Fe=(z,unitary)`, `Fi=(x,unitary)`, `Te=(x,pinch)`
- cycle orientations: `Ti-Fe-Fi-Te-Ti` and `Ti-Te-Fi-Fe-Ti`
- one cycle modulo rotation and reversal
- erase either coordinate: two classes and no four-cell cycle
- remove a cell: no closed Hamiltonian cycle
- add y: six classes
- allow diagonal jumps: the cycle is no longer unique

The result is conditional on the source selecting exactly x/z and the two operator families, plus completeness and one-coordinate adjacency. It does not prove sequential substages in each of 16 stages, Axis-6 execution, personalities, perception, or useful engines.

## Parity Checks

- both_independent_runs_pass: `True`
- both_fenced_scratch: `True`
- four_measured_cells_agree: `True`
- parameter_variant_quotient_agrees: `True`
- core_graph_shape_agrees: `True`
- oriented_operator_cycles_agree: `True`
- one_unoriented_operator_cycle_agrees: `True`
- coordinate_erasure_agrees: `True`
- cell_removal_agrees: `True`
- diagonal_control_agrees: `True`
- y_axis_control_agrees: `True`
- julia_does_not_read_jax: `True`
- jax_does_not_read_julia: `True`
- premise_boundary_present: `True`

Generated: 2026-07-09T22:52:13Z
