# Builder Self-Assessment - gcm_geometry_attach_v0

Status after live rerun: source files authored, result JSONs generated, and validators passed for the first nested geometry-attachment packet.

Claim ceiling remains `scratch_diagnostic`, `promotion_allowed=false`, and `formal_admission_allowed=false`.

What this packet is meant to do:

- consume the frozen `gcm_object_id` registry by hash;
- attach 1Q `C^2`, `S^3`, Hopf projection, density quotient, loops, connection/curvature, and `T_eta` shell strata to the frozen survivor/class/region IDs;
- emit lineage maps from `survivor_id` to spinor coordinates, quotient class, density quotient, candidate region, and shell;
- run phase-quotient and carve-erasure controls;
- make `scripts/gcm_substrate_check.py` green for the real payload and red for a lineage-free variant;
- use the G.2a boundary helper from birth.

Builder status is not an audit verdict. No `audit_verdict.md` was written by the builder.

## Live Results

- Common packet: `ok=true`, result `system_v6/sims/gcm_geometry_attach_v0/results/gcm_geometry_attach_v0_results.json`.
- JAX lane: `ok=true`, result `system_v6/sims/gcm_geometry_attach_v0/results/gcm_geometry_attach_v0_jax_results.json`.
- PyTorch lane: `ok=true`, result `system_v6/sims/gcm_geometry_attach_v0/results/gcm_geometry_attach_v0_pytorch_results.json`.
- Julia lane: `ok=true`, result `system_v6/sims/gcm_geometry_attach_v0/results/gcm_geometry_attach_v0_julia_results.json`.
- Envelope: `ok=true`, result `system_v6/sims/gcm_geometry_attach_v0/results/gcm_geometry_attach_v0_envelope_results.json`.
- Packet validator: `ok=true`, errors `[]`.
- Strict three-engine validator: `ok=true`.
- Pytest: `4 passed`.

## Decisive Rows

- 16 frozen survivors attach to normalized spinors.
- 8 quotient classes survive as 8 density quotient states.
- occupied `T_eta` shells: `0`, `pi/8`, `pi/4`, `3pi/8`, `pi/2`.
- phase quotient preserves density/class/region/shell readouts but loses the S3 fiber coordinate.
- carve erasure leaves unanchored geometry feedstock and fails nested-substrate enforcement.
