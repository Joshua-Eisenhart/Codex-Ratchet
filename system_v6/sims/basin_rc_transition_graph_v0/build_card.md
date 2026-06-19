# basin_rc_transition_graph_v0

Status: builder packet only.
Ceiling: `scratch_diagnostic`, `promotion_allowed=false`, `formal_admission_allowed=false`.
Cost class: light bounded finite graph.

## Goal

Close the carried basin-pilot caveats by building the first explicit finite `R_C`
transition graph and basin partition for a bounded Bloch-ball discretization.

This packet is the named successor to `basin_criterion_pilot_v0`. It earns only
what the computed graph supports.

## Parents

- `basin_criterion_pilot_v0`, committed parent `4e082f525`, carries open caveats
  `G1`, `G4`, and `G5`.
- Basin contract receipt `50f16d82d`, with the 9 requirements and the
  clustering/model-agreement guard.
- `geo_s5_terrain_flows_v0` for committed terrain `A,b` rows.
- `geo_s4_operator_stage_v0` for committed operator channel rows.
- Disintegration/conditioning rule receipts for conditioned-shell membership.
- User build card hash: `28551e3f6`.

## Finite State

`S` is the 5-point Cartesian grid `{ -1, -1/2, 0, 1/2, 1 }^3` filtered by
`x^2 + y^2 + z^2 <= 1`. This yields 33 cells. `Adm_C` is the Bloch-ball
membership predicate. Conditioned-shell cells are flagged by
`z=1/2` and `x^2 + y^2 = 1/2`; the graph keeps all admitted cells and records
the shell flag per cell.

## Generator Set

Base `R_C` uses six declared generators:

- S5 terrains with `h=1/2`: `Se_Funnel_L`, `Ni_Pit_L`, `Ni_Source_R`,
  `Ne_Spiral_R`.
- S4 operators as one pinned channel application: `D_z`, `R_x`.

Each generator maps a cell by applying the committed affine row and then
quantizing to the nearest admitted cell with deterministic lexicographic tie
break. The semigroup is the closure under compositions of these generators,
computed through graph reachability.

With a generating set, `R_C` is a nondeterministic transition system. Basin-map
citations must therefore name which standard semantics they use:

- `can_reach_terminal`: existential/may reachability to the terminal closed
  class.
- `sure_basin_omega_containment`: universal/must omega-containment, where all
  generator choices remain forced into the terminal class.

Plain `B(A)` wording is not enough in this packet unless it also names the
semantics.

## Required Deliverables

- finite `S`, `Adm_C`, and conditioned-shell flags;
- explicit generator-labelled transition relation;
- SCC/communicating classes, closed terminal classes, absent-exit proof,
  metastable/almost-invariant and leaky classes;
- split basin map per terminal class (`can_reach_terminal` and
  `sure_basin_omega_containment`), boundary/separatrix cells, and Morse graph
  rows;
- trapping verification and monotone-exclusion observable, with direction
  convention stated as exclusion non-decreasing / reachable-set size
  non-increasing;
- escape tests and engine-DoF perturbation rows;
- seven negative controls, all firing;
- source-backed Julia, JAX/Python, and PyTorch lanes;
- `z3`, `cvc5`, and Julia `Z3.jl` no-exit proof with an erased flip;
- envelope via `scripts/build_three_engine_envelope.py`;
- packet-local validator green;
- no `audit_verdict.md`, no git add, no git commit.

## Honest Expected Outcome

The base generating set plausibly yields one terminal class at the origin. If
so, that is the result: a single terminal closed class plus split basin rows.
The expected may row can include all 33 cells, while the strict must/sure
omega-containment row may be only the terminal singleton. `CAVEAT-COARSE-33`
stays carried: the 33-cell grid earns the partition and controls, not refined
sub-basin claims. The refinement ladder is successor work.
