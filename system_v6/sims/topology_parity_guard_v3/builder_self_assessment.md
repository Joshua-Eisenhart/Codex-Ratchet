# Builder Self-Assessment - topology_parity_guard_v3

## Scope

Built `topology_parity_guard_v3` as a file-disjoint, single-engine Python
consumer guard over `fiber_augmented_cover_v2_1`. The packet computes
torsion-aware homology from the four hash-pinned boundary-matrix complexes and
does not introduce new cells or update the work order.

## Boundary

- Classification remains `scratch_diagnostic`.
- Formal admission and promotion remain false.
- The result may adjudicate the two readings at consumer-guard ceiling only.
- G.2a is wired from birth through `topology_parity_guard_v3_boundary.py`,
  `validate_topology_parity_guard_v3.py`, and
  `scripts/builder_audit_boundary.py`.
- This file is not an audit verdict.

## Result Shape

- The shifted repair complex is expected to compute Betti `[1,0,0,1]` with
  `H1=Z/3`.
- The zero-shift, wrong-gluing, and old-v2 regression controls are expected to
  compute Betti `[1,1,1,1]` with no torsion.
- The boundary-matrix-only separability row is expected to find exactly two
  pure complexes: shifted `d2=[3]` and a shared zero-boundary control class.

## Self-Assessment

The packet is a scratch-diagnostic adjudicating consumer. It earns no formal
admission, topology admission, bridge, physics, manifold, axis closure, or
canonical-process claim.
