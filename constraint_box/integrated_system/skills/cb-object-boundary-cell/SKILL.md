---
name: cb-object-boundary-cell
description: Restate a supplied object boundary and its constraints as a deterministic, non-authoritative proposal receipt.
---

# Object boundary cell

`scripts/restate.py` accepts one exact JSON card with `schema`, `operation`,
`operation_id`, `target`, `object`, `invariants`, `non_objectives`,
`forbidden_substitutions`, and `amendment_authority`. Both operation fields
must equal `cb-object-boundary-cell.v1`; unknown or case-variant keys refuse.

It emits `constraintbox.object-boundary.v1`, binds the target and operation,
records a bounded claim ceiling, and always sets `promotion_allowed` and
`writes_performed` to `false`.  An incomplete card is `HOLD`; malformed or
authority-shaped input is a literal structural `REFUSE`.  It never amends the
card or decides whether its object is true.

```json
{
  "schema": "constraintbox.object-boundary.v1",
  "operation": "cb-object-boundary-cell.v1",
  "operation_id": "cb-object-boundary-cell.v1",
  "target": "object-1",
  "object": "the bounded object",
  "invariants": ["preserve input"],
  "non_objectives": ["activation"],
  "forbidden_substitutions": ["winner"],
  "amendment_authority": "owner-only"
}
```

Use `verify_receipt` and `replay` from the script for local digest checks.
