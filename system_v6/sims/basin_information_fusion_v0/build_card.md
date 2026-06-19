# basin_information_fusion_v0

Status: builder packet only.
Ceiling: `scratch_diagnostic`, `promotion_allowed=false`, `formal_admission_allowed=false`.
Cost class: light bounded finite graph accounting over committed 33-cell rows.

## Goal

Fuse the committed basin transition partitions with the typed entropy ledger:
compute per-transition information accounting for G0-G5 generating-set moves,
including support/class deltas, may/must basin-size deltas, typed entropy
deltas, responsible generator differences, and committed flux/current rows
where scoped.

## Parents

- `basin_rc_transition_graph_v0`, committed parent `631f1c3db`.
- `basin_generating_set_sweep_v0`, committed parent `ba1bfc4d1`.
- `manifold_entropy_ledger_v0`, committed parent `a54224476`.
- `mct_dynamic_deformation_v0`, committed parent `cdf437053`.
- `manifold_information_throughput_v0` was untracked at build time, so the
  committed parent rows above are used directly.

## Deliverables

- Fusion table for `G0->G1`, `G1->G2`, `G2->G3L`, `G2->G3R`, `G2->G4`,
  `G2->G5`, and `G2->G2` null control.
- Synthesis row answering the basin-level information question:
  `G0->G1` gains `log(3)` nats of typed counting partition information.
- Re-merge conservation row for `G1->G2`: `log(3)=log(1)+log(3)`.
- Controls: byte-exact partition anchor, deliberate type-mixing flag, and null
  transition zero-delta row.
- z3/cvc5 plus Julia Z3 accounting identity with erased flips.
- Real Julia `Graphs`/`Z3` leg and Python/JAX-slot `networkx`/`sympy`/`z3`/`cvc5` leg.
- Envelope via `scripts/build_three_engine_envelope.py`, with PyTorch explicitly
  omitted because no graph/network/autograd claim path is scoped.

## Boundary

This packet quantifies information movement at the committed finite basin
partition level. It does not promote a basin theorem, geometric invariant
reading, continuum conservation law, bridge claim, or formal admission.
