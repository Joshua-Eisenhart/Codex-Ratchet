# geo_s1_q3_finite_incidence_v0

Builder lane for the q=3 follow-up to the committed finite twistor incidence packet and finite lens tower.

Scope:
- Build exact `PG(3,3)` projective incidence under the `F_3^4 / F_3^*` quotient.
- Check points `40`, lines `130`, planes `40`, pair-line uniqueness, and line-intersection graph invariants.
- Add the `Z_3` lens quotient `L(3,1)` phase-resolution probe row on the committed finite lens-tower shape.
- Compare the q=3 twistor-candidate incidence behavior against the committed q=2 packet.

Mode and ceiling:
- Mode: `julia_canon_plus_jax_diagnostic`, mirroring `twistor_incidence_finite_packet_v0`.
- Classification: `scratch_diagnostic`.
- `promotion_allowed=false`.
- `formal_admission_allowed=false`.
- No physics, spacetime, GR, canonical, or Penrose-validation claim.

Done criterion:
- JAX/galois leg and Julia/mod-3 leg both run without peer-result reads.
- Envelope compares like-for-like values with zero divergence on shared observables.
- `scripts/validate_three_engine_sim_result.py` accepts the two-engine declared envelope.

Audit boundary:
- This is builder output only. A fresh audit verdict is intentionally not included; builder self-check is not evidence.
