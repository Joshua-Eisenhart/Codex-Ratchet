# Builder Self-Assessment - gcm_constraint_carve_v1

Status after live rerun: source files authored, result JSONs generated, and validators passed.

Claim ceiling remains `scratch_diagnostic`, `promotion_allowed=false`, and `formal_admission_allowed=false`.

What this packet is meant to fix:

- C4 is split out of the active admissibility carve.
- C2 is explicitly demoted to a local adapter pin for the exact x/z probe and zero-active-class exclusion.
- No-identity-leak independence fields are emitted.
- Terrain readout is post-carve only and cannot affect survival.
- G.2a boundary uses `scripts/builder_audit_boundary.py` from birth.

Builder status is not an audit verdict. No `audit_verdict.md` was written by the builder.

## Live Results

- Common packet: `ok=true`, result `system_v6/sims/gcm_constraint_carve_v1/results/gcm_constraint_carve_v1_results.json`.
- JAX lane: `ok=true`, result `system_v6/sims/gcm_constraint_carve_v1/results/gcm_constraint_carve_v1_jax_results.json`.
- PyTorch lane: `ok=true`, result `system_v6/sims/gcm_constraint_carve_v1/results/gcm_constraint_carve_v1_pytorch_results.json`.
- Julia lane: `ok=true`, result `system_v6/sims/gcm_constraint_carve_v1/results/gcm_constraint_carve_v1_julia_results.json`.
- Envelope: `ok=true`, result `system_v6/sims/gcm_constraint_carve_v1/results/gcm_constraint_carve_v1_envelope_results.json`.
- Packet validator: `ok=true`, errors `[]`.
- Strict three-engine validator: `ok=true`.
- Pytest: `5 passed`.

## Decisive v1 Rows

- v1 blind C1-C3 carve: 16 survivors, 8 quotient classes.
- rejected v0 C4 regression: 8 survivors, 4 quotient classes.
- removed by rejected v0 C4: `[31, 33, 41, 43, 81, 83, 91, 93]`.
- active predicate forbidden-token hits: none.
- injected terrain-framed variant: caught.
- no-identity-leak fields emitted with `identity_leak_detected=true` and `identity_leak_excluded_best_accuracy=0.968`.
