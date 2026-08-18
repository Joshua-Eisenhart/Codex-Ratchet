---
name: cb-option-value-retreat-cell
description: Map reversible probes, irreversible commitments, hold and retreat conditions, and preserved options without committing an action.
---

# Option-value retreat cell

`scripts/retreat.py` accepts an exact JSON card with canonical `operation` and
`operation_id` (both `cb-option-value-retreat-cell.v1`), a nonblank `target`,
and `reversible_probes`, `irreversible_commitments`, `hold_conditions`,
`retreat_conditions`, and `preserved_options`. Every probe is exactly
`{name,scope,reversible,undo_operation,restored_state_check}` with scope
`read_only` or `local_scratch`, literal `reversible: true`, and nonblank undo
and restoration checks. External/production/release scopes and ship, rollout,
deploy, release, publish, commit, or delete action tokens refuse. Irreversible
commitments must link to retreat conditions and preserved options.

The output schema is `constraintbox.option-retreat.v1`.  An irreversible
commitment without a retreat condition is a non-authoritative
`HOLD_REVERSIBILITY`; it never authorizes that commitment.  Missing fields
hold, malformed or authority-shaped input refuses, and every receipt is
non-writing with `promotion_allowed: false` and a replay/tamper digest.
