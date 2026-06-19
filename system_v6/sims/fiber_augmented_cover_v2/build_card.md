# BUILD CARD - fiber_augmented_cover_v2

Source request: build `fiber_augmented_cover_v2` under
`system_v6/sims/fiber_augmented_cover_v2/`, file-disjoint, with no `git add`
or commit.

## Ceiling

- `classification=scratch_diagnostic`
- `claim_ceiling=axis_readout_candidate_only + cellular_cover_law_test_v2_no_admission`
- `promotion_allowed=false`
- `formal_admission_allowed=false`
- NO Betti in this packet. The packet emits chain complexes for a later guard
  consumer only.
- Boundary helper: `fiber_augmented_cover_v2_boundary.py` plus
  `scripts/builder_audit_boundary.py`.
- G.2a from birth: validators/tests delegate audit-file handling to the shared
  helper and do not require permanent absence of `audit_verdict.md`.

## Authority Read Order

1. `fiber_cover_incidence_structure_v0` at `a04f76e1a`: honest block says the
   committed 33-cell adjacency is a dense graph, not a surface mesh. Base Euler
   was `-153`; only 12 derivable 2-cells were available; a source-side committed
   cellular structure is required.
2. `fiber_augmented_cover_v1` plus audit at `80860aa4f`: carries `|F|=3`,
   degree-1 clutching, lifted winding witness gate, axis faithfulness
   obligations, law table, controls, and the v1 comparison row.
3. `topology_parity_cell_model_v1` plus audit at `0207fecaf`: rejected because
   its load-bearing cellular model was packet-introduced to fit topology.
4. `system_v6/receipts/audit_standards_codex_v1.md`: G.2a and standards codex
   bind from birth.

## Cellular Base

The v2 construction commits its own cellular sphere:

- `C0=33` vertices, labelled by the existing v1/base cell ids for axis
  projection.
- `C1=92` cellular edges.
- `C2=61` committed faces: south pole cap triangles, band quads/triangles, and
  north pole cap triangles.
- Euler gate: `33 - 92 + 61 = 2`.
- Every cellular edge is incident to exactly two faces.

This cellular adjacency is the v2 surface structure. The v1 dense graph remains
valid as a distinguishability/generator transition graph, but it is not the
surface mesh. Both objects remain valid with different roles.

## Fiber Augmentation

The packet applies the v1 finite-fiber machinery to the cellular base:

- `|F|=3`.
- committed seam loop: `20 -> 17 -> 12 -> 15 -> 20`.
- lifted clutching steps: `[1, 1, 1, 0]`.
- winding witness: `3 / 3 = 1`.
- zero-shift v2 cover computes witness `0` and refuses law rows.

The total-space cellular structure emits product cells plus gluing rows:

- `C0=99`
- `C1=375`
- `C2=459`
- `C3=183`
- `d^2=0` is verified and boundary matrices are hash-pinned.

## Witness Gates

The packet refuses law rows unless all construction gates pass:

- `chi(base)=2`
- winding/full-turn witness is `+/-1`
- total-space chain complex has `d^2=0`

## Axis Realizations And Law Table

- Axis0 is pulled back through the projection to committed v1/base Axis0 rows.
- Axis6 is pulled back through the projection to committed v1/base Axis6 rows.
- Axis3 is computed natively on pinned finite fiber phases using the committed
  `gamma_in` / `gamma_out` predicates.
- The law row is `b6 = -b0*b3`, with all eight sign variants and binomial
  p-values.
- The v1 result `46/99` at-chance is carried only as a comparison row.

## Controls

- zero-shift v2 cover: winding `0`, law table refused.
- scrambled b6 control.
- convention-flip control.
- v1 comparison row.

## Boundaries

Allowed claims:

- v2 commits a cellular sphere carrier from construction data.
- v2 computes a degree-1 finite fiber cover on that carrier.
- v2 emits chain complexes for a guard v2 consumer.
- v2 runs the b6 law table at scratch-diagnostic ceiling.

Disallowed claims:

- Betti computation;
- homology certificate;
- S3 or S2xS1 topology claim;
- formal admission;
- canonical by process;
- axis independence proof;
- bridge, physics, manifold, or axis-level closure;
- global disproof of the b6 law.

## Expected Commands

```bash
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/fiber_augmented_cover_v2/fiber_augmented_cover_v2.py
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/fiber_augmented_cover_v2/fiber_augmented_cover_v2_envelope.py
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/fiber_augmented_cover_v2/validate_fiber_augmented_cover_v2.py
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 -m pytest -q system_v6/sims/fiber_augmented_cover_v2/tests
```
