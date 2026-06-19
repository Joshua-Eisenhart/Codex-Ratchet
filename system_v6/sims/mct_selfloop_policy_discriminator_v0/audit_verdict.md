# Independent audit verdict -- mct_selfloop_policy_discriminator_v0

Auditor: independent fresh Codex audit. I did not build this packet. I read the build card/result claims fresh and recomputed the policy-branch consequences from the committed G0 graph before accepting the packet prose.

## Verdict

VERDICT: PASS / SUSTAINED as a discriminator table only, with a G.2a violation noted.

Claim ceiling: `policy_discriminator_table_only` under `scratch_diagnostic`, `promotion_allowed=false`, and `formal_admission_allowed=false`. This verdict does not make, recommend, infer, or canonize the M(C,t) self-loop policy.

Citation rule: cite this packet only for computed consequences of the two folded self-loop policy branches on the committed G0 transition graph. Any citation must state `decision_status=owner_gated` and `recommendation_emitted=false`.

## Fresh Recompute

I imported `mct_selfloop_policy_discriminator_v0.py`, loaded `basin_rc_transition_graph_v0_envelope_results.json`, checked the G0 graph hash, and recomputed both branches in memory using `folded_branch()`. I did not run the writer entrypoint.

Fresh recomputation returned:

- G0 transition graph hash matched `bd0cd3b551bbb3f323eb596695da8d91429f010780c1c137af4a253bd73438f0`.
- folded node count: 2.
- source transition edge rows: 198.
- fresh branch payloads matched committed `branches`.
- fresh consequence table matched committed `computed_consequences_table`.
- `erase`: unique folded relation edges 1, retained transport rows 2, erased transport rows 196, unique self-loop relation edges 0, must basin size 2, post-policy edge-type entropy 0.0.
- `retain`: unique folded relation edges 3, retained transport rows 198, erased transport rows 0, unique self-loop relation edges 2, must basin size 1, post-policy edge-type entropy 0.056465174279.
- terminal folded node count stayed 1 in both branches; may/existential basin folded node count stayed 2 in both branches.

I also ran the packet-local validator:

- `ok=true`.
- errors: none.
- checked branch edge counts `erase=1`, `retain=3`.
- checked branch must sizes `erase=2`, `retain=1`.

## Policy Boundary

No decision smuggling found. The committed result has `decision_status=owner_gated`, `recommendation_emitted=false`, and disallows default policy recommendation, owner decision, canonical policy, axis admission, bridge claim, and physics claim. The table states that the decision is owner-gated and makes no recommendation.

## G.2a State

G.2a state: violation / pre-G.2a packet. I found no `builder_audit_boundary` helper use, no `no_builder_audit_verdict` field, and no build-card declaration of G.2a from birth. The packet predates or bypasses the later builder/audit idempotency convention. Violation noted here; not repaired by this audit.

## Bottom Line

The audited claims survive only as discriminator/consequence rows. The packet distinguishes erase versus retain consequences, but the M(C,t) self-loop policy itself remains owner-gated.
