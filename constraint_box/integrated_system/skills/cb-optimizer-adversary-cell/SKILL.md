---
name: cb-optimizer-adversary-cell
description: Attempt bounded optimizer-adversary attacks such as reward hacking, evaluator manipulation, and receipt forgery, reporting only observations.
---

# Optimizer adversary cell

`scripts/attack.py` evaluates an exact JSON map bound to canonical
`operation_id` `cb-optimizer-adversary-cell.v1` and a consistent nonempty
`target`/`target_id`. Attempts must use the known attack names and only
`BLOCKED`/`SUCCEEDED` statuses; output order is canonical. Incomplete coverage
holds, successful attacks refuse, and cancellation is passive with no sealed
receipt.
