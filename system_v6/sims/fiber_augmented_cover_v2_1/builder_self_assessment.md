# Builder Self-Assessment - fiber_augmented_cover_v2_1

Builder status: scratch diagnostic decisive-repair packet built at
`axis_readout_candidate_only + decisive_repair_cover_no_admission` ceiling.

What this packet does:

- Keeps the v2 CW base unchanged by hash.
- States the central repair explicitly: old shifts `[1,1,1,0]` have integer-lift
  sum `3` but mod-3 holonomy `0`; v2.1 is a different pinned construction with
  seam steps `[1,0,0,0]` and mod-3 holonomy `1`.
- Emits the guard-v3 control family: shifted repair, zero-shift product,
  wrong-gluing not-threaded, and old-v2-regression complexes.
- Hash-pins every emitted complex and verifies `d^2=0` for each.
- Records both invariants for every emitted complex: mod-3 holonomy and
  integer-lift sum.
- Recomputes Axis0, Axis3, and Axis6 faithfulness obligations on the v2.1 cover.
- Runs the third-construction `b6=-b0*b3` law table, eight sign variants,
  binomial p-values, SMT rows, and controls.
- Uses the G.2a builder/audit boundary helper from birth.

What this packet does not do:

- It does not compute Betti numbers or homology.
- It does not claim a lens-space certificate or SECOND certificate.
- It does not claim formal admission, canonical-by-process status, axis
  independence, bridge, physics, or manifold evidence.
- It does not reinterpret the old v1/v2 shifts as finite-nontrivial.

Known honest limitation:

The positive shifted complex is a builder-side guard input. The torsion-aware
homology adjudication belongs to guard v3, outside this packet. Until guard v3
runs, the ceiling stays `axis_readout_candidate_only`.
