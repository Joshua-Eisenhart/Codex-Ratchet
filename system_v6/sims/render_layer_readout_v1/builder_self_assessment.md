# Builder Self-Assessment - render_layer_readout_v1

Builder verdict: useful scratch diagnostic candidate, not an audit verdict.

## What This Builds

`render_layer_readout_v1` re-pins the render polarity after v0's
by-construction degeneracy. The new pin is a signed projection of the committed
render correction onto the committed source-to-render direction. The packet
requires both `reshape_the_render` and `resist_the_update` to be reachable on
real committed dynamics before any readout table runs.

## Boundary

- `classification=scratch_diagnostic`
- `promotion_allowed=false`
- `formal_admission_allowed=false`
- No holodeck, FEP, physics, Axis-0 admission, bridge, manifold, or formal
  promotion claim.
- G.2a is handled from birth by `render_layer_readout_v1_boundary.py` calling
  `scripts/builder_audit_boundary.py`.

## Self-Checks

- v0 distance pin is retained only as a killed regression.
- Scrambled-error must break the v1 nonconstant readout.
- Identity-dynamics degeneracy and no-identity-leak controls are recorded.
- Three-engine envelope is scoped to a scratch render-layer readout candidate.

## Known Limits

JAX/PyTorch lanes share the Python common core; Julia mirrors the formula from
the committed carrier result. This is cross-runtime consistency evidence, not
independent proof or admission.
