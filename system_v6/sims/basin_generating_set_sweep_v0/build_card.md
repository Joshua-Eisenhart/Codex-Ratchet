# basin_generating_set_sweep_v0

Status: builder packet only.
Ceiling: `scratch_diagnostic`, `promotion_allowed=false`, `formal_admission_allowed=false`.
Cost class: light bounded finite graph.

## Goal

Ratchet the active generating set on the committed 33-cell basin graph machinery
and ask whether the one-terminal-class baseline splits into computed sub-basin
structure.

## Parents

- `basin_rc_transition_graph_v0`, committed parent `631f1c3db`, supplies the
  33-cell carrier, generator-labelled graph machinery, and may/must basin
  semantics.
- Basin contract `000f48e71`, with extended basin vocabulary.
- Committed S4/S5 generator inventory from `geo_s4_operator_stage_v0` and
  `geo_s5_terrain_flows_v0`.

## Sweep Rows

- `G0`: committed six-generator baseline, re-derived as the byte-exact anchor.
- `G1`: rotations only: `R_x`, `R_z`, `Ne_Spiral_R`, `Ne_Vortex_L`.
- `G2`: full eight-terrain plus four-operator set.
- `G3L` and `G3R`: L-only and R-only terrain chirality subsets.
- `G4`: conditioned-shell restriction of the baseline generators, with `C`
  tightened before recomputing `M(C)`.
- `G5`: one composite generator, the word `Ni_Pit_L` then `R_x`, treated as a
  single move.

## Required Deliverables

- partition-fate table across the sweep rows;
- terminal-class counts, may/must basin sizes, metastable classes, and Morse
  rows where multiple classes exist;
- sub-basin answer with earn-the-term discipline;
- engine-DoF reading: the generating set is the active DoF choice;
- controls per set: similarity-cluster contrast and root-off contrast;
- G5 commutative-collapse contrast;
- z3/cvc5 partition identity checks with erased flips;
- real Julia Graphs.jl plus Z3.jl leg;
- parent lineage, capability receipts, tool calls, versions, and deterministic
  seed ledger;
- envelope via the canonical helper;
- packet-local validator green and generic source-backed validator green.

## Honest Expected Outcome

`G0` is expected to preserve the one-terminal-class anchor. A second terminal
closed class in any other row earns the first computed sub-basin structure only
for that row and only at this scratch ceiling. Rows that stay single-terminal
remain honest unitary results; they are not retroactively called split.
