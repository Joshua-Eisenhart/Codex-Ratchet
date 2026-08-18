---
name: cb-termination-budget-cell
description: Require satisfice conditions, diminishing-return limits, stop criteria, cancellation obedience, and bounded retry and resource budgets.
---

# Termination budget cell

This leaf checks a finite termination proposal. It does not run a loop, spend
resources, cancel another process, or promote a result.

The JSON object must use schema `constraintbox.termination-budget.v1`, the
exact operation `cb-termination-budget-cell.v1`, and one canonical non-empty
string `target`. `target_id` and operation aliases are refused. It must
provide `satisfice`, `diminishing_return`, `stop`, `cancellation_obeys` (a
strict boolean), and bounded non-negative integer `time_budget`,
`compute_budget`, `resource_budget`, and `retry_budget`. `resource_budget` is
required; each dimension is capped at 1,000,000. `resist_one_more_round: true`
is refused as infinite optimization.
`cancelled: true` returns `CANCELLED_NO_AUTHORITY` with
`writes_performed: false`.

Run from the repository root:

```text
python3 constraint_box/integrated_system/skills/cb-termination-budget-cell/scripts/check_budget.py \
  --payload '{"schema":"constraintbox.termination-budget.v1","operation":"cb-termination-budget-cell.v1","target":"loop-1","satisfice":"seed ADMIT","diminishing_return":"no_improve","stop":"ENOUGH","cancellation_obeys":true,"time_budget":10,"compute_budget":100,"resource_budget":1,"retry_budget":1}'
```

Receipts are deterministic and self-digested, echo/bind all four budgets,
remain audit/proposal-only, and always carry `promotion_allowed: false`.
Malformed JSON, missing identity/budget dimensions, authority-shaped flags,
and cancellation resistance fail closed.
