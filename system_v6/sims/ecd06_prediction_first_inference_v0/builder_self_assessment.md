# Builder Self-Assessment - ecd06_prediction_first_inference_v0

Status: builder self-assessment only; not an independent audit.

## What Was Built

`ecd06_prediction_first_inference_v0` builds the prediction-first discriminator fed by `render_layer_readout_v1`. It compares the searched QIT render-gain family against searched fair classical predictors using a typed prediction-error metric over the committed v1 edge family.

## Boundary

- Ceiling remains `scratch_diagnostic`.
- No holodeck, FEP, physics, bridge, manifold, Axis-0, formal, canonical, or QIT-engine admission is claimed.
- The exact `3`-cell set from `render_layer_readout_v1` is not consumed as invariant.
- G.2a is wired from birth through `scripts/builder_audit_boundary.py`.

## Builder Checks

- Both sides are searched.
- Mandatory persistence is reported, but it is identity-inclusive and excluded from the fair winner.
- The fair classical side includes empirical one-step generator frequency/mean and a searched generator-family policy class.
- The metric includes typed components and a diversity penalty to avoid rewarding trivially injective readouts.
- Controls include order-blind collapse, scrambled-error regression, dropped-half sensitivity for both sides, and no-identity-leak fields.

## Open For Audit

The Julia lane is a strict-carrier structural guard for the standard three-engine envelope, while the finite discriminator arithmetic is built in the Python/JAX/PyTorch lanes from the committed v1 source machinery. An independent audit should decide whether that scoping is enough for future ECD.06 reruns or whether a fuller Julia-native recomputation should be required.
