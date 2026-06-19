# BUILD CARD: mct_selfloop_policy_discriminator_v0

Status: builder packet only.
Ceiling: `scratch_diagnostic`, `promotion_allowed=false`, `formal_admission_allowed=false`.
Claim ceiling: `policy_discriminator_table_only`.
Decision status: `owner_gated`; this packet makes no recommendation.

## Authority

- `system_v6/receipts/evening_mining_estate_s11_20260611.json`, S11 mining row `OWNER DECISION 2 - self-loop retention policy for folded relations`: both policies are mathematically valid; the owner chooses the default.
- `system_v6/receipts/mct_reconciled_spec_20260609.md`: M(C,t) folded-relation choice point; the 8-state fixture reports erase/retain as distinct relation policies.
- Fable-audit improvement: a bounded discriminator may inform the owner choice without making it.
- Committed 33-cell carrier and G0 transition graph from `system_v6/sims/basin_rc_transition_graph_v0/results/basin_rc_transition_graph_v0_envelope_results.json`, pinned by `transition_graph_sha256 = bd0cd3b551bbb3f323eb596695da8d91429f010780c1c137af4a253bd73438f0`.

## Object

On the committed 33-cell carrier and G0 transition graph, compute the quotient/folded relation by the graph's computed communicating-class/SCC partition. Run both folded self-loop policies:

- `retain`: quotient pushforward relation keeps self-loops created by internal source-class edges.
- `erase`: quotient pushforward relation drops folded self-loops and ledgers the dropped transported source edges.

## Required Output

Emit a computed consequences table with:

- edge counts;
- terminal-class structure and absent-exit proofs;
- may/must semantics impact;
- typed-entropy ledger impact;
- downstream-consumer impact, naming committed packet rows that would change under each branch;
- vacuity control: branches must differ somewhere computable, otherwise report the decision as vacuous.

## Boundaries

- No recommendation.
- No owner decision.
- No canonical default.
- No axis, bridge, physics, or manifold-admission claim.
- No edits outside `system_v6/sims/mct_selfloop_policy_discriminator_v0/`.
- No `git add`, no commit.

## Files

- `mct_selfloop_policy_discriminator_v0.py`
- `validate_mct_selfloop_policy_discriminator_v0.py`
- `build_card.md`
- `results/mct_selfloop_policy_discriminator_v0_results.json`
- `results/mct_selfloop_policy_discriminator_v0_table.md`
