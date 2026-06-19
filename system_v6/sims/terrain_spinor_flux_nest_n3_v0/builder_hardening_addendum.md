# Builder Hardening Addendum: terrain_spinor_flux_nest_n3_v0

Date: 2026-06-11
Ceiling: `scratch_diagnostic`
Promotion: `promotion_allowed: false`; `formal_admission_allowed: false`

## Closed In This Round

- G1 closed: the continuity proof is now an in-solver derivation over computed finite values. Z3, cvc5, and Julia-Z3 bind scaled edge-current formula rows, derive site divergence from edge-current variables, and prove the negated population-balance violation `unsat`. The erased one-unit balance target still flips to `sat`.
- G2 closed: the decoupling control now claims exact `z_dot` agreement with parent rows only. Full-row byte consistency is explicitly deprecated because parent and child rows have different schemas.

## Partially Closed And Carried

- G3 partially closed: the zero-terrain child network is now recomputed mechanically and checks zero couplings, zero currents, zero transport flux, and continuity. The remaining parent-row comparison is carried because no committed bare-network current row was found in the cited parents.
- G4 carried: the C^8 carrier is reconstructed from committed parent site spinors. It is not a copied parent state-vector row, and the packet records reconstruction hashes instead of claiming copied-row provenance.

## Boundaries

No n>3 claim, universal mirror law, bridge claim, axis claim, physics claim, manifold claim, promotion, or formal admission is supported by this addendum.
