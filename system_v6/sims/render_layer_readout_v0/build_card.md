# BUILD CARD - render_layer_readout_v0

## Scope

Build the holodeck doctrine expectation-1 packet in:

`system_v6/sims/render_layer_readout_v0/`

No git add or commit is authorized.

## Binding Authority

- `system_v6/receipts/owner_doctrine_holodeck_render_layer_20260612.md`
- CP.12 exclusion absorbed in commit `7c839050c`: render polarity reads a different distinction than Axis-0 response.
- `system_v6/receipts/holodeck_model_deepread_20260612.md`
- CP.11/CP.14 gate order satisfied by commit `4ef6cf0d8`.

## Packet Claim

Expectation 1, pre-registered: on the committed carrier with the committed generators:

- `RENDER` = the committed dynamics' one-step image.
- `ERROR` = typed divergence between render and realized state, computed under the co-ratchet type discipline.
- `UPDATE` = committed error-correction applied to the render side.

All three are finite objects and are run over a trajectory.

## Own-Readout Question

Expectation 2, post-exclusion: compute the render polarity from error-flow direction and test it against the committed Axis-0 phi/readout:

- same distinction: alias into Axis-0;
- different distinction: own readout family, and state what it reads;
- no stable distinction: falsifier for the readout.

## Falsifier

If the render row is indistinguishable from the substrate row under all probes, the layer is decorative on this carrier. Record that verdict as a result.

## Controls

- Identity-dynamics degeneracy.
- Scrambled-error control: random error assignment must break the polarity.
- No-identity-leak rule: polarity readout must not condition on cell identity.
- Positive-predicate boundary: the boundary must be able to admit.

## Required Outputs

- JAX/Python-style exact lane result.
- PyTorch graph/tensor lane result.
- Julia mirror result with no peer-result read.
- Standard helper-built envelope.
- Packet validator and tests.
- `builder_self_assessment.md`, not `audit_verdict.md`.

## Claim Ceiling

`scratch_diagnostic`; render-layer readout candidate only. No holodeck, FEP, physics, Axis-0, bridge, manifold, formal, canonical, or admission claim.
