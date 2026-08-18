---
name: cb-proxy-severance-cell
description: Search a bounded intervention for a rising proxy while the object stays fixed or worsens, without making a promotion decision.
---

# Proxy severance cell

`scripts/sever.py` accepts an exact JSON trial bound to canonical
`operation_id` `cb-proxy-severance-cell.v1`, a consistent nonempty
`target`/`target_id`, and a nonempty string intervention. Measures are finite,
bounded JSON numbers (not booleans or numeric strings). It reports `SEVERED`
or `NOT_FOUND`; `cancel_requested: true` is passive `CANCELLED` with no sealed
receipt.
