# Builder Self-Assessment - gcm_constraint_carve_2q_v0

Status after live rerun: source files authored, result JSONs generated, and validators passed.

Claim ceiling remains `scratch_diagnostic`, `promotion_allowed=false`, and `formal_admission_allowed=false`.

Builder status is not an audit verdict. No `audit_verdict.md` was written by the builder.

## Intended Decisive Rows

- Coordinates: `layers 1-2 | carve (order B) | 2Q`.
- 2Q C1-C3 carve: `544` survivors, `8` quotient classes.
- Candidate family: product-grid + Bell-diagonal + purification-boundary.
- Cross-rung row: all `16` pinned 1Q survivors embed by product with the pinned control qubit, and the 2Q survivor partial-trace image equals the 1Q survivor set.
- Boundary row: entanglement enters the valid 2Q candidate space; Bell-diagonal entangled candidates are killed by local-probe C2, while purification-boundary entangled survivors remain because their partial trace is already a 1Q survivor.
- G.2a boundary uses `scripts/builder_audit_boundary.py` from birth.

## Live Results

- Common packet: `ok=true`, result `system_v6/sims/gcm_constraint_carve_2q_v0/results/gcm_constraint_carve_2q_v0_results.json`.
- JAX lane: `ok=true`, result `system_v6/sims/gcm_constraint_carve_2q_v0/results/gcm_constraint_carve_2q_v0_jax_results.json`.
- PyTorch lane: `ok=true`, result `system_v6/sims/gcm_constraint_carve_2q_v0/results/gcm_constraint_carve_2q_v0_pytorch_results.json`.
- Julia lane: `ok=true`, result `system_v6/sims/gcm_constraint_carve_2q_v0/results/gcm_constraint_carve_2q_v0_julia_results.json`.
- Envelope: `ok=true`, result `system_v6/sims/gcm_constraint_carve_2q_v0/results/gcm_constraint_carve_2q_v0_envelope_results.json`.
- Packet validator: `ok=true`, errors `[]`.
- Strict three-engine validator: `ok=true`.
- Pytest: `5 passed`.
