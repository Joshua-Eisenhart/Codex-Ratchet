---
name: cb-context-ledger
description: Append-only process-persistent storage of owner statements, ObjectCards, decisions, branches, contradictions, failures, negatives, re-offer conditions, claim ceilings, and lineage. Nothing is deleted because it is old. Use instead of recency-pruned StrategyMemory for durable context.
---

# CB context ledger

StrategyMemory keeps a tiny conserved stratum. This ledger is the archive.

Kinds: `owner_statement`, `object_card`, `decision`, `branch`, `contradiction`, `failure`, `negative`, `reoffer`, `claim_ceiling`, `lineage`, `proposal`.

A proposal is not canon. Rewrites refuse.

```text
python3 $CB_SKILLS_ROOT/cb-context-ledger/scripts/ledger.py \
  --ledger receipts/context_ledger/ledger.jsonl \
  --append '{"kind":"owner_statement","text":"..."}'
```

Couples to `long-horizon-context-curator`. Same append-only law. Broader kinds.
