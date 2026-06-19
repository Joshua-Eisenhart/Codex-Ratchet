# BUILD CARD - ecd02_chiral_information_routing_v0

## Boundary

Build in `system_v6/sims/ecd02_chiral_information_routing_v0/` only. No git add. No git commit.

## Authority

- Capability registry: `system_v6/receipts/engine_capability_differentiators_20260612.md`, `ECD.02`.
- QCA v3 fixture: `system_v6/sims/ring_checkerboard_qca_v3/`, the open-chain L/R engine fixture with extracted indices `L=-1`, `R=+1`.
- Alt-view receipt: `system_v6/receipts/altviews_capability_and_surface_miss_20260612.md`, Q1 chiral information diode finite-test designs. Advisory only; consume as labeled test inspiration, not authority.
- Cross-model anchor receipt: `system_v6/receipts/cross_model_anchor_recompute_panel8_20260612.md`, open-chain calibration expectation `right=+1`, `left=-1`, `onsite=0`.

## Discriminator

Build a capability-discriminator packet for chiral information routing:

- Use the QCA v3 L/R engine pair as a directional information channel on the same finite open chain.
- Inject a pinned one-bit state at one end of the chain.
- Run the L-engine and R-engine routing models for finite `k` steps.
- Compute the endpoint mutual-information arrival profile: left endpoint vs right endpoint.
- Compute routing asymmetry.
- The extracted index sign must predict the routing direction.
- The Szilard baseline must fail because it has no chirality: its opposite-end routing profile is symmetric/zero on the same chain.
- Include a diode row: information passes left-to-right through the R-engine but is blocked/attenuated right-to-left, or record the honest negative.

## Controls

- Index-0 engine: routing symmetric; capability tracks the index.
- Swapped-chirality mirror: direction prediction flips with the sign.
- Falsifier reachable: force the R-engine onto the L sign and kill the original opposite-sign predicate.
- Keep finite-ring/QCA admission fences from QCA v3: this is not finite-ring GNVW admission, not all-cells QCA admission, and not a physics chirality claim.

## Standard Contract

Emit `classification=scratch_diagnostic`, `promotion_allowed=false`, `formal_admission_allowed=false`, `claim_ceiling=capability_discriminator_only`, non-empty `TOOL_MANIFEST`, non-empty `TOOL_INTEGRATION_DEPTH`, honest `tool_intent`, positive/negative/boundary sections, three engine results, envelope, packet-local validator result, and focused pytest coverage.

