---
name: cb-externality-horizon-cell
description: Identify costs displaced onto future runs, maintainers, absent stakeholders, evidence quality, rival branches, or the wider system.
---

# Externality horizon cell

This leaf is a deterministic proposal/audit surface. It maps the six named
horizons; it does not decide, activate, write, or promote anything.

The JSON object must use schema `constraintbox.externality-horizon.v1`, the
exact operation `cb-externality-horizon-cell.v1`, and one canonical non-empty
string `target`. `target_id` and operation aliases are refused. It must also
contain one value for each of
`future_runs`, `maintainers`, `absent_stakeholders`, `evidence_quality`,
`rival_branches`, and `wider_system`. Use the string `none` when no displaced
cost is observed. An input with `cancelled: true` returns
`CANCELLED_NO_AUTHORITY` and performs no write.

Run from the repository root:

```text
python3 constraint_box/integrated_system/skills/cb-externality-horizon-cell/scripts/map_horizon.py \
  --payload '{"schema":"constraintbox.externality-horizon.v1","operation":"cb-externality-horizon-cell.v1","target":"object-1","future_runs":"none","maintainers":"none","absent_stakeholders":"none","evidence_quality":"none","rival_branches":"none","wider_system":"none"}'
```

Every receipt echoes the exact target and operation identity, self-binds its
digest to the current input, sets `audit_only` and `proposal_only` true, sets
`promotion_allowed` false, and reports no write/provider. Unknown keys,
non-JSON values, deep/oversized inputs, receipt replay, and authority-shaped
fields fail closed.
