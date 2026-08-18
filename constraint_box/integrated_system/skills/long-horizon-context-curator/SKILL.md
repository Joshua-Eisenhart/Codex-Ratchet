---
name: long-horizon-context-curator
description: Append-only decision ledger. Records original intent, invariants, rejected alternatives, failures, changes of mind, and unresolved contradictions. The latest prompt is a proposal against the ledger, never canon. Use before a self-loop keep or when recency is about to redefine the objective.
---

# Long-horizon context curator

This is not a rolling summary. It is the decision genealogy.

Entry kinds:

- `intent`
- `invariant`
- `rejected_alternative`
- `failure`
- `change_of_mind`
- `unresolved_contradiction`
- `proposal` (latest context; not canon)

Rules:

1. Append only. Rewriting an old entry refuses.
2. A proposal must name the current ledger head digest.
3. A proposal does not overwrite intent.
4. Couple with `failure-memory-resurrection-checker` for rejected branches.

```text
python3 $CB_SKILLS_ROOT/long-horizon-context-curator/scripts/curate_ledger.py \
  --ledger receipts/decision_ledger/ledger.jsonl \
  --append '{"kind":"proposal","text":"...","head":"<sha256>"}'
```

Claim ceiling: ledger hygiene only. Not Light geometry. Not promotion.
