---
name: mass-drift-guard
description: Refuse a loop that lost alignment. Use when context-strategy is not ready, corpora mixed, or the exploration antichain collapsed.
---

# Mass drift guard

Mass drift is not a higher score. It is the object sliding.

Refuse when:

- context-strategy is not `CONTEXT_SNAPSHOT_READY`
- prompt and output corpora overlap
- an exploration harvest has fewer than two families
- a draft was treated as law

```text
python3 $CB_SKILLS_ROOT/mass-drift-guard/scripts/check_drift.py \
  --context /path/context-strategy.receipt.json \
  --harvest /path/exploration.receipt.json
```

Terminals: `DRIFT_CLEAN`, `REFUSE_MASS_DRIFT`.
