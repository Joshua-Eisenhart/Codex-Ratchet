# Builder Self-Assessment - gcm_object_id_freeze_v0

Status: builder assessment only, not an audit verdict.

## Boundary

- Claim ceiling remains `scratch_diagnostic`: first candidate substrate ID registry, carrier-and-pins-relative, not THE manifold.
- The registry consumes `gcm_constraint_carve_v1` by source/result hashes and does not recompute or strengthen the carve claim.
- G.2a is wired from birth through `gcm_object_id_freeze_v0_boundary.py` and `scripts/builder_audit_boundary.py`.

## Controls

- Stale registry control mutates a carve result hash in scratch and `gcm_substrate_check(payload)` fails.
- Unknown object control cites an unknown frozen survivor ID and `gcm_substrate_check(payload)` fails.
- Future nested packets must cite the frozen `gcm_object_id` and map objects to registry IDs.
