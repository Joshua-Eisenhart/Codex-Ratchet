# Builder Self-Assessment

sim: `gcm_connection_flux_attach_v0`
status: builder-side scratch diagnostic
ceiling: `scratch_diagnostic`, carrier-and-pins-relative, no admission claims

## What Was Built

This packet evaluates Hopf connection `A`, curvature `F=dA`, lifted holonomy `h(eta)`, occupied-shell flux rows, and leakage rows on the attached geometry produced by `gcm_geometry_attach_v0`.

The upstream geometry attach audit is in flight. This packet consumes its result by hash and keeps every claim conditional on that verdict.

## Seven Audit Questions

- Which layer? layers 10-12.
- Which nesting relation? integrated-onto-the-carve.
- Which qubit depth? 1Q.
- Which surface/network? attached survivor shell strata on the frozen GCM object, not a CA/QCA or ring-checkerboard runner.
- Which three engines ran? Julia, JAX, PyTorch.
- Which entropy/readout families varied? geometric curvature flux, Hopf holonomy, shell adjacency Stokes residual.
- What broke when removed? lineage-free substrate negative breaks anchoring; shell permutation changes the declared shell order; phase quotient loses vertical fiber anchoring while base flux rows remain.

## Builder Boundary

The builder did not write `audit_verdict.md`. Independent audit remains separate.

Disallowed claims: THE manifold, runtime/QIT flux, terrain admission, axis admission, physics admission, formal admission.
