# gcm_connection_flux_attach_v0 Build Card

status: builder packet, audit is in flight upstream
classification: scratch_diagnostic
ceiling: carrier-and-pins-relative, no admission claims
instruction boundary: NO git add/commit

## Coordinates

- layer coordinate: layers 10-12
- nesting coordinate: integrated-onto-the-carve
- qubit depth: 1Q

This is ladder step 4: `A, F=dA, holonomy, shell flux, leakage ON the attached geometry`.

## Authority And Lineage

- frozen substrate: `gcm_object_id_freeze_v0`
- `gcm_object_id`: `gcmobj_a40e54e13cec01466c9d675028b3574b`
- registry body hash: `0fddf60cea951e88ddde9cde6cb3e6c49ee36c77ae02dfe059d8550f2c6221ed`
- geometry authority: `gcm_geometry_attach_v0` RESULTS by hash; its audit is in flight, so this packet is conditional on its verdict
- formula feedstock: `geo_s2_connection_flux_foliation_v0`, reused for the S2/Hopf connection formulas and recomputed on the survivor loci

The payload consumes survivor, quotient-class, and candidate-region mappings through `scripts/gcm_substrate_check.py`. The lineage-free negative must fail red.

## Flux Fence

This packet computes geometric flux only: Hopf curvature flux from `A`, `F=dA`, holonomy, and shell annulus flux on the attached 1Q carrier. It is NEVER runtime/QIT flux, Hermes-runtime flux, memory flux, terrain/operator flux, or physics admission evidence.

## G.2a Boundary

G.2a is active from birth. The builder emits `builder_self_assessment.md`, not `audit_verdict.md`; `scripts/builder_audit_boundary.py` is load-bearing in the validator.
