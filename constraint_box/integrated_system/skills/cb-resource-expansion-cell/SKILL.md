---
name: cb-resource-expansion-cell
description: Check whether optimization expands tools, writes, compute, time, persistence, permissions, or external actions beyond explicit authorization.
---

# Resource expansion cell

`scripts/check_expansion.py` compares one exact JSON authorization map with
one used-resource map, bound to canonical `operation_id`
`cb-resource-expansion-cell.v1` and a consistent nonempty `target`/`target_id`.
Axes reject unknown names, scalar/list mismatches, nonstrict numeric types,
negative quotas, and oversized values. It reports bounded `INSIDE` or `REFUSE`; cancellation is
passive with no sealed receipt, and no provider, activation, promotion, or
write occurs.
